import { useState } from 'react';
import api from './api';

const RECOMMENDATION_OPTIONS = ['Village', 'Clave', 'Kingdom', 'Aisling', 'No Award'];

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
          const complete = n <= stepsComplete;
          return <div key={n} className={`step step-${n}${complete ? ' complete' : ''}`} />;
        })}
      </div>
      <span className="progress-text">{stepsComplete}/{total}</span>
    </div>
  );
}

export default function EntryCard({ entry, isLoggedIn }) {
  const total = entry.total_steps || 4;
  const [showReview, setShowReview] = useState(false);
  const [reviews, setReviews] = useState(null);
  const [recommendation, setRecommendation] = useState('Village');
  const [comment, setComment] = useState('');
  const [msg, setMsg] = useState(null);

  const loadReviews = async () => {
    try {
      const res = await api.get(`votes/?entry=${entry.id}`);
      setReviews(res.data);
    } catch {
      setReviews([]);
    }
  };

  const toggleReview = () => {
    const next = !showReview;
    setShowReview(next);
    if (next && reviews === null) loadReviews();
  };

  const submitReview = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('votes/', { entry: entry.id, recommendation, comment, score: 1 });
      setMsg({ type: 'ok', text: 'Review recorded. Thank you, noble.' });
      setComment('');
      loadReviews();
    } catch (err) {
      const detail = err?.response?.data;
      const text = detail?.non_field_errors?.[0] || 'You may have already reviewed this entry.';
      setMsg({ type: 'err', text });
    }
  };

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

      {isLoggedIn && (
        <div className="review-area">
          <button className="btn btn-outline" style={{ width: '100%' }} onClick={toggleReview}>
            {showReview ? 'Hide Reviews' : 'Review this Submission'}
          </button>

          {showReview && (
            <>
              {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
              <form onSubmit={submitReview} style={{ marginTop: '0.75rem' }}>
                <div className="input-group">
                  <label>Recommended recognition</label>
                  <select value={recommendation} onChange={e => setRecommendation(e.target.value)}>
                    {RECOMMENDATION_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div className="input-group">
                  <label>Comments (optional)</label>
                  <textarea rows={2} value={comment} onChange={e => setComment(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                  Submit Review
                </button>
              </form>

              {reviews !== null && (
                <div className="review-list">
                  {reviews.length === 0
                    ? <p className="muted">No reviews recorded yet.</p>
                    : reviews.map(r => (
                        <div key={r.id} className="review-item">
                          <strong>{r.username}</strong> recommended{' '}
                          <span className={`rec-badge ${recClass(r.recommendation)}`}>{r.recommendation}</span>
                          {r.comment && <div className="muted">{r.comment}</div>}
                        </div>
                      ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
