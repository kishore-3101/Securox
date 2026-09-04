import React, { useState } from 'react';
import { Shield, AlertTriangle, ArrowRight, CheckCircle, Clock } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const IncidentsView = () => {
  const { incidents, setActiveView, setSelectedIncidentId } = useTraffic();
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const filtered = incidents.filter(i => {
    if (filterSeverity === 'ALL') return true;
    return i.severity === filterSeverity;
  });

  const handleOpenIncident = (id) => {
    setSelectedIncidentId(id);
    setActiveView('incident-detail');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>INCIDENT MANAGEMENT & RESPONSE</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Lifecycle Tracking: Detected → Triaged → Acknowledged → Investigating → Contained → Resolved
          </p>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
            <button
              key={sev}
              className={`btn btn-sm ${filterSeverity === sev ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilterSeverity(sev)}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Title / Summary</th>
                <th>Severity</th>
                <th>Type</th>
                <th>Location</th>
                <th>Risk Score</th>
                <th>Status</th>
                <th>Assigned Operator</th>
                <th>Detected At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(inc => (
                <tr key={inc.incident_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                    {inc.incident_id}
                  </td>
                  <td>
                    <strong style={{ color: '#fff' }}>{inc.title}</strong>
                  </td>
                  <td>
                    <SeverityBadge severity={inc.severity} />
                  </td>
                  <td>
                    <span className="badge badge-info">{inc.type}</span>
                  </td>
                  <td>{inc.location}</td>
                  <td>
                    <strong style={{ color: inc.risk_score > 80 ? '#ef4444' : '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                      {inc.risk_score ? inc.risk_score.toFixed(0) : '—'} / 100
                    </strong>
                  </td>
                  <td>
                    <span style={{ 
                      fontSize: '11px', 
                      fontWeight: 600,
                      color: inc.status === 'RESOLVED' ? '#34d399' : (inc.status === 'DETECTED' ? '#ef4444' : '#38bdf8')
                    }}>
                      {inc.status}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{inc.assigned_to || 'Unassigned'}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    {inc.detected_at ? new Date(inc.detected_at).toLocaleTimeString() : '—'}
                  </td>
                  <td>
                    <button 
                      className="btn btn-outline btn-sm"
                      onClick={() => handleOpenIncident(inc.incident_id)}
                    >
                      Investigate <ArrowRight size={11} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
