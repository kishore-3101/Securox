import React, { useState, useEffect } from 'react';
import { Database, Shield, Server, ArrowRight } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const AssetSecurityView = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8001/api/cyber/asset-security')
      .then(res => res.json())
      .then(data => {
        setAssets(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>INFRASTRUCTURE ASSET INVENTORY & RISK MAP</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          OT Asset Hierarchy: Cameras, Traffic Controllers, Loop Detectors, Radar Sensors & Edge Gateways
        </p>
      </div>

      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Asset ID</th>
                <th>Name / Hardware</th>
                <th>Asset Type</th>
                <th>IP Address</th>
                <th>Physical Location</th>
                <th>Firmware</th>
                <th>Criticality</th>
                <th>Security Risk</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {assets.map(a => (
                <tr key={a.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                    {a.id}
                  </td>
                  <td>
                    <strong style={{ color: '#fff' }}>{a.name}</strong>
                  </td>
                  <td><span className="badge badge-info">{a.asset_type}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{a.ip_address}</td>
                  <td>{a.location}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>{a.firmware_version}</td>
                  <td><SeverityBadge severity={a.criticality} /></td>
                  <td>
                    <strong style={{ color: a.risk_score > 70 ? '#ef4444' : '#34d399', fontFamily: 'var(--font-mono)' }}>
                      {a.risk_score} / 100
                    </strong>
                  </td>
                  <td>
                    <SeverityBadge 
                      severity={a.status === 'HEALTHY' ? 'SUCCESS' : 'CRITICAL'} 
                      text={a.status}
                    />
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
