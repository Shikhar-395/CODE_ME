const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  username: string;
  role: 'user' | 'admin';
}

export interface SignInRequest {
  username: string;
  password: string;
}

export interface SignUpRequest extends SignInRequest {
  name: string;
  role: User['role'];
}

export interface Test {
  id: number;
  title: string;
  description: string;
  duration: number; // in minutes
  created_by: number;
}

export interface Question {
  id: number;
  title: string;
  description: string;
  test_id: number;
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
}

export interface Submission {
  id: number;
  code: string;
  language: 'cpp' | 'python' | 'java' | 'javascript';
  status: 'pending' | 'running' | 'accepted' | 'wrong_answer' | 'tle' | 'compile_error' | 'runtime_error';
  user_id: number;
  question_id: number;
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
  
  getTest: (testId: number) => request<TestWithQuestions>(`/tests/${testId}`),
  
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

  getSubmission: (submissionId: number) => request<Submission>(`/submissions/${submissionId}`),

  // WebSocket URL
  getWebSocketUrl: (submissionId: number) => {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Clean api host
    const apiHost = API_URL.replace(/^https?:\/\//, '');
    return `${wsProto}//${apiHost}/ws/${submissionId}`;
  }
};
