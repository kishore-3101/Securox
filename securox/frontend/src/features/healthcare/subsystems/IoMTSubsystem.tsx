import React, { useState, useEffect } from 'react';
import {
  Radio,
  Activity,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  Zap,
  Lock,
  Search,
  CheckCircle2,
  Server,
  Cpu,
} from 'lucide-react';
import { IoMTDevice } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface IoMTSubsystemProps {
  userRole: string;
}

export const IoMTSubsystem: React.FC<IoMTSubsystemProps> = ({ userRole }) => {
  const [devices, setDevices] = useState<IoMTDevice[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [isolatingId, setIsolatingId] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getIoMTDevices();
      if (res && res.devices) {
        setDevices(res.devices);
      }
    } catch (err) {
      console.error('Error fetching IoMT devices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await healthcareService.scanIoMTDevices();
      if (res && res.devices) {
        setDevices(res.devices);
      }
      setActionMsg(`IoMT Network Scan Complete: ${res.devices_scanned} devices inspected, ${res.anomalies_detected} anomalies flagged.`);
      setTimeout(() => setActionMsg(null), 5000);
    } catch (err: any) {
      alert(`Scan failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setScanning(false);
    }
  };

  const handleIsolate = async (deviceId: string, deviceName: string) => {
    setIsolatingId(deviceId);
    try {
      const res = await healthcareService.isolateIoMTDevice(
        deviceId,
        'QUARANTINE_VLAN_99',
        'Bedside IoMT abnormal flow-rate and buffer overflow detected'
      );
      setDevices((prev) =>
        prev.map((d) =>
          d.id === deviceId
            ? { ...d, status: 'QUARANTINED', quarantine: true, risk_score: 5 }
            : d
        )
      );
      setActionMsg(`Device ${deviceName} (${deviceId}) successfully quarantined to ${res.quarantine_vlan}.`);
      setTimeout(() => setActionMsg(null), 5000);
    } catch (err: any) {
      alert(`Isolation failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setIsolatingId(null);
    }
  };

  const anomalousCount = devices.filter((d) => d.status === 'ANOMALOUS' || d.risk_score > 60).length;

  return (
    <div className="space-y-6 font-mono text-xs">
      {actionMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Header & Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-rose-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Bedside IoMT Medical Device Defense & Microsegmentation
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time HL7 protocol inspection, infusion pump flow-rate anomaly ML detection, and zero-downtime VLAN isolation
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-2 shadow-lg shadow-rose-900/20 disabled:opacity-50"
          >
            <Activity className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            <span>{scanning ? 'Inspecting Telemetry...' : 'Run IoMT Threat Scan'}</span>
          </button>
          <button
            onClick={fetchDevices}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Device Cartography Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-sky-400" />
            <span>Connected Medical Equipment Cartography ({devices.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">
            {anomalousCount > 0 ? (
              <b className="text-rose-400">{anomalousCount} Device Anomalies Active</b>
            ) : (
              <span className="text-emerald-400 font-bold">All Streams Nominal</span>
            )}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Device ID</th>
                <th className="px-3.5 py-2.5">Equipment Name</th>
                <th className="px-3.5 py-2.5">Ward / Department</th>
                <th className="px-3.5 py-2.5">IP & MAC</th>
                <th className="px-3.5 py-2.5">Protocol</th>
                <th className="px-3.5 py-2.5">Cyber Risk</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Defense Containment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {devices.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No medical devices scanned.
                  </td>
                </tr>
              ) : (
                devices.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{d.id}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-slate-200">{d.name}</td>
                    <td className="px-3.5 py-2.5 text-slate-400">{d.department}</td>
                    <td className="px-3.5 py-2.5 text-slate-300">
                      <div>{d.ip_address}</div>
                      <div className="text-[10px] text-slate-500">{d.mac_address}</div>
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        {d.protocol}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`font-bold ${
                          d.risk_score > 70
                            ? 'text-rose-400 animate-pulse'
                            : d.risk_score > 40
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {d.risk_score}%
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          d.status === 'QUARANTINED'
                            ? 'bg-purple-950 text-purple-300 border border-purple-800'
                            : d.status === 'ANOMALOUS'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800 animate-pulse'
                            : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}
                      >
                        {d.status}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-right">
                      {d.status === 'QUARANTINED' ? (
                        <span className="text-[11px] text-purple-400 font-bold">VLAN 99 ISOLATED</span>
                      ) : (
                        <button
                          onClick={() => handleIsolate(d.id, d.name)}
                          disabled={isolatingId === d.id}
                          className="px-2.5 py-1 rounded bg-rose-600/20 text-rose-400 border border-rose-500/40 hover:bg-rose-600/30 text-[11px] font-bold transition flex items-center gap-1 inline-flex disabled:opacity-50"
                        >
                          <Lock className="w-3 h-3" />
                          <span>{isolatingId === d.id ? 'Isolating...' : 'Isolate to VLAN 99'}</span>
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
