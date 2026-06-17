import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { Test, Question, User } from '../api';
import { getErrorMessage } from '../errors';
import { Plus, ShieldAlert, Award, FileQuestion, ListPlus, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

interface AdminPanelProps {
  user: User | null;
  initialTestId?: number;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ user, initialTestId }) => {
  const [activeTab, setActiveTab] = useState<'test' | 'question' | 'testcase'>('test');
  
  // Data lists
  const [tests, setTests] = useState<Test[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form states - Create Test
  const [testTitle, setTestTitle] = useState('');
  const [testDesc, setTestDesc] = useState('');
  const [testDuration, setTestDuration] = useState<number>(60);

  // Form states - Create Question
  const [selectedTestId, setSelectedTestId] = useState<number>(0);
  const [qTitle, setQTitle] = useState('');
  const [qDesc, setQDesc] = useState('');

  // Form states - Add Testcase
  const [tcTestId, setTcTestId] = useState<number>(0);
  const [selectedQId, setSelectedQId] = useState<number>(0);
  const [tcInput, setTcInput] = useState('');
  const [tcOutput, setTcOutput] = useState('');
  const [tcHidden, setTcHidden] = useState(true);

  // Initial load
  const loadInitialData = async () => {
    try {
      const allTests = await api.listTests();
      setTests(allTests);
      
      // If we have an initial test ID (passed from quick-link), select it and switch to question tab
      if (initialTestId) {
        setSelectedTestId(initialTestId);
        setTcTestId(initialTestId);
        setActiveTab('question');
      } else if (allTests.length > 0) {
        setSelectedTestId(allTests[0].id);
        setTcTestId(allTests[0].id);
      }
    } catch (err) {
      console.error('Failed to load admin lists', err);
    }
  };

  useEffect(() => {
    let ignore = false;

    api.listTests()
      .then((allTests) => {
        if (ignore) return;

        setTests(allTests);

        if (initialTestId) {
          setSelectedTestId(initialTestId);
          setTcTestId(initialTestId);
          setActiveTab('question');
        } else if (allTests.length > 0) {
          setSelectedTestId(allTests[0].id);
          setTcTestId(allTests[0].id);
        }
      })
      .catch((err) => console.error('Failed to load admin lists', err));

    return () => {
      ignore = true;
    };
  }, [initialTestId]);

  // Load questions when test selection changes for Test Case creation
  useEffect(() => {
    let ignore = false;

    if (tcTestId) {
      api.getTest(tcTestId).then(data => {
        if (ignore) return;

        setQuestions(data.questions || []);
        if (data.questions && data.questions.length > 0) {
          setSelectedQId(data.questions[0].id);
        } else {
          setSelectedQId(0);
        }
      }).catch(err => console.error(err));
    } else {
      Promise.resolve().then(() => {
        if (ignore) return;

        setQuestions([]);
        setSelectedQId(0);
      });
    }

    return () => {
      ignore = true;
    };
  }, [tcTestId]);

  const showFeedback = (success: string | null, error: string | null) => {
    setSuccessMsg(success);
    setErrorMsg(error);
    setTimeout(() => {
      setSuccessMsg(null);
      setErrorMsg(null);
    }, 5000);
  };

  // Submit handlers
  const handleCreateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testTitle.trim() || !testDesc.trim() || testDuration <= 0) return;
    
    setLoading(true);
    try {
      const newTest = await api.createTest({
        title: testTitle,
        description: testDesc,
        duration: testDuration
      });
      showFeedback(`Successfully created test "${newTest.title}"!`, null);
      
      // Reset form & reload list
      setTestTitle('');
      setTestDesc('');
      setTestDuration(60);
      loadInitialData();
    } catch (err: unknown) {
      showFeedback(null, getErrorMessage(err, 'Failed to create test.'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTestId === 0 || !qTitle.trim() || !qDesc.trim()) return;

    setLoading(true);
    try {
      const newQ = await api.createQuestion({
        test_id: selectedTestId,
        title: qTitle,
        description: qDesc
      });
      showFeedback(`Successfully added question "${newQ.title}"!`, null);
      
      // Reset form
      setQTitle('');
      setQDesc('');
      loadInitialData(); // reload tests to ensure we get questions refreshed
    } catch (err: unknown) {
      showFeedback(null, getErrorMessage(err, 'Failed to create question.'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddTestCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedQId === 0 || !tcInput.trim() || !tcOutput.trim()) return;

    setLoading(true);
    try {
      await api.addTestCase({
        question_id: selectedQId,
        input_data: tcInput,
        output_data: tcOutput,
        is_hidden: tcHidden
      });
      showFeedback('Successfully added test case!', null);
      
      // Reset form
      setTcInput('');
      setTcOutput('');
    } catch (err: unknown) {
      showFeedback(null, getErrorMessage(err, 'Failed to add testcase.'));
    } finally {
      setLoading(false);
    }
  };

  if (!user || user.role !== 'admin') {
    return (
      <div className="container py-12 text-center fade-in">
        <div className="card max-w-md mx-auto py-12">
          <ShieldAlert size={48} className="text-danger mb-4 mx-auto" />
          <h2>Access Denied</h2>
          <p className="text-secondary mb-6">You must be an administrator to view this panel.</p>
          <a href="#dashboard" className="btn btn-primary">Go to Dashboard</a>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container container fade-in">
      <div className="admin-header flex justify-between items-center mb-6">
        <div>
          <h1>Admin Dashboard</h1>
          <p className="text-secondary text-sm">Configure contests, code challenges, and test cases.</p>
        </div>
        <Award className="text-primary" size={32} />
      </div>

      {successMsg && (
        <div className="alert alert-success mb-6">
          <CheckCircle size={20} className="text-success" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} className="text-danger" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="admin-layout">
        {/* Sidebar Nav Tabs */}
        <div className="admin-tabs-sidebar card">
          <button 
            className={`admin-tab-link ${activeTab === 'test' ? 'active' : ''}`}
            onClick={() => setActiveTab('test')}
          >
            <Award size={18} />
            <span>Create Test</span>
          </button>
          
          <button 
            className={`admin-tab-link ${activeTab === 'question' ? 'active' : ''}`}
            onClick={() => setActiveTab('question')}
            disabled={tests.length === 0}
          >
            <FileQuestion size={18} />
            <span>Add Question</span>
          </button>
          
          <button 
            className={`admin-tab-link ${activeTab === 'testcase' ? 'active' : ''}`}
            onClick={() => setActiveTab('testcase')}
            disabled={tests.length === 0}
          >
            <ListPlus size={18} />
            <span>Add Testcase</span>
          </button>
        </div>

        {/* Tab Forms Panel */}
        <div className="admin-forms-panel card">
          
          {activeTab === 'test' && (
            <div className="fade-in">
              <h3 className="mb-4">Create New Contest</h3>
              <form onSubmit={handleCreateTest}>
                <div className="form-group">
                  <label className="form-label">Contest Title</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Dynamic Programming Warmup"
                    value={testTitle}
                    onChange={e => setTestTitle(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-input text-area-input"
                    rows={4}
                    placeholder="e.g. A contest containing fundamental DP algorithms challenges."
                    value={testDesc}
                    onChange={e => setTestDesc(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Duration (in minutes)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="60"
                    value={testDuration}
                    onChange={e => setTestDuration(parseInt(e.target.value) || 0)}
                    min={1}
                    required
                    disabled={loading}
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading || !testTitle || !testDesc}>
                  {loading ? <RefreshCw className="animate-spin" size={16} /> : <Plus size={16} />}
                  <span>Create Contest</span>
                </button>
              </form>
            </div>
          )}

          {activeTab === 'question' && (
            <div className="fade-in">
              <h3 className="mb-4">Add Problem to Contest</h3>
              <form onSubmit={handleCreateQuestion}>
                <div className="form-group">
                  <label className="form-label">Select Contest</label>
                  <select
                    className="form-input select-input"
                    value={selectedTestId}
                    onChange={e => setSelectedTestId(parseInt(e.target.value) || 0)}
                    required
                    disabled={loading}
                  >
                    <option value={0} disabled>-- Select a Contest --</option>
                    {tests.map(t => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Problem Title</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Two Sum"
                    value={qTitle}
                    onChange={e => setQTitle(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Problem Description (supports markdown instructions)</label>
                  <textarea
                    className="form-input text-area-input"
                    rows={6}
                    placeholder="e.g. Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target..."
                    value={qDesc}
                    onChange={e => setQDesc(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading || selectedTestId === 0 || !qTitle || !qDesc}>
                  {loading ? <RefreshCw className="animate-spin" size={16} /> : <Plus size={16} />}
                  <span>Add Problem</span>
                </button>
              </form>
            </div>
          )}

          {activeTab === 'testcase' && (
            <div className="fade-in">
              <h3 className="mb-4">Add Test Case to Problem</h3>
              <form onSubmit={handleAddTestCase}>
                <div className="form-group">
                  <label className="form-label">Select Contest</label>
                  <select
                    className="form-input select-input"
                    value={tcTestId}
                    onChange={e => setTcTestId(parseInt(e.target.value) || 0)}
                    required
                    disabled={loading}
                  >
                    <option value={0} disabled>-- Select a Contest --</option>
                    {tests.map(t => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Select Problem</label>
                  <select
                    className="form-input select-input"
                    value={selectedQId}
                    onChange={e => setSelectedQId(parseInt(e.target.value) || 0)}
                    required
                    disabled={loading || questions.length === 0}
                  >
                    {questions.length === 0 ? (
                      <option value={0}>-- No Problems in this Contest --</option>
                    ) : (
                      <>
                        <option value={0} disabled>-- Select a Problem --</option>
                        {questions.map(q => (
                          <option key={q.id} value={q.id}>{q.title}</option>
                        ))}
                      </>
                    )}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Standard Input Data</label>
                  <textarea
                    className="form-input text-area-input"
                    rows={3}
                    placeholder="e.g. 2 7 11 15&#10;9"
                    value={tcInput}
                    onChange={e => setTcInput(e.target.value)}
                    required
                    disabled={loading || selectedQId === 0}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Expected Standard Output Data</label>
                  <textarea
                    className="form-input text-area-input"
                    rows={3}
                    placeholder="e.g. 0 1"
                    value={tcOutput}
                    onChange={e => setTcOutput(e.target.value)}
                    required
                    disabled={loading || selectedQId === 0}
                  />
                </div>

                <div className="form-group flex-row items-center gap-2 mb-4">
                  <input
                    type="checkbox"
                    id="tc-hidden"
                    checked={tcHidden}
                    onChange={e => setTcHidden(e.target.checked)}
                    disabled={loading || selectedQId === 0}
                  />
                  <label htmlFor="tc-hidden" className="form-label cursor-pointer select-none">
                    Is Hidden Testcase? (Hidden cases will not be visible to users)
                  </label>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading || selectedQId === 0 || !tcInput || !tcOutput}>
                  {loading ? <RefreshCw className="animate-spin" size={16} /> : <Plus size={16} />}
                  <span>Add Test Case</span>
                </button>
              </form>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
