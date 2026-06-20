import { useState } from 'react';
import api from './api';

const RECOMMENDATION_OPTIONS = [
  ['', 'Undecided'], ['Village', 'Village'], ['Clave', 'Clave'],
  ['Kingdom', 'Kingdom'], ['Aisling', 'Aisling'], ['No Award', 'No Award'],
];

function recClass(rec) {
  if (!rec) return 'rec-Pending';
  return 'rec-' + rec.replace(/\s+/g, '');
}

function ProgressBar({ stepsComplete, total }) {
  return (
    <div className="progress-wrapper">
      <div className="step-container">
        {Array.from({ length: total }, (_, i) => {
          const n = i + 1;
          return <div key={n} className={`step step-${n}${n <= stepsComplete ? ' complete' : ''}`} />;
        })}
      </div>
      <span className="progress-text">{stepsComplete}/{total}</span>
    </div>
  );
}

// A noble's private draft recommendation + review to copy into the in-game Hall.
function VoteIntentionPanel({ entry }) {
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [recommendation, setRecommendation] = useState('');
  const [reviewText, setReviewText] = useState('');
  const [remind, setRemind] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    try {
      const res = await api.get(`intentions/?entry=${entry.id}`);
      const mine = res.data[0];
      if (mine) {
        setRecommendation(mine.recommendation || '');
        setReviewText(mine.review_text || '');
        setRemind(mine.remind_before_close || false);
      }
    } catch { /* ignore */ }
    setLoaded(true);
  };

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && !loaded) load();
  };

  const save = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('intentions/', {
        entry: entry.id, recommendation, review_text: reviewText, remind_before_close: remind,
      });
      setMsg({ type: 'ok', text: 'Saved privately. Copy it into the in-game Contest Hall when you review.' });
    } catch {
      setMsg({ type: 'err', text: 'Could not save your intention.' });
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(reviewText);
      setMsg({ type: 'ok', text: 'Review copied to clipboard.' });
    } catch {
      setMsg({ type: 'err', text: 'Copy failed — select the text manually.' });
    }
  };

  return (
    <div className="review-area">
      <button className="btn btn-outline" style={{ width: '100%' }} onClick={toggle}>
        {open ? 'Hide my vote intention' : '🔒 My vote intention (private)'}
      </button>
      {open && (
        <>
          {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
          <p className="muted" style={{ fontSize: '0.82rem', margin: '0.6rem 0' }}>
            Private to you and the Chancellors. Real voting happens in-game — prepare your review here
            and copy it across.
          </p>
          <form onSubmit={save}>
            <div className="input-group">
              <label>Intended recommendation</label>
              <select value={recommendation} onChange={e => setRecommendation(e.target.value)}>
                {RECOMMENDATION_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div className="input-group">
              <label>Draft review</label>
              <textarea rows={4} value={reviewText} onChange={e => setReviewText(e.target.value)}
                placeholder="Write the review you'll submit in-game…" />
            </div>
            <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1rem', fontSize: '0.85rem' }}>
              <input type="checkbox" checked={remind} onChange={e => setRemind(e.target.checked)} style={{ width: 'auto' }} />
              Email me before the review period ends
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Save</button>
              <button type="button" className="btn btn-outline" onClick={copy} disabled={!reviewText}>Copy review</button>
            </div>
          </form>
        </>
      )}
    </div>
  );
}

// Chancellors can see every noble's intention on an entry.
function ChancellorIntentions({ entry }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState(null);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next && items === null) {
      try {
        const res = await api.get(`intentions/?entry=${entry.id}`);
        setItems(res.data);
      } catch { setItems([]); }
    }
  };

  return (
    <div className="review-area">
      <button className="btn btn-outline" style={{ width: '100%' }} onClick={toggle}>
        {open ? 'Hide nobles’ intentions' : 'Nobles’ intentions (Chancellor)'}
      </button>
      {open && items !== null && (
        <div className="review-list">
          {items.length === 0 ? <p className="muted">No intentions recorded yet.</p> : items.map(it => (
            <div key={it.id} className="review-item">
              <strong>{it.username}</strong>{' '}
              <span className={`rec-badge ${recClass(it.recommendation)}`}>{it.recommendation || 'Undecided'}</span>
              {it.remind_before_close && <span className="muted"> · wants reminder</span>}
              {it.review_text && <div className="muted" style={{ whiteSpace: 'pre-wrap' }}>{it.review_text}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function EntryCard({ entry, user }) {
  const total = entry.total_steps || 4;
  const isVerifiedNoble = user?.is_verified;
  const isChancellor = user?.role === 'admin';

  return (
    <div className="submission-box">
      <div className="box-title">{entry.entrant_name}, &ldquo;{entry.work_title}&rdquo;</div>

      <ProgressBar stepsComplete={entry.steps_complete} total={total} />

      <div className="submission-details">
        <div className="row"><strong>On Step:</strong><span>{entry.on_step}</span></div>
        <div className="row"><strong>Entrant:</strong><span>{entry.entrant_name}</span></div>
        <div className="row"><strong>Work Title:</strong><span>{entry.work_title}</span></div>
        <div className="row"><strong>Work Subject:</strong><span className="subject-tag">{entry.work_subject}</span></div>
        <div className="row">
          <strong>Original Work Location:</strong>
          <span>
            {entry.original_location_url
              ? <a href={entry.original_location_url} target="_blank" rel="noreferrer">Click Here</a>
              : <span className="muted">{entry.original_location_label || '—'}</span>}
          </span>
        </div>
        <div className="row">
          <strong>Archived Location:</strong>
          <span>
            {entry.archived_location_url
              ? <a href={entry.archived_location_url} target="_blank" rel="noreferrer">Click Here</a>
              : <span className="muted">—</span>}
          </span>
        </div>
        <div className="row"><strong>Review Overseer:</strong><span>{entry.review_overseer || '—'}</span></div>
        <div className="row"><strong>Review Opened:</strong><span>{entry.review_opened || '—'}</span></div>
        <div className="row"><strong>Review Closed:</strong><span>{entry.review_closed || '—'}</span></div>
        <div className="row">
          <strong>Recommendation:</strong>
          <span className={`rec-badge ${recClass(entry.recommendation)}`}>
            {entry.recommendation || 'Pending'}
          </span>
        </div>
      </div>

      {isVerifiedNoble && <VoteIntentionPanel entry={entry} />}
      {isChancellor && <ChancellorIntentions entry={entry} />}
    </div>
  );
}
