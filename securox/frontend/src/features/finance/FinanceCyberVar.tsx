import React, { useState, useEffect } from 'react';
import { financeService } from '../../services/financeService';
import {
  FinanceBranch,
  FinanceCustomer,
  FinanceAccount,
  FinanceTransaction,
  FinanceFraudCase,
  FinanceAmlFinding,
  CyberVarMetrics,
  SecurityEvent,
  SecurityEventStats,
  FinancePersona,
  FinancePersonaRole
} from '../../types/finance';
import { OverviewSubsystem } from './subsystems/OverviewSubsystem';
import { AccountsBranchesSubsystem } from './subsystems/AccountsBranchesSubsystem';
import { TransactionPipelineSubsystem } from './subsystems/TransactionPipelineSubsystem';
import { FraudInvestigationSubsystem } from './subsystems/FraudInvestigationSubsystem';
import { AmlContagionSubsystem } from './subsystems/AmlContagionSubsystem';
import { CyberVarSubsystem } from './subsystems/CyberVarSubsystem';
import { UniversalEventFabricSubsystem } from './subsystems/UniversalEventFabricSubsystem';
import {
  Landmark,
  UserCheck,
  Shield,
  Layers,
  Send,
  ShieldAlert,
  Network,
  TrendingDown,
  Radio,
  Lock,
  RefreshCw
} from 'lucide-react';

const PERSONAS: FinancePersona[] = [
  {
    role: 'customer',
    username: 'customer',
    name: 'Tony Stark',
    title: 'Industrialist Account Holder',
    scopeDescription: 'Customer scope: View and transact on own accounts only.',
    isReadOnly: false
  },
  {
    role: 'teller',
    username: 'teller',
    name: 'Daniel Wu',
    title: 'Branch Vault & Cashier Officer',
    branchId: 'BR-01',
    scopeDescription: 'Branch scope: Process customer deposits/withdrawals for Metro Central.',
    isReadOnly: false
  },
  {
    role: 'branch_manager',
    username: 'branch_manager',
    name: 'Anita Roy',
    title: 'Metro Central Branch Manager',
    branchId: 'BR-01',
    scopeDescription: 'Branch scope: Manage branch accounts, limits, and approval workflows.',
    isReadOnly: false
  },
  {
    role: 'fraud_analyst',
    username: 'fraud_analyst',
    name: 'Sarah Connor',
    title: 'Lead Financial Fraud Hunter',
    scopeDescription: 'Security scope: Investigate suspicious outflows, decide cases, quarantine accounts.',
    isReadOnly: false
  },
  {
    role: 'aml_analyst',
    username: 'aml_analyst',
    name: 'James Bond',
    title: 'Anti-Money Laundering Lead',
    scopeDescription: 'Security scope: Graph contagion analysis, mule detection, and SAR filings.',
    isReadOnly: false
  },
  {
    role: 'risk_analyst',
    username: 'risk_analyst',
    name: 'Peter Parker',
    title: 'Treasury Cyber-VaR Specialist',
    scopeDescription: 'Risk scope: Parametric & Monte Carlo exposure estimation and stress testing.',
    isReadOnly: false
  },
  {
    role: 'compliance_officer',
    username: 'compliance_officer',
    name: 'Diana Prince',
    title: 'Chief Regulatory Compliance Officer',
    scopeDescription: 'Compliance scope: Review regulatory evidence, audit trails, and SAR compliance.',
    isReadOnly: false
  },
  {
    role: 'auditor',
    username: 'auditor',
    name: 'Clark Kent',
    title: 'Independent Regulatory Auditor',
    scopeDescription: 'Auditor scope: STRICTLY READ-ONLY across all financial entities and logs.',
    isReadOnly: true
  }
];

