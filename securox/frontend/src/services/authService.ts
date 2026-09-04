import { api, setAuthToken, clearAuthToken } from './api';
import { AuthToken, CapabilitiesResponse, SectorPersona, User } from '../types/auth';

export const authService = {
  async login(username: string, password: string): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid username or password');
    }

    const data: AuthToken = await response.json();
    setAuthToken(data.access_token);
    return data;
  },

  async switchRole(roleOrUsername: string): Promise<AuthToken> {
    const data = await api.post<AuthToken>('/auth/switch-role', {
      role_or_username: roleOrUsername,
    });
    setAuthToken(data.access_token);
    return data;
  },

  async getCapabilities(): Promise<CapabilitiesResponse> {
    return api.get<CapabilitiesResponse>('/auth/capabilities');
  },

  async getMe(): Promise<User> {
    return api.get<User>('/me');
  },

  async listRoles(): Promise<{ roles: SectorPersona[] }> {
    return api.get<{ roles: SectorPersona[] }>('/auth/roles');
  },

  logout(): void {
    clearAuthToken();
  },
};
