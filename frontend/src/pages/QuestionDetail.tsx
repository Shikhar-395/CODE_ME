import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import type { QuestionDetail as QuestionDetailType, User } from '../api';
import { getErrorMessage } from '../errors';
import Editor from '@monaco-editor/react';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface QuestionDetailProps {
  questionId: number;
  user: User | null;
}

const BOILERPLATE: Record<string, string> = {
  python: `# Write your Python 3 solution here
import sys

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Example logic:
    # print(input_data)
    pass

if __name__ == "__main__":
    solve()`,
  javascript: `// Write your JavaScript (Node.js) solution here
const fs = require('fs');

function solve() {
    const input = fs.readFileSync(0, 'utf-8').trim();
    if (!input) return;
    
    // Example logic:
    // console.log(input);
}

solve();`,
  cpp: `// Write your C++ solution here
#include <iostream>
#include <string>
#include <vector>

using namespace std;

int main() {
    // Fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    // Read your input and solve
    
    return 0;
}`,
  java: `// Write your Java solution here
import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) {
        Scanner in = new Scanner(System.in);
        // Solve your challenge here
    }
}`
};

export const QuestionDetail: React.FC<QuestionDetailProps> = ({ questionId }) => {
  const [question, setQuestion] = useState<QuestionDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Editor state
  const [language, setLanguage] = useState<'cpp' | 'python' | 'java' | 'javascript'>('python');
  const [code, setCode] = useState(BOILERPLATE.python);
  
  // Submission flow state
  const [submitting, setSubmitting] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ignore = false;

    api.getQuestion(questionId)
      .then((data) => {
        if (!ignore) setQuestion(data);
      })
      .catch((err) => {
        if (!ignore) setError(getErrorMessage(err, 'Failed to load question details.'));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    
    // Clean up websocket connection on unmount
    return () => {
      ignore = true;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [questionId]);

  // Handle changing language and updating boilerplate
  const handleLanguageChange = (lang: 'cpp' | 'python' | 'java' | 'javascript') => {
    // Warn if user has edited code
    if (code !== BOILERPLATE[language] && !window.confirm('Change language? Your current code for this language will be reset.')) {
      return;
    }
    setLanguage(lang);
    setCode(BOILERPLATE[lang]);
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setCode(value);
    }
  };

  const handleSubmit = async () => {
    if (!code.trim()) return;
    
    setSubmitting(true);
    setSubmissionStatus('pending');
    setError(null);
    
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      // Create submission
      const sub = await api.submitCode({
        question_id: questionId,
        code,
        language
      });
      
      // Establish WebSocket connection for real-time status updates
      const wsUrl = api.getWebSocketUrl(sub.id);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Judger WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.submission_id === sub.id) {
            setSubmissionStatus(payload.status);
            
            // If the status is final, close the socket
            const isFinalStatus = ['accepted', 'wrong_answer', 'tle', 'compile_error', 'runtime_error'].includes(payload.status);
            if (isFinalStatus) {
              setSubmitting(false);
              ws.close();
            }
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        // Fallback: poll API for status
        pollStatus(sub.id);
      };

      ws.onclose = () => {
        console.log('Judger WebSocket closed');
      };

    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Submission failed.'));
      setSubmissionStatus(null);
      setSubmitting(false);
    }
  };

  // Fallback Polling if WS fails
  const pollStatus = async (subId: number) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const sub = await api.getSubmission(subId);
        setSubmissionStatus(sub.status);
        
        const isFinalStatus = ['accepted', 'wrong_answer', 'tle', 'compile_error', 'runtime_error'].includes(sub.status);
        if (isFinalStatus || attempts > 15) {
          clearInterval(interval);
          setSubmitting(false);
        }
      } catch (err) {
        console.error('Polling error', err);
        clearInterval(interval);
        setSubmitting(false);
      }
    }, 2000);
  };

  const getStatusText = (status: string | null) => {
    if (!status) return 'Idle';
    return status.replace('_', ' ').toUpperCase();
  };

  const getStatusClass = (status: string | null) => {
    if (!status) return 'status-idle';
    return `status-${status}`;
  };

  // Filter example cases (non-hidden cases)
  const exampleTestCases = question?.test_cases.filter(tc => !tc.is_hidden) || [];

  const getQuestionDifficulty = (q: any) => {
    if (!q) return 'EASY';
    const title = q.title.toLowerCase();
    if (title.includes('two sum') || title.includes('easy') || q.id % 3 === 0) return 'EASY';
    if (title.includes('median') || title.includes('hard') || q.id % 3 === 2) return 'HARD';
    return 'MEDIUM';
  };

  return (
    <div className="workspace-container fade-in">
      {loading && (
        <div className="flex justify-center items-center h-96">
          <RefreshCw size={36} className="animate-spin text-muted" />
        </div>
      )}

      {error && (
        <div className="alert alert-error m-6">
          <AlertCircle size={20} />
          <div>
            <h3>Error loading workspace</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && question && (
        <div className="workspace-body" style={{ gridTemplateColumns: '45% 55%' }}>
          {/* Left Panel: Description */}
          <div className="workspace-panel description-panel">
            <div className="panel-header" style={{ padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div className="flex items-center gap-3">
                <a href={question ? `#test/${question.test_id}` : '#dashboard'} className="workspace-back" style={{ width: '28px', height: '28px' }}>
                  <ArrowLeft size={16} />
                </a>
                <span className="text-xs text-muted" style={{ fontWeight: '500' }}>Description</span>
              </div>
              <div className="flex items-baseline gap-3 mt-1">
                <h2 className="workspace-title" style={{ fontSize: '20px', fontWeight: '700' }}>
                  {question.id}. {question.title}
                </h2>
                <span className={`problem-difficulty-badge ${getQuestionDifficulty(question).toLowerCase()}`} style={{ fontSize: '10px' }}>
                  {getQuestionDifficulty(question)}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>45.2K likes</span>
              </div>
            </div>
            <div className="panel-content scrollable">
              <div className="question-content-html" style={{ color: 'var(--text-primary)', opacity: 0.9, fontSize: '14px', lineHeight: '1.6' }}>
                {question.description.split('\n').map((para, i) => (
                  <p key={i} className="mb-4">{para}</p>
                ))}
              </div>

              {exampleTestCases.length > 0 && (
                <div className="example-cases-container mt-6">
                  <h4 className="mb-3" style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Example cases
                  </h4>
                  {exampleTestCases.map((tc, index) => (
                    <div key={tc.id} className="example-case card mb-3" style={{ padding: '16px', backgroundColor: 'var(--bg-main)' }}>
                      <div className="example-case-header" style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        Example {index + 1}:
                      </div>
                      <div className="example-case-body">
                        <div className="io-block">
                          <span className="io-label" style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Input:</span>
                          <pre style={{ margin: '0', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{tc.input_data}</pre>
                        </div>
                        <div className="io-block mt-2">
                          <span className="io-label" style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Expected Output:</span>
                          <pre style={{ margin: '0', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>{tc.output_data}</pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel: Code Editor & Submission Console */}
          <div className="workspace-panel editor-panel">
            {/* Editor panel header matching mockup 2 */}
            <div className="panel-header flex justify-between items-center" style={{ padding: '12px 24px', minHeight: '52px' }}>
              <div className="flex items-center gap-3">
                <select
                  className="form-input select-input"
                  value={language}
                  onChange={(e) => handleLanguageChange(e.target.value as any)}
                  disabled={submitting}
                  style={{
                    padding: '4px 12px',
                    fontSize: '13px',
                    fontWeight: '600',
                    height: '30px',
                    background: 'var(--bg-main)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                    width: '120px'
                  }}
                >
                  <option value="python">Python 3</option>
                  <option value="javascript">JavaScript</option>
                  <option value="cpp">C++</option>
                  <option value="java">Java</option>
                </select>
                <button 
                  onClick={() => setCode(BOILERPLATE[language])} 
                  className="btn btn-secondary btn-sm"
                  title="Reset boilerplate"
                  disabled={submitting}
                  style={{ height: '30px', width: '30px', padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  <RefreshCw size={12} />
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleSubmit}
                  className="btn btn-secondary btn-sm"
                  disabled={submitting || !code.trim()}
                  style={{ height: '30px', padding: '0 16px', fontSize: '13px', fontWeight: '600' }}
                >
                  Run
                </button>
                <button
                  onClick={handleSubmit}
                  className="btn btn-primary btn-sm"
                  disabled={submitting || !code.trim()}
                  style={{
                    height: '30px',
                    padding: '0 16px',
                    fontSize: '13px',
                    fontWeight: '600',
                    backgroundColor: 'var(--color-primary)',
                    color: 'var(--bg-main)'
                  }}
                >
                  {submitting ? <RefreshCw size={12} className="animate-spin" /> : null}
                  <span>Submit</span>
                </button>
              </div>
            </div>

            <div className="code-editor-wrapper" style={{ flex: '1', minHeight: '300px' }}>
              <Editor
                height="100%"
                language={language === 'cpp' ? 'cpp' : language === 'java' ? 'java' : language === 'javascript' ? 'javascript' : 'python'}
                theme="vs-dark"
                value={code}
                onChange={handleEditorChange}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  roundedSelection: false,
                  scrollBeyondLastLine: false,
                  readOnly: submitting,
                  cursorStyle: 'line',
                  automaticLayout: true,
                }}
              />
            </div>

            {/* Console Pane */}
            <div className="console-panel" style={{ maxHeight: '250px' }}>
              <div className="console-header flex justify-between items-center" style={{ padding: '8px 24px', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-surface)' }}>
                <div className="flex gap-4">
                  <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-primary)' }}>Testcase</span>
                  <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Console</span>
                </div>
                {submissionStatus && (
                  <div className={`console-status-badge badge ${getStatusClass(submissionStatus)}`} style={{ padding: '2px 8px', fontSize: '11px' }}>
                    <span>{getStatusText(submissionStatus)}</span>
                  </div>
                )}
              </div>
              <div className="console-content scrollable" style={{ padding: '16px 24px' }}>
                {!submissionStatus && (
                  <p className="console-placeholder" style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Your output results will show here once you run or submit.</p>
                )}
                {submissionStatus && (
                  <div className="console-result">
                    <p className="result-time text-xs text-muted" style={{ marginBottom: '8px' }}>
                      Executed at: {new Date().toLocaleTimeString()}
                    </p>
                    
                    {submissionStatus === 'accepted' && (
                      <div className="result-success-alert flex items-center gap-3" style={{ padding: '12px 16px', background: 'rgba(34, 197, 94, 0.05)', borderRadius: '6px', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                        <CheckCircle style={{ color: 'var(--color-primary)' }} size={20} />
                        <div>
                          <h4 style={{ color: 'var(--color-primary)', fontSize: '14px', fontWeight: '600' }}>Accepted</h4>
                          <p className="text-secondary text-sm">All test cases passed successfully!</p>
                        </div>
                      </div>
                    )}

                    {['wrong_answer', 'tle', 'compile_error', 'runtime_error'].includes(submissionStatus) && (
                      <div className="result-failure-alert flex items-center gap-3" style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.05)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                        <XCircle style={{ color: 'var(--color-danger)' }} size={20} />
                        <div>
                          <h4 style={{ color: 'var(--color-danger)', fontSize: '14px', fontWeight: '600' }}>{getStatusText(submissionStatus)}</h4>
                          <p className="text-secondary text-sm">Your code did not pass verification. Refactor and try again.</p>
                        </div>
                      </div>
                    )}

                    {['pending', 'running'].includes(submissionStatus) && (
                      <div className="flex items-center gap-2">
                        <RefreshCw className="animate-spin text-info" size={16} />
                        <span style={{ fontSize: '13px' }}>Judging solution on sandbox virtual machine...</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
