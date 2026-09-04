# Securox — Granular RBAC + ABAC Policy Engine Specification

## 1. Permission Matrix & Stakeholder Taxonomy

The platform strictly rejects simplistic boolean admin checks (`if role == 'admin'`). Instead, every operation passes through a granular 5-tuple evaluation:
$$\text{Evaluation} = \langle \text{USER}, \text{ROLE}, \text{RESOURCE}, \text{ACTION}, \text{SCOPE} \rangle$$

### Supported Actions:
`VIEW`, `CREATE`, `UPDATE`, `DELETE`, `APPROVE`, `EXPORT`, `DOWNLOAD`, `DISPATCH`, `INVESTIGATE`, `BLOCK`, `RESOLVE`, `CONFIGURE`.

---

## 2. Multi-Domain Role Catalog (35+ Roles)

### A. Super Administration
- **`superadmin`**: Pan-city governance, system configuration, user provisioning, security policies. **Monitored and audited** on all actions.
- **`admin`**: CISO operations, global risk posture analytics, active incident response.

### B. Healthcare Roles (12 Roles)
| Role Name | Identifier | Primary Grants | Scope Restrictions |
| :--- | :--- | :--- | :--- |
| Hospital Admin | `hospital_admin` | Bed management, hospital security overview | Cannot alter clinical diagnosis |
| Doctor | `doctor` | View/Update clinical charts, diagnosis, Rx | **Assigned Inpatients Only** |
| Nurse | `nurse` | Record vitals, nursing notes, bed updates | Ward / Inpatient Scope |
| Ambulance Driver | `ambulance_driver` | Accept, GPS route, update mission status | **Zero clinical records access** |
| Paramedic | `paramedic` | Record emergency triage notes, vitals | En-route handover only |
| Reception / Admissions | `reception` | Patient registration, appointment booking | Demographic scope only |
| Pharmacist | `pharmacist` | Medication dispensing, inventory | Prescription records only |
| Lab Technologist | `lab_technician` | Upload verified specimen lab results | Assigned test orders only |
| Billing Coordinator | `billing_staff` | Create invoices, insurance claims | Zero clinical modification |
| Emergency Dispatcher | `emergency_coordinator` | Ambulance dispatch, triage routing | Fleet & bed capacity scope |
| Hospital IT Security | `hospital_security` | Health IT device trust, IoMT alerts | Hospital infrastructure scope |
| Patient | `patient` | Personal appointments, prescriptions, bills | **Own personal data only** |

### C. Smart Traffic Roles (11 Roles)
| Role Name | Identifier | Primary Grants | Scope Restrictions |
| :--- | :--- | :--- | :--- |
| Traffic Control Operator | `traffic_operator` | Signal timings, green corridors, map | TMC Operations Scope |
| Traffic Police Officer | `traffic_police` | Incident logging, roadside evidence | Enforcement scope |
| Traffic Supervisor | `traffic_supervisor` | Multi-zone overrides, escalations | Regional sector scope |
| CCTV Camera Operator | `camera_operator` | Camera health, live video feeds | **No traffic signal control** |
| Signal Field Tech | `signal_technician` | Hardware diagnostics, phase loops | Maintenance scope |
| Emergency Traffic Lead | `emergency_traffic` | Green corridor pre-emption dispatch | Emergency routing only |
| Road Maintenance Lead | `road_maintenance` | Work zones, lane closure updates | Physical obstruction scope |
| Transport Commissioner | `transport_authority` | City-wide mobility reports, trends | Executive aggregate scope |
| Traffic Data Analyst | `traffic_analyst` | Flow metrics, congestion modeling | Anonymized data scope |
| Traffic Cyber Officer | `traffic_cybersecurity` | SCADA anomaly defense, signal locks | SCADA / Network scope |
| Citizen | `citizen` | Congestion map, road closure alerts | Public alerts only |

### D. Finance & Banking Roles (11 Roles)
| Role Name | Identifier | Primary Grants | Scope Restrictions |
| :--- | :--- | :--- | :--- |
| Financial Risk Admin | `finance_admin` | Portfolio risk exposure, institutions | Governance scope |
| Branch Manager | `branch_manager` | Branch approvals, cashier oversight | Branch limits |
| Teller / Cashier | `teller` | Cash transactions, deposits | Limit: ₹50,000 / transaction |
| Relationship Manager | `relationship_manager` | Assigned client portfolios | Assigned accounts only |
| Lead Fraud Analyst | `fraud_analyst` | ML fraud scores, transaction graph, freeze | Investigation scope |
| AML Compliance Officer | `aml_analyst` | Structuring alerts, SAR filing | AML network scope |
| Treasury Cyber-VaR Analyst| `risk_analyst` | Systemic capital-at-risk analytics | Read-only risk models |
| Chief Compliance Officer | `compliance_officer` | Regulatory filings, policy changes | Compliance scope |
| SOC Threat Hunter | `soc_analyst` | Forensic XAI, MITRE ATT&CK | Cyber defense scope |
| Independent Auditor | `auditor` | Audit logs, immutable access records | **STRICTLY READ-ONLY** |
| Retail Customer | `customer` | Own account balance, transfer funds | **Own accounts only** |

---

## 3. ABAC Contextual Rules & Adaptive Escalation

The platform evaluates 7 contextual attributes on every access request:
1. **Device Trust**: Unknown or unregistered devices add $+25.0$ risk points.
2. **Impossible Travel**: Login velocity exceeding $800\text{ km/h}$ adds $+35.0$ risk points.
3. **Off-Hours Shift**: Operations between 23:00 and 04:00 add $+18.0$ risk points.
4. **Data Volume Spike**: Batch retrieval $>500$ records adds $+30.0$ risk points ($>50$ adds $+15.0$).
5. **Clinical Scope**: Accessing unassigned patient records adds $+28.0$ risk points.
6. **Network Trust**: Connections via Tor exit nodes add $+40.0$ risk points.
7. **Financial Threshold**: Transactions exceeding ₹100,000 add $+22.0$ risk points.

### Decision Matrix:
- **Risk 0 – 25 (LOW)**: `ALLOW` (Instant execution).
- **Risk 26 – 50 (MEDIUM)**: `ALLOW_MONITORED` (Logged with enhanced audit tracking).
- **Risk 51 – 75 (HIGH)**: `STEP_UP_AUTH` (Enforces secondary biometric / FIDO2 challenge).
- **Risk 76 – 100 (CRITICAL)**: `BLOCK` (Request severed in-flight + automated incident dispatched to SOC).
