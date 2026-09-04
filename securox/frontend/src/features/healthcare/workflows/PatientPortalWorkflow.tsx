import React, { useState } from 'react';
import {
  Heart,
  Activity,
  Calendar,
  Pill,
  Bell,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock,
  User,
  CreditCard,
  FileText,
  PhoneCall,
} from 'lucide-react';

export const PatientPortalWorkflow: React.FC = () => {
  const [nurseCallActive, setNurseCallActive] = useState(false);
  const [refillRequested, setRefillRequested] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const appointments = [
    {
      id: 'APT-01',
      doctor: 'Dr. Sarah Chen (Cardiology)',
      time: 'Today, 10:30 AM',
      location: 'Cardiology Clinic, Room 402',
      status: 'CONFIRMED',
      type: 'Post-Op Followup',
    },
    {
      id: 'APT-02',
      doctor: 'Dr. Ramesh Rao (Echocardiography)',
      time: 'Thursday, 02:00 PM',
      location: 'Diagnostics Wing, Bay 2',
      status: 'SCHEDULED',
      type: 'Routine Echo Scan',
    },
  ];

  const medications = [
    {
      id: 'MED-01',
      name: 'Aspirin (Ecosprin)',
      dose: '75 mg',
      schedule: 'Once daily after breakfast',
      remainingDays: 14,
      refillAllowed: true,
    },
    {
      id: 'MED-02',
      name: 'Metoprolol Succinate',
      dose: '25 mg',
      schedule: 'Twice daily (Morning & Evening)',
      remainingDays: 3,
      refillAllowed: true,
    },
    {
      id: 'MED-03',
      name: 'Atorvastatin',
      dose: '40 mg',
      schedule: 'Once daily at bedtime',
      remainingDays: 20,
      refillAllowed: false,
    },
  ];

  const handleCallNurse = () => {
    setNurseCallActive(true);
    setFeedback('NURSING STATION NOTIFIED: Duty nurse alerted to Room ICU-Stepdown Bed 04.');
  };

  const handleCancelNurse = () => {
    setNurseCallActive(false);
    setFeedback('Nurse chime canceled.');
    setTimeout(() => setFeedback(null), 3000);
  };

  const handleRequestRefill = (medName: string) => {
    setRefillRequested(medName);
    setFeedback(`Pharmacy refill request submitted for ${medName}.`);
    setTimeout(() => setFeedback(null), 4000);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Patient Greeting & Status Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <Heart className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide">
                PATIENT PORTAL & BEDSIDE CONSOLE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                ● RECOVERY STABLE
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">
              Welcome back, Ramesh Patel
            </h2>
            <p className="text-xs font-mono text-slate-400">
              MRN #PAT-8812 • Room ICU-Stepdown Bed 04 • Attending: Dr. Sarah Chen
            </p>
          </div>
        </div>

        {/* Priority Bedside Nurse Chime */}
        <div>
          {nurseCallActive ? (
            <div className="flex items-center gap-2">
              <div className="px-4 py-2.5 rounded-xl bg-rose-500/20 border border-rose-500/50 text-rose-300 font-mono text-xs font-bold flex items-center gap-2 animate-pulse">
                <Bell className="w-4 h-4 text-rose-400" />
                <span>Nurse Chime Active...</span>
              </div>
              <button
                onClick={handleCancelNurse}
                className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={handleCallNurse}
              className="px-5 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold transition flex items-center gap-2.5 shadow-lg shadow-rose-500/25 active:scale-95"
            >
              <Bell className="w-4 h-4 fill-current" />
              Call Bedside Nurse
            </button>
          )}
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Vitals Telemetry Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-[10px] font-mono text-slate-400 uppercase">Heart Rate</div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">78 bpm</div>
          <span className="text-[10px] font-mono text-emerald-400">Normal Sinus</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-[10px] font-mono text-slate-400 uppercase">Blood Pressure</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">122 / 82</div>
          <span className="text-[10px] font-mono text-emerald-400">Optimal Range</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-[10px] font-mono text-slate-400 uppercase">Oxygen (SpO2)</div>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">98%</div>
          <span className="text-[10px] font-mono text-slate-400">Room Air</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-[10px] font-mono text-slate-400 uppercase">Body Temp</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">36.8 °C</div>
          <span className="text-[10px] font-mono text-emerald-400">Afebrile</span>
        </div>
      </div>

      {/* Appointments & Active Prescriptions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Appointments (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Upcoming Care Schedule</span>
            <span>2 Scheduled</span>
          </div>

          <div className="space-y-3">
            {appointments.map((apt) => (
              <div
                key={apt.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-2.5"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-xs font-bold font-mono text-slate-100">{apt.type}</h4>
                    <p className="text-xs font-mono text-cyan-400 mt-0.5">{apt.doctor}</p>
                  </div>
                  <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                    {apt.status}
                  </span>
                </div>

                <div className="flex items-center gap-4 text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-500" /> {apt.time}
                  </span>
                  <span>{apt.location}</span>
                </div>

                <button
                  onClick={() => {
                    setFeedback(`Checked in for ${apt.type} with ${apt.doctor}.`);
                    setTimeout(() => setFeedback(null), 3000);
                  }}
                  className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono font-bold transition"
                >
                  Confirm Check-In
                </button>
              </div>
            ))}
          </div>

          {/* Quick Discharge Records Download */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-2">
            <div className="text-xs font-bold font-mono text-slate-200 flex items-center gap-2">
              <Download className="w-4 h-4 text-cyan-400" />
              Download My Medical Records
            </div>
            <p className="text-[10px] font-mono text-slate-400">
              Download cryptographically verified clinical summaries and lab reports.
            </p>
            <button
              onClick={() => {
                setFeedback('Encrypted PDF record package generated and downloaded.');
                setTimeout(() => setFeedback(null), 3000);
              }}
              className="w-full py-2 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-bold transition flex items-center justify-center gap-2"
            >
              <Download className="w-3.5 h-3.5" />
              Download Signed Health Passport (PDF)
            </button>
          </div>
        </div>

        {/* Digital Prescriptions & Pharmacy Refill (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Prescription Medications</span>
            <span>Refills Managed Directly</span>
          </div>

          <div className="space-y-3">
            {medications.map((med) => (
              <div
                key={med.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Pill className="w-4 h-4 text-rose-400" />
                    <h4 className="text-xs font-bold font-mono text-slate-100">{med.name}</h4>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {med.dose}
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-400">{med.schedule}</p>
                  <p className="text-[10px] font-mono text-amber-400">
                    {med.remainingDays} days supply remaining
                  </p>
                </div>

                <div>
                  <button
                    onClick={() => handleRequestRefill(med.name)}
                    disabled={!med.refillAllowed || refillRequested === med.name}
                    className={`px-4 py-2 rounded-xl font-mono text-xs font-bold transition ${
                      refillRequested === med.name
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : med.refillAllowed
                        ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                        : 'bg-slate-950 text-slate-600 cursor-not-allowed border border-slate-900'
                    }`}
                  >
                    {refillRequested === med.name
                      ? 'Refill Pending'
                      : med.refillAllowed
                      ? 'Request Refill'
                      : 'Refill Locked'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
