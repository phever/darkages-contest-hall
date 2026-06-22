import { useState, useEffect } from 'react';
import api from './api';
import EntryCard from './EntryCard';

const SUBJECTS = ['Art', 'Literature', 'Lore', 'Philosophy', 'History', 'Persona', 'Music', 'Other'];

// Chancellor-only form to add an older work to the Archive: records the metadata
// (is_archived) and, optionally, uploads the archived copy to object storage.
function ArchiveUploadForm({ onAdded }) {
  const [open, setOpen] = useState(false);
  const [contestId, setContestId] = useState(null);
  const [form, setForm] = useState({
    entrant_name: '', work_title: '', work_subject: 'Literature',
    content: '', original_location_url: '', original_location_label: '',
  });
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
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
    setBusy(true);
    setMsg(null);
    try {
      const { data: entry } = await api.post('entries/', { ...form, contest: contestId, is_archived: true });
      let finalEntry = entry;
      if (file) {
        try {
          const { data: presign } = await api.post(`entries/${entry.id}/archive-upload-url/`, {
            filename: file.name, content_type: file.type || 'application/octet-stream',
          });
          const put = await fetch(presign.upload_url, {
            method: 'PUT', body: file, headers: { 'Content-Type': presign.content_type },
          });
          if (!put.ok) throw new Error('upload failed');
          const { data: patched } = await api.patch(`entries/${entry.id}/`, { archived_location_url: presign.public_url });
          finalEntry = patched;
          setMsg({ type: 'ok', text: `Archived “${form.work_title}” with its file.` });
        } catch {
          setMsg({ type: 'ok', text: `Archived “${form.work_title}”. The file upload failed (storage may be unconfigured) — you can attach it later from the card.` });
        }
      } else {
        setMsg({ type: 'ok', text: `Archived “${form.work_title}”.` });
      }
      onAdded(finalEntry);
      setForm({ entrant_name: '', work_title: '', work_subject: 'Literature', content: '', original_location_url: '', original_location_label: '' });
      setFile(null);
    } catch (err) {
      const data = err?.response?.data;
      const text = data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(' • ')
        : 'Could not archive this work.';
      setMsg({ type: 'err', text });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card" style={{ borderColor: 'rgba(99,102,241,.4)', marginBottom: '2rem' }}>
      <button className="btn btn-outline" style={{ width: '100%' }} onClick={() => setOpen(o => !o)}>
        {open ? 'Hide archive upload' : '➕ Add an archived work'}
      </button>
      {open && (
        <div style={{ marginTop: '1.25rem' }}>
          <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Preserve an older submission. It won't appear on the live board — only here in the Archive.
          </p>
          {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="input-group">
                <label>Entrant (in-game name) *</label>
                <input value={form.entrant_name} onChange={set('entrant_name')} required />
              </div>
              <div className="input-group">
                <label>Work Title *</label>
                <input value={form.work_title} onChange={set('work_title')} required />
              </div>
            </div>
            <div className="input-group">
              <label>Work Subject *</label>
              <select value={form.work_subject} onChange={set('work_subject')}>
                {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="input-group">
              <label>Description / Content</label>
              <textarea rows={3} value={form.content} onChange={set('content')} />
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
              <label>Archived file (optional)</label>
              <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} style={{ fontSize: '0.85rem' }} />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={busy || !contestId}>
              {busy ? 'Archiving…' : 'Add to Archive'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

// The Archive: older submissions kept for posterity, searchable by entrant/title
// and filterable by category. Public to view; Chancellors can add works.
export default function Archive({ user }) {
  const isChancellor = user?.role === 'admin';
  const [items, setItems] = useState(null);
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('All');
  const [error, setError] = useState(null);

  useEffect(() => {
    // Debounced server-side search + category filter. When a search or category
    // filter is active, surface live board entries too (badged "Board Entry");
    // the default browse view stays archive-only.
    const t = setTimeout(() => {
      const active = search.trim() !== '' || subject !== 'All';
      const params = new URLSearchParams({ archived: active ? 'all' : 'true' });
      if (subject !== 'All') params.set('subject', subject);
      if (search.trim()) params.set('search', search.trim());
      api.get(`entries/?${params.toString()}`)
        .then(res => { setItems(res.data); setError(null); })
        .catch(() => setError('Could not load the Archive. Is the backend running?'));
    }, 250);
    return () => clearTimeout(t);
  }, [search, subject]);

  const handleAdded = (entry) => setItems(prev => (prev ? [entry, ...prev] : [entry]));

  const filtering = search.trim() !== '' || subject !== 'All';

  return (
    <div>
      <h1 className="board-title">Archive</h1>
      <div className="board-info">
        Older contest submissions, preserved for posterity. Search by entrant or title, or filter by
        category — results also include matching works still on the live board, marked “Board Entry”.
      </div>

      {isChancellor && <ArchiveUploadForm onAdded={handleAdded} />}

      <div className="archive-controls">
        <input
          className="archive-search"
          type="search"
          placeholder="Search entrant or title…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="filters">
          {['All', ...SUBJECTS].map(s => (
            <button
              key={s}
              className={`filter-chip ${subject === s ? 'active' : ''}`}
              onClick={() => setSubject(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="center mt-2">{error}</p>}
      {items === null && !error && <p className="center mt-2 muted">Loading the Archive…</p>}
      {items !== null && items.length === 0 && (
        <p className="center mt-2 muted">
          {filtering ? 'No works match your search.' : 'No works have been archived yet.'}
        </p>
      )}
      {items !== null && items.length > 0 && (
        <>
          <p className="pager-meta" style={{ marginBottom: '1rem' }}>
            {items.length} work{items.length !== 1 ? 's' : ''}
          </p>
          <div className="submission-grid">
            {items.map(entry => <EntryCard key={entry.id} entry={entry} user={user} inArchive />)}
          </div>
        </>
      )}
    </div>
  );
}
