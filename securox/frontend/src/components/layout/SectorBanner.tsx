import React from 'react';
import { usePermissions } from '../../hooks/usePermissions';
import { ShieldCheck, AlertCircle, Eye, Stethoscope, Ambulance, Car, Landmark } from 'lucide-react';

export const SectorBanner: React.FC = () => {
  const { role, sector, capabilities } = usePermissions();

  if (role === 'admin' || role === 'superadmin') {
    return null; // Clean topbar for global admin
  }

  const roleBanners: Record<string, { icon: React.ElementType; title: string; desc: string; color: string }> = {
    doctor: {
      icon: Stethoscope,
      title: 'CLINICAL CONTEXT: Dr. Sarah Chen (Cardiology)',
      desc: 'Scoped to assigned Cardiology patients. Bulk record exports trigger adaptive zero-trust audit alerts.',
      color: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300',
    },
    nurse: {
      icon: Stethoscope,
      title: 'CLINICAL CONTEXT: Ward Care Specialist',
      desc: 'Authorized for vitals telemetry and bedside monitoring. Prescription edits restricted.',
      color: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300',
    },
    ambulance_driver: {
      icon: Ambulance,
      title: 'MOBILE EMERGENCY DISPATCH: Unit CAD-04',
      desc: 'Authorized to broadcast mission status and request Green Corridor traffic pre-emption.',
      color: 'bg-rose-950/40 border-rose-500/30 text-rose-300',
    },
    traffic_operator: {
      icon: Car,
      title: 'TRAFFIC OPERATIONS CONSOLE: Corridor STIG Control',
      desc: 'Authorized for signal cycle override and emergency lane pre-emption. FASTag holds require supervisor sign-off.',
      color: 'bg-cyan-950/40 border-cyan-500/30 text-cyan-300',
    },
    finance_investigator: {
      icon: Landmark,
      title: 'FINANCIAL INTELLIGENCE: AML & Treasury Triage',
      desc: 'Authorized to inspect money-mule clusters and execute pre-settlement escrow holds.',
      color: 'bg-amber-950/40 border-amber-500/30 text-amber-300',
    },
    viewer: {
      icon: Eye,
      title: 'READ-ONLY AUDITOR MODE',
      desc: 'All mutating controls (overrides, dispatches, freezes) are disabled by server-side policy.',
      color: 'bg-slate-900 border-slate-700 text-slate-300',
    },
  };

  const banner = roleBanners[role] || {
    icon: AlertCircle,
    title: `ACTIVE ROLE: ${role.toUpperCase()}`,
    desc: `Access restricted to ${sector} operational boundaries.`,
    color: 'bg-slate-900 border-slate-700 text-slate-300',
  };

  const Icon = banner.icon;

  return (
    <div className={`px-4 py-2 border-b flex items-center gap-3 text-xs font-mono ${banner.color}`}>
      <Icon className="w-4 h-4 shrink-0" />
      <div className="flex-1 flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">{banner.title}</span>
        <span className="text-[11px] opacity-80">{banner.desc}</span>
      </div>
    </div>
  );
};
