import React from 'react';
import {
  HeartPulse,
  Activity,
  Bed,
  Users,
  ShieldCheck,
  AlertTriangle,
  Radio,
  FileCheck,
  Zap,
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronRight,
  Database,
} from 'lucide-react';
import { KpiCard } from '../../../components/common/KpiCard';
import { Patient, IoMTDevice } from '../../../types/healthcare';

interface OverviewSubsystemProps {
  patients: Patient[];
  devices: IoMTDevice[];
  onNavigateTab: (tabId: string) => void;
  onOpenBreakGlass: () => void;
}

export const OverviewSubsystem: React.FC<OverviewSubsystemProps> = ({
  patients,
  devices,
  onNavigateTab,
  onOpenBreakGlass,
}) => {
  const totalBeds = 60;
  const occupiedBeds = patients.length + 32; // Inpatient census
  const icuOccupied = 12;
  const icuTotal = 15;
  const compromisedDevices = devices.filter((d) => (d.status as string) === 'ANOMALOUS' || (d.status as string) === 'ATTACK_DETECTED' || d.risk_score > 70).length;

  return (
    <div className="space-y-6">
      {/* Top Clinical & Cyber Posture KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Active Hospital Census"
          value={`${occupiedBeds} / ${totalBeds}`}
          subtitle={`${Math.round((occupiedBeds / totalBeds) * 100)}% Bed Occupancy Rate`}
          icon={Bed}
          accentColor="blue"
        />
        <KpiCard
          title="ICU Critical Capacity"
          value={`${icuOccupied} / ${icuTotal}`}
          subtitle="3 Trauma Bays on Standby"
          icon={HeartPulse}
          accentColor="red"
        />
        <KpiCard
          title="Protected Bedside IoMT"
          value={devices.length}
          subtitle={compromisedDevices > 0 ? `${compromisedDevices} device flagged anomalous` : 'All telemetry nominal'}
          icon={Radio}
          accentColor={compromisedDevices > 0 ? 'red' : 'green'}
        />
        <KpiCard
          title="Systemic Cyber Risk"
          value="18 / 100"
          subtitle="CareGuard Zero-Trust Active"
          icon={ShieldCheck}
          accentColor="green"
        />
      </div>

      {/* Real-time Integrated Datasets Telemetry Engine Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                Integrated Clinical Research & Infrastructure Datasets
              </h3>
              <p className="text-xs font-mono text-slate-400">
                Continuous ingestion from MIT PhysioNet MIMIC-IV, eICU Collaborative Research, and ONC Health IT
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Live Telemetry Ingestion
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-sky-300">MIMIC-IV-ED</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">v2.2</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400">Emergency Dept Triage, Acuity & Chief Complaints</p>
            <div className="text-xs font-mono font-bold text-emerald-400 pt-1">Active (Real-time)</div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-sky-300">MIMIC-IV Clinical</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">PhysioNet</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400">ICU Chart Events, Troponin Biomarkers & Vitals</p>
            <div className="text-xs font-mono font-bold text-emerald-400 pt-1">Synchronized</div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-sky-300">eICU Collaborative</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">Multicenter</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400">Physiological APACHE Risk & Bedside Infusion Rates</p>
            <div className="text-xs font-mono font-bold text-emerald-400 pt-1">Flow Calibrated</div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-sky-300">ONC Health IT</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">Standard</span>
            </div>
            <p className="text-[11px] font-mono text-slate-400">FHIR / HL7v2 Audit Controls & Interoperability</p>
            <div className="text-xs font-mono font-bold text-emerald-400 pt-1">Compliant</div>
          </div>
        </div>
      </div>

      {/* Bed Matrix & Quick Action Launchpad */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Ward Bed Status Matrix */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Bed className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
                Live Inpatient Ward & Bed Matrix
              </h3>
            </div>
            <button
              onClick={() => onNavigateTab('admissions')}
              className="text-xs font-mono text-sky-400 hover:text-sky-300 flex items-center gap-1 transition"
            >
              <span>Manage Admissions</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {/* Cardiac ICU */}
            <div className="bg-slate-950/50 border border-slate-800/60 rounded-lg p-3">
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="font-bold text-slate-300">Cardiac Intensive Care Unit (CICU)</span>
                <span className="text-rose-400 font-bold">5 / 6 Beds Occupied (83%)</span>
              </div>
              <div className="grid grid-cols-6 gap-2">
                {['ICU-01', 'ICU-02', 'ICU-03', 'ICU-04', 'ICU-05', 'ICU-06'].map((bed, idx) => (
                  <div
                    key={bed}
                    className={`p-2 rounded border text-center font-mono text-[10px] ${
                      idx === 5
                        ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                        : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
                    }`}
                  >
                    <div className="font-bold">{bed}</div>
                    <div className="text-[9px] mt-0.5 opacity-80">{idx === 5 ? 'AVAILABLE' : 'OCCUPIED'}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Stepdown Ward */}
            <div className="bg-slate-950/50 border border-slate-800/60 rounded-lg p-3">
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="font-bold text-slate-300">Stepdown Cardiac Ward</span>
                <span className="text-amber-400 font-bold">4 / 6 Beds Occupied (67%)</span>
              </div>
              <div className="grid grid-cols-6 gap-2">
                {['STP-01', 'STP-02', 'STP-03', 'STP-04', 'STP-05', 'STP-06'].map((bed, idx) => (
                  <div
                    key={bed}
                    className={`p-2 rounded border text-center font-mono text-[10px] ${
                      idx >= 4
                        ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                        : 'bg-amber-950/30 border-amber-500/40 text-amber-300'
                    }`}
                  >
                    <div className="font-bold">{bed}</div>
                    <div className="text-[9px] mt-0.5 opacity-80">{idx >= 4 ? 'AVAILABLE' : 'OCCUPIED'}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* General Med/Surg */}
            <div className="bg-slate-950/50 border border-slate-800/60 rounded-lg p-3">
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="font-bold text-slate-300">General Medicine & Surgical Ward</span>
                <span className="text-sky-400 font-bold">8 / 12 Beds Occupied (67%)</span>
              </div>
              <div className="grid grid-cols-6 gap-2">
                {['GEN-01', 'GEN-02', 'GEN-03', 'GEN-04', 'GEN-05', 'GEN-06', 'GEN-07', 'GEN-08', 'GEN-09', 'GEN-10', 'GEN-11', 'GEN-12'].map((bed, idx) => (
                  <div
                    key={bed}
                    className={`p-1.5 rounded border text-center font-mono text-[9px] ${
                      idx >= 8
                        ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                        : 'bg-slate-800/60 border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="font-bold">{bed}</div>
                    <div className="text-[8px] opacity-75">{idx >= 8 ? 'OPEN' : 'ADMIT'}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Operational Quick Launch & Emergency Protocol */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
              <Zap className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
                Operational Subsystems Quick Launch
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <button
                onClick={() => onNavigateTab('patients')}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/40 text-left transition group"
              >
                <div className="text-xs font-mono font-bold text-slate-200 group-hover:text-sky-400 flex items-center justify-between">
                  <span>Register Patient</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400" />
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">Intake form & triage assignment</div>
              </button>

              <button
                onClick={() => onNavigateTab('appointments')}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/40 text-left transition group"
              >
                <div className="text-xs font-mono font-bold text-slate-200 group-hover:text-sky-400 flex items-center justify-between">
                  <span>Doctor Tokens</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400" />
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">Consultation queue & slots</div>
              </button>

              <button
                onClick={() => onNavigateTab('emergency')}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-rose-500/50 hover:bg-slate-800/40 text-left transition group"
              >
                <div className="text-xs font-mono font-bold text-slate-200 group-hover:text-rose-400 flex items-center justify-between">
                  <span>ED Trauma CAD</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-rose-400" />
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">P1-P4 priority triage dispatch</div>
              </button>

              <button
                onClick={() => onNavigateTab('ambulance')}
                className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-800/40 text-left transition group"
              >
                <div className="text-xs font-mono font-bold text-slate-200 group-hover:text-emerald-400 flex items-center justify-between">
                  <span>Ambulance CAD</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400" />
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-1">Fleet tracking & Green Corridor</div>
              </button>
            </div>
          </div>

          {/* Emergency Break-Glass Shortcut Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-rose-950/60 to-red-950/40 border border-rose-500/40 space-y-2.5">
            <div className="flex items-center gap-2 text-rose-300 font-mono text-xs font-bold">
              <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
              <span>EMERGENCY BREAK-GLASS OVERRIDE</span>
            </div>
            <p className="text-[11px] font-mono text-slate-300 leading-relaxed">
              Clinicians encountering an unassigned emergency patient can break privacy glass immediately. Mandatory justification required; triggers SOC incident dispatch & +35.0 risk score escalation.
            </p>
            <button
              onClick={onOpenBreakGlass}
              className="w-full py-2 px-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>REQUEST EMERGENCY BREAK-GLASS ACCESS</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
