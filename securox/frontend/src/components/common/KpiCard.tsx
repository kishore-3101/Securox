import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  icon: LucideIcon;
  accentColor?: 'blue' | 'green' | 'amber' | 'red' | 'purple';
  onClick?: () => void;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  accentColor = 'blue',
  onClick,
}) => {
  const borderColors = {
    blue: 'border-l-sky-500',
    green: 'border-l-emerald-500',
    amber: 'border-l-amber-500',
    red: 'border-l-rose-500',
    purple: 'border-l-purple-500',
  }[accentColor];

  const iconColors = {
    blue: 'text-sky-400 bg-sky-500/10',
    green: 'text-emerald-400 bg-emerald-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-rose-400 bg-rose-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  }[accentColor];

  return (
    <div
      onClick={onClick}
      className={`bg-slate-900/80 border border-slate-800 rounded-lg p-4 border-l-4 ${borderColors} shadow-lg backdrop-blur transition-all duration-200 hover:border-slate-700 ${
        onClick ? 'cursor-pointer hover:bg-slate-800/50' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-mono tracking-wider text-slate-400 uppercase">{title}</p>
          <p className="text-2xl font-bold font-mono text-slate-100 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          {trend && (
            <p
              className={`text-xs font-mono mt-1 ${
                trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {trend.isPositive ? '↑' : '↓'} {trend.value}
            </p>
          )}
        </div>
        <div className={`p-2 rounded-lg ${iconColors}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
