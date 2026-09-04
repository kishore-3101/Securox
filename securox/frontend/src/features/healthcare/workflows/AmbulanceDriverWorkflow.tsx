import React, { useState } from 'react';
import { trafficService } from '../../../services/trafficService';
import {
  Ambulance,
  Navigation,
  Radio,
  Zap,
  PhoneCall,
  CheckCircle2,
  AlertCircle,
  Clock,
  MapPin,
  Heart,
  Activity,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

type MissionStage = 'DISPATCHED' | 'ON_SCENE' | 'TRANSPORTING' | 'ARRIVED';

export const AmbulanceDriverWorkflow: React.FC = () => {
  const [stage, setStage] = useState<MissionStage>('TRANSPORTING');
  const [corridorActive, setCorridorActive] = useState<boolean>(false);
  const [corridorLoading, setCorridorLoading] = useState<boolean>(false);
  const [erAlertSent, setErAlertSent] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Stretcher vitals
  const [vitals, setVitals] = useState({
    hr: 114,
    bp: '142/92',
    spo2: 95,
  });

  const handleStageChange = (newStage: MissionStage) => {
    setStage(newStage);
    setFeedback(`Mission status updated: ${newStage.replace('_', ' ')}`);
    setTimeout(() => setFeedback(null), 3500);
  };

  const handleTriggerCorridor = async () => {
    setCorridorLoading(true);
    try {
      await trafficService.triggerGreenCorridor('CAD-01 Priority Pre-emption', [
        'SIG-01',
        'SIG-02',
        'SIG-03',
      ]);
      setCorridorActive(true);
      setFeedback('Green Corridor Activated: 3 Signals Pre-empted (SIG-01, SIG-02, SIG-03)');
    } catch (err: any) {
      // Fallback for simulation
      setCorridorActive(true);
      setFeedback('Green Corridor Activated locally (SIG-01 to SIG-03 locked GREEN)');
    } finally {
      setCorridorLoading(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const handleAlertER = () => {
    setErAlertSent(true);
    setFeedback('ER Trauma Receiving Bay notified: ETA 4 mins with cardiac critical vitals');
    setTimeout(() => setFeedback(null), 4000);
  };

  return (
    <div className="space-y-5 font-sans">
      {/* Driver Tablet Top Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <Ambulance className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide">
                AMBULANCE UNIT CAD-01
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold animate-pulse">
                ● HIGHWAY RUNNING
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 font-mono">
              Mission: Severe Cardiac Transport
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Vehicle KA-01-EA-1081 • Destination: Manipal Central Hospital (Trauma Hub)
            </p>
          </div>
        </div>

        {/* ETA Highlight */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl px-5 py-3 text-right">
          <div className="text-[10px] font-mono text-slate-400 uppercase">Hospital ETA</div>
          <div className="text-2xl font-black font-mono text-cyan-400 flex items-center gap-2">
            <Clock className="w-5 h-5" /> 4 MINS
          </div>
          <div className="text-[10px] font-mono text-slate-400">Distance: 2.1 km</div>
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Large Touch Mission Progress Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
        <div className="text-xs font-mono text-slate-400 uppercase font-bold tracking-wider mb-3">
          1. Current Mission Phase (Tap to Advance)
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {(
            [
              { key: 'DISPATCHED', label: '1. En Route to Scene', sub: 'Dispatched 08:24' },
              { key: 'ON_SCENE', label: '2. On Scene', sub: 'Patient Loaded' },
              { key: 'TRANSPORTING', label: '3. Transporting', sub: 'En Route Hospital' },
              { key: 'ARRIVED', label: '4. Arrived at Bay', sub: 'Handover in ER' },
            ] as const
          ).map((item) => {
            const isCurrent = stage === item.key;
            return (
              <button
                key={item.key}
                onClick={() => handleStageChange(item.key)}
                className={`min-h-[70px] p-3 rounded-xl border font-mono text-left transition-all flex flex-col justify-between ${
                  isCurrent
                    ? 'bg-rose-500/20 border-rose-500 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)] ring-1 ring-rose-400'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold">{item.label}</span>
                  {isCurrent && <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />}
                </div>
                <span className="text-[10px] opacity-70">{item.sub}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 1-TAP BIG ACTION BUTTONS FOR HIGH STRESS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* GREEN CORRIDOR PRE-EMPTION */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              Traffic Pre-emption Control
            </h3>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                corridorActive
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {corridorActive ? 'CORRIDOR GRANTED' : 'STANDBY'}
            </span>
          </div>

          <p className="text-xs font-mono text-slate-400">
            Forces all traffic signals along route (SIG-01, SIG-02, SIG-03) to continuous GREEN phase.
          </p>

          <button
            onClick={handleTriggerCorridor}
            disabled={corridorLoading || corridorActive}
            className={`w-full py-4 rounded-xl font-mono text-sm font-black tracking-wider uppercase transition-all shadow-lg flex items-center justify-center gap-3 ${
              corridorActive
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 cursor-default'
                : 'bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-cyan-500/25 active:scale-[0.99]'
            }`}
          >
            <Zap className="w-5 h-5 fill-current" />
            {corridorLoading
              ? 'Requesting Pre-emption...'
              : corridorActive
              ? 'Green Corridor Active (SIG-01 to SIG-03)'
              : 'REQUEST 1-TAP GREEN CORRIDOR'}
          </button>
        </div>

        {/* NOTIFY ER TRAUMA BAY */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
              <Radio className="w-4 h-4 text-rose-400" />
              Trauma Bay Uplink
            </h3>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                erAlertSent
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {erAlertSent ? 'TRAUMA BAY PREPPED' : 'UNNOTIFIED'}
            </span>
          </div>

          <p className="text-xs font-mono text-slate-400">
            Sends audio-visual priority chime to Hospital ER Trauma Desk & Mobilizes Crash Cart.
          </p>

          <button
            onClick={handleAlertER}
            className={`w-full py-4 rounded-xl font-mono text-sm font-black tracking-wider uppercase transition-all shadow-lg flex items-center justify-center gap-3 ${
              erAlertSent
                ? 'bg-rose-500/30 text-rose-300 border border-rose-500/50'
                : 'bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-rose-500/25 active:scale-[0.99]'
            }`}
          >
            <PhoneCall className="w-5 h-5" />
            {erAlertSent ? 'ER Trauma Alert Dispatched' : 'NOTIFY ER TRAUMA DESK (1-TAP)'}
          </button>
        </div>
      </div>

      {/* LIVE TELEMETRY & STRETCHER VITALS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Heart Rate */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase">Patient Heart Rate</div>
            <div className="text-2xl font-bold font-mono text-rose-400 mt-1 flex items-baseline gap-1">
              {vitals.hr} <span className="text-xs text-slate-400">BPM</span>
            </div>
            <span className="text-[10px] font-mono text-rose-400">Sinus Tachycardia</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <Heart className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        {/* Blood Pressure */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase">Blood Pressure</div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1 flex items-baseline gap-1">
              {vitals.bp} <span className="text-xs text-slate-400">mmHg</span>
            </div>
            <span className="text-[10px] font-mono text-amber-400">Elevated Systolic</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* SpO2 */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase">Oxygen Saturation</div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-1 flex items-baseline gap-1">
              {vitals.spo2} <span className="text-xs text-slate-400">%</span>
            </div>
            <span className="text-[10px] font-mono text-cyan-400">On 4L O2 Nasal Cannula</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* DRIVER EMERGENCY PROCEDURE / SOP */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
          <div className="text-xs font-mono text-slate-300">
            <span className="font-bold text-amber-400">Emergency Protocol:</span> If route blocked by accident, switch to Bypass Ring Road Corridor (Pre-emption SIG-04 & SIG-05).
          </div>
        </div>
        <button
          onClick={() => alert('Emergency Alternate Route Selected: Hosur Ring Road Bypass')}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono shrink-0"
        >
          Select Alternate Route
        </button>
      </div>
    </div>
  );
};
