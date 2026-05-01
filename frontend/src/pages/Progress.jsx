import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { progressApi } from '../api';

export default function Progress() {
  const [progress, setProgress] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [learningPath, setLearningPath] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      progressApi.getProgress(),
      progressApi.getPatterns(),
      progressApi.getLearningPath(),
    ]).then(([p, pat, lp]) => {
      setProgress(p.data);
      setPatterns(pat.data.patterns || []);
      setLearningPath(lp.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-screen">Loading...</div>;

  return (
    <div className="page">
      <nav className="navbar">
        <Link to="/" className="nav-brand">DSA Interview</Link>
        <Link to="/" className="nav-link">Dashboard</Link>
      </nav>

      <main className="progress-main">
        <h2>Your Progress</h2>

        {progress && (
          <>
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
                <div className="stat-value">{Math.round((progress.overall_success_rate || 0) * 100)}%</div>
                <div className="stat-label">Success Rate</div>
              </div>
            </div>

            {progress.topic_stats && (
              <div className="section">
                <h3>Topic Performance</h3>
                <table className="sessions-table">
                  <thead>
                    <tr><th>Topic</th><th>Attempted</th><th>Solved</th><th>Success Rate</th></tr>
                  </thead>
                  <tbody>
                    {Object.entries(progress.topic_stats).map(([topic, s]) => (
                      <tr key={topic}>
                        <td><span className="badge">{topic}</span></td>
                        <td>{s.attempted}</td>
                        <td>{s.solved}</td>
                        <td>
                          <div className="topic-bar" style={{ width: 120 }}>
                            <div className="topic-bar-fill" style={{ width: `${s.success_rate * 100}%` }} />
                          </div>
                          <span style={{ marginLeft: 8 }}>{Math.round(s.success_rate * 100)}%</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {patterns.length > 0 && (
          <div className="section">
            <h3>Recurring Patterns</h3>
            <div className="patterns-list">
              {patterns.map((p, i) => (
                <div key={i} className={`pattern-card sev-${p.severity}`}>
                  <div className="pattern-type">{p.pattern_type}</div>
                  <div className="pattern-topic">{p.topic}</div>
                  <div className="pattern-count">{p.occurrence_count}x</div>
                  <div className="pattern-desc">{p.description}</div>
                  <span className={`badge sev-badge sev-${p.severity}`}>{p.severity}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {patterns.length === 0 && (
          <div className="section">
            <h3>Recurring Patterns</h3>
            <p className="muted">No recurring patterns detected yet. Complete more sessions to see your patterns.</p>
          </div>
        )}

        {learningPath && (
          <div className="section">
            <h3>Learning Path</h3>
            {learningPath.milestone && (
              <div className="milestone">{learningPath.milestone}</div>
            )}
            {learningPath.suggested_difficulty && (
              <p>Recommended difficulty: <b>{learningPath.suggested_difficulty}</b></p>
            )}
            {learningPath.focus_areas?.length > 0 && (
              <div>
                <b>Focus areas:</b>
                <ul>{learningPath.focus_areas.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </div>
            )}
            {learningPath.next_recommended_topics?.length > 0 && (
              <div>
                <b>Suggested next topics:</b>
                <ul>{learningPath.next_recommended_topics.map((t, i) => <li key={i}>{t}</li>)}</ul>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
