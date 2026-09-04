import React, { useState, useEffect } from 'react';
import {
  Pill,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Clock,
  Check,
} from 'lucide-react';
import { Prescription, Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface PharmacySubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const PharmacySubsystem: React.FC<PharmacySubsystemProps> = ({ patients, userRole }) => {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(false);
  const [dispensingId, setDispensingId] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchPrescriptions = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getPrescriptions();
      if (res && res.prescriptions) {
        setPrescriptions(res.prescriptions);
      }
    } catch (err) {
      console.error('Error fetching prescriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, []);

  const handleDispense = async (prescriptionId: string, medName: string) => {
    setDispensingId(prescriptionId);
    try {
      await healthcareService.dispensePrescription(prescriptionId, 'pharmacist');
      setPrescriptions((prev) =>
        prev.map((p) =>
          p.id === prescriptionId
            ? { ...p, status: 'DISPENSED', dispensed_at: new Date().toISOString() }
            : p
        )
      );
      setActionMsg(`Medication "${medName}" (${prescriptionId}) dispensed from Pyxis MedStation.`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      alert(`Dispense failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setDispensingId(null);
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

      {/* Header */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Pill className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Central Pharmacy & Pyxis MedStation Dispensing
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time prescription validation, automated DDI safety engine, and electronic cabinet actuation
          </p>
        </div>

        <button
          onClick={fetchPrescriptions}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Prescriptions Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-400" />
            <span>Prescriptions & Automated Safety Alerts ({prescriptions.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">Pyxis Vault Unit 4A</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Rx ID</th>
                <th className="px-3.5 py-2.5">Patient</th>
                <th className="px-3.5 py-2.5">Medication & Regimen</th>
                <th className="px-3.5 py-2.5">Frequency & Duration</th>
                <th className="px-3.5 py-2.5">Prescriber</th>
                <th className="px-3.5 py-2.5">DDI / Interaction Engine</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Pyxis Actuation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {prescriptions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No pending prescriptions in pharmacy queue.
                  </td>
                </tr>
              ) : (
                prescriptions.map((rx) => (
                  <tr key={rx.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{rx.id}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-slate-200">
                      {rx.patient_name || rx.patient_id}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <div className="font-bold text-slate-100">{rx.medication}</div>
                      <div className="text-[11px] text-slate-400">{rx.dosage}</div>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-300">
                      {rx.frequency} • {rx.duration}
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">Dr. {rx.doctor_id}</td>
                    <td className="px-3.5 py-2.5">
                      {rx.ddi_warning ? (
                        <span className="px-2 py-1 rounded text-[10px] font-bold bg-amber-950/70 text-amber-300 border border-amber-800 flex items-center gap-1.5 w-max">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <span>{rx.ddi_warning}</span>
                        </span>
                      ) : (
                        <span className="text-[10px] text-emerald-400 font-semibold">No DDI Conflicts</span>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          rx.status === 'DISPENSED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}
                      >
                        {rx.status}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-right">
                      {rx.status !== 'DISPENSED' ? (
                        <button
                          onClick={() => handleDispense(rx.id, rx.medication)}
                          disabled={dispensingId === rx.id}
                          className="px-2.5 py-1 rounded bg-sky-600/20 text-sky-400 border border-sky-500/40 hover:bg-sky-600/30 text-[11px] font-bold transition flex items-center gap-1 inline-flex disabled:opacity-50"
                        >
                          <Zap className="w-3 h-3 text-sky-400" />
                          <span>{dispensingId === rx.id ? 'Unlocking...' : 'Dispense Pyxis'}</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1 justify-end">
                          <Check className="w-3 h-3" />
                          <span>Dispensed</span>
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
