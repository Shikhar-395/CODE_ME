const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  username: string;
  role: 'user' | 'admin';
}

export interface SignInRequest {
  username: string;
  password: string;
  role: User['role'];
}

export interface SignUpRequest {
  name: string;
  username: string;
  password: string;
  role: User['role'];
}

export interface Test {
  id: number;
  title: string;
  description: string;
  duration: number; // in minutes
  created_by: number;
  question_count: number;
  attempt: Attempt | null;
  access_state: 'locked' | 'timed' | 'practice' | 'admin' | 'preview';
}

export interface Question {
  id: number;
  title: string;
  description: string;
  test_id: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface TestCase {
  id: number;
  input_data: string;
  output_data: string;
  is_hidden: boolean;
  question_id: number;
}

export interface TestWithQuestions extends Test {
  questions: Question[];
}

export interface QuestionDetail extends Question {
  test_cases: TestCase[];
  contest_title: string;
  contest_duration: number;
  attempt: Attempt | null;
  access_state: 'timed' | 'practice' | 'admin';
}

export interface Attempt {
  id: number;
  test_id: number;
  user_id: number;
  score: number;
  solved_count: number;
  status: 'not_started' | 'active' | 'completed' | 'expired';
  started_at: string;
  expires_at: string;
  submitted_at: string | null;
  server_time: string;
}

export interface Submission {
  id: number;
  code: string;
  language: 'cpp' | 'python' | 'java' | 'javascript';
  status: 'pending' | 'running' | 'accepted' | 'wrong_answer' | 'tle' | 'compile_error' | 'runtime_error';
  kind: 'run' | 'submit';
  user_id: number;
  question_id: number;
  attempt_id: number | null;
  created_at: string;
}

export interface SubmissionHistoryItem {
  id: number;
  question_id: number;
  question_title: string;
  test_id: number;
  contest_title: string;
  language: Submission['language'];
  status: Submission['status'];
  mode: 'timed' | 'practice';
  created_at: string;
}

export interface SubmissionHistoryResponse {
  items: SubmissionHistoryItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// Global configurations for fetch
const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const url = `${API_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // essential for session cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<T>;
};

export const api = {
  // Authentication
  getMe: () => request<User>('/me'),
  
  signIn: (data: SignInRequest) => request<User>('/signin', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  signUp: (data: SignUpRequest) => request<User>('/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  logout: () => request<{ detail: string }>('/logout', {
    method: 'POST',
  }),

  // Tests
  listTests: () => request<Test[]>('/tests'),

  listAdminTests: () => request<TestWithQuestions[]>('/admin/tests'),
  
  getTest: (testId: number) => request<TestWithQuestions>(`/tests/${testId}`),

  startAttempt: (testId: number) => request<Attempt>(`/tests/${testId}/attempts/start`, {
    method: 'POST',
  }),

  getAttempt: (testId: number) => request<Attempt | null>(`/tests/${testId}/attempt`),

  finishAttempt: (attemptId: number) => request<Attempt>(`/attempts/${attemptId}/finish`, {
    method: 'POST',
  }),
  
  createTest: (data: { title: string; description: string; duration: number }) => request<Test>('/create-test', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Questions
  getQuestion: (questionId: number) => request<QuestionDetail>(`/questions/${questionId}`),
  
  createQuestion: (data: { test_id: number; title: string; description: string }) => request<Question>('/create-question', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Test cases
  addTestCase: (data: { question_id: number; input_data: string; output_data: string; is_hidden: boolean }) => request<TestCase>('/add-testcase', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Submissions
  submitCode: (data: { question_id: number; code: string; language: string }) => request<Submission>('/submission', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  runCode: (data: { question_id: number; code: string; language: string }) => request<Submission>('/executions/run', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  getSubmission: (submissionId: number) => request<Submission>(`/submissions/${submissionId}`),

  listSubmissions: (page = 1, pageSize = 20) =>
    request<SubmissionHistoryResponse>(`/submissions?page=${page}&page_size=${pageSize}`),

  // WebSocket URL
  getWebSocketUrl: (submissionId: number) => {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Clean api host
    const apiHost = API_URL.replace(/^https?:\/\//, '');
    return `${wsProto}//${apiHost}/ws/${submissionId}`;
  }
};
