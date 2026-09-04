import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { usePermissions } from '../../hooks/usePermissions';
import { useWebSocket } from '../../hooks/useWebSocket';
import { RiskPill } from '../common/RiskPill';
import {
  Radio,
  UserCheck,
  ChevronDown,
  LogOut,
  Shield,
  Stethoscope,
  Ambulance,
  Car,
  Landmark,
  Eye,
  RefreshCw,
  Search,
  X,
  Sparkles,
  HeartPulse,
  Activity,
  Briefcase,
} from 'lucide-react';

interface RoleEntry {
  id: string;
  name: string;
  domain: 'HEALTHCARE' | 'TRAFFIC' | 'FINANCE' | 'SECURITY';
  summary: string;
}

const ALL_ROLES: RoleEntry[] = [
  // HEALTHCARE (12)
  { id: 'patient', name: 'Patient (Self-Service)', domain: 'HEALTHCARE', summary: 'Appointments, vitals telemetry, digital prescriptions & bedside nurse call.' },
  { id: 'reception', name: 'Reception & Triage Desk', domain: 'HEALTHCARE', summary: 'Patient intake, bed allocation, insurance verification & triage assignment.' },
  { id: 'nurse', name: 'Ward / ICU Nurse', domain: 'HEALTHCARE', summary: 'Bedside telemetry tracking, medication administration & stat doctor escalations.' },
  { id: 'doctor', name: 'Doctor (Attending Clinician)', domain: 'HEALTHCARE', summary: 'Inpatient rounds, clinical diagnosis notes, BOLA checks & pharmacotherapy.' },
  { id: 'lab_technician', name: 'Lab Technician', domain: 'HEALTHCARE', summary: 'Phlebotomy results, pathology specimen testing & stat diagnostic sign-offs.' },
  { id: 'pharmacist', name: 'Clinical Pharmacist', domain: 'HEALTHCARE', summary: 'Prescription dispensing, drug-drug interaction audits & controlled substance locks.' },
  { id: 'billing_staff', name: 'Medical Billing Specialist', domain: 'HEALTHCARE', summary: 'Cashless insurance claims, itemized tariff invoices & UPI settlement.' },
  { id: 'paramedic', name: 'Emergency Paramedic', domain: 'HEALTHCARE', summary: 'Pre-hospital cardiac telemetry, resuscitation & crash-site stabilization.' },
  { id: 'ambulance_driver', name: 'Ambulance Driver', domain: 'HEALTHCARE', summary: 'High-stress rapid navigation, 1-tap green corridor pre-emption & ER uplinks.' },
  { id: 'emergency_coordinator', name: 'Emergency Coordinator', domain: 'HEALTHCARE', summary: 'Multi-casualty incident dispatch, trauma bay routing & fleet coordination.' },
  { id: 'hospital_admin', name: 'Hospital Operations Director', domain: 'HEALTHCARE', summary: 'Bed census optimization, surgical schedule approvals & supply chain monitoring.' },
  { id: 'hospital_security', name: 'Hospital Security Specialist', domain: 'HEALTHCARE', summary: 'PACS/DICOM server protection, physical infant ward access & CCTV surveillance.' },

  // TRAFFIC (11)
  { id: 'citizen', name: 'Citizen (Public Transit & Alerts)', domain: 'TRAFFIC', summary: 'Live route congestion advisory, road closures & emergency traffic broadcasts.' },
  { id: 'traffic_operator', name: 'Traffic Operations Controller', domain: 'TRAFFIC', summary: 'Live signal overrides (SIG-01..06), green corridor dispatch & CCTV verification.' },
  { id: 'traffic_police', name: 'Traffic Enforcement Officer', domain: 'TRAFFIC', summary: 'On-scene road clearance, manual intersection control & VIP convoy dispatch.' },
  { id: 'traffic_supervisor', name: 'Traffic Dispatch Supervisor', domain: 'TRAFFIC', summary: 'Citywide SCADA health, incident escalation & cross-sector municipal liaison.' },
  { id: 'camera_operator', name: 'CCTV & ANPR Operator', domain: 'TRAFFIC', summary: 'Gantry plate recognition, optical speed violations & roadside obstruction spotting.' },
  { id: 'signal_technician', name: 'Signal & SCADA Technician', domain: 'TRAFFIC', summary: 'PLC firmware maintenance, loop detector calibrations & fail-safe amber locks.' },
  { id: 'emergency_traffic', name: 'Emergency Route Coordinator', domain: 'TRAFFIC', summary: 'Dedicated ambulance corridor pre-emption & fire tender corridor orchestration.' },
  { id: 'road_maintenance', name: 'Road Maintenance Engineer', domain: 'TRAFFIC', summary: 'Pothole telemetry, gantry repairs, lane closures & hazard clearance crews.' },
  { id: 'transport_authority', name: 'Transport Authority Director', domain: 'TRAFFIC', summary: 'Transit policy compliance, arterial flow analytics & congestion tariff reviews.' },
  { id: 'traffic_analyst', name: 'Traffic Modeler & Analyst', domain: 'TRAFFIC', summary: 'Rush-hour predictive modeling, bottleneck AI diagnostics & corridor optimization.' },
  { id: 'traffic_cybersecurity', name: 'Traffic Cybersecurity Specialist', domain: 'TRAFFIC', summary: 'SCADA PLC intrusion detection, FASTag cryptographic spoofing & sensor integrity.' },

  // FINANCE (10)
  { id: 'customer', name: 'Customer (Banking & UPI)', domain: 'FINANCE', summary: 'Self-service account management, wire transfers & card transaction security.' },
  { id: 'teller', name: 'Branch Teller / Cashier', domain: 'FINANCE', summary: 'Cash handling, counter deposits, high-value wire dual-approval & basic KYC.' },
  { id: 'relationship_manager', name: 'Corporate Relationship Manager', domain: 'FINANCE', summary: 'Commercial credit lines, municipal bond escrow & corporate client oversight.' },
  { id: 'branch_manager', name: 'Branch General Manager', domain: 'FINANCE', summary: 'High-value wire release approvals, vault access controls & branch compliance.' },
  { id: 'fraud_analyst', name: 'Real-Time Fraud Analyst', domain: 'FINANCE', summary: 'Pre-settlement escrow holds, 3-hop mule graph traversal & account freezes.' },
  { id: 'aml_analyst', name: 'AML Compliance Analyst', domain: 'FINANCE', summary: 'Suspicious Activity Reports (SAR), structuring pattern flags & KYC investigations.' },
  { id: 'risk_analyst', name: 'Financial Cyber-VaR Analyst', domain: 'FINANCE', summary: 'Capital at Risk simulations, SWIFT attack exposure & liquidity reserve stress tests.' },
  { id: 'compliance_officer', name: 'Chief Compliance Officer', domain: 'FINANCE', summary: 'RBI/FinCEN audit dossiers, AML sanction screenings & regulatory disclosures.' },
  { id: 'auditor', name: 'Auditor (Read-Only Independent)', domain: 'FINANCE', summary: 'Cryptographic immutable audit trails, access log verification & SOC2 compliance.' },
  { id: 'finance_admin', name: 'FinTech Platform Administrator', domain: 'FINANCE', summary: 'Banking gateway routing, liquidity clearing window controls & API token management.' },

  // SECURITY (4)
  { id: 'soc_analyst', name: 'SOC Tier-1 / Tier-2 Analyst', domain: 'SECURITY', summary: 'Live SIEM alert triage, MITRE ATT&CK kill-chain mapping & subnet isolation.' },
  { id: 'security_analyst', name: 'Threat Hunter & Forensics', domain: 'SECURITY', summary: 'Malware sandbox analysis, memory dump forensics & zero-day indicator correlation.' },
  { id: 'security_manager', name: 'SOC Incident Commander', domain: 'SECURITY', summary: 'Enterprise incident escalation, crisis declaration & regulatory breach disclosure.' },
  { id: 'admin', name: 'Global CISO & Super Admin', domain: 'SECURITY', summary: 'Full authority across platform configuration, cross-domain RBAC & emergency kill switches.' },
];

