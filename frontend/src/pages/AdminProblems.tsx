import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Eye, FileQuestion, Plus, RefreshCw, Search } from 'lucide-react';
import { api } from '../api';
import type { Question, User } from '../api';
import { getErrorMessage } from '../errors';

interface AdminProblemsProps {
  user: User | null;
}

interface OwnedProblem extends Question {
  contestTitle: string;
}

const ITEMS_PER_PAGE = 10;

export const AdminProblems: React.FC<AdminProblemsProps> = ({ user }) => {
  const [problems, setProblems] = useState<OwnedProblem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProblems = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const tests = await api.listAdminTests();
      setProblems(
        tests.flatMap((test) =>
          test.questions.map((question) => ({
            ...question,
            contestTitle: test.title,
          })),
        ),
      );
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not load your problems.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.role !== 'admin') return;

    let ignore = false;

    api.listAdminTests()
      .then((tests) => {
        if (ignore) return;

        setProblems(
          tests.flatMap((test) =>
            test.questions.map((question) => ({
              ...question,
              contestTitle: test.title,
            })),
          ),
        );
      })
      .catch((err: unknown) => {
        if (!ignore) setError(getErrorMessage(err, 'Could not load your problems.'));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [user?.role]);

  const filteredProblems = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return problems;

    return problems.filter(
      (problem) =>
        problem.title.toLowerCase().includes(query) ||
        problem.contestTitle.toLowerCase().includes(query) ||
        problem.id.toString().includes(query),
    );
  }, [problems, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredProblems.length / ITEMS_PER_PAGE));
  const safePage = Math.min(currentPage, totalPages);
  const firstItemIndex = (safePage - 1) * ITEMS_PER_PAGE;
  const currentProblems = filteredProblems.slice(
    firstItemIndex,
    firstItemIndex + ITEMS_PER_PAGE,
  );

  if (!user || user.role !== 'admin') {
    return (
      <div className="container py-12 text-center fade-in">
        <div className="card max-w-md mx-auto py-12">
          <AlertCircle size={44} className="text-danger mb-4 mx-auto" aria-hidden="true" />
          <h2>Administrator access required</h2>
          <p className="text-secondary mb-6">This page is reserved for problem creators.</p>
          <a href="#dashboard" className="btn btn-primary">Go to Dashboard</a>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container container fade-in admin-problems-page">
      <div className="dashboard-header flex justify-between items-center mb-6">
        <div>
          <h1>Your Problems</h1>
          <p className="text-secondary text-sm">
            Problems from contests created by {user.username}.
          </p>
        </div>
        <a href="#admin" className="btn btn-primary btn-sm">
          <Plus size={16} aria-hidden="true" />
          <span>Create Problem</span>
        </a>
      </div>

      {error && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} aria-hidden="true" />
          <div className="flex-1">
            <h3>Could not load your problems</h3>
            <p className="text-sm">{error}</p>
          </div>
          <button type="button" className="btn btn-secondary btn-sm" onClick={loadProblems}>
            <RefreshCw size={15} aria-hidden="true" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {loading && (
        <div className="problems-table-container" aria-busy="true" aria-label="Loading your problems">
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

      {!loading && !error && problems.length === 0 && (
        <div className="empty-state card text-center">
          <FileQuestion size={48} className="text-muted mb-4 mx-auto" aria-hidden="true" />
          <h2>No problems created yet</h2>
          <p className="text-secondary mb-4">
            Create your first contest problem and it will appear here.
          </p>
          <a href="#admin" className="btn btn-primary">Create Problem</a>
        </div>
      )}

      {!loading && !error && problems.length > 0 && (
        <>
          <div className="problems-table-container">
            <div className="problems-table-header">
              <div className="input-with-icon admin-problem-search">
                <Search size={16} className="input-icon" aria-hidden="true" />
                <label className="sr-only" htmlFor="admin-problem-search">Search your problems</label>
                <input
                  id="admin-problem-search"
                  type="search"
                  className="form-input"
                  placeholder="Search by ID, title, or contest"
                  value={searchQuery}
                  onChange={(event) => {
                    setSearchQuery(event.target.value);
                    setCurrentPage(1);
                  }}
                />
              </div>
            </div>

            {filteredProblems.length === 0 ? (
              <div className="empty-table-state text-center">
                <Search size={36} className="text-muted mb-3 mx-auto" aria-hidden="true" />
                <h3>No matching problems</h3>
                <p className="text-secondary text-sm mb-4">
                  Try a different title, contest, or problem ID.
                </p>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setSearchQuery('')}
                >
                  Clear search
                </button>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="problems-table">
                  <thead>
                    <tr>
                      <th scope="col">ID</th>
                      <th scope="col">Title</th>
                      <th scope="col">Contest</th>
                      <th scope="col" className="table-action-column">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentProblems.map((problem) => (
                      <tr key={problem.id}>
                        <td className="text-muted">#{problem.id}</td>
                        <td className="problem-title-cell">{problem.title}</td>
                        <td className="text-secondary">{problem.contestTitle}</td>
                        <td className="table-action-column">
                          <a
                            href={`#question/${problem.id}`}
                            className="btn btn-secondary btn-sm"
                            aria-label={`View ${problem.title}`}
                          >
                            <Eye size={15} aria-hidden="true" />
                            <span>View</span>
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {filteredProblems.length > ITEMS_PER_PAGE && (
            <div className="pagination-row">
              <span className="text-sm text-muted">
                Showing {firstItemIndex + 1}–
                {Math.min(firstItemIndex + ITEMS_PER_PAGE, filteredProblems.length)} of{' '}
                {filteredProblems.length}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                  disabled={safePage === 1}
                >
                  Previous
                </button>
                <span className="pagination-status" aria-live="polite">
                  Page {safePage} of {totalPages}
                </span>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                  disabled={safePage === totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
