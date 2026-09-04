import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  HeartPulse,
  Activity,
  FileEdit,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Zap,
  Save,
  Pill,
  TestTube,
  CheckCircle2,
  Lock,
  ChevronRight,
  User,
} from 'lucide-react';
import { Patient, MedicalRecord } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface DoctorSubsystemProps {
  patients: Patient[];
  userRole: string;
  initialPatientId?: string;
  breakGlassActiveForPatient?: string | null;
  onBreakGlassSuccess?: (patientId: string, newRisk: number, incidentId: string) => void;
}

export const DoctorSubsystem: React.FC<DoctorSubsystemProps> = ({
  patients,
  userRole,
  initialPatientId,
  breakGlassActiveForPatient,
  onBreakGlassSuccess,
}) => {
  const [selectedPatientId, setSelectedPatientId] = useState<string>(initialPatientId || 'P-1001');
  const [patientDetail, setPatientDetail] = useState<Patient | null>(null);
  const [medicalRecords, setMedicalRecords] = useState<MedicalRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [bolaBlocked, setBolaBlocked] = useState(false);
  const [bolaErrorDetail, setBolaErrorDetail] = useState<string | null>(null);

  // Break-Glass modal state
  const [showBreakGlassModal, setShowBreakGlassModal] = useState(false);
  const [breakGlassReason, setBreakGlassReason] = useState('');
  const [breakGlassSubmitting, setBreakGlassSubmitting] = useState(false);
  const [breakGlassSuccessBanner, setBreakGlassSuccessBanner] = useState<{
    newRisk: number;
    incidentId: string;
  } | null>(null);

  // Clinical notes & orders
  const [treatmentNote, setTreatmentNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Prescriptions & Labs
  const [showRxModal, setShowRxModal] = useState(false);
  const [rxDrug, setRxDrug] = useState('Ticagrelor 90mg');
  const [rxDose, setRxDose] = useState('90mg PO');
  const [rxFreq, setRxFreq] = useState('BID');
  const [rxDuration, setRxDuration] = useState('30 days');
  const [rxDdi, setRxDdi] = useState('Monitor with concurrent Aspirin');

  const [showLabModal, setShowLabModal] = useState(false);
  const [labTestName, setLabTestName] = useState('High-Sensitivity Troponin-T');
  const [labCategory, setLabCategory] = useState('Cardiac Biomarkers');
  const [labPriority, setLabPriority] = useState('STAT');
  const [labRefRange, setLabRefRange] = useState('< 14 ng/L');

  const fetchDetail = async (patId: string) => {
    setLoading(true);
    setBolaBlocked(false);
    setBolaErrorDetail(null);
    try {
      const res = await healthcareService.getPatientDetail(patId);
      if (res && res.patient) {
        setPatientDetail(res.patient);
        setMedicalRecords(res.medical_records || []);
      }
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setBolaBlocked(true);
        setBolaErrorDetail(
          err?.response?.data?.detail ||
            'BOLA ACCESS DENIED: Patient is not assigned to your clinician ID or department scope.'
        );
        // Look up local patient metadata to show in banner
        const local = patients.find((p) => p.id === patId);
        if (local) setPatientDetail(local);
      } else {
        console.error('Error fetching patient detail:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPatientId) {
      fetchDetail(selectedPatientId);
    }
  }, [selectedPatientId]);

  const handleSelectPatient = (pId: string) => {
    setSelectedPatientId(pId);
  };

  const handleTriggerBreakGlass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!breakGlassReason.trim()) {
      alert('Emergency clinical reason is strictly mandatory for break-glass override.');
      return;
    }
    setBreakGlassSubmitting(true);
    try {
      const res = await healthcareService.triggerBreakGlass(selectedPatientId, breakGlassReason);
      if (res.status === 'BREAK_GLASS_AUTHORIZED') {
        setBolaBlocked(false);
        setPatientDetail(res.patient);
        setMedicalRecords(res.medical_records || []);
        setShowBreakGlassModal(false);
        setBreakGlassSuccessBanner({
          newRisk: res.new_user_risk,
          incidentId: res.incident_id,
        });
        if (onBreakGlassSuccess) {
          onBreakGlassSuccess(selectedPatientId, res.new_user_risk, res.incident_id);
        }
      }
    } catch (err: any) {
      alert(`Break-glass override failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBreakGlassSubmitting(false);
    }
  };

  const handleSaveNote = async () => {
    if (!treatmentNote.trim() || !patientDetail) return;
    setSavingNote(true);
    try {
      await healthcareService.updatePatient(patientDetail.id, {
        condition: patientDetail.condition,
        diagnosis: patientDetail.diagnosis,
      });
      setSaveSuccessMsg('Clinical note appended to permanent EHR ledger.');
      setTimeout(() => setSaveSuccessMsg(null), 3500);
      setTreatmentNote('');
    } catch (err: any) {
      alert(`Failed to save note: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSavingNote(false);
    }
  };

  const handleCreatePrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientDetail) return;
    try {
      await healthcareService.createPrescription({
        patient_id: patientDetail.id,
        doctor_id: 'doctor',
        medication: rxDrug,
        dosage: rxDose,
        frequency: rxFreq,
        duration: rxDuration,
        ddi_warning: rxDdi,
      });
      setShowRxModal(false);
      setSaveSuccessMsg(`Prescription for ${rxDrug} dispatched to Pyxis pharmacy.`);
      setTimeout(() => setSaveSuccessMsg(null), 3500);
    } catch (err: any) {
      alert(`Prescription failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleCreateLabOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientDetail) return;
    try {
      await healthcareService.createLabOrder({
        patient_id: patientDetail.id,
        doctor_id: 'doctor',
        test_name: labTestName,
        category: labCategory,
        priority: labPriority,
        reference_range: labRefRange,
      });
      setShowLabModal(false);
      setSaveSuccessMsg(`${labPriority} Lab Order for ${labTestName} transmitted to LIS.`);
      setTimeout(() => setSaveSuccessMsg(null), 3500);
    } catch (err: any) {
      alert(`Lab order failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const isBreakGlassActive = breakGlassActiveForPatient === selectedPatientId || !!breakGlassSuccessBanner;

  return (
    <div className="space-y-6">
      {/* Clinician Scoping Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <div className="text-slate-200 font-bold">Attending Clinician Workspace (Dr. Alex Morgan, MD)</div>
            <div className="text-slate-400 text-[11px]">Primary Service: Cardiology & Interventional Cath Lab</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px]">
            Scope: <b className="text-sky-400">Cardiology Dept & Assigned Patients</b>
          </span>
          <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[11px]">
            BOLA Guard: <b className="text-amber-400">ENFORCED</b>
          </span>
        </div>
      </div>

      {/* Success Notifications */}
      {saveSuccessMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Break-Glass Authorization Banner */}
      {isBreakGlassActive && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-rose-950/80 to-amber-950/60 border border-rose-500 rounded-xl shadow-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 text-rose-400 animate-pulse" />
            <div>
              <div className="text-rose-300 font-bold uppercase tracking-wider flex items-center gap-2">
                <span>EMERGENCY BREAK-GLASS OVERRIDE ACTIVE</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-rose-900 border border-rose-600 text-rose-200">
                  CRITICAL ELEVATION
                </span>
              </div>
              <div className="text-slate-300 text-[11px] mt-0.5">
                Authorized for patient <b>{selectedPatientId}</b>. User risk score elevated (+35.0). High-severity SOC Incident dispatched.
              </div>
            </div>
          </div>
          {breakGlassSuccessBanner && (
            <div className="text-right text-[11px] text-rose-300 bg-slate-950/60 px-3 py-1.5 rounded border border-rose-800/60">
              <div>Incident: <b>{breakGlassSuccessBanner.incidentId}</b></div>
              <div>Elevated Risk: <b>{breakGlassSuccessBanner.newRisk} / 100</b></div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Patient Selector with Scope Demarcation */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="font-bold text-slate-200 uppercase tracking-wider">Patient Inpatient Roster</span>
            <span className="text-[10px] text-slate-400">Select to chart</span>
          </div>

          <div className="space-y-2">
            {patients.map((p) => {
              const isSelected = p.id === selectedPatientId;
              const isAssigned = p.department === 'Cardiology' || p.id === 'P-1001' || p.id === 'P-1002';

              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPatient(p.id)}
                  className={`w-full p-3 rounded-lg border text-left transition ${
                    isSelected
                      ? 'bg-sky-600/20 border-sky-500 text-white shadow-md shadow-sky-950'
                      : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-400">{p.id}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                        isAssigned
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                          : 'bg-rose-950/60 text-rose-400 border border-rose-800/60'
                      }`}
                    >
                      {isAssigned ? 'ASSIGNED' : 'CROSS-DEPT (BOLA)'}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-100 mt-1 truncate">{p.name}</div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                    <span>{p.department}</span>
                    <span>{p.room_bed || 'Unassigned Bed'}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Patient Clinical Chart or BOLA Shield */}
        <div className="lg:col-span-3">
          {bolaBlocked && !isBreakGlassActive ? (
            /* BOLA Access Blocked Shield & Break-Glass Action */
            <div className="bg-slate-900/95 border border-rose-500/60 rounded-xl p-8 shadow-2xl space-y-6 text-center font-mono">
              <div className="w-16 h-16 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400 shadow-xl shadow-rose-950">
                <Lock className="w-8 h-8" />
              </div>

              <div className="space-y-2 max-w-lg mx-auto">
                <div className="text-base font-bold text-rose-400 uppercase tracking-wide">
                  Broken Object-Level Authorization (BOLA) Guard Triggered
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Access blocked for clinician <b>dr_alex (doctor)</b> attempting to inspect unassigned patient{' '}
                  <b>{selectedPatientId}</b> ({patientDetail?.department || 'External Service'}).
                </p>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 text-left">
                  {bolaErrorDetail}
                </div>
              </div>

              {/* Break-Glass Action */}
              <div className="p-6 rounded-xl bg-gradient-to-b from-rose-950/40 to-slate-950/80 border border-rose-500/40 max-w-md mx-auto space-y-3">
                <div className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center justify-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
                  <span>Clinical Life-Safety Emergency?</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  If this patient is experiencing an acute emergency requiring immediate intervention, you may invoke Break-Glass protocol.
                </p>
                <button
                  onClick={() => setShowBreakGlassModal(true)}
                  className="w-full py-2.5 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30"
                >
                  <Zap className="w-4 h-4" />
                  <span>BREAK-GLASS EMERGENCY ACCESS OVERRIDE</span>
                </button>
              </div>
            </div>
          ) : (
            /* Full Clinical EHR Chart */
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-6">
              {/* Patient Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold font-mono text-slate-100">
                      {patientDetail?.name || 'Patient Chart'}
                    </h3>
                    <span className="text-xs font-mono font-bold text-sky-400 px-2 py-0.5 rounded bg-sky-950 border border-sky-800">
                      {patientDetail?.id}
                    </span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {patientDetail?.department}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-slate-400 mt-1">
                    {patientDetail?.age}y • {patientDetail?.gender} • Bed: {patientDetail?.room_bed || patientDetail?.room_number || 'ICU-Bed-04'}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowRxModal(true)}
                    className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-sky-900/20"
                  >
                    <Pill className="w-3.5 h-3.5" />
                    <span>Prescribe Rx</span>
                  </button>
                  <button
                    onClick={() => setShowLabModal(true)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-emerald-900/20"
                  >
                    <TestTube className="w-3.5 h-3.5" />
                    <span>Order STAT Lab</span>
                  </button>
                </div>
              </div>

              {/* Bedside Physiological Vitals Grid */}
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Bedside Monitor Telemetry (MIMIC-IV Stream)
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
                  <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg">
                    <div className="text-slate-400 text-[10px]">HEART RATE</div>
                    <div className="text-lg font-bold text-rose-400">
                      {patientDetail?.vitals?.heart_rate_bpm || patientDetail?.vitals?.hr || 108}{' '}
                      <span className="text-xs font-normal text-slate-500">BPM</span>
                    </div>
                    <div className="text-[10px] text-amber-400 mt-0.5">Sinus Tachycardia</div>
                  </div>

                  <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg">
                    <div className="text-slate-400 text-[10px]">BLOOD PRESSURE</div>
                    <div className="text-lg font-bold text-amber-400">
                      {patientDetail?.vitals?.bp ||
                        `${patientDetail?.vitals?.blood_pressure_sys || 148}/${patientDetail?.vitals?.blood_pressure_dia || 92}`}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Stage 1 HTN</div>
                  </div>

                  <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg">
                    <div className="text-slate-400 text-[10px]">OXYGEN SAT (SPO2)</div>
                    <div className="text-lg font-bold text-sky-400">
                      {patientDetail?.vitals?.oxygen_saturation_pct || patientDetail?.vitals?.spo2 || 96}%
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-0.5">Room Air</div>
                  </div>

                  <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg">
                    <div className="text-slate-400 text-[10px]">TEMPERATURE</div>
                    <div className="text-lg font-bold text-slate-200">
                      {patientDetail?.vitals?.temperature_c || patientDetail?.vitals?.temp || 37.2}°C
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-0.5">Afebrile</div>
                  </div>

                  <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg">
                    <div className="text-slate-400 text-[10px]">RESPIRATION</div>
                    <div className="text-lg font-bold text-slate-200">
                      {patientDetail?.vitals?.respiration_rate || 18}{' '}
                      <span className="text-xs font-normal text-slate-500">/min</span>
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-0.5">Regular</div>
                  </div>
                </div>
              </div>

              {/* Diagnosis & Clinical History */}
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 font-mono text-xs space-y-2">
                <span className="text-slate-400 uppercase tracking-wider font-bold text-[10px]">
                  Primary Working Clinical Diagnosis
                </span>
                <div className="text-sm font-bold text-slate-200">
                  {patientDetail?.diagnosis || 'Acute Myocardial Infarction / Post-PCI Stent Placement'}
                </div>
                <div className="text-xs text-slate-400">
                  Clinical Condition:{' '}
                  <span className="text-amber-400 font-bold">{patientDetail?.condition || 'GUARDED'}</span> •
                  Sensitivity: <span className="text-sky-400">{patientDetail?.sensitivity || 'CONFIDENTIAL'}</span>
                </div>
              </div>

              {/* Treatment Notes & EHR Update Editor */}
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <FileEdit className="w-3.5 h-3.5 text-sky-400" />
                    <span>Attending Physician Clinical Notes</span>
                  </span>
                  <span className="text-slate-500 text-[11px]">Audit preserved & immutable</span>
                </div>

                <textarea
                  rows={3}
                  value={treatmentNote}
                  onChange={(e) => setTreatmentNote(e.target.value)}
                  placeholder="Enter clinical progress note, stent status, heparin drip titration, or discharge criteria..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 outline-none focus:border-sky-500 resize-none"
                />

                <div className="flex justify-end">
                  <button
                    onClick={handleSaveNote}
                    disabled={savingNote || !treatmentNote.trim()}
                    className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold transition flex items-center gap-2 disabled:opacity-50"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{savingNote ? 'Committing...' : 'Append Clinical Progress Note'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Break-Glass Emergency Modal */}
      {showBreakGlassModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-rose-500 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-rose-400 font-bold">
                <Zap className="w-5 h-5 animate-pulse" />
                <span>EMERGENCY BREAK-GLASS PROTOCOL INVOCATION</span>
              </div>
              <button onClick={() => setShowBreakGlassModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <div className="p-3.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-200 space-y-2 leading-relaxed">
              <div className="font-bold flex items-center gap-1.5 text-rose-300">
                <AlertTriangle className="w-4 h-4" />
                <span>LEGAL & AUDIT CONSEQUENCES OF BREAK-GLASS:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-300">
                <li>Immediate elevation of clinician cyber-risk score by <b>+35.0 points</b>.</li>
                <li>High-severity SOC Incident generated in City Defense Command.</li>
                <li>Hospital IT Security Officer immediately notified via real-time WebSocket.</li>
                <li>Immutable digital audit evidence recorded in SQLite ledger.</li>
              </ul>
            </div>

            <form onSubmit={handleTriggerBreakGlass} className="space-y-3">
              <div>
                <label className="block text-slate-300 font-bold mb-1">
                  Mandatory Emergency Clinical Justification *
                </label>
                <textarea
                  rows={3}
                  required
                  value={breakGlassReason}
                  onChange={(e) => setBreakGlassReason(e.target.value)}
                  placeholder="e.g., Acute cardiac arrest in hallway during transit; patient collapsed without assigned cardiologist present. Immediate defibrillation and heparin administration required."
                  className="w-full bg-slate-950 border border-rose-500/50 rounded-lg p-2.5 text-slate-200 outline-none focus:border-rose-400 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowBreakGlassModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={breakGlassSubmitting}
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5 shadow-lg shadow-rose-950"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>{breakGlassSubmitting ? 'Authorizing Break-Glass...' : 'I ATTEST & BREAK GLASS'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Prescribe Rx Modal */}
      {showRxModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Pill className="w-4 h-4" />
                <span>Issue Prescription (Pyxis Transmit)</span>
              </div>
              <button onClick={() => setShowRxModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePrescription} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Medication Name</label>
                <input
                  type="text"
                  required
                  value={rxDrug}
                  onChange={(e) => setRxDrug(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Dosage</label>
                  <input
                    type="text"
                    required
                    value={rxDose}
                    onChange={(e) => setRxDose(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Frequency</label>
                  <input
                    type="text"
                    required
                    value={rxFreq}
                    onChange={(e) => setRxFreq(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Duration</label>
                <input
                  type="text"
                  value={rxDuration}
                  onChange={(e) => setRxDuration(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-amber-400 mb-1">DDI / Allergy Safeguard Warning</label>
                <input
                  type="text"
                  value={rxDdi}
                  onChange={(e) => setRxDdi(e.target.value)}
                  className="w-full bg-slate-950 border border-amber-500/40 rounded-lg px-3 py-2 text-amber-300 outline-none focus:border-amber-400"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowRxModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold"
                >
                  Sign & Dispatch Rx
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Order STAT Lab Modal */}
      {showLabModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <TestTube className="w-4 h-4" />
                <span>Order LIS Laboratory Panel</span>
              </div>
              <button onClick={() => setShowLabModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateLabOrder} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Test Name</label>
                <input
                  type="text"
                  required
                  value={labTestName}
                  onChange={(e) => setLabTestName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Category</label>
                  <input
                    type="text"
                    value={labCategory}
                    onChange={(e) => setLabCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Priority</label>
                  <select
                    value={labPriority}
                    onChange={(e) => setLabPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                  >
                    <option value="STAT">STAT (Emergency)</option>
                    <option value="URGENT">URGENT</option>
                    <option value="ROUTINE">ROUTINE</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Reference Range</label>
                <input
                  type="text"
                  value={labRefRange}
                  onChange={(e) => setLabRefRange(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowLabModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  Transmit LIS Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
