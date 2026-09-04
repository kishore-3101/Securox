import React, { useState } from 'react';
import { GreenCorridor } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import { Zap, RefreshCw, Video, AlertTriangle, Clock, ShieldCheck, Activity } from 'lucide-react';

interface Props {
  corridors: GreenCorridor[];
  onRefresh: () => void;
}

export const EmergencyResponseSubsystem: React.FC<Props> = ({ corridors, onRefresh }) => {
  const [activatingId, setActivatingId] = useState<string | null>(null);

  const handleActivate = async (corridorId: string) => {
    setActivatingId(corridorId);
    try {
      await trafficService.activateGreenCorridor(corridorId);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Corridor activation failed');
    } finally {
      setActivatingId(null);
    }
  };

  const handleDeactivate = async (corridorId: string) => {
    try {
      await trafficService.deactivateGreenCorridor(corridorId);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Corridor clearance failed');
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Subsystem Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Zap className="w-5 h-5 text-rose-400" />
            Emergency CAD & Green Corridor Vision Preemption
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            1-Tap Emergency Route Preemption • Sequential Phase Clearance • CCTV Corridor Health & Congestion Telemetry
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Corridors
        </button>
      </div>

      {/* Corridor Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {corridors.map((corr) => {
          const isActive = corr.status === 'ACTIVE';
          const cameras = corr.corridor_cameras && corr.corridor_cameras.length > 0
            ? corr.corridor_cameras
            : ['CAM-101', 'CAM-102', 'CAM-105', 'CAM-108'];
          const coverage = corr.camera_coverage || `${cameras.length} / ${cameras.length} ONLINE`;
          const congestion = corr.congestion_level ?? 22;
          const isCongested = congestion >= 70;

          return (
            <div
              key={corr.id}
              className={`p-6 rounded-xl border shadow-xl flex flex-col justify-between font-mono ${
                isActive
                  ? 'bg-rose-950/20 border-rose-500/80 shadow-rose-950/30'
                  : 'bg-slate-900/80 border-slate-800'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-rose-400">{corr.id}</span>
                  <span
                    className={`px-2.5 py-0.5 text-xs font-bold rounded ${
                      isActive
                        ? 'bg-rose-950 text-rose-400 border border-rose-800 animate-pulse'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {corr.status}
                  </span>
                </div>
                <h4 className="text-base font-bold text-slate-100">{corr.name}</h4>
                <div className="mt-2 text-xs text-slate-400 space-y-1">
                  <div>Origin: <span className="text-slate-200">{corr.origin_location}</span></div>
                  <div>Destination: <span className="text-emerald-400 font-bold">{corr.destination_hospital}</span></div>
                  <div className="flex items-center justify-between">
                    <span>Ambulance Unit: <strong className="text-cyan-400">{corr.ambulance_id || 'AMB-021'}</strong></span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-300">
                      <Clock className="w-3 h-3 text-cyan-400" />
                      ETA: <strong className="text-emerald-300">{corr.estimated_duration_sec ?? 360}s</strong>
                    </span>
                  </div>
                </div>

                {/* Real-time Congestion Warning if applicable */}
                {isCongested && (
                  <div className="mt-3 p-2.5 rounded bg-amber-950/80 border border-amber-800 text-amber-300 text-[11px] flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 animate-pulse" />
                    <span>Heavy congestion ({congestion}%) detected on corridor path. Dynamic rerouting advisory active.</span>
                  </div>
                )}

                {/* Preempted Intersections */}
                <div className="mt-4 pt-3 border-t border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-2 flex items-center justify-between">
                    <span>Preempted Sequential Signals:</span>
                    <span className="text-[10px] text-emerald-400">Green Wave Active</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {corr.route_intersections.map((sigId) => (
                      <span
                        key={sigId}
                        className={`px-2 py-0.5 text-[10px] font-bold rounded border ${
                          isActive
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-700 animate-pulse'
                            : 'bg-slate-950 text-slate-400 border-slate-800'
                        }`}
                      >
                        {sigId} {isActive ? '🟢 LOCKED GREEN' : '⚪ STANDBY'}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Corridor CCTV Camera Coverage */}
                <div className="mt-4 pt-3 border-t border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-2 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Video className="w-3.5 h-3.5 text-cyan-400" />
                      CCTV Optical Coverage:
                    </span>
                    <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-800">
                      {coverage}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {cameras.map((camId) => (
                      <div
                        key={camId}
                        className="p-2 rounded bg-slate-950/80 border border-slate-800/80 flex items-center justify-between text-[10px]"
                      >
                        <span className="font-bold text-slate-300">{camId}</span>
                        <span className="text-emerald-400 font-mono flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                          ONLINE
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end gap-2">
                {isActive ? (
                  <button
                    onClick={() => handleDeactivate(corr.id)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition"
                  >
                    Deactivate & Restore Adaptive Timing
                  </button>
                ) : (
                  <button
                    onClick={() => handleActivate(corr.id)}
                    disabled={activatingId === corr.id}
                    className="px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition shadow-lg shadow-rose-950/40 disabled:opacity-50"
                  >
                    <Zap className="w-4 h-4" />
                    {activatingId === corr.id ? 'Preempting Signals...' : '1-Tap Activate Corridor'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
