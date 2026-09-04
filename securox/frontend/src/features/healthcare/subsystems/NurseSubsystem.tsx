import React, { useState } from 'react';
import {
  HeartPulse,
  Activity,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  Save,
  CheckSquare,
  Square,
  Droplet,
  Pill,
} from 'lucide-react';
import { Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface NurseSubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const NurseSubsystem: React.FC<NurseSubsystemProps> = ({ patients, userRole }) => {
  // Nurse shift isolation: only patients where assigned_nurse_id is nurse or cardiology assigned
  const nurseAssignedPatients = patients.filter(
    (p) => p.assigned_nurse_id === 'nurse' || p.department === 'Cardiology'
  );

  const [selectedPatientId, setSelectedPatientId] = useState<string>(
    nurseAssignedPatients[0]?.id || 'P-1001'
  );

  const activePatient =
    nurseAssignedPatients.find((p) => p.id === selectedPatientId) || nurseAssignedPatients[0];

  // Bedside Vitals input state
  const [hr, setHr] = useState<number>(activePatient?.vitals?.heart_rate_bpm || activePatient?.vitals?.hr || 104);
  const [bpSys, setBpSys] = useState<number>(activePatient?.vitals?.blood_pressure_sys || 142);
  const [bpDia, setBpDia] = useState<number>(activePatient?.vitals?.blood_pressure_dia || 88);
  const [spo2, setSpo2] = useState<number>(activePatient?.vitals?.oxygen_saturation_pct || activePatient?.vitals?.spo2 || 97);
  const [temp, setTemp] = useState<number>(activePatient?.vitals?.temperature_c || activePatient?.vitals?.temp || 37.1);
  const [respRate, setRespRate] = useState<number>(activePatient?.vitals?.respiration_rate || 18);
  const [savingVitals, setSavingVitals] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // eMAR & IV Drip Checklist
  const [ivTasks, setIvTasks] = useState([
    { id: 'IV-1', task: 'Titrate IV Heparin Drip to 12 units/kg/hr', done: true, time: '08:00 AM' },
    { id: 'IV-2', task: 'Administer IV Pantoprazole 40mg', done: true, time: '09:00 AM' },
    { id: 'IV-3', task: 'Check continuous 12-lead telemetry leads & battery', done: false, time: '11:00 AM' },
    { id: 'IV-4', task: 'Draw 4-hour High-Sensitivity Troponin STAT panel', done: false, time: '12:30 PM' },
    { id: 'IV-5', task: 'Check peripheral IV cannula insertion site & flush saline', done: false, time: '02:00 PM' },
  ]);

  const handleSelectPatient = (pId: string) => {
    setSelectedPatientId(pId);
    const pat = nurseAssignedPatients.find((p) => p.id === pId);
    if (pat) {
      setHr(pat.vitals?.heart_rate_bpm || pat.vitals?.hr || 98);
      setBpSys(pat.vitals?.blood_pressure_sys || 135);
      setBpDia(pat.vitals?.blood_pressure_dia || 85);
      setSpo2(pat.vitals?.oxygen_saturation_pct || pat.vitals?.spo2 || 98);
      setTemp(pat.vitals?.temperature_c || pat.vitals?.temp || 37.0);
      setRespRate(pat.vitals?.respiration_rate || 16);
    }
  };

  const handleSaveVitals = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePatient) return;
    setSavingVitals(true);
    try {
      await healthcareService.updatePatient(activePatient.id, {
        vitals: {
          heart_rate_bpm: Number(hr),
          blood_pressure_sys: Number(bpSys),
          blood_pressure_dia: Number(bpDia),
          bp: `${bpSys}/${bpDia}`,
          hr: Number(hr),
          oxygen_saturation_pct: Number(spo2),
          spo2: Number(spo2),
          temperature_c: Number(temp),
          temp: Number(temp),
          respiration_rate: Number(respRate),
        },
      });
      setStatusMsg(`Bedside vitals recorded for ${activePatient.name} (${activePatient.id})`);
      setTimeout(() => setStatusMsg(null), 3500);
    } catch (err: any) {
      alert(`Error updating vitals: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSavingVitals(false);
    }
  };

  const toggleIvTask = (id: string) => {
    setIvTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, done: !t.done } : t))
    );
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Shift Isolation Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-slate-200 font-bold">Inpatient Nurse Shift Station (Staff Nurse Priya Nair, RN)</div>
            <div className="text-slate-400 text-[11px]">Active Shift: Day Shift (07:00 - 19:00) • Unit: Cardiology CICU</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px]">
            Shift Assigned Patients: <b className="text-teal-400">{nurseAssignedPatients.length}</b>
          </span>
          <span className="px-2.5 py-1 rounded bg-teal-500/10 border border-teal-500/30 text-teal-300 text-[11px]">
            Cross-Patient Isolation: <b className="text-teal-400">ACTIVE</b>
          </span>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{statusMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Assigned Patient Roster */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="font-bold text-slate-200 uppercase tracking-wider">Assigned Shift Roster</span>
            <span className="text-[10px] text-teal-400">Nurse Primary</span>
          </div>

          <div className="space-y-2">
            {nurseAssignedPatients.map((p) => {
              const isSelected = p.id === activePatient?.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPatient(p.id)}
                  className={`w-full p-3 rounded-lg border text-left transition ${
                    isSelected
                      ? 'bg-teal-600/20 border-teal-500 text-white shadow-md shadow-teal-950'
                      : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-teal-400">{p.id}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {p.room_bed || 'Bed 01'}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-100 mt-1 truncate">{p.name}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{p.condition || 'GUARDED'}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Bedside Vitals Recorder & eMAR */}
        <div className="lg:col-span-3 space-y-6">
          {/* Active Patient Vitals Recorder Form */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-100">
                    Bedside Physiological Vitals Uplink: {activePatient?.name}
                  </h3>
                  <span className="text-[10px] font-bold text-teal-400 px-2 py-0.5 rounded bg-teal-950 border border-teal-800">
                    {activePatient?.id}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Allocated Bed: {activePatient?.room_bed || 'ICU-Bed-04'} • Attending: Dr. {activePatient?.assigned_doctor_id || 'doctor'}
                </div>
              </div>
            </div>

            <form onSubmit={handleSaveVitals} className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Heart Rate (BPM)</label>
                  <input
                    type="number"
                    value={hr}
                    onChange={(e) => setHr(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-400 font-bold outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">BP Sys (mmHg)</label>
                  <input
                    type="number"
                    value={bpSys}
                    onChange={(e) => setBpSys(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-400 font-bold outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">BP Dia (mmHg)</label>
                  <input
                    type="number"
                    value={bpDia}
                    onChange={(e) => setBpDia(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-400 font-bold outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">SpO2 (%)</label>
                  <input
                    type="number"
                    value={spo2}
                    onChange={(e) => setSpo2(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sky-400 font-bold outline-none focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Temp (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={temp}
                    onChange={(e) => setTemp(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-bold outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={savingVitals}
                  className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold transition flex items-center gap-2 disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{savingVitals ? 'Recording...' : 'Commit Bedside Vitals to Chart'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* eMAR & Medication Administration Record */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Droplet className="w-4 h-4 text-sky-400" />
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Electronic Medication Administration (eMAR) & IV Titration Checklist
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">Shift Checklist</span>
            </div>

            <div className="space-y-2">
              {ivTasks.map((t) => (
                <div
                  key={t.id}
                  onClick={() => toggleIvTask(t.id)}
                  className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition ${
                    t.done
                      ? 'bg-slate-950/40 border-slate-800/60 text-slate-400 line-through'
                      : 'bg-slate-950 border-teal-500/30 text-slate-200 hover:border-teal-500'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {t.done ? (
                      <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-500 shrink-0" />
                    )}
                    <span className="text-xs">{t.task}</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {t.time}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
