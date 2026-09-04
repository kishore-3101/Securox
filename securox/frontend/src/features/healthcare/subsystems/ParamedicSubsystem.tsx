import React, { useState } from 'react';
import {
  HeartPulse,
  Activity,
  Radio,
  Send,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Save,
  Clock,
  Compass,
} from 'lucide-react';
import { healthcareService } from '../../../services/healthcareService';

interface ParamedicSubsystemProps {
  userRole: string;
}

export const ParamedicSubsystem: React.FC<ParamedicSubsystemProps> = ({ userRole }) => {
  const [dispatchId, setDispatchId] = useState('CAD-EMS-001');
  const [ambulanceId] = useState('AMB-01 (ALS Unit)');
  const [paramedicName] = useState('Paramedic Sunita Rao, EMT-P');

  // Live in-transit vitals
  const [hr, setHr] = useState<number>(118);
  const [bpSys, setBpSys] = useState<number>(158);
  const [bpDia, setBpDia] = useState<number>(94);
  const [spo2, setSpo2] = useState<number>(93);
  const [ecgFinding, setEcgFinding] = useState('ST-Elevation 3.5mm in leads II, III, aVF (Acute Inferior STEMI)');
  const [triageNotes, setTriageNotes] = useState(
    'Patient 58M presenting with acute substernal chest pain, diaphoresis, and radiating jaw pain. 325mg Aspirin given PO. O2 delivered at 4L/min via nasal cannula. Cath lab activation requested.'
  );

  const [transmitting, setTransmitting] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const handleTransmitUplink = async (e: React.FormEvent) => {
    e.preventDefault();
    setTransmitting(true);
    try {
      await healthcareService.updateEmergencyDispatch(dispatchId, {
        status: 'IN_TRANSIT',
        vitals: {
          hr: Number(hr),
          bp: `${bpSys}/${bpDia}`,
          spo2: Number(spo2),
          ecg: ecgFinding,
        },
      });
      setActionMsg(
        `Pre-Hospital Vitals Uplink successfully transmitted to City General Hospital ED Trauma Bay 1.`
      );
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      alert(`Uplink failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setTransmitting(false);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {actionMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <div className="text-slate-200 font-bold">{paramedicName}</div>
            <div className="text-slate-400 text-[11px]">Unit: {ambulanceId} • CAD Mission: {dispatchId}</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px]">
            Destination: <b className="text-rose-400">City General Hospital ED (Bay 1)</b>
          </span>
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>ED Uplink Active</span>
          </span>
        </div>
      </div>

      {/* Vitals Uplink Form */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <HeartPulse className="w-4 h-4 text-rose-400" />
            <span>Real-time Pre-Hospital Cardiac Telemetry Uplink</span>
          </div>
          <span className="text-[11px] text-slate-400">Continuous 4G/5G Hospital Broadcast</span>
        </div>

        <form onSubmit={handleTransmitUplink} className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-slate-400 mb-1">Heart Rate (BPM)</label>
              <input
                type="number"
                value={hr}
                onChange={(e) => setHr(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-400 font-bold text-base outline-none focus:border-rose-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">BP Systolic (mmHg)</label>
              <input
                type="number"
                value={bpSys}
                onChange={(e) => setBpSys(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-400 font-bold text-base outline-none focus:border-rose-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">BP Diastolic (mmHg)</label>
              <input
                type="number"
                value={bpDia}
                onChange={(e) => setBpDia(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-400 font-bold text-base outline-none focus:border-rose-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">SpO2 Oxygen (%)</label>
              <input
                type="number"
                value={spo2}
                onChange={(e) => setSpo2(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sky-400 font-bold text-base outline-none focus:border-rose-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">12-Lead ECG Interpretation & Rhythm Finding</label>
            <input
              type="text"
              value={ecgFinding}
              onChange={(e) => setEcgFinding(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-300 font-bold outline-none focus:border-rose-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Pre-Hospital Field Triage & Intervention Notes</label>
            <textarea
              rows={3}
              value={triageNotes}
              onChange={(e) => setTriageNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 outline-none focus:border-rose-500 resize-none"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={transmitting}
              className="px-5 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-2 shadow-lg shadow-rose-950 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{transmitting ? 'Transmitting...' : 'Transmit Telemetry to ED Trauma Bay'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
