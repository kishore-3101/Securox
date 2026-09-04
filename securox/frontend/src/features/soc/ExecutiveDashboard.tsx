import React from 'react';
import { useCityRisk } from '../../hooks/useCityRisk';
import { KpiCard } from '../../components/common/KpiCard';
import {
  BarChart3,
  ShieldCheck,
  DollarSign,
  TrendingDown,
  Building,
  Award,
  Globe,
  FileDown,
} from 'lucide-react';

export const ExecutiveDashboard: React.FC = () => {
  const { score, tier } = useCityRisk();

  const sectorBreakdowns = [
    { name: 'Healthcare & Clinical Defense', score: 68, exposureMillion: 1.45, weight: '35%', color: 'bg-rose-500' },
    { name: 'Smart Traffic & Transit Corridor', score: 32, exposureMillion: 0.82, weight: '30%', color: 'bg-cyan-500' },
    { name: 'Fintech, AML & Municipal Treasury', score: 28, exposureMillion: 2.10, weight: '25%', color: 'bg-amber-500' },
    { name: 'SCADA Water & Power Substation', score: 45, exposureMillion: 0.95, weight: '10%', color: 'bg-emerald-500' },
  ];

  const totalExposure = sectorBreakdowns.reduce((acc, s) => acc + s.exposureMillion, 0);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-sky-400" />
            Executive Cyber Intelligence & Resilience
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Board-Level Cyber Risk Quantification, Financial Value-at-Risk & UN SDG Alignment
          </p>
        </div>

        <button
          onClick={() => alert('Executive Intelligence PDF report generated and queued for download.')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-mono text-xs transition"
        >
          <FileDown className="w-4 h-4" />
          <span>Export Board Briefing</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Composite City Risk Index"
          value={`${score} / 100`}
          subtitle={`Current Status: ${tier.label}`}
          icon={ShieldCheck}
          accentColor="blue"
        />
        <KpiCard
          title="Value-at-Risk (VaR 95%)"
          value={`$${totalExposure.toFixed(2)}M`}
          subtitle="Estimated 24-hr max loss"
          icon={DollarSign}
          accentColor="amber"
        />
        <KpiCard
          title="Incident Containment MTTR"
          value="4.2 mins"
          subtitle="Down 28% with autonomous AI"
          icon={TrendingDown}
          accentColor="green"
        />
        <KpiCard
          title="Smart City Uptime"
          value="99.98%"
          subtitle="Zero cascading blackout"
          icon={Building}
          accentColor="purple"
        />
      </div>

      {/* Multi-Sector Cyber Risk Distribution */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur">
        <h3 className="text-sm font-bold font-mono text-slate-200 uppercase tracking-wider mb-4">
          Multi-Sector Cyber Risk & Financial Loss Exposure Breakdown
        </h3>

        <div className="space-y-4">
          {sectorBreakdowns.map((sec) => (
            <div key={sec.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300 font-semibold">{sec.name}</span>
                <div className="flex items-center gap-4 text-slate-400">
                  <span>Weight: {sec.weight}</span>
                  <span>Exposure: <b className="text-slate-200">${sec.exposureMillion.toFixed(2)}M</b></span>
                  <span className="font-bold text-sky-400">Score: {sec.score}/100</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${sec.color} transition-all duration-500`}
                  style={{ width: `${sec.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* UN SDG Sustainability & Governance Scorecard */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur flex gap-4 items-start">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
            <Award className="w-8 h-8" />
          </div>
          <div>
            <h4 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              UN SDG Goal 9: Industry, Innovation & Infrastructure
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Securox ensures resilient digital infrastructure through autonomous threat containment, zero-trust SCADA network microsegmentation, and quantum-resistant cryptographic envelope protection.
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs font-mono text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Resilience Compliance: 96.4% (Pass)</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur flex gap-4 items-start">
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 shrink-0">
            <Globe className="w-8 h-8" />
          </div>
          <div>
            <h4 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              UN SDG Goal 11: Sustainable Cities & Communities
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Protects public health, emergency dispatch corridors, and citizen data confidentiality against hostile ransomware and cyber-physical systemic cascading failure.
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs font-mono text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Citizen Safety Assurance: 98.1% (High)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
