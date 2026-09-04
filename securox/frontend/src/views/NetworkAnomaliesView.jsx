import React, { useState } from 'react';
import { Server, Radio, Shield, AlertTriangle, ArrowRight } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { useTraffic } from '../context/TrafficContext';

export const NetworkAnomaliesView = () => {
  const { setActiveView } = useTraffic();

  const networkFlows = [
    {
      flow_id: "FLOW-9821",
      source_ip: "192.168.10.84",
      dest_ip: "192.168.10.24 (CAM-04)",
      protocol: "TCP / SYN-SCAN",
      port_range: "80, 554, 502, 161, 8080",
      rate_pps: 420,
      severity: "HIGH",
      flag: "PORT_SCAN",
      status: "BLOCKED_BY_FIREWALL"
    },
    {
      flow_id: "FLOW-9822",
      source_ip: "185.220.101.44 (External)",
      dest_ip: "192.168.10.21 (CAM-01)",
      protocol: "RTSP / ONVIF",
      port_range: "554",
      rate_pps: 85,
      severity: "HIGH",
      flag: "UNAUTHORIZED_BURST",
      status: "ISOLATED"
    },
    {
      flow_id: "FLOW-9823",
      source_ip: "192.168.10.1 (Gateway)",
      dest_ip: "192.168.10.84 (CTRL-INT12)",
      protocol: "NTCIP 1202 / UDP",
      port_range: "5150",
      rate_pps: 12,
      severity: "CRITICAL",
      flag: "UNAUTHORIZED_OVERRIDE",
      status: "FLAGGED_FOR_AUDIT"
    },
    {
      flow_id: "FLOW-9824",
      source_ip: "192.168.10.101 (Sensor Loop)",
      dest_ip: "10.0.4.15 (SOC Host)",
      protocol: "MQTT / TLS",
      port_range: "8883",
      rate_pps: 5,
      severity: "LOW",
      flag: "NORMAL_CADENCE",
      status: "APPROVED"
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>OT NETWORK TELEMETRY & INTRUSION DETECTION</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Deep Packet Metadata Inspection across Highway Surveillance & Controller Subnets
          </p>
        </div>
        <div className="sim-badge">EDGE IDS TELEMETRY</div>
      </div>

      <div className="soc-card">
        <div className="soc-card-header">
          <div className="soc-card-title">
            <Server size={15} color="var(--cyan-accent)" />
            MONITORED OT NETWORK FLOWS
          </div>
        </div>

        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Flow ID</th>
                <th>Source IP</th>
                <th>Destination Asset</th>
                <th>Protocol</th>
                <th>Target Ports</th>
                <th>Packet Rate</th>
                <th>Threat Flag</th>
                <th>Severity</th>
                <th>Mitigation State</th>
              </tr>
            </thead>
            <tbody>
              {networkFlows.map(f => (
                <tr key={f.flow_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)' }}>{f.flow_id}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{f.source_ip}</td>
                  <td>{f.dest_ip}</td>
                  <td><span className="badge badge-info">{f.protocol}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{f.port_range}</td>
                  <td>{f.rate_pps} pps</td>
                  <td><strong style={{ color: f.severity === 'CRITICAL' ? '#ef4444' : (f.severity === 'HIGH' ? '#f97316' : '#34d399') }}>{f.flag}</strong></td>
                  <td><SeverityBadge severity={f.severity} /></td>
                  <td><span className="badge badge-info">{f.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
