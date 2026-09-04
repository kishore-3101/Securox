import React from 'react';
import { FileText, Shield, Clock, Compass, Activity, ArrowRight } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const ForensicsView = () => {
  const { incidents, setActiveView, setSelectedIncidentId } = useTraffic();

  const handleInspect = (incId) => {
    setSelectedIncidentId(incId);
    setActiveView('incident-detail');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>DIGITAL FORENSICS INVESTIGATION DESK</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Multi-Domain Incident Reconstruction: Physical Congestion, Controller Telemetry & Network Evidence
        </p>
      </div>

      {/* Forensics Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {incidents.map(inc => (
          <div key={inc.incident_id} className="soc-card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan-accent)' }}>
                  {inc.incident_id}
                </span>
                <span style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>{inc.title}</span>
              </div>
              <SeverityBadge severity={inc.severity} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', background: 'var(--bg-surface)', padding: '10px', borderRadius: '6px', fontSize: '12px', margin: '8px 0' }}>
              <div>📍 Location: <strong style={{ color: '#fff' }}>{inc.location}</strong></div>
              <div>⚡ Incident Type: <strong style={{ color: 'var(--cyan-accent)' }}>{inc.type}</strong></div>
              <div>🛡️ Risk Score: <strong style={{ color: inc.risk_score > 70 ? '#ef4444' : '#f59e0b' }}>{inc.risk_score}/100</strong></div>
              <div>👤 Assigned To: <strong style={{ color: '#fff' }}>{inc.assigned_to || 'Unassigned'}</strong></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                Detected: {inc.detected_at ? new Date(inc.detected_at).toLocaleString() : '—'}
              </span>
              <button className="btn btn-primary btn-sm" onClick={() => handleInspect(inc.incident_id)}>
                Open Forensic Dossier & Evidence <ArrowRight size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
