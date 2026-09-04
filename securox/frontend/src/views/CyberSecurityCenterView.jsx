import React, { useState, useEffect } from 'react';
import { Lock, Shield, Server, Terminal, AlertTriangle, Eye, ArrowRight } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { KpiCard } from '../components/common/KpiCard';

export const CyberSecurityCenterView = () => {
  const { setActiveView } = useTraffic();
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/cyber/threats')
      .then(res => res.json())
      .then(data => {
        setThreats(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>CYBER SECURITY OPERATIONS CENTER (SOC)</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Real-Time Cyber Threat Defense across Cameras, Traffic Controllers, Sensors & Edge Gateways
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-primary" onClick={() => setActiveView('threat-hunting')}>
            <Terminal size={14} /> Threat Hunting Console
          </button>
          <button className="btn btn-outline" onClick={() => setActiveView('asset-security')}>
            <Server size={14} /> Asset Inventory
          </button>
        </div>
      </div>

      {/* Top Cyber Metrics */}
      <div className="soc-kpi-grid">
        <KpiCard
          title="ACTIVE CYBER THREATS"
          value={threats.length}
          trend={threats.length > 0 ? "ATTACK SUSPECTED" : "NOMINAL"}
          severity={threats.length > 0 ? "HIGH" : "INFO"}
          icon={Lock}
        />
        <KpiCard
          title="OT FIREWALL STATUS"
          value="ENFORCING"
          trend="0 BYPASS"
          severity="INFO"
          icon={Shield}
        />
        <KpiCard
          title="CONTROLLER INTEGRITY"
          value="98.5%"
          trend="NTCIP SAFE"
          severity="INFO"
          icon={Server}
        />
        <KpiCard
          title="PORT SCAN DETECTORS"
          value="ACTIVE"
          trend="VLAN-20 PROBED"
          severity="MEDIUM"
          icon={Terminal}
        />
      </div>

      {/* Cyber Threat Feed */}
      <div className="soc-card">
        <div className="soc-card-header">
          <div className="soc-card-title">
            <Lock size={15} color="#ef4444" />
            LIVE CYBER THREAT FEED & INCIDENT EVIDENCE
          </div>
          <span className="badge badge-info">{threats.length} Active Detections</span>
        </div>

        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Threat ID</th>
                <th>Threat Type</th>
                <th>Target Asset</th>
                <th>Location</th>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Risk Score</th>
                <th>Source IDS</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {threats.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
                    Zero malicious cyber intrusions flagged on OT network.
                  </td>
                </tr>
              ) : (
                threats.map(t => (
                  <tr key={t.threat_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                      {t.threat_id}
                    </td>
                    <td>
                      <strong style={{ color: '#fff' }}>{t.threat_type}</strong>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{t.asset_id}</td>
                    <td>{t.location}</td>
                    <td>
                      <SeverityBadge severity={t.severity} />
                    </td>
                    <td>{(t.confidence * 100).toFixed(0)}%</td>
                    <td>
                      <strong style={{ color: t.risk_score > 80 ? '#ef4444' : '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                        {t.risk_score} / 100
                      </strong>
                    </td>
                    <td>{t.source}</td>
                    <td>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: '#f87171' }}>{t.status}</span>
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
