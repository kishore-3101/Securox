export interface AttackScenario {
  id: string; // e.g., '01', '02', '03', '04', '05', '06'
  scenario_number: string;
  name: string;
  title: string;
  sector: string;
  target_asset: string;
  attack_vector: string;
  description: string;
  mitre_technique: string;
  severity: 'MEDIUM' | 'HIGH' | 'CRITICAL';
  estimated_blast_radius_pct: number;
  expected_financial_loss_million: number;
  is_active: boolean;
}

export interface WhatIfNode {
  id: string;
  name: string;
  sector: string;
  initial_state: 'OPERATIONAL' | 'DEGRADED' | 'FAILED';
  cascade_probability: number;
  dependent_nodes: string[];
  failure_mode: string;
  mitigation_sla_minutes: number;
}

export interface SimulationState {
  is_running: boolean;
  active_scenario_id: string | null;
  scenario_started_at: string | null;
  elapsed_seconds: number;
  affected_assets_count: number;
  current_city_risk: number;
  timeline: {
    second: number;
    event: string;
    sector: string;
    severity: string;
  }[];
}

// ═══════════════════════════════════════════════════════════════════
// DEMO CENTER & 9-STAGE PROGRESSION INTERFACES
// ═══════════════════════════════════════════════════════════════════

export type DemoCategory = 'HEALTHCARE' | 'TRAFFIC' | 'FINANCE' | 'CROSS_DOMAIN';
export type DemoMode = 'NORMAL' | 'ATTACK' | 'RECOVERY';
export type DemoStage =
  | 'EVENT'
  | 'DETECTION'
  | 'AI_ANALYSIS'
  | 'RISK'
  | 'POLICY'
  | 'ACTION'
  | 'INCIDENT'
  | 'INVESTIGATION'
  | 'RECOVERY';

export interface StakeholderInfo {
  name: string;
  role: string;
  department: string;
  contact: string;
  pager: string;
  channel: string;
}

export interface AttackerAttemptInfo {
  summary: string;
  objective: string;
  vector: string;
  severity: string;
}

export interface SystemPreventedInfo {
  summary: string;
  action: string;
  protected_asset: string;
}

export interface DecisionReasonInfo {
  composite_score: number;
  tier: string;
  factors: Array<{
    name: string;
    points: number;
    source: string;
    severity?: string;
  }>;
  uncertainty?: number;
}

export interface DemoCenterStatusResponse {
  session_id: string;
  status: 'IDLE' | 'RUNNING' | 'PAUSED' | 'COMPLETED';
  category: DemoCategory;
  mode: DemoMode;
  speed: number;
  current_stage: DemoStage;
  current_stage_index: number;
  stages: string[];
  risk: {
    current_score: number;
    tier: string;
    is_increasing: boolean;
    is_decreasing: boolean;
    trend: Array<{
      timestamp: string;
      risk_score: number;
      stage: string;
    }>;
  };
  stakeholder: StakeholderInfo;
  attacker_attempt: AttackerAttemptInfo;
  system_prevented: SystemPreventedInfo;
  decision_reason: DecisionReasonInfo;
  ai_inference?: any;
  safety_evaluation?: any;
  active_incident?: any;
  cross_domain_cluster?: any;
  stage_data: Record<string, any>;
  events_timeline: Array<{
    id: string;
    timestamp: string;
    domain: string;
    action: string;
    asset: string;
    summary: string;
  }>;
  timestamp: string;
}
