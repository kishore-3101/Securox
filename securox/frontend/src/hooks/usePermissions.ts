import { useSyncExternalStore } from 'react';
import { permissionStore } from '../stores/permissionStore';
import { UserCapabilities } from '../types/auth';

export function usePermissions() {
  const state = useSyncExternalStore(
    permissionStore.subscribe,
    permissionStore.getState,
    permissionStore.getState
  );

  return {
    capabilities: state.capabilities,
    allowedPages: state.allowedPages,
    sector: state.sector,
    role: state.role,
    isLoading: state.isLoading,
    can: (cap: keyof UserCapabilities) => permissionStore.can(cap),
    isPageAllowed: (page: string) => permissionStore.isPageAllowed(page),
    refresh: () => permissionStore.refresh(),
  };
}
