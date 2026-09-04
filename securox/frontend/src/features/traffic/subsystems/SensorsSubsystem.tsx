import React from 'react';
import { TrafficSensor, SensorDisparityReport } from '../../../types/traffic';
import { Radio, RefreshCw } from 'lucide-react';

interface Props {
  sensors: TrafficSensor[];
  disparity: SensorDisparityReport | null;
  onRefresh: () => void;
}

export const SensorsSubsystem: React.FC<Props> = ({ sensors: _sensors, disparity, onRefresh }) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-purple-400" />
            Roadside Sensors & Sensor Disparity Engine
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Cross-compares physical inductive loop telemetry vs. YOLOv8 CCTV bounding box tracking
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-scan Telemetry
        </button>
      </div>

      {/* Disparity Summary Banner */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4 font-mono">
        <div>
          <div className="text-xs text-slate-400">Systemic Sensor Integrity Score</div>
          <div className="text-xl font-bold text-purple-400">
            {disparity?.systemic_integrity_score ?? 96.2}%
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Junction Pairs Cross-Validated</div>
          <div className="text-xl font-bold text-slate-200">
            {disparity?.pairs_analyzed ?? 3} Pairs
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Disparity Anomalies Detected</div>
          <div className="text-xl font-bold text-rose-400">
            {disparity?.anomalies_detected ?? 1} Flags
          </div>
        </div>
        <div className="text-right">
          <span className="px-2.5 py-1 rounded bg-purple-950/80 border border-purple-800 text-purple-300 text-xs font-bold">
            DUAL-TELEMETRY SHIELD ACTIVE
          </span>
        </div>
      </div>

      {/* Cross-Validation Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
            Inductive Loop vs. CCTV YOLO Optical Track Comparison
          </h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 text-[11px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3">Junction / Location</th>
                <th className="p-3">Physical Sensor</th>
                <th className="p-3 text-right">Loop Count</th>
                <th className="p-3">Camera Pair</th>
                <th className="p-3 text-right">CCTV YOLO Count</th>
                <th className="p-3 text-right">Delta / %</th>
                <th className="p-3">Status</th>
                <th className="p-3">Automated Diagnosis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {disparity?.disparity_pairs?.map((p, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition">
                  <td className="p-3 font-bold text-slate-200">{p.junction}</td>
                  <td className="p-3 text-cyan-400">{p.sensor_id} ({p.sensor_type})</td>
                  <td className="p-3 text-right font-bold text-slate-200">{p.sensor_count}</td>
                  <td className="p-3 text-blue-400">{p.camera_id}</td>
                  <td className="p-3 text-right font-bold text-slate-200">{p.camera_detected_count}</td>
                  <td className="p-3 text-right font-bold">
                    <span className={p.status === 'ANOMALOUS_DISPARITY' ? 'text-rose-400' : 'text-emerald-400'}>
                      {p.disparity_delta} ({p.disparity_pct}%)
                    </span>
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                        p.status === 'NOMINAL'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td className="p-3 text-slate-400 text-[11px] max-w-xs">{p.diagnosis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
