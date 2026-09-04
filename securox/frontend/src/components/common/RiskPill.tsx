import React, { useState } from 'react';
import { useCityRisk } from '../../hooks/useCityRisk';
import { Activity, X, Info } from 'lucide-react';

export const RiskPill: React.FC = () => {
  const { score, tier, details } = useCityRisk();
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold border transition-all hover:scale-105 ${tier.bg} ${tier.border} ${tier.color}`}
        title="Click to view Composite City Risk Formula Breakdown"
      >
        <Activity className="w-3.5 h-3.5 animate-pulse" />
        <span>CITY RISK: {score}/100</span>
        <span className="text-[10px] px-1 py-0.2 rounded bg-black/40 border border-white/10 uppercase">
          {tier.label}
        </span>
      </button>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-100"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-6 h-6 text-sky-400" />
              <h3 className="text-lg font-bold text-slate-100">Smart City Cyber Risk Formula</h3>
            </div>

            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              The composite city risk index is dynamically calculated in real time using multi-sector
              telemetry, IoMT sensor flow anomalies, SCADA actuator health, and fintech transaction velocities.
            </p>

            <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-sky-300 border border-slate-800 mb-4">
              <code>
                City Risk = (0.35 × Healthcare) + (0.30 × Traffic STIG) + (0.25 × Finance AML) + (0.10 × SCADA Water/Grid)
              </code>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Current Composite Index:</span>
                <span className="font-bold text-sky-400 font-mono">{score} / 100</span>
              </div>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Healthcare Weight (IoMT + EHR):</span>
                <span className="font-mono text-slate-200">35%</span>
              </div>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Traffic & Transit Weight:</span>
                <span className="font-mono text-slate-200">30%</span>
              </div>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Financial Treasury & AML:</span>
                <span className="font-mono text-slate-200">25%</span>
              </div>
              <div className="flex justify-between text-xs py-1">
                <span className="text-slate-400">Grid / Utilities Infrastructure:</span>
                <span className="font-mono text-slate-200">10%</span>
              </div>
            </div>

            <button
              onClick={() => setModalOpen(false)}
              className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white font-mono text-xs rounded-lg transition"
            >
              Close Breakdown
            </button>
          </div>
        </div>
      )}
    </>
  );
};
