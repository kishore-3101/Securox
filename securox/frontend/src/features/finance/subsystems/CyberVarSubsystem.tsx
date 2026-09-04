import React, { useState } from 'react';
import { CyberVarMetrics } from '../../../types/finance';
import { TrendingDown, Sliders, ShieldCheck, AlertTriangle, RefreshCw } from 'lucide-react';

interface CyberVarSubsystemProps {
  cyberVar: CyberVarMetrics | null;
  onRefreshMultiplier: (multiplier: number) => void;
}

export const CyberVarSubsystem: React.FC<CyberVarSubsystemProps> = ({
  cyberVar,
  onRefreshMultiplier
}) => {
  const [multiplier, setMultiplier] = useState(1.0);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setMultiplier(val);
    onRefreshMultiplier(val);
  };

  const isSimulation = cyberVar?.model_attribution === 'SIMULATION';

  return (
    <div className="space-y-6">
      {/* Attribution Disclosure Header */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-rose-400" />
            Parametric & Monte Carlo Cyber-VaR Exposure Engine
          </h3>
          <p className="text-xs text-slate-400">
            Formula: Expected Exposure = Risk Probability × Financial Exposure × Impact Factor × Propagation Blast
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs px-3 py-1 rounded font-mono font-bold border ${
              isSimulation
                ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            }`}
          >
            {cyberVar?.model_attribution ?? 'LIVE INFERENCE'}
          </span>
        </div>
      </div>

      {/* Interactive Simulation Stress Multiplier Slider */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-300 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            Stress Scenario Multiplier (Simulation Engine)
          </span>
          <span className="font-mono font-bold text-blue-400">{multiplier.toFixed(1)}x Shock Multiplier</span>
        </div>
        <input
          type="range"
          min="1.0"
          max="3.5"
          step="0.1"
          value={multiplier}
          onChange={handleSliderChange}
          className="w-full accent-blue-500 cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>1.0x (Live Baseline)</span>
          <span>2.0x (Coordinated Threat Wave)</span>
          <span>3.5x (Systemic APT Core Compromise)</span>
        </div>
      </div>

      {/* Cyber-VaR KPI Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">95% 1-Day Cyber-VaR</div>
          <div className="text-2xl font-bold text-amber-400">
            ₹{(cyberVar?.cyber_var_95_1day_inr ?? 2280000).toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">95% confidence max daily expected loss</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">99% 1-Day Cyber-VaR</div>
          <div className="text-2xl font-bold text-rose-400">
            ₹{(cyberVar?.cyber_var_99_1day_inr ?? 3240000).toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Tail-risk VaR under 99% confidence</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">Expected Shortfall (CVaR)</div>
          <div className="text-2xl font-bold text-purple-400">
            ₹{(cyberVar?.expected_shortfall_cvar_inr ?? 3820000).toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Average loss in the worst 1% tail</div>
        </div>
      </div>

      {/* Stress Scenarios Table */}
      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Simulated Cyber Attack Stress Test Scenarios
        </h4>
        <div className="space-y-2">
          {cyberVar?.stress_scenarios.map((scen, idx) => (
            <div key={idx} className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-white">{scen.name}</div>
                <div className="text-[10px] text-slate-400">Annualized Probability: {(scen.probability * 100).toFixed(1)}%</div>
              </div>
              <div className="text-right font-mono">
                <div className="text-xs font-bold text-rose-400">
                  ₹{scen.projected_loss_inr.toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-slate-500">{scen.status}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
