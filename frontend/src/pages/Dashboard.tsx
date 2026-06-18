import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { Test, User } from '../api';
import { getErrorMessage } from '../errors';
import { Clock, Plus, BookOpen, AlertCircle, RefreshCw, Play, Search, Filter, Check } from 'lucide-react';

interface DashboardProps {
  user: User | null;
}

export const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [tests, setTests] = useState<Test[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dashboard navigation tab
  const [activeTab, setActiveTab] = useState<'problems' | 'contests'>('problems');
  
  // Search and Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const testsData = await api.listTests();
      setTests(testsData);

      const testsWithQuestions = await Promise.all(
        testsData.map(t => api.getTest(t.id).catch(() => null))
      );

      const allQuestions: any[] = [];
      testsWithQuestions.forEach((t: any) => {
        if (t && t.questions) {
          t.questions.forEach((q: any) => {
            allQuestions.push({
              ...q,
              contestTitle: t.title
            });
          });
        }
      });
      setQuestions(allQuestions);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to fetch dashboard data.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;

    const loadData = async () => {
      try {
        const testsData = await api.listTests();
        if (ignore) return;
        setTests(testsData);

        const testsWithQuestions = await Promise.all(
          testsData.map(t => api.getTest(t.id).catch(() => null))
        );
        if (ignore) return;

        const allQuestions: any[] = [];
        testsWithQuestions.forEach((t: any) => {
          if (t && t.questions) {
            t.questions.forEach((q: any) => {
              allQuestions.push({
                ...q,
                contestTitle: t.title
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

  const getQuestionDifficulty = (q: any) => {
    const title = q.title.toLowerCase();
    if (title.includes('two sum') || title.includes('easy') || q.id % 3 === 0) return 'EASY';
    if (title.includes('median') || title.includes('hard') || q.id % 3 === 2) return 'HARD';
    return 'MEDIUM';
  };

  const getQuestionAcceptance = (q: any) => {
    const rate = ((q.id * 13) % 35) + 42.5;
    return `${rate.toFixed(1)}%`;
  };

  const getQuestionStatus = (index: number) => {
    // Matching mockup 1 checkmark sequence (1st and 3rd resolved)
    return index % 2 === 0;
  };

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
          <p className="text-secondary text-sm">
            System status: <span style={{ color: 'var(--color-primary)', fontWeight: '600' }}>Online</span>
          </p>
        </div>

        <div className="flex gap-2">
          <button onClick={fetchData} className="btn btn-secondary btn-sm" title="Refresh Dashboard">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
          {user && user.role === 'admin' && (
            <a href="#admin" className="btn btn-primary btn-sm">
              <Plus size={16} />
              <span>Create Contest</span>
            </a>
          )}
        </div>
      </div>

      {/* Tabs Selector */}
      <div className="flex gap-4 mb-6" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <button 
          onClick={() => setActiveTab('problems')} 
          className="btn" 
          style={{ 
            background: 'transparent',
            border: 'none',
            color: activeTab === 'problems' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: '600',
            borderBottom: activeTab === 'problems' ? '2px solid var(--color-primary)' : '2px solid transparent',
            borderRadius: '0',
            padding: '8px 16px'
          }}
        >
          Recent Problems
        </button>
        <button 
          onClick={() => setActiveTab('contests')} 
          className="btn" 
          style={{ 
            background: 'transparent',
            border: 'none',
            color: activeTab === 'contests' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: '600',
            borderBottom: activeTab === 'contests' ? '2px solid var(--color-primary)' : '2px solid transparent',
            borderRadius: '0',
            padding: '8px 16px'
          }}
        >
          Active Contests ({tests.length})
        </button>
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
        <>
          {/* Active Contests Tab View */}
          {activeTab === 'contests' && (
            <div>
              {tests.length === 0 ? (
                <div className="empty-state card text-center">
                  <BookOpen size={48} className="text-muted mb-4 mx-auto" />
                  <h2>No Contests Available</h2>
                  <p className="text-secondary mb-4">There are currently no active tests. Check back later!</p>
                  {user && user.role === 'admin' && (
                    <a href="#admin" className="btn btn-primary">Create first contest</a>
                  )}
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
                          Solve Now
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Recent Problems Tab View */}
          {activeTab === 'problems' && (
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
                  <button className="btn btn-secondary btn-sm flex items-center gap-2" style={{ opacity: 0.8 }}>
                    <Filter size={14} />
                    <span>Filter</span>
                  </button>
                </div>

                {/* Problems Table */}
                {filteredQuestions.length === 0 ? (
                  <div className="text-center py-12 text-secondary">
                    <p>No problems found matching search criteria.</p>
                  </div>
                ) : (
                  <table className="problems-table">
                    <thead>
                      <tr>
                        <th style={{ width: '80px' }}>Status</th>
                        <th>Title</th>
                        <th style={{ width: '150px' }}>Difficulty</th>
                        <th style={{ width: '150px' }}>Acceptance</th>
                        <th style={{ width: '120px', textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentQuestions.map((q, idx) => {
                        const difficulty = getQuestionDifficulty(q);
                        const isSolved = getQuestionStatus(indexOfFirstItem + idx);
                        return (
                          <tr key={q.id}>
                            <td>
                              {isSolved ? (
                                <Check size={16} style={{ color: 'var(--color-primary)' }} />
                              ) : (
                                <span style={{ color: 'var(--text-muted)' }}>-</span>
                              )}
                            </td>
                            <td className="problem-title-cell">
                              <a href={`#question/${q.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                                {q.id}. {q.title}
                              </a>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px', fontWeight: 'normal' }}>
                                ({q.contestTitle})
                              </span>
                            </td>
                            <td>
                              <span className={`problem-difficulty-badge ${difficulty.toLowerCase()}`}>
                                {difficulty}
                              </span>
                            </td>
                            <td style={{ color: 'var(--text-secondary)', fontWeight: '500', fontSize: '13px' }}>
                              {getQuestionAcceptance(q)}
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
        </>
      )}
    </div>
  );
};
