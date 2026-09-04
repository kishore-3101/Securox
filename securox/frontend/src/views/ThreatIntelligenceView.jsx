import React from 'react';
import { Terminal, Shield, AlertTriangle, Cpu } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const ThreatIntelligenceView = () => {
  const threatSignatures = [
    {
      sig_id: "SIG-CP-001",
      name: "Coordinated NTCIP Controller Phase Hold + Gridlock Induction",
      target: "Traffic Signal Controllers (NTCIP 1202 / UDP 5150)",
      vector: "Cyber-Physical Manipulation",
      severity: "CRITICAL",
      cve_refs: "CVE-2023-4212, NTCIP-AUTH-BYPASS",
      remediation: "Force hardware watchdog fail-safe to FLASHING RED and isolate field VLAN."
    },
    {
      sig_id: "SIG-CAM-002",
      name: "RTSP ONVIF Credential Stuffing & Stream Interception",
      target: "Optical Surveillance Cameras (RTSP 554 / HTTP 80)",
      vector: "Surveillance Blindspot Generation",
      severity: "HIGH",
      cve_refs: "CVE-2022-30563, ONVIF-REPLAY",
      remediation: "Rotate cryptographic certificates and enforce IEEE 802.1X port security."
    },
    {
      sig_id: "SIG-SEN-003",
      name: "Inductive Loop Telemetry Freeze / Zero-Reading Spoofing",
      target: "Roadway Inductive Loop Detectors & Radar Probes",
      vector: "Algorithm De-synchronization",
      severity: "MEDIUM",
      cve_refs: "MODBUS-CLEAR-TEXT, MQTT-INJECT",
      remediation: "Cross-validate readings against Computer Vision vehicle counts."
    },
    {
      sig_id: "SIG-NET-004",
      name: "Volumetric SYN/ACK Flood on Core Traffic Gateway",
      target: "Central Telemetry Ingestion Host (Port 8000 / 443)",
      vector: "Denial of Service (DoS)",
      severity: "HIGH",
      cve_refs: "TCP-SYN-BURST",
      remediation: "Rate limit incoming SYN packets and activate edge scrubbing firewall."
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>THREAT INTELLIGENCE & CYBER-PHYSICAL SIGNATURES</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Known Attack Vectors, CVE Reference Catalog & Defensive Response Playbooks
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {threatSignatures.map(sig => (
          <div key={sig.sig_id} className="soc-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                {sig.sig_id}
              </span>
              <SeverityBadge severity={sig.severity} />
            </div>

            <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
              {sig.name}
            </div>

            <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', marginBottom: '8px' }}>
              <div>Target: <strong style={{ color: 'var(--text-muted)' }}>{sig.target}</strong></div>
              <div>Vector: <strong style={{ color: 'var(--text-muted)' }}>{sig.vector}</strong></div>
              <div>References: <code style={{ color: 'var(--cyan-accent)' }}>{sig.cve_refs}</code></div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '10px', borderRadius: '4px', fontSize: '11.5px', borderLeft: '3px solid #06b6d4', marginTop: '10px' }}>
              <strong style={{ color: '#fff', display: 'block', marginBottom: '2px' }}>Standard Playbook Remediation:</strong>
              <span style={{ color: 'var(--text-muted)' }}>{sig.remediation}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
