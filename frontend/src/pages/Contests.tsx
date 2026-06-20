import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { Test, User } from '../api';
import { getErrorMessage } from '../errors';
import { Clock, BookOpen, AlertCircle, RefreshCw } from 'lucide-react';

interface ContestsProps {
  user: User | null;
}

export const Contests: React.FC<ContestsProps> = ({ user }) => {
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    let ignore = false;

    api.listTests()
      .then((testsData) => {
        if (!ignore) setTests(testsData);
      })
      .catch((err: unknown) => {
        if (!ignore) setError(getErrorMessage(err, 'Failed to fetch contests.'));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="dashboard-container container fade-in" style={{ padding: '32px 24px', maxWidth: '1440px' }}>
      
      {/* Contests Top Header */}
      <div className="dashboard-header flex justify-between items-center mb-6">
        <div>
          <h1 style={{ fontSize: '28px' }}>{user?.role === 'admin' ? 'Contests' : 'Active Contests'}</h1>
          <p className="text-secondary text-sm">
            {user?.role === 'admin'
              ? 'Review every contest without participating or submitting solutions.'
              : 'Participate in running contests and challenge yourself.'}
          </p>
        </div>

      </div>

      {error && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} />
          <div>
            <h3>Error fetching data</h3>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex justify-center items-center py-12">
          <RefreshCw size={36} className="animate-spin text-muted" />
        </div>
      )}

      {!loading && !error && (
        <div>
          {tests.length === 0 ? (
            <div className="empty-state card text-center">
              <BookOpen size={48} className="text-muted mb-4 mx-auto" />
              <h2>No Contests Available</h2>
              <p className="text-secondary mb-4">There are currently no active tests. Check back later!</p>
            </div>
          ) : (
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
                      {user?.role === 'admin' ? 'View Contest' : 'Solve Now'}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
