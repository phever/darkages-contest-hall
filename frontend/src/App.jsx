import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import './index.css';
import api from './api';
import Board from './Board';
import HowToEnter from './HowToEnter';
import Login from './Login';
import InvitePage from './InvitePage';
import AcceptInvite from './AcceptInvite';

// Non-sensitive hint so we only probe /me when a session likely exists.
const HINT_KEY = 'auth_hint';

function App() {
  const [user, setUser] = useState(null);
  const isLoggedIn = !!user;
  const isChancellor = user?.role === 'admin';

  const refreshUser = useCallback(async () => {
    try {
      const res = await api.get('auth/me/');
      setUser(res.data);
      localStorage.setItem(HINT_KEY, '1');
      return res.data;
    } catch {
      setUser(null);
      localStorage.removeItem(HINT_KEY);
      return null;
    }
  }, []);

  useEffect(() => {
    if (localStorage.getItem(HINT_KEY)) {
      refreshUser();
    } else {
      api.get('auth/csrf/').catch(() => {});
    }
  }, [refreshUser]);

  const handleLogout = async () => {
    try { await api.post('auth/logout/'); } catch { /* ignore */ }
    setUser(null);
    localStorage.removeItem(HINT_KEY);
  };

  return (
    <Router>
      <div className="app-container">
        <header className="header">
          <Link to="/" className="brand">
            <img src="/8231.png" alt="" className="header-logo" />
            <h1>Contest Hall</h1>
          </Link>
          <nav>
            <Link to="/">Board</Link>
            <Link to="/how-to-enter">How to Enter</Link>
            {isChancellor && <Link to="/invite">Invite Nobles</Link>}
            {isLoggedIn ? (
              <>
                {user.in_game_name && <span className="muted">{user.in_game_name}</span>}
                <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
              </>
            ) : (
              <Link to="/login" className="btn btn-primary">Login</Link>
            )}
          </nav>
        </header>

        <main>
          <Routes>
            <Route path="/" element={<Board user={user} />} />
            <Route path="/how-to-enter" element={<HowToEnter user={user} />} />
            <Route path="/invite" element={<InvitePage user={user} />} />
            <Route path="/accept-invite" element={<AcceptInvite onLogin={refreshUser} />} />
            <Route path="/login" element={<Login onLogin={refreshUser} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
