import React, { useState } from 'react';
import { AlertTriangle, Bell, CheckCircle, ArrowRight, ShieldAlert } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { istFormat } from '../utils/dateUtils';

export const AlertCenterView = () => {
  const { alerts, setActiveView, setSelectedIncidentId, refreshAll } = useTraffic();
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const filtered = alerts.filter(a => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  });

  const handleOpenIncident = (incId) => {
    if (incId) {
      setSelectedIncidentId(incId);
      setActiveView('incident-detail');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>ACTIVE ALERT CENTER</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Real-time critical alarms across traffic velocity anomalies and cyber security probes
          </p>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map(sev => (
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
                <th>Alert ID</th>
                <th>Severity</th>
                <th>Alert Details</th>
                <th>Source Domain</th>
                <th>Location</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
                    Zero active alerts pending operator triage. All systems nominal.
                  </td>
                </tr>
              ) : (
                filtered.map(a => (
                  <tr key={a.alert_id} style={{ background: a.is_critical ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)' }}>
                      {a.alert_id}
                    </td>
                    <td>
                      <SeverityBadge severity={a.severity} />
                    </td>
                    <td>
                      <strong style={{ color: '#fff' }}>{a.title}</strong>
                    </td>
                    <td>
                      <span className="badge badge-info">{a.source}</span>
                    </td>
                    <td>{a.location}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                      {istFormat(a.timestamp)}
                    </td>
                    <td>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: a.status === 'PERMITTED' ? '#22c55e' : (a.status === 'BLOCKED' || a.is_critical) ? '#ef4444' : '#38bdf8' }}>
                        {a.status}
                      </span>
                    </td>
                    <td>
                      {a.incident_id ? (
                        <button 
                          className="btn btn-primary btn-sm"
                          onClick={() => handleOpenIncident(a.incident_id)}
                        >
                          Triage Incident <ArrowRight size={11} />
                        </button>
                      ) : (
                        <button 
                          className="btn btn-outline btn-sm"
                          onClick={() => alert(`Alert ${a.alert_id} acknowledged by operator.`)}
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
