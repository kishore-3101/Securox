import React, { useState, useEffect } from 'react';
import { FileText, Shield, User, Clock } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const AuditLogView = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/system/audit-logs')
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>IMMUTABLE OPERATIONAL AUDIT LOG</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Tamper-evident record of operator actions, signal overrides, incident resolutions & system logins
        </p>
      </div>

      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Operator / User</th>
                <th>Action Executed</th>
                <th>Target Type</th>
                <th>Target ID</th>
                <th>IP Address</th>
                <th>Status</th>
                <th>Action Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
                    No audit records loaded.
                  </td>
                </tr>
              ) : (
                logs.map(l => (
                  <tr key={l.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                      {l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : '—'}
                    </td>
                    <td>
                      <strong style={{ color: '#fff' }}>{l.username}</strong>
                    </td>
                    <td><span className="badge badge-info">{l.action}</span></td>
                    <td>{l.target_type || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{l.target_id || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>{l.ip_address}</td>
                    <td><SeverityBadge severity="SUCCESS" text="SUCCESS" /></td>
                    <td style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {JSON.stringify(l.details || {})}
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
