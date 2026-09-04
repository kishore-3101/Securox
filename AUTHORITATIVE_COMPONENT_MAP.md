# Securox — Authoritative Component & Architecture Map

**Document Version:** 1.0.0  
**Map Date:** September 2026  
**Auditor:** Senior Software Architect & Lead Security Engineer  

---

## 1. System Topography & Active Hierarchy

The running system is an integrated multi-domain platform centered around `finance/backend/main.py`.

```
                                    CLIENT / BROWSER
                                           │
                       ┌───────────────────┴───────────────────┐
                       │                                       │
            HTTP Requests (Port 8000)               WebSockets (/ws, /api/ws)
                       │                                       │
                       ▼                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │             AUTHORITATIVE RUNTIME: main.py                  │
        │                   (FastAPI on Uvicorn)                      │
        └──────┬───────────────────────┬───────────────────────┬──────┘
               │                       │                       │
               ▼                       ▼                       ▼
    ┌────────────────────┐   ┌───────────────────┐   ┌───────────────────┐
    │  Healthcare Domain │   │   Traffic Domain  │   │   Finance Domain  │
    │  (healthcare_core) │   │   (traffic_core)  │   │(finance_cyber_risk│
    └──────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
               │                       │                       │
               ▼                       ▼                       ▼
    ┌────────────────────┐   ┌───────────────────┐   ┌───────────────────┐
    │ MIMIC / eICU       │   │ YOLOv8n ONNX      │   │ XGBoost 550k      │
    │ IoMT Security      │   │ Signal Preemption │   │ AMLSim Graph BFS  │
    │ Blast Radius Graph │   │ ANPR / FastTag    │   │ Cyber-VaR Engine  │
    └──────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
               │                       │                       │
               └───────────────────────┼───────────────────────┘
                                       │
                                       ▼
               ┌───────────────────────────────────────────────┐
               │         SECURITY & PERSISTENCE CORE           │
               │  • AccessControlEngine (5-Tuple RBAC+ABAC)    │
               │  • Merkle Vault Cryptographic Audit Trail     │
               │  • Primary DB: securox.db (21 tables)         │
               │  • Secondary DB: traffic.db (19 tables)       │
               └───────────────────────────────────────────────┘
```

---

## 2. Authoritative vs. Duplicate Component Comparison Table

| Component Category | Path in Repo | Status | Authority Level | Role / Justification |
|---|---|---|---|---|
| **Primary Backend** | `finance/backend/main.py` | **ACTIVE** | **AUTHORITATIVE** | Central FastAPI application hosting all 243 routes, event bus, and WebSocket endpoints. |
| **Secondary Traffic Backend** | `finance/backend/traffic_core/` | **ACTIVE** | **AUTHORITATIVE (SUB-APP)** | Mounted by `main.py`; handles traffic signals, cameras, and toll gates. |
| **Legacy Traffic Backend** | `traffic/backend/` | **INACTIVE** | **DEAD / DUPLICATE** | Redundant standalone copy; not mounted by `main.py`. |
| **Healthcare Backend** | `finance/backend/healthcare_core/` | **ACTIVE** | **AUTHORITATIVE (SUB-APP)** | Mounted by `main.py`; handles MIMIC-IV, eICU, IoMT assets, and blast radius. |
| **Finance Cyber Risk Engine** | `finance/backend/finance_cyber_risk/`| **ACTIVE** | **AUTHORITATIVE (MODULE)** | Dynamically imported by `finance_risk_engine.py` for XGBoost and graph contagion. |
| **Monolithic Frontend** | `finance/frontend/index.html` | **ACTIVE** | **AUTHORITATIVE (RUNTIME)**| Primary 12,680-line UI served directly at `/` hosting all 9 dashboards. |
| **Traffic Frontend (Compiled)** | `finance/frontend/traffic_dist/` | **ACTIVE** | **AUTHORITATIVE (STATIC)** | Pre-compiled React 19 build mounted statically at `/traffic/`. |
| **Healthcare Frontend (Compiled)**| `finance/frontend/healthcare_dist/` | **ACTIVE** | **AUTHORITATIVE (STATIC)** | Pre-compiled Vite build mounted statically at `/healthcare/`. Source is missing. |
| **Traffic Frontend (Source 1)** | `finance/frontend/traffic_src/` | **INACTIVE** | **SOURCE CODE ONLY** | React 19 source code used to build `traffic_dist`. |
| **Traffic Frontend (Source 2)** | `traffic/frontend/` | **INACTIVE** | **DEAD / DUPLICATE** | Duplicate React 19 source code at the repository root. |
| **Primary Database** | `finance/backend/database/securox.db`| **ACTIVE** | **AUTHORITATIVE** | 65.6 MB SQLite database with 21 tables managed via `store.py`. |
| **Secondary Database** | `finance/backend/traffic_core/traffic.db`| **ACTIVE** | **AUTHORITATIVE** | 330 KB SQLite database with 19 tables managed via SQLAlchemy. |
| **Root Stale Database** | `database/securox.db` | **INACTIVE** | **DEAD / EMPTY** | 0 bytes, 0 tables. Completely uninitialized. |
| **Root Stale Camera File**| `database/cameras.json` | **INACTIVE** | **DEAD / OUTDATED** | 415 bytes. Legacy camera definition file. |

