import React, { useState, useEffect } from 'react';
import { Sliders, Shield, AlertTriangle, Check, RefreshCw } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const TrafficSignalsView = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const fetchSignals = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/traffic/signals');
      if (res.ok) {
        const data = await res.json();
        setSignals(data);
      }
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleOverride = async (signalId, newState) => {
    try {
      setActionMsg(`Overriding ${signalId} to ${newState}...`);
      const res = await fetch(`http://localhost:8001/api/traffic/signals/${signalId}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_state: newState,
          timing_plan: 'OPERATOR_MANUAL_HOLD',
          operator_note: `Manual override to ${newState}`
        })
      });
      if (res.ok) {
        setActionMsg(`Signal ${signalId} successfully forced to ${newState}. Audit logged.`);
        fetchSignals();
      }
    } catch (e) {
      setActionMsg('Override action failed.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>TRAFFIC SIGNAL & NTCIP CONTROLLER SECURITY</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Phase Timing Verification, Conflicting Green Interlocks & Failsafe Controls
          </p>
        </div>
        <div className="sim-badge">NTCIP 1202 PROTOCOL MONITOR</div>
      </div>

      {actionMsg && (
        <div style={{ padding: '8px 12px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid var(--border-accent)', borderRadius: '4px', fontSize: '12px', color: '#38bdf8' }}>
          {actionMsg}
        </div>
      )}

      {/* Signals Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {signals.map(sig => {
          const isCompromised = sig.is_compromised || sig.status === 'MANIPULATED';
          return (
            <div key={sig.id} className="soc-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan-accent)' }}>
                  {sig.id}
                </span>
                <SeverityBadge 
                  severity={isCompromised ? 'CRITICAL' : 'SUCCESS'}
                  text={isCompromised ? 'MANIPULATED' : sig.status}
                />
              </div>

              <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>
                Intersection: {sig.intersection_id}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '10px' }}>
                Controller: <strong style={{ color: 'var(--text-main)' }}>{sig.controller_id}</strong>
              </div>

              {/* Traffic Light State Visualizer */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '6px', background: '#070b14', padding: '6px 10px', borderRadius: '20px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: sig.current_state === 'RED' ? '#ef4444' : '#334155', boxShadow: sig.current_state === 'RED' ? '0 0 8px #ef4444' : 'none' }} />
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: sig.current_state === 'YELLOW' ? '#f59e0b' : '#334155', boxShadow: sig.current_state === 'YELLOW' ? '0 0 8px #f59e0b' : 'none' }} />
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: sig.current_state === 'GREEN' ? '#10b981' : '#334155', boxShadow: sig.current_state === 'GREEN' ? '0 0 8px #10b981' : 'none' }} />
                </div>

                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  <div>Phase: <strong style={{ color: '#fff' }}>{sig.current_state}</strong></div>
                  <div>Cycle: <strong style={{ color: '#fff' }}>{sig.cycle_time}s</strong> ({sig.timing_plan})</div>
                </div>
              </div>

              {/* Failsafe Override Controls */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <button 
                  className="btn btn-primary btn-sm" 
                  onClick={() => handleOverride(sig.id, 'GREEN')}
                  style={{ flex: 1 }}
                >
                  Force Green
                </button>
                <button 
                  className="btn btn-outline btn-sm" 
                  onClick={() => handleOverride(sig.id, 'FLASHING_RED')}
                  style={{ flex: 1, color: '#f59e0b' }}
                >
                  Failsafe Amber
                </button>
                <button 
                  className="btn btn-danger btn-sm" 
                  onClick={() => handleOverride(sig.id, 'RED')}
                  style={{ flex: 1 }}
                >
                  Hold Red
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
