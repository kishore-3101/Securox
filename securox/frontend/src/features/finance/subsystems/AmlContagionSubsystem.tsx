import React, { useState } from 'react';
import { FinanceAmlFinding, FinancePersonaRole } from '../../../types/finance';
import { Network, FileCheck, AlertTriangle, RefreshCw, Send, CheckCircle2 } from 'lucide-react';

interface AmlContagionSubsystemProps {
  findings: FinanceAmlFinding[];
  activePersonaRole: FinancePersonaRole;
  isReadOnly: boolean;
  onAnalyzeAccount: (accountId: string) => Promise<any>;
  onFileSar: (findingId: string, ref: string) => Promise<any>;
  onRefresh: () => void;
}

export const AmlContagionSubsystem: React.FC<AmlContagionSubsystemProps> = ({
  findings,
  activePersonaRole,
  isReadOnly,
  onAnalyzeAccount,
  onFileSar,
  onRefresh
}) => {
  const [targetAccount, setTargetAccount] = useState('ACC-7006');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [filingFindingId, setFilingFindingId] = useState<string | null>(null);
  const [sarReference, setSarReference] = useState('');

  const handleAnalyze = async () => {
    if (!targetAccount) return;
    setAnalyzing(true);
    try {
      const res = await onAnalyzeAccount(targetAccount);
      setAnalysisResult(res);
      onRefresh();
    } catch (err: any) {
      alert(`AML analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileSarSubmit = async (findingId: string) => {
    if (!sarReference) {
      alert('Please enter a SAR filing reference.');
      return;
    }
    try {
      await onFileSar(findingId, sarReference);
      alert(`SAR report filed successfully: ${sarReference}`);
      setFilingFindingId(null);
      setSarReference('');
      onRefresh();
    } catch (err: any) {
      alert(`SAR filing error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controller: Run Graph Contagion Analysis */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Network className="w-4 h-4 text-purple-400" />
            AMLSim Graph Contagion & Mule Detection Engine
          </h3>
          <p className="text-xs text-slate-400">
            Analyzes fan-in / fan-out graph degree, circular topologies, and structuring smurfing patterns.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={targetAccount}
            onChange={e => setTargetAccount(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
            placeholder="Account ID (e.g. ACC-7006)"
          />
          <button
            onClick={handleAnalyze}
            disabled={analyzing || isReadOnly}
            className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center gap-2"
          >
            {analyzing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Network className="w-3.5 h-3.5" />}
            Analyze Topology
          </button>
        </div>
      </div>

      {/* Analysis Result Banner */}
      {analysisResult && (
        <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-500/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Topology Finding</span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
              {analysisResult.model_attribution}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div>
              <span className="text-slate-400">Mule Probability:</span>{' '}
              <span className="font-bold text-rose-400 font-mono">
                {(analysisResult.mule_probability * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400">Pattern:</span>{' '}
              <span className="font-bold text-white font-mono">{analysisResult.finding.finding_type}</span>
            </div>
            <div>
              <span className="text-slate-400">Connected Nodes:</span>{' '}
              <span className="font-bold text-white font-mono">
                {analysisResult.topology.connected_counterparties.length} Counterparties
              </span>
            </div>
          </div>
        </div>
      )}

      {/* AML Findings List */}
      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white">Persisted AML Findings & Regulatory SAR Register</h3>
          <button onClick={onRefresh} className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 border-b border-slate-800">
              <tr>
                <th className="pb-2">Finding ID</th>
                <th className="pb-2">Primary Account</th>
                <th className="pb-2">Pattern Type</th>
                <th className="pb-2 text-right">Mule Probability</th>
                <th className="pb-2 text-center">SAR Status</th>
                <th className="pb-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {findings.map(f => {
                const isHighMule = f.mule_probability >= 0.70;
                const isSarFiled = f.sar_filed === 1;

                return (
                  <tr key={f.id} className="hover:bg-slate-800/30">
                    <td className="py-3 text-white">{f.id}</td>
                    <td className="py-3 text-slate-300 font-bold">{f.primary_account}</td>
                    <td className="py-3 text-slate-300">{f.finding_type}</td>
                    <td className="py-3 text-right">
                      <span className={`font-bold ${isHighMule ? 'text-rose-400' : 'text-amber-400'}`}>
                        {(f.mule_probability * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 text-center">
                      {isSarFiled ? (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold">
                          SAR FILED ({f.sar_reference})
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          PENDING FILING
                        </span>
                      )}
                    </td>
                    <td className="py-3 text-right">
                      {!isSarFiled && !isReadOnly && (
                        <button
                          onClick={() => {
                            setFilingFindingId(f.id);
                            setSarReference(`SAR-2026-REG-${Math.floor(1000 + Math.random() * 9000)}`);
                          }}
                          className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-[11px] font-semibold text-white transition flex items-center gap-1.5 ml-auto"
                        >
                          <FileCheck className="w-3.5 h-3.5" />
                          File SAR
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* SAR Filing Modal */}
      {filingFindingId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl max-w-md w-full space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-indigo-400" />
              File Suspicious Activity Report (SAR)
            </h4>
            <p className="text-xs text-slate-400">
              Submit regulatory filing to FIU-IND / RBI for finding{' '}
              <span className="font-mono text-white">{filingFindingId}</span>.
            </p>
            <div>
              <label className="block text-xs text-slate-400 mb-1">SAR Regulatory Reference Number</label>
              <input
                type="text"
                value={sarReference}
                onChange={e => setSarReference(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-white font-mono"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setFilingFindingId(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleFileSarSubmit(filingFindingId)}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition"
              >
                Confirm Regulatory SAR Submission
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
