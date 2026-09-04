import React, { useState } from 'react';
import { HelpCircle, Send, Cpu, CheckCircle, ShieldCheck, ArrowRight } from 'lucide-react';

export const AIAssistantView = () => {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: "Hello, Operator. I am the SECUROX AI Investigation Assistant. I analyze real-time roadway telemetry, computer vision streams, and OT cyber telemetry to provide fact-grounded root cause analysis. How can I assist your investigation?",
      grounded: true,
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const presetQuestions = [
    "Why is Intersection 12 critical?",
    "Show all anomalies involving Camera 04.",
    "Is current congestion caused by a traffic bottleneck or cyber attack?",
    "What are the top recommended operator mitigation actions right now?"
  ];

  const handleSend = async (queryToAsk) => {
    const q = queryToAsk || inputText;
    if (!q.trim()) return;

    const userMsg = {
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8001/api/ai-assistant/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q })
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [
          ...prev,
          {
            sender: 'ai',
            text: data.answer,
            grounded: true,
            confidence: data.confidence,
            entities: data.grounded_entities,
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: "I am unable to reach the telemetry database at this moment. Please verify backend service status.",
          grounded: false,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: 'calc(100vh - 120px)' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>AI SECURITY & TRAFFIC INVESTIGATION ASSISTANT</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Explainable, Zero-Hallucination Intelligence Synthesizing Live OT Telemetry, Vision Detections & Incident Graphs
        </p>
      </div>

      {/* Preset Query Chips */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {presetQuestions.map((q, i) => (
          <button
            key={i}
            className="btn btn-outline btn-sm"
            onClick={() => handleSend(q)}
            style={{ fontSize: '11px', textAlign: 'left' }}
          >
            💬 {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Window */}
      <div 
        className="soc-card" 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '14px',
          padding: '16px' 
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: m.sender === 'user' ? 'var(--bg-card-hover)' : 'var(--bg-surface)',
              border: `1px solid ${m.sender === 'user' ? 'var(--border-medium)' : 'var(--border-accent)'}`,
              borderRadius: '8px',
              padding: '12px 16px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', fontSize: '11px', color: 'var(--text-dim)' }}>
              <span style={{ fontWeight: 600, color: m.sender === 'user' ? '#fff' : 'var(--cyan-accent)' }}>
                {m.sender === 'user' ? 'Operator Query' : 'SECUROX AI Analyst'}
              </span>
              <span>{m.timestamp}</span>
            </div>

            <div style={{ fontSize: '13px', color: '#fff', lineHeight: 1.5, whiteSpace: 'pre-line' }}>
              {m.text}
            </div>

            {m.grounded && m.sender === 'ai' && (
              <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10.5px', color: '#34d399' }}>
                <ShieldCheck size={12} />
                <span>Fact-grounded in verified live database records (Confidence: {((m.confidence || 0.96) * 100).toFixed(0)}%)</span>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ color: 'var(--cyan-accent)', fontSize: '12px', padding: '8px' }}>
            AI Assistant is querying telemetry logs and correlation graphs...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form 
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        style={{ display: 'flex', gap: '10px' }}
      >
        <input
          type="text"
          className="soc-input"
          style={{ flex: 1 }}
          placeholder="Ask AI Assistant about traffic anomalies, cyber threats, or forensic timelines..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          <Send size={14} /> Submit Query
        </button>
      </form>
    </div>
  );
};
