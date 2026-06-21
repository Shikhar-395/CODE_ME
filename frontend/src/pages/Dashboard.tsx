import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { Question, User } from '../api';
import { getErrorMessage } from '../errors';
import { Plus, AlertCircle, Play, Search } from 'lucide-react';

interface DashboardProps {
  user: User | null;
}

interface DashboardQuestion extends Question {
  contestTitle: string;
  accessState: 'timed' | 'practice' | 'admin' | 'preview' | 'locked';
}

export const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [questions, setQuestions] = useState<DashboardQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search and Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    let ignore = false;

    const loadData = async () => {
      try {
        const testsData = await api.listTests();
        if (ignore) return;

        const testsWithQuestions = await Promise.all(
          testsData.map(t => api.getTest(t.id).catch(() => null))
        );
        if (ignore) return;

        const allQuestions: DashboardQuestion[] = [];
        testsWithQuestions.forEach((test) => {
          if (test) {
            test.questions.forEach((question) => {
              allQuestions.push({
                ...question,
                contestTitle: test.title,
                accessState: test.access_state,
              });
            });
          }
        });
        setQuestions(allQuestions);
      } catch (err) {
        if (!ignore) setError(getErrorMessage(err, 'Failed to load data.'));
      } finally {
        if (!ignore) setLoading(false);
      }
    };

    loadData();

    return () => {
      ignore = true;
    };
  }, []);

  // Filter questions by search query
  const filteredQuestions = questions.filter(q => 
    q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    q.id.toString().includes(searchQuery)
  );

  // Pagination calculations
  const totalPages = Math.max(1, Math.ceil(filteredQuestions.length / itemsPerPage));
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentQuestions = filteredQuestions.slice(indexOfFirstItem, indexOfLastItem);

  return (
    <div className="dashboard-container container fade-in" style={{ padding: '32px 24px', maxWidth: '1440px' }}>
      
      {/* Dashboard Top Header */}
      <div className="dashboard-header flex justify-between items-center mb-6">
        <div>
          <h1 style={{ fontSize: '28px' }}>Dashboard</h1>
        </div>

        <div className="flex gap-2">
          {user && user.role === 'admin' && (
            <a href="#admin" className="btn btn-primary btn-sm">
              <Plus size={16} />
              <span>Create Contest</span>
            </a>
          )}
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
        <div className="problems-table-container" aria-busy="true" aria-label="Loading problems">
          <div className="problems-table-header">
            <div className="skeleton skeleton-input" />
          </div>
          <div className="problem-list-skeleton">
            {Array.from({ length: 5 }, (_, index) => (
              <div className="skeleton skeleton-row" key={index} />
            ))}
          </div>
        </div>
      )}

      {!loading && !error && (
        <div>
          <div className="problems-table-container">
            {/* Search Header */}
            <div className="problems-table-header">
              <div className="input-with-icon" style={{ maxWidth: '300px', flex: '1' }}>
                <Search size={16} className="input-icon" />
                <input
                  type="text"
                  className="form-input"
                  placeholder="Search ID or Title..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  style={{ width: '100%', paddingLeft: '40px' }}
                />
              </div>
            </div>

            {/* Problems Table */}
            {filteredQuestions.length === 0 ? (
              <div className="empty-table-state text-center text-secondary">
                <p className="mb-4">
                  {questions.length === 0
                    ? 'Start a contest to unlock its problems.'
                    : 'No problems match your search.'}
                </p>
                {questions.length === 0 && <a href="#contests" className="btn btn-primary">Browse contests</a>}
              </div>
            ) : (
              <table className="problems-table">
                <thead>
                  <tr>
                    <th style={{ width: '60px' }}>#</th>
                    <th>Title</th>
                    <th style={{ width: '150px' }}>Difficulty</th>
                    <th style={{ width: '150px' }}>Status</th>
                    <th style={{ width: '120px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {currentQuestions.map((q, idx) => {
                    return (
                      <tr key={q.id}>
                        <td style={{ color: 'var(--text-muted)', fontWeight: '500' }}>
                          {indexOfFirstItem + idx + 1}
                        </td>
                        <td className="problem-title-cell">
                          <a href={`#question/${q.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                            {q.title}
                          </a>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px', fontWeight: 'normal' }}>
                            ({q.contestTitle})
                          </span>
                        </td>
                        <td>
                          <span className={`problem-difficulty-badge ${q.difficulty}`}>
                            {q.difficulty}
                          </span>
                        </td>
                        <td>
                          <span className={`attempt-state ${q.accessState === 'timed' ? 'attempt-active' : 'attempt-completed'}`}>
                            {q.accessState === 'timed' ? 'Timed' : 'Practice'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <a href={`#question/${q.id}`} className="play-btn" title="Solve problem">
                            <Play size={14} fill="currentColor" />
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination controls */}
          {filteredQuestions.length > itemsPerPage && (
            <div className="flex justify-between items-center mt-6 text-sm text-muted">
              <span>
                Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredQuestions.length)} of {filteredQuestions.length}
              </span>
              <div className="flex gap-2">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Prev
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    className={`btn btn-sm ${currentPage === page ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </button>
                ))}
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
