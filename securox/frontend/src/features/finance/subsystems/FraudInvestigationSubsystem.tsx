import React, { useState } from 'react';
import { FinanceFraudCase, FinancePersonaRole } from '../../../types/finance';
import { ShieldAlert, CheckCircle2, Lock, FileText, AlertTriangle, RefreshCw } from 'lucide-react';

interface FraudInvestigationSubsystemProps {
  cases: FinanceFraudCase[];
  activePersonaRole: FinancePersonaRole;
  isReadOnly: boolean;
  onDecideCase: (caseId: string, payload: any) => Promise<any>;
  onRefresh: () => void;
}

export const FraudInvestigationSubsystem: React.FC<FraudInvestigationSubsystemProps> = ({
  cases,
  activePersonaRole,
  isReadOnly,
  onDecideCase,
  onRefresh
}) => {
  const [selectedCase, setSelectedCase] = useState<FinanceFraudCase | null>(cases[0] || null);
  const [decision, setDecision] = useState('CONFIRMED_FRAUD');
  const [rationale, setRationale] = useState('');
  const [notes, setNotes] = useState('');
  const [freezeAccount, setFreezeAccount] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const handleResolve = async () => {
    if (!selectedCase || isReadOnly) return;
    if (!rationale) {
      alert('Please enter an investigative rationale.');
      return;
    }
    setSubmitting(true);
    try {
      await onDecideCase(selectedCase.id, {
        decision,
        decision_rationale: rationale,
        resolution_notes: notes || 'Resolved by lead fraud analyst in SOC command.',
        freeze_account: freezeAccount
      });
      alert(`Case ${selectedCase.case_number} resolved as ${decision}.`);
      onRefresh();
    } catch (err: any) {
      alert(`Decision error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List */}
        <div className="lg:col-span-1 bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Active Fraud Investigations ({cases.length})
            </h3>
            <button onClick={onRefresh} className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {cases.map(c => {
              const isSelected = selectedCase?.id === c.id;
              const isOpen = c.status === 'OPEN' || c.status === 'INVESTIGATING';

              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCase(c)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    isSelected
                      ? 'bg-blue-950/40 border-blue-500'
                      : 'bg-slate-800/40 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-white">{c.case_number}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                        isOpen
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-medium truncate">{c.title}</div>
                  <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
                    <span>Exp: ₹{c.total_exposure_inr.toLocaleString('en-IN')}</span>
                    <span className="text-rose-400 font-semibold">{c.severity}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Case Detail & Adjudication Console */}
        <div className="lg:col-span-2 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
          {selectedCase ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <div className="text-xs text-slate-400">CASE DOSSIER</div>
                  <h3 className="text-base font-bold text-white font-mono">{selectedCase.case_number}</h3>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">TOTAL EXPOSURE</div>
                  <div className="text-lg font-bold text-rose-400 font-mono">
                    ₹{selectedCase.total_exposure_inr.toLocaleString('en-IN')}
                  </div>
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-400 mb-1">Incident Summary</div>
                <div className="p-3 bg-slate-950 rounded-lg text-xs text-slate-200 border border-slate-800/80">
                  {selectedCase.title}
                </div>
              </div>

              {selectedCase.decision_rationale && (
                <div>
                  <div className="text-xs font-semibold text-slate-400 mb-1">AI Risk & Model Telemetry</div>
                  <div className="p-3 bg-slate-950 rounded-lg text-xs text-amber-300 font-mono border border-slate-800/80">
                    {selectedCase.decision_rationale}
                  </div>
                </div>
              )}

              {/* Adjudication Controls (if not resolved) */}
              {selectedCase.status !== 'RESOLVED' && selectedCase.status !== 'CLOSED' && (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 mt-4">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Investigative Decision & Resolution
                  </div>

                  {isReadOnly ? (
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
                      Auditor mode: Adjudication and quarantine mutations are prohibited for read-only auditors.
                    </div>
                  ) : (
                    <>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Final Decision</label>
                        <select
                          value={decision}
                          onChange={e => setDecision(e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-medium"
                        >
                          <option value="CONFIRMED_FRAUD">CONFIRMED FRAUD (Quarantine & Block Outflow)</option>
                          <option value="FALSE_POSITIVE">FALSE POSITIVE (Clear & Resume Normal Operations)</option>
                          <option value="PENDING_LAW_ENFORCEMENT">ESCALATE TO REGULATOR / LAW ENFORCEMENT</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Investigative Rationale</label>
                        <textarea
                          rows={2}
                          value={rationale}
                          onChange={e => setRationale(e.target.value)}
                          placeholder="State forensic justification (e.g. C2 IP match, credential stuffing correlation, money mule pattern)..."
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white"
                        />
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id="freeze"
                          checked={freezeAccount}
                          onChange={e => setFreezeAccount(e.target.checked)}
                          className="rounded bg-slate-800 border-slate-700 text-rose-500"
                        />
                        <label htmlFor="freeze" className="text-xs text-rose-400 font-semibold flex items-center gap-1.5">
                          <Lock className="w-3.5 h-3.5" />
                          Immediately quarantine & FREEZE affected beneficiary account
                        </label>
                      </div>

                      <button
                        onClick={handleResolve}
                        disabled={submitting}
                        className="w-full py-2 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white transition flex items-center justify-center gap-2"
                      >
                        {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                        Submit Case Decision & Execute Resolution
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-slate-500 text-xs">Select a fraud case to inspect details.</div>
          )}
        </div>
      </div>
    </div>
  );
};
