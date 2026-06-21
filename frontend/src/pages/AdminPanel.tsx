import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { TestWithQuestions, Question, User } from '../api';
import { getErrorMessage } from '../errors';
import { Plus, ShieldAlert, FileQuestion, ListPlus, CheckCircle, AlertCircle, RefreshCw, Trophy } from 'lucide-react';

interface AdminPanelProps {
  user: User | null;
  initialTestId?: number;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ user, initialTestId }) => {
  const [activeTab, setActiveTab] = useState<'test' | 'question' | 'testcase'>('test');
  
  // Data lists
  const [tests, setTests] = useState<TestWithQuestions[]>([]);
  
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
  const [qDifficulty, setQDifficulty] = useState<Question['difficulty']>('easy');
  const [tc1Input, setTc1Input] = useState('5\n1 2 3 4 5\n3');
  const [tc1Output, setTc1Output] = useState('3');
  const [tc2Input, setTc2Input] = useState('0\n0');
  const [tc2Output, setTc2Output] = useState('-1');

  // Form states - Add Testcase
  const [tcTestId, setTcTestId] = useState<number>(0);
  const [selectedQId, setSelectedQId] = useState<number>(0);
  const [tcInput, setTcInput] = useState('');
  const [tcOutput, setTcOutput] = useState('');
  const [tcHidden, setTcHidden] = useState(true);

  // Initial load
  useEffect(() => {
    let ignore = false;

    api.listAdminTests()
      .then((allTests) => {
        if (ignore) return;

        setTests(allTests);

        if (initialTestId && allTests.some((test) => test.id === initialTestId)) {
          setSelectedTestId(initialTestId);
          setTcTestId(initialTestId);
          setSelectedQId(
            allTests.find((test) => test.id === initialTestId)?.questions[0]?.id || 0,
          );
          setActiveTab('question');
        } else if (allTests.length > 0) {
          setSelectedTestId(allTests[0].id);
          setTcTestId(allTests[0].id);
          setSelectedQId(allTests[0].questions[0]?.id || 0);
        }
      })
      .catch((err) => console.error('Failed to load admin lists', err));

    return () => {
      ignore = true;
    };
  }, [initialTestId]);

  const questions = tests.find((test) => test.id === tcTestId)?.questions || [];

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
      
      // Reset form, select the new contest, and continue into problem creation.
      setTestTitle('');
      setTestDesc('');
      setTestDuration(60);
      const allTests = await api.listAdminTests();
      setTests(allTests);
      setSelectedTestId(newTest.id);
      setTcTestId(newTest.id);
      setSelectedQId(0);
      setActiveTab('question');
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
        description: qDesc,
        difficulty: qDifficulty,
      });
      
      // Submit visible test case
      if (tc1Input.trim() && tc1Output.trim()) {
        await api.addTestCase({
          question_id: newQ.id,
          input_data: tc1Input,
          output_data: tc1Output,
          is_hidden: false
        });
      }

      // Submit hidden test case
      if (tc2Input.trim() && tc2Output.trim()) {
        await api.addTestCase({
          question_id: newQ.id,
          input_data: tc2Input,
          output_data: tc2Output,
          is_hidden: true
        });
      }

      showFeedback(`Successfully created problem "${newQ.title}" with test cases!`, null);
      
      // Reset form
      setQTitle('');
      setQDesc('');
      setQDifficulty('easy');
      setTc1Input('5\n1 2 3 4 5\n3');
      setTc1Output('3');
      setTc2Input('0\n0');
      setTc2Output('-1');
      const allTests = await api.listAdminTests();
      setTests(allTests);
      setTcTestId(selectedTestId);
      setSelectedQId(newQ.id);
      setActiveTab('testcase');
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
          <h1>Creator Workspace</h1>
          <p className="text-secondary text-sm">Create problems for your contests and manage their test cases.</p>
        </div>
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
            <Trophy size={18} />
            <span>Create Contest</span>
          </button>

          <button
            className={`admin-tab-link ${activeTab === 'question' ? 'active' : ''}`}
            onClick={() => setActiveTab('question')}
          >
            <FileQuestion size={18} />
            <span>Create Problem</span>
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
                  <label className="form-label" htmlFor="contest-title">Contest Title</label>
                  <input
                    id="contest-title"
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
                  <label className="form-label" htmlFor="contest-description">Description</label>
                  <textarea
                    id="contest-description"
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
                  <label className="form-label" htmlFor="contest-duration">Duration (in minutes)</label>
                  <input
                    id="contest-duration"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="form-input"
                    placeholder="60"
                    value={testDuration}
                    onChange={e => setTestDuration(Number.parseInt(e.target.value, 10) || 0)}
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
              {tests.length === 0 ? (
                <div className="admin-prerequisite text-center">
                  <FileQuestion size={48} className="text-muted mb-4 mx-auto" aria-hidden="true" />
                  <h3>Create a contest first</h3>
                  <p className="text-secondary mb-6">
                    Every problem belongs to one of your contests. Create a contest, then return here to add its first problem.
                  </p>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => setActiveTab('test')}
                  >
                    <Plus size={16} aria-hidden="true" />
                    <span>Create Contest</span>
                  </button>
                </div>
              ) : (
                <>
                  <h3 className="mb-6" style={{ fontSize: '20px', fontWeight: '700' }}>Create New Problem</h3>
                  <form onSubmit={handleCreateQuestion} style={{ maxWidth: '800px' }}>
                    {/* Form Details */}
                    <div className="flex flex-col gap-4">
                      <div className="form-group">
                        <label className="form-label" htmlFor="problem-contest">Select Contest</label>
                        <select
                          id="problem-contest"
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
                        <label className="form-label" htmlFor="problem-title">Problem Title</label>
                        <input
                          id="problem-title"
                          type="text"
                          className="form-input"
                          placeholder="e.g. Reverse Linked List III"
                          value={qTitle}
                          onChange={e => setQTitle(e.target.value)}
                          required
                          disabled={loading}
                        />
                      </div>

                      <div className="flex gap-4">
                        <div className="form-group" style={{ flex: 1 }}>
                          <label className="form-label" htmlFor="problem-difficulty">Difficulty</label>
                          <select
                            id="problem-difficulty"
                            className="form-input select-input"
                            value={qDifficulty}
                            onChange={(event) => setQDifficulty(event.target.value as Question['difficulty'])}
                            disabled={loading}
                          >
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                          </select>
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                          <label className="form-label">Category Tags</label>
                          <input
                            type="text"
                            className="form-input"
                            placeholder="e.g. dp, graph, tree"
                            disabled
                            style={{ background: 'var(--bg-main)', opacity: 0.8 }}
                          />
                        </div>
                      </div>

                      <div className="form-group">
                        <label className="form-label" htmlFor="problem-description">Problem Description (Markdown)</label>
                        <textarea
                          id="problem-description"
                          className="form-input text-area-input"
                          rows={8}
                          placeholder="Write problem description here..."
                          value={qDesc}
                          onChange={e => setQDesc(e.target.value)}
                          required
                          disabled={loading}
                          style={{ minHeight: '180px' }}
                        />
                      </div>

                      <div className="flex gap-2 mt-4">
                        <button type="button" className="btn btn-secondary btn-sm" style={{ width: '110px' }} onClick={() => showFeedback('Draft saved successfully (mocked)!', null)}>
                          <span>Save Draft</span>
                        </button>
                        <button type="submit" className="btn btn-primary btn-sm" style={{ width: '110px', backgroundColor: 'var(--color-primary)', color: 'var(--bg-main)' }} disabled={loading || selectedTestId === 0 || !qTitle || !qDesc}>
                          {loading ? <RefreshCw className="animate-spin" size={14} /> : null}
                          <span>Publish</span>
                        </button>
                      </div>
                    </div>
                  </form>
                </>
              )}
            </div>
          )}

          {activeTab === 'testcase' && (
            <div className="fade-in">
              <h3 className="mb-4">Add Test Case to Problem</h3>
              <form onSubmit={handleAddTestCase}>
                <div className="form-group">
                  <label className="form-label" htmlFor="testcase-contest">Select Contest</label>
                  <select
                    id="testcase-contest"
                    className="form-input select-input"
                    value={tcTestId}
                    onChange={(event) => {
                      const nextTestId = Number.parseInt(event.target.value, 10) || 0;
                      const nextQuestions = tests.find((test) => test.id === nextTestId)?.questions || [];
                      setTcTestId(nextTestId);
                      setSelectedQId(nextQuestions[0]?.id || 0);
                    }}
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
                  <label className="form-label" htmlFor="testcase-problem">Select Problem</label>
                  <select
                    id="testcase-problem"
                    className="form-input select-input"
                    value={selectedQId}
                    onChange={event => setSelectedQId(Number.parseInt(event.target.value, 10) || 0)}
                    required
                    disabled={loading || questions.length === 0}
                  >
                    {questions.length === 0 ? (
                      <option value={0}>-- No problems in this contest --</option>
                    ) : (
                      <>
                        <option value={0} disabled>-- Select a Problem --</option>
                        {questions.map(q => (
                          <option key={q.id} value={q.id}>{q.title}</option>
                        ))}
                      </>
                    )}
                  </select>
                  {questions.length === 0 && (
                    <p className="text-muted text-xs mt-1">
                      Create a problem in this contest before adding test cases.
                    </p>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="testcase-input">Standard Input Data</label>
                  <textarea
                    id="testcase-input"
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
                  <label className="form-label" htmlFor="testcase-output">Expected Standard Output Data</label>
                  <textarea
                    id="testcase-output"
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
