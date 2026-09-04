import React, { useState, useEffect, useCallback } from 'react';
import { trafficService } from '../../services/trafficService';
import {
  TrafficOverview,
  TrafficSignal,
  CameraFeed,
  RoadSegment,
  TrafficSensor,
  SensorDisparityReport,
  TrafficIncident,
  TollScanRecord,
  GreenCorridor,
  MaintenanceTicket,
} from '../../types/traffic';
import {
  Car,
  Video,
  Radio,
  Navigation,
  Activity,
  AlertTriangle,
  CreditCard,
  Zap,
  Wrench,
  Users,
  Shield,
  ShieldCheck,
  RefreshCw,
  UserCheck,
} from 'lucide-react';

// Subsystems
import { ControlCenterSubsystem } from './subsystems/ControlCenterSubsystem';
import { CctvSurveillanceSubsystem } from './subsystems/CctvSurveillanceSubsystem';
import { SignalsSubsystem } from './subsystems/SignalsSubsystem';
import { RoadsSubsystem } from './subsystems/RoadsSubsystem';
import { SensorsSubsystem } from './subsystems/SensorsSubsystem';
import { IncidentsSubsystem } from './subsystems/IncidentsSubsystem';
import { TollFastagSubsystem } from './subsystems/TollFastagSubsystem';
import { EmergencyResponseSubsystem } from './subsystems/EmergencyResponseSubsystem';
import { MaintenanceSubsystem } from './subsystems/MaintenanceSubsystem';
import { CitizenPortalSubsystem } from './subsystems/CitizenPortalSubsystem';

export type StakeholderPersona =
  | 'OPERATOR'
  | 'POLICE'
  | 'TECHNICIAN'
  | 'EMERGENCY'
  | 'CYBERSECURITY'
  | 'CITIZEN'
  | 'ALL';

export type SubsystemTab =
  | 'CONTROL_CENTER'
  | 'CCTV'
  | 'SIGNALS'
  | 'ROADS'
  | 'SENSORS'
  | 'INCIDENTS'
  | 'TOLL'
  | 'EMERGENCY'
  | 'MAINTENANCE'
  | 'CITIZEN';

