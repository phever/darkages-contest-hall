import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from './api';

export default function ContestDetails({ isLoggedIn }) {
  const { id } = useParams();
  const [contest, setContest] = useState(null);
  const [entries, setEntries] = useState([]);
  const [votes, setVotes] = useState([]);

  useEffect(() => {
    // Fetch contest details
    api.get(`contests/${id}/`)
      .then(res => setContest(res.data))
      .catch(err => console.error(err));

    // Fetch entries
    api.get(`entries/`)
      .then(res => {
        const contestEntries = res.data.filter(e => e.contest === parseInt(id));
        setEntries(contestEntries);
      })
      .catch(err => console.error(err));

    // Fetch user votes if logged in
    if (isLoggedIn) {
      api.get(`votes/`)
        .then(res => setVotes(res.data))
        .catch(err => console.error(err));
    }
  }, [id, isLoggedIn]);

  const handleVote = async (entryId) => {
    if (!isLoggedIn) {
      alert("Please login to vote.");
      return;
    }
    try {
      await api.post('votes/', { entry: entryId, score: 1 });
      // Refresh votes
      const res = await api.get('votes/');
      setVotes(res.data);
    } catch (err) {
      alert("Failed to cast vote. You may have already voted for this entry.");
    }
  };

  const hasVotedFor = (entryId) => {
    return votes.some(v => v.entry === entryId);
  };

  if (!contest) return <p>Loading contest...</p>;

  return (
    <div>
      <Link to="/" className="btn btn-outline" style={{ marginBottom: '2rem' }}>&larr; Back to Contests</Link>
      
      <div className="card" style={{ marginBottom: '3rem' }}>
        <h2>{contest.title}</h2>
        <p style={{ color: 'var(--text-muted)' }}>{contest.description}</p>
        <div style={{ marginTop: '1rem' }}>
          <span className={`badge ${contest.is_active ? 'badge-active' : 'badge-inactive'}`}>
            {contest.is_active ? 'Active' : 'Ended'}
          </span>
        </div>
      </div>

      <h3>Contest Entries</h3>
      <div className="grid" style={{ marginTop: '1.5rem' }}>
        {entries.length > 0 ? entries.map(entry => (
          <div key={entry.id} className="card">
            <h4>{entry.title}</h4>
            <p style={{ fontSize: '0.9rem', color: 'var(--primary)', marginBottom: '1rem' }}>By: {entry.author_in_game_name}</p>
            <p style={{ marginBottom: '1.5rem' }}>{entry.content}</p>
            {entry.original_board_link && (
              <a href={entry.original_board_link} target="_blank" rel="noreferrer" style={{ display: 'block', marginBottom: '1rem', fontSize: '0.9rem' }}>
                View Original Post
              </a>
            )}
            
            {contest.is_active && (
              <button 
                className={`btn ${hasVotedFor(entry.id) ? 'btn-outline' : 'btn-primary'}`} 
                style={{ width: '100%' }}
                onClick={() => handleVote(entry.id)}
                disabled={hasVotedFor(entry.id)}
              >
                {hasVotedFor(entry.id) ? '✓ Voted' : 'Vote for Entry'}
              </button>
            )}
          </div>
        )) : (
          <p>No entries have been posted for this contest yet.</p>
        )}
      </div>
    </div>
  );
}
