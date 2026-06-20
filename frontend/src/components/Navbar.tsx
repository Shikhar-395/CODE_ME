import React from 'react';
import { api } from '../api';
import type { User } from '../api';
import { LogOut, LayoutDashboard, FileText } from 'lucide-react';

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

  const isAdmin = user?.role === 'admin';
  const isContestsActive = currentHash.startsWith('#test/') || currentHash === '#contests';
  const isDashboardActive = currentHash === '#dashboard' || currentHash === '' || currentHash === '#';
  const isCreateProblemActive = currentHash.startsWith('#admin');

  return (
    <header className="navbar-container">
      <div className="navbar-content" style={{ maxWidth: '1440px', padding: '10px 24px' }}>
        <a href={isAdmin ? '#admin' : '#dashboard'} className="navbar-brand">
          <span className="navbar-brand-text" style={{ fontSize: '16px', letterSpacing: '0.05em' }}>
            CODE_<span className="brand-accent">ME</span>
          </span>
        </a>

        {user && (
          <nav className="flex items-center gap-6" style={{ margin: '0 auto' }}>
            {isAdmin ? (
              <>
                <a
                  href="#admin"
                  className={`navbar-link ${isCreateProblemActive ? 'active' : ''}`}
                >
                  <span>Workshop</span>
                </a>

                <a
                  href="#contests"
                  className={`navbar-link ${isContestsActive ? 'active' : ''}`}
                >
                  <span>Contests</span>
                </a>
              </>
            ) : (
              <>
                <a
                  href="#dashboard"
                  className={`navbar-link ${isDashboardActive ? 'active' : ''}`}
                >
                  <LayoutDashboard size={15} aria-hidden="true" />
                  <span>Dashboard</span>
                </a>

                <a
                  href="#contests"
                  className={`navbar-link ${isContestsActive ? 'active' : ''}`}
                >
                  <span>Contests</span>
                </a>

                <a
                  href="#submissions"
                  className={`navbar-link ${currentHash === '#submissions' ? 'active' : ''}`}
                  onClick={(e) => e.preventDefault()}
                >
                  <FileText size={15} aria-hidden="true" />
                  <span>Submissions</span>
                </a>
              </>
            )}
          </nav>
        )}

        <div className="navbar-actions">
          {user ? (
            <>
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
