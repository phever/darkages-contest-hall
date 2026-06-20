import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from './api';
import EntryCard from './EntryCard';

const STEP_CLASS = { 1: 's1', 2: 's2', 3: 's3', 4: 's4' };

export default function Board({ isLoggedIn }) {
  const [contest, setContest] = useState(null);
  const [error, setError] = useState(null);
  const [subject, setSubject] = useState('All');

  useEffect(() => {
    // The board shows the primary (first active) contest with all its entries.
    api.get('contests/')
      .then(res => {
        const list = res.data;
        if (!list.length) { setError('No contest board found.'); return; }
        const board = list.find(c => c.is_active) || list[0];
        return api.get(`contests/${board.id}/`).then(r => setContest(r.data));
      })
      .catch(() => setError('Could not reach the Contest Hall. Is the backend running?'));
  }, []);

  if (error) return <p className="center mt-2">{error}</p>;
  if (!contest) return <p className="center mt-2 muted">Loading the Contest Hall…</p>;

  const subjects = ['All', ...Array.from(new Set(contest.entries.map(e => e.work_subject)))];
  const entries = subject === 'All'
    ? contest.entries
    : contest.entries.filter(e => e.work_subject === subject);

  return (
    <div>
      <h1 className="board-title">{contest.title}</h1>

      {contest.info_message && <div className="board-info">{contest.info_message}</div>}

      <div className="board-toolbar">
        <div className="filters">
          {subjects.map(s => (
            <button
              key={s}
              className={`filter-chip ${subject === s ? 'active' : ''}`}
              onClick={() => setSubject(s)}
            >
              {s}{s === 'All' ? ` (${contest.entries.length})` : ''}
            </button>
          ))}
        </div>
        <Link to="/submit" className="btn btn-primary">+ Submit a Work</Link>
      </div>

      <div className="submission-grid">
        {entries.map(entry => (
          <EntryCard key={entry.id} entry={entry} isLoggedIn={isLoggedIn} />
        ))}
      </div>

      {contest.steps?.length > 0 && (
        <section className="steps-section">
          <h2>Contest Steps</h2>
          <div className="steps-grid">
            {contest.steps.map(step => (
              <div key={step.id} className={`step-card ${STEP_CLASS[step.number] || ''}`}>
                <h3>Step {step.number}/4: {step.title}</h3>
                <p>{step.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
