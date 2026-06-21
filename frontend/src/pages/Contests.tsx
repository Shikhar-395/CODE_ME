import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type { Test, User } from '../api';
import { getErrorMessage } from '../errors';
import { useContestCountdown } from '../contestTime';
import { AlertCircle, BookOpen, Clock, Play } from 'lucide-react';

interface ContestsProps {
  user: User | null;
}

interface ContestCardProps {
  test: Test;
  isAdmin: boolean;
  onStart: (test: Test) => Promise<void>;
  starting: boolean;
  onRefresh: () => void;
}

const ContestCard: React.FC<ContestCardProps> = ({
  test,
  isAdmin,
  onStart,
  starting,
  onRefresh,
}) => {
  const expire = useCallback(() => onRefresh(), [onRefresh]);
  const countdown = useContestCountdown(test.attempt, expire);
  const status = test.attempt?.status || 'not_started';

  const action = () => {
    if (isAdmin) {
      return <a href={`#test/${test.id}`} className="btn btn-secondary">View Contest</a>;
    }
    if (status === 'not_started') {
      return (
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void onStart(test)}
          disabled={starting}
          aria-busy={starting}
        >
          {starting ? <div className="premium-spinner sm" aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
          Start
        </button>
      );
    }
    if (status === 'active') {
      return <a href={`#test/${test.id}`} className="btn btn-primary">Resume</a>;
    }
    return <a href={`#test/${test.id}`} className="btn btn-secondary">{status === 'expired' ? 'Practice' : 'Results'}</a>;
  };

  return (
    <article className="test-card card card-hover">
      <div className="test-card-body">
        <div className="contest-card-heading">
          <h2 className="test-title">{test.title}</h2>
          {!isAdmin && <span className={`attempt-state attempt-${status}`}>{status.replace('_', ' ')}</span>}
        </div>
        <p className="test-desc text-secondary">{test.description}</p>
        <div className="contest-card-stats">
          <span><BookOpen size={15} aria-hidden="true" /> {test.question_count} problems</span>
          <span><Clock size={15} aria-hidden="true" /> {test.duration} minutes</span>
        </div>
      </div>
      <footer className="test-card-footer">
        {status === 'active' && (
          <div className="contest-countdown compact" aria-live="polite">
            <span>Time remaining</span>
            <strong>{countdown.formatted}</strong>
          </div>
        )}
        {action()}
      </footer>
    </article>
  );
};

export const Contests: React.FC<ContestsProps> = ({ user }) => {
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startingId, setStartingId] = useState<number | null>(null);

  const loadTests = useCallback(async () => {
    setError(null);
    try {
      setTests(await api.listTests());
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not load contests.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => void loadTests());
    return () => window.cancelAnimationFrame(frame);
  }, [loadTests]);

  useEffect(() => {
    const sync = () => void loadTests();
    window.addEventListener('focus', sync);
    const interval = window.setInterval(sync, 30_000);
    return () => {
      window.removeEventListener('focus', sync);
      window.clearInterval(interval);
    };
  }, [loadTests]);

  const handleStart = async (test: Test) => {
    setStartingId(test.id);
    setError(null);
    try {
      await api.startAttempt(test.id);
      window.location.hash = `#test/${test.id}`;
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not start this contest.'));
      setStartingId(null);
    }
  };

  return (
    <div className="dashboard-container container fade-in">
      <header className="dashboard-header">
        <h1>{user?.role === 'admin' ? 'Contests' : 'Contest room'}</h1>
        <p className="text-secondary text-sm">
          {user?.role === 'admin'
            ? 'Review every contest without participating.'
            : 'Start once, race the clock, then return for unlimited practice.'}
        </p>
      </header>

      {error && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} aria-hidden="true" />
          <div>
            <h2>Could not load contests</h2>
            <p className="text-sm">{error}</p>
            <button type="button" className="btn btn-secondary btn-sm mt-4" onClick={() => void loadTests()}>
              Try again
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="tests-grid grid" aria-label="Loading contests" aria-busy="true">
          {Array.from({ length: 6 }).map((_, index) => (
            <div className="card contest-card-skeleton" key={index}>
              <div className="skeleton skeleton-title" />
              <div className="skeleton skeleton-copy" />
              <div className="skeleton skeleton-copy short" />
              <div className="skeleton skeleton-action" />
            </div>
          ))}
        </div>
      )}

      {!loading && !error && tests.length === 0 && (
        <div className="empty-state card">
          <BookOpen size={48} className="text-muted mb-4" aria-hidden="true" />
          <h2>No contests yet</h2>
          <p className="text-secondary">New contests will appear here when an administrator publishes them.</p>
        </div>
      )}

      {!loading && tests.length > 0 && (
        <div className="tests-grid grid">
          {tests.map((test) => (
            <ContestCard
              key={test.id}
              test={test}
              isAdmin={user?.role === 'admin'}
              onStart={handleStart}
              starting={startingId === test.id}
              onRefresh={loadTests}
            />
          ))}
        </div>
      )}
    </div>
  );
};
