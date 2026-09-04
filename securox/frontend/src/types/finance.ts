// Securox Financial Security & Central Security Event Fabric Types

export type ModelAttribution = 'LIVE INFERENCE' | 'CACHED RESULT' | 'SIMULATION' | 'DEMO';

export type FinancePersonaRole =
  | 'customer'
  | 'teller'
  | 'relationship_manager'
  | 'branch_manager'
  | 'fraud_analyst'
  | 'aml_analyst'
  | 'risk_analyst'
  | 'compliance_officer'
  | 'auditor'
  | 'admin';

export interface FinancePersona {
  role: FinancePersonaRole;
  username: string;
  name: string;
  title: string;
  branchId?: string;
  scopeDescription: string;
  isReadOnly: boolean;
}

export interface FinanceBranch {
  id: string;
  code: string;
  name: string;
  city: string;
  region: string;
  manager_id: string;
  daily_volume_limit: number;
  current_volume: number;
  status: 'ACTIVE' | 'AUDIT_HOLD' | 'INACTIVE';
}

export interface FinanceCustomer {
  id: string;
  name: string;
  pan_or_ssn: string;
  kyc_status: 'VERIFIED' | 'PENDING' | 'FLAGGED';
  risk_rating: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  phone?: string;
  email?: string;
  branch_id: string;
  created_at: string;
  accounts?: FinanceAccount[];
}

export interface FinanceAccount {
  id: string;
  customer_id: string;
  customer_name?: string;
  account_number: string;
  branch_id: string;
  branch_name?: string;
  account_type: 'SAVINGS' | 'CURRENT' | 'ESCROW' | 'TREASURY';
  balance: number;
  currency: string;
  status: 'ACTIVE' | 'FROZEN' | 'RESTRICTED';
  risk_score: number;
  created_at: string;
}

export interface FinanceTransaction {
  id: string;
  account_id: string;
  account_number?: string;
  customer_name?: string;
  counterparty_account: string;
  amount: number;
  channel: string;
  currency: string;
  timestamp: string;
  ip_address?: string;
  device_id?: string;
  location?: string;
  status: 'SETTLED' | 'BLOCKED' | 'FLAGGED_AML' | 'FLAGGED_FRAUD';
  risk_score: number;
  model_attribution: ModelAttribution;
  flag_reason?: string;
  created_at: string;
}

export interface FinanceFraudCase {
  id: string;
  case_number: string;
  transaction_id?: string;
  customer_id: string;
  account_id: string;
  title: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'INVESTIGATING' | 'ESCALATED' | 'RESOLVED' | 'CLOSED';
  total_exposure_inr: number;
  assigned_analyst: string;
  decision?: string;
  decision_rationale?: string;
  resolution_notes?: string;
  opened_at: string;
  closed_at?: string;
  transaction?: FinanceTransaction;
  aml_findings?: FinanceAmlFinding[];
}

export interface FinanceAmlFinding {
  id: string;
  case_id?: string;
  finding_type: string;
  primary_account: string;
  counterparty_accounts: string[];
  mule_probability: number;
  hop_count: number;
  structuring_pattern?: string;
  graph_metrics: {
    degree_centrality?: number;
    inflow_transactions?: number;
    outflow_transactions?: number;
    velocity_spike_ratio?: number;
  };
  sar_filed: number;
  sar_reference?: string;
  detected_at: string;
}

export interface CyberVarMetrics {
  timestamp: string;
  methodology: string;
  model_attribution: ModelAttribution;
  portfolio_total_balance_inr: number;
  quarantined_frozen_inr: number;
  open_case_exposure_inr: number;
  high_risk_transaction_volume_inr: number;
  cyber_var_95_1day_inr: number;
  cyber_var_99_1day_inr: number;
  expected_shortfall_cvar_inr: number;
  stress_scenarios: Array<{
    name: string;
    probability: number;
    projected_loss_inr: number;
    status: string;
  }>;
}

export interface SecurityEvent {
  event_id: string;
  timestamp: string;
  domain: string;
  organization: string;
  user: string;
  role: string;
  device?: string;
  ip?: string;
  location?: string;
  resource: string;
  action: string;
  result: string;
  risk: number;
  metadata: Record<string, any>;
}

export interface SecurityEventStats {
  total_events: number;
  high_risk_events: number;
  domains: Record<string, number>;
  top_actions: Record<string, number>;
  results: Record<string, number>;
  recent: SecurityEvent[];
}