export const TrafficOperations: React.FC = () => {
  const [persona, setPersona] = useState<StakeholderPersona>('OPERATOR');
  const [activeTab, setActiveTab] = useState<SubsystemTab>('CONTROL_CENTER');

  // Unified State Across 10 Subsystems
  const [overview, setOverview] = useState<TrafficOverview | null>(null);
  const [signals, setSignals] = useState<TrafficSignal[]>([]);
  const [cameras, setCameras] = useState<CameraFeed[]>([]);
  const [roads, setRoads] = useState<RoadSegment[]>([]);
  const [sensors, setSensors] = useState<TrafficSensor[]>([]);
  const [disparity, setDisparity] = useState<SensorDisparityReport | null>(null);
  const [incidents, setIncidents] = useState<TrafficIncident[]>([]);
  const [scans, setScans] = useState<TollScanRecord[]>([]);
  const [corridors, setCorridors] = useState<GreenCorridor[]>([]);
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAllTelemetry = useCallback(async () => {
    setLoading(true);
    try {
      const [
        ovRes,
        sigRes,
        camRes,
        rdRes,
        senRes,
        dispRes,
        incRes,
        tollRes,
        corrRes,
        tktRes,
      ] = await Promise.allSettled([
        trafficService.getOverview(),
        trafficService.getSignals(),
        trafficService.getCameras(),
        trafficService.getRoads(),
        trafficService.getSensors(),
        trafficService.getSensorDisparity(),
        trafficService.getIncidents(),
        trafficService.getTollScans(),
        trafficService.getGreenCorridors(),
        trafficService.getMaintenanceTickets(),
      ]);

      if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
      if (sigRes.status === 'fulfilled') setSignals(sigRes.value);
      if (camRes.status === 'fulfilled') setCameras(camRes.value);
      if (rdRes.status === 'fulfilled') setRoads(rdRes.value);
      if (senRes.status === 'fulfilled') setSensors(senRes.value);
      if (dispRes.status === 'fulfilled') setDisparity(dispRes.value);
      if (incRes.status === 'fulfilled') setIncidents(incRes.value);
      if (tollRes.status === 'fulfilled') setScans(tollRes.value);
      if (corrRes.status === 'fulfilled') setCorridors(corrRes.value);
      if (tktRes.status === 'fulfilled') setTickets(tktRes.value);
    } catch (e) {
      console.warn('Telemetry refresh partial warning', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllTelemetry();
  }, [loadAllTelemetry]);

  // When persona changes, adjust default tab appropriately
  const handlePersonaChange = (p: StakeholderPersona) => {
    setPersona(p);
    switch (p) {
      case 'OPERATOR':
        setActiveTab('CONTROL_CENTER');
        break;
      case 'POLICE':
        setActiveTab('INCIDENTS');
        break;
      case 'TECHNICIAN':
        setActiveTab('MAINTENANCE');
        break;
      case 'EMERGENCY':
        setActiveTab('EMERGENCY');
        break;
      case 'CYBERSECURITY':
        setActiveTab('SENSORS');
        break;
      case 'CITIZEN':
        setActiveTab('CITIZEN');
        break;
      case 'ALL':
        setActiveTab('CONTROL_CENTER');
        break;
    }
  };

  // Tabs visible per persona
  const getAvailableTabs = (): { id: SubsystemTab; label: string; icon: any }[] => {
    switch (persona) {
      case 'OPERATOR':
        return [
          { id: 'CONTROL_CENTER', label: 'Control Center', icon: Car },
          { id: 'CCTV', label: 'CCTV Feeds', icon: Video },
          { id: 'SIGNALS', label: 'Traffic Signals', icon: Radio },
          { id: 'ROADS', label: 'Road Density', icon: Navigation },
          { id: 'EMERGENCY', label: 'Green Corridors', icon: Zap },
        ];
      case 'POLICE':
        return [
          { id: 'INCIDENTS', label: 'Incidents & Verification', icon: AlertTriangle },
          { id: 'CCTV', label: 'CCTV Surveillance', icon: Video },
          { id: 'EMERGENCY', label: 'Emergency Corridors', icon: Zap },
        ];
      case 'TECHNICIAN':
        return [
          { id: 'SIGNALS', label: 'Signal Controllers', icon: Radio },
          { id: 'MAINTENANCE', label: 'Hardware Maintenance', icon: Wrench },
          { id: 'SENSORS', label: 'Sensor Health', icon: Activity },
        ];
      case 'EMERGENCY':
        return [
          { id: 'EMERGENCY', label: 'CAD Green Preemption', icon: Zap },
          { id: 'CONTROL_CENTER', label: 'GIS Live Map', icon: Car },
          { id: 'SIGNALS', label: 'Preempted Signals', icon: Radio },
        ];
      case 'CYBERSECURITY':
        return [
          { id: 'SENSORS', label: 'Sensor Disparity Audit', icon: Activity },
          { id: 'TOLL', label: 'FASTag Anti-Clone Shield', icon: CreditCard },
          { id: 'SIGNALS', label: 'SCADA Signal Logs', icon: Radio },
        ];
      case 'CITIZEN':
        return [
          { id: 'CITIZEN', label: 'Public Traffic Advisory', icon: Users },
        ];
      case 'ALL':
      default:
        return [
          { id: 'CONTROL_CENTER', label: 'Control Center', icon: Car },
          { id: 'CCTV', label: 'CCTV Vision', icon: Video },
          { id: 'SIGNALS', label: 'Signals', icon: Radio },
          { id: 'ROADS', label: 'Roads & V/C', icon: Navigation },
          { id: 'SENSORS', label: 'Sensors & Disparity', icon: Activity },
          { id: 'INCIDENTS', label: 'Incidents', icon: AlertTriangle },
          { id: 'TOLL', label: 'FASTag / ANPR', icon: CreditCard },
          { id: 'EMERGENCY', label: 'Emergency CAD', icon: Zap },
          { id: 'MAINTENANCE', label: 'Maintenance', icon: Wrench },
          { id: 'CITIZEN', label: 'Citizen Feed', icon: Users },
        ];
    }
  };

  const tabs = getAvailableTabs();

  return (
    <div className="space-y-6 animate-fadeIn font-mono">
      {/* Top Header & Global SCADA Guard Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Car className="w-7 h-7 text-cyan-400" />
            <h1 className="text-xl font-bold text-slate-100">
              STIG Smart Traffic & Mobility Operations
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Zero-Trust SCADA Infrastructure • Multi-Agency Clearance • 10 Integrated Subsystems
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" /> SCADA GUARD ACTIVE
          </div>
          <button
            onClick={loadAllTelemetry}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition border border-slate-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Sync Grid
          </button>
        </div>
      </div>

      {/* Stakeholder Persona Switcher Bar */}
      <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <span className="font-bold text-slate-300">Stakeholder Persona:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {[
            { id: 'OPERATOR', label: 'Traffic Operator', roleBadge: 'SCADA Grid Control' },
            { id: 'POLICE', label: 'Traffic Police', roleBadge: 'Verification & Clearance' },
            { id: 'TECHNICIAN', label: 'Signal Technician', roleBadge: 'Diagnostics & Locks' },
            { id: 'EMERGENCY', label: 'Emergency Response', roleBadge: 'Ambulance CAD' },
            { id: 'CYBERSECURITY', label: 'Cybersecurity Analyst', roleBadge: 'SCADA & Anti-Clone' },
            { id: 'CITIZEN', label: 'Citizen', roleBadge: 'Public Advisory Only' },
            { id: 'ALL', label: 'System Admin', roleBadge: 'Full 10-Subsystem Matrix' },
          ].map((p) => {
            const isSelected = persona === p.id;
            return (
              <button
                key={p.id}
                onClick={() => handlePersonaChange(p.id as StakeholderPersona)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition border ${
                  isSelected
                    ? 'bg-cyan-950 text-cyan-300 border-cyan-500 shadow-md shadow-cyan-950/40'
                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Subsystem Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-800 overflow-x-auto pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-t-lg text-xs font-bold transition whitespace-nowrap border-b-2 ${
                isSelected
                  ? 'bg-slate-900/90 text-cyan-400 border-cyan-400'
                  : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-slate-900/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Subsystem Views Container */}
      <div className="pt-2">
        {activeTab === 'CONTROL_CENTER' && (
          <ControlCenterSubsystem
            overview={overview}
            signals={signals}
            roads={roads}
            cameras={cameras}
            incidents={incidents}
            onSelectTab={setActiveTab}
          />
        )}

        {activeTab === 'CCTV' && (
          <CctvSurveillanceSubsystem
            cameras={cameras}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'SIGNALS' && (
          <SignalsSubsystem
            signals={signals}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'ROADS' && (
          <RoadsSubsystem
            roads={roads}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'SENSORS' && (
          <SensorsSubsystem
            sensors={sensors}
            disparity={disparity}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'INCIDENTS' && (
          <IncidentsSubsystem
            incidents={incidents}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'TOLL' && (
          <TollFastagSubsystem
            scans={scans}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'EMERGENCY' && (
          <EmergencyResponseSubsystem
            corridors={corridors}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'MAINTENANCE' && (
          <MaintenanceSubsystem
            tickets={tickets}
            onRefresh={loadAllTelemetry}
          />
        )}

        {activeTab === 'CITIZEN' && (
          <CitizenPortalSubsystem />
        )}
      </div>
    </div>
  );
};

export default TrafficOperations;
