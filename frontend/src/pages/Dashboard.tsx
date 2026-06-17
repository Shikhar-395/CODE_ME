import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { Test, User } from '../api';
import { getErrorMessage } from '../errors';
import { Clock, Plus, BookOpen, AlertCircle, RefreshCw } from 'lucide-react';

interface DashboardProps {
  user: User | null;
}

export const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTests = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listTests();
      setTests(data);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to fetch tests.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;

    api.listTests()
      .then((data) => {
        if (!ignore) setTests(data);
      })
      .catch((err) => {
        if (!ignore) setError(getErrorMessage(err, 'Failed to fetch tests.'));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="dashboard-container container fade-in">
      <div className="dashboard-header flex justify-between items-center mb-6">
        <div>
          <h1>Available Contests</h1>
          <p className="text-secondary text-sm">Select a test to solve the coding challenges within the time limit.</p>
        </div>

        <div className="flex gap-2">
          <button onClick={fetchTests} className="btn btn-secondary btn-sm" title="Refresh">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
          {user && user.role === 'admin' && (
            <a href="#admin" className="btn btn-primary btn-sm">
              <Plus size={16} />
              <span>Create Test</span>
            </a>
          )}
        </div>
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
            <h3>Error fetching tests</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && tests.length === 0 && (
        <div className="empty-state card">
          <BookOpen size={48} className="text-muted mb-4" />
          <h2>No Tests Available</h2>
          <p className="text-secondary mb-4">There are currently no active tests. Check back later!</p>
          {user && user.role === 'admin' && (
            <a href="#admin" className="btn btn-primary">
              Create the first Test
            </a>
          )}
        </div>
      )}

      {!loading && !error && tests.length > 0 && (
        <div className="tests-grid grid">
          {tests.map((test) => (
            <div key={test.id} className="test-card card card-hover">
              <div className="test-card-body">
                <h3 className="test-title">{test.title}</h3>
                <p className="test-desc text-secondary">{test.description}</p>
              </div>
              <div className="test-card-footer flex justify-between items-center">
                <span className="test-duration flex items-center gap-2 text-muted text-sm">
                  <Clock size={16} />
                  <span>{test.duration} mins</span>
                </span>
                <a href={`#test/${test.id}`} className="btn btn-primary btn-sm">
                  Solve Now
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
