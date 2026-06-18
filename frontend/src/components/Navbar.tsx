import React from 'react';
import { api } from '../api';
import type { User } from '../api';
import { Terminal, LogOut, LayoutDashboard, ShieldAlert, Plus, Trophy, Code2, Settings, FileText } from 'lucide-react';

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

  const isProblemsActive = currentHash.startsWith('#question/') || currentHash === '#problems';
  const isContestsActive = currentHash.startsWith('#test/') || currentHash === '#contests';
  const isDashboardActive = currentHash === '#dashboard' || currentHash === '' || currentHash === '#';
  const isAdminActive = currentHash.startsWith('#admin');

  return (
    <header className="navbar-container">
      <div className="navbar-content" style={{ maxWidth: '1440px', padding: '10px 24px' }}>
        <a href="#dashboard" className="navbar-brand" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0px' }}>
          <div className="flex items-center gap-2">
            <Terminal size={20} className="navbar-logo-icon" />
            <span className="navbar-brand-text" style={{ fontSize: '16px', letterSpacing: '0.05em' }}>
              CODE_<span className="brand-accent">EXEC</span>
            </span>
          </div>
          <span className="navbar-brand-subtitle">v2.0.4-stable</span>
        </a>

        {user && (
          <nav className="flex items-center gap-6" style={{ margin: '0 auto' }}>
            <a 
              href="#dashboard" 
              className={`navbar-link ${isDashboardActive ? 'active' : ''}`}
            >
              <LayoutDashboard size={15} />
              <span>Dashboard</span>
            </a>

            <a 
              href="#dashboard" 
              className={`navbar-link ${isProblemsActive ? 'active' : ''}`}
            >
              <Code2 size={15} />
              <span>Problems</span>
            </a>

            <a 
              href="#dashboard" 
              className={`navbar-link ${isContestsActive ? 'active' : ''}`}
            >
              <Trophy size={15} />
              <span>Contests</span>
            </a>

            <a 
              href="#leaderboard" 
              className={`navbar-link ${currentHash === '#leaderboard' ? 'active' : ''}`}
              onClick={(e) => e.preventDefault()}
            >
              <Trophy size={15} />
              <span>Leaderboard</span>
            </a>

            <a 
              href="#submissions" 
              className={`navbar-link ${currentHash === '#submissions' ? 'active' : ''}`}
              onClick={(e) => e.preventDefault()}
            >
              <FileText size={15} />
              <span>Submissions</span>
            </a>

            {user.role === 'admin' && (
              <a 
                href="#admin" 
                className={`navbar-link ${isAdminActive ? 'active' : ''}`}
              >
                <ShieldAlert size={15} />
                <span>Admin Panel</span>
              </a>
            )}

            <a 
              href="#settings" 
              className={`navbar-link ${currentHash === '#settings' ? 'active' : ''}`}
              onClick={(e) => e.preventDefault()}
            >
              <Settings size={15} />
              <span>Settings</span>
            </a>
          </nav>
        )}

        <div className="navbar-actions">
          {user ? (
            <>
              {user.role === 'admin' && (
                <a href="#admin" className="btn btn-primary btn-sm flex items-center gap-1">
                  <Plus size={14} />
                  <span>New Snippet</span>
                </a>
              )}

              <div className="navbar-user-info" style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '16px' }}>
                <span className="navbar-username" style={{ fontSize: '13px' }}>{user.username}</span>
                <span className={`role-badge role-${user.role}`} style={{ fontSize: '10px' }}>{user.role}</span>
              </div>

              <button onClick={handleLogout} className="btn btn-secondary btn-sm" title="Log Out" style={{ padding: '6px 10px' }}>
                <LogOut size={14} />
              </button>
            </>
          ) : (
            <div className="flex gap-2">
              <a href="#login" className="btn btn-secondary btn-sm">Sign In</a>
              <a href="#signup" className="btn btn-primary btn-sm">Sign Up</a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

