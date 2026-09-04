import React from 'react';
import { Severity } from '../../types/soc';

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  className = '',
}) => {
  const norm = (severity || 'LOW').toUpperCase();

  let styles = 'bg-slate-800/80 text-slate-300 border-slate-700/50';

  if (norm === 'CRITICAL') {
    styles = 'bg-rose-950/60 text-rose-400 border-rose-500/40 animate-pulse';
  } else if (norm === 'HIGH') {
    styles = 'bg-amber-950/60 text-amber-400 border-amber-500/40';
  } else if (norm === 'MEDIUM') {
    styles = 'bg-yellow-950/50 text-yellow-300 border-yellow-500/30';
  } else if (norm === 'LOW' || norm === 'INFO') {
    styles = 'bg-sky-950/50 text-sky-300 border-sky-500/30';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border tracking-wider ${styles} ${className}`}
    >
      {norm}
    </span>
  );
};
