import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePermissions } from '../hooks/usePermissions';
import { WorkflowShell } from '../components/workflow/WorkflowShell';
import { getWorkflowForRole } from '../services/workflowRegistry';

// Spotlight Specialized Workflows
import { AmbulanceDriverWorkflow } from '../features/healthcare/workflows/AmbulanceDriverWorkflow';
import { DoctorClinicalWorkflow } from '../features/healthcare/workflows/DoctorClinicalWorkflow';
import { FraudAnalystWorkflow } from '../features/finance/workflows/FraudAnalystWorkflow';
import { TrafficOperatorWorkflow } from '../features/traffic/workflows/TrafficOperatorWorkflow';
import { SocThreatWorkflow } from '../features/soc/workflows/SocThreatWorkflow';
import { PatientPortalWorkflow } from '../features/healthcare/workflows/PatientPortalWorkflow';

import {
  Briefcase,
  Layers,
  Sparkles,
  RefreshCw,
  Stethoscope,
  Ambulance,
  Car,
  Landmark,
  Shield,
  Heart,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

export const WorkflowWorkspacePage: React.FC = () => {
  const { role, user, switchRole } = useAuth();
  const [switching, setSwitching] = useState(false);
  const [viewMode, setViewMode] = useState<'SPECIALIZED' | 'QUESTIONS'>('SPECIALIZED');

  const normalizedRole = (role || 'admin').toLowerCase().trim();
  const workflow = getWorkflowForRole(normalizedRole);

  const hasSpecializedWorkflow = [
    'ambulance_driver',
    'doctor',
    'fraud_analyst',
    'traffic_operator',
    'soc_analyst',
    'patient',
  ].includes(normalizedRole);

  const handleSwitch = async (newRole: string) => {
    setSwitching(true);
    try {
      await switchRole(newRole);
    } catch (err) {
      console.error('Failed to switch role:', err);
    } finally {
      setSwitching(false);
    }
  };

  const renderSpecializedComponent = () => {
    switch (normalizedRole) {
      case 'ambulance_driver':
        return <AmbulanceDriverWorkflow />;
      case 'doctor':
        return <DoctorClinicalWorkflow />;
      case 'fraud_analyst':
        return <FraudAnalystWorkflow />;
      case 'traffic_operator':
        return <TrafficOperatorWorkflow />;
      case 'soc_analyst':
        return <SocThreatWorkflow />;
      case 'patient':
        return <PatientPortalWorkflow />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Workspace Header & Mode Switcher */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wide">
                OPERATIONAL STAKEHOLDER WORKSPACE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Persona: <strong className="text-sky-300 uppercase">{role}</strong>
              </span>
            </div>
            <h1 className="text-xl font-bold font-mono text-slate-100">
              {workflow.roleName} Workspace
            </h1>
            <p className="text-xs font-mono text-slate-400">
              {workflow.summary}
            </p>
          </div>
        </div>

        {/* View Mode Toggle (Specialized vs 5-Questions Layout) */}
        <div className="flex items-center gap-2">
          {hasSpecializedWorkflow && (
            <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
              <button
                onClick={() => setViewMode('SPECIALIZED')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  viewMode === 'SPECIALIZED'
                    ? 'bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Specialized Dashboard
              </button>
              <button
                onClick={() => setViewMode('QUESTIONS')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  viewMode === 'QUESTIONS'
                    ? 'bg-sky-500/20 text-sky-300 font-bold border border-sky-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                5-Questions SOP Matrix
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 6 Spotlight Roles Quick Bar for instant demonstration */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex items-center justify-between gap-2 overflow-x-auto">
        <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider pl-2 shrink-0">
          Spotlight Demos:
        </div>

        <div className="flex items-center gap-2">
          {[
            { id: 'ambulance_driver', name: 'Ambulance Driver', icon: Ambulance, color: 'text-rose-400' },
            { id: 'doctor', name: 'Doctor (Clinician)', icon: Stethoscope, color: 'text-emerald-400' },
            { id: 'fraud_analyst', name: 'Fraud Analyst', icon: Landmark, color: 'text-amber-400' },
            { id: 'traffic_operator', name: 'Traffic Operator', icon: Car, color: 'text-cyan-400' },
            { id: 'soc_analyst', name: 'SOC Analyst', icon: Shield, color: 'text-purple-400' },
            { id: 'patient', name: 'Patient (Self-Service)', icon: Heart, color: 'text-pink-400' },
          ].map((item) => {
            const isCurrent = normalizedRole === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleSwitch(item.id)}
                disabled={switching}
                className={`px-3 py-1.5 rounded-lg border font-mono text-xs transition flex items-center gap-1.5 shrink-0 ${
                  isCurrent
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 font-bold shadow-sm'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${item.color}`} />
                <span>{item.name}</span>
                {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      {hasSpecializedWorkflow && viewMode === 'SPECIALIZED' ? (
        <div className="space-y-6">
          {renderSpecializedComponent()}
          
          {/* Also provide the 5 questions below the specialized component for comprehensive SOP visibility */}
          <div className="pt-4 border-t border-slate-800/80">
            <div className="text-xs font-mono text-slate-400 uppercase font-bold tracking-wider mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Stakeholder SOP 5-Questions Baseline
            </div>
            <WorkflowShell workflow={workflow} />
          </div>
        </div>
      ) : (
        /* Standard 5-Questions Layout Shell for all 35 roles */
        <WorkflowShell workflow={workflow} />
      )}
    </div>
  );
};
