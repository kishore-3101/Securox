import React, { useState } from 'react';
import {
  UserPlus,
  Users,
  Search,
  Filter,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Stethoscope,
  Building,
  Bed,
  Heart,
  Lock,
} from 'lucide-react';
import { Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface PatientRegistrationSubsystemProps {
  patients: Patient[];
  onPatientRegistered: (patient: Patient) => void;
  userRole: string;
}

export const PatientRegistrationSubsystem: React.FC<PatientRegistrationSubsystemProps> = ({
  patients,
  onPatientRegistered,
  userRole,
}) => {
  const [name, setName] = useState('');
  const [age, setAge] = useState<number>(45);
  const [gender, setGender] = useState('Male');
  const [department, setDepartment] = useState('Cardiology');
  const [condition, setCondition] = useState('GUARDED');
  const [diagnosis, setDiagnosis] = useState('');
  const [roomBed, setRoomBed] = useState('Ward-2 / Bed-04');
  const [assignedDoctor, setAssignedDoctor] = useState('doctor');
  const [assignedNurse, setAssignedNurse] = useState('nurse');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deptFilter, setDeptFilter] = useState('ALL');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !department) {
      setErrorMsg('Patient name and department are required.');
      return;
    }
    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await healthcareService.createPatient({
        name,
        age: Number(age),
        gender,
        department,
        condition,
        diagnosis: diagnosis || 'Under Evaluation',
        room_bed: roomBed,
        assigned_doctor_id: assignedDoctor,
        assigned_nurse_id: assignedNurse,
        hospital_id: 'H001',
      });
      if (res.patient) {
        onPatientRegistered(res.patient);
        setSuccessMsg(`Patient ${res.patient.name} (${res.patient.id}) successfully registered!`);
        setName('');
        setDiagnosis('');
      }
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err.message || 'Failed to register patient');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.department && p.department.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesDept = deptFilter === 'ALL' || p.department === deptFilter;
    return matchesSearch && matchesDept;
  });

  const isReception = userRole === 'reception';

  return (
    <div className="space-y-6">
      {/* Role Scoping Notice */}
      {isReception && (
        <div className="p-3.5 rounded-xl bg-sky-950/40 border border-sky-500/40 flex items-center justify-between text-xs font-mono text-sky-300">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-sky-400" />
            <span><b>Reception Stakeholder Scope:</b> Authorized for demographics & intake registration. Clinical medical records & physician treatment notes are masked by HIPAA/DISHA Privacy Shield.</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-sky-900/60 border border-sky-700 text-sky-200">
            PRIVACY SHIELD ACTIVE
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Intake Registration Form */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <UserPlus className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Patient Intake & Demographics Registration
            </h3>
          </div>

          {successMsg && (
            <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-3 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Full Legal Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Rajesh Krishnan"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Age *</label>
                <input
                  type="number"
                  min="1"
                  max="120"
                  required
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Gender *</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Department *</label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                >
                  <option value="Cardiology">Cardiology</option>
                  <option value="Emergency">Emergency</option>
                  <option value="Oncology">Oncology</option>
                  <option value="Neurology">Neurology</option>
                  <option value="Orthopedics">Orthopedics</option>
                  <option value="Nephrology">Nephrology</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Clinical Condition</label>
                <select
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                >
                  <option value="STABLE">STABLE</option>
                  <option value="GUARDED">GUARDED</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Assigned Bed / Ward</label>
              <input
                type="text"
                value={roomBed}
                onChange={(e) => setRoomBed(e.target.value)}
                placeholder="e.g. Ward-3 / Bed-08"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Attending Physician ID</label>
                <input
                  type="text"
                  value={assignedDoctor}
                  onChange={(e) => setAssignedDoctor(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Primary Nurse ID</label>
                <input
                  type="text"
                  value={assignedNurse}
                  onChange={(e) => setAssignedNurse(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Initial Intake Chief Complaint</label>
              <textarea
                rows={2}
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                placeholder="e.g., Acute substernal chest discomfort radiating to left arm"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-sky-500 outline-none resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <UserPlus className="w-4 h-4" />
              <span>{submitting ? 'Registering...' : 'Register Patient & Assign Bed'}</span>
            </button>
          </form>
        </div>

        {/* Live Patient Directory & Scoping */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
                Hospital Master Patient Census ({filteredPatients.length})
              </h3>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search name, ID, dept..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs font-mono text-slate-200 focus:border-sky-500 outline-none w-48"
                />
              </div>

              <select
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200 focus:border-sky-500 outline-none"
              >
                <option value="ALL">All Departments</option>
                <option value="Cardiology">Cardiology</option>
                <option value="Oncology">Oncology</option>
                <option value="Emergency">Emergency</option>
                <option value="Neurology">Neurology</option>
                <option value="Orthopedics">Orthopedics</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-3.5 py-2.5">ID</th>
                  <th className="px-3.5 py-2.5">Patient Name</th>
                  <th className="px-3.5 py-2.5">Demographics</th>
                  <th className="px-3.5 py-2.5">Department</th>
                  <th className="px-3.5 py-2.5">Ward / Bed</th>
                  <th className="px-3.5 py-2.5">Attending</th>
                  <th className="px-3.5 py-2.5">Condition</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredPatients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{p.id}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-slate-200">{p.name}</td>
                    <td className="px-3.5 py-2.5 text-slate-400">
                      {p.age}y • {p.gender}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {p.department}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-300">{p.room_bed || p.room_number || 'Unallocated'}</td>
                    <td className="px-3.5 py-2.5 text-slate-400">Dr. {p.assigned_doctor_id || 'On-Call'}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          p.condition === 'CRITICAL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : p.condition === 'GUARDED'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}
                      >
                        {p.condition || 'STABLE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