export const Topbar: React.FC = () => {
  const { user, role, switchRole, logout } = useAuth();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();

  const [modalOpen, setModalOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [domainFilter, setDomainFilter] = useState<'ALL' | 'HEALTHCARE' | 'TRAFFIC' | 'FINANCE' | 'SECURITY'>('ALL');

  const filteredRoles = ALL_ROLES.filter((r) => {
    const matchesDomain = domainFilter === 'ALL' || r.domain === domainFilter;
    const matchesQuery =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesQuery;
  });

  const handleSelectRole = async (targetRole: string) => {
    setSwitching(true);
    try {
      await switchRole(targetRole);
      navigate('/workspace');
    } catch (err) {
      console.error('Failed to switch role:', err);
    } finally {
      setSwitching(false);
      setModalOpen(false);
    }
  };

  const domainColors = {
    HEALTHCARE: 'border-rose-500/30 text-rose-400 bg-rose-500/10',
    TRAFFIC: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10',
    FINANCE: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    SECURITY: 'border-sky-500/30 text-sky-400 bg-sky-500/10',
  };

  return (
    <header className="h-16 bg-slate-950/80 border-b border-slate-800 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Left side: System status & telemetry */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              isConnected ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]' : 'bg-rose-500'
            }`}
            title={isConnected ? 'Real-time WebSocket feed active' : 'WebSocket connecting...'}
          />
          <span className="text-xs font-mono text-slate-400 hidden sm:inline">
            {isConnected ? 'STREAMING ACTIVE' : 'CONNECTING...'}
          </span>
        </div>

        <div className="h-4 w-[1px] bg-slate-800" />

        <RiskPill />
      </div>

      {/* Right side: 35-Role Switcher & User Profile */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setModalOpen(true)}
          disabled={switching}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-500 text-xs font-mono text-slate-200 transition shadow-sm"
        >
          {switching ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />
          ) : (
            <UserCheck className="w-3.5 h-3.5 text-sky-400" />
          )}
          <span className="hidden sm:inline text-slate-400">ROLE:</span>
          <span className="font-bold text-sky-400 uppercase tracking-wide">{role}</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 font-mono hidden md:inline">
            35 Available
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </button>

        {/* User Identity Chip */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-mono text-xs text-slate-300 font-bold">
            {(user?.username || 'A')[0].toUpperCase()}
          </div>
          <span className="text-xs font-mono text-slate-300 hidden md:inline">
            {user?.username || 'admin'}
          </span>
          <button
            onClick={logout}
            title="Sign Out"
            className="p-1 text-slate-400 hover:text-rose-400 transition ml-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 35-ROLE INTERACTIVE SELECTION MODAL */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-fadeIn font-sans">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold font-mono text-slate-100 flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-sky-400" />
                  Select Stakeholder Persona (35 Integrated Roles)
                </h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">
                  Switches active RBAC credentials, backend permissions & launches role-specific 5-questions workflow.
                </p>
              </div>

              <button
                onClick={() => setModalOpen(false)}
                className="p-2 text-slate-400 hover:text-slate-200 transition rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Filter Controls */}
            <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex flex-col sm:flex-row items-center justify-between gap-3">
              {/* Search Bar */}
              <div className="relative w-full sm:w-72">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter by role or task..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Domain Tabs */}
              <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto text-xs font-mono">
                {(['ALL', 'HEALTHCARE', 'TRAFFIC', 'FINANCE', 'SECURITY'] as const).map((dom) => (
                  <button
                    key={dom}
                    onClick={() => setDomainFilter(dom)}
                    className={`px-3 py-1.5 rounded-lg border transition ${
                      domainFilter === dom
                        ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 font-bold'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {dom}
                  </button>
                ))}
              </div>
            </div>

            {/* Modal Role Cards Grid */}
            <div className="flex-1 overflow-y-auto p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredRoles.map((r) => {
                const isCurrent = (role || '').toLowerCase() === r.id.toLowerCase();
                const colorClass = domainColors[r.domain];

                return (
                  <button
                    key={r.id}
                    onClick={() => handleSelectRole(r.id)}
                    className={`p-3.5 rounded-xl border text-left font-mono transition-all flex flex-col justify-between ${
                      isCurrent
                        ? 'bg-sky-500/15 border-sky-500 ring-1 ring-sky-500/50 shadow-md'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase ${colorClass}`}>
                          {r.domain}
                        </span>
                        {isCurrent && (
                          <span className="text-[10px] text-sky-400 font-bold">● ACTIVE</span>
                        )}
                      </div>

                      <h4 className="text-xs font-bold text-slate-100 mt-2">{r.name}</h4>
                      <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                        {r.summary}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-2 mt-2 border-t border-slate-800/60 text-[9px] text-slate-500">
                      <span>id: {r.id}</span>
                      <span className="text-sky-400 font-bold flex items-center gap-1">
                        Select Role →
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
