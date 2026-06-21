import React, { useCallback, useEffect, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Eye,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { api } from '../api';
import type { QuestionDetail as QuestionDetailType, Submission, User } from '../api';
import { useContestCountdown } from '../contestTime';
import { getErrorMessage } from '../errors';

interface QuestionDetailProps {
  questionId: number;
  user: User | null;
}

type SupportedLanguage = Submission['language'];
type ExecutionKind = 'run' | 'submit';

const BOILERPLATE: Record<SupportedLanguage, string> = {
  python: `import sys

def solve():
    data = sys.stdin.read().split()
    # Write your solution here.

if __name__ == "__main__":
    solve()
`,
  javascript: `const fs = require('fs');
const input = fs.readFileSync(0, 'utf8').trim().split(/\\s+/);

function solve() {
  // Write your solution here.
}

solve();
`,
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // Write your solution here.
    return 0;
}
`,
  java: `import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        Scanner input = new Scanner(System.in);
        // Write your solution here.
    }
}
`,
};

const FINAL_STATUSES: Submission['status'][] = [
  'accepted',
  'wrong_answer',
  'tle',
  'compile_error',
  'runtime_error',
];

const editorKey = (questionId: number, language: SupportedLanguage) =>
  `code-me:${questionId}:${language}`;

export const QuestionDetail: React.FC<QuestionDetailProps> = ({ questionId, user }) => {
  const [question, setQuestion] = useState<QuestionDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<SupportedLanguage>('python');
  const [code, setCode] = useState(() => localStorage.getItem(editorKey(questionId, 'python')) || BOILERPLATE.python);
  const [executing, setExecuting] = useState(false);
  const [executionKind, setExecutionKind] = useState<ExecutionKind | null>(null);
  const [executionStatus, setExecutionStatus] = useState<Submission['status'] | null>(null);
  const [executedAt, setExecutedAt] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<number | null>(null);
  const executionKindRef = useRef<ExecutionKind | null>(null);
  const executionActiveRef = useRef(false);

  const clearConnections = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const loadQuestion = useCallback(async () => {
    setError(null);
    try {
      setQuestion(await api.getQuestion(questionId));
    } catch (err: unknown) {
      setQuestion(null);
      setError(getErrorMessage(err, 'Could not open this problem.'));
    } finally {
      setLoading(false);
    }
  }, [questionId]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setLoading(true);
      void loadQuestion();
    });
    return () => {
      window.cancelAnimationFrame(frame);
      clearConnections();
    };
  }, [clearConnections, loadQuestion]);

  useEffect(() => {
    localStorage.setItem(editorKey(questionId, language), code);
  }, [code, language, questionId]);

  useEffect(() => {
    const sync = () => void loadQuestion();
    window.addEventListener('focus', sync);
    const interval = window.setInterval(sync, 30_000);
    return () => {
      window.removeEventListener('focus', sync);
      window.clearInterval(interval);
    };
  }, [loadQuestion]);

  const handleExpire = useCallback(() => {
    void loadQuestion();
  }, [loadQuestion]);
  const countdown = useContestCountdown(question?.attempt, handleExpire);

  const changeLanguage = (next: SupportedLanguage) => {
    setLanguage(next);
    setCode(localStorage.getItem(editorKey(questionId, next)) || BOILERPLATE[next]);
  };

  const finishExecution = useCallback((status: Submission['status']) => {
    setExecutionStatus(status);
    if (FINAL_STATUSES.includes(status)) {
      setExecuting(false);
      executionActiveRef.current = false;
      setExecutedAt(new Date());
      clearConnections();
      if (executionKindRef.current === 'submit') {
        void loadQuestion();
      }
    }
  }, [clearConnections, loadQuestion]);

  const pollStatus = useCallback((submissionId: number) => {
    if (pollRef.current !== null) return;
    let attempts = 0;
    pollRef.current = window.setInterval(async () => {
      attempts += 1;
      try {
        const submission = await api.getSubmission(submissionId);
        finishExecution(submission.status);
        if (FINAL_STATUSES.includes(submission.status) || attempts >= 30) {
          if (pollRef.current !== null) window.clearInterval(pollRef.current);
          pollRef.current = null;
          if (attempts >= 30 && !FINAL_STATUSES.includes(submission.status)) {
            setExecuting(false);
            executionActiveRef.current = false;
            setError('Judging is taking longer than expected. Check Submissions for the final result.');
          }
        }
      } catch (err: unknown) {
        if (pollRef.current !== null) window.clearInterval(pollRef.current);
        pollRef.current = null;
        setExecuting(false);
        executionActiveRef.current = false;
        setError(getErrorMessage(err, 'Could not retrieve the judge result.'));
      }
    }, 1_000);
  }, [finishExecution]);

  const followSubmission = useCallback((submission: Submission) => {
    const socket = new WebSocket(api.getWebSocketUrl(submission.id));
    wsRef.current = socket;
    let receivedStatus = false;
    const fallback = window.setTimeout(() => {
      if (!receivedStatus) pollStatus(submission.id);
    }, 2_000);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as { submission_id: number; status: Submission['status'] };
        if (payload.submission_id === submission.id) {
          receivedStatus = true;
          window.clearTimeout(fallback);
          finishExecution(payload.status);
        }
      } catch {
        pollStatus(submission.id);
      }
    };
    socket.onerror = () => {
      window.clearTimeout(fallback);
      pollStatus(submission.id);
    };
    socket.onclose = () => {
      window.clearTimeout(fallback);
      if (executionActiveRef.current && !receivedStatus) pollStatus(submission.id);
    };
  }, [finishExecution, pollStatus]);

  const execute = async (kind: ExecutionKind) => {
    if (!code.trim() || executing) return;
    clearConnections();
    setExecuting(true);
    executionActiveRef.current = true;
    setExecutionKind(kind);
    executionKindRef.current = kind;
    setExecutionStatus('pending');
    setExecutedAt(null);
    setError(null);
    try {
      const payload = { question_id: questionId, code, language };
      const submission = kind === 'run'
        ? await api.runCode(payload)
        : await api.submitCode(payload);
      followSubmission(submission);
    } catch (err: unknown) {
      setExecutionStatus(null);
      setExecuting(false);
      executionActiveRef.current = false;
      setError(getErrorMessage(err, kind === 'run' ? 'Run failed.' : 'Submission failed.'));
      await loadQuestion();
    }
  };

  const statusLabel = executionStatus?.replaceAll('_', ' ') || '';
  const exampleCases = question?.test_cases || [];

  if (loading) {
    return (
      <div className="workspace-container">
        <div className="workspace-loading" aria-label="Loading problem" aria-busy="true">
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-copy" />
          <div className="skeleton workspace-skeleton" />
        </div>
      </div>
    );
  }

  if (error && !question) {
    return (
      <div className="container problem-gate">
        <div className="card empty-state">
          <AlertCircle size={40} className="text-muted mb-4" aria-hidden="true" />
          <h1>Problem locked</h1>
          <p className="text-secondary">{error}</p>
          <a href="#contests" className="btn btn-primary mt-4">Go to contests</a>
        </div>
      </div>
    );
  }

  if (!question) return null;

  if (user?.role === 'admin') {
    return (
      <div className="admin-problem-detail container">
        <div className="admin-problem-toolbar">
          <a href={`#test/${question.test_id}`} className="btn btn-secondary">
            <ArrowLeft size={16} aria-hidden="true" /> Back to contest
          </a>
          <div className="view-only-badge"><Eye size={16} aria-hidden="true" /> View only</div>
        </div>
        <article className="admin-problem-statement card">
          <header className="admin-problem-statement-header">
            <div>
              <p className="eyebrow">Problem #{question.id}</p>
              <h1>{question.title}</h1>
              <div className="admin-problem-meta">
                <span>{question.contest_title}</span>
                <span className={`problem-difficulty-badge ${question.difficulty}`}>{question.difficulty}</span>
              </div>
            </div>
            <div className="view-only-callout">
              <Eye size={20} aria-hidden="true" />
              <div><strong>Administrator preview</strong><p>Review the statement and public cases without executing code.</p></div>
            </div>
          </header>
          <section className="statement-section">
            <h2>Description</h2>
            <div className="question-content-html"><p>{question.description}</p></div>
          </section>
          <section className="statement-section">
            <h2>Example cases</h2>
            <div className="admin-example-grid">
              {exampleCases.map((testCase, index) => (
                <div className="example-case card" key={testCase.id}>
                  <h3>Example {index + 1}</h3>
                  <div className="io-block"><span className="io-label">Input</span><pre>{testCase.input_data}</pre></div>
                  <div className="io-block"><span className="io-label">Expected output</span><pre>{testCase.output_data}</pre></div>
                </div>
              ))}
            </div>
          </section>
        </article>
      </div>
    );
  }

  return (
    <div className="workspace-container fade-in">
      <div className="workspace-mode-bar">
        <a href={`#test/${question.test_id}`} className="workspace-back" aria-label="Back to contest">
          <ArrowLeft size={16} aria-hidden="true" />
        </a>
        <span className={`attempt-state attempt-${question.attempt?.status || 'completed'}`}>
          {question.access_state === 'timed' ? 'timed attempt' : 'practice mode'}
        </span>
        {question.access_state === 'timed' && (
          <div className="workspace-timer" aria-live="polite">
            <Clock size={15} aria-hidden="true" />
            <strong>{countdown.formatted}</strong>
          </div>
        )}
        <span className="workspace-contest-name">{question.contest_title}</span>
      </div>

      {error && (
        <div className="workspace-inline-error" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      <div className="workspace-body">
        <section className="workspace-panel description-panel" aria-labelledby="problem-title">
          <header className="panel-header problem-panel-heading">
            <div>
              <p className="eyebrow">Problem {question.id}</p>
              <h1 id="problem-title">{question.title}</h1>
            </div>
            <span className={`problem-difficulty-badge ${question.difficulty}`}>{question.difficulty}</span>
          </header>
          <div className="panel-content scrollable">
            <div className="question-content-html"><p>{question.description}</p></div>
            <section className="example-cases-container">
              <h2>Examples</h2>
              {exampleCases.length === 0 ? (
                <div className="statement-empty">No public examples are available.</div>
              ) : exampleCases.map((testCase, index) => (
                <div key={testCase.id} className="example-case card">
                  <h3>Example {index + 1}</h3>
                  <div className="io-block"><span className="io-label">Input</span><pre>{testCase.input_data}</pre></div>
                  <div className="io-block"><span className="io-label">Output</span><pre>{testCase.output_data}</pre></div>
                </div>
              ))}
            </section>
          </div>
        </section>

        <section className="workspace-panel editor-panel" aria-label="Code editor">
          <header className="panel-header editor-toolbar">
            <div className="editor-language-controls">
              <label className="sr-only" htmlFor="editor-language">Programming language</label>
              <select
                id="editor-language"
                className="form-input select-input"
                value={language}
                onChange={(event) => changeLanguage(event.target.value as SupportedLanguage)}
                disabled={executing}
              >
                <option value="python">Python 3</option>
                <option value="javascript">JavaScript</option>
                <option value="cpp">C++</option>
                <option value="java">Java</option>
              </select>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCode(BOILERPLATE[language])}
                disabled={executing}
              >
                Reset
              </button>
            </div>
            <div className="editor-actions">
              <button type="button" className="btn btn-secondary" onClick={() => void execute('run')} disabled={executing || !code.trim()}>
                {executing && executionKind === 'run' && <RefreshCw size={15} className="animate-spin" aria-hidden="true" />}
                Run examples
              </button>
              <button type="button" className="btn btn-primary" onClick={() => void execute('submit')} disabled={executing || !code.trim()}>
                {executing && executionKind === 'submit' && <RefreshCw size={15} className="animate-spin" aria-hidden="true" />}
                Submit
              </button>
            </div>
          </header>

          <div className="code-editor-wrapper">
            <Editor
              height="100%"
              language={language === 'cpp' ? 'cpp' : language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                readOnly: executing,
                automaticLayout: true,
              }}
            />
          </div>

          <div className="console-panel" aria-live="polite">
            <header className="console-header">
              <div>
                <strong>Judge result</strong>
                {executionKind && <span>{executionKind === 'run' ? 'Public examples' : 'Full submission'}</span>}
              </div>
              {executionStatus && <span className={`console-status-badge status-${executionStatus}`}>{statusLabel}</span>}
            </header>
            <div className="console-content">
              {!executionStatus && <p className="console-placeholder">Run the public examples or submit against the full test suite.</p>}
              {['pending', 'running'].includes(executionStatus || '') && (
                <div className="judge-progress"><RefreshCw size={16} className="animate-spin" aria-hidden="true" /> Judging in the isolated runner…</div>
              )}
              {executionStatus === 'accepted' && (
                <div className="result-alert result-success">
                  <CheckCircle size={20} aria-hidden="true" />
                  <div><strong>Accepted</strong><p>{executionKind === 'run' ? 'Every public example passed.' : 'All public and hidden cases passed.'}</p></div>
                </div>
              )}
              {executionStatus && FINAL_STATUSES.includes(executionStatus) && executionStatus !== 'accepted' && (
                <div className="result-alert result-failure">
                  <XCircle size={20} aria-hidden="true" />
                  <div><strong>{statusLabel}</strong><p>Review the edge cases, adjust your solution, and try again.</p></div>
                </div>
              )}
              {executedAt && <p className="result-time">Completed at {executedAt.toLocaleTimeString()}</p>}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
