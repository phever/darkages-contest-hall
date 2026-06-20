import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import './index.css';
import api from './api';
import Board from './Board';
import SubmissionForm from './SubmissionForm';
import Login from './Login';

// Non-sensitive hint so we only probe /me when a session likely exists.
const HINT_KEY = 'auth_hint';

function App() {
  const [user, setUser] = useState(null);
  const isLoggedIn = !!user;

  // Confirm the session against the server (the token cookie is httpOnly).
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
      // Still bootstrap the CSRF cookie for anonymous actions.
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
          <Link to="/" style={{ textDecoration: 'none' }}>
            <h1>Contest Hall</h1>
          </Link>
          <nav>
            <Link to="/">Board</Link>
            <Link to="/submit">Submit</Link>
            {isLoggedIn ? (
              <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
            ) : (
              <Link to="/login" className="btn btn-primary">Login</Link>
            )}
          </nav>
        </header>

        <main>
          <Routes>
            <Route path="/" element={<Board isLoggedIn={isLoggedIn} />} />
            <Route path="/submit" element={<SubmissionForm />} />
            <Route path="/login" element={<Login onLogin={refreshUser} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
