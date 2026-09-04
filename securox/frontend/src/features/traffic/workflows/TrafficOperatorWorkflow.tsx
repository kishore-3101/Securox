import React, { useState } from 'react';
import { trafficService } from '../../../services/trafficService';
import { TrafficSignal, CameraFeed } from '../../../types/traffic';
import {
  Car,
  Video,
  Sliders,
  Zap,
  CheckCircle2,
  AlertTriangle,
  MapPin,
  RefreshCw,
  Radio,
  Clock,
  ShieldCheck,
} from 'lucide-react';

export const TrafficOperatorWorkflow: React.FC = () => {
  const [signals, setSignals] = useState<TrafficSignal[]>([
    { id: 'SIG-01', name: 'MG Road Junction', current_phase: 'GREEN', phase_duration_seconds: 60, time_in_current_phase: 24, mode: 'AUTO', is_active: true },
    { id: 'SIG-02', name: 'Hebbal Flyover North', current_phase: 'RED', phase_duration_seconds: 45, time_in_current_phase: 15, mode: 'AUTO', is_active: true },
    { id: 'SIG-03', name: 'Hospital Emergency Gate', current_phase: 'GREEN', phase_duration_seconds: 60, time_in_current_phase: 50, mode: 'EMERGENCY_CORRIDOR', is_active: true },
    { id: 'SIG-04', name: 'Financial District Outer', current_phase: 'YELLOW', phase_duration_seconds: 5, time_in_current_phase: 2, mode: 'AUTO', is_active: true },
    { id: 'SIG-05', name: 'Airport Express Toll', current_phase: 'GREEN', phase_duration_seconds: 60, time_in_current_phase: 12, mode: 'AUTO', is_active: true },
    { id: 'SIG-06', name: 'Central SCADA Hub', current_phase: 'RED', phase_duration_seconds: 60, time_in_current_phase: 38, mode: 'AUTO', is_active: true },
  ]);

  const [selectedSignalId, setSelectedSignalId] = useState<string>('SIG-01');
  const [selectedCorridor, setSelectedCorridor] = useState<string>('Hospital Emergency Line');
  const [feedback, setFeedback] = useState<string | null>(null);

  const selectedSignal = signals.find((s) => s.id === selectedSignalId) || signals[0];

  const handleOverridePhase = async (signalId: string, phase: 'GREEN' | 'RED' | 'YELLOW') => {
    try {
      await trafficService.overrideSignal(signalId, phase, 'MANUAL_OVERRIDE');
    } catch {
      // local simulated fallback
    }
    setSignals((prev) =>
      prev.map((s) =>
        s.id === signalId
          ? { ...s, current_phase: phase, mode: 'MANUAL', time_in_current_phase: 0 }
          : s
      )
    );
    setFeedback(`Manual Phase Override: ${signalId} forced to ${phase} (90s lock).`);
    setTimeout(() => setFeedback(null), 3500);
  };

  const handleRestoreAuto = (signalId: string) => {
    setSignals((prev) =>
      prev.map((s) => (s.id === signalId ? { ...s, mode: 'AUTO' } : s))
    );
    setFeedback(`Signal ${signalId} restored to Adaptive AI SCADA Auto-cycle.`);
    setTimeout(() => setFeedback(null), 3500);
  };

  const handleDispatchCorridor = async () => {
    try {
      await trafficService.triggerGreenCorridor(selectedCorridor, ['SIG-01', 'SIG-02', 'SIG-03']);
    } catch {
      // simulated fallback
    }
    setSignals((prev) =>
      prev.map((s) =>
        ['SIG-01', 'SIG-02', 'SIG-03'].includes(s.id)
          ? { ...s, current_phase: 'GREEN', mode: 'EMERGENCY_CORRIDOR' }
          : s
      )
    );
    setFeedback(`Emergency Green Corridor "${selectedCorridor}" activated. Cascaded signals forced GREEN.`);
    setTimeout(() => setFeedback(null), 4500);
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Operator Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Car className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wide">
                TRAFFIC OPERATIONS CENTER (TOC)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                ● 6 / 6 JUNCTIONS CONNECTED
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">
              Corridor Orchestration & Manual Signal Control
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Authoritative SCADA Overrides • Pre-emption Telemetry • Video Verification
            </p>
          </div>
        </div>

        {/* Emergency Pre-emption Action */}
        <div className="flex items-center gap-2">
          <select
            value={selectedCorridor}
            onChange={(e) => setSelectedCorridor(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none"
          >
            <option value="Hospital Emergency Line">Hospital Emergency Line</option>
            <option value="Airport VIP Express">Airport VIP Express</option>
            <option value="Central Fire Station Route">Central Fire Station Route</option>
          </select>

          <button
            onClick={handleDispatchCorridor}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-mono text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-cyan-500/20"
          >
            <Zap className="w-4 h-4" />
            Dispatch Green Corridor
          </button>
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2.5 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Main Grid: Signal Overrides & CCTV Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Signal Matrix (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase font-bold px-1">
            <span>Intersections & Signal Phases</span>
            <span>Click to Override</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {signals.map((sig) => {
              const isSelected = sig.id === selectedSignal.id;
              const phaseColor =
                sig.current_phase === 'GREEN'
                  ? 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30'
                  : sig.current_phase === 'RED'
                  ? 'text-rose-400 bg-rose-500/20 border-rose-500/30'
                  : 'text-amber-400 bg-amber-500/20 border-amber-500/30';

              return (
                <div
                  key={sig.id}
                  onClick={() => setSelectedSignalId(sig.id)}
                  className={`p-4 rounded-xl border font-mono cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-cyan-500 shadow-md ring-1 ring-cyan-500/50'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs font-bold text-slate-100">{sig.name}</div>
                      <span className="text-[10px] text-slate-400">{sig.id}</span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase border ${phaseColor}`}>
                      {sig.current_phase}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-3 text-[10px] text-slate-400 border-t border-slate-800/60 pt-2">
                    <span>Mode: <strong className="text-slate-200">{sig.mode}</strong></span>
                    <span>Phase: {sig.time_in_current_phase}s / {sig.phase_duration_seconds}s</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active Signal Control Console */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  Manual Phase Override: {selectedSignal.name} ({selectedSignal.id})
                </h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">
                  Direct SCADA PLC Command Packet Transmission
                </p>
              </div>

              <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-slate-300">
                Current: {selectedSignal.current_phase} ({selectedSignal.mode})
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button
                onClick={() => handleOverridePhase(selectedSignal.id, 'GREEN')}
                className="py-3 rounded-xl bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 border border-emerald-500/50 font-mono text-xs font-bold transition flex items-center justify-center gap-2"
              >
                <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
                Force GREEN
              </button>

              <button
                onClick={() => handleOverridePhase(selectedSignal.id, 'RED')}
                className="py-3 rounded-xl bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/50 font-mono text-xs font-bold transition flex items-center justify-center gap-2"
              >
                <span className="w-3 h-3 rounded-full bg-rose-400 shadow-[0_0_8px_#f43f5e]" />
                Force RED
              </button>

              <button
                onClick={() => handleOverridePhase(selectedSignal.id, 'YELLOW')}
                className="py-3 rounded-xl bg-amber-600/30 hover:bg-amber-600/50 text-amber-300 border border-amber-500/50 font-mono text-xs font-bold transition flex items-center justify-center gap-2"
              >
                <span className="w-3 h-3 rounded-full bg-amber-400 shadow-[0_0_8px_#fbbf24]" />
                Flash AMBER
              </button>

              <button
                onClick={() => handleRestoreAuto(selectedSignal.id)}
                className="py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-mono text-xs font-bold transition flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
                Auto Mode
              </button>
            </div>
          </div>
        </div>

        {/* CCTV Verification Panel (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="text-xs font-mono text-slate-400 uppercase font-bold px-1">
            Visual Verification & ANPR Camera
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
            {/* Simulated Live Camera Screen */}
            <div className="relative aspect-video bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex flex-col justify-between p-3">
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 z-10">
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  LIVE CAM-01 (MG Road Gantry)
                </span>
                <span>30 FPS • 1080p H.265</span>
              </div>

              {/* Graphical representation of cars passing */}
              <div className="my-auto flex items-center justify-center">
                <div className="text-center space-y-2">
                  <Video className="w-10 h-10 text-slate-600 mx-auto animate-pulse" />
                  <div className="text-xs font-mono text-slate-400">
                    ANPR Optical Recognition Active
                  </div>
                  <div className="text-sm font-mono font-bold text-cyan-400 bg-slate-900/80 px-3 py-1 rounded border border-slate-800 inline-block">
                    Plate: KA-01-MJ-4412 (Speed: 48 km/h)
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 z-10 border-t border-slate-800/80 pt-1.5">
                <span>Vehicles: 42 / min</span>
                <span className="text-emerald-400">Congestion: Moderate (38%)</span>
              </div>
            </div>

            {/* Incidents & Anomaly Feed */}
            <div className="space-y-2 pt-2">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">
                Active Roadside Anomalies
              </div>

              <div className="p-3 bg-slate-950 border border-rose-500/30 rounded-xl flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div className="text-xs font-mono">
                  <div className="font-bold text-rose-300">Stalled Bus on Hebbal Flyover (Lane 2)</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Towing dispatch team mobilized • ETA 8 mins</div>
                </div>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div className="text-xs font-mono">
                  <div className="font-bold text-slate-200">FASTag Gantry 04 Audit Clean</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">850 scans verified in last hour</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
