import React, { useState, useEffect } from 'react';
import {
  HeartPulse,
  AlertTriangle,
  Radio,
  Clock,
  RotateCcw,
  CheckCircle2,
  Plus,
  Compass,
  MapPin,
  Ambulance,
  PhoneCall,
  Activity,
} from 'lucide-react';
import { EmergencyDispatch, TriagePriority } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface EmergencySubsystemProps {
  userRole: string;
}

export const EmergencySubsystem: React.FC<EmergencySubsystemProps> = ({ userRole }) => {
  const [dispatches, setDispatches] = useState<EmergencyDispatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [showIntakeModal, setShowIntakeModal] = useState(false);

  // New emergency dispatch state
  const [callerName, setCallerName] = useState('Emergency Hotline 108');
  const [emergencyType, setEmergencyType] = useState('Acute STEMI Infarction');
  const [triagePriority, setTriagePriority] = useState<TriagePriority>('P1_CRITICAL');
  const [originLocation, setOriginLocation] = useState('Indiranagar 100ft Road');
  const [ambulanceId, setAmbulanceId] = useState('AMB-01');
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchDispatches = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getEmergencyDispatches();
      if (res && res.dispatches) {
        setDispatches(res.dispatches);
      }
    } catch (err) {
      console.error('Error fetching emergency dispatches:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDispatches();
  }, []);

  const handleCreateDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await healthcareService.createEmergencyDispatch({
        ambulance_id: ambulanceId,
        paramedic_id: 'paramedic',
        caller_name: callerName,
        emergency_type: emergencyType,
        triage_priority: triagePriority,
        origin_location: originLocation,
        destination_hospital: 'City General Hospital (H001)',
        green_corridor_active: triagePriority === 'P1_CRITICAL',
        vitals: { hr: 118, bp: '158/94', spo2: 93 },
      });
      if (res.dispatch) {
        setDispatches((prev) => [res.dispatch, ...prev]);
        setShowIntakeModal(false);
        setActionMsg(`Emergency Call ${res.dispatch.id} dispatched to ${res.dispatch.ambulance_id}`);
        setTimeout(() => setActionMsg(null), 4000);
      }
    } catch (err: any) {
      alert(`Dispatch failed: ${err?.response?.data?.detail || err.message}`);
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

      {/* Header & Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <HeartPulse className="w-5 h-5 text-rose-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Emergency Department (ED) CAD & Triage Bays
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time trauma bay availability, Manchester acuity triage (P1-P4), and ambulance coordination
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setShowIntakeModal(true)}
            className="px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5 shadow-lg shadow-rose-900/30"
          >
            <PhoneCall className="w-4 h-4" />
            <span>Intake Emergency 108 Call</span>
          </button>
          <button
            onClick={fetchDispatches}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Trauma Bay Grid Status */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/90 border border-rose-500/40 p-4 rounded-xl shadow-lg space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-rose-400">TRAUMA BAY 1 (Resus)</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
              OCCUPIED
            </span>
          </div>
          <div className="text-slate-200 font-bold">P1 STEMI Cardiac Arrest</div>
          <div className="text-[11px] text-slate-400">Dr. Alex Morgan & Cath Team</div>
        </div>

        <div className="bg-slate-900/90 border border-emerald-500/40 p-4 rounded-xl shadow-lg space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-emerald-400">TRAUMA BAY 2 (Surgical)</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              STANDBY
            </span>
          </div>
          <div className="text-slate-200 font-bold">Trauma Team Ready</div>
          <div className="text-[11px] text-slate-400">Awaiting Inbound AMB-01</div>
        </div>

        <div className="bg-slate-900/90 border border-amber-500/40 p-4 rounded-xl shadow-lg space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-amber-400">TRAUMA BAY 3 (Neuro)</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
              IN TRANSIT
            </span>
          </div>
          <div className="text-slate-200 font-bold">Acute Ischemic Stroke</div>
          <div className="text-[11px] text-slate-400">CT Angiography Reserved</div>
        </div>

        <div className="bg-slate-900/90 border border-emerald-500/40 p-4 rounded-xl shadow-lg space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-emerald-400">TRAUMA BAY 4 (Pediatric)</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              STANDBY
            </span>
          </div>
          <div className="text-slate-200 font-bold">Pediatric Crash Cart Ready</div>
          <div className="text-[11px] text-slate-400">Dr. Rachel Green, MD</div>
        </div>
      </div>

      {/* Emergency CAD Dispatches Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Radio className="w-4 h-4 text-rose-400" />
            <span>Active Emergency Dispatches ({dispatches.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">ED Telemetry CAD Link</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">CAD #</th>
                <th className="px-3.5 py-2.5">Ambulance</th>
                <th className="px-3.5 py-2.5">Emergency Incident</th>
                <th className="px-3.5 py-2.5">Triage Priority</th>
                <th className="px-3.5 py-2.5">Scene Location</th>
                <th className="px-3.5 py-2.5">Green Corridor</th>
                <th className="px-3.5 py-2.5">Telemetry</th>
                <th className="px-3.5 py-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {dispatches.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No active emergency dispatches.
                  </td>
                </tr>
              ) : (
                dispatches.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{d.id}</td>
                    <td className="px-3.5 py-2.5 font-bold text-slate-200">{d.ambulance_id}</td>
                    <td className="px-3.5 py-2.5">
                      <div className="font-semibold text-slate-200">{d.emergency_type}</div>
                      <div className="text-[11px] text-slate-400">Caller: {d.caller_name}</div>
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          d.triage_priority === 'P1_CRITICAL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800 animate-pulse'
                            : d.triage_priority === 'P2_URGENT'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-sky-950 text-sky-300 border border-sky-800'
                        }`}
                      >
                        {d.triage_priority}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-300">{d.origin_location}</td>
                    <td className="px-3.5 py-2.5">
                      {d.green_corridor_active ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                          PRE-EMPTION ENGAGED
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-500">Inactive</span>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-300">
                      {d.vitals ? `HR ${d.vitals.hr || 108} • BP ${d.vitals.bp || '148/92'} • SpO2 ${d.vitals.spo2 || 96}%` : 'Pending Link'}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {d.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Emergency Call Intake Modal */}
      {showIntakeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400 font-bold">
                <PhoneCall className="w-4 h-4" />
                <span>Intake Incoming Emergency Call & CAD Dispatch</span>
              </div>
              <button onClick={() => setShowIntakeModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDispatch} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Caller / Dispatch Channel</label>
                <input
                  type="text"
                  required
                  value={callerName}
                  onChange={(e) => setCallerName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Emergency Incident Classification</label>
                <input
                  type="text"
                  required
                  value={emergencyType}
                  onChange={(e) => setEmergencyType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-rose-500 font-bold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Triage Priority</label>
                  <select
                    value={triagePriority}
                    onChange={(e) => setTriagePriority(e.target.value as TriagePriority)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-rose-500"
                  >
                    <option value="P1_CRITICAL">P1 CRITICAL (Resuscitation)</option>
                    <option value="P2_URGENT">P2 URGENT (Immediate)</option>
                    <option value="P3_DELAYED">P3 DELAYED (Guarded)</option>
                    <option value="P4_EXPECTANT">P4 EXPECTANT (Minor)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Assign Ambulance</label>
                  <select
                    value={ambulanceId}
                    onChange={(e) => setAmbulanceId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-rose-500"
                  >
                    <option value="AMB-01">AMB-01 (Advanced Life Support)</option>
                    <option value="AMB-02">AMB-02 (Cardiac Resus Unit)</option>
                    <option value="AMB-03">AMB-03 (Basic Life Support)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Scene Origin Location</label>
                <input
                  type="text"
                  required
                  value={originLocation}
                  onChange={(e) => setOriginLocation(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowIntakeModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold"
                >
                  Confirm Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
