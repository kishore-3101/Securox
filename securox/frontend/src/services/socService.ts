import { api } from './api';
import { Alert, Incident, MitigationAction, DigitalTwinNode } from '../types/soc';

export interface SocDashboardData {
  posture: {
    posture_score: number;
    status: string;
    uncontained_incidents_count: number;
    domains: Record<string, any>;
    calculation_basis: any;
    timestamp: string;
  };
  threats: {
    total_active: number;
    by_severity: Record<string, number>;
    recent_threats: Alert[];
  };
  incidents: {
    total: number;
    by_status: Record<string, number>;
    recent_incidents: any[];
  };
  risk: {
    average_risk_score: number;
    top_risk_assets: any[];
    risk_evaluations_count: number;
  };
  users: {
    total_users: number;
    anomalous_users_count: number;
    anomalous_users: any[];
  };
  devices: {
    total_monitored: number;
    isolated_count: number;
    untrusted_count: number;
    devices: any[];
  };
  domains: Record<string, any>;
  attack_chains: any[];
  audit_logs: any[];
  telemetry_source: string;
  timestamp: string;
}

export interface IncidentTimelinesData {
  incident: any;
  attack_timeline: any[];
  risk_timeline: any[];
  user_timeline: any[];
  device_timeline: any[];
  evidence: any[];
  notes: any[];
  related_events: any[];
}

export const socService = {
  // ── Legacy Compatibility ─────────────────────────────────────────
  async getAlerts(limit: number = 50, severity?: string): Promise<Alert[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (severity) params.append('severity', severity);
    return api.get<Alert[]>(`/alerts?${params.toString()}`);
  },

  async getAlertStats(): Promise<{ total: number; by_severity: Record<string, number> }> {
    return api.get<{ total: number; by_severity: Record<string, number> }>('/alerts/stats');
  },

  async getIncidents(limit: number = 100, status?: string): Promise<Incident[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.append('status', status);
    return api.get<Incident[]>(`/incidents?${params.toString()}`);
  },

  async updateIncidentStatus(
    incidentId: string,
    status: 'open' | 'investigating' | 'contained' | 'resolved' | 'false_positive',
    owner?: string
  ): Promise<Incident> {
    return api.patch<Incident>(`/incidents/${incidentId}`, { status, owner });
  },

  async getDigitalTwinState(): Promise<{
    assets: Record<string, any>;
    status: string;
    sector_filter?: string;
  }> {
    return api.get('/twin/state');
  },

  async resetDigitalTwin(): Promise<{ status: string; message: string }> {
    return api.post('/twin/reset');
  },

  async getMitigations(limit: number = 20): Promise<MitigationAction[]> {
    return api.get<MitigationAction[]>(`/mitigations?limit=${limit}`);
  },

  async getCityRisk(): Promise<any> {
    return api.get('/risk/city');
  },

  async getRiskHistory(limit: number = 50): Promise<any[]> {
    return api.get<any[]>(`/risk/history?limit=${limit}`);
  },

  async getThreats(limit: number = 50): Promise<Alert[]> {
    return api.get<Alert[]>(`/threats?limit=${limit}`);
  },

  // ── Unified SOC Command Center & Incident Workflows ──────────────
  async getSocDashboard(): Promise<SocDashboardData> {
    return api.get<SocDashboardData>('/soc/dashboard');
  },

  async getSocPosture(): Promise<any> {
    return api.get('/soc/posture');
  },

  async getSocIncidents(filters?: { status?: string; domain?: string; severity?: string; limit?: number }): Promise<any[]> {
    const params = new URLSearchParams();
    if (filters?.status && filters.status !== 'ALL') params.append('status', filters.status);
    if (filters?.domain && filters.domain !== 'ALL') params.append('domain', filters.domain);
    if (filters?.severity && filters.severity !== 'ALL') params.append('severity', filters.severity);
    if (filters?.limit) params.append('limit', String(filters.limit));
    return api.get<any[]>(`/soc/incidents?${params.toString()}`);
  },

  async createSocIncident(payload: any): Promise<any> {
    return api.post('/soc/incidents', payload);
  },

  async getSocIncidentDetail(incidentId: string): Promise<any> {
    return api.get(`/soc/incidents/${incidentId}`);
  },

  async assignAnalyst(incidentId: string, analyst: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/assign`, { analyst });
  },

  async addEvidence(incidentId: string, data: { evidence_type: string; description: string; artifact_ref?: string; hash_value?: string }): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/evidence`, data);
  },

  async addNotes(incidentId: string, note: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/notes`, { note });
  },

  async containIncident(incidentId: string, containment_action: string, notes?: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/contain`, { containment_action, notes });
  },

  async escalateIncident(incidentId: string, escalation_level: string, reason?: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/escalate`, { escalation_level, reason });
  },

  async resolveIncident(incidentId: string, resolution_summary: string, root_cause?: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/resolve`, { resolution_summary, root_cause });
  },

  async markFalsePositive(incidentId: string, reason: string): Promise<any> {
    return api.post(`/soc/incidents/${incidentId}/false-positive`, { reason });
  },

  async getIncidentTimelines(incidentId: string): Promise<IncidentTimelinesData> {
    return api.get<IncidentTimelinesData>(`/soc/incidents/${incidentId}/timelines`);
  },

  async getAttackChains(limit: number = 50): Promise<any[]> {
    return api.get<any[]>(`/soc/attack-chains?limit=${limit}`);
  },

  async getCrossDomainCorrelation(window_hours: number = 24.0): Promise<any[]> {
    return api.get<any[]>(`/soc/cross-domain-correlation?window_hours=${window_hours}`);
  },

  async correlateEvents(events: any[], window_hours: number = 24.0): Promise<any[]> {
    return api.post<any[]>('/soc/correlate', { events, window_hours, create_incident: true });
  }
};
