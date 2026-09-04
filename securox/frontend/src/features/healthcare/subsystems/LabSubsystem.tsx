import React, { useState, useEffect } from 'react';
import {
  TestTube,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RotateCcw,
  Check,
  Search,
} from 'lucide-react';
import { LabOrder, Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface LabSubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const LabSubsystem: React.FC<LabSubsystemProps> = ({ patients, userRole }) => {
  const [labOrders, setLabOrders] = useState<LabOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLabId, setSelectedLabId] = useState<string | null>(null);

  // Result entry state
  const [resultVal, setResultVal] = useState<string>('142.5');
  const [resultUnit, setResultUnit] = useState<string>('ng/L');
  const [flagAbnormal, setFlagAbnormal] = useState<boolean>(true);
  const [submittingResult, setSubmittingResult] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getLabOrders();
      if (res && res.lab_orders) {
        setLabOrders(res.lab_orders);
      }
    } catch (err) {
      console.error('Error fetching lab orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleOpenResultModal = (lab: LabOrder) => {
    setSelectedLabId(lab.id);
    if (lab.test_name.toLowerCase().includes('troponin')) {
      setResultVal('142.5');
      setResultUnit('ng/L');
      setFlagAbnormal(true);
    } else {
      setResultVal('14.2');
      setResultUnit('mg/dL');
      setFlagAbnormal(false);
    }
  };

  const handleSubmitResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLabId) return;
    setSubmittingResult(true);
    try {
      await healthcareService.updateLabResult(
        selectedLabId,
        {
          measured_value: Number(resultVal) || resultVal,
          unit: resultUnit,
          flag: flagAbnormal ? 'CRITICAL_HIGH' : 'NORMAL',
        },
        flagAbnormal,
        'lab_tech'
      );
      setLabOrders((prev) =>
        prev.map((l) =>
          l.id === selectedLabId
            ? {
                ...l,
                status: 'COMPLETED',
                flagged_abnormal: flagAbnormal,
                result_data: { measured_value: resultVal, unit: resultUnit },
              }
            : l
        )
      );
      setActionMsg(`Lab order ${selectedLabId} successfully completed and verified.`);
      setSelectedLabId(null);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      alert(`Failed to submit lab result: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSubmittingResult(false);
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
            <TestTube className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Laboratory Information System (LIS) Diagnostics Queue
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            STAT Troponin-T panels, cardiac biomarker verification, and reference range validation
          </p>
        </div>

        <button
          onClick={fetchOrders}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Lab Queue Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <span>Active Specimen Analysis Orders ({labOrders.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">LIS Biochemistry Division</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Order ID</th>
                <th className="px-3.5 py-2.5">Patient</th>
                <th className="px-3.5 py-2.5">Test Name</th>
                <th className="px-3.5 py-2.5">Category</th>
                <th className="px-3.5 py-2.5">Priority</th>
                <th className="px-3.5 py-2.5">Ref Range</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Result Intake</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {labOrders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3.5 py-6 text-center text-slate-500">
                    No diagnostic laboratory orders in queue.
                  </td>
                </tr>
              ) : (
                labOrders.map((lab) => (
                  <tr key={lab.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{lab.id}</td>
                    <td className="px-3.5 py-2.5 font-semibold text-slate-200">
                      {lab.patient_name || lab.patient_id}
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-200 font-bold">{lab.test_name}</td>
                    <td className="px-3.5 py-2.5 text-slate-400">{lab.category}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          lab.priority === 'STAT'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800 animate-pulse'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {lab.priority}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">{lab.reference_range || '< 14 ng/L'}</td>
                    <td className="px-3.5 py-2.5">
                      {lab.flagged_abnormal ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 flex items-center gap-1 w-max">
                          <AlertTriangle className="w-3 h-3 text-rose-400" />
                          <span>ABNORMAL CRITICAL</span>
                        </span>
                      ) : (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            lab.status === 'COMPLETED'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : 'bg-slate-800 text-slate-300 border border-slate-700'
                          }`}
                        >
                          {lab.status}
                        </span>
                      )}
                    </td>
                    <td className="px-3.5 py-2.5 text-right">
                      {lab.status !== 'COMPLETED' ? (
                        <button
                          onClick={() => handleOpenResultModal(lab)}
                          className="px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-600/30 text-[11px] font-bold transition"
                        >
                          Enter Result
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-400 font-bold">Verified & Signed</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Result Entry Modal */}
      {selectedLabId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <TestTube className="w-4 h-4" />
                <span>Submit & Sign LIS Laboratory Result: {selectedLabId}</span>
              </div>
              <button onClick={() => setSelectedLabId(null)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmitResult} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Measured Value *</label>
                  <input
                    type="text"
                    required
                    value={resultVal}
                    onChange={(e) => setResultVal(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500 font-bold"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Unit of Measure</label>
                  <input
                    type="text"
                    value={resultUnit}
                    onChange={(e) => setResultUnit(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={flagAbnormal}
                    onChange={(e) => setFlagAbnormal(e.target.checked)}
                    className="rounded border-slate-700 text-rose-600 focus:ring-rose-500"
                  />
                  <span className="text-rose-400 font-bold">Flag as Critically Abnormal (STAT Alert)</span>
                </label>
                <div className="text-[10px] text-slate-400">
                  Value exceeds normal clinical thresholds (&gt; 14 ng/L for hs-cTnT). Will trigger emergency alert on doctor's station.
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedLabId(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingResult}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                >
                  {submittingResult ? 'Signing...' : 'Sign & Transmit Result'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
