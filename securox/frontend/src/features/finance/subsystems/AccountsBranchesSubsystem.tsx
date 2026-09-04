import React from 'react';
import { FinanceBranch, FinanceAccount, FinancePersonaRole } from '../../../types/finance';
import { Landmark, Building2, User, Lock, CheckCircle2, AlertOctagon } from 'lucide-react';

interface AccountsBranchesSubsystemProps {
  branches: FinanceBranch[];
  accounts: FinanceAccount[];
  activePersonaRole: FinancePersonaRole;
  selectedBranchId: string;
  onSelectBranchId: (id: string) => void;
}

export const AccountsBranchesSubsystem: React.FC<AccountsBranchesSubsystemProps> = ({
  branches,
  accounts,
  activePersonaRole,
  selectedBranchId,
  onSelectBranchId
}) => {
  const filteredAccounts = selectedBranchId === 'ALL'
    ? accounts
    : accounts.filter(a => a.branch_id === selectedBranchId);

  return (
    <div className="space-y-6">
      {/* Branch Selector (if staff / management) */}
      {activePersonaRole !== 'customer' && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <Building2 className="w-4 h-4 text-blue-400" />
            Filter by Branch Scope:
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onSelectBranchId('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedBranchId === 'ALL'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              All Branches ({branches.length})
            </button>
            {branches.map(b => (
              <button
                key={b.id}
                onClick={() => onSelectBranchId(b.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  selectedBranchId === b.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {b.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Account Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAccounts.map(acc => {
          const isFrozen = acc.status === 'FROZEN';
          const isCritical = acc.risk_score >= 80;

          return (
            <div
              key={acc.id}
              className={`p-4 rounded-xl border transition ${
                isFrozen
                  ? 'bg-rose-950/20 border-rose-500/40'
                  : isCritical
                  ? 'bg-amber-950/20 border-amber-500/40'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg ${isFrozen ? 'bg-rose-500/20 text-rose-400' : 'bg-blue-500/20 text-blue-400'}`}>
                    {isFrozen ? <Lock className="w-4 h-4" /> : <Landmark className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">{acc.account_type} ACCOUNT</div>
                    <div className="text-sm font-bold text-white font-mono">{acc.account_number}</div>
                  </div>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
                    isFrozen
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}
                >
                  {acc.status}
                </span>
              </div>

              <div className="text-xs text-slate-300 mb-2">
                <span className="text-slate-500">Holder:</span> {acc.customer_name || 'Verified Retail Customer'}
              </div>

              <div className="flex items-baseline justify-between pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Available Balance</div>
                  <div className="text-base font-bold text-white font-mono">
                    ₹{acc.balance.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">Risk Score</div>
                  <div
                    className={`text-xs font-mono font-bold ${
                      acc.risk_score >= 80 ? 'text-rose-400' : acc.risk_score >= 50 ? 'text-amber-400' : 'text-emerald-400'
                    }`}
                  >
                    {acc.risk_score.toFixed(1)} / 100
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
