import { useState, useEffect } from 'react';
import api from './api';

const SUBJECTS = ['Art', 'Literature', 'Lore', 'Philosophy', 'History', 'Persona'];

const STEPS = [
  ['Bring your work to the College', 'Travel in-game to the Mileth College Contest Hall (see the map below) and present your entry to a College Chancellor.'],
  ['Meet the entry requirement', 'Clave recognition or higher is required to enter the Contest Hall — or you may spend three education marks to submit a work.'],
  ['Your entry is opened for review', 'A Chancellor accepts the entry and becomes its review overseer. Nobles with village recognition or greater review it and recommend a recognition level.'],
  ['Loures confirmation & nobility', 'If recognition is recommended, the result is sent to the Library of Loures for final approval, after which nobility is awarded.'],
];

function ChancellorEntryForm() {
  const [contestId, setContestId] = useState(null);
  const [form, setForm] = useState({
    entrant_name: '', work_title: '', work_subject: 'Literature',
    content: '', original_location_url: '', original_location_label: '',
  });
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    api.get('contests/')
      .then(res => {
        const board = res.data.find(c => c.is_active) || res.data[0];
        if (board) setContestId(board.id);
      })
      .catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('entries/', { ...form, contest: contestId });
      setMsg({ type: 'ok', text: `Recorded "${form.work_title}" on the board at Step 1/4.` });
      setForm({ entrant_name: '', work_title: '', work_subject: 'Literature', content: '', original_location_url: '', original_location_label: '' });
    } catch (err) {
      const data = err?.response?.data;
      const text = data ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(' • ') : 'Failed to record entry.';
      setMsg({ type: 'err', text });
    }
  };

  return (
    <div className="card" style={{ marginTop: '2rem', borderColor: 'rgba(99,102,241,.4)' }}>
      <h3 style={{ marginBottom: '0.25rem' }}>Chancellor: record an entry</h3>
      <p className="muted" style={{ marginBottom: '1.25rem', fontSize: '0.9rem' }}>
        Use this to place an in-game submission onto the board (enters at Step 1/4). Visible to Chancellors only.
      </p>
      {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
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
          <textarea rows={4} value={form.content} onChange={set('content')} />
        </div>
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={!contestId}>
          Record Entry
        </button>
      </form>
    </div>
  );
}

export default function HowToEnter({ user }) {
  const isChancellor = user?.role === 'admin';

  return (
    <div style={{ maxWidth: 820, margin: '0 auto' }}>
      <h1 className="board-title">How to Enter a Contest</h1>

      <div className="board-info">
        Submissions, reviews, and voting all happen <strong>in-game</strong> at the Mileth College
        Contest Hall — not on this website. This site archives entries and lets nobles privately
        prepare their reviews. Here's how to enter a work for recognition:
      </div>

      <div className="steps-grid" style={{ marginBottom: '2rem' }}>
        {STEPS.map(([title, body], i) => (
          <div key={i} className={`step-card s${i + 1}`}>
            <h3>Step {i + 1}/4: {title}</h3>
            <p>{body}</p>
          </div>
        ))}
      </div>

      <h2 style={{ textAlign: 'center', marginBottom: '1rem' }}>Finding the Contest Hall</h2>
      <p className="muted center" style={{ marginBottom: '1rem' }}>
        The Contest Hall is in the Mileth College. Use the campus map below to find your way.
      </p>
      <img
        src="/media/campus-map-full.jpg"
        alt="Map of the Mileth College campus showing the Contest Hall"
        style={{ width: '100%', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}
      />

      {isChancellor && <ChancellorEntryForm />}
    </div>
  );
}
