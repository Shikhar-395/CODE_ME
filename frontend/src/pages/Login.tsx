import React, { useState } from 'react';
import { api } from '../api';
import type { User } from '../api';
import { getErrorMessage } from '../errors';
import { KeyRound, Mail, AlertTriangle, Loader2 } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: (user: User) => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please fill in all fields');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const user = await api.signIn({ username, password });
      onLoginSuccess(user);
      window.location.hash = '#dashboard';
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Wrong credentials. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container fade-in">
      <div className="auth-card card">
        <div className="auth-header">
          <h2>Welcome Back</h2>
          <p className="text-secondary text-sm">Solve code challenges on our modern platform</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label">Username</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                type="text"
                className="form-input"
                placeholder="enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-with-icon">
              <KeyRound size={16} className="input-icon" />
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Signing In...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <span className="text-muted text-sm">Don't have an account? </span>
          <a href="#signup" className="auth-link text-sm">Sign Up</a>
        </div>
      </div>
    </div>
  );
};