---

## 3. Active Database Entity Map

### 3.1 Primary Database: `finance/backend/database/securox.db` (21 Tables)
1. `users` — 41 seeded users, PBKDF2 password hashes, multi-domain role assignments.
2. `alerts` — Real-time cybersecurity and physical infrastructure alerts.
3. `event_stream` — High-frequency telemetry log stream.
4. `risk_history` — Historical risk score records for trending.
5. `mitigations` — Automated and manual mitigation action records.
6. `fraud_alerts` — Financial transaction fraud detections.
7. `incidents` — Correlated security incident records.
8. `audit_logs` — Tamper-evident operational audit trail.
9. `campaigns` — Multi-stage threat campaign tracking.
10. `response_actions` — Execution records of response playbooks.
11. `simulations` — History of launched attack simulations.
12. `devices` — IoMT medical devices and IT hardware assets.
13. `patients` — Hospital clinical patient registry (MIMIC-IV linked).
14. `medical_records` — Patient clinical diagnoses and treatment history.
15. `ambulances` — Emergency vehicle fleet telemetry.
16. `traffic_signals` — City intersection signal controllers.
17. `traffic_cameras` — CCTV cameras with geolocation and attestation status.
18. `bank_accounts` — Financial accounts monitored for AML/fraud.
19. `bank_transactions` — Financial transaction ledger.
20. `security_policies` — ABAC dynamic security rules.
21. `cross_domain_threats` — Threats spanning traffic, healthcare, and finance.

### 3.2 Secondary Database: `finance/backend/traffic_core/traffic.db` (19 Tables)
1. `vehicles` — Registered vehicles and license plate mappings.
2. `tollgates` — FastTag electronic toll collection plazas.
3. `tollgate_distances` — Road network distance matrix.
4. `scans` — FastTag toll gate tag read events.
5. `anomalies` — Toll evasion and cloned plate detections.
6. `users` — **Duplicate user table** for traffic operators.
7. `cameras` — **Duplicate camera table** for traffic cameras.
8. `road_segments` — Highway and arterial road segment definitions.
9. `intersections` — Physical road junction coordinates.
10. `traffic_signals` — **Duplicate traffic signal table**.
11. `sensors` — Inductive loop and radar speed sensors.
12. `assets` — **Duplicate asset table** for traffic hardware.
13. `event_logs` — Traffic operational event stream.
14. `cyber_threats` — Traffic-specific cyber attack logs.
15. `incidents` — **Duplicate incident table** for traffic incidents.
16. `audit_logs` — **Duplicate audit log table**.
17. `traffic_predictions` — Predictive traffic congestion data.
18. `tracked_vehicles` — Actively tracked target vehicles.
19. `incident_timelines` — Incident timeline event entries.

---

## 4. AI/ML Model Asset Map

