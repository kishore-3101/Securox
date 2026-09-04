import React, { useState, useEffect } from 'react';
import { Shield, ArrowLeft, Clock, CheckCircle2, AlertTriangle, FileText, UserCheck, Check } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const IncidentDetailView = () => {
  const { selectedIncidentId, setActiveView, refreshAll } = useTraffic();
  const incId = selectedIncidentId || 'INC-2026-BASELINE-01';

  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');
  const [resolutionNote, setResolutionNote] = useState('');

  const fetchDossier = async () => {
    try {
      const res = await fetch(`http://localhost:8001/api/incidents/${incId}`);
      if (res.ok) {
        const data = await res.json();
        setDossier(data);
      }
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchDossier();
  }, [incId]);

  const handleUpdateStatus = async (newStatus, note = '') => {
    try {
      setActionMsg(`Transitioning status to ${newStatus}...`);
      const res = await fetch(`http://localhost:8001/api/incidents/${incId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_status: newStatus,
          operator_name: 'Lead SOC Operator',
          note: note || resolutionNote
        })
      });
      if (res.ok) {
        setActionMsg(`Incident successfully updated to ${newStatus}.`);
        fetchDossier();
        refreshAll();
      }
    } catch (e) {
      setActionMsg('Failed to update status.');
    }
  };

  if (loading) {
    return <div style={{ color: 'var(--text-muted)', padding: '20px' }}>Loading forensic dossier...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn btn-outline btn-sm" onClick={() => setActiveView('incidents')}>
            <ArrowLeft size={14} /> Back to Incidents
          </button>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              INCIDENT DOSSIER: <span style={{ color: 'var(--cyan-accent)' }}>{dossier?.incident_id}</span>
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Digital Forensic Reconstruction & Investigation Playbook</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <SeverityBadge severity={dossier?.severity} />
          <span style={{ 
            fontSize: '11px', 
            fontWeight: 700, 
            padding: '3px 10px', 
            borderRadius: '4px',
            background: dossier?.status === 'RESOLVED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            color: dossier?.status === 'RESOLVED' ? '#34d399' : '#f87171',
            border: `1px solid ${dossier?.status === 'RESOLVED' ? '#10b981' : '#ef4444'}`
          }}>
            STATUS: {dossier?.status}
          </span>
        </div>
      </div>

      {actionMsg && (
        <div style={{ padding: '8px 12px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid var(--border-accent)', borderRadius: '4px', fontSize: '12px', color: '#38bdf8' }}>
          {actionMsg}
        </div>
      )}

      {/* Forensic Overview (What, When, Where, How, Impact) */}
      <div className="soc-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
        <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px' }}>
          <span style={{ fontSize: '10.5px', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase' }}>WHAT HAPPENED</span>
          <p style={{ fontSize: '12.5px', color: '#fff', fontWeight: 600, marginTop: '4px' }}>{dossier?.what}</p>
        </div>
        <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px' }}>
          <span style={{ fontSize: '10.5px', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase' }}>WHEN</span>
          <p style={{ fontSize: '12.5px', color: '#fff', fontWeight: 600, marginTop: '4px' }}>{dossier?.when}</p>
        </div>
        <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px' }}>
          <span style={{ fontSize: '10.5px', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase' }}>WHERE</span>
          <p style={{ fontSize: '12.5px', color: '#fff', fontWeight: 600, marginTop: '4px' }}>{dossier?.where}</p>
        </div>
        <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px' }}>
          <span style={{ fontSize: '10.5px', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase' }}>VERDICT</span>
          <p style={{ fontSize: '12.5px', color: dossier?.verdict === 'CONFIRMED' ? '#ef4444' : '#f59e0b', fontWeight: 700, marginTop: '4px' }}>
            {dossier?.verdict}
          </p>
        </div>
      </div>

      {/* Main Grid: Left Timeline & Right Lifecycle Actions & Evidence */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '20px' }}>
        {/* Left: Forensic Timeline (Requirement 22) */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Clock size={15} color="var(--cyan-accent)" />
              CHRONOLOGICAL INVESTIGATION TIMELINE
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingLeft: '8px' }}>
            {dossier?.timeline?.map((entry, idx) => (
              <div 
                key={idx}
                style={{ 
                  position: 'relative', 
                  paddingLeft: '24px', 
                  borderLeft: '2px solid var(--border-medium)',
                  paddingBottom: '8px'
                }}
              >
                <div style={{
                  position: 'absolute',
                  left: '-7px',
                  top: '0px',
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: entry.severity === 'CRITICAL' ? '#ef4444' : 'var(--cyan-accent)',
                  border: '2px solid var(--bg-card)'
                }} />
                <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  {entry.timestamp} | {entry.source}
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff', marginTop: '2px' }}>
                  {entry.title}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {entry.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Actions & Evidence Locker */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Operator Action Controls */}
          <div className="soc-card">
            <div className="soc-card-header">
              <div className="soc-card-title">
                <UserCheck size={15} color="var(--emerald)" />
                INCIDENT RESPONSE PLAYBOOK ACTIONS
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button 
                  className="btn btn-outline btn-sm"
                  onClick={() => handleUpdateStatus('ACKNOWLEDGED', 'Operator acknowledged alert')}
                  disabled={dossier?.status === 'ACKNOWLEDGED' || dossier?.status === 'RESOLVED'}
                >
                  1. Acknowledge
                </button>
                <button 
                  className="btn btn-outline btn-sm"
                  onClick={() => handleUpdateStatus('INVESTIGATING', 'Initiated active forensics')}
                  disabled={dossier?.status === 'RESOLVED'}
                >
                  2. Investigate
                </button>
                <button 
                  className="btn btn-danger btn-sm"
                  onClick={() => handleUpdateStatus('CONTAINED', 'Isolated network port & engaged failsafe')}
                  disabled={dossier?.status === 'RESOLVED'}
                >
                  3. Contain
                </button>
              </div>

              {/* Resolution Form */}
              <div style={{ marginTop: '10px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                <textarea
                  className="soc-input"
                  style={{ width: '100%', height: '60px', marginBottom: '8px', resize: 'none' }}
                  placeholder="Enter mitigation notes / root cause verification..."
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                />
                <button 
                  className="btn btn-primary"
                  onClick={() => handleUpdateStatus('RESOLVED', resolutionNote || 'Mitigation verified and traffic flow restored.')}
                  disabled={dossier?.status === 'RESOLVED'}
                  style={{ width: '100%', background: '#10b981', color: '#000' }}
                >
                  <Check size={14} /> Mark Incident as RESOLVED
                </button>
              </div>
            </div>
          </div>

          {/* Evidence Locker */}
          <div className="soc-card" style={{ flex: 1 }}>
            <div className="soc-card-header">
              <div className="soc-card-title">
                <FileText size={15} color="var(--cyan-accent)" />
                DIGITAL EVIDENCE LOCKER
              </div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', overflowX: 'auto' }}>
              <pre>{JSON.stringify(dossier?.evidence || {}, null, 2)}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
