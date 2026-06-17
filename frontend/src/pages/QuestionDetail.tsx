import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import type { QuestionDetail as QuestionDetailType, User } from '../api';
import { getErrorMessage } from '../errors';
import Editor from '@monaco-editor/react';
import { ArrowLeft, Send, RefreshCw, AlertCircle, HelpCircle, CheckCircle, XCircle } from 'lucide-react';

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

  const getStatusIcon = (status: string | null) => {
    switch (status) {
      case 'accepted':
        return <CheckCircle size={20} className="text-success" />;
      case 'wrong_answer':
      case 'tle':
      case 'compile_error':
      case 'runtime_error':
        return <XCircle size={20} className="text-danger" />;
      case 'pending':
      case 'running':
        return <RefreshCw size={20} className="animate-spin text-info" />;
      default:
        return <HelpCircle size={20} className="text-muted" />;
    }
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

  return (
    <div className="workspace-container fade-in">
      <div className="workspace-header flex justify-between items-center">
        <div className="flex items-center gap-4">
          <a href={question ? `#test/${question.test_id}` : '#dashboard'} className="workspace-back">
            <ArrowLeft size={18} />
          </a>
          {question && <h2 className="workspace-title">{question.title}</h2>}
        </div>

        <div className="flex items-center gap-4">
          <div className="language-tabs">
            {(['python', 'javascript', 'cpp', 'java'] as const).map((lang) => (
              <button
                key={lang}
                className={`lang-tab-btn ${language === lang ? 'active' : ''}`}
                onClick={() => handleLanguageChange(lang)}
                disabled={submitting}
              >
                {lang === 'cpp' ? 'C++' : lang.toUpperCase()}
              </button>
            ))}
          </div>

          <button 
            onClick={handleSubmit} 
            className="btn btn-primary btn-sm submit-btn" 
            disabled={submitting || !code.trim()}
          >
            {submitting ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
            <span>Submit Solution</span>
          </button>
        </div>
      </div>

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
        <div className="workspace-body">
          {/* Left Panel: Description */}
          <div className="workspace-panel description-panel">
            <div className="panel-header">
              <h3>Problem Description</h3>
            </div>
            <div className="panel-content scrollable">
              <div className="question-content-html">
                {question.description.split('\n').map((para, i) => (
                  <p key={i} className="mb-4">{para}</p>
                ))}
              </div>

              {exampleTestCases.length > 0 && (
                <div className="example-cases-container mt-6">
                  <h4 className="mb-3">Visible Test Cases</h4>
                  {exampleTestCases.map((tc, index) => (
                    <div key={tc.id} className="example-case card mb-3">
                      <div className="example-case-header">Example {index + 1}</div>
                      <div className="example-case-body">
                        <div className="io-block">
                          <span className="io-label">Input:</span>
                          <pre>{tc.input_data}</pre>
                        </div>
                        <div className="io-block mt-2">
                          <span className="io-label">Expected Output:</span>
                          <pre>{tc.output_data}</pre>
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
            <div className="code-editor-wrapper">
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
            <div className="console-panel">
              <div className="console-header flex justify-between items-center">
                <span>Submission Output</span>
                {submissionStatus && (
                  <div className={`console-status-badge badge ${getStatusClass(submissionStatus)}`}>
                    {getStatusIcon(submissionStatus)}
                    <span>{getStatusText(submissionStatus)}</span>
                  </div>
                )}
              </div>
              <div className="console-content scrollable">
                {!submissionStatus && (
                  <p className="console-placeholder">Your output results will show here once you submit.</p>
                )}
                {submissionStatus && (
                  <div className="console-result">
                    <p className="result-time text-xs text-muted">
                      Submitted at: {new Date().toLocaleTimeString()}
                    </p>
                    
                    {submissionStatus === 'accepted' && (
                      <div className="result-success-alert flex items-center gap-2 mt-2">
                        <CheckCircle className="text-success" size={24} />
                        <div>
                          <h4 className="text-success">Accepted</h4>
                          <p className="text-secondary text-sm">All test cases passed successfully!</p>
                        </div>
                      </div>
                    )}

                    {['wrong_answer', 'tle', 'compile_error', 'runtime_error'].includes(submissionStatus) && (
                      <div className="result-failure-alert flex items-center gap-2 mt-2">
                        <XCircle className="text-danger" size={24} />
                        <div>
                          <h4 className="text-danger">{getStatusText(submissionStatus)}</h4>
                          <p className="text-secondary text-sm">Your code did not pass verification. Refactor and try again.</p>
                        </div>
                      </div>
                    )}

                    {['pending', 'running'].includes(submissionStatus) && (
                      <div className="flex items-center gap-2 mt-2">
                        <RefreshCw className="animate-spin text-info" size={20} />
                        <span>Judging solution on sandbox virtual machine...</span>
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
