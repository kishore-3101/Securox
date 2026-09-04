import React, { useState, useEffect } from 'react';
import { Eye, Shield, UserX, AlertTriangle } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const UserSecurityView = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>OPERATOR ACCOUNT SECURITY & BEHAVIORAL RISK</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Credential Brute-Force Monitoring, Impossible Travel, Privilege Escalation & User Risk Scores
        </p>
      </div>

      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Operator Username</th>
                <th>Full Name</th>
                <th>Privilege Level</th>
                <th>Failed Login Attempts</th>
                <th>Behavioral Risk Score</th>
                <th>Risk Category</th>
                <th>Account Status</th>
                <th>Last Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td><strong style={{ color: '#fff' }}>{u.username}</strong></td>
                  <td>{u.full_name}</td>
                  <td><span className="badge badge-info">{u.role}</span></td>
                  <td>
                    <span style={{ color: u.failed_logins > 0 ? '#ef4444' : 'var(--text-muted)', fontWeight: 600 }}>
                      {u.failed_logins} failed
                    </span>
                  </td>
                  <td>
                    <strong style={{ color: u.risk_score > 60 ? '#ef4444' : '#34d399', fontFamily: 'var(--font-mono)' }}>
                      {u.risk_score} / 100
                    </strong>
                  </td>
                  <td>
                    <SeverityBadge severity={u.risk_score > 60 ? 'HIGH' : (u.risk_score > 30 ? 'MEDIUM' : 'LOW')} />
                  </td>
                  <td>
                    <span style={{ color: u.is_active ? '#34d399' : '#ef4444', fontWeight: 600 }}>
                      {u.is_active ? 'ACTIVE' : 'LOCKED'}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleTimeString() : 'Never'}
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
