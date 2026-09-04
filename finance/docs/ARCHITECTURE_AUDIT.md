# Securox — Architecture Audit
**Document Version**: 1.0.0  
**Target Challenge**: SH-FIN-05 (AI-Driven Cyber Risk Detection for Smart City Digital Infrastructure)  
**Date**: September 2026  
**Auditor**: Securox Core Engineering Team  

---

## 1. Executive Summary

This document provides a comprehensive technical audit of the **Securox** repository as it exists prior to the SH-FIN-05 upgrade. In strict adherence to **Rule 0**, no working component is discarded or rewritten from scratch. Instead, existing production-grade modules—including the FastAPI backend, Core-4 AI ensemble, SQLite WAL persistent store, digital twin state machine, CCTV ANPR vision engine, and dark SOC dashboard—are documented for incremental enhancement and integration with public cybersecurity datasets.

---

## 2. Current Folder Structure

```
c:\Users\praja\Downloads\sentinelai\sentinelai/
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git exclusion rules
├── README.md                    # Project documentation
├── backend/                     # Core Python backend service
│   ├── Dockerfile               # Container build instructions
│   ├── requirements.txt         # Python package dependencies
│   ├── main.py                  # Primary FastAPI application entrypoint (2,400+ LOC)
│   ├── auth/                    # PBKDF2/JWT authentication and RBAC
│   │   ├── __init__.py
│   │   └── jwt_auth.py
│   ├── bin/                     # Hardware & media acceleration binaries (ffmpeg.exe)
│   ├── data/                    # Dataset cache (nsl_kdd.csv, 3.8MB)
│   ├── database/                # Persistent SQLite data layer (securox.db, store.py)
│   │   ├── camera_key.key       # Cryptographic key for camera feed encryption
│   │   ├── cameras.json         # Camera hardware registry
│   │   ├── securox.db           # SQLite WAL database (45MB)
│   │   └── store.py             # Asynchronous SQLite storage abstraction
│   ├── finance_cyber_risk/      # Indian Banking ML suite & Cyber-VaR engine
│   │   └── finance-cyber-risk/  # Pre-trained models (XGBoost, IsolationForest, AMLSim)
│   ├── ml/                      # Machine learning engines & pipelines
│   │   ├── anomaly_detector.py  # Isolation Forest unsupervised detector
│   │   ├── clustering.py        # DBSCAN behavioral clustering engine
│   │   ├── core4_ensemble.py    # Multi-model ensemble (XGBoost + IsoForest + Graph + Temporal)
│   │   ├── lstm_predictor.py    # Temporal forecast model
│   │   ├── proactive_model.py   # Pre-breach velocity predictor
│   │   ├── saved_models/        # Joblib serialized model artifacts
│   │   └── yolov8n.onnx         # ONNX vehicle & object detection model (12.8MB)
│   ├── scripts/                 # Download and utility scripts
│   ├── security/                # Cryptographic audit vault & Merkle tree ledger
│   │   └── crypto_vault.py
│   ├── services/                # Modular domain services
│   │   ├── ai_commander.py      # LLM incident assistant
│   │   ├── camera_manager.py    # Multi-brand CCTV RTSP/HLS & security monitor
│   │   ├── cascade_engine.py    # Infrastructure failure cascade calculator
│   │   ├── city_health_engine.py# High-level municipal health aggregator
│   │   ├── digital_twin.py      # Smart City digital twin & asset topology
│   │   ├── event_bus.py         # Pub/Sub event distribution bus
│   │   ├── explainability.py    # Initial explainability module
│   │   ├── finance_risk_engine.py# Real Indian banking risk evaluator
│   │   ├── flagship_scenario.py # 12-stage sequential flagship scenario
│   │   ├── fraud_detection.py   # FASTag & financial cloning detector
│   │   ├── fraud_graph_engine.py# Account-to-account risk contagion graph
│   │   ├── ingestion.py         # Telemetry parser & feature extractor
│   │   ├── integrations.py      # External threat intel & webhook simulator
│   │   ├── mitigation_engine.py # Actionable response recommendation generator
│   │   ├── proactive_service.py # Time-to-Compromise (TTC) radar service
│   │   ├── real_world_feeds.py  # Live weather, crypto, DNS latency polling
│   │   ├── response_engine.py   # Automated containment engine
│   │   ├── risk_engine.py       # Dynamic composite 0–100 risk scoring
│   │   └── traffic_engine.py    # Traffic density & signal controller simulator
│   ├── simulation/              # Attack scenario injectors & synthetic generators
│   │   ├── attack_scenarios.py
│   │   └── data_generator.py
│   └── traffic_core/            # Dedicated 26-view traffic & ANPR command center
│       ├── app.py               # 41 traffic and toll intelligence endpoints
│       ├── config.py
│       ├── generate_toll_data.py
│       ├── schema.sql
│       ├── seed_data.py
│       ├── toll_scans.csv       # FASTag toll transaction log
│       ├── tollgate_distances.csv
│       ├── traffic.db           # SQLite database for roads & intersections
│       ├── traffic_db.py
│       ├── traffic_models.py
│       ├── services/            # CV engine, correlation engine, cyber engine
│       └── tests/               # Traffic test suite
├── frontend/                    # Web-based security operations center
│   ├── index.html               # Palantir/CrowdStrike style SOC dashboard (362KB)
│   ├── static/                  # Shared CSS, JavaScript, and asset icons
│   └── traffic_dist/            # Built React Vite command center (assets/, index.html)
├── docker-compose.yml           # Multi-container deployment configuration
├── nginx.conf                   # Reverse proxy configuration
├── start.bat                    # Windows startup script
├── start.sh                     # Linux/Unix startup script
└── test_system.py               # 9-module automated verification suite
```

