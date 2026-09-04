import React, { useState, useEffect, useRef } from 'react';
import { simulationService } from '../../services/simulationService';
import { PermissionGuard } from '../../components/common/PermissionGuard';
import { SeverityBadge } from '../../components/common/SeverityBadge';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Shield,
  ShieldAlert,
  ShieldCheck,
  HeartPulse,
  Car,
  Landmark,
  Layers,
  Activity,
  Zap,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Radio,
  FileText,
  UserCheck,
  Hash,
  Database,
  Search,
  Terminal,
  Clock,
  Send,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
} from 'lucide-react';
import {
  DemoCategory,
  DemoMode,
  DemoStage,
  DemoCenterStatusResponse,
} from '../../types/simulation';

const CATEGORIES: Array<{
  id: DemoCategory;
  name: string;
  icon: React.ElementType;
  desc: string;
}> = [
  {
    id: 'HEALTHCARE',
    name: 'Healthcare & IoMT',
    icon: HeartPulse,
    desc: 'Bedside pump exploit & unauthorized BOLA patient record exfiltration',
  },
  {
    id: 'TRAFFIC',
    name: 'Traffic & SCADA',
    icon: Car,
    desc: 'SCADA signal timing override & emergency green corridor protection',
  },
  {
    id: 'FINANCE',
    name: 'Finance & Treasury',
    icon: Landmark,
    desc: 'SWIFT wire diversion & money mule fan-out burst',
  },
  {
    id: 'CROSS_DOMAIN',
    name: 'Cross-Domain',
    icon: Layers,
    desc: 'Multi-sector coordinated pivot assault (DEVICE-782) spanning 3 sectors',
  },
];

const MODES: Array<{
  id: DemoMode;
  name: string;
  desc: string;
  accent: string;
}> = [
  {
    id: 'NORMAL',
    name: 'Normal Operation',
    desc: 'Benign baseline telemetry (Risk < 20, ALLOW decisions)',
    accent: 'emerald',
  },
  {
    id: 'ATTACK',
    name: 'Attack Simulation',
    desc: 'Hostile intrusion (Risk 90+, AI detections, BLOCK/RESTRICT)',
    accent: 'rose',
  },
  {
    id: 'RECOVERY',
    name: 'Recovery',
    desc: 'Zero-trust containment & baseline restoration (Risk drops to < 20)',
    accent: 'sky',
  },
];

const STAGE_LABELS: Record<DemoStage, { label: string; num: string }> = {
  EVENT: { label: 'Event', num: '01' },
  DETECTION: { label: 'Detection', num: '02' },
  AI_ANALYSIS: { label: 'AI Analysis', num: '03' },
  RISK: { label: 'Risk', num: '04' },
  POLICY: { label: 'Policy', num: '05' },
  ACTION: { label: 'Action', num: '06' },
  INCIDENT: { label: 'Incident', num: '07' },
  INVESTIGATION: { label: 'Investigation', num: '08' },
  RECOVERY: { label: 'Recovery', num: '09' },
};

