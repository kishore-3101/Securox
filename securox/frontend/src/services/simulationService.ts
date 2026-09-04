import { api } from './api';

export const simulationService = {
  async runSimulation(scenario: string, targetAsset: string = 'traffic_system', duration: number = 20): Promise<any> {
    return api.post('/simulate', {
      scenario,
      target_asset: targetAsset,
      duration,
    });
  },

  async evaluateAccess(payload: {
    user_id: string;
    username: string;
    role: string;
    domain: string;
    resource_type: string;
    action: string;
    department?: string;
    device_id?: string;
    device_trust?: number;
    is_known_device?: boolean;
    client_ip?: string;
    geo_location?: string;
    record_count?: number;
    transaction_amount?: number;
    patient_assignment?: string;
    network_trust?: string;
    auth_strength?: string;
  }): Promise<any> {
    return api.post('/security/evaluate-access', payload);
  },

  async resetCity(): Promise<any> {
    return api.post('/twin/reset');
  },

  // ── DEMO CENTER 9-STAGE PROGRESSION ──────────────────────────────
  async startDemo(category: string, mode: string, speed: number = 1.0): Promise<any> {
    return api.post('/demo-center/start', {
      category,
      mode,
      speed,
    });
  },

  async pauseDemo(): Promise<any> {
    return api.post('/demo-center/pause');
  },

  async resumeDemo(): Promise<any> {
    return api.post('/demo-center/resume');
  },

  async resetDemo(): Promise<any> {
    return api.post('/demo-center/reset');
  },

  async setDemoSpeed(speed: number): Promise<any> {
    return api.post('/demo-center/speed', { speed });
  },

  async getDemoStatus(): Promise<any> {
    return api.get('/demo-center/status');
  },

  async getDemoScenarios(): Promise<any> {
    return api.get('/demo-center/scenarios');
  },
};
