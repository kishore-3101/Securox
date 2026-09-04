import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Briefcase,
  Shield,
  Network,
  HeartPulse,
  Stethoscope,
  Ambulance,
  Car,
  Landmark,
  BarChart3,
  PlayCircle,
  Lock,
} from 'lucide-react';
import { usePermissions } from '../../hooks/usePermissions';
import { useWebSocket } from '../../hooks/useWebSocket';

interface NavItem {
  id: string;
  name: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const { isPageAllowed, role } = usePermissions();
  const { incidents } = useWebSocket();

  const openIncidents = incidents.filter((i) => i.status !== 'RESOLVED').length;

  const navItems: NavItem[] = [
    { id: 'workspace', name: 'Role Workflow HQ', path: '/workspace', icon: Briefcase },
    { id: 'overview', name: 'SOC Command Center', path: '/soc', icon: Shield, badge: openIncidents > 0 ? String(openIncidents) : undefined },
    { id: 'twin', name: 'Digital Twin', path: '/twin', icon: Network },
    { id: 'healthcare', name: 'Healthcare Command', path: '/healthcare', icon: HeartPulse },
    { id: 'doctor', name: 'Doctor Portal', path: '/doctor', icon: Stethoscope },
    { id: 'ambulance', name: 'Ambulance CAD', path: '/ambulance', icon: Ambulance },
    { id: 'traffic', name: 'Traffic Operations', path: '/traffic', icon: Car },
    { id: 'finance', name: 'Finance Cyber-VaR', path: '/finance', icon: Landmark },
    { id: 'executive', name: 'Executive Intelligence', path: '/executive', icon: BarChart3 },
    { id: 'demo', name: 'Demo & SimLab', path: '/demo', icon: PlayCircle },
  ];

  return (
    <aside className="w-64 bg-slate-950/95 border-r border-slate-800 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold font-mono text-sm tracking-wider text-slate-100 flex items-center gap-1.5">
            SECUROX <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">v2.0</span>
          </h1>
          <p className="text-[10px] font-mono text-slate-400">Cyber-Physical Fusion Engine</p>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono font-semibold tracking-wider text-slate-500 uppercase">
          OPERATIONAL DOMAINS
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const allowed = isPageAllowed(item.id);

          return (
            <NavLink
              key={item.id}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-mono transition-all group ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
                <span>{item.name}</span>
              </div>

              <div className="flex items-center gap-1.5">
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40">
                    {item.badge}
                  </span>
                )}
                {!allowed && (
                  <span title={`Restricted for role: ${role}`}>
                    <Lock className="w-3 h-3 text-amber-500/60" />
                  </span>
                )}
              </div>
            </NavLink>
          );
        })}
      </div>

      {/* Persona Badge */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-slate-400">ACTIVE ROLE</span>
            <span className="text-xs font-mono font-semibold text-sky-400 uppercase">{role}</span>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="System Online" />
        </div>
      </div>
    </aside>
  );
};
