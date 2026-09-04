import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  Lock,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Plus,
  RotateCcw,
  Receipt,
  FileText,
  DollarSign,
  QrCode,
} from 'lucide-react';
import { BillingInvoice, Patient } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface BillingSubsystemProps {
  patients: Patient[];
  userRole: string;
}

export const BillingSubsystem: React.FC<BillingSubsystemProps> = ({ patients, userRole }) => {
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [patientId, setPatientId] = useState('P-1001');
  const [totalAmt, setTotalAmt] = useState<number>(78500);
  const [claimAmt, setClaimAmt] = useState<number>(65000);
  const [paymentMethod, setPaymentMethod] = useState('INSURANCE_TPA');
  const [settlingId, setSettlingId] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getBillingInvoices();
      if (res && res.invoices) {
        setInvoices(res.invoices);
      }
    } catch (err) {
      console.error('Error fetching invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    const payable = Math.max(0, totalAmt - claimAmt);
    try {
      const res = await healthcareService.createBillingInvoice({
        patient_id: patientId,
        hospital_id: 'H001',
        total_amount: totalAmt,
        insurance_claim_amount: claimAmt,
        patient_payable: payable,
        payment_method: paymentMethod,
        line_items: [
          { item: 'Cath Lab / Angiography Procedure', amount: totalAmt * 0.65 },
          { item: 'Inpatient Bed & Intensive Nursing (2 days)', amount: totalAmt * 0.2 },
          { item: 'STAT Laboratory Panels & Pharmacy', amount: totalAmt * 0.15 },
        ],
      });
      if (res.invoice) {
        setInvoices((prev) => [res.invoice, ...prev]);
        setShowCreateModal(false);
        setActionMsg(`Invoice ${res.invoice.id} generated for patient ${res.invoice.patient_id}`);
        setTimeout(() => setActionMsg(null), 4000);
      }
    } catch (err: any) {
      alert(`Failed to create invoice: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleSettle = async (invoiceId: string) => {
    setSettlingId(invoiceId);
    try {
      await healthcareService.settleBillingInvoice(invoiceId, 'UPI_INSTANT');
      setInvoices((prev) =>
        prev.map((inv) =>
          inv.id === invoiceId
            ? { ...inv, status: 'SETTLED', settled_at: new Date().toISOString() }
            : inv
        )
      );
      setActionMsg(`Invoice ${invoiceId} marked SETTLED via Cashless TPA / UPI.`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (err: any) {
      alert(`Settlement failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSettlingId(null);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Clinical Privacy Barrier Warning Banner */}
      <div className="bg-slate-900/90 border border-amber-500/40 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-amber-300">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold uppercase tracking-wider flex items-center gap-2">
              <span>DISHA & HIPAA Clinical Privacy Barrier Enforced</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 border border-amber-700 text-amber-200">
                ZERO CLINICAL LEAK
              </span>
            </div>
            <div className="text-slate-400 text-[11px] mt-0.5">
              Billing and administrative personnel are strictly barred from clinical medical records. Diagnoses are redacted as <b>[CLINICAL_RESTRICTED]</b> to comply with statutory healthcare privacy mandates.
            </div>
          </div>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Header & Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Patient Billing, TPA Insurance Claims & Settlement
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Cashless claim verification, automated copay calculation, and instant UPI / TPA reconciliation
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold transition flex items-center gap-1.5 shadow-lg shadow-sky-900/20"
          >
            <Plus className="w-4 h-4" />
            <span>Generate Inpatient Invoice</span>
          </button>
          <button
            onClick={fetchInvoices}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh Invoices"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Receipt className="w-4 h-4 text-sky-400" />
            <span>Hospital Billing Invoices ({invoices.length})</span>
          </div>
          <span className="text-[11px] text-slate-400">Revenue Cycle Operations</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-3.5 py-2.5">Invoice #</th>
                <th className="px-3.5 py-2.5">Patient ID</th>
                <th className="px-3.5 py-2.5">Diagnosis (Privacy Shield)</th>
                <th className="px-3.5 py-2.5">Total Bill (₹)</th>
                <th className="px-3.5 py-2.5">TPA Claim (₹)</th>
                <th className="px-3.5 py-2.5">Patient Payable (₹)</th>
                <th className="px-3.5 py-2.5">Method</th>
                <th className="px-3.5 py-2.5">Status</th>
                <th className="px-3.5 py-2.5 text-right">Settlement</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3.5 py-6 text-center text-slate-500">
                    No billing invoices generated.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-2.5 font-bold text-sky-400">{inv.id}</td>
                    <td className="px-3.5 py-2.5 text-slate-200 font-semibold">{inv.patient_id}</td>
                    <td className="px-3.5 py-2.5">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 font-mono">
                        [CLINICAL_RESTRICTED]
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 font-bold text-slate-100">
                      ₹{Number(inv.total_amount).toLocaleString('en-IN')}
                    </td>
                    <td className="px-3.5 py-2.5 text-emerald-400">
                      ₹{Number(inv.insurance_claim_amount).toLocaleString('en-IN')}
                    </td>
                    <td className="px-3.5 py-2.5 font-bold text-amber-400">
                      ₹{Number(inv.patient_payable).toLocaleString('en-IN')}
                    </td>
                    <td className="px-3.5 py-2.5 text-slate-400">{inv.payment_method}</td>
                    <td className="px-3.5 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          inv.status === 'SETTLED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-3.5 py-2.5 text-right">
                      {inv.status !== 'SETTLED' ? (
                        <button
                          onClick={() => handleSettle(inv.id)}
                          disabled={settlingId === inv.id}
                          className="px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-600/30 text-[11px] font-bold transition flex items-center gap-1 inline-flex disabled:opacity-50"
                        >
                          <QrCode className="w-3 h-3" />
                          <span>{settlingId === inv.id ? 'Reconciling...' : 'Settle UPI/TPA'}</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-400 font-bold">Reconciled</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Invoice Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Receipt className="w-4 h-4" />
                <span>Generate Inpatient Hospital Invoice</span>
              </div>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateInvoice} className="space-y-3">
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
                <label className="block text-slate-400 mb-1">Total Billable Amount (₹)</label>
                <input
                  type="number"
                  required
                  value={totalAmt}
                  onChange={(e) => setTotalAmt(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500 font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">TPA Insurance Pre-Auth Claim (₹)</label>
                <input
                  type="number"
                  required
                  value={claimAmt}
                  onChange={(e) => setClaimAmt(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-emerald-400 outline-none focus:border-emerald-500 font-bold"
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center font-bold">
                <span className="text-slate-400">Patient Direct Payable:</span>
                <span className="text-amber-400 text-sm">
                  ₹{Math.max(0, totalAmt - claimAmt).toLocaleString('en-IN')}
                </span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Payment Channel</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-sky-500"
                >
                  <option value="INSURANCE_TPA">Cashless TPA Pre-Auth</option>
                  <option value="UPI">UPI Instant QR</option>
                  <option value="CREDIT_CARD">Credit / Debit Card</option>
                  <option value="NEFT_WIRE">Hospital Corporate Wire</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold"
                >
                  Generate Invoice
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
