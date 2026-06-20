import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState } from 'react';
import './index.css';
import Board from './Board';
import SubmissionForm from './SubmissionForm';
import Login from './Login';

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
            <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
