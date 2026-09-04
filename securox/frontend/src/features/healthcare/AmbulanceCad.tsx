import React, { useState, useEffect } from 'react';
import { healthcareService } from '../../services/healthcareService';
import { trafficService } from '../../services/trafficService';
import { PermissionGuard } from '../../components/common/PermissionGuard';
import { OperationalMap } from '../../components/map/OperationalMap';
import { StatusDot } from '../../components/common/StatusDot';
import { AmbulanceCAD, AmbulanceStatus } from '../../types/healthcare';
import {
  Ambulance,
  Radio,
  Clock,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Zap,
} from 'lucide-react';

export const AmbulanceCad: React.FC = () => {
  const [ambulances, setAmbulances] = useState<AmbulanceCAD[]>([
    {
      id: 'AMB-CAD-01',
      call_sign: 'CAD-01 (ALS Mobile)',
      vehicle_number: 'KA-01-EA-1081',
      status: 'EN_ROUTE',
      priority: 'P1_CRITICAL',
      assigned_hospital: 'Manipal Central Hospital',
      current_latitude: 13.205,
      current_longitude: 77.610,
      eta_minutes: 6,
      crew: ['Paramedic Rao', 'Driver Anil'],
      green_corridor_active: true,
    },
    {
      id: 'AMB-CAD-02',
      call_sign: 'CAD-02 (Cardiac Care)',
      vehicle_number: 'KA-01-EA-1082',
      status: 'TRANSPORTING',
      priority: 'P1_CRITICAL',
      assigned_hospital: 'Apollo Multi-Specialty',
      current_latitude: 13.185,
      current_longitude: 77.595,
      eta_minutes: 11,
      crew: ['Dr. Meera', 'Driver Suresh'],
      green_corridor_active: false,
    },
    {
      id: 'AMB-CAD-03',
      call_sign: 'CAD-03 (Trauma Response)',
      vehicle_number: 'KA-01-EA-1083',
      status: 'AVAILABLE',
      priority: 'P3_DELAYED',
      assigned_hospital: 'City Emergency Hub',
      current_latitude: 13.235,
      current_longitude: 77.625,
      eta_minutes: 0,
      crew: ['Paramedic John'],
      green_corridor_active: false,
    },
    {
      id: 'AMB-CAD-04',
      call_sign: 'CAD-04 (Neonatal ALS)',
      vehicle_number: 'KA-01-EA-1084',
      status: 'ON_SCENE',
      priority: 'P2_URGENT',
      assigned_hospital: 'Rainbow Children Hospital',
      current_latitude: 13.165,
      current_longitude: 77.585,
      eta_minutes: 14,
      crew: ['Nurse Priya', 'Driver Ramesh'],
      green_corridor_active: false,
    },
  ]);

  const [greenCorridorActive, setGreenCorridorActive] = useState(false);
  const [corridorSuccess, setCorridorSuccess] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await healthcareService.getAmbulances();
        if (res.ambulances && res.ambulances.length > 0) {
          const normalized = res.ambulances.map((a: any) => ({
            ...a,
            call_sign: a.call_sign || `CAD-${a.id}`,
            priority: a.priority || a.patient_priority || 'P1_CRITICAL',
            assigned_hospital: a.assigned_hospital || a.destination_hospital || 'City General Hospital',
            crew: Array.isArray(a.crew) ? a.crew : (a.driver_id ? [`Driver ${a.driver_id}`] : ['Paramedic Unit']),
            eta_minutes: a.eta_minutes ?? 8,
          }));
          setAmbulances(normalized);
        }
      } catch (err) {
        console.warn('Using default ambulance CAD fleet');
      }
    }
    load();
  }, []);

  const handleUpdateStatus = async (ambulanceId: string, status: AmbulanceStatus) => {
    try {
      await healthcareService.updateAmbulanceStatus(ambulanceId, status);
      setAmbulances((prev) =>
        prev.map((a) => (a.id === ambulanceId ? { ...a, status } : a))
      );
    } catch (err: any) {
      alert(`Error updating status: ${err.message}`);
    }
  };

  const handleTriggerGreenCorridor = async (amb: AmbulanceCAD) => {
    try {
      await trafficService.triggerGreenCorridor(`Emergency Corridor - ${amb.call_sign}`, [
        'SIG-01',
        'SIG-02',
        'SIG-03',
      ]);
      setGreenCorridorActive(true);
      setCorridorSuccess(true);
      setTimeout(() => setCorridorSuccess(false), 5000);
    } catch (err: any) {
      alert(`Green Corridor error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <Ambulance className="w-6 h-6 text-rose-500" />
            Computer-Aided Dispatch (CAD) & Green Corridor Control
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Emergency Medical Fleet Tracking, Hospital Rerouting & Traffic Pre-emption Signals
          </p>
        </div>

        {corridorSuccess && (
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2 animate-bounce">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span>Green Corridor Pre-emption Signals Granted (SIG-01 to SIG-03)</span>
          </div>
        )}
      </div>

      {/* GIS Leaflet Map with Active Ambulances */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur">
        <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-rose-400" />
          Live Fleet GIS Positioning (Bangalore-Hyderabad Corridor)
        </h3>
        <OperationalMap height="360px" ambulances={ambulances} />
      </div>

      {/* Ambulance Fleet Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {ambulances.map((amb) => (
          <div
            key={amb.id}
            className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3 shadow-lg hover:border-slate-700 transition"
          >
            <div className="flex items-start justify-between">
              <span className="text-xs font-mono font-bold text-slate-100">{amb.call_sign}</span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  amb.priority === 'P1_CRITICAL'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {amb.priority}
              </span>
            </div>

            <div className="text-xs font-mono space-y-1 text-slate-400">
              <div>Destination: <b className="text-slate-200">{amb.assigned_hospital}</b></div>
              <div>ETA: <b className="text-rose-400">{amb.eta_minutes} min</b></div>
              <div>Crew: {(amb.crew || []).join(', ')}</div>
            </div>

            {/* Status Selector & Green Corridor Button with PermissionGuard */}
            <div className="pt-2 border-t border-slate-800 flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Status:</span>
                <span className="text-sky-400 font-bold uppercase">{amb.status}</span>
              </div>

              <div className="flex items-center gap-1.5">
                <PermissionGuard capability="can_dispatch_ambulances">
                  <button
                    onClick={() => handleUpdateStatus(amb.id, 'EN_ROUTE')}
                    className="flex-1 py-1 rounded text-[10px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  >
                    En Route
                  </button>
                </PermissionGuard>

                <PermissionGuard capability="can_dispatch_ambulances">
                  <button
                    onClick={() => handleUpdateStatus(amb.id, 'TRANSPORTING')}
                    className="flex-1 py-1 rounded text-[10px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  >
                    Transport
                  </button>
                </PermissionGuard>
              </div>

              <PermissionGuard capability="can_dispatch_ambulances">
                <button
                  onClick={() => handleTriggerGreenCorridor(amb)}
                  className="w-full py-1.5 rounded text-xs font-mono font-bold bg-rose-600 hover:bg-rose-500 text-white transition flex items-center justify-center gap-1.5 shadow-md"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Request Green Corridor</span>
                </button>
              </PermissionGuard>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
