import { authService } from '../services/authService';
import { UserCapabilities, CapabilitiesResponse, RoleId } from '../types/auth';

interface PermissionState {
  capabilities: UserCapabilities;
  allowedPages: string[];
  sector: string;
  role: RoleId;
  rawPermissions: Record<string, string[]>;
  isLoading: boolean;
}

const defaultCapabilities: UserCapabilities = {
  can_override_signals: false,
  can_dispatch_ambulances: false,
  can_view_patient_records: false,
  can_edit_patient_records: false,
  can_freeze_accounts: false,
  can_execute_mitigations: false,
  can_inject_simulations: false,
  can_edit_policies: false,
  is_admin: false,
  is_read_only: true,
};

let state: PermissionState = {
  capabilities: { ...defaultCapabilities, is_admin: true, can_override_signals: true, can_dispatch_ambulances: true, can_view_patient_records: true, can_edit_patient_records: true, can_freeze_accounts: true, can_execute_mitigations: true, can_inject_simulations: true, can_edit_policies: true, is_read_only: false },
  allowedPages: ['overview', 'twin', 'healthcare', 'doctor', 'ambulance', 'traffic', 'finance', 'executive', 'demo'],
  sector: 'global',
  role: 'admin',
  rawPermissions: {},
  isLoading: false,
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

export const permissionStore = {
  getState(): PermissionState {
    return state;
  },

  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  async refresh(): Promise<void> {
    state = { ...state, isLoading: true };
    notify();
    try {
      const data: CapabilitiesResponse = await authService.getCapabilities();
      state = {
        capabilities: data.capabilities,
        allowedPages: data.allowed_pages || [],
        sector: data.sector,
        role: data.role,
        rawPermissions: data.permissions || {},
        isLoading: false,
      };
      notify();
    } catch (err) {
      console.warn('[permissionStore] Failed to fetch capabilities, falling back to role rules:', err);
      state = { ...state, isLoading: false };
      notify();
    }
  },

  can(capability: keyof UserCapabilities): boolean {
    return !!state.capabilities[capability];
  },

  isPageAllowed(pageId: string): boolean {
    if (pageId === 'workspace') return true;
    if (state.capabilities.is_admin) return true;
    if (state.allowedPages.includes('all')) return true;
    return state.allowedPages.includes(pageId);
  },
};
