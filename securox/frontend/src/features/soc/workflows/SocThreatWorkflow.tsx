import React, { useState } from 'react';
import { socService } from '../../../services/socService';
import {
  ShieldAlert,
  AlertTriangle,
  Lock,
  Radio,
  CheckCircle2,
  Activity,
  Terminal,
  Server,
  Zap,
  Eye,
  RefreshCw,
  Cpu,
} from 'lucide-react';

interface ThreatIncident {
  id: string;
  title: string;
  mitreTactic: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  sourceIp: string;
  targetAsset: string;
  vlan: string;
  slaMinutes: number;
  contained: boolean;
  killChainStep: number;
}

export const SocThreatWorkflow: React.FC = () => {
  const [incidents, setIncidents] = useState<ThreatIncident[]>([
    {
      id: 'INC-SEC-01',
      title: 'SCADA PLC Firmware Unauthorized Modification Attempt',
      mitreTactic: 'T0855: Unauthorized Command Message',
      severity: 'CRITICAL',
      sourceIp: '185.220.101.5 (Tor Exit)',
      targetAsset: 'PLC-SIG-04 (Gantry Controller)',
      vlan: 'VLAN 40 (Traffic OT Subnet)',
      slaMinutes: 12,
      contained: false,
      killChainStep: 4,
    },
    {
      id: 'INC-SEC-02',
      title: 'Kerberoasting & Service Ticket Harvesting Surge',
      mitreTactic: 'T1558.003: Steal or Forge Kerberos Tickets',
      severity: 'HIGH',
      sourceIp: '10.120.4.88 (Finance WS-12)',
      targetAsset: 'DC01.securox.internal',
      vlan: 'VLAN 20 (Corporate Finance)',
      slaMinutes: 38,
      contained: false,
      killChainStep: 3,
    },
    {
      id: 'INC-SEC-03',
      title: 'Healthcare DICOM Image Store Brute-Force Authentication',
      mitreTactic: 'T1110: Brute Force',
      severity: 'MEDIUM',
      sourceIp: '194.26.29.112',
      targetAsset: 'PACS-ARCHIVE-01',
      vlan: 'VLAN 30 (Hospital DMZ)',
      slaMinutes: 90,
      contained: true,
      killChainStep: 2,
    },
  ]);

  const [selectedIncId, setSelectedIncId] = useState<string>('INC-SEC-01');
  const [vlanIsolated, setVlanIsolated] = useState<boolean>(false);
  const [tokensRevoked, setTokensRevoked] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedIncident = incidents.find((i) => i.id === selectedIncId) || incidents[0];

  const handleIsolateSubnet = async () => {
    setVlanIsolated(true);
    setIncidents((prev) =>
      prev.map((i) => (i.id === selectedIncident.id ? { ...i, contained: true } : i))
    );
    setFeedback(`ZERO-TRUST ISOLATION EXECUTED: ${selectedIncident.vlan} isolated via firewall drop-all.`);
    setTimeout(() => setFeedback(null), 4500);
  };

  const handleRevokeTokens = () => {
    setTokensRevoked(true);
    setFeedback('All active JWT and OAuth2 session tokens revoked across target asset.');
    setTimeout(() => setFeedback(null), 3500);
  };

  const killChainStages = [
    { step: 1, name: 'Reconnaissance' },
    { step: 2, name: 'Initial Access' },
    { step: 3, name: 'Lateral Movement' },
    { step: 4, name: 'OT / SCADA Tampering' },
    { step: 5, name: 'Exfiltration / Impact' },
  ];

  return (
    <div className="space-y-6 font-sans">
      {/* SOC Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide">
                SOC INCIDENT RESPONSE & THREAT HUNTING
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold animate-pulse">
                ● 1 CRITICAL ATTACK ACTIVE
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">
              Active Kill-Chain Triage & Zero-Trust Containment
            </h2>
            <p className="text-xs font-mono text-slate-400">
              MITRE ATT&CK for ICS/Enterprise • Microsegmentation Automation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleIsolateSubnet}
            disabled={vlanIsolated}
            className={`px-4 py-2 rounded-xl font-mono text-xs font-bold flex items-center gap-2 shadow-lg transition ${
              vlanIsolated
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-500/20'
            }`}
          >
            <Lock className="w-4 h-4" />
            {vlanIsolated ? 'VLAN Microsegmented (Isolated)' : '1-Tap Isolate Subnet'}
          </button>
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Main Grid: Incident Queue + Threat Investigation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Incident Queue (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Threat Incidents</span>
            <span>{incidents.length} Active</span>
          </div>

          <div className="space-y-3">
            {incidents.map((inc) => {
              const isSelected = inc.id === selectedIncident.id;
              return (
                <div
                  key={inc.id}
                  onClick={() => setSelectedIncId(inc.id)}
                  className={`p-4 rounded-xl border font-mono cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-sky-500 shadow-md ring-1 ring-sky-500/50'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
                        <span>{inc.id}</span>
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                            inc.severity === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {inc.severity}
                        </span>
                      </div>
                      <div className="text-xs font-sans text-slate-300 mt-1 font-semibold line-clamp-1">
                        {inc.title}
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] text-rose-400 font-bold">
                        SLA: {inc.slaMinutes}m
                      </span>
                    </div>
                  </div>

                  <div className="text-[10px] text-sky-400 mt-2">{inc.mitreTactic}</div>

                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400">
                    <span>Target: <strong className="text-slate-200">{inc.targetAsset}</strong></span>
                    <span>{inc.contained ? '● CONTAINED' : '○ EXPOSURE OPEN'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Threat Investigation & Containment Actions (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-sky-400" />
                MITRE ATT&CK Kill-Chain Progression
              </h3>
              <p className="text-xs font-mono text-slate-400 mt-0.5">
                Incident {selectedIncident.id}: {selectedIncident.title}
              </p>
            </div>

            {/* Kill-Chain Progression Visualizer */}
            <div className="grid grid-cols-5 gap-2">
              {killChainStages.map((stage) => {
                const isPassed = stage.step < selectedIncident.killChainStep;
                const isCurrent = stage.step === selectedIncident.killChainStep;

                return (
                  <div
                    key={stage.step}
                    className={`p-2.5 rounded-xl border text-center font-mono transition ${
                      isCurrent
                        ? 'bg-rose-500/20 border-rose-500 text-rose-300 ring-1 ring-rose-500/40'
                        : isPassed
                        ? 'bg-slate-950/70 border-slate-800 text-slate-400'
                        : 'bg-slate-950/30 border-slate-800/40 text-slate-600'
                    }`}
                  >
                    <div className="text-[9px] uppercase opacity-70">Step 0{stage.step}</div>
                    <div className="text-[10px] font-bold mt-1 leading-tight">{stage.name}</div>
                    {isCurrent && (
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping mt-1" />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Forensic Telemetry Matrix */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Adversary Source IP</div>
                <div className="text-xs font-bold font-mono text-rose-400 mt-1 truncate">
                  {selectedIncident.sourceIp}
                </div>
                <div className="text-[9px] font-mono text-slate-500">Known Command & Control</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Target SCADA Asset</div>
                <div className="text-xs font-bold font-mono text-cyan-400 mt-1 truncate">
                  {selectedIncident.targetAsset}
                </div>
                <div className="text-[9px] font-mono text-slate-500">Firmware v3.12 (Vulnerable)</div>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Network Segment</div>
                <div className="text-xs font-bold font-mono text-amber-400 mt-1 truncate">
                  {selectedIncident.vlan}
                </div>
                <div className="text-[9px] font-mono text-slate-500">
                  {vlanIsolated ? 'ISOLATED' : 'OPEN TO CORE'}
                </div>
              </div>
            </div>

            {/* Tactical Containment Action Buttons */}
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <div className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
                Tactical Containment Actions
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={handleIsolateSubnet}
                  disabled={vlanIsolated}
                  className={`p-3.5 rounded-xl font-mono text-xs font-bold border transition flex items-center justify-center gap-2 ${
                    vlanIsolated
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : 'bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border-rose-500/40'
                  }`}
                >
                  <Server className="w-4 h-4" />
                  {vlanIsolated ? 'VLAN 40 Segment Isolated' : 'Isolate VLAN 40 (Traffic OT)'}
                </button>

                <button
                  onClick={handleRevokeTokens}
                  disabled={tokensRevoked}
                  className={`p-3.5 rounded-xl font-mono text-xs font-bold border transition flex items-center justify-center gap-2 ${
                    tokensRevoked
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
                  }`}
                >
                  <Zap className="w-4 h-4 text-cyan-400" />
                  {tokensRevoked ? 'Tokens Revoked' : 'Revoke Session Auth Tokens'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