---

## 3. Technology Stack Breakdown

| Layer | Current Implementation | Status |
|---|---|---|
| **Backend Framework** | FastAPI 0.136.1, Uvicorn 0.47.0, Starlette, Pydantic v2 | Production-ready, asynchronous, high throughput |
| **Frontend Framework** | Pure HTML5, CSS3, Vanilla ES6 JavaScript, Feather Icons, Chart.js + Built React 18 / Vite app (`traffic_dist`) | Highly responsive, dark theme, zero unnecessary frameworks |
| **Database & Persistence**| SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`), SQLAlchemy 2.0.52 | Persistent across restarts, concurrent async reads/writes |
| **Machine Learning** | Scikit-learn 1.8.0, XGBoost 3.3.0, Joblib 1.5.3, NumPy 2.4.6, Pandas 3.0.3, ONNX Runtime | Fully functional, high-performance CPU execution |
| **Real-time Telemetry** | Native WebSockets (`/ws` and `/api/ws`), Server-Sent Events (SSE) fallback | Bidirectional streaming, sub-second telemetry broadcast |
| **Computer Vision** | OpenCV 5.0.0-dev, ONNX YOLOv8n vehicle detection, Indian ANPR OCR normalizer | Edge camera processing, vehicle counting, plate recognition |
| **Containerization** | Dockerfile, docker-compose.yml, Nginx reverse proxy | Functional container definitions |

---

## 4. Subsystem Audits

### 4.1 Backend APIs
- **Router Architecture**: Centralized in `backend/main.py` with modular sub-app routes included from `backend/traffic_core/app.py`.
- **Active Route Count**: 65+ distinct REST endpoints and 2 WebSocket streams.
- **Key Route Families**:
  - `/api/auth/*`: JWT login, user profile, RBAC enforcement.
  - `/api/command-center/*`: Executive KPIs, system health summary, active incident counts.
  - `/api/traffic/*`: Road corridors, intersections, signal overrides, sensor streams.
  - `/api/cameras/*`: Camera registry, RTSP/HLS live frames, behavior injection.
  - `/api/cyber/*`: Threat intelligence, asset security, threat hunting queries.
  - `/api/correlation/*`: Cyber-physical event correlations.
  - `/api/incidents/*`: Incident lifecycle, status transitions, forensic evidence.
  - `/api/ml/core4/*`: Multi-model ensemble inference, architecture status, Conformal Prediction region.
  - `/api/finance/*`: Cyber-VaR quantitative monetary exposure in ₹, Indian Banking model status.
  - `/api/security/*`: Merkle blockchain audit ledger, hardware firmware attestation, canary traps.
  - `/api/proactive/*`: Pre-breach Time-to-Compromise (TTC) radar clock, escrow holds.

### 4.2 Machine Learning Modules
1. **Unsupervised Anomaly Detection (`backend/ml/anomaly_detector.py`)**:
   - Uses `IsolationForest` (200 estimators, 5% contamination).
   - Currently trained on synthetic normal baseline vectors.
   - *Upgrade Requirement*: Ingest real public cybersecurity datasets (CICIDS2017 / UNSW-NB15).
2. **Supervised Attack Classifier (`backend/ml/core4_ensemble.py` & `backend/finance_cyber_risk`)**:
   - Contains pre-trained XGBoost models on 550,000 banking and AML records.
   - Platt probability calibration applied.
   - *Upgrade Requirement*: Add standalone multi-class network attack classifier on canonical network flows.
3. **Behavioral Clustering (`backend/ml/clustering.py`)**:
   - Rolling buffer of 500 entity profiles clustered via `DBSCAN` (`eps=0.5`, `min_samples=3`).
   - Identifies outliers (cluster `-1`) representing botnets, scanning bursts, or abnormal sources.
4. **Temporal Modeling (`backend/ml/lstm_predictor.py`)**:
   - Statistical and sequence-based trend predictor forecasting peak risk.

### 4.3 Risk Intelligence Engine (`backend/services/risk_engine.py`)
- Dynamic 0–100 composite risk score computed per smart-city asset.
- Evaluates:
  $$\text{Score} = w_1 \text{Cyber} + w_2 \text{Financial} + w_3 \text{Behavioral} + w_4 \text{Criticality} + w_5 \text{Propagation} + w_6 \text{Intel} + w_7 \text{Forecast}$$
- *Upgrade Requirement*: Externalize risk weights to `risk/config.yaml` and provide explainability breakdowns.

### 4.4 Digital Twin & Attack Propagation (`backend/services/digital_twin.py`)
- Represents 12 municipal and financial assets: Power Grid, Core Banking, Payment Gateway, Tax Portal, Banking API, Water Supply, Healthcare, Traffic System, Emergency Services, Citizen Services, IoT Gateways, Communications.
- Contains directed dependency graph: `power_grid -> core_banking -> payment_gateway -> upi_gateway`.
- Computes BFS blast radius and cascading failure propagation.

### 4.5 CCTV & Traffic Subsystem (`backend/services/camera_manager.py` & `backend/traffic_core`)
- Edge camera manager supporting RTSP, MJPEG, and simulated video feeds.
- YOLOv8 vehicle detection canvas with ANPR plate recognition (`backend/traffic_core/services/cv_engine.py`).
- Correlates physical traffic gridlock with concurrent cyberattacks against intersection controllers.

---

## 5. Components Reused vs. Components Upgraded

| Component | Disposition | Planned Action |
|---|---|---|
| **FastAPI Core (`backend/main.py`)** | **REUSE & EXTEND** | Preserve all 65+ active routes; add canonical telemetry ingestion endpoints |
| **SQLite WAL DataStore (`backend/database/store.py`)**| **REUSE** | Retain persistent event and alert storage schema |
| **Core-4 AI Ensemble (`backend/ml/core4_ensemble.py`)**| **REUSE** | Preserve 4-core multi-model ensemble and 99% Conformal Prediction guarantee |
| **Traffic Core & 26-View UI (`backend/traffic_core`)**| **REUSE** | Maintain full database schema, ANPR OCR, and React portal at `/traffic` |
| **SOC Dashboard (`frontend/index.html`)** | **REUSE & UPGRADE**| Enhance with Competition Demo Mode, SHAP explanation modal, and live ML metrics |
| **Dataset Ingestion Pipeline** | **NEW / UPGRADE** | Implement `data/download_datasets.py`, `data/schema.py`, `data/normalizer.py` |
| **ML Training & Evaluation (`ml/train.py`, `ml/evaluate.py`)**| **NEW / UPGRADE** | Build unified CLI training and benchmarking pipeline producing real confusion matrices |
| **Configurable Risk Config (`risk/config.yaml`)**| **NEW / UPGRADE** | Decouple hardcoded weights into transparent, editable YAML configuration |
| **Threat Intelligence Layer (`threat_intel/`)** | **NEW / UPGRADE** | Create formal IOC matcher, IP reputation checker, and external API adapter |
| **Real-time Dataset Replay (`replay.py`)** | **NEW** | Create configurable CLI tool to stream historical dataset records into live pipeline |
| **Automated Testing Suite (`tests/`)** | **NEW / UPGRADE** | Comprehensive pytest suite covering ingestion, ML, risk, digital twin, and APIs |

---

## 6. Known Limitations to Resolve in SH-FIN-05

1. **Synthetic Telemetry Bias**: While the financial and traffic engines use real datasets (550k banking records, tollgate logs), the network intrusion anomaly detector previously relied on synthetic Gaussian baselines. *Resolution: Ingest CICIDS2017 and UNSW-NB15.*
2. **Hardcoded Risk Weights**: Scoring weights were defined directly in Python source. *Resolution: Create `risk/config.yaml`.*
3. **Implicit Explainability**: Explainability was partially rule-based. *Resolution: Implement SHAP feature attribution waterfall breakdowns.*
4. **Standalone Dataset Replay**: Needed a single CLI command to replay public datasets at variable speeds. *Resolution: Create `replay.py`.*
5. **Standardized Verification**: Needed a unified validation script to certify system health in one command. *Resolution: Create `scripts/validate_project.py`.*
