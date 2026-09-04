import { UserCapabilities } from './auth';

export type WorkflowUrgency = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type DutyStatus = 'ACTIVE_DUTY' | 'ON_CALL' | 'INCIDENT_RESPONSE' | 'STANDBY';

export interface PriorityTask {
  id: string;
  title: string;
  subtitle: string;
  urgency: WorkflowUrgency;
  slaMinutes?: number;
  category: string;
  actionLabel?: string;
  payload?: any;
}

export interface ContextMetric {
  label: string;
  value: string | number;
  status?: string;
  trend?: string;
}

export interface WorkflowAction {
  id: string;
  label: string;
  description: string;
  icon: string;
  variant?: 'primary' | 'danger' | 'warning' | 'success' | 'outline';
  requiredCapability?: keyof UserCapabilities;
  confirmMessage?: string;
  successFeedback?: string;
  payload?: any;
}

export interface ApprovalItem {
  id: string;
  title: string;
  submittedBy: string;
  submittedAt: string;
  reason: string;
  approverRole: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  riskScore?: number;
}

export interface EmergencyProcedure {
  name: string;
  trigger: string;
  sopSteps: string[];
  failsafeAction: string;
  escalationContact: string;
}

export interface WorkflowDefinition {
  roleId: string;
  roleName: string;
  domain: 'HEALTHCARE' | 'TRAFFIC' | 'FINANCE' | 'SECURITY';
  department: string;
  dutyStatus: DutyStatus;
  summary: string;
  q1_immediate: {
    headline: string;
    tasks: PriorityTask[];
  };
  q2_information: {
    headline: string;
    metrics: ContextMetric[];
    keyContextList: { label: string; value: string }[];
  };
  q3_actions: {
    headline: string;
    actions: WorkflowAction[];
  };
  q4_approvals: {
    headline: string;
    items: ApprovalItem[];
  };
  q5_escalation: {
    headline: string;
    procedures: EmergencyProcedure[];
  };
}
