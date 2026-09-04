import React, { useState, useEffect } from 'react';
import { CitizenPublicFeed } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import { AlertTriangle, Zap, Clock, RefreshCw } from 'lucide-react';

export const CitizenPortalSubsystem: React.FC = () => {
  const [feed, setFeed] = useState<CitizenPublicFeed | null>(null);

  const loadFeed = async () => {
    try {
      const data = await trafficService.getCitizenPublicFeed();
      setFeed(data);
    } catch {
      console.warn('Could not load citizen feed');
    }
  };

  useEffect(() => {
    loadFeed();
  }, []);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Citizen Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-cyan-950/60 to-slate-900 border border-cyan-800/40 shadow-xl font-mono">
        <div className="flex items-center justify-between">
          <div>
            <span className="px-3 py-1 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-bold uppercase tracking-wider">
              Public Mobility Information Service
            </span>
            <h2 className="text-xl font-bold text-slate-100 mt-2">
              {feed?.city || 'Bengaluru Metropolitan Mobility Grid'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Live traffic conditions, corridor travel delay advisories, and emergency vehicle right-of-way alerts.
            </p>
          </div>
          <button
            onClick={loadFeed}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Status
          </button>
        </div>
      </div>

      {/* Emergency Corridor Advisories */}
      {feed?.active_green_corridors_advisories && feed.active_green_corridors_advisories.length > 0 && (
        <div className="space-y-2">
          {feed.active_green_corridors_advisories.map((adv, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs font-mono flex items-center gap-3 animate-fadeIn"
            >
              <Zap className="w-5 h-5 text-rose-400 shrink-0" />
              <div>
                <div className="font-bold uppercase tracking-wide">{adv.corridor_name}</div>
                <div className="text-rose-200 mt-0.5">{adv.advisory}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Grid: Public Corridors & Travel Delays */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {feed?.corridors?.map((corridor, idx) => (
          <div
            key={idx}
            className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow font-mono flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-200">{corridor.corridor}</span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    corridor.congestion_level === 'LOW'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : corridor.congestion_level === 'MODERATE'
                      ? 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                      : 'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}
                >
                  {corridor.congestion_level}
                </span>
              </div>
              <div className="text-xs text-slate-400 mt-2">
                Average Speed: <strong className="text-slate-100">{corridor.speed_kmh} km/h</strong>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-500" /> Travel Delay:
              </span>
              <span className={corridor.travel_delay_minutes > 5 ? 'text-amber-400 font-bold' : 'text-emerald-400'}>
                +{corridor.travel_delay_minutes} mins
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Public Incidents */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow font-mono">
        <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Active Public Road Obstructions & Delays
        </h3>
        <div className="space-y-2">
          {feed?.public_incidents?.map((pi, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs flex items-center justify-between"
            >
              <div>
                <span className="text-slate-200 font-bold">{pi.title}</span>
                <div className="text-[11px] text-slate-400">{pi.location} • {pi.category}</div>
              </div>
              <span className="text-[11px] text-slate-500">
                {pi.reported_at ? pi.reported_at.slice(0, 16).replace('T', ' ') : 'Live'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
