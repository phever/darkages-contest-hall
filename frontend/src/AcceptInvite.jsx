import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import api from './api';

// Public page reached from an invitation email link (?token=…). The invitee's
// email and in-game name are set by the Chancellor and shown read-only; the
// noble only chooses a username and password. On success they're logged in.
export default function AcceptInvite({ onLogin }) {
  const [params] = useSearchParams();
  const token = params.get('token');
  const navigate = useNavigate();

  const [invite, setInvite] = useState(null);   // { email, in_game_name }
  const [loadError, setLoadError] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    if (!token) return;
    api.get(`auth/invitation/?token=${encodeURIComponent(token)}`)
      .then(res => setInvite(res.data))
      .catch(err => setLoadError(
        err?.response?.data?.detail || 'This invitation is invalid or has expired.'
      ));
  }, [token]);

  // A missing token is known at render time — no effect/state needed for it.
  const displayError = !token ? 'No invitation token was provided.' : loadError;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.post('auth/accept-invite/', { token, username, password });
      await onLogin();
      navigate('/');
    } catch (err) {
      const data = err?.response?.data;
      const text = data && typeof data === 'object'
        ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(' ') : v}`).join(' • ')
        : 'Could not create your account.';
      setMsg({ type: 'err', text });
      setBusy(false);
    }
  };

  if (displayError) {
    return (
      <div className="card" style={{ maxWidth: 420, margin: '2rem auto', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '1rem' }}>Invitation unavailable</h2>
        <p className="muted">{displayError}</p>
        <p className="muted" style={{ marginTop: '1rem' }}>
          Ask a College Chancellor to send a new invitation, or <Link to="/login">log in</Link>.
        </p>
      </div>
    );
  }

  if (!invite) {
    return <p className="center mt-2 muted">Checking your invitation…</p>;
  }

  return (
    <div className="card" style={{ maxWidth: 420, margin: '2rem auto' }}>
      <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Welcome to the Contest Hall</h2>
      <p className="muted" style={{ textAlign: 'center', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
        Create your account to review contest entries.
      </p>
      {msg && <p className={`form-message ${msg.type}`}>{msg.text}</p>}
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label>In-game name (set by the Chancellor)</label>
          <input value={invite.in_game_name || '—'} readOnly disabled />
        </div>
        <div className="input-group">
          <label>Email (set by the Chancellor)</label>
          <input value={invite.email} readOnly disabled />
        </div>
        <div className="input-group">
          <label>Choose a username *</label>
          <input value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
        </div>
        <div className="input-group">
          <label>Choose a password *</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            required minLength={10} />
        </div>
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </div>
  );
}
