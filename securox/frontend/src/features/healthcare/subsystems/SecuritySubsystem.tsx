import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  Activity,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle2,
  Lock,
  FileCheck,
  Server,
  Network,
  Users,
} from 'lucide-react';
import { BreakGlassEvent } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface SecuritySubsystemProps {
  userRole: string;
}

export const SecuritySubsystem: React.FC<SecuritySubsystemProps> = ({ userRole }) => {
  const [breakGlassLogs, setBreakGlassLogs] = useState<BreakGlassEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getBreakGlassLogs();
      if (res && res.logs) {
        setBreakGlassLogs(res.logs);
      }
    } catch (err) {
      console.error('Error fetching break-glass logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleSimulateExfiltration = async () => {
    setSimulating(true);
    try {
      const res = await healthcareService.simulateExfiltration();
      setSimResult(res);
    } catch (err: any) {
      alert(`Simulation error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Simulation Result Alert Banner */}
      {simResult && (
        <div className="bg-rose-950/60 border border-rose-500 rounded-xl p-5 shadow-2xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-rose-400 font-bold">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
              <span>CAREGUARD ZERO-TRUST MASS EXFILTRATION INTERCEPTION</span>
            </div>
            <span className="text-[10px] bg-rose-900 text-rose-200 px-2 py-0.5 rounded border border-rose-700">
              BLOCKED
            </span>
          </div>

          <p className="text-slate-200 text-xs">
            <b>Incident:</b> Unauthorized mass bulk clinical records query from anomalous IP 185.220.101.5 (London, UK VPN). Intercepted at database boundary before egress.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-950/80 p-3 rounded-lg border border-slate-800">
            <div>Decision: <b className="text-rose-400">{simResult.evaluation?.decision || 'BLOCKED'}</b></div>
            <div>Risk Score: <b className="text-rose-400">{simResult.evaluation?.risk_score || 94} / 100</b></div>
            <div>SOC Incident: <b className="text-sky-400">{simResult.evaluation?.incident_id || 'INC-HC-0089'}</b></div>
            <div>Escalation: <b className="text-emerald-400">Hospital IT Security</b></div>
          </div>
        </div>
      )}

      {/* Header & Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Hospital IT Security, Break-Glass Audit & Blast-Radius
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Forensic break-glass accountability, risk score elevation ledger, and cross-tier dependency blast radius
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={handleSimulateExfiltration}
            disabled={simulating}
            className="px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-2 shadow-lg shadow-rose-900/30 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : ''}`} />
            <span>{simulating ? 'Running Attack Demo...' : 'Simulate Exfiltration (Scenario 03)'}</span>
          </button>
          <button
            onClick={fetchLogs}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Break-Glass Immutable Audit Trail Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-rose-400" />
            <span>Break-Glass Forensic Audit Trail ({breakGlassLogs.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">Immutable Cryptographic Audit Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Audit ID</th>
                <th className="px-3.5 py-2.5">Clinician</th>
                <th className="px-3.5 py-2.5">Role</th>
                <th className="px-3.5 py-2.5">Target Patient</th>
                <th className="px-3.5 py-2.5">Mandatory Emergency Reason</th>
                <th className="px-3.5 py-2.5">Risk Delta</th>
                <th className="px-3.5 py-2.5">SOC Incident</th>
                <th className="px-3.5 py-2.5">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {breakGlassLogs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No break-glass emergency access events recorded.
                  </td>
                </tr>
              ) : (
                breakGlassLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{log.id}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-slate-200">{log.username}</td>
                    <td className="px-3.5 py-2.5 text-slate-400 uppercase">{log.role}</td>
                    <td className="px-3.5 py-2.5 font-bold text-rose-400">{log.patient_id}</td>
                    <td className="px-3.5 py-2.5 text-slate-300 max-w-sm truncate" title={log.reason}>
                      {log.reason}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">
                        {log.previous_risk_score} &rarr; {log.new_risk_score} (+35.0)
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 font-bold text-amber-400">{log.security_incident_id}</td>
                    <td className="px-3.5 py-2.5 text-slate-400 text-[10px]">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cyber Blast-Radius & Asset Dependency Topology */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Network className="w-4 h-4 text-sky-400" />
            <span>Clinical Cyber Blast-Radius & Dependency Cartography</span>
          </div>
          <span className="text-[11px] text-slate-400">Layered Zero-Trust Perimeter</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-950 border border-rose-500/40 p-4 rounded-xl space-y-2">
            <div className="text-[10px] font-bold text-rose-400 uppercase">TIER 1: BEDSIDE IOMT</div>
            <div className="text-sm font-bold text-slate-200">12 Connected Devices</div>
            <p className="text-[11px] text-slate-400">
              Infusion pumps, ventilators, pacemaker gates. Containment: VLAN 99 microsegmentation.
            </p>
            <div className="text-[10px] text-emerald-400 font-bold pt-1">Blast Radius: Low (Isolated)</div>
          </div>

          <div className="bg-slate-950 border border-amber-500/40 p-4 rounded-xl space-y-2">
            <div className="text-[10px] font-bold text-amber-400 uppercase">TIER 2: WARD SWITCHES</div>
            <div className="text-sm font-bold text-slate-200">4 Access Gateways</div>
            <p className="text-[11px] text-slate-400">
              Cardiology, Surgical ICU, Emergency LAN. Containment: 802.1X Port Quarantine.
            </p>
            <div className="text-[10px] text-amber-400 font-bold pt-1">Blast Radius: Moderate</div>
          </div>

          <div className="bg-slate-950 border border-sky-500/40 p-4 rounded-xl space-y-2">
            <div className="text-[10px] font-bold text-sky-400 uppercase">TIER 3: CLINICAL EHR CORE</div>
            <div className="text-sm font-bold text-slate-200">Postgres & SQLite Core</div>
            <p className="text-[11px] text-slate-400">
              Master patient records, LIS results, billing ledgers. Containment: BOLA Guard + Field Masking.
            </p>
            <div className="text-[10px] text-sky-400 font-bold pt-1">Blast Radius: High (Protected)</div>
          </div>

          <div className="bg-slate-950 border border-emerald-500/40 p-4 rounded-xl space-y-2">
            <div className="text-[10px] font-bold text-emerald-400 uppercase">TIER 4: CITY SOC INTERLINK</div>
            <div className="text-sm font-bold text-slate-200">Securox Unified Defense</div>
            <p className="text-[11px] text-slate-400">
              Cross-domain correlation with Traffic STIG & Finance Core. Automatic incident dispatch.
            </p>
            <div className="text-[10px] text-emerald-400 font-bold pt-1">Blast Radius: City-Wide Sync</div>
          </div>
        </div>
      </div>
    </div>
  );
};
