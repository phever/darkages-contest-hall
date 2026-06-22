import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from './api';
import EntryCard from './EntryCard';

const STEP_CLASS = { 1: 's1', 2: 's2', 3: 's3', 4: 's4' };
const PAGE_SIZES = [24, 48, 96];
const PAGE_SIZE_KEY = 'board_page_size';

// Compact page list: every page when small, else a window around the current
// page with first/last and ellipses (e.g. 1 … 4 5 6 … 12).
function pageList(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = new Set([1, total, current, current - 1, current + 1]);
  const sorted = [...pages].filter(p => p >= 1 && p <= total).sort((a, b) => a - b);
  const out = [];
  let prev = 0;
  for (const p of sorted) {
    if (p - prev > 1) out.push(`gap-${p}`);
    out.push(p);
    prev = p;
  }
  return out;
}

export default function Board({ user }) {
  const [contest, setContest] = useState(null);
  const [error, setError] = useState(null);
  const [subject, setSubject] = useState('All');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(() => {
    const saved = Number(localStorage.getItem(PAGE_SIZE_KEY));
    return PAGE_SIZES.includes(saved) ? saved : PAGE_SIZES[0];
  });

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

  // Derive (and clamp) the current page so changing the filter/size can't strand
  // us on an empty page — no effect needed.
  const totalPages = Math.max(1, Math.ceil(entries.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  const pageEntries = entries.slice(start, start + pageSize);
  const showPager = entries.length > PAGE_SIZES[0];

  const pickSubject = (s) => { setSubject(s); setPage(1); };
  const pickPageSize = (n) => {
    setPageSize(n);
    setPage(1);
    localStorage.setItem(PAGE_SIZE_KEY, String(n));
  };
  const goTo = (p) => {
    setPage(Math.min(Math.max(1, p), totalPages));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

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
              onClick={() => pickSubject(s)}
            >
              {s}{s === 'All' ? ` (${contest.entries.length})` : ''}
            </button>
          ))}
        </div>
        <Link to="/how-to-enter" className="btn btn-primary">How to Enter</Link>
      </div>

      {showPager && (
        <div className="pager-bar">
          <span className="pager-meta">
            Showing {start + 1}–{start + pageEntries.length} of {entries.length}
          </span>
          <div className="page-size-group">
            <span className="pager-label">Per page</span>
            {PAGE_SIZES.map(n => (
              <button
                key={n}
                className={`filter-chip ${pageSize === n ? 'active' : ''}`}
                onClick={() => pickPageSize(n)}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="submission-grid">
        {pageEntries.map(entry => (
          <EntryCard key={entry.id} entry={entry} user={user} />
        ))}
      </div>

      {showPager && totalPages > 1 && (
        <nav className="pagination" aria-label="Board pages">
          <button className="filter-chip" onClick={() => goTo(safePage - 1)} disabled={safePage === 1}>
            ‹ Prev
          </button>
          {pageList(safePage, totalPages).map(p => (
            typeof p === 'number' ? (
              <button
                key={p}
                className={`filter-chip ${p === safePage ? 'active' : ''}`}
                onClick={() => goTo(p)}
                aria-current={p === safePage ? 'page' : undefined}
              >
                {p}
              </button>
            ) : (
              <span key={p} className="pager-ellipsis">…</span>
            )
          ))}
          <button className="filter-chip" onClick={() => goTo(safePage + 1)} disabled={safePage === totalPages}>
            Next ›
          </button>
        </nav>
      )}

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
