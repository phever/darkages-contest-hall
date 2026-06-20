import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from './api';
import EntryCard from './EntryCard';

const STEP_CLASS = { 1: 's1', 2: 's2', 3: 's3', 4: 's4' };

export default function Board({ user }) {
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
        <Link to="/how-to-enter" className="btn btn-primary">How to Enter</Link>
      </div>

      <div className="submission-grid">
        {entries.map(entry => (
          <EntryCard key={entry.id} entry={entry} user={user} />
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

      <footer className="board-footer">
        <span>Made by phever</span>
        <span className="board-footer-sep">·</span>
        <a
          href="https://github.com/phever/darkages-contest-hall"
          target="_blank"
          rel="noreferrer noopener"
          className="board-footer-link"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          <span>GitHub</span>
        </a>
      </footer>
    </div>
  );
}
