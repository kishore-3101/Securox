import React, { useState, useEffect } from 'react';
import {
  Ambulance,
  Radio,
  MapPin,
  Compass,
  Navigation,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Clock,
  ShieldCheck,
  Play,
} from 'lucide-react';
import { AmbulanceCAD } from '../../../types/healthcare';
import { healthcareService } from '../../../services/healthcareService';

interface AmbulanceSubsystemProps {
  userRole: string;
}

export const AmbulanceSubsystem: React.FC<AmbulanceSubsystemProps> = ({ userRole }) => {
  const [ambulances, setAmbulances] = useState<AmbulanceCAD[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeAmbulanceId, setActiveAmbulanceId] = useState<string>('AMB-01');
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [greenCorridorActive, setGreenCorridorActive] = useState<boolean>(false);

  const fetchAmbulances = async () => {
    setLoading(true);
    try {
      const res = await healthcareService.getAmbulances();
      if (res && res.ambulances) {
        setAmbulances(res.ambulances);
      }
    } catch (err) {
      console.error('Error fetching ambulances:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAmbulances();
  }, []);

  const handleUpdateStatus = async (ambId: string, nextStatus: string, etaMins?: number) => {
    try {
      await healthcareService.updateAmbulanceStatus(ambId, nextStatus, 'Indiranagar 100ft Road', etaMins || 6);
      setAmbulances((prev) =>
        prev.map((a) => (a.id === ambId ? { ...a, status: nextStatus as any, eta_minutes: etaMins || a.eta_minutes } : a))
      );
      setActionMsg(`Ambulance ${ambId} status transitioned to ${nextStatus}`);
      setTimeout(() => setActionMsg(null), 3500);
    } catch (err: any) {
      alert(`Failed to update ambulance status: ${err?.response?.data?.detail || err.message}`);
    }
  };

  const handleToggleGreenCorridor = (ambId: string) => {
    const nextState = !greenCorridorActive;
    setGreenCorridorActive(nextState);
    setAmbulances((prev) =>
      prev.map((a) => (a.id === ambId ? { ...a, green_corridor_active: nextState } : a))
    );
    setActionMsg(
      nextState
        ? `EMERGENCY GREEN CORRIDOR ENGAGED for ${ambId}: 6 Traffic Signals along route pre-empted to GREEN!`
        : `Green corridor deactivated for ${ambId}. Normal traffic timing restored.`
    );
    setTimeout(() => setActionMsg(null), 5000);
  };

  const activeAmbulance = ambulances.find((a) => a.id === activeAmbulanceId) || ambulances[0];

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Privacy Notice for Ambulance Driver */}
      <div className="bg-slate-900/90 border border-sky-500/40 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sky-300">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Ambulance className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold uppercase tracking-wider flex items-center gap-2">
              <span>Paramedic & Ambulance CAD Operational Scope</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 border border-sky-700 text-sky-200">
                ROLE SCOPED
              </span>
            </div>
            <div className="text-slate-400 text-[11px] mt-0.5">
              Ambulance drivers are provisioned with operational emergency mission data (triage acuity, destination bay, ETA, route telemetry), while historical patient charts and past diagnoses remain strictly shielded.
            </div>
          </div>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Header & Fleet Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Navigation className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Ambulance Fleet CAD & Traffic Green Corridor Pre-emption
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time GPS tracking, mission phase lifecycle, and STIG smart traffic controller integration
          </p>
        </div>

        <button
          onClick={fetchAmbulances}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Refresh Fleet CAD</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Fleet Selector */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="font-bold text-slate-200 uppercase tracking-wider">Active CAD Fleet Units</span>
            <span className="text-[10px] text-emerald-400">Telemetry Live</span>
          </div>

          <div className="space-y-2">
            {ambulances.map((amb) => {
              const isSelected = amb.id === activeAmbulanceId;
              return (
                <button
                  key={amb.id}
                  onClick={() => setActiveAmbulanceId(amb.id)}
                  className={`w-full p-3 rounded-lg border text-left transition ${
                    isSelected
                      ? 'bg-emerald-600/20 border-emerald-500 text-white shadow-md shadow-emerald-950'
                      : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-400">{amb.id}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                        amb.status === 'TRANSPORTING' || amb.status === 'EN_ROUTE'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800 animate-pulse'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {amb.status}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-100 mt-1">{amb.call_sign}</div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-0.5">
                    <span>ETA: {amb.eta_minutes} mins</span>
                    <span>{amb.vehicle_number}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Active Mission Control */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100">
                  {activeAmbulance?.call_sign || 'AMB-01'} ({activeAmbulance?.vehicle_number || 'KA-01-EQ-9090'})
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {activeAmbulance?.status || 'TRANSPORTING'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Assigned Hospital: {activeAmbulance?.assigned_hospital || 'City General Hospital (H001)'} • Triage Priority: P1_CRITICAL
              </p>
            </div>

            <div className="text-right">
              <div className="text-slate-400 text-[10px]">ESTIMATED TIME OF ARRIVAL</div>
              <div className="text-2xl font-bold text-emerald-400">
                {activeAmbulance?.eta_minutes || 6} <span className="text-xs font-normal text-slate-400">MINS</span>
              </div>
            </div>
          </div>

          {/* 1-Tap Green Corridor Pre-emption Trigger */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/60 to-slate-950 border border-emerald-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-300 font-bold text-xs uppercase tracking-wider">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span>Smart Traffic Green Corridor Pre-Emption</span>
              </div>
              <div className="text-[11px] text-slate-300 mt-0.5">
                Automatically pre-empts all 6 traffic signals along route to GREEN, clearing highway intersections.
              </div>
            </div>

            <button
              onClick={() => handleToggleGreenCorridor(activeAmbulance?.id || 'AMB-01')}
              className={`px-4 py-2.5 rounded-lg font-bold text-xs transition flex items-center gap-2 shadow-lg ${
                greenCorridorActive
                  ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/30'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>{greenCorridorActive ? 'DISENGAGE CORRIDOR' : '1-TAP ENGAGE GREEN CORRIDOR'}</span>
            </button>
          </div>

          {/* Mission Stage Lifecycle Progression */}
          <div className="space-y-3">
            <span className="text-slate-300 font-bold uppercase tracking-wider text-xs">
              CAD Mission Phase Progression
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              <button
                onClick={() => handleUpdateStatus(activeAmbulance?.id || 'AMB-01', 'EN_ROUTE', 14)}
                className={`p-2.5 rounded-lg border text-center font-bold ${
                  activeAmbulance?.status === 'EN_ROUTE'
                    ? 'bg-sky-600/30 border-sky-500 text-sky-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                1. EN ROUTE
              </button>

              <button
                onClick={() => handleUpdateStatus(activeAmbulance?.id || 'AMB-01', 'ON_SCENE', 10)}
                className={`p-2.5 rounded-lg border text-center font-bold ${
                  activeAmbulance?.status === 'ON_SCENE'
                    ? 'bg-amber-600/30 border-amber-500 text-amber-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                2. ON SCENE
              </button>

              <button
                onClick={() => handleUpdateStatus(activeAmbulance?.id || 'AMB-01', 'TRANSPORTING', 5)}
                className={`p-2.5 rounded-lg border text-center font-bold ${
                  activeAmbulance?.status === 'TRANSPORTING'
                    ? 'bg-rose-600/30 border-rose-500 text-rose-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                3. TRANSPORTING
              </button>

              <button
                onClick={() => handleUpdateStatus(activeAmbulance?.id || 'AMB-01', 'ARRIVED_ER', 0)}
                className={`p-2.5 rounded-lg border text-center font-bold ${
                  activeAmbulance?.status === 'ARRIVED_ER'
                    ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                4. ARRIVED ER
              </button>

              <button
                onClick={() => handleUpdateStatus(activeAmbulance?.id || 'AMB-01', 'AVAILABLE', 0)}
                className={`p-2.5 rounded-lg border text-center font-bold ${
                  activeAmbulance?.status === 'AVAILABLE'
                    ? 'bg-slate-800 border-slate-600 text-slate-200'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                5. MISSION DONE
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
