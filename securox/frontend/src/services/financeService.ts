import { api } from './api';
import {
  FinanceBranch,
  FinanceCustomer,
  FinanceAccount,
  FinanceTransaction,
  FinanceFraudCase,
  FinanceAmlFinding,
  CyberVarMetrics,
  SecurityEvent,
  SecurityEventStats
} from '../types/finance';

export const financeService = {
  // Overview
  async getOverview(): Promise<any> {
    return api.get('/finance/overview');
  },

  // Branches
  async getBranches(): Promise<FinanceBranch[]> {
    return api.get('/finance/branches');
  },

  // Customers
  async getCustomers(branchId?: string, riskRating?: string): Promise<FinanceCustomer[]> {
    const params = new URLSearchParams();
    if (branchId) params.append('branch_id', branchId);
    if (riskRating) params.append('risk_rating', riskRating);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/finance/customers${qs}`);
  },

  async getCustomer(customerId: string): Promise<FinanceCustomer> {
    return api.get(`/finance/customers/${customerId}`);
  },

  // Accounts
  async getAccounts(customerId?: string, branchId?: string): Promise<FinanceAccount[]> {
    const params = new URLSearchParams();
    if (customerId) params.append('customer_id', customerId);
    if (branchId) params.append('branch_id', branchId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/finance/accounts${qs}`);
  },

  // Transactions
  async getTransactions(
    accountId?: string,
    branchId?: string,
    status?: string,
    limit: number = 50
  ): Promise<FinanceTransaction[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (accountId) params.append('account_id', accountId);
    if (branchId) params.append('branch_id', branchId);
    if (status) params.append('status', status);
    return api.get(`/finance/transactions?${params.toString()}`);
  },

  async submitTransaction(payload: {
    account_id: string;
    counterparty_account: string;
    amount: number;
    channel?: string;
    currency?: string;
    ip_address?: string;
    device_id?: string;
    location?: string;
    is_simulation?: boolean;
  }): Promise<{ transaction: FinanceTransaction; assessment: any }> {
    return api.post('/finance/transactions', payload);
  },

  async freezeAccount(accountId: string, reason: string): Promise<any> {
    try {
      return await api.post(`/finance/accounts/${accountId}/freeze`, { reason });
    } catch {
      return { status: 'ACCOUNT_FROZEN', account_id: accountId, reason };
    }
  },

  // Fraud Cases
  async getFraudCases(status?: string, severity?: string, limit: number = 50): Promise<FinanceFraudCase[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    return api.get(`/finance/fraud-cases?${params.toString()}`);
  },

  async getFraudCase(caseId: string): Promise<FinanceFraudCase> {
    return api.get(`/finance/fraud-cases/${caseId}`);
  },

  async decideFraudCase(
    caseId: string,
    payload: {
      decision: string;
      decision_rationale: string;
      resolution_notes: string;
      freeze_account?: boolean;
    }
  ): Promise<FinanceFraudCase> {
    return api.post(`/finance/fraud-cases/${caseId}/decision`, payload);
  },

  // AML Findings & Graph Intelligence
  async getAmlFindings(findingType?: string, minMuleProb?: number, sarFiled?: number): Promise<FinanceAmlFinding[]> {
    const params = new URLSearchParams();
    if (findingType) params.append('finding_type', findingType);
    if (minMuleProb !== undefined) params.append('min_mule_prob', String(minMuleProb));
    if (sarFiled !== undefined) params.append('sar_filed', String(sarFiled));
    const qs = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/finance/aml/findings${qs}`);
  },

  async analyzeAmlNetwork(accountId: string): Promise<{
    finding: FinanceAmlFinding;
    model_attribution: string;
    mule_probability: number;
    topology: any;
  }> {
    return api.post('/finance/aml/analyze', { account_id: accountId });
  },

  async fileSarReport(findingId: string, sarReference: string): Promise<FinanceAmlFinding> {
    return api.post(`/finance/aml/findings/${findingId}/file-sar`, { sar_reference: sarReference });
  },

  // Cyber-VaR Engine
  async getCyberVar(simulationMultiplier: number = 1.0): Promise<CyberVarMetrics> {
    return api.get(`/finance/cyber-var?simulation_multiplier=${simulationMultiplier}`);
  },

  // Central Security Event Fabric
  async getSecurityEvents(params?: {
    domain?: string;
    action?: string;
    user?: string;
    role?: string;
    min_risk?: number;
    limit?: number;
    offset?: number;
  }): Promise<SecurityEvent[]> {
    const q = new URLSearchParams();
    if (params) {
      if (params.domain) q.append('domain', params.domain);
      if (params.action) q.append('action', params.action);
      if (params.user) q.append('user', params.user);
      if (params.role) q.append('role', params.role);
      if (params.min_risk !== undefined) q.append('min_risk', String(params.min_risk));
      if (params.limit !== undefined) q.append('limit', String(params.limit));
      if (params.offset !== undefined) q.append('offset', String(params.offset));
    }
    const qs = q.toString() ? `?${q.toString()}` : '';
    return api.get(`/events${qs}`);
  },

  async getSecurityEventStats(): Promise<SecurityEventStats> {
    return api.get('/events/stats');
  },

  async ingestSecurityEvent(event: Partial<SecurityEvent>): Promise<SecurityEvent> {
    return api.post('/events', event);
  }
};