export const FinanceCyberVar: React.FC = () => {
  const [activePersona, setActivePersona] = useState<FinancePersona>(PERSONAS[3]); // Default: Fraud Analyst
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [selectedBranchId, setSelectedBranchId] = useState<string>('ALL');

  // Data states
  const [overviewData, setOverviewData] = useState<any>(null);
  const [branches, setBranches] = useState<FinanceBranch[]>([]);
  const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
  const [transactions, setTransactions] = useState<FinanceTransaction[]>([]);
  const [fraudCases, setFraudCases] = useState<FinanceFraudCase[]>([]);
  const [amlFindings, setAmlFindings] = useState<FinanceAmlFinding[]>([]);
  const [cyberVar, setCyberVar] = useState<CyberVarMetrics | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [eventStats, setEventStats] = useState<SecurityEventStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [ov, br, acc, tx, fc, aml, cv, ev, evs] = await Promise.all([
        financeService.getOverview().catch(() => null),
        financeService.getBranches().catch(() => []),
        financeService.getAccounts().catch(() => []),
        financeService.getTransactions(undefined, undefined, undefined, 50).catch(() => []),
        financeService.getFraudCases().catch(() => []),
        financeService.getAmlFindings().catch(() => []),
        financeService.getCyberVar(1.0).catch(() => null),
        financeService.getSecurityEvents({ limit: 50 }).catch(() => []),
        financeService.getSecurityEventStats().catch(() => null)
      ]);

      setOverviewData(ov);
      setBranches(br);
      setAccounts(acc);
      setTransactions(tx);
      setFraudCases(fc);
      setAmlFindings(aml);
      setCyberVar(cv);
      setEvents(ev);
      setEventStats(evs);
    } catch (err) {
      console.error('Failed to load finance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [activePersona]);

  return (
    <div className="space-y-6 pb-12">
      {/* 1-Click Stakeholder Persona Switcher */}
      <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-blue-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              1-Click Stakeholder Persona Switcher
            </h2>
          </div>
          {activePersona.isReadOnly && (
            <span className="text-xs px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              STRICTLY READ-ONLY AUDIT MODE
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {PERSONAS.map(p => {
            const isSelected = activePersona.role === p.role;
            return (
              <button
                key={p.role}
                onClick={() => setActivePersona(p)}
                className={`p-2.5 rounded-lg border text-left transition ${
                  isSelected
                    ? 'bg-blue-600 border-blue-400 text-white shadow-lg shadow-blue-500/20'
                    : 'bg-slate-800/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="text-[11px] font-bold truncate">{p.name}</div>
                <div className="text-[9px] opacity-80 truncate">{p.title}</div>
              </button>
            );
          })}
        </div>

        <div className="text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <span className="font-semibold text-white">{activePersona.name} ({activePersona.role}):</span>{' '}
          {activePersona.scopeDescription}
        </div>
      </div>

      {/* Subsystems Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {[
          { id: 'overview', label: 'Overview', icon: Landmark },
          { id: 'accounts', label: 'Accounts & Branches', icon: Layers },
          { id: 'transactions', label: 'Transaction Pipeline', icon: Send },
          { id: 'cases', label: 'Fraud Investigation', icon: ShieldAlert },
          { id: 'aml', label: 'AML Graph Contagion', icon: Network },
          { id: 'cybervar', label: 'Cyber-VaR Engine', icon: TrendingDown },
          { id: 'events', label: 'Central Event Fabric', icon: Radio }
        ].map(tab => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
                isSelected
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Active Subsystem View */}
      {activeTab === 'overview' && (
        <OverviewSubsystem
          overviewData={overviewData}
          cyberVar={cyberVar}
          onNavigateTab={setActiveTab}
        />
      )}

      {activeTab === 'accounts' && (
        <AccountsBranchesSubsystem
          branches={branches}
          accounts={accounts}
          activePersonaRole={activePersona.role}
          selectedBranchId={selectedBranchId}
          onSelectBranchId={setSelectedBranchId}
        />
      )}

      {activeTab === 'transactions' && (
        <TransactionPipelineSubsystem
          transactions={transactions}
          accounts={accounts}
          activePersonaRole={activePersona.role}
          isReadOnly={activePersona.isReadOnly}
          onSubmitTransaction={payload => financeService.submitTransaction(payload)}
          onRefresh={loadAllData}
        />
      )}

      {activeTab === 'cases' && (
        <FraudInvestigationSubsystem
          cases={fraudCases}
          activePersonaRole={activePersona.role}
          isReadOnly={activePersona.isReadOnly}
          onDecideCase={(caseId, payload) => financeService.decideFraudCase(caseId, payload)}
          onRefresh={loadAllData}
        />
      )}

      {activeTab === 'aml' && (
        <AmlContagionSubsystem
          findings={amlFindings}
          activePersonaRole={activePersona.role}
          isReadOnly={activePersona.isReadOnly}
          onAnalyzeAccount={accId => financeService.analyzeAmlNetwork(accId)}
          onFileSar={(fId, ref) => financeService.fileSarReport(fId, ref)}
          onRefresh={loadAllData}
        />
      )}

      {activeTab === 'cybervar' && (
        <CyberVarSubsystem
          cyberVar={cyberVar}
          onRefreshMultiplier={async mult => {
            const updated = await financeService.getCyberVar(mult);
            setCyberVar(updated);
          }}
        />
      )}

      {activeTab === 'events' && (
        <UniversalEventFabricSubsystem
          events={events}
          stats={eventStats}
          onRefresh={loadAllData}
        />
      )}
    </div>
  );
};
