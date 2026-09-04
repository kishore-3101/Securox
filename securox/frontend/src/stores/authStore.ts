import { authService } from '../services/authService';
import { getAuthToken, setAuthToken, clearAuthToken } from '../services/api';
import { User, RoleId } from '../types/auth';

interface AuthState {
  token: string | null;
  user: User | null;
  role: RoleId;
  isAuthenticated: boolean;
  isLoading: boolean;
}

let state: AuthState = {
  token: getAuthToken(),
  user: null,
  role: 'admin',
  isAuthenticated: !!getAuthToken(),
  isLoading: true,
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export const authStore = {
  getState(): AuthState {
    return state;
  },

  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  async init(): Promise<void> {
    const token = getAuthToken();
    if (!token) {
      // For seamless demo access, auto-login as admin if no token
      try {
        await this.switchRole('admin');
        return;
      } catch (err) {
        state = { ...state, token: null, user: null, role: 'viewer', isAuthenticated: false, isLoading: false };
        notify();
        return;
      }
    }

    try {
      const user = await authService.getMe();
      state = {
        ...state,
        token,
        user,
        role: user.role || 'admin',
        isAuthenticated: true,
        isLoading: false,
      };
    } catch (err) {
      console.warn('[authStore] Token expired or invalid, auto-renewing as admin demo:', err);
      try {
        await this.switchRole('admin');
      } catch {
        clearAuthToken();
        state = { ...state, token: null, user: null, role: 'viewer', isAuthenticated: false, isLoading: false };
      }
    }
    notify();
  },

  async login(username: string, password: string): Promise<void> {
    state = { ...state, isLoading: true };
    notify();
    try {
      const tokenData = await authService.login(username, password);
      const user = await authService.getMe();
      state = {
        token: tokenData.access_token,
        user,
        role: tokenData.role,
        isAuthenticated: true,
        isLoading: false,
      };
      notify();
    } catch (err) {
      state = { ...state, isLoading: false };
      notify();
      throw err;
    }
  },

  async switchRole(roleOrUsername: string): Promise<void> {
    state = { ...state, isLoading: true };
    notify();
    try {
      const tokenData = await authService.switchRole(roleOrUsername);
      const user = await authService.getMe();
      state = {
        token: tokenData.access_token,
        user,
        role: tokenData.role,
        isAuthenticated: true,
        isLoading: false,
      };
      notify();
    } catch (err) {
      state = { ...state, isLoading: false };
      notify();
      throw err;
    }
  },

  logout(): void {
    authService.logout();
    state = {
      token: null,
      user: null,
      role: 'viewer',
      isAuthenticated: false,
      isLoading: false,
    };
    notify();
  },
};
