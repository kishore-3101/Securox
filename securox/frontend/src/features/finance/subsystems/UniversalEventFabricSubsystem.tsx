import React, { useState } from 'react';
import { SecurityEvent, SecurityEventStats } from '../../../types/finance';
import { Layers, Activity, Radio, Filter, RefreshCw } from 'lucide-react';

interface UniversalEventFabricSubsystemProps {
  events: SecurityEvent[];
  stats: SecurityEventStats | null;
  onRefresh: () => void;
}

export const UniversalEventFabricSubsystem: React.FC<UniversalEventFabricSubsystemProps> = ({
  events,
  stats,
  onRefresh
}) => {
  const [domainFilter, setDomainFilter] = useState('ALL');

  const filteredEvents = domainFilter === 'ALL'
    ? events
    : events.filter(e => e.domain.toUpperCase() === domainFilter.toUpperCase());

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="p-4 rounded-xl border border-indigo-500/30 bg-indigo-950/20 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Securox Universal Security Event Fabric (Canonical 14-Field Schema)
            </h3>
            <p className="text-xs text-slate-400">
              Single unified security telemetry fabric across Healthcare, Smart Traffic, Finance, and City SOC.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            WEBSOCKET STREAM ONLINE
          </span>
        </div>
      </div>

      {/* Domain Stats Pills */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 font-mono text-xs">
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center">
            <div className="text-slate-500 text-[10px]">TOTAL EVENTS</div>
            <div className="text-lg font-bold text-white">{stats.total_events}</div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center">
            <div className="text-slate-500 text-[10px]">HEALTHCARE</div>
            <div className="text-lg font-bold text-emerald-400">{stats.domains['HEALTHCARE'] || 0}</div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center">
            <div className="text-slate-500 text-[10px]">SMART TRAFFIC</div>
            <div className="text-lg font-bold text-blue-400">{stats.domains['TRAFFIC'] || 0}</div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center">
            <div className="text-slate-500 text-[10px]">FINANCE</div>
            <div className="text-lg font-bold text-amber-400">{stats.domains['FINANCE'] || 0}</div>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-center">
            <div className="text-slate-500 text-[10px]">HIGH RISK (≥70)</div>
            <div className="text-lg font-bold text-rose-400">{stats.high_risk_events}</div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex items-center justify-between p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400 font-semibold uppercase tracking-wider">Filter Domain:</span>
          {['ALL', 'FINANCE', 'TRAFFIC', 'HEALTHCARE', 'SECURITY'].map(d => (
            <button
              key={d}
              onClick={() => setDomainFilter(d)}
              className={`px-2.5 py-1 rounded font-medium transition ${
                domainFilter === d
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <button onClick={onRefresh} className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Canonical Events Table */}
      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="text-slate-400 border-b border-slate-800">
            <tr>
              <th className="pb-2">Event ID</th>
              <th className="pb-2">Domain</th>
              <th className="pb-2">Action</th>
              <th className="pb-2">User (Role)</th>
              <th className="pb-2">Target Resource</th>
              <th className="pb-2 text-center">Result</th>
              <th className="pb-2 text-right">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredEvents.map(ev => {
              const isBlocked = ev.result === 'BLOCKED' || ev.result === 'DENIED';
              const isFlagged = ev.result === 'FLAGGED';

              return (
                <tr key={ev.event_id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 text-white">{ev.event_id}</td>
                  <td className="py-2.5 text-indigo-400">{ev.domain}</td>
                  <td className="py-2.5 text-white font-bold">{ev.action}</td>
                  <td className="py-2.5 text-slate-300">{ev.user} ({ev.role})</td>
                  <td className="py-2.5 text-slate-400">{ev.resource}</td>
                  <td className="py-2.5 text-center">
                    <span
                      className={`text-[9px] px-2 py-0.5 rounded font-semibold ${
                        isBlocked
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : isFlagged
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {ev.result}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-bold text-amber-400">{ev.risk}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
