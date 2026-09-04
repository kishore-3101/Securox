import React, { useState } from 'react';
import {
  Stethoscope,
  HeartPulse,
  Activity,
  UserCheck,
  FileEdit,
  ShieldCheck,
  ShieldAlert,
  AlertCircle,
  Save,
  Pill,
  CheckCircle2,
  Clock,
  Lock,
  Plus,
} from 'lucide-react';

interface ClinicalPatient {
  id: string;
  name: string;
  age: number;
  gender: string;
  department: string;
  room: string;
  primaryCondition: string;
  triage: 'P1_CRITICAL' | 'P2_URGENT' | 'P3_STABLE';
  hr: number;
  bp: string;
  spo2: number;
  troponin: string;
  ecgFinding: string;
  notes: string;
}

export const DoctorClinicalWorkflow: React.FC = () => {
  const [patients, setPatients] = useState<ClinicalPatient[]>([
    {
      id: 'PAT-CAR-01',
      name: 'Ramesh Patel',
      age: 58,
      gender: 'Male',
      department: 'Cardiology',
      room: 'ICU Bed 04',
      primaryCondition: 'Acute Inferior STEMI (Post-PCI)',
      triage: 'P1_CRITICAL',
      hr: 108,
      bp: '148/94',
      spo2: 95,
      troponin: '14.2 ng/mL (HIGH)',
      ecgFinding: 'ST-Elevation in leads II, III, aVF',
      notes: 'Patient stent placed in RCA. Vitals continuously monitored. Heparin drip maintained at 12 units/kg/hr.',
    },
    {
      id: 'PAT-CAR-02',
      name: 'Sunita Sharma',
      age: 44,
      gender: 'Female',
      department: 'Cardiology',
      room: 'Stepdown Bed 12',
      primaryCondition: 'Paroxysmal Supraventricular Tachycardia',
      triage: 'P2_URGENT',
      hr: 86,
      bp: '124/80',
      spo2: 98,
      troponin: '< 0.01 ng/mL (Normal)',
      ecgFinding: 'Normal Sinus Rhythm post adenosine conversion',
      notes: 'Conversion successful. Awaiting 24-hr Holter review tomorrow.',
    },
    {
      id: 'PAT-ONC-99',
      name: 'Devraj Mukherjee (Restricted)',
      age: 62,
      gender: 'Male',
      department: 'Oncology',
      room: 'Ward ONC-08',
      primaryCondition: 'Chemotherapy Regimen Day 3',
      triage: 'P3_STABLE',
      hr: 76,
      bp: '118/76',
      spo2: 99,
      troponin: 'Normal',
      ecgFinding: 'Sinus Rhythm',
      notes: 'DEPARTMENTAL BOLA RESTRICTED: Assigned to Oncology service.',
    },
  ]);

  const [activePatientId, setActivePatientId] = useState<string>('PAT-CAR-01');
  const [doctorDepartment] = useState<string>('Cardiology');
  const [noteText, setNoteText] = useState<string>('');
  const [prescriptions, setPrescriptions] = useState<
    Array<{ id: string; drug: string; dose: string; freq: string; status: string }>
  >([
    { id: 'RX-1', drug: 'Aspirin', dose: '75 mg', freq: 'OD (Oral)', status: 'ACTIVE' },
    { id: 'RX-2', drug: 'Ticagrelor', dose: '90 mg', freq: 'BD (Oral)', status: 'ACTIVE' },
    { id: 'RX-3', drug: 'Atorvastatin', dose: '80 mg', freq: 'HS (Oral)', status: 'ACTIVE' },
  ]);
  const [newDrug, setNewDrug] = useState('');
  const [newDose, setNewDose] = useState('');
  const [interactionWarning, setInteractionWarning] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedPatient = patients.find((p) => p.id === activePatientId) || patients[0];
  const isBolaRestricted = selectedPatient.department !== doctorDepartment;

  const handleSelectPatient = (p: ClinicalPatient) => {
    setActivePatientId(p.id);
    setNoteText(p.notes);
    setInteractionWarning(null);
  };

  const handleSaveNotes = () => {
    if (isBolaRestricted) {
      alert('ACCESS DENIED (BOLA Violation): You are assigned to Cardiology. Patient belongs to Oncology service.');
      return;
    }
    setPatients((prev) =>
      prev.map((p) => (p.id === selectedPatient.id ? { ...p, notes: noteText } : p))
    );
    setFeedback('Clinical diagnosis notes signed and committed to authoritative medical record.');
    setTimeout(() => setFeedback(null), 4000);
  };

  const handleAddPrescription = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDrug) return;
    if (isBolaRestricted) {
      alert('ACCESS DENIED: Cannot prescribe across unauthorized department.');
      return;
    }

    // Drug-drug interaction check logic
    if (newDrug.toLowerCase().includes('ibuprofen') || newDrug.toLowerCase().includes('nsaid')) {
      setInteractionWarning('ALERT: High gastrointestinal bleeding risk with dual antiplatelet therapy (Aspirin + Ticagrelor)!');
      return;
    }

    setPrescriptions((prev) => [
      ...prev,
      {
        id: `RX-${Date.now()}`,
        drug: newDrug,
        dose: newDose || '1 tab',
        freq: 'BD',
        status: 'DISPENSING PENDING',
      },
    ]);
    setNewDrug('');
    setNewDose('');
    setInteractionWarning(null);
    setFeedback(`Prescription for ${newDrug} issued to hospital pharmacy.`);
    setTimeout(() => setFeedback(null), 3500);
  };

  const handleStatOrder = (testName: string) => {
    setFeedback(`STAT ORDER SUBMITTED: ${testName} flagged for immediate lab phlebotomy.`);
    setTimeout(() => setFeedback(null), 4000);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Clinician Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Stethoscope className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wide">
                ATTENDING CLINICIAN WORKSPACE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 font-bold">
                ● SERVICE: {doctorDepartment}
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">
              Inpatient Rounds & Clinical Decision Support
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Departmental BOLA Guard Active • Digital Signature Verification Enabled
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleStatOrder('STAT Troponin-I Serial Repeat')}
            className="px-3.5 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-mono font-bold transition flex items-center gap-2"
          >
            <HeartPulse className="w-4 h-4 text-rose-400" />
            Stat Troponin Order
          </button>
          <button
            onClick={() => handleStatOrder('12-Lead Repeat ECG')}
            className="px-3.5 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold transition flex items-center gap-2"
          >
            <Activity className="w-4 h-4 text-cyan-400" />
            Stat ECG
          </button>
        </div>
      </div>

      {feedback && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Main Clinical Grid: Patient Selector + Patient Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Inpatient Patient List (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Inpatient Queue</span>
            <span>{patients.length} Active</span>
          </div>

          <div className="space-y-2">
            {patients.map((p) => {
              const isSelected = p.id === selectedPatient.id;
              const isRestricted = p.department !== doctorDepartment;

              return (
                <div
                  key={p.id}
                  onClick={() => handleSelectPatient(p)}
                  className={`p-3.5 rounded-xl border font-mono cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-emerald-500 shadow-md ring-1 ring-emerald-500/50'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
                        <span>{p.name}</span>
                        {isRestricted && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-0.5">
                            <Lock className="w-2.5 h-2.5" /> BOLA
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        {p.age}y {p.gender} • {p.room}
                      </div>
                    </div>
                    <span
                      className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                        p.triage === 'P1_CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : p.triage === 'P2_URGENT'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {p.triage.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-300 mt-2 font-sans truncate">
                    {p.primaryCondition}
                  </div>

                  <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-400 pt-2 border-t border-slate-800/60">
                    <span>HR: <strong className="text-rose-400">{p.hr}</strong></span>
                    <span>BP: <strong className="text-amber-400">{p.bp}</strong></span>
                    <span>SpO2: <strong className="text-cyan-400">{p.spo2}%</strong></span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Inpatient Detail & Clinical Actions (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {/* Patient Card Header */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold font-mono text-slate-100">{selectedPatient.name}</h3>
                  <span className="text-xs font-mono text-slate-400">({selectedPatient.id})</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    Dept: {selectedPatient.department}
                  </span>
                </div>
                <p className="text-xs font-mono text-emerald-400 mt-1 font-semibold">
                  Primary Diagnosis: {selectedPatient.primaryCondition}
                </p>
              </div>

              {isBolaRestricted ? (
                <div className="px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-mono flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span>BOLA RESTRICTED (VIEW ONLY)</span>
                </div>
              ) : (
                <div className="px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>ASSIGNED CLINICIAN PERMITTED</span>
                </div>
              )}
            </div>

            {/* Live Telemetry Display */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Heart Rate</div>
                <div className="text-xl font-bold font-mono text-rose-400 mt-0.5">{selectedPatient.hr} bpm</div>
                <div className="text-[9px] font-mono text-slate-500">Continuous ECG</div>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Blood Pressure</div>
                <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">{selectedPatient.bp}</div>
                <div className="text-[9px] font-mono text-slate-500">Arterial Line</div>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Oxygen Saturation</div>
                <div className="text-xl font-bold font-mono text-cyan-400 mt-0.5">{selectedPatient.spo2}%</div>
                <div className="text-[9px] font-mono text-slate-500">Room Air / Cannula</div>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
                <div className="text-[10px] font-mono text-slate-400">Serum Troponin-I</div>
                <div className="text-sm font-bold font-mono text-purple-400 mt-1 truncate">
                  {selectedPatient.troponin}
                </div>
                <div className="text-[9px] font-mono text-slate-500">High-Sensitivity</div>
              </div>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>ECG Telemetry Note: <strong className="text-slate-100">{selectedPatient.ecgFinding}</strong></span>
            </div>
          </div>

          {/* Clinical Diagnosis & Rounding Notes Editor */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <FileEdit className="w-4 h-4 text-emerald-400" />
                Attending Clinical Assessment & Management Plan
              </h4>
              <span className="text-[10px] font-mono text-slate-400">Auto-timestamps with Doctor Signature</span>
            </div>

            <textarea
              rows={4}
              value={noteText || selectedPatient.notes}
              disabled={isBolaRestricted}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder={isBolaRestricted ? 'Restricted: You cannot write notes for patients outside your department.' : 'Enter clinical observations, progress notes, and titration plan...'}
              className={`w-full p-3 rounded-xl border font-mono text-xs focus:outline-none transition ${
                isBolaRestricted
                  ? 'bg-slate-950/50 border-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-slate-950 border-slate-700 text-slate-200 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
              }`}
            />

            <div className="flex items-center justify-between pt-1">
              <div className="text-[10px] font-mono text-slate-400">
                Signer: Dr. Sarah Chen, MD (Cardiology) • License #KA-MED-4412
              </div>

              <button
                onClick={handleSaveNotes}
                disabled={isBolaRestricted}
                className={`px-4 py-2 rounded-xl font-mono text-xs font-bold flex items-center gap-2 transition shadow-lg ${
                  isBolaRestricted
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20'
                }`}
              >
                <Save className="w-4 h-4" />
                Sign & Commit Clinical Note
              </button>
            </div>
          </div>

          {/* Prescription Ordering Pad with Interaction Guard */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Pill className="w-4 h-4 text-cyan-400" />
                Active Prescriptions & Pharmacotherapy
              </h4>
              <span className="text-[10px] font-mono text-slate-400">Real-Time DDI Check</span>
            </div>

            {interactionWarning && (
              <div className="p-3 bg-rose-950/60 border border-rose-500/50 rounded-xl text-xs font-mono text-rose-300 flex items-center gap-2 animate-fadeIn">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{interactionWarning}</span>
              </div>
            )}

            {/* List of active meds */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {prescriptions.map((rx) => (
                <div
                  key={rx.id}
                  className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-mono font-bold text-slate-100">{rx.drug}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      {rx.status}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 mt-2">
                    {rx.dose} • {rx.freq}
                  </div>
                </div>
              ))}
            </div>

            {/* Add medication form */}
            <form onSubmit={handleAddPrescription} className="flex flex-col sm:flex-row gap-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Drug name (e.g. Clopidogrel, Metoprolol)..."
                value={newDrug}
                disabled={isBolaRestricted}
                onChange={(e) => setNewDrug(e.target.value)}
                className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <input
                type="text"
                placeholder="Dosage (e.g. 75mg OD)..."
                value={newDose}
                disabled={isBolaRestricted}
                onChange={(e) => setNewDose(e.target.value)}
                className="w-full sm:w-40 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <button
                type="submit"
                disabled={isBolaRestricted}
                className={`px-4 py-2 rounded-xl font-mono text-xs font-bold flex items-center justify-center gap-1.5 transition ${
                  isBolaRestricted
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-500/20'
                }`}
              >
                <Plus className="w-4 h-4" />
                Prescribe
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
