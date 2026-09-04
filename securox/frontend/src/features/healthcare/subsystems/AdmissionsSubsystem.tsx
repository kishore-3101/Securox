import React, { useState, useEffect } from 'react';
import {
  Bed,
  CheckCircle2,
  AlertCircle,
  Plus,
  LogOut,
  RotateCcw,
  Building,
  HeartPulse,
  UserCheck,
} from 'lucide-react';
import { Admission, Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface AdmissionsSubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const AdmissionsSubsystem: React.FC<AdmissionsSubsystemProps> = ({ patients, userRole }) => {
  const [admissions, setAdmissions] = useState<Admission[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAdmitModal, setShowAdmitModal] = useState(false);
  const [patientId, setPatientId] = useState('P-1002');
  const [department, setDepartment] = useState('Cardiology');
  const [roomBed, setRoomBed] = useState('ICU-Bed-04');
  const [admissionType, setAdmissionType] = useState('ICU');
  const [admittingDoctor, setAdmittingDoctor] = useState('doctor');
  const [assignedNurse, setAssignedNurse] = useState('nurse');
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchAdmissions = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getAdmissions();
      if (res && res.admissions) {
        setAdmissions(res.admissions);
      }
    } catch (err) {
      console.error('Error fetching admissions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmissions();
  }, []);

  const handleAdmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await healthcareService.createAdmission({
        patient_id: patientId,
        hospital_id: 'H001',
        department,
        room_bed: roomBed,
        admission_type: admissionType,
        admitting_doctor_id: admittingDoctor,
        assigned_nurse_id: assignedNurse,
      });
      if (res.admission) {
        setAdmissions((prev) => [res.admission, ...prev]);
        setShowAdmitModal(false);
        setActionMsg(`Patient ${res.admission.patient_id} admitted to ${res.admission.room_bed}`);
        setTimeout(() => setActionMsg(null), 4000);
      }
    } catch (err: any) {
      alert(`Admission failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleDischarge = async (admissionId: string, patientName?: string) => {
    if (!confirm(`Confirm clinical discharge for admission ${admissionId}? This will release the bed.`)) {
      return;
    }
    try {
      await healthcareService.dischargeAdmission(admissionId);
      setAdmissions((prev) =>
        prev.map((a) => (a.id === admissionId ? { ...a, status: 'DISCHARGED' } : a))
      );
      setActionMsg(`Admission ${admissionId} successfully discharged and bed released.`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      alert(`Discharge failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const activeAdmissions = admissions.filter((a) => a.status === 'ADMITTED');

  return (
    <div className="space-y-6">
      {actionMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Header & Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Bed className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
              Inpatient Admissions & Ward Bed Management
            </h3>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Dynamic bed allocation, ward occupancy tracking, and clinical discharge pipeline
          </p>
        </div>

        <button
          onClick={() => setShowAdmitModal(true)}
          className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-mono text-xs font-bold transition flex items-center gap-2 self-start sm:self-auto shadow-lg shadow-sky-900/20"
        >
          <Plus className="w-4 h-4" />
          <span>Admit Patient to Bed</span>
        </button>
      </div>

      {/* Admissions Roster Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <HeartPulse className="w-4 h-4 text-rose-400" />
            <span>Currently Admitted Inpatients ({activeAdmissions.length})</span>
          </div>
          <button
            onClick={fetchAdmissions}
            className="text-xs font-mono text-slate-400 hover:text-sky-400 flex items-center gap-1 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Adm ID</th>
                <th className="px-3.5 py-2.5">Patient</th>
                <th className="px-3.5 py-2.5">Department</th>
                <th className="px-3.5 py-2.5">Allocated Bed</th>
                <th className="px-3.5 py-2.5">Acuity Type</th>
                <th className="px-3.5 py-2.5">Attending Doctor</th>
                <th className="px-3.5 py-2.5">Assigned Nurse</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Discharge</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {admissions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3.5 py-6 text-center text-slate-500">
                    No admission records currently tracked.
                  </td>
                </tr>
              ) : (
                admissions.map((adm) => (
                  <tr key={adm.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{adm.id}</td>
                    <td className="px-3.5 py-2.5 text-slate-200 font-semibold">
                      {adm.patient_name || adm.patient_id}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {adm.department}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-200 font-bold">{adm.room_bed}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          adm.admission_type === 'ICU'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : adm.admission_type === 'EMERGENCY'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-sky-950 text-sky-300 border border-sky-800'
                        }`}
                      >
                        {adm.admission_type}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">Dr. {adm.admitting_doctor_id}</td>
                    <td className="px-3.5 py-2.5 text-slate-400">{adm.assigned_nurse_id || 'On-Duty'}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          adm.status === 'ADMITTED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {adm.status}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-right">
                      {adm.status === 'ADMITTED' ? (
                        <button
                          onClick={() => handleDischarge(adm.id, adm.patient_name)}
                          className="px-2.5 py-1 rounded bg-rose-600/20 text-rose-400 border border-rose-500/40 hover:bg-rose-600/30 text-[11px] font-bold transition flex items-center gap-1 inline-flex"
                        >
                          <LogOut className="w-3 h-3" />
                          <span>Discharge</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500">Released</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Admit Patient Modal */}
      {showAdmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Bed className="w-4 h-4" />
                <span>Admit Inpatient & Allocate Bed</span>
              </div>
              <button onClick={() => setShowAdmitModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleAdmit} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Select Registered Patient</label>
                <select
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.id}) - {p.department}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Department</label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  >
                    <option value="Cardiology">Cardiology</option>
                    <option value="Emergency">Emergency</option>
                    <option value="Oncology">Oncology</option>
                    <option value="Neurology">Neurology</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Admission Type</label>
                  <select
                    value={admissionType}
                    onChange={(e) => setAdmissionType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  >
                    <option value="ICU">ICU</option>
                    <option value="EMERGENCY">EMERGENCY</option>
                    <option value="PLANNED">PLANNED</option>
                    <option value="TRANSFER">TRANSFER</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Allocated Bed / Room</label>
                <input
                  type="text"
                  value={roomBed}
                  onChange={(e) => setRoomBed(e.target.value)}
                  placeholder="e.g., ICU-Bed-05 or Stepdown-02"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Admitting Physician</label>
                  <input
                    type="text"
                    value={admittingDoctor}
                    onChange={(e) => setAdmittingDoctor(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Assigned Nurse</label>
                  <input
                    type="text"
                    value={assignedNurse}
                    onChange={(e) => setAssignedNurse(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAdmitModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold"
                >
                  Confirm Admission
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
