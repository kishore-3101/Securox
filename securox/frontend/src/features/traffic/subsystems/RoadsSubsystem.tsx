import React from 'react';
import { RoadSegment } from '../../../types/traffic';
import { Navigation, RefreshCw } from 'lucide-react';

interface Props {
  roads: RoadSegment[];
  onRefresh: () => void;
}

export const RoadsSubsystem: React.FC<Props> = ({ roads, onRefresh }) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Navigation className="w-5 h-5 text-blue-400" />
            Corridor Velocity & Density Analytics (V/C Ratio)
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Real-time arterial speed deficits, lane capacity utilization, and congestion horizons
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Corridors
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {roads.map((road) => {
          const speedDeficit = Math.max(0, road.speed_limit_kmh - road.current_speed_kmh);
          const speedPct = Math.round((road.current_speed_kmh / road.speed_limit_kmh) * 100);

          return (
            <div
              key={road.id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between font-mono"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-blue-400">{road.id}</span>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                      road.congestion_level === 'LOW'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : road.congestion_level === 'MODERATE'
                        ? 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                        : road.congestion_level === 'HEAVY'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                        : 'bg-rose-950 text-rose-400 border border-rose-800'
                    }`}
                  >
                    {road.congestion_level}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-200">{road.name}</h4>
                <div className="text-[11px] text-slate-400 mt-1">
                  Length: {road.length_km} km | Lanes: {road.lanes || 3}
                </div>

                {/* Speed Meter */}
                <div className="mt-4 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Current Velocity:</span>
                    <span className="text-slate-200 font-bold">
                      {road.current_speed_kmh} <span className="text-slate-500 font-normal">/ {road.speed_limit_kmh} km/h</span>
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        speedPct > 70 ? 'bg-emerald-500' : speedPct > 40 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, speedPct)}%` }}
                    />
                  </div>
                </div>

                {/* Metrics Pill Matrix */}
                <div className="grid grid-cols-2 gap-2 mt-4 text-[11px]">
                  <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                    <div className="text-slate-500 text-[10px]">Speed Deficit</div>
                    <div className="text-amber-400 font-bold">-{speedDeficit} km/h</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                    <div className="text-slate-500 text-[10px]">Incidents</div>
                    <div className="text-slate-300 font-bold">{road.incident_count || 0} active</div>
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
