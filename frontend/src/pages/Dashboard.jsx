import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { sessionApi, progressApi } from '../api';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [progress, setProgress] = useState(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    progressApi.getProgress()
      .then((r) => setProgress(r.data))
      .catch(() => {});
  }, []);

  async function startSession() {
    setStarting(true);
    setError('');
    try {
      const { data } = await sessionApi.start();
      navigate(`/session/${data.session_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start session');
      setStarting(false);
    }
  }

  return (
    <div className="page">
      <nav className="navbar">
        <span className="nav-brand">DSA Interview</span>
        <div className="nav-links">
          <span className="nav-user">Hi, {user?.username}</span>
          <Link to="/progress" className="nav-link">Progress</Link>
          <button onClick={logout} className="btn-ghost">Logout</button>
        </div>
      </nav>

      <main className="dashboard-main">
        <div className="dashboard-hero">
          <h2>Ready to practice?</h2>
          <p>The AI interviewer will select a problem based on your weak areas and history.</p>
          {error && <p className="error-msg">{error}</p>}
          <button className="btn-primary btn-large" onClick={startSession} disabled={starting}>
            {starting ? 'Loading problem...' : 'Start Interview'}
          </button>
        </div>

        {progress && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{progress.total_sessions}</div>
              <div className="stat-label">Sessions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{progress.total_solved}</div>
              <div className="stat-label">Solved</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {Math.round((progress.overall_success_rate || 0) * 100)}%
              </div>
              <div className="stat-label">Success Rate</div>
            </div>
          </div>
        )}

        {progress?.topic_stats && (
          <div className="section">
            <h3>Topic Breakdown</h3>
            <div className="topic-grid">
              {Object.entries(progress.topic_stats).map(([topic, stats]) => (
                <div key={topic} className="topic-card">
                  <div className="topic-name">{topic}</div>
                  <div className="topic-stats">
                    {stats.solved}/{stats.attempted} solved
                  </div>
                  <div className="topic-bar">
                    <div
                      className="topic-bar-fill"
                      style={{ width: `${stats.success_rate * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {progress?.recent_sessions?.length > 0 && (
          <div className="section">
            <h3>Recent Sessions</h3>
            <table className="sessions-table">
              <thead>
                <tr>
                  <th>Problem</th>
                  <th>Topic</th>
                  <th>Difficulty</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {progress.recent_sessions.map((s) => (
                  <tr key={s.session_id}>
                    <td>{s.title}</td>
                    <td><span className="badge">{s.topic}</span></td>
                    <td>{s.difficulty}</td>
                    <td>
                      <span className={`badge ${s.solved ? 'badge-success' : 'badge-fail'}`}>
                        {s.solved ? 'Solved' : 'Not solved'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
