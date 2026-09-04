import React, { useState } from 'react';
import { WorkflowDefinition, WorkflowAction } from '../../types/workflow';
import { PermissionGuard } from '../common/PermissionGuard';
import { KpiCard } from '../common/KpiCard';
import { StatusDot } from '../common/StatusDot';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  HelpCircle,
  Zap,
  Lock,
  Phone,
  FileCheck,
  Activity,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

interface WorkflowShellProps {
  workflow: WorkflowDefinition;
  customMainView?: React.ReactNode;
}

export const WorkflowShell: React.FC<WorkflowShellProps> = ({ workflow, customMainView }) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'Q5'>('ALL');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const handleExecuteAction = (action: WorkflowAction) => {
    if (action.confirmMessage) {
      if (!window.confirm(action.confirmMessage)) return;
    }
    setActionFeedback(`Action executed: ${action.label}`);
    setTimeout(() => setActionFeedback(null), 4000);
  };

  const domainColors = {
    HEALTHCARE: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    TRAFFIC: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    FINANCE: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    SECURITY: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  }[workflow.domain];

  return (
    <div className="space-y-6 animate-fadeIn font-sans">
      {/* Role Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${domainColors}`}>
                {workflow.domain} WORKFLOW
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                ● {workflow.dutyStatus.replace('_', ' ')}
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100">{workflow.roleName}</h2>
            <p className="text-xs font-mono text-slate-400">{workflow.department} — {workflow.summary}</p>
          </div>

          {/* 5-Questions Quick Filter Bar */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'ALL'
                  ? 'bg-sky-500/20 text-sky-400 border-sky-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              All 5 Questions
            </button>
            <button
              onClick={() => setActiveTab('Q1')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'Q1'
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              1. What to do now?
            </button>
            <button
              onClick={() => setActiveTab('Q2')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'Q2'
                  ? 'bg-sky-500/20 text-sky-400 border-sky-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              2. Information
            </button>
            <button
              onClick={() => setActiveTab('Q3')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'Q3'
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              3. Actions
            </button>
            <button
              onClick={() => setActiveTab('Q4')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'Q4'
                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              4. Approvals
            </button>
            <button
              onClick={() => setActiveTab('Q5')}
              className={`px-3 py-1.5 rounded-lg border transition ${
                activeTab === 'Q5'
                  ? 'bg-purple-500/20 text-purple-400 border-purple-500/40 font-bold'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              5. Escalation
            </button>
          </div>
        </div>
      </div>

      {actionFeedback && (
        <div className="p-3 bg-emerald-950/50 border border-emerald-500/50 rounded-xl text-xs font-mono text-emerald-300 flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{actionFeedback}</span>
        </div>
      )}

      {/* Custom deep specialized component if provided */}
      {customMainView && (
        <div className="space-y-6">{customMainView}</div>
      )}

      {/* QUESTION 1: What do I need to do right now? */}
      {(activeTab === 'ALL' || activeTab === 'Q1') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-400 flex items-center justify-center text-xs font-mono font-bold">
                1
              </span>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                What do I need to do right now?
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {workflow.q1_immediate.headline}
            </span>
          </div>

          <div className="space-y-2.5">
            {workflow.q1_immediate.tasks.map((task) => {
              let urgencyBadge = 'bg-sky-500/20 text-sky-400 border-sky-500/30';
              if (task.urgency === 'CRITICAL') urgencyBadge = 'bg-rose-500/20 text-rose-400 border-rose-500/30 animate-pulse';
              else if (task.urgency === 'HIGH') urgencyBadge = 'bg-amber-500/20 text-amber-400 border-amber-500/30';

              return (
                <div
                  key={task.id}
                  className="bg-slate-950/70 border border-slate-800 rounded-lg p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-700 transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${urgencyBadge}`}>
                        {task.urgency}
                      </span>
                      <span className="text-xs font-mono text-slate-400">{task.category}</span>
                      {task.slaMinutes && (
                        <span className="text-[11px] font-mono text-amber-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> SLA: {task.slaMinutes}m
                        </span>
                      )}
                    </div>
                    <h4 className="text-xs font-mono font-bold text-slate-100">{task.title}</h4>
                    <p className="text-[11px] font-sans text-slate-400">{task.subtitle}</p>
                  </div>

                  <button
                    onClick={() => {
                      setActionFeedback(`Task started: ${task.title}`);
                      setTimeout(() => setActionFeedback(null), 3000);
                    }}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-sky-600 hover:bg-sky-500 text-white transition shrink-0 flex items-center justify-center gap-1.5"
                  >
                    <span>{task.actionLabel || 'Engage'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* QUESTION 2: What information do I need? */}
      {(activeTab === 'ALL' || activeTab === 'Q2') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-sky-500/20 border border-sky-500/40 text-sky-400 flex items-center justify-center text-xs font-mono font-bold">
                2
              </span>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                What information do I need?
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {workflow.q2_information.headline}
            </span>
          </div>

          {/* Metric telemetry strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {workflow.q2_information.metrics.map((m, idx) => (
              <div key={idx} className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 text-center">
                <span className="text-[10px] font-mono text-slate-400 block uppercase">{m.label}</span>
                <span className="text-lg font-mono font-bold text-slate-100 mt-0.5 block">{m.value}</span>
                {m.trend && <span className="text-[10px] font-mono text-emerald-400">{m.trend}</span>}
              </div>
            ))}
          </div>

          {/* Context Key-Value Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs font-mono">
            {workflow.q2_information.keyContextList.map((ctx, idx) => (
              <div key={idx} className="flex justify-between py-1.5 px-3 bg-slate-950/40 rounded border border-slate-800/60">
                <span className="text-slate-400">{ctx.label}:</span>
                <span className="font-semibold text-slate-200">{ctx.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* QUESTION 3: What actions can I perform? */}
      {(activeTab === 'ALL' || activeTab === 'Q3') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center text-xs font-mono font-bold">
                3
              </span>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                What actions can I perform?
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-400">
              Guarded by Authoritative Zero-Trust RBAC
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {workflow.q3_actions.actions.map((act) => {
              const buttonVariantClasses = {
                primary: 'bg-sky-600 hover:bg-sky-500 text-white',
                danger: 'bg-rose-600 hover:bg-rose-500 text-white',
                warning: 'bg-amber-600 hover:bg-amber-500 text-white',
                success: 'bg-emerald-600 hover:bg-emerald-500 text-white',
                outline: 'bg-slate-950 hover:bg-slate-800 text-slate-200 border border-slate-700',
              }[act.variant || 'primary'];

              const buttonElement = (
                <button
                  onClick={() => handleExecuteAction(act)}
                  className={`w-full p-3.5 rounded-xl text-left flex flex-col justify-between transition-all duration-200 shadow-md ${buttonVariantClasses}`}
                >
                  <div className="space-y-1">
                    <span className="text-xs font-mono font-bold block">{act.label}</span>
                    <p className="text-[11px] opacity-80 leading-relaxed font-sans">{act.description}</p>
                  </div>
                  <span className="text-[10px] font-mono mt-3 opacity-90 underline">Execute Action ➔</span>
                </button>
              );

              return act.requiredCapability ? (
                <PermissionGuard key={act.id} capability={act.requiredCapability}>
                  {buttonElement}
                </PermissionGuard>
              ) : (
                <div key={act.id}>{buttonElement}</div>
              );
            })}
          </div>
        </div>
      )}

      {/* QUESTION 4: What requires approval? */}
      {(activeTab === 'ALL' || activeTab === 'Q4') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center text-xs font-mono font-bold">
                4
              </span>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                What requires approval?
              </h3>
            </div>
            <span className="text-xs font-mono text-amber-400">
              Dual-Control & Governance Interlocks
            </span>
          </div>

          <div className="space-y-2.5">
            {workflow.q4_approvals.items.map((item) => (
              <div
                key={item.id}
                className="bg-slate-950/70 border border-slate-800 rounded-lg p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        item.status === 'APPROVED'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {item.status}
                    </span>
                    <span className="text-slate-400">By: {item.submittedBy} ({item.submittedAt})</span>
                    {item.riskScore && (
                      <span className="text-rose-400">Risk: {item.riskScore}/100</span>
                    )}
                  </div>
                  <h4 className="font-bold text-slate-200">{item.title}</h4>
                  <p className="text-[11px] text-slate-400 font-sans">{item.reason}</p>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-[10px] text-slate-500 block">AUTHORIZATION ROLE:</span>
                  <span className="text-xs font-bold text-amber-300">{item.approverRole}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* QUESTION 5: What happens when something goes wrong? */}
      {(activeTab === 'ALL' || activeTab === 'Q5') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-400 flex items-center justify-center text-xs font-mono font-bold">
                5
              </span>
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                What happens when something goes wrong?
              </h3>
            </div>
            <span className="text-xs font-mono text-rose-400 font-bold">
              Emergency Playbooks & Failsafe Interlocks
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workflow.q5_escalation.procedures.map((proc, idx) => (
              <div
                key={idx}
                className="bg-slate-950/80 border border-rose-500/30 rounded-xl p-4 space-y-3 font-mono text-xs"
              >
                <div className="flex items-start justify-between">
                  <h4 className="font-bold text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {proc.name}
                  </h4>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-300">
                    SOP ACTIVE
                  </span>
                </div>

                <div className="p-2 bg-slate-900 rounded border border-slate-800 text-slate-300 text-[11px]">
                  <b>Trigger Condition:</b> {proc.trigger}
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Immediate SOP Steps:</span>
                  <ol className="list-decimal list-inside space-y-1 text-[11px] text-slate-300 font-sans">
                    {proc.sopSteps.map((step, sIdx) => (
                      <li key={sIdx}>{step}</li>
                    ))}
                  </ol>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                  <div>
                    <span className="text-slate-500 block text-[10px]">FAILSAFE ACTION:</span>
                    <span className="text-amber-300 font-bold">{proc.failsafeAction}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 block text-[10px]">ESCALATION:</span>
                    <span className="text-sky-400 font-bold">{proc.escalationContact}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
