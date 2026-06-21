import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { api } from '../api';
import type { SubmissionHistoryResponse } from '../api';
import { getErrorMessage } from '../errors';

export const Submissions: React.FC = () => {
  const [data, setData] = useState<SubmissionHistoryResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await api.listSubmissions(page, 20));
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not load submission history.'));
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => void load());
    return () => window.cancelAnimationFrame(frame);
  }, [load]);

  return (
    <div className="dashboard-container container fade-in">
      <header className="dashboard-header">
        <h1>Submissions</h1>
        <p className="text-secondary text-sm">Full judge submissions from timed attempts and practice.</p>
      </header>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} aria-hidden="true" />
          <div>
            <h2>Could not load submissions</h2>
            <p className="text-sm">{error}</p>
            <button type="button" className="btn btn-secondary btn-sm mt-4" onClick={() => void load()}>Try again</button>
          </div>
        </div>
      )}

      {loading && (
        <div className="problems-table-container" aria-label="Loading submissions" aria-busy="true">
          <div className="problem-list-skeleton">
            {Array.from({ length: 8 }).map((_, index) => <div className="skeleton skeleton-row" key={index} />)}
          </div>
        </div>
      )}

      {!loading && !error && data?.items.length === 0 && (
        <div className="empty-state card">
          <FileText size={44} className="text-muted mb-4" aria-hidden="true" />
          <h2>No submissions yet</h2>
          <p className="text-secondary mb-4">Run examples freely, then submit a solution when it is ready for the full judge.</p>
          <a href="#contests" className="btn btn-primary">Choose a contest</a>
        </div>
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <>
          <div className="problems-table-container table-scroll">
            <table className="problems-table submissions-table">
              <thead>
                <tr>
                  <th>Result</th>
                  <th>Problem</th>
                  <th>Contest</th>
                  <th>Language</th>
                  <th>Mode</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((submission) => (
                  <tr key={submission.id}>
                    <td>
                      <span className={`submission-result status-${submission.status}`}>
                        {submission.status.replaceAll('_', ' ')}
                      </span>
                    </td>
                    <td><a href={`#question/${submission.question_id}`}>{submission.question_title}</a></td>
                    <td><a href={`#test/${submission.test_id}`}>{submission.contest_title}</a></td>
                    <td className="text-secondary">{submission.language}</td>
                    <td><span className={`attempt-state attempt-${submission.mode === 'timed' ? 'active' : 'completed'}`}>{submission.mode}</span></td>
                    <td className="text-secondary">{new Date(submission.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination-row">
            <span className="pagination-status">{data.total} submissions</span>
            <div className="flex gap-2">
              <button type="button" className="btn btn-secondary" onClick={() => setPage((value) => value - 1)} disabled={page <= 1}>
                Previous
              </button>
              <span className="pagination-status">Page {data.page} of {data.total_pages}</span>
              <button type="button" className="btn btn-secondary" onClick={() => setPage((value) => value + 1)} disabled={page >= data.total_pages}>
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {loading && <RefreshCw className="sr-only" aria-hidden="true" />}
    </div>
  );
};
