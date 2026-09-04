# Securox — Smart City Digital Infrastructure Cyber Defense Architecture

## 1. System Overview
Securox is an enterprise-grade, multi-domain cybersecurity and adaptive access control platform protecting critical smart-city digital infrastructure across three foundational sectors:
1. **Healthcare**: Hospital Clinical Information Systems, Electronic Health Records (EHR), Medical IoMT devices, and Emergency Dispatch.
2. **Smart Traffic & Transport**: STIG Adaptive Traffic Signal Networks, ANPR Camera Grids, Computer Vision Edge Detections, and Emergency Green Corridors.
3. **Finance & Treasury**: Core Banking Gateways, Interbank SWIFT/RTGS Rails, Anti-Money Laundering (AML) Networks, and Municipal Treasury Accounts.

---

## 2. Core Conceptual Architecture

```
                    [ INBOUND ACCESS / TELEMETRY EVENT ]
                                    │
                                    ▼
                    [ LAYER 1: IDENTITY & AUTHENTICATION ]
                    (JWT + PBKDF2 Password Hashing + Device Fingerprint)
                                    │
                                    ▼
                    [ LAYER 2: ROLE-BASED ACCESS CONTROL (RBAC) ]
                    (35+ Role Matrix across Healthcare, Traffic, Finance)
                                    │
                                    ▼
                    [ LAYER 3: ATTRIBUTE-BASED ACCESS CONTROL (ABAC) ]
                    (Device Trust, Geolocation, Impossible Travel,
                     Shift Hours, Resource Scope, Data Volume)
                                    │
                                    ▼
                    [ LAYER 4: AI CYBER RISK ENGINE ]
                    (XGBoost Classifier + Isolation Forest Zero-Day +
                     Core-4 Consensus + TreeSHAP Feature Attributions)
                                    │
                                    ▼
                    [ LAYER 5: ADAPTIVE POLICY ENFORCEMENT ]
         ┌───────────────┬──────────────────┬─────────────────┬───────────────┐
         ▼               ▼                  ▼                 ▼               ▼
      [ ALLOW ]     [ ALLOW + ]        [ STEP-UP / ]     [ RESTRICT / ]   [ IMMUTABLE ]
     (Risk 0-25)     MONITORED           CHALLENGE           BLOCK          AUDIT LOG
                    (Risk 26-50)       (Risk 51-75)       (Risk 76-100)           │
                                                               │                  ▼
                                                               ▼            [ SOC THREAT ]
                                                        [ AUTOMATED ]         RADAR &
                                                          INCIDENT          CROSS-DOMAIN
                                                         DISPATCHED          CORRELATION
```

---

## 3. Component Hierarchy & Domain Isolation

### A. Healthcare Subsystem (`healthcare_core`)
- **Clinical Data Loaders**: Ingests authentic MIMIC-IV-ED, MIMIC-IV Clinical, eICU Collaborative Research, and ONC Health IT datasets.
- **Dependency Graph**: Models clinical care pathways, PACS imaging servers, vital sign monitors, and life-support assets.
- **Scope Restriction**: Clinicians (Doctors and Nurses) are strictly restricted to assigned patients in their department; unassigned access triggers immediate ABAC risk escalation.

### B. Smart Traffic Subsystem (`traffic_core`)
- **STIG Signal Controller Grid**: Real-time signal cycle timing management, adaptive congestion clearance, and automated green corridor pre-emption for emergency ambulances.
- **Computer Vision Engine**: YOLOv8n ONNX edge object detection and ANPR OCR license plate verification.
- **SCADA Security**: Detects unauthorized phase timing modifications and sensor spoofing.

### C. Finance & Treasury Subsystem (`finance_cyber_risk`)
- **Indian Banking Fraud Models**: Supervised XGBoost trained on 550,000 transaction records with `scale_pos_weight` and PR-AUC optimization.
- **AML Graph Engine**: NetworkX multi-directed transaction graphs with PageRank, degree centrality, and 3-hop contagion blast radius simulation.
- **Pre-Emptive Escrow Hold**: Evaluates transactions in-flight before ledger settlement, freezing high-risk fraudulent wire transfers.

---

## 4. Cross-Domain Threat Correlation Engine
When threat actors execute multi-stage blended campaigns (e.g. compromising a hospital doctor credential to distract security while probing traffic signals and initiating high-value SWIFT wire fraud), the **Cross-Domain Threat Correlation Engine**:
1. Groups disparate sector telemetry by common Threat Actor IP (`198.51.100.77`) or Device Fingerprint (`DEV-ROGUE-EXT-88`).
2. Calculates compounded multi-sector risk multipliers ($1.15\times$ to $1.45\times$).
3. Dispatches a **Unified P1 Pan-City Coordinated Crisis Incident** to the central SOC console.
