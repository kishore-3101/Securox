export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED' | string;

export interface Alert {
  id: string;
  timestamp: string;
  asset: string;
  source_ip?: string;
  dest_ip?: string;
  attack_type: string;
  severity: Severity;
  anomaly_score?: number;
  confidence?: number;
  status?: string;
  description?: string;
  mitigation_status?: string;
}

export interface Incident {
  id: string;
  incident_id?: string;
  title?: string;
  asset: string;
  severity: Severity;
  attack_type: string;
  status: IncidentStatus;
  detected_at?: string;
  resolved_at?: string;
  assigned_to?: string;
  summary?: string;
  impact_score?: number;
  containment_action?: string;
}

export interface DigitalTwinNode {
  id: string;
  name: string;
  sector: 'transport' | 'healthcare' | 'finance' | 'water' | 'energy' | 'telecom' | 'public_safety' | string;
  ip: string;
  status: 'HEALTHY' | 'WARNING' | 'COMPROMISED' | 'ISOLATED' | string;
  risk_score: number; // 0 - 100
  active_alerts: number;
  anomaly_score: number;
  coordinates?: [number, number];
  dependencies: string[];
  last_telemetry?: string;
}

export interface Campaign {
  id: string;
  name: string;
  threat_actor: string;
  tactic: string;
  technique: string;
  mitre_id: string;
  target_sector: string;
  severity: Severity;
  kill_chain_stage: 'Recon' | 'Initial Access' | 'Execution' | 'Persistence' | 'Lateral Movement' | 'Exfiltration' | 'Impact' | string;
  status: string;
  first_seen: string;
  indicators: string[];
}

export interface CityRiskMetric {
  composite_score: number; // 0 - 100
  trend: 'UP' | 'DOWN' | 'STABLE';
  sectors: {
    healthcare: number;
    traffic: number;
    finance: number;
    water: number;
    energy: number;
  };
  loss_exposure_million_usd: number;
  active_threats_count: number;
  contained_count: number;
  formula: {
    base_threat: number;
    cross_sector_multiplier: number;
    iomt_weight: number;
    traffic_weight: number;
    finance_weight: number;
  };
}

export interface MitigationAction {
  id: string;
  action: string;
  target_id: string;
  target_type: 'ip' | 'device' | 'signal' | 'account' | 'node';
  initiated_by: string;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  timestamp: string;
  details?: string;
}
