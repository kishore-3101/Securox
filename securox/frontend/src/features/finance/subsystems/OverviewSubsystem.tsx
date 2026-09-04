import React from 'react';
import {
  Landmark,
  ShieldAlert,
  AlertTriangle,
  TrendingDown,
  Activity,
  DollarSign,
  Layers,
  Network
} from 'lucide-react';
import { CyberVarMetrics } from '../../../types/finance';

interface OverviewSubsystemProps {
  overviewData: any;
  cyberVar: CyberVarMetrics | null;
  onNavigateTab: (tab: string) => void;
}

export const OverviewSubsystem: React.FC<OverviewSubsystemProps> = ({
  overviewData,
  cyberVar,
  onNavigateTab
}) => {
  return (
    <div className="space-y-6">
      {/* Top Banner with Model Attribution Disclosure */}
      <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-500/20 text-blue-400">
            <Landmark className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              State Apex Municipal Banking & Financial Cyber-Physical Operations
            </h3>
            <p className="text-xs text-slate-400">
              Core banking fabric with pre-settlement AI fraud mitigation and AML graph contagion scoring.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            LIVE INFERENCE
          </span>
          <span className="text-xs px-2.5 py-1 rounded font-mono font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            XGBoost + Isolation Forest
          </span>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Portfolio Volume</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            ₹{(overviewData?.total_portfolio_balance_inr ?? 139450000).toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-slate-400 mt-1">Across 3 Operating Metro Branches</div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">1-Day Cyber-VaR (95%)</span>
            <TrendingDown className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            ₹{(cyberVar?.cyber_var_95_1day_inr ?? 2280000).toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-slate-400 mt-1">Parametric Value-at-Risk Engine</div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Open Fraud Cases</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {overviewData?.open_fraud_cases_count ?? 2}
          </div>
          <div className="text-xs text-slate-400 mt-1">Pending Analyst Investigation</div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Quarantined Accounts</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-500 font-mono">
            {overviewData?.frozen_accounts_count ?? 1}
          </div>
          <div className="text-xs text-slate-400 mt-1">FROZEN pending SAR resolution</div>
        </div>
      </div>

      {/* Quick Action Navigation Panels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => onNavigateTab('transactions')}
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-blue-500/50 cursor-pointer transition group"
        >
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-5 h-5 text-blue-400 group-hover:scale-110 transition" />
            <h4 className="text-sm font-semibold text-white">Live Transaction Pipeline</h4>
          </div>
          <p className="text-xs text-slate-400">
            Submit transfers through pre-settlement XGBoost & Isolation Forest risk evaluation.
          </p>
        </div>

        <div
          onClick={() => onNavigateTab('cases')}
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-amber-500/50 cursor-pointer transition group"
        >
          <div className="flex items-center gap-3 mb-2">
            <ShieldAlert className="w-5 h-5 text-amber-400 group-hover:scale-110 transition" />
            <h4 className="text-sm font-semibold text-white">Fraud Case Investigation</h4>
          </div>
          <p className="text-xs text-slate-400">
            Investigate suspicious transactions, adjudicate decisions, and quarantine accounts.
          </p>
        </div>

        <div
          onClick={() => onNavigateTab('aml')}
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/50 cursor-pointer transition group"
        >
          <div className="flex items-center gap-3 mb-2">
            <Network className="w-5 h-5 text-purple-400 group-hover:scale-110 transition" />
            <h4 className="text-sm font-semibold text-white">AML Graph & Mule Contagion</h4>
          </div>
          <p className="text-xs text-slate-400">
            Run AMLSim graph topology contagion, calculate mule probability, and file regulatory SARs.
          </p>
        </div>
      </div>
    </div>
  );
};
