import React, { useState } from 'react';
import { api } from '../api';
import type { User } from '../api';
import { getErrorMessage } from '../errors';
import { KeyRound, Mail, User as UserIcon, ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';

interface SignupProps {
  onSignupSuccess: (user: User) => void;
}

export const Signup: React.FC<SignupProps> = ({ onSignupSuccess }) => {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<User['role']>('user');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !username || !password) {
      setError('Please fill in all fields');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      // Create user
      await api.signUp({ name, username, password, role });
      
      // Auto-login after signup
      const loggedInUser = await api.signIn({ username, password, role });
      onSignupSuccess(loggedInUser);
      window.location.hash = loggedInUser.role === 'admin' ? '#admin' : '#dashboard';
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Registration failed. Try another username.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container fade-in">
      <div className="auth-card card">
        <div className="auth-header">
          <h2>Create Account</h2>
          <p className="text-secondary text-sm">Join to create tests, write code, and judge submissions</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label" htmlFor="signup-name">Full Name</label>
            <div className="input-with-icon">
              <UserIcon size={16} className="input-icon" />
              <input
                id="signup-name"
                type="text"
                className="form-input"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                autoComplete="name"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-username">Username</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                id="signup-username"
                type="text"
                className="form-input"
                placeholder="john_doe"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                autoComplete="username"
                spellCheck={false}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-password">Password</label>
            <div className="input-with-icon">
              <KeyRound size={16} className="input-icon" />
              <input
                id="signup-password"
                type="password"
                className="form-input"
                placeholder="min 4 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                autoComplete="new-password"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-role">Create account as</label>
            <div className="input-with-icon">
              <ShieldCheck size={16} className="input-icon" />
              <select
                id="signup-role"
                className="form-input select-input"
                value={role}
                onChange={(e) => setRole(e.target.value as User['role'])}
                disabled={loading}
              >
                <option value="user">User (Solver)</option>
                <option value="admin">Administrator (Test Creator)</option>
              </select>
            </div>
            <p className="text-muted text-xs mt-1">
              Administrators can create tests, questions, and test cases.
            </p>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Create {role === 'admin' ? 'Administrator' : 'User'} Account</span>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <span className="text-muted text-sm">Already have an account? </span>
          <a href="#login" className="auth-link text-sm">Sign In</a>
        </div>
      </div>
    </div>
  );
};
