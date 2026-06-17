import React, { useState } from 'react';
import { api } from '../api';
import type { User } from '../api';
import { getErrorMessage } from '../errors';
import { KeyRound, Mail, User as UserIcon, AlertTriangle, Loader2, Info } from 'lucide-react';

interface SignupProps {
  onSignupSuccess: (user: User) => void;
}

export const Signup: React.FC<SignupProps> = ({ onSignupSuccess }) => {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'user' | 'admin'>('user');
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
      const loggedInUser = await api.signIn({ username, password });
      onSignupSuccess(loggedInUser);
      window.location.hash = '#dashboard';
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
            <label className="form-label">Full Name</label>
            <div className="input-with-icon">
              <UserIcon size={16} className="input-icon" />
              <input
                type="text"
                className="form-input"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Username</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                type="text"
                className="form-input"
                placeholder="john_doe"
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
                placeholder="min 4 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Account Role</label>
            <select
              className="form-input select-input"
              value={role}
              onChange={(e) => setRole(e.target.value as 'user' | 'admin')}
              disabled={loading}
            >
              <option value="user">User (Solver)</option>
              <option value="admin">Admin (Test Creator)</option>
            </select>
            <p className="text-muted text-xs flex items-center gap-2 mt-1">
              <Info size={12} />
              <span>Admins can create tests, add questions and test cases.</span>
            </p>
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Register & Sign In</span>
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
