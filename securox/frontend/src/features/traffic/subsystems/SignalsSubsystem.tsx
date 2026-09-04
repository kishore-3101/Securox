import React, { useState } from 'react';
import { TrafficSignal, SignalSafetyOverrideRequest, SignalSafetyOverrideResponse } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import { Radio, AlertTriangle, ShieldCheck, CheckCircle2, Lock, RefreshCw } from 'lucide-react';

interface Props {
  signals: TrafficSignal[];
  onRefresh: () => void;
}

export const SignalsSubsystem: React.FC<Props> = ({ signals, onRefresh }) => {
  const [selectedSignal, setSelectedSignal] = useState<TrafficSignal | null>(null);
  const [targetState, setTargetState] = useState<'GREEN' | 'YELLOW' | 'RED'>('GREEN');
  const [contextType, setContextType] = useState<SignalSafetyOverrideRequest['context_type']>('EMERGENCY_PREEMPTION');
  const [reason, setReason] = useState<string>('');
  const [contextRef, setContextRef] = useState<string>('');
  const [overridePlan, setOverridePlan] = useState<SignalSafetyOverrideResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Conflicting intersection pairs
  const CONFLICT_PAIRS: Record<string, string> = {
    'SIG-01': 'SIG-02',
    'SIG-02': 'SIG-01',
    'SIG-03': 'SIG-05',
    'SIG-05': 'SIG-03',
    'SIG-04': 'SIG-06',
    'SIG-06': 'SIG-04',
  };

  const handleExecuteSafetyOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSignal) return;
    if (reason.trim().length < 5) {
      setErrorMsg('Mandatory operational justification (min 5 characters) required.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await trafficService.safetyOverrideSignal(selectedSignal.id, {
        target_state: targetState,
        mode: 'MANUAL_OVERRIDE',
        reason,
        context_type: contextType,
        context_ref: contextRef || undefined,
      });
      setOverridePlan(res);
      onRefresh();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Signal override policy violation';
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            Adaptive Signal Grid & Safety Conflict Matrix
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Zero-Trust SCADA Interlocks • Multi-Phase Safety Clearance Intervals (Yellow → All-Red → Green)
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Signals
        </button>
      </div>

      {/* Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {signals.map((sig) => {
          const conflictingSignalId = CONFLICT_PAIRS[sig.id];
          const conflictingSig = signals.find((s) => s.id === conflictingSignalId);
          const currentState = sig.current_state || sig.current_phase || 'RED';

          return (
            <div
              key={sig.id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold font-mono text-cyan-400">{sig.id}</span>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                      currentState === 'GREEN'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : currentState === 'YELLOW'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                        : 'bg-rose-950 text-rose-400 border border-rose-800'
                    }`}
                  >
                    {currentState} PHASE
                  </span>
                </div>
                <h4 className="text-sm font-bold font-mono text-slate-200">{sig.intersection || sig.name || 'Junction'}</h4>
                <div className="text-[11px] font-mono text-slate-400 mt-1">Zone: {sig.zone || 'Central'} | Mode: {sig.mode}</div>

                {/* Conflict Interlock Info */}
                <div className="mt-3 p-2.5 rounded bg-slate-950/70 border border-slate-800/80 text-[11px] font-mono">
                  <div className="text-slate-400 flex items-center justify-between">
                    <span>Conflicting Approach:</span>
                    <span className="text-slate-300 font-bold">{conflictingSignalId || 'None'}</span>
                  </div>
                  {conflictingSig && (
                    <div className="text-slate-500 mt-0.5 text-[10px]">
                      Current Opposing Phase: <span className="text-amber-400">{conflictingSig.current_state || conflictingSig.current_phase}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button: Opens Multi-Factor Override Modal */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500">
                  Cycle: {sig.cycle_time_sec || 90}s
                </span>
                <button
                  onClick={() => {
                    setSelectedSignal(sig);
                    setOverridePlan(null);
                    setErrorMsg(null);
                    setReason('');
                  }}
                  className="px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-700/60 text-xs font-mono font-bold text-cyan-300 hover:text-cyan-200 transition flex items-center gap-1"
                >
                  <Lock className="w-3 h-3" /> Safety Override
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Multi-Factor Safety Override Modal */}
      {selectedSignal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                Multi-Factor Safety Override: {selectedSignal.id}
              </h4>
              <button
                onClick={() => setSelectedSignal(null)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-slate-400 leading-relaxed">
              Traffic signal override commands require multi-tier authorization, mandatory operational context, risk score inspection, and automatic conflict matrix clearance.
            </p>

            {errorMsg && (
              <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {overridePlan ? (
              <div className="space-y-3 p-4 bg-slate-950 rounded-lg border border-emerald-800/80 text-xs animate-fadeIn">
                <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  SAFETY CLEARANCE PLAN COMMITTED (Audit ID: {overridePlan.audit_id})
                </div>
                <div className="text-slate-300">
                  Target State: <span className="text-emerald-300 font-bold">{overridePlan.target_state}</span> | Conflict Detected: {overridePlan.conflict_detected ? 'YES (Opposing Green Cleared)' : 'NO'}
                </div>
                <div className="space-y-1.5 mt-2">
                  {overridePlan.safety_transition_plan?.map((st) => (
                    <div key={st.stage} className="p-2 bg-slate-900 rounded border border-slate-800 text-[11px]">
                      Stage {st.stage}: <span className="text-cyan-400 font-bold">{st.phase}</span> ({st.duration_seconds}s) — {st.action}
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="w-full mt-3 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold"
                >
                  Close Console
                </button>
              </div>
            ) : (
              <form onSubmit={handleExecuteSafetyOverride} className="space-y-3">
                <div>
                  <label className="block text-slate-400 mb-1">Target Phase State</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['GREEN', 'YELLOW', 'RED'] as const).map((st) => (
                      <button
                        type="button"
                        key={st}
                        onClick={() => setTargetState(st)}
                        className={`py-2 rounded border font-bold transition ${
                          targetState === st
                            ? st === 'GREEN'
                              ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                              : st === 'YELLOW'
                              ? 'bg-amber-950 border-amber-500 text-amber-400'
                              : 'bg-rose-950 border-rose-500 text-rose-400'
                            : 'bg-slate-950 border-slate-800 text-slate-400'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Operational Context Type *</label>
                  <select
                    value={contextType}
                    onChange={(e: any) => setContextType(e.target.value)}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="EMERGENCY_PREEMPTION">EMERGENCY_PREEMPTION (Ambulance / CAD Corridor)</option>
                    <option value="INCIDENT_CLEARANCE">INCIDENT_CLEARANCE (Police On-Scene Command)</option>
                    <option value="CONGESTION_MITIGATION">CONGESTION_MITIGATION (Arterial Flow Reliever)</option>
                    <option value="SCHEDULED_MAINTENANCE">SCHEDULED_MAINTENANCE (Technician Lockout)</option>
                    <option value="MANUAL_OVERRIDE">MANUAL_OVERRIDE (Supervisory Intervention)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Linked CAD / Incident / Ticket Reference ID (Optional)</label>
                  <input
                    type="text"
                    value={contextRef}
                    onChange={(e) => setContextRef(e.target.value)}
                    placeholder="e.g. DISP-AMB-902, INC-TRF-01, TKT-MAINT-44"
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Mandatory Justification (min 5 characters) *</label>
                  <textarea
                    rows={2}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide verifiable reason for signal phase override..."
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSelectedSignal(null)}
                    className="px-4 py-2 rounded bg-slate-800 text-slate-300 font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold"
                  >
                    {submitting ? 'Evaluating SCADA Rules...' : 'Submit Override Request'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
