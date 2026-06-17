import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { TestWithQuestions, User } from '../api';
import { getErrorMessage } from '../errors';
import { ArrowLeft, Clock, Code, AlertCircle, RefreshCw, ChevronRight } from 'lucide-react';

interface TestDetailProps {
  testId: number;
  user: User | null;
}

export const TestDetail: React.FC<TestDetailProps> = ({ testId, user }) => {
  const [test, setTest] = useState<TestWithQuestions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    api.getTest(testId)
      .then((data) => {
        if (!ignore) setTest(data);
      })
      .catch((err) => {
        if (!ignore) setError(getErrorMessage(err, 'Failed to load test details.'));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [testId]);

  return (
    <div className="test-detail-container container fade-in">
      <div className="mb-4">
        <a href="#dashboard" className="btn btn-secondary btn-sm">
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </a>
      </div>

      {loading && (
        <div className="flex justify-center items-center py-12">
          <RefreshCw size={36} className="animate-spin text-muted" />
        </div>
      )}

      {error && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} />
          <div>
            <h3>Error loading contest</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && test && (
        <div className="test-layout">
          <div className="test-info-sidebar card">
            <h2 className="contest-title">{test.title}</h2>
            <p className="contest-desc text-secondary mb-4">{test.description}</p>
            
            <div className="contest-meta">
              <div className="meta-item flex items-center gap-2 text-secondary text-sm">
                <Clock size={16} className="text-muted" />
                <span>Time Limit: <strong>{test.duration} minutes</strong></span>
              </div>
            </div>

            {user && user.role === 'admin' && (
              <div className="admin-quick-actions mt-4 pt-4 border-t">
                <p className="text-xs text-muted mb-2 font-semibold uppercase">Admin Actions</p>
                <a href={`#admin?test_id=${test.id}`} className="btn btn-primary btn-sm btn-block">
                  Add Question / Testcases
                </a>
              </div>
            )}
          </div>

          <div className="test-questions-panel">
            <div className="flex justify-between items-center mb-4">
              <h3>Contest Problems ({test.questions?.length || 0})</h3>
            </div>

            {test.questions && test.questions.length === 0 ? (
              <div className="empty-questions card text-center py-12">
                <Code size={40} className="text-muted mb-2" />
                <h4>No Questions Added Yet</h4>
                <p className="text-secondary text-sm mb-4">Questions will appear here once the creator adds them.</p>
                {user && user.role === 'admin' && (
                  <a href={`#admin?test_id=${test.id}`} className="btn btn-primary btn-sm">
                    Add first Question
                  </a>
                )}
              </div>
            ) : (
              <div className="questions-list">
                {test.questions.map((question, index) => (
                  <a 
                    key={question.id} 
                    href={`#question/${question.id}`} 
                    className="question-row card card-hover flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="question-index flex justify-center items-center">
                        {index + 1}
                      </div>
                      <div>
                        <h4 className="question-title">{question.title}</h4>
                        <p className="question-desc text-secondary text-xs">{question.description}</p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-muted" />
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
