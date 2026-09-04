export type RoleId =
  | 'admin'
  | 'superadmin'
  | 'soc_analyst'
  | 'analyst'
  | 'health_operator'
  | 'doctor'
  | 'nurse'
  | 'hospital_admin'
  | 'hospital_security'
  | 'traffic_operator'
  | 'traffic_supervisor'
  | 'traffic_police'
  | 'signal_technician'
  | 'emergency_commander'
  | 'emergency_coordinator'
  | 'finance_investigator'
  | 'fraud_analyst'
  | 'aml_analyst'
  | 'risk_analyst'
  | 'viewer'
  | 'auditor'
  | string;

export interface User {
  id?: string;
  username: string;
  role: RoleId;
  full_name?: string;
  is_active?: boolean;
  last_login_at?: string;
  department?: string;
  token?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role: RoleId;
  username: string;
}

export interface UserCapabilities {
  can_override_signals: boolean;
  can_dispatch_ambulances: boolean;
  can_view_patient_records: boolean;
  can_edit_patient_records: boolean;
  can_freeze_accounts: boolean;
  can_execute_mitigations: boolean;
  can_inject_simulations: boolean;
  can_edit_policies: boolean;
  is_admin: boolean;
  is_read_only: boolean;
}

export interface CapabilitiesResponse {
  username: string;
  role: RoleId;
  sector: 'global' | 'healthcare' | 'transport' | 'finance' | 'emergency' | 'threat_ops' | string;
  capabilities: UserCapabilities;
  allowed_pages: string[];
  permissions: Record<string, string[]>;
}

export interface SectorPersona {
  id: string;
  name: string;
  sector: string;
  sector_name: string;
  username: string;
  badge_color: string;
  icon: string;
  landing_page: string;
  allowed_pages: string[];
  description: string;
}
