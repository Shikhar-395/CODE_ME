import React from 'react';
import { api } from '../api';
import type { User } from '../api';
import { Terminal, LogOut, LayoutDashboard, ShieldAlert } from 'lucide-react';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
  currentHash: string;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout, currentHash }) => {
  const handleLogout = async () => {
    try {
      await api.logout();
      onLogout();
      window.location.hash = '#login';
    } catch (err) {
      console.error('Failed to logout', err);
    }
  };

  return (
    <header className="navbar-container">
      <div className="navbar-content">
        <a href="#dashboard" className="navbar-brand">
          <Terminal size={22} className="navbar-logo-icon" />
          <span className="navbar-brand-text">LeetCode <span className="brand-accent">Lite</span></span>
        </a>

        {user ? (
          <div className="navbar-actions">
            <a 
              href="#dashboard" 
              className={`navbar-link ${currentHash === '#dashboard' || currentHash === '' ? 'active' : ''}`}
            >
              <LayoutDashboard size={16} />
              <span>Dashboard</span>
            </a>

            {user.role === 'admin' && (
              <a 
                href="#admin" 
                className={`navbar-link ${currentHash === '#admin' ? 'active' : ''}`}
              >
                <ShieldAlert size={16} />
                <span>Admin Panel</span>
              </a>
            )}

            <div className="navbar-user-info">
              <span className="navbar-username">{user.username}</span>
              <span className={`role-badge role-${user.role}`}>{user.role}</span>
            </div>

            <button onClick={handleLogout} className="btn btn-secondary btn-sm" title="Log Out">
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <div className="navbar-actions">
            <a href="#login" className="btn btn-secondary btn-sm">Sign In</a>
            <a href="#signup" className="btn btn-primary btn-sm">Sign Up</a>
          </div>
        )}
      </div>
    </header>
  );
};
