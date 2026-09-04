import React from 'react';
import { TrafficOverview, TrafficSignal, RoadSegment, CameraFeed, TrafficIncident } from '../../../types/traffic';
import { KpiCard } from '../../../components/common/KpiCard';
import { StatusDot } from '../../../components/common/StatusDot';
import { OperationalMap } from '../../../components/map/OperationalMap';
import {
  Car,
  Radio,
  AlertTriangle,
  Zap,
  Navigation,
  ShieldCheck,
  Activity,
  Layers,
  Video,
} from 'lucide-react';

interface Props {
  overview: TrafficOverview | null;
  signals: TrafficSignal[];
  roads: RoadSegment[];
  cameras?: CameraFeed[];
  incidents?: TrafficIncident[];
  onSelectTab: (tab: any) => void;
}

export const ControlCenterSubsystem: React.FC<Props> = ({
  overview,
  signals,
  roads,
  cameras = [],
  incidents = [],
  onSelectTab,
}) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Citywide Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          title="Grid Signals"
          value={overview?.total_signals || signals.length || 6}
          subtitle="Adaptive Connected"
          icon={Radio}
          accentColor="blue"
        />
        <KpiCard
          title="Active Incidents"
          value={overview?.active_incidents_count ?? incidents.filter(i => i.status !== 'RESOLVED').length ?? 3}
          subtitle="Under Police Dispatch"
          icon={AlertTriangle}
          accentColor="amber"
        />
        <KpiCard
          title="Green Corridors"
          value={overview?.active_green_corridors ?? 1}
          subtitle="Preempted Emergency"
          icon={Zap}
          accentColor="green"
        />
        <KpiCard
          title="City Avg Speed"
          value={`${overview?.average_speed_kmh ?? 46.5} km/h`}
          subtitle="Urban Mobility Index"
          icon={Car}
          accentColor="blue"
        />
        <KpiCard
          title="Sensor Integrity"
          value={overview?.sensor_disparity_alerts ? `${overview.sensor_disparity_alerts} Alerts` : '96.2%'}
          subtitle="Loop vs CCTV Disparity"
          icon={ShieldCheck}
          accentColor="purple"
        />
        <KpiCard
          title="Grid Congestion"
          value={overview?.grid_congestion_index ?? 'MODERATE'}
          subtitle="V/C Density Ratio"
          icon={Activity}
          accentColor="green"
        />
      </div>

      {/* Operational Interactive Map */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100">
              Metropolitan SCADA GIS Operational Map (Leaflet Live Feed)
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Real-time Layers: Signals, YOLO CCTVs, Corridors & Road Incidents
          </span>
        </div>
        <div className="rounded-lg overflow-hidden border border-slate-800">
          <OperationalMap
            height="420px"
            signals={signals}
            cameras={cameras}
            incidents={incidents}
          />
        </div>
      </div>

      {/* Grid Overview & Quick Navigation Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Signal Hub Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400" />
              Real-Time Signal Junction Status
            </h3>
            <button
              onClick={() => onSelectTab('SIGNALS')}
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 underline"
            >
              View All Signals →
            </button>
          </div>
          <div className="space-y-2.5">
            {signals.slice(0, 5).map((sig) => {
              const currentState = sig.current_state || sig.current_phase || 'RED';
              return (
                <div
                  key={sig.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
                >
                  <div>
                    <div className="text-xs font-bold font-mono text-slate-200">{sig.id} - {sig.intersection || sig.name || 'Junction'}</div>
                    <div className="text-[10px] font-mono text-slate-400">Zone: {sig.zone || 'Central'} | Mode: {sig.mode}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                        currentState === 'GREEN'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : currentState === 'YELLOW'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {currentState}
                    </span>
                    <StatusDot status={sig.status === 'OFFLINE' ? 'OFFLINE' : 'ONLINE'} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Arterial Corridors Density */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2">
              <Navigation className="w-4 h-4 text-blue-400" />
              Arterial Road Network V/C Density
            </h3>
            <button
              onClick={() => onSelectTab('ROADS')}
              className="text-xs font-mono text-blue-400 hover:text-blue-300 underline"
            >
              Corridor Flow →
            </button>
          </div>
          <div className="space-y-2.5">
            {roads.slice(0, 5).map((road) => (
              <div
                key={road.id}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="text-xs font-bold font-mono text-slate-200">{road.name}</div>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                      road.congestion_level === 'LOW'
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                        : road.congestion_level === 'MODERATE'
                        ? 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/60'
                        : road.congestion_level === 'HEAVY'
                        ? 'bg-amber-950/80 text-amber-400 border border-amber-800/60'
                        : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                    }`}
                  >
                    {road.congestion_level}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Speed: {road.current_speed_kmh} / {road.speed_limit_kmh} km/h</span>
                  <span>Volume: {road.current_volume || 320} vph</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Dispatch & Actions Banner */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-lg flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold font-mono text-slate-200 flex items-center gap-2 mb-3">
              <Layers className="w-4 h-4 text-purple-400" />
              Integrated Subsystem Matrix
            </h3>
            <p className="text-xs font-mono text-slate-400 leading-relaxed mb-4">
              Direct access into all 10 unified traffic subsystems. Enforces Zero-Trust SCADA guard, dual-loop disparity checks, and encrypted FASTag anti-clone shielding.
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <button
                onClick={() => onSelectTab('CCTV')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-cyan-400 transition"
              >
                📹 CCTV & YOLOv8
              </button>
              <button
                onClick={() => onSelectTab('SENSORS')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-purple-400 transition"
              >
                📡 Disparity Engine
              </button>
              <button
                onClick={() => onSelectTab('INCIDENTS')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-amber-400 transition"
              >
                🚨 Police Incidents
              </button>
              <button
                onClick={() => onSelectTab('TOLL')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-emerald-400 transition"
              >
                💳 FASTag / ANPR
              </button>
              <button
                onClick={() => onSelectTab('EMERGENCY')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-rose-400 transition"
              >
                🚑 Green Corridors
              </button>
              <button
                onClick={() => onSelectTab('MAINTENANCE')}
                className="p-2.5 rounded bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-slate-300 hover:text-blue-400 transition"
              >
                🔧 Signal Diagnostics
              </button>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>SCADA Integrity Guard: ACTIVE</span>
            <span className="text-emerald-400 font-bold">● ZERO TRUST</span>
          </div>
        </div>
      </div>
    </div>
  );
};