| Model Name | Physical File Location | Framework / Size | Calling Service | Active Runtime Role |
|---|---|---|---|---|
| **YOLOv8n Object Detector** | `finance/backend/ml/yolov8n.onnx` | ONNX Runtime (12.8 MB) | `services/cv_engine.py` | Detects vehicles, buses, trucks, and pedestrians from camera frames. |
| **Proactive Classifier** | `finance/backend/ml/saved_models/proactive_classifier.joblib` | Scikit-learn Random Forest (95 KB) | `services/proactive_ml.py` | Classifies streaming network flow vectors into benign vs attack categories. |
| **CIC-IDS2017 Classifier**| `finance/models/classifier/cicids2017_classifier.joblib` | Scikit-learn (578 KB) | `services/analytics_service.py` | Multi-class network intrusion classification. |
| **CIC-IDS2017 Iso Forest**| `finance/models/isolation_forest/cicids2017_iso_forest.joblib` | Scikit-learn (1.57 MB) | `services/analytics_service.py` | Unsupervised network anomaly detection. |
| **CIC-IDS2017 DBSCAN** | `finance/models/clustering/cicids2017_dbscan.joblib` | Scikit-learn (179 KB) | `services/analytics_service.py` | Spatial-temporal incident clustering. |
| **NSL-KDD Suite** | `finance/models/*/nsl_kdd_*.joblib` | Scikit-learn (2.48 MB combined) | `services/analytics_service.py` | Intrusion classification, anomaly scoring, and clustering. |
| **UNSW-NB15 Suite** | `finance/models/*/unsw_nb15_*.joblib` | Scikit-learn (2.72 MB combined) | `services/analytics_service.py` | Intrusion classification, anomaly scoring, and clustering. |
| **Indian Banking XGBoost**| Loaded via `finance-cyber-risk` | XGBoost | `services/finance_risk_engine.py`| Fraud classification on 550,000 banking transaction patterns. |
| **AMLSim Graph Contagion**| Loaded via `finance-cyber-risk` | NetworkX / BFS Graph | `services/finance_risk_engine.py`| Identifies money mule syndicates across 3-hop transaction contagion. |
| **LSTM Threat Predictor** | `finance/backend/ml/lstm_predictor.py` | Pure NumPy Autoencoder | `services/analytics_service.py` | Time-series forecasting of threat volume without heavy framework overhead. |

---

## 5. Persona & RBAC/ABAC Domain Map (41 Seeded Users across 35 Roles)

```
[EXECUTIVE DOMAIN]
  ├── city_admin       (City Administrator)
  ├── ciso             (Chief Information Security Officer)
  └── mayor            (Mayor / City Commissioner)

[SOC & CYBER DEFENSE]
  ├── soc_lead         (SOC Lead Analyst)
  ├── soc_analyst      (SOC Security Analyst L1/L2)
  ├── incident_resp    (Incident Response Commander)
  ├── threat_hunter    (Threat Intelligence Hunter)
  └── compliance_off   (Regulatory Compliance Officer)

[HEALTHCARE DOMAIN]
  ├── dr_smith         (Emergency Physician / ER Doctor)
  ├── dr_chen          (Chief Medical Officer)
  ├── nurse_sarah      (Lead Triage Nurse)
  ├── hospital_ciso    (Hospital Cybersecurity Officer)
  ├── iomt_engineer    (IoMT Biomedical Device Specialist)
  ├── pharma_mgr       (Pharmacy Dispensary Manager)
  └── ems_dispatcher   (Emergency Medical Services Dispatcher)

[SMART TRAFFIC & ITS DOMAIN]
  ├── traffic_mgr      (Traffic Operations Center Manager)
  ├── traffic_op       (Traffic Signal Controller Operator)
  ├── camera_admin     (CCTV Surveillance Administrator)
  ├── toll_supervisor  (FastTag Electronic Toll Supervisor)
  └── transit_coord    (Public Metro / Bus Transit Coordinator)

[BANKING & FINANCE DOMAIN]
  ├── bank_admin       (Core Banking Operations Director)
  ├── fraud_analyst    (Fintech Fraud Investigation Specialist)
  ├── aml_officer      (Anti-Money Laundering Compliance Officer)
  ├── treasury_mgr     (City Municipal Treasury Manager)
  └── fintech_auditor  (Independent Financial Auditor)

[INFRASTRUCTURE & UTILITIES]
  ├── grid_operator    (Smart Power Grid SCADA Operator)
  ├── water_engr       (Municipal Water SCADA Engineer)
  └── telecom_admin    (Municipal 5G / IoT Network Admin)

[CITIZEN & PUBLIC]
  ├── citizen_user     (Resident Public Portal User)
  └── transit_rider    (Public Transportation Commuter)

[DECOYS & HONEYTOKENS]
  ├── test_user        (Diagnostic Testing Persona)
  ├── decoy_admin      (Canary Decoy Account)
  └── honey_treasury   (Honeytoken Treasury Account)
```

---

*End of Authoritative Component Map.*
