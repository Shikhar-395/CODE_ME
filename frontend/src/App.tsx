import { useEffect, useState } from 'react';
import { api } from './api';
import type { User } from './api';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { Contests } from './pages/Contests';
import { AdminProblems } from './pages/AdminProblems';
import { TestDetail } from './pages/TestDetail';
import { QuestionDetail } from './pages/QuestionDetail';
import { AdminPanel } from './pages/AdminPanel';
import { Loader2 } from 'lucide-react';

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);

  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return hash;
}

function App() {
  const hash = useHashRoute();
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Authenticate user on load
  useEffect(() => {
    const checkUser = async () => {
      try {
        const u = await api.getMe();
        setUser(u);
        // If logged in and on auth pages, redirect to dashboard
        if (window.location.hash === '#login' || window.location.hash === '#signup') {
          window.location.hash = u.role === 'admin' ? '#admin' : '#dashboard';
        } else if (
          u.role === 'admin' &&
          (window.location.hash === '' ||
            window.location.hash === '#' ||
            window.location.hash === '#dashboard')
        ) {
          window.location.hash = '#admin';
        }
      } catch {
        setUser(null);
        // If not logged in and not on signup/login, redirect to login
        if (window.location.hash !== '#login' && window.location.hash !== '#signup') {
          window.location.hash = '#login';
        }
      } finally {
        setCheckingAuth(false);
      }
    };
    checkUser();
  }, [hash]);

  useEffect(() => {
    if (!checkingAuth && !user && hash !== '#login' && hash !== '#signup') {
      window.location.hash = '#login';
    }
  }, [checkingAuth, hash, user]);

  if (checkingAuth) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-main gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-secondary text-sm">Securing your workspace connection...</p>
      </div>
    );
  }

  // Parse routing from hash
  const parseRoute = () => {
    const cleanHash = hash.replace(/^#/, '');

    if (cleanHash === 'login') return { route: 'login' };
    if (cleanHash === 'signup') return { route: 'signup' };
    if (cleanHash === 'admin') return { route: 'admin' };
    
    if (cleanHash.startsWith('admin?')) {
      const parts = cleanHash.split('?');
      const params = new URLSearchParams(parts[1] || '');
      const testId = parseInt(params.get('test_id') || '0');
      return { route: 'admin', testId };
    }
    
    if (cleanHash.startsWith('test/')) {
      const testId = parseInt(cleanHash.substring(5));
      return { route: 'test', testId };
    }
    
    if (cleanHash.startsWith('question/')) {
      const questionId = parseInt(cleanHash.substring(9));
      return { route: 'question', questionId };
    }

    if (cleanHash === 'contests') return { route: 'contests' };
    if (cleanHash === 'problems') return { route: 'problems' };

    return { route: user?.role === 'admin' ? 'admin' : 'dashboard' };
  };

  const parsed = parseRoute();

  const handleLoginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    setUser(null);
  };

  const renderPage = () => {
    // Force login if not authenticated (except for login/signup pages)
    if (!user && parsed.route !== 'login' && parsed.route !== 'signup') {
      return <Login onLoginSuccess={handleLoginSuccess} />;
    }

    switch (parsed.route) {
      case 'login':
        return <Login onLoginSuccess={handleLoginSuccess} />;
      case 'signup':
        return <Signup onSignupSuccess={handleLoginSuccess} />;
      case 'admin':
        return <AdminPanel user={user} initialTestId={parsed.testId} />;
      case 'test':
        return <TestDetail testId={parsed.testId!} user={user} />;
      case 'question':
        return <QuestionDetail questionId={parsed.questionId!} user={user} />;
      case 'contests':
        return <Contests user={user} />;
      case 'problems':
        return <AdminProblems user={user} />;
      case 'dashboard':
      default:
        return <Dashboard user={user} />;
    }
  };

  return (
    <>
      {parsed.route !== 'login' && parsed.route !== 'signup' && (
        <Navbar user={user} onLogout={handleLogout} currentHash={hash} />
      )}
      <main className="flex-1 flex flex-col">
        {renderPage()}
      </main>
    </>
  );
}

export default App;