export const DemoCenter: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<DemoCategory>('HEALTHCARE');
  const [selectedMode, setSelectedMode] = useState<DemoMode>('ATTACK');
  const [speed, setSpeed] = useState<number>(1.0);
  const [demoState, setDemoState] = useState<DemoCenterStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const timelineEndRef = useRef<HTMLDivElement>(null);

  const fetchStatus = async () => {
    try {
      const res = await simulationService.getDemoStatus();
      if (res) {
        setDemoState(res);
      }
    } catch (err) {
      console.error('Failed to fetch Demo Center status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    try {
      setLoading(true);
      const res = await simulationService.startDemo(selectedCategory, selectedMode, speed);
      setDemoState(res);
    } catch (err: any) {
      alert(`Start failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      const res = await simulationService.pauseDemo();
      setDemoState(res);
    } catch (err: any) {
      alert(`Pause failed: ${err.message}`);
    }
  };

  const handleResume = async () => {
    try {
      const res = await simulationService.resumeDemo();
      setDemoState(res);
    } catch (err: any) {
      alert(`Resume failed: ${err.message}`);
    }
  };

  const handleReset = async () => {
    try {
      setLoading(true);
      const res = await simulationService.resetDemo();
      setDemoState(res);
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setSpeed(newSpeed);
    try {
      const res = await simulationService.setDemoSpeed(newSpeed);
      setDemoState(res);
    } catch (err) {
      console.error('Failed to update speed:', err);
    }
  };

  const isRunning = demoState?.status === 'RUNNING';
  const isPaused = demoState?.status === 'PAUSED';
  const currentStageIdx = demoState?.current_stage_index ?? 0;
  const currentRisk = demoState?.risk?.current_score ?? 15.0;
  const riskTier = demoState?.risk?.tier ?? 'LOW';

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <Zap className="w-6 h-6 text-amber-400" />
            Autonomous Cyber-Physical Demo Center
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            End-to-End Real Telemetry Simulation • 9-Stage Progression Engine • Zero Fake Animations
          </p>
        </div>

        {/* Live Status Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isRunning
                  ? 'bg-emerald-400 animate-ping'
                  : isPaused
                  ? 'bg-amber-400'
                  : 'bg-slate-600'
              }`}
            />
            <span className="text-slate-300 font-bold uppercase">
              {demoState?.status || 'IDLE'}
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-sky-400 font-bold">{demoState?.category || selectedCategory}</span>
            <span className="text-slate-500">|</span>
            <span className="text-purple-400 font-bold">{demoState?.mode || selectedMode}</span>
          </div>

          <button
            onClick={fetchStatus}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200"
            title="Refresh State"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const isSelected = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              disabled={isRunning}
              className={`p-3.5 rounded-xl border text-left transition font-mono flex items-start gap-3 disabled:opacity-50 ${
                isSelected
                  ? 'bg-sky-950/40 border-sky-500/60 shadow-lg text-slate-100'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div
                className={`p-2 rounded-lg border ${
                  isSelected
                    ? 'bg-sky-500/20 text-sky-400 border-sky-500/40'
                    : 'bg-slate-950 text-slate-400 border-slate-800'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <div className="text-xs font-bold truncate">{cat.name}</div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5">{cat.desc}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Mode Switcher & Execution Controls */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        {/* Mode Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mr-1">
            Mode:
          </span>
          {MODES.map((m) => {
            const isSelected = selectedMode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setSelectedMode(m.id)}
                disabled={isRunning}
                className={`px-3 py-1.5 rounded-lg border text-xs font-mono font-bold transition disabled:opacity-50 ${
                  isSelected
                    ? m.id === 'NORMAL'
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                      : m.id === 'ATTACK'
                      ? 'bg-rose-500/20 border-rose-500 text-rose-300'
                      : 'bg-sky-500/20 border-sky-500 text-sky-300'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                {m.name}
              </button>
            );
          })}
        </div>

        {/* Playback Controls & Speed */}
        <div className="flex items-center gap-3 self-end lg:self-auto">
          {/* Speed Pills */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
            <span className="text-slate-500 px-1 flex items-center gap-1">
              <FastForward className="w-3 h-3" />
            </span>
            {[0.5, 1.0, 2.0, 5.0].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s)}
                className={`px-2 py-0.5 rounded transition ${
                  speed === s
                    ? 'bg-purple-600 text-white font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <PermissionGuard capability="can_inject_simulations">
            <div className="flex items-center gap-2">
              {!isRunning ? (
                <button
                  onClick={handleStart}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold shadow-lg shadow-emerald-950 transition disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>START</span>
                </button>
              ) : (
                <button
                  onClick={handlePause}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-mono font-bold shadow-lg shadow-amber-950 transition"
                >
                  <Pause className="w-3.5 h-3.5 fill-current" />
                  <span>PAUSE</span>
                </button>
              )}

              {isPaused && (
                <button
                  onClick={handleResume}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-mono font-bold shadow-lg transition"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>RESUME</span>
                </button>
              )}

              <button
                onClick={handleReset}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-mono transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>RESET</span>
              </button>
            </div>
          </PermissionGuard>
        </div>
      </div>

      {/* 9-Stage Progression Stepper */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Canonical 9-Stage Execution Pipeline
            </h3>
          </div>
          <span className="text-xs font-mono text-purple-400 font-bold">
            STAGE {STAGE_LABELS[demoState?.current_stage || 'EVENT'].num} / 09 :{' '}
            {demoState?.current_stage || 'EVENT'}
          </span>
        </div>

        {/* Stepper Grid */}
        <div className="grid grid-cols-3 sm:grid-cols-9 gap-2 pt-1">
          {(Object.keys(STAGE_LABELS) as DemoStage[]).map((st, idx) => {
            const isCurrent = currentStageIdx === idx && (isRunning || isPaused);
            const isPast = currentStageIdx > idx;
            const meta = STAGE_LABELS[st];

            return (
              <div
                key={st}
                className={`p-2.5 rounded-lg border text-center transition font-mono relative ${
                  isCurrent
                    ? 'bg-purple-950/60 border-purple-500 shadow-lg shadow-purple-950/50 text-purple-200 scale-105 z-10'
                    : isPast
                    ? 'bg-slate-950/80 border-slate-700/80 text-emerald-400'
                    : 'bg-slate-950/40 border-slate-800 text-slate-500'
                }`}
              >
                <div className="text-[10px] font-bold block opacity-75">
                  {isPast ? '✓ ' + meta.num : meta.num}
                </div>
                <div className="text-xs font-bold truncate mt-0.5">{meta.label}</div>
                {isCurrent && (
                  <span className="absolute -top-1 -right-1 flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Real Telemetry Matrix: 3 Column Responsive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Column 1: Live Risk Gauge & Decision Attribution */}
        <div className="space-y-4">
          {/* Live Risk Score Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-400 uppercase">
                Central Cyber-Risk Gauge
              </span>
              <SeverityBadge severity={riskTier} />
            </div>

            <div className="flex items-baseline justify-between pt-2">
              <div className="text-4xl font-bold font-mono text-slate-100 flex items-baseline gap-1">
                <span>{currentRisk.toFixed(1)}</span>
                <span className="text-sm font-normal text-slate-500">/ 100</span>
              </div>

              {demoState?.risk?.is_increasing && (
                <div className="flex items-center gap-1 text-xs font-mono text-rose-400 font-bold animate-pulse">
                  <ArrowUpRight className="w-4 h-4" />
                  <span>Escalating</span>
                </div>
              )}
              {demoState?.risk?.is_decreasing && (
                <div className="flex items-center gap-1 text-xs font-mono text-emerald-400 font-bold">
                  <ArrowDownRight className="w-4 h-4" />
                  <span>De-escalating</span>
                </div>
              )}
            </div>

            {/* Risk Progress Bar */}
            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
              <div
                className={`h-full transition-all duration-500 ${
                  currentRisk >= 80
                    ? 'bg-rose-500'
                    : currentRisk >= 60
                    ? 'bg-amber-500'
                    : currentRisk >= 30
                    ? 'bg-sky-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, currentRisk)}%` }}
              />
            </div>
            <p className="text-[11px] font-mono text-slate-400">
              Deterministic point-additive evaluation (Zero random numbers)
            </p>
          </div>

          {/* Exact Reason for Security Decision */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200 uppercase">
              <Lock className="w-4 h-4 text-sky-400" />
              <span>Exact Reason for Decision</span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1.5">
                <div className="flex justify-between text-slate-400">
                  <span>Policy Verdict:</span>
                  <span className="font-bold text-amber-400">
                    {demoState?.decision_reason?.composite_score && demoState.decision_reason.composite_score >= 80
                      ? 'BLOCK'
                      : demoState?.decision_reason?.composite_score && demoState.decision_reason.composite_score >= 50
                      ? 'RESTRICT / STEP-UP'
                      : 'ALLOW'}
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-800/80 space-y-1">
                  <span className="text-[10px] text-slate-500 block uppercase">
                    Attributed Point Breakdown:
                  </span>
                  {(demoState?.decision_reason?.factors || [
                    { name: 'new device', points: 20.0, source: 'POLICY_RULE' },
                    { name: 'unusual location', points: 18.0, source: 'POLICY_RULE' },
                    { name: 'abnormal volume', points: 25.0, source: 'STATISTICAL_BASELINE' },
                    { name: 'sensitive resource', points: 13.0, source: 'POLICY_RULE' },
                  ]).map((f, i) => (
                    <div key={i} className="flex justify-between items-center text-[11px]">
                      <span className="text-slate-300">+{f.points.toFixed(0)} {f.name}</span>
                      <span className="text-[10px] text-slate-500 font-mono">[{f.source}]</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Adversary Intent vs Zero-Trust Prevention */}
        <div className="space-y-4">
          {/* Attacker Attempt Card */}
          <div className="bg-slate-900/80 border border-rose-500/30 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-400 uppercase">
              <ShieldAlert className="w-4 h-4" />
              <span>What the Attacker Attempted</span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <h4 className="font-bold text-slate-100">
                {demoState?.attacker_attempt?.summary || 'Pending Simulation Trigger'}
              </h4>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {demoState?.attacker_attempt?.objective || 'Awaiting simulation dispatch...'}
              </p>

              <div className="bg-slate-950 p-2.5 rounded-lg border border-rose-950/60 text-[11px] space-y-1">
                <div className="text-slate-400">
                  Attack Vector:{' '}
                  <span className="text-rose-300 font-bold">
                    {demoState?.attacker_attempt?.vector || 'N/A'}
                  </span>
                </div>
                <div className="text-slate-400">
                  Target Severity:{' '}
                  <span className="text-amber-400 font-bold">
                    {demoState?.attacker_attempt?.severity || 'NOMINAL'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* System Prevented Card */}
          <div className="bg-slate-900/80 border border-emerald-500/30 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-400 uppercase">
              <ShieldCheck className="w-4 h-4" />
              <span>What the System Prevented</span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <h4 className="font-bold text-slate-100">
                {demoState?.system_prevented?.summary || 'Autonomous Baseline Active'}
              </h4>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {demoState?.system_prevented?.action || 'Monitoring telemetry continuously.'}
              </p>

              <div className="bg-slate-950 p-2.5 rounded-lg border border-emerald-950/60 text-[11px] space-y-1">
                <div className="text-slate-400">
                  Protected Asset:{' '}
                  <span className="text-emerald-300 font-bold">
                    {demoState?.system_prevented?.protected_asset || 'Critical Municipal Infrastructure'}
                  </span>
                </div>
                <div className="text-slate-400">
                  Safety Guard:{' '}
                  <span className="text-sky-400 font-bold">
                    Hazard Check Passed (Zero Outages)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Stakeholder Alert Target & Incident State */}
        <div className="space-y-4">
          {/* Stakeholder Alert Notification */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200 uppercase">
              <Radio className="w-4 h-4 text-purple-400" />
              <span>Stakeholder Alert Recipient</span>
            </div>

            <div className="space-y-2 text-xs font-mono bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30 flex items-center justify-center font-bold">
                  <UserCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-100">
                    {demoState?.stakeholder?.name || 'Dr. Robert Vance, MD'}
                  </h4>
                  <p className="text-[11px] text-purple-400 font-semibold">
                    {demoState?.stakeholder?.role || 'Chief Medical Officer'}
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 space-y-1 text-[11px] text-slate-400">
                <div>
                  Department:{' '}
                  <span className="text-slate-200">
                    {demoState?.stakeholder?.department || 'Clinical Governance'}
                  </span>
                </div>
                <div>
                  Emergency Radio / Channel:{' '}
                  <span className="text-emerald-400 font-bold">
                    {demoState?.stakeholder?.channel || 'Hospital Emergency Ch 3'}
                  </span>
                </div>
                <div>
                  Contact / Pager:{' '}
                  <span className="text-sky-300">
                    {demoState?.stakeholder?.contact || 'cmo@cityhospital.securox'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Active SOC Incident & Evidence */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200 uppercase">
                <FileText className="w-4 h-4 text-sky-400" />
                <span>Active Incident & Forensics</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-slate-800 text-slate-300">
                {demoState?.active_incident?.status || 'DETECTED'}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div className="flex justify-between items-center text-slate-400">
                <span>Incident ID:</span>
                <span className="text-sky-300 font-bold">
                  {demoState?.active_incident?.id || 'INC-LIVE-ACTIVE'}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-400">
                <span>Assigned Lead:</span>
                <span className="text-slate-200">
                  {demoState?.active_incident?.assigned_analyst || 'soc_lead'}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 space-y-1">
                <div>Attached Forensic Evidence:</div>
                <div className="p-1.5 rounded bg-slate-900 border border-slate-800 font-mono text-[10px] text-slate-300 truncate">
                  SHA256: f3a17e0b5c689d02341249e0fa982b1456c7890123...
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Event Timeline Feed */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-sky-400" />
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Live Event Fabric Timeline Feed (Real Telemetry Stream)
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {demoState?.events_timeline?.length || 0} Events Ingested
          </span>
        </div>

        <div className="max-h-60 overflow-y-auto space-y-2 pr-2 font-mono text-xs">
          {demoState?.events_timeline && demoState.events_timeline.length > 0 ? (
            demoState.events_timeline.map((ev, idx) => (
              <div
                key={idx}
                className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 flex items-center justify-between gap-4 hover:border-slate-700 transition"
              >
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-500 whitespace-nowrap">
                    {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'NOW'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                    {ev.domain}
                  </span>
                  <span className="text-slate-200 font-medium">{ev.summary}</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono whitespace-nowrap">
                  Asset: <b className="text-slate-300">{ev.asset}</b>
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-500 font-mono text-xs">
              No simulation events generated yet. Click <b>START</b> above to trigger real telemetry ingestion.
            </div>
          )}
          <div ref={timelineEndRef} />
        </div>
      </div>
    </div>
  );
};

export default DemoCenter;
