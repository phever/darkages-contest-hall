import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from './api';
import ConfirmModal from './ConfirmModal';

const STATUS_LABEL = { pending: 'Pending', accepted: 'Accepted', expired: 'Expired' };

// Chancellor-only: invite new nobles by email. The Chancellor sets the email and
// in-game name (which the invited noble cannot change); the noble receives a link
// to choose a username + password and is then a verified voter.
export default function InvitePage({ user }) {
  const isChancellor = user?.role === 'admin';

  const [invitations, setInvitations] = useState([]);
  const [form, setForm] = useState({ email: '', in_game_name: '' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [revoking, setRevoking] = useState(null); // invitation pending revoke
  const [revokeBusy, setRevokeBusy] = useState(false);

  const load = () => {
    api.get('invitations/').then(res => setInvitations(res.data)).catch(() => {});
  };

  useEffect(() => {
    if (!isChancellor) return;
    api.get('invitations/').then(res => setInvitations(res.data)).catch(() => {});
  }, [isChancellor]);

  if (!user) {
    return <p className="center mt-2 muted">Please <Link to="/login">log in</Link> as a Chancellor.</p>;
  }
  if (!isChancellor) {
    return <p className="center mt-2 muted">This page is for College Chancellors only.</p>;
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.post('invitations/', form);
      setMsg({ type: 'ok', text: `Invitation sent to ${form.email}.` });
      setForm({ email: '', in_game_name: '' });
      load();
    } catch (err) {
      const data = err?.response?.data;
      const text = data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(' • ')
        : 'Could not send the invitation.';
      setMsg({ type: 'err', text });
    } finally {
      setBusy(false);
    }
  };

  const confirmRevoke = async () => {
    setRevokeBusy(true);
    try {
      await api.delete(`invitations/${revoking.id}/`);
      setRevoking(null);
      load();
    } catch {
      setMsg({ type: 'err', text: 'Could not revoke that invitation.' });
    } finally {
      setRevokeBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <h1 className="board-title">Invite Nobles</h1>
      <div className="board-info">
        Invite a noble by email. You set their <strong>in-game name</strong> and{' '}
        <strong>email</strong> — these are fixed and cannot be changed by the noble. They'll
        receive a link to choose a username and password, and join as a verified voter.
      </div>

      <div className="card" style={{ borderColor: 'rgba(99,102,241,.4)' }}>
        <h3 style={{ marginBottom: '1rem' }}>Send an invitation</h3>
        {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Email *</label>
            <input type="email" value={form.email} onChange={set('email')} required />
          </div>
          <div className="input-group">
            <label>In-game name</label>
            <input value={form.in_game_name} onChange={set('in_game_name')} placeholder="e.g. Mayheart" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={busy}>
            {busy ? 'Sending…' : 'Send invitation'}
          </button>
        </form>
      </div>

      <h2 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Invitations</h2>
      {invitations.length === 0 ? (
        <p className="muted">No invitations sent yet.</p>
      ) : (
        <div className="invite-list">
          {invitations.map(inv => (
            <div key={inv.id} className="invite-item">
              <div className="invite-main">
                <strong>{inv.email}</strong>
                {inv.in_game_name && <span className="muted"> · {inv.in_game_name}</span>}
              </div>
              <span className={`invite-status invite-status-${inv.status}`}>
                {STATUS_LABEL[inv.status] || inv.status}
              </span>
              {inv.status !== 'accepted' && (
                <button className="btn btn-outline btn-sm" onClick={() => setRevoking(inv)}>
                  Revoke
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmModal
        open={!!revoking}
        title="Revoke this invitation?"
        confirmLabel="Yes, revoke it"
        busyLabel="Revoking…"
        busy={revokeBusy}
        onCancel={() => { if (!revokeBusy) setRevoking(null); }}
        onConfirm={confirmRevoke}
      >
        <p className="modal-entry">{revoking?.email}</p>
        <p className="muted" style={{ fontSize: '0.85rem' }}>
          The invitation link will stop working. You can always send a new one.
        </p>
      </ConfirmModal>
    </div>
  );
}
