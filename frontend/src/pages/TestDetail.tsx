import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type { TestWithQuestions, User } from '../api';
import { getErrorMessage } from '../errors';
import { useContestCountdown } from '../contestTime';
import {
  AlertCircle,
  ArrowLeft,
  ChevronRight,
  Clock,
  Code,
  LockKeyhole,
  Play,
  Trophy,
} from 'lucide-react';

interface TestDetailProps {
  testId: number;
  user: User | null;
}

export const TestDetail: React.FC<TestDetailProps> = ({ testId, user }) => {
  const [test, setTest] = useState<TestWithQuestions | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [finishArmed, setFinishArmed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTest = useCallback(async () => {
    setError(null);
    try {
      setTest(await api.getTest(testId));
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not load this contest.'));
    } finally {
      setLoading(false);
    }
  }, [testId]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => void loadTest());
    return () => window.cancelAnimationFrame(frame);
  }, [loadTest]);

  useEffect(() => {
    const sync = () => void loadTest();
    window.addEventListener('focus', sync);
    const interval = window.setInterval(sync, 30_000);
    return () => {
      window.removeEventListener('focus', sync);
      window.clearInterval(interval);
    };
  }, [loadTest]);

  const handleExpire = useCallback(() => {
    void loadTest();
  }, [loadTest]);
  const countdown = useContestCountdown(test?.attempt, handleExpire);

  const start = async () => {
    setActionLoading(true);
    setError(null);
    try {
      await api.startAttempt(testId);
      await loadTest();
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not start this contest.'));
    } finally {
      setActionLoading(false);
    }
  };

  const finish = async () => {
    if (!test?.attempt) return;
    if (!finishArmed) {
      setFinishArmed(true);
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await api.finishAttempt(test.attempt.id);
      setFinishArmed(false);
      await loadTest();
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not finish this contest.'));
    } finally {
      setActionLoading(false);
    }
  };

  const isAdmin = user?.role === 'admin';
  const isLocked = test?.access_state === 'locked';
  const isTimed = test?.access_state === 'timed';
  const isPractice = test?.access_state === 'practice';

  return (
    <div className="test-detail-container container fade-in">
      <a href="#contests" className="btn btn-secondary btn-sm mb-4">
        <ArrowLeft size={16} aria-hidden="true" />
        Back to contests
      </a>

      {loading && (
        <div className="test-layout" aria-label="Loading contest" aria-busy="true">
          <div className="card contest-detail-skeleton">
            <div className="skeleton skeleton-title" />
            <div className="skeleton skeleton-copy" />
            <div className="skeleton skeleton-action" />
          </div>
          <div className="problem-list-skeleton card">
            {Array.from({ length: 6 }).map((_, index) => <div className="skeleton skeleton-row" key={index} />)}
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} aria-hidden="true" />
          <div>
            <h2>Contest unavailable</h2>
            <p className="text-sm">{error}</p>
            <button type="button" className="btn btn-secondary btn-sm mt-4" onClick={() => void loadTest()}>
              Try again
            </button>
          </div>
        </div>
      )}

      {!loading && test && (
        <div className="test-layout">
          <aside className="test-info-sidebar card">
            <div className="contest-status-row">
              <span className={`attempt-state attempt-${test.attempt?.status || (isAdmin ? 'admin' : 'not_started')}`}>
                {isAdmin ? 'administrator preview' : (test.attempt?.status || 'not started').replace('_', ' ')}
              </span>
            </div>
            <h1 className="contest-title">{test.title}</h1>
            <p className="contest-desc text-secondary">{test.description}</p>

            <div className="contest-meta">
              <div className="meta-item">
                <Clock size={16} aria-hidden="true" />
                <span>{test.duration} minutes</span>
              </div>
              <div className="meta-item">
                <Code size={16} aria-hidden="true" />
                <span>{test.question_count} problems</span>
              </div>
            </div>

            {isTimed && test.attempt && (
              <>
                <div className="contest-countdown" aria-live="polite">
                  <span>Time remaining</span>
                  <strong>{countdown.formatted}</strong>
                </div>
                <button
                  type="button"
                  className={finishArmed ? 'btn btn-danger btn-block' : 'btn btn-secondary btn-block'}
                  onClick={() => void finish()}
                  disabled={actionLoading}
                >
                  {finishArmed ? 'Confirm finish' : 'Finish contest'}
                </button>
                {finishArmed && (
                  <button type="button" className="btn btn-secondary btn-block" onClick={() => setFinishArmed(false)}>
                    Keep solving
                  </button>
                )}
              </>
            )}

            {isLocked && (
              <div className="contest-start-panel">
                <LockKeyhole size={24} aria-hidden="true" />
                <div>
                  <strong>Problems are locked</strong>
                  <p>Your personal timer begins when you start. You get one scored attempt.</p>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={() => void start()}
                  disabled={actionLoading}
                  aria-busy={actionLoading}
                >
                  {actionLoading ? <div className="premium-spinner sm" aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
                  Start contest
                </button>
              </div>
            )}

            {isPractice && test.attempt && (
              <div className="contest-result-card">
                <Trophy size={22} aria-hidden="true" />
                <div>
                  <span>{test.attempt.status === 'expired' ? 'Time expired' : 'Scored attempt finished'}</span>
                  <strong>{test.attempt.score} / {test.question_count} solved</strong>
                  <p>Practice is now unlimited and does not change your score.</p>
                </div>
              </div>
            )}

            {isAdmin && (
              <div className="view-only-note">
                Administrator view only — solving and submissions are disabled.
              </div>
            )}

            {isAdmin && test.created_by === user?.id && (
              <div className="admin-quick-actions border-t pt-4">
                <a href={`#admin?test_id=${test.id}`} className="btn btn-primary btn-block">
                  Add question or test cases
                </a>
              </div>
            )}
          </aside>

          <section className="test-questions-panel" aria-labelledby="contest-problems-title">
            <div className="contest-problems-heading">
              <div>
                <h2 id="contest-problems-title">Contest problems</h2>
                <p className="text-secondary text-sm">
                  {isLocked ? 'Start the contest to reveal the problem set.' : isPractice ? 'Practice mode — take your time.' : 'Solve in any order.'}
                </p>
              </div>
            </div>

            {isLocked ? (
              <div className="locked-problem-list card">
                {Array.from({ length: test.question_count }).map((_, index) => (
                  <div className="locked-problem-row" key={index}>
                    <span>{index + 1}</span>
                    <div className="locked-problem-line" />
                    <LockKeyhole size={16} aria-hidden="true" />
                  </div>
                ))}
              </div>
            ) : test.questions.length === 0 ? (
              <div className="empty-questions card empty-state">
                <Code size={40} className="text-muted mb-4" aria-hidden="true" />
                <h3>No problems added</h3>
                <p className="text-secondary">The contest creator has not added problems yet.</p>
              </div>
            ) : (
              <div className="questions-list">
                {test.questions.map((question, index) => (
                  <a
                    key={question.id}
                    href={`#question/${question.id}`}
                    className="question-row card card-hover"
                  >
                    <div className="question-row-main">
                      <div className="question-index">{index + 1}</div>
                      <div>
                        <div className="question-title-line">
                          <h3 className="question-title">{question.title}</h3>
                          <span className={`problem-difficulty-badge ${question.difficulty}`}>{question.difficulty}</span>
                        </div>
                        <p className="question-desc text-secondary text-xs">{question.description}</p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-muted" aria-hidden="true" />
                  </a>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};
