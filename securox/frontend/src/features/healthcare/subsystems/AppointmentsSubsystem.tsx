import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  UserCheck,
  Plus,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Check,
  X,
  Stethoscope,
} from 'lucide-react';
import { Appointment, Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface AppointmentsSubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const AppointmentsSubsystem: React.FC<AppointmentsSubsystemProps> = ({ patients, userRole }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [showBookModal, setShowBookModal] = useState(false);
  const [patientId, setPatientId] = useState('P-1001');
  const [department, setDepartment] = useState('Cardiology');
  const [doctorId, setDoctorId] = useState('doctor');
  const [reason, setReason] = useState('Routine Cardiac Consultation & Echo Review');
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getAppointments();
      if (res && res.appointments) {
        setAppointments(res.appointments);
      }
    } catch (err) {
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleCreateAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await healthcareService.createAppointment({
        patient_id: patientId,
        department,
        doctor_id: doctorId,
        reason,
        hospital_id: 'H001',
      });
      if (res.appointment) {
        setAppointments((prev) => [res.appointment, ...prev]);
        setShowBookModal(false);
        setActionMsg(`Appointment token ${res.appointment.id} successfully generated!`);
        setTimeout(() => setActionMsg(null), 4000);
      }
    } catch (err: any) {
      alert(`Error creating appointment: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleStatusTransition = async (appointmentId: string, nextStatus: string) => {
    try {
      await healthcareService.updateAppointmentStatus(appointmentId, nextStatus);
      setAppointments((prev) =>
        prev.map((a) => (a.id === appointmentId ? { ...a, status: nextStatus as any } : a))
      );
      setActionMsg(`Token ${appointmentId} status moved to ${nextStatus}`);
      setTimeout(() => setActionMsg(null), 3000);
    } catch (err: any) {
      alert(`Status transition failed: ${err?.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Message Banner */}
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
            <Calendar className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
              Doctor Consultation Token Queue & Scheduling
            </h3>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time outpatient tokens, queuing priority, and consultation lifecycle tracking
          </p>
        </div>

        <button
          onClick={() => setShowBookModal(true)}
          className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-mono text-xs font-bold transition flex items-center gap-2 self-start sm:self-auto shadow-lg shadow-sky-900/20"
        >
          <Plus className="w-4 h-4" />
          <span>Issue Consultation Token</span>
        </button>
      </div>

      {/* Appointment Tokens Queue Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-400" />
            <span>Active Outpatient Consultation Tokens ({appointments.length})</span>
          </div>
          <button
            onClick={fetchAppointments}
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
                <th className="px-3.5 py-2.5">Token ID</th>
                <th className="px-3.5 py-2.5">Patient</th>
                <th className="px-3.5 py-2.5">Department</th>
                <th className="px-3.5 py-2.5">Clinician</th>
                <th className="px-3.5 py-2.5">Scheduled Slot</th>
                <th className="px-3.5 py-2.5">Reason</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Queue Progression</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {appointments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No consultation tokens currently scheduled.
                  </td>
                </tr>
              ) : (
                appointments.map((apt) => (
                  <tr key={apt.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{apt.id}</td>
                    <td className="px-3.5 py-2.5 text-slate-200 font-semibold">
                      {apt.patient_name || apt.patient_id}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {apt.department}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">Dr. {apt.doctor_id}</td>
                    <td className="px-3.5 py-2.5 text-slate-300">
                      {apt.scheduled_at ? new Date(apt.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Immediate Token'}
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400 max-w-xs truncate">{apt.reason}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          apt.status === 'COMPLETED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : apt.status === 'IN_CONSULTATION'
                            ? 'bg-sky-950 text-sky-300 border border-sky-800 animate-pulse'
                            : apt.status === 'CONFIRMED'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {apt.status}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-right space-x-1.5">
                      {apt.status === 'SCHEDULED' && (
                        <button
                          onClick={() => handleStatusTransition(apt.id, 'CONFIRMED')}
                          className="px-2 py-1 rounded bg-amber-600/20 text-amber-400 border border-amber-500/40 hover:bg-amber-600/30 text-[11px]"
                        >
                          Confirm
                        </button>
                      )}
                      {apt.status === 'CONFIRMED' && (
                        <button
                          onClick={() => handleStatusTransition(apt.id, 'IN_CONSULTATION')}
                          className="px-2 py-1 rounded bg-sky-600/20 text-sky-400 border border-sky-500/40 hover:bg-sky-600/30 text-[11px] flex items-center gap-1 inline-flex"
                        >
                          <Play className="w-3 h-3" />
                          <span>Call In</span>
                        </button>
                      )}
                      {apt.status === 'IN_CONSULTATION' && (
                        <button
                          onClick={() => handleStatusTransition(apt.id, 'COMPLETED')}
                          className="px-2 py-1 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-600/30 text-[11px] flex items-center gap-1 inline-flex"
                        >
                          <Check className="w-3 h-3" />
                          <span>Complete</span>
                        </button>
                      )}
                      {apt.status !== 'COMPLETED' && apt.status !== 'CANCELLED' && (
                        <button
                          onClick={() => handleStatusTransition(apt.id, 'CANCELLED')}
                          className="px-1.5 py-1 rounded bg-rose-600/10 text-rose-400 hover:bg-rose-600/20 text-[11px]"
                          title="Cancel token"
                        >
                          <X className="w-3 h-3" />
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

      {/* Book Appointment Modal */}
      {showBookModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Calendar className="w-4 h-4" />
                <span>Issue Outpatient Consultation Token</span>
              </div>
              <button onClick={() => setShowBookModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAppointment} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Select Patient</label>
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
                  <option value="Orthopedics">Orthopedics</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Doctor ID</label>
                <input
                  type="text"
                  value={doctorId}
                  onChange={(e) => setDoctorId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Consultation Reason</label>
                <textarea
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowBookModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold"
                >
                  Generate Token
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
