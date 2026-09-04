import React from 'react';

interface StatusDotProps {
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'WARNING' | 'ALERT' | 'HEALTHY' | string;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export const StatusDot: React.FC<StatusDotProps> = ({
  status,
  size = 'md',
  pulse = true,
}) => {
  const norm = (status || '').toUpperCase();

  let color = 'bg-slate-500';
  let pulseColor = 'bg-slate-400';

  if (['ONLINE', 'HEALTHY', 'NORMAL', 'CLEARED', 'RESOLVED', 'ACTIVE', 'GREEN'].includes(norm)) {
    color = 'bg-emerald-400';
    pulseColor = 'bg-emerald-400';
  } else if (['DEGRADED', 'WARNING', 'SUSPECT', 'HELD', 'ELEVATED', 'INVESTIGATING', 'YELLOW'].includes(norm)) {
    color = 'bg-amber-400';
    pulseColor = 'bg-amber-400';
  } else if (['OFFLINE', 'ALERT', 'CRITICAL', 'COMPROMISED', 'FAILED', 'RED', 'BLOCKED', 'ATTACK_DETECTED'].includes(norm)) {
    color = 'bg-rose-500';
    pulseColor = 'bg-rose-500';
  }

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3.5 h-3.5',
  }[size];

  return (
    <span className="relative flex items-center justify-center shrink-0">
      {pulse && (
        <span
          className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pulseColor}`}
        />
      )}
      <span className={`relative inline-flex rounded-full ${sizeClasses} ${color}`} />
    </span>
  );
};
