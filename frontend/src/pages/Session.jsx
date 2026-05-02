import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { sessionApi } from '../api';
import { normalizeApiError } from '../utils/errors';

const PHASE_LABELS = {
  problem_presentation: 'Problem Presentation',
  clarification: 'Clarification',
  brute_force: 'Brute Force',
  optimization: 'Optimization',
  coding: 'Coding',
  code_review: 'Code Review',
  wrap_up: 'Wrap Up',
};

export default function Session() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [phase, setPhase] = useState('clarification');
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showEditor, setShowEditor] = useState(true);
  const [code, setCode] = useState('# Write your solution here\n');
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);
  const [ending, setEnding] = useState(false);
  const [sessionDone, setSessionDone] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    sessionApi.get(id).then(({ data }) => {
      setSession(data);
      setPhase(data.phase);
      const history = data.conversation_history || [];
      setMessages(history);
      const lastPhase = data.phase;
      setShowEditor(true);
    });
  }, [id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const content = input.trim();
    setInput('');
    setSending(true);
    setMessages((m) => [...m, { role: 'user', content }]);
    try {
      const { data } = await sessionApi.message(id, content);
      setMessages((m) => [...m, { role: 'assistant', content: data.content }]);
      setPhase(data.phase);
      if (data.should_show_code_editor) setShowEditor(true);
      if (data.session_complete) setSessionDone(true);
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: `Error: ${normalizeApiError(err, 'Failed to send message')}` }]);
    } finally {
      setSending(false);
    }
  }

  async function handleSubmitCode() {
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const { data } = await sessionApi.submitCode(id, code, 'python');
      setSubmitResult(data);
      setPhase(data.all_passed ? 'wrap_up' : 'code_review');
      setMessages((m) => [...m, { role: 'assistant', content: data.interviewer_follow_up }]);
      if (data.all_passed) setSessionDone(true);
    } catch (err) {
      setSubmitResult({ error: normalizeApiError(err, 'Submission failed') });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEndSession() {
    setEnding(true);
    try {
      await sessionApi.end(id);
      navigate('/');
    } catch {
      navigate('/');
    }
  }

  async function handleExitSession() {
    setEnding(true);
    try {
      // Persist progress even if the user exits before fully solving.
      await sessionApi.end(id);
    } catch {
      // Ignore end-session failures on explicit exit and return user to dashboard.
    } finally {
      navigate('/');
    }
  }

  if (!session) {
    return <div className="loading-screen">Loading session...</div>;
  }

  const problem = session.problem;
  const canEndSession = sessionDone || submitResult?.all_passed === true;

  return (
    <div className="session-layout">
      {/* Header */}
      <div className="session-header">
        <div className="session-problem-title">{problem?.title}</div>
        <div className="session-meta">
          <span className={`badge diff-${problem?.difficulty}`}>{problem?.difficulty}</span>
          <span className="badge">{problem?.topic}</span>
          <span className="phase-label">{PHASE_LABELS[phase] || phase}</span>
        </div>
        <div className="session-actions">
          {canEndSession && (
            <button className="btn-primary" onClick={handleEndSession} disabled={ending}>
              {ending ? 'Ending...' : 'End & Save'}
            </button>
          )}
          <button className="btn-ghost" onClick={handleExitSession} disabled={ending}>
            {ending ? 'Exiting...' : 'Exit'}
          </button>
        </div>
      </div>

      <div className="session-body">
        {/* Left: Problem + Chat */}
        <div className="chat-panel">
          <div className="problem-desc">
            <h3>Problem</h3>
            {problem?.function_name && (
              <div className="expected-function-callout">
                <span className="label">Expected function</span>
                <code>{problem.function_name}(...)</code>
              </div>
            )}
            <p>{problem?.description}</p>
            {problem?.examples?.length > 0 && (
              <div className="examples">
                {problem.examples.map((ex, i) => (
                  <div key={i} className="example">
                    <div><b>Input:</b> <code>{ex.input}</code></div>
                    <div><b>Output:</b> <code>{ex.output}</code></div>
                    {ex.explanation && <div><b>Explanation:</b> {ex.explanation}</div>}
                  </div>
                ))}
              </div>
            )}
            {problem?.constraints?.length > 0 && (
              <div className="constraints">
                <b>Constraints:</b>
                <ul>{problem.constraints.map((c, i) => <li key={i}><code>{c}</code></li>)}</ul>
              </div>
            )}
          </div>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg chat-msg-${m.role}`}>
                <div className="chat-msg-role">{m.role === 'assistant' ? 'Interviewer' : 'You'}</div>
                <div className="chat-msg-content">{m.content}</div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {!canEndSession && (
            <form onSubmit={sendMessage} className="chat-input-row">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your response..."
                disabled={sending}
                className="chat-input"
              />
              <button type="submit" className="btn-primary" disabled={sending || !input.trim()}>
                {sending ? '...' : 'Send'}
              </button>
            </form>
          )}
        </div>

        {/* Right: Editor + Results */}
        <div className={`editor-panel ${showEditor ? 'editor-panel-visible' : ''}`}>
          <div className="editor-header">
            <span>Python</span>
            <div className="editor-header-actions">
              {problem?.function_name && (
                <span className="expected-function-inline">
                  Expected: <code>{problem.function_name}(...)</code>
                </span>
              )}
              <span className="phase-label">{phase === 'coding' ? 'Ready to code' : 'Editor available'}</span>
              <button
                className="btn-primary"
                onClick={handleSubmitCode}
                disabled={submitting}
              >
                {submitting ? 'Running...' : 'Submit Code'}
              </button>
            </div>
          </div>
          <div className="editor-wrapper">
            <Editor
              height="100%"
              width="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={(v) => setCode(v || '')}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                tabSize: 4,
                automaticLayout: true,
              }}
            />
          </div>

          {submitResult && (
            <div className="review-panel">
              {submitResult.error ? (
                <p className="error-msg">{submitResult.error}</p>
              ) : (
                <>
                  <div className={`test-summary ${submitResult.all_passed ? 'passed' : 'failed'}`}>
                    {submitResult.test_cases_passed}/{submitResult.test_cases_total} tests passed
                    {submitResult.all_passed ? ' — All Passed!' : ''}
                  </div>

                  <div className="test-cases">
                    {submitResult.test_case_results?.map((tc, i) => (
                      <div key={i} className={`tc ${tc.passed ? 'tc-pass' : 'tc-fail'}`}>
                        <span>{tc.passed ? '✓' : '✗'}</span>
                        <span>Test {i + 1}</span>
                        {!tc.passed && tc.error && <span className="tc-error">{tc.error}</span>}
                      </div>
                    ))}
                  </div>

                  {submitResult.review && (
                    <div className="review-details">
                      <h4>Code Review</h4>
                      <div className="complexity-row">
                        <span>Time: <b>{submitResult.review.detected_time_complexity}</b></span>
                        <span>Space: <b>{submitResult.review.detected_space_complexity}</b></span>
                        <span className={`badge verdict-${submitResult.review.complexity_verdict}`}>
                          {submitResult.review.complexity_verdict}
                        </span>
                      </div>
                      <p className="overall-feedback">{submitResult.review.overall_feedback}</p>
                      {submitResult.review.edge_cases_missed?.length > 0 && (
                        <div>
                          <b>Edge cases missed:</b>
                          <ul>{submitResult.review.edge_cases_missed.map((e, i) => <li key={i}>{e}</li>)}</ul>
                        </div>
                      )}
                      {submitResult.review.improvement_suggestions?.length > 0 && (
                        <div>
                          <b>Suggestions:</b>
                          <ul>{submitResult.review.improvement_suggestions.map((s, i) => <li key={i}>{s}</li>)}</ul>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
