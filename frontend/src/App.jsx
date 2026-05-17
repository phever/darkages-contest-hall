import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from './api';
import './index.css';
import Login from './Login';
import ContestDetails from './ContestDetails';

function Home() {
  const [contests, setContests] = useState([]);

  useEffect(() => {
    api.get('contests/')
      .then(res => setContests(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h2>Active Contests</h2>
      <div className="grid">
        {contests.length > 0 ? contests.map(contest => (
          <div key={contest.id} className="card">
            <h3>{contest.title}</h3>
            <p>{contest.description}</p>
            <div style={{ marginTop: '1rem' }}>
              <span className={`badge ${contest.is_active ? 'badge-active' : 'badge-inactive'}`}>
                {contest.is_active ? 'Active' : 'Ended'}
              </span>
            </div>
            <Link to={`/contest/${contest.id}`} className="btn btn-primary" style={{ marginTop: '1.5rem', width: '100%' }}>
              View Entries
            </Link>
          </div>
        )) : (
          <p>No contests found. Check back later!</p>
        )}
      </div>
    </div>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
  };

  return (
    <Router>
      <div className="app-container">
        <header className="header">
          <h1>Contest Hall</h1>
          <nav>
            <Link to="/">Home</Link>
            {isLoggedIn ? (
              <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
            ) : (
              <Link to="/login" className="btn btn-primary">Login</Link>
            )}
          </nav>
        </header>

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/contest/:id" element={<ContestDetails isLoggedIn={isLoggedIn} />} />
            <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
