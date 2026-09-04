import React, { useState } from 'react';
import { FinanceTransaction, FinanceAccount, FinancePersonaRole } from '../../../types/finance';
import { Send, ShieldCheck, ShieldAlert, CheckCircle2, AlertOctagon, RefreshCw } from 'lucide-react';

interface TransactionPipelineSubsystemProps {
  transactions: FinanceTransaction[];
  accounts: FinanceAccount[];
  activePersonaRole: FinancePersonaRole;
  isReadOnly: boolean;
  onSubmitTransaction: (payload: any) => Promise<any>;
  onRefresh: () => void;
}

export const TransactionPipelineSubsystem: React.FC<TransactionPipelineSubsystemProps> = ({
  transactions,
  accounts,
  activePersonaRole,
  isReadOnly,
  onSubmitTransaction,
  onRefresh
}) => {
  const [selectedAccountId, setSelectedAccountId] = useState(accounts[0]?.id || 'ACC-7001');
  const [counterparty, setCounterparty] = useState('ACC-7003');
  const [amount, setAmount] = useState<number>(25000);
  const [channel, setChannel] = useState('UPI');
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isReadOnly) return;
    setSubmitting(true);
    try {
      const res = await onSubmitTransaction({
        account_id: selectedAccountId,
        counterparty_account: counterparty,
        amount: Number(amount),
        channel
      });
      setLastResult(res);
      onRefresh();
    } catch (err: any) {
      alert(`Transaction rejected: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Transaction Submission & Evaluation Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Send className="w-4 h-4 text-blue-400" />
              Pre-Settlement Transaction Gateway
            </h3>
          </div>

          {isReadOnly ? (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
              Auditor persona active: Transaction initiation is disabled in read-only audit mode.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Debit Account</label>
                <select
                  value={selectedAccountId}
                  onChange={e => setSelectedAccountId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white"
                >
                  {accounts.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.account_number} ({a.account_type}) - ₹{a.balance.toLocaleString('en-IN')}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Counterparty / Recipient Account</label>
                <input
                  type="text"
                  value={counterparty}
                  onChange={e => setCounterparty(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono"
                  placeholder="e.g. ACC-7003 or OFFSHORE-ACC-9981"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Amount (INR)</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={e => setAmount(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Channel</label>
                  <select
                    value={channel}
                    onChange={e => setChannel(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white"
                  >
                    <option value="UPI">UPI (Immediate)</option>
                    <option value="IMPS">IMPS</option>
                    <option value="NEFT">NEFT</option>
                    <option value="RTGS">RTGS High-Value</option>
                    <option value="SWIFT">SWIFT International</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full mt-2 py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center justify-center gap-2"
              >
                {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Evaluate & Execute Pre-Settlement Check
              </button>
            </form>
          )}

          {/* Assessment Result Box */}
          {lastResult && (
            <div className="mt-4 p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">ML Scoring Result</span>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {lastResult.assessment.model_attribution}
                </span>
              </div>
              <div className="text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Decision:</span>
                  <span className="font-bold font-mono text-white">{lastResult.assessment.decision}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">XGBoost Fraud Score:</span>
                  <span className="font-mono text-amber-400">{lastResult.assessment.xgboost_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Isolation Forest Score:</span>
                  <span className="font-mono text-purple-400">{lastResult.assessment.isolation_forest_score}</span>
                </div>
                {lastResult.assessment.case && (
                  <div className="pt-2 text-rose-400 text-[11px] font-semibold">
                    🚨 Fraud Case Auto-Created: {lastResult.assessment.case.case_number}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Live Transaction Feed Table */}
        <div className="lg:col-span-2 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Live Transactions Audit Feed</h3>
            <button onClick={onRefresh} className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="pb-2">TX ID</th>
                  <th className="pb-2">Channel</th>
                  <th className="pb-2">Counterparty</th>
                  <th className="pb-2 text-right">Amount</th>
                  <th className="pb-2 text-center">Status</th>
                  <th className="pb-2 text-right">Risk Score</th>
                  <th className="pb-2 text-center">Attribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {transactions.map(tx => {
                  const isBlocked = tx.status === 'BLOCKED';
                  const isFlagged = tx.status.includes('FLAGGED');

                  return (
                    <tr key={tx.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 text-white">{tx.id}</td>
                      <td className="py-2.5 text-slate-400">{tx.channel}</td>
                      <td className="py-2.5 text-slate-300">{tx.counterparty_account}</td>
                      <td className="py-2.5 text-right font-bold text-white">₹{tx.amount.toLocaleString('en-IN')}</td>
                      <td className="py-2.5 text-center">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded ${
                            isBlocked
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : isFlagged
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}
                        >
                          {tx.status}
                        </span>
                      </td>
                      <td className="py-2.5 text-right text-amber-400">{tx.risk_score}</td>
                      <td className="py-2.5 text-center">
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          {tx.model_attribution}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
