import { useSyncExternalStore, useEffect } from 'react';
import { authStore } from '../stores/authStore';
import { permissionStore } from '../stores/permissionStore';

export function useAuth() {
  const state = useSyncExternalStore(
    authStore.subscribe,
    authStore.getState,
    authStore.getState
  );

  useEffect(() => {
    // Whenever role changes, refresh permissions
    if (state.isAuthenticated) {
      permissionStore.refresh();
    }
  }, [state.role, state.isAuthenticated]);

  return {
    ...state,
    login: authStore.login.bind(authStore),
    switchRole: authStore.switchRole.bind(authStore),
    logout: authStore.logout.bind(authStore),
  };
}
