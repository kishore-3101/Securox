import React, { useState, useEffect } from 'react';
import { Settings, Users, Shield, Lock, Database, Check } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const AdministrationView = () => {
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
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>SYSTEM ADMINISTRATION & ACCESS CONTROL</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Role-Based Access Control (RBAC), Security Hardening & Gateway Configuration
        </p>
      </div>

      {/* Security Hardening Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Lock size={15} color="var(--cyan-accent)" />
              SESSION AUTHENTICATION
            </div>
            <SeverityBadge severity="SUCCESS" text="ENFORCED" />
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <div>Algorithm: <strong style={{ color: '#fff' }}>PBKDF2-HMAC-SHA256 (100k rounds)</strong></div>
            <div>Token Standard: <strong style={{ color: '#fff' }}>JWT / HS256 (24hr TTL)</strong></div>
          </div>
        </div>

        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Shield size={15} color="var(--cyan-accent)" />
              API RATE LIMITING & CORS
            </div>
            <SeverityBadge severity="SUCCESS" text="ACTIVE" />
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <div>Protection: <strong style={{ color: '#fff' }}>Strict Origin Validation</strong></div>
            <div>Brute-Force Shield: <strong style={{ color: '#34d399' }}>Auto-Lockout (&gt;5 attempts)</strong></div>
          </div>
        </div>

        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Database size={15} color="var(--cyan-accent)" />
              DATA INTEGRITY
            </div>
            <SeverityBadge severity="SUCCESS" text="SECURE" />
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <div>Database Mode: <strong style={{ color: '#fff' }}>Dual SQLite / PostgreSQL</strong></div>
            <div>Audit Logging: <strong style={{ color: '#34d399' }}>Tamper-Evident Active</strong></div>
          </div>
        </div>
      </div>

      {/* User Accounts Table */}
      <div className="soc-card">
        <div className="soc-card-header">
          <div className="soc-card-title">
            <Users size={15} color="var(--cyan-accent)" />
            AUTHENTICATED USER DIRECTORY & ROLES
          </div>
        </div>

        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role / Privilege</th>
                <th>Status</th>
                <th>Failed Logins</th>
                <th>Account Risk</th>
                <th>Last Login</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>
                    <strong style={{ color: '#fff' }}>{u.username}</strong>
                  </td>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td><span className="badge badge-info">{u.role}</span></td>
                  <td><SeverityBadge severity={u.is_active ? 'SUCCESS' : 'CRITICAL'} text={u.is_active ? 'ACTIVE' : 'LOCKED'} /></td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{u.failed_logins}</td>
                  <td>
                    <strong style={{ color: u.risk_score > 50 ? '#ef4444' : '#34d399', fontFamily: 'var(--font-mono)' }}>
                      {u.risk_score} / 100
                    </strong>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleString() : '—'}
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
