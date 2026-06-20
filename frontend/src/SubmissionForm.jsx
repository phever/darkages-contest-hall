import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from './api';

const SUBJECTS = ['Art', 'Literature', 'Lore', 'Philosophy', 'History', 'Persona', 'Music', 'Other'];

export default function SubmissionForm() {
  const [contestId, setContestId] = useState(null);
  const [form, setForm] = useState({
    entrant_name: '', work_title: '', work_subject: 'Literature',
    content: '', original_location_url: '', original_location_label: '',
  });
  const [msg, setMsg] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    api.get('contests/')
      .then(res => {
        const board = res.data.find(c => c.is_active) || res.data[0];
        if (board) setContestId(board.id);
      })
      .catch(() => setMsg({ type: 'err', text: 'Could not reach the Contest Hall.' }));
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('entries/', { ...form, contest: contestId });
      setSubmitted(true);
      setMsg({ type: 'ok', text: 'Your work has been submitted to the Mileth College (Step 1/4: Submission).' });
    } catch (err) {
      const data = err?.response?.data;
      const text = data ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(' • ') : 'Submission failed.';
      setMsg({ type: 'err', text });
    }
  };

  return (
    <div className="card" style={{ maxWidth: 640, margin: '1rem auto' }}>
      <h2 style={{ marginBottom: '0.5rem' }}>Submit a Work to the Contest Hall</h2>
      <p className="muted" style={{ marginBottom: '1.5rem' }}>
        New submissions enter the board at <strong>Step 1/4: Submission</strong> and await a College
        Chancellor to open them for review.
      </p>

      {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}

      {submitted ? (
        <Link to="/" className="btn btn-primary" style={{ width: '100%' }}>← Back to the Board</Link>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Entrant (in-game name) *</label>
            <input value={form.entrant_name} onChange={set('entrant_name')} required />
          </div>
          <div className="input-group">
            <label>Work Title *</label>
            <input value={form.work_title} onChange={set('work_title')} required />
          </div>
          <div className="input-group">
            <label>Work Subject *</label>
            <select value={form.work_subject} onChange={set('work_subject')}>
              {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="input-group">
            <label>Original Work Location (URL)</label>
            <input type="url" placeholder="https://…" value={form.original_location_url} onChange={set('original_location_url')} />
          </div>
          <div className="input-group">
            <label>…or board reference</label>
            <input placeholder="[Post 123 on College Contest Board]" value={form.original_location_label} onChange={set('original_location_label')} />
          </div>
          <div className="input-group">
            <label>Content / Description</label>
            <textarea rows={5} value={form.content} onChange={set('content')} />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={!contestId}>
            Submit Work
          </button>
        </form>
      )}
    </div>
  );
}
