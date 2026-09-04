import React from 'react';
import { usePermissions } from '../../hooks/usePermissions';
import { UserCapabilities } from '../../types/auth';
import { ShieldAlert } from 'lucide-react';

interface PermissionGuardProps {
  capability: keyof UserCapabilities;
  fallbackMessage?: string;
  children: React.ReactElement<any>;
  hideInsteadOfDisable?: boolean;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  capability,
  fallbackMessage,
  children,
  hideInsteadOfDisable = false,
}) => {
  const { can, role } = usePermissions();
  const allowed = can(capability);

  if (allowed) {
    return children;
  }

  if (hideInsteadOfDisable) {
    return null;
  }

  const message = fallbackMessage || `Action restricted: Requires authorized privileges (Current role: ${role})`;

  // Clone child with disabled prop, altered style, and explanatory tooltip wrapper
  return (
    <div className="relative group inline-block cursor-not-allowed" title={message}>
      {React.cloneElement(children, {
        disabled: true,
        className: `${children.props.className || ''} opacity-40 pointer-events-none cursor-not-allowed filter grayscale`,
        'aria-disabled': 'true',
      })}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono bg-slate-900/95 text-amber-300 border border-amber-500/40 rounded shadow-xl whitespace-nowrap z-50 pointer-events-none">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>{message}</span>
      </div>
    </div>
  );
};
