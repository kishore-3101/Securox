# SH-FIN-05 Requirements Mapping Matrix
**Project**: Securox — Smart City Cyber-Physical Risk Detection & Visualization Platform  
**Challenge**: SH-FIN-05: AI-Driven Cyber Risk Detection for Smart City Digital Infrastructure  
**Status**: 100% Verified Mapping  

---

## 1. Challenge Objectives to Securox Components

| # | SH-FIN-05 Requirement | Securox Implementation Component | Source File / Endpoint | Verification Mechanism |
|---|---|---|---|---|
| **1** | **Security Telemetry Ingestion** | Canonical Multi-Source Ingestion Pipeline (`IngestionService`) | [`data/normalizer.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/data/normalizer.py)<br>[`backend/services/ingestion.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/services/ingestion.py)<br>`POST /api/events` | Ingests real CICIDS2017, UNSW-NB15, and IoT JSON records into standard schema. |
| **2** | **Processing Logs & Telemetry** | High-throughput async stream parser & SQLite WAL Event Store | [`backend/database/store.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/database/store.py)<br>`POST /api/telemetry` | Validates, deduplicates, and stores telemetry with microsecond latency. |
| **3** | **AI/ML Anomaly Detection** | Unsupervised Isolation Forest (200 trees, 5% contamination) | [`backend/ml/anomaly_detector.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/ml/anomaly_detector.py)<br>`POST /api/ml/core4/evaluate` | Identifies zero-day deviations; outputs `anomaly_score`, `anomaly_probability`, `is_anomaly`. |
| **4** | **Attack Classification** | Supervised Multi-Class Classifier (XGBoost & Random Forest) | [`ml/train.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/ml/train.py)<br>[`backend/ml/core4_ensemble.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/ml/core4_ensemble.py) | Classifies 9 attack categories: `BENIGN`, `DOS`, `DDOS`, `BRUTE_FORCE`, `PORT_SCAN`, `BOTNET`, `INFILTRATION`, `WEB_ATTACK`, `OTHER`. |
| **5** | **Behavioral Analysis** | Entity DBSCAN Clustering Engine on IP & Device Profiles | [`backend/ml/clustering.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/ml/clustering.py)<br>`GET /api/threats` | Detects coordinated botnet clusters, rapid credential spraying, and scanner outliers. |
| **6** | **Explainable Cyber-Risk Scores** | Transparent Composite 0–100 Risk Engine with YAML weights | [`risk/config.yaml`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/risk/config.yaml)<br>[`backend/services/risk_engine.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/services/risk_engine.py)<br>`GET /api/risk/current` | Formulates: $30\%\text{Anomaly} + 20\%\text{Attack} + 20\%\text{Criticality} + 15\%\text{Cascade} + 10\%\text{Behavior} + 5\%\text{Intel}$. |
| **7** | **Correlating Attacks with Assets**| Smart City Asset Registry (12 Core Municipal Nodes) | [`backend/assets/registry.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/assets/registry.py)<br>`GET /api/cyber/asset-security` | Maps inbound telemetry directly to asset IDs, physical coordinates, and criticality tiers. |
| **8** | **Attack Propagation Modeling** | Digital Twin Directed Graph with BFS Cascading Failure Simulator | [`backend/services/digital_twin.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/services/digital_twin.py)<br>`GET /api/digital-twin` | Models downstream failure cascades (e.g. Power Grid failure cascading to Traffic & Hospitals). |
| **9** | **Threat Intelligence Integration** | Threat Intel Abstraction Layer with IOC & RFC Block Matcher | [`threat_intel/threat_intelligence.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/threat_intel/threat_intelligence.py)<br>`GET /api/threat-intel/status` | Matches external malicious IPs, C2 domains, and Tor exit nodes with offline curated fallback. |
| **10** | **Explainable Alerts (XAI)** | SHAP Feature Attribution Waterfall & Plain-English Reasoner | [`ml/explainability.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/ml/explainability.py)<br>`GET /api/explanations/{alert_id}` | Breaks down exact percentage drivers (e.g., `+32% Request Rate`, `+24% Port Entropy`). |
| **11** | **Professional SOC Dashboard** | Dark-Themed Operations Center with Digital Twin & Demo Mode | [`frontend/index.html`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/frontend/index.html)<br>[http://localhost:8000/](http://localhost:8000/) | 10 institutional tabs, interactive network topology, live attack feed, and Judge Demo button. |
| **12** | **Real-Time / Replay Telemetry** | Stream Replay Engine streaming at configurable speed | [`replay.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/replay.py)<br>`/ws` and `/api/ws` WebSockets | Streams historical dataset records into live pipeline via WebSockets and REST. |
| **13** | **Scalability & Containerization** | Modular Lightweight Container Stack | [`Dockerfile`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/Dockerfile)<br>[`docker-compose.yml`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/docker-compose.yml) | Containerized FastAPI backend, embedded SQLite WAL, and static asset distribution. |
| **14** | **Measurable ML Evaluation** | Genuine Evaluation Suite with Confusion Matrices & Cross-Test | [`ml/evaluate.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/ml/evaluate.py)<br>[`reports/ML_RESULTS.md`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/reports/ML_RESULTS.md) | Computes real Accuracy, Precision, Recall, Macro-F1, ROC-AUC, latency, and generalization shift. |

---

## 2. Cyber-Physical Edge Extension

| Subsystem | Requirement | Securox Implementation | Source File |
|---|---|---|---|
| **CCTV & Edge AI** | Camera Edge Telemetry Node | YOLOv8n object detection & ANPR license plate OCR | [`backend/traffic_core/services/cv_engine.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/traffic_core/services/cv_engine.py) |
| **Cyber-Physical Correlation** | Correlate Physical Anomaly with Cyber Telemetry | Fuses camera gridlock & plate clones with signal controller tampering | [`backend/traffic_core/services/correlation_engine.py`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/backend/traffic_core/services/correlation_engine.py) |
| **Traffic Portal** | Complete Traffic & Signal Control | 26-view React command center mounted natively at `/traffic` | [`frontend/traffic_dist/index.html`](file:///c:/Users/praja/Downloads/sentinelai/sentinelai/frontend/traffic_dist/index.html) |
