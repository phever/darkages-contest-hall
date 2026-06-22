import { useEffect, useState } from 'react';
import api from './api';

const SUBJECTS = ['Art', 'Literature', 'Lore', 'Philosophy', 'History', 'Persona', 'Music', 'Other'];

const RECOMMENDATION_OPTIONS = [
  ['', 'Pending'], ['Village', 'Village'], ['Clave', 'Clave'],
  ['Kingdom', 'Kingdom'], ['Aisling', 'Aisling'], ['No Award', 'No Award'],
];

// Workflow step labels — mirrors Entry.STEP_LABELS on the backend.
const STEP_LABELS = {
  1: 'Submission', 2: 'Review', 3: 'Loures Confirmation', 4: 'Nobility Awarded',
};

// Only the fields a Chancellor edits inline live here; deep edits stay in /admin.
function initialForm(entry) {
  return {
    entrant_name: entry.entrant_name || '',
    work_title: entry.work_title || '',
    work_subject: entry.work_subject || 'Other',
    original_location_url: entry.original_location_url || '',
    original_location_label: entry.original_location_label || '',
    content: entry.content || '',
    review_overseer: entry.review_overseer || '',
    review_opened: entry.review_opened || '',
    review_closed: entry.review_closed || '',
    recommendation: entry.recommendation || '',
    current_step: entry.steps_complete || entry.current_step || 1,
  };
}

// A Chancellor-only editing view for one entry, shown in a glassmorphism modal.
// Mirrors the submission form but lets a Chancellor edit every board field
// (including the workflow step) without opening the Django admin.
export default function EntryEditForm({ entry, onClose, onSaved }) {
  const [form, setForm] = useState(() => initialForm(entry));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape' && !busy) onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [busy, onClose]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    const step = Number(form.current_step);
    try {
      const { data } = await api.patch(`entries/${entry.id}/`, {
        ...form,
        current_step: step,
        step_status: STEP_LABELS[step] || form.step_status,
      });
      onSaved(data);
      onClose();
    } catch (err) {
      const data = err?.response?.data;
      const text = data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(' • ')
        : 'Could not save changes.';
      setMsg({ type: 'err', text });
      setBusy(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => { if (!busy) onClose(); }}>
      <div
        className="modal-card modal-card-wide"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="modal-title">Edit entry</h3>
        <p className="muted" style={{ fontSize: '0.85rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
          Quick edits for this work. For deeper changes, use the <strong>/admin</strong> panel.
        </p>
        {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
        <form onSubmit={handleSubmit}>
          <div className="modal-body modal-scroll">
            <div className="input-group">
              <label>Entrant (in-game name)</label>
              <input value={form.entrant_name} onChange={set('entrant_name')} required />
            </div>
            <div className="input-group">
              <label>Work Title</label>
              <input value={form.work_title} onChange={set('work_title')} required />
            </div>
            <div className="input-group">
              <label>Work Subject</label>
              <select value={form.work_subject} onChange={set('work_subject')}>
                {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="input-group">
              <label>Original Work Location (URL)</label>
              <input type="url" placeholder="https://…"
                value={form.original_location_url} onChange={set('original_location_url')} />
            </div>
            <div className="input-group">
              <label>…or board reference</label>
              <input placeholder="[Post 123 on College Contest Board]"
                value={form.original_location_label} onChange={set('original_location_label')} />
            </div>
            <div className="input-group">
              <label>Content / Description</label>
              <textarea rows={3} value={form.content} onChange={set('content')} />
            </div>
            <div className="input-group">
              <label>Review Overseer</label>
              <input value={form.review_overseer} onChange={set('review_overseer')} />
            </div>
            <div className="form-row">
              <div className="input-group">
                <label>Review Opened</label>
                <input placeholder="220.02.16" value={form.review_opened} onChange={set('review_opened')} />
              </div>
              <div className="input-group">
                <label>Review Closed</label>
                <input placeholder="220.06.18" value={form.review_closed} onChange={set('review_closed')} />
              </div>
            </div>
            <div className="form-row">
              <div className="input-group">
                <label>Recommendation</label>
                <select value={form.recommendation} onChange={set('recommendation')}>
                  {RECOMMENDATION_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              {!entry.is_archived && (
                <div className="input-group">
                  <label>Workflow Step</label>
                  <select value={form.current_step} onChange={set('current_step')}>
                    {[1, 2, 3, 4].map(n => (
                      <option key={n} value={n}>{n}/4 — {STEP_LABELS[n]}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
