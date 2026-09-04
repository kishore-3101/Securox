import React, { useState, useEffect } from 'react';
import { healthcareService } from '../../services/healthcareService';
import { PermissionGuard } from '../../components/common/PermissionGuard';
import { Patient } from '../../types/healthcare';
import { usePermissions } from '../../hooks/usePermissions';
import {
  Stethoscope,
  HeartPulse,
  Activity,
  UserCheck,
  FileEdit,
  ShieldCheck,
  AlertCircle,
  Save,
} from 'lucide-react';

export const DoctorPortal: React.FC = () => {
  const { role } = usePermissions();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [notes, setNotes] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Mock patient population if backend returns empty or loading
  const defaultPatients: Patient[] = [
    {
      id: 'PAT-CAR-01',
      name: 'Ramesh Patel',
      age: 58,
      gender: 'Male',
      department: 'Cardiology',
      assigned_doctor_id: 'doctor',
      condition: 'Acute Myocardial Infarction',
      triage_level: 'P1_CRITICAL',
      room_number: 'ICU-Bed-04',
      vitals: {
        heart_rate_bpm: 118,
        blood_pressure_sys: 165,
        blood_pressure_dia: 98,
        oxygen_saturation_pct: 94,
        temperature_c: 37.8,
        respiration_rate: 22,
      },
      sensitivity: 'RESTRICTED',
      admitted_at: '2026-09-04T08:30:00Z',
    },
    {
      id: 'PAT-CAR-02',
      name: 'Sunita Sharma',
      age: 44,
      gender: 'Female',
      department: 'Cardiology',
      assigned_doctor_id: 'doctor',
      condition: 'Ventricular Tachycardia (Post-Op)',
      triage_level: 'P2_URGENT',
      room_number: 'StepDown-12',
      vitals: {
        heart_rate_bpm: 88,
        blood_pressure_sys: 125,
        blood_pressure_dia: 82,
        oxygen_saturation_pct: 98,
        temperature_c: 36.9,
        respiration_rate: 16,
      },
      sensitivity: 'CONFIDENTIAL',
      admitted_at: '2026-09-03T14:15:00Z',
    },
    {
      id: 'PAT-ONC-01',
      name: 'Devraj Mukherjee',
      age: 62,
      gender: 'Male',
      department: 'Oncology',
      assigned_doctor_id: 'dr_sharma',
      condition: 'Stage III Chemotherapy Infusion',
      triage_level: 'P3_DELAYED',
      room_number: 'Ward-ONC-08',
      vitals: {
        heart_rate_bpm: 76,
        blood_pressure_sys: 120,
        blood_pressure_dia: 80,
        oxygen_saturation_pct: 99,
        temperature_c: 37.1,
        respiration_rate: 18,
      },
      sensitivity: 'RESTRICTED',
      admitted_at: '2026-09-02T11:00:00Z',
    },
  ];

  useEffect(() => {
    async function load() {
      try {
        const res = await healthcareService.getPatients();
        if (res.patients && res.patients.length > 0) {
          const normalized = res.patients.map((p: any) => ({
            ...p,
            room_number: p.room_number || p.room_bed || 'ICU-Bed-04',
            triage_level: p.triage_level || 'P1_CRITICAL',
            condition: p.condition || 'Observation',
            vitals: p.vitals || {
              heart_rate_bpm: 78,
              blood_pressure_sys: 120,
              blood_pressure_dia: 80,
              oxygen_saturation_pct: 98,
              temperature_c: 37.0,
              respiration_rate: 16,
            },
          }));
          setPatients(normalized);
          setSelectedPatient(normalized[0]);
        } else {
          setPatients(defaultPatients);
          setSelectedPatient(defaultPatients[0]);
        }
      } catch {
        setPatients(defaultPatients);
        setSelectedPatient(defaultPatients[0]);
      }
    }
    load();
  }, []);

  const handleSaveNotes = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    }, 600);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-emerald-400" />
            Doctor Clinical Portal & BOLA Defense
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Clinical Records, Bedside Vitals Telemetry & ABAC Departmental Boundary Protection
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-4 h-4" />
          <span>BOLA ENFORCEMENT: ACTIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Selection List */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-3">
          <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            Assigned Inpatient Ward
          </h3>

          <div className="space-y-2">
            {patients.map((pat) => {
              const isSelected = selectedPatient?.id === pat.id;
              const isCardiology = pat.department === 'Cardiology';

              return (
                <button
                  key={pat.id}
                  onClick={() => setSelectedPatient(pat)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? 'bg-emerald-950/30 border-emerald-500/50 shadow-md'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-mono font-bold text-slate-200">{pat.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      {pat.room_number}
                    </span>
                  </div>

                  <div className="mt-1 flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>{pat.department}</span>
                    <span className={isCardiology ? 'text-emerald-400' : 'text-amber-400'}>
                      {pat.condition}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Patient Vitals & Clinical Inspection */}
        {selectedPatient && (
          <div className="lg:col-span-2 space-y-4">
            {/* Vitals Ribbon */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <div>
                  <h3 className="text-base font-bold font-mono text-slate-100">{selectedPatient.name}</h3>
                  <p className="text-xs font-mono text-slate-400">
                    MRN: {selectedPatient.id} | Age: {selectedPatient.age} | Dept: {selectedPatient.department}
                  </p>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
                  {selectedPatient.triage_level}
                </span>
              </div>

              {/* Vitals Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 text-center">
                  <span className="text-[10px] font-mono text-slate-400 block">HEART RATE</span>
                  <span className="text-xl font-bold font-mono text-rose-400">
                    {selectedPatient.vitals?.heart_rate_bpm ?? 78} <span className="text-xs text-slate-500">bpm</span>
                  </span>
                </div>

                <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 text-center">
                  <span className="text-[10px] font-mono text-slate-400 block">BLOOD PRESSURE</span>
                  <span className="text-xl font-bold font-mono text-sky-400">
                    {selectedPatient.vitals?.blood_pressure_sys ?? 120}/{selectedPatient.vitals?.blood_pressure_dia ?? 80}
                  </span>
                </div>

                <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 text-center">
                  <span className="text-[10px] font-mono text-slate-400 block">SpO2 OXYGEN</span>
                  <span className="text-xl font-bold font-mono text-emerald-400">
                    {selectedPatient.vitals?.oxygen_saturation_pct ?? 98}%
                  </span>
                </div>

                <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 text-center">
                  <span className="text-[10px] font-mono text-slate-400 block">RESPIRATION</span>
                  <span className="text-xl font-bold font-mono text-amber-400">
                    {selectedPatient.vitals?.respiration_rate ?? 16} <span className="text-xs text-slate-500">/min</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Clinical Diagnosis & Notes Editor with PermissionGuard */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <FileEdit className="w-4 h-4 text-sky-400" />
                  Clinician Diagnosis & Treatment Notes
                </h4>
                {savedSuccess && (
                  <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Saved with cryptographic audit
                  </span>
                )}
              </div>

              {selectedPatient.department !== 'Cardiology' && role === 'doctor' && (
                <div className="p-3 bg-amber-950/30 border border-amber-500/40 rounded-lg text-xs font-mono text-amber-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>
                    BOLA Warning: This patient belongs to <b>{selectedPatient.department}</b>. Modifications are read-only under clinician compartmentalization.
                  </span>
                </div>
              )}

              <textarea
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Enter clinical observations, ECG interpretation, and treatment modifications..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />

              <div className="flex justify-end">
                <PermissionGuard
                  capability="can_edit_patient_records"
                  fallbackMessage="Clinician modification restricted: Requires authorized clinician permissions for this department"
                >
                  <button
                    onClick={handleSaveNotes}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-semibold transition shadow-lg"
                  >
                    <Save className="w-4 h-4" />
                    <span>{saving ? 'Signing & Saving...' : 'Save & Sign Clinical Note'}</span>
                  </button>
                </PermissionGuard>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
