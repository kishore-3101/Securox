# Comprehensive Technical & Product Audit: Securox Smart City Platform

**Document Version:** 1.0.0  
**Audit Date:** September 2026  
**Auditor:** Senior Software Architect, AI/ML Engineer & Cybersecurity Specialist  
**Target Repository:** `Securox-main`  
**Current Branch / Commit:** `master` (`f53bcc6`)  
**Audit Purpose:** Comprehensive technical, security, architectural, and product baseline audit prior to system modernization and phase execution.

---

## Executive Summary

The **Securox** (also branded as *SentinelAI* / *CareGuard*) platform is an ambitious, high-concurrency digital infrastructure defense system designed for multi-domain smart city cyber-physical security across **Healthcare**, **Smart Traffic / Intelligent Transportation Systems (ITS)**, and **Banking / Finance**.

### Key Strengths
1. **Extensive Domain Modeling:** The repository encompasses sophisticated domain models representing acute hospital operations (MIMIC-IV / eICU), urban traffic signal control & FastTag tolling, and core banking / AML transaction graphs.
2. **Authentic AI/ML Integration:** Genuine serialized machine learning models exist and execute locally, including a **YOLOv8n ONNX** computer vision model for vehicle/pedestrian detection, **XGBoost** and **Random Forest** classifiers for network intrusion (CIC-IDS2017, UNSW-NB15, NSL-KDD), **DBSCAN** spatial-temporal clustering for incident correlation, **Isolation Forests** for anomaly detection, and graph-based contagion models for AML financial tracking.
3. **Multi-Domain RBAC+ABAC Design:** A 5-tuple context-aware access engine (`auth/access_control.py`) provides mathematically rigorous policy decisions evaluating Subject, Role, Action, Resource, and Context (device trust, time-of-day, IP reputation, patient assignment, emergency status).
4. **Resilient Test Baseline:** The test suite in `finance/tests/` achieves a 100% pass rate across 39 core integration and security tests.

### Critical Vulnerabilities & Architectural Flaws
1. **Extreme Code Duplication:** The standalone `traffic/` directory (backend, frontend, database) is duplicated inside `finance/backend/traffic_core` and `finance/frontend/traffic_src`. Similarly, `finance-cyber-risk` is a nested standalone Git repository duplicated inside `finance/backend/finance_cyber_risk/`.
2. **Missing Frontend Source Code:** While `traffic_src` contains React 19 source code, `finance/frontend/healthcare_dist` contains *only* pre-compiled production JavaScript/CSS bundles with zero source code present in the repository.
3. **Hardcoded Machine-Specific Paths:** `healthcare_core/core/config.py` contains hardcoded paths to local user directories (`C:\Users\praja\Downloads\Healthcare\datasets`), making deployment on any other machine or container fail to locate original datasets unless locally patched.
4. **Dual Incompatible Persistence Layers:** The platform concurrently runs two separate SQLite database files (`securox.db` via raw SQL and `traffic.db` via SQLAlchemy ORM) with overlapping entity models (`users`, `incidents`, `signals`, `assets`).
5. **Authorization Bypass / Route Exposure:** While `access_control.py` is well architected, **only 1 endpoint** in the entire codebase actually calls `access_engine.evaluate_access()`. Over 60 routes across `healthcare_core` and `traffic_core` (including critical signal override and toll modification endpoints) lack any authentication or permission checks (`Depends(get_current_user)` is missing).
6. **Monolithic Frontend Tech Debt:** The main user interface is an unminified, monolithic `finance/frontend/index.html` file spanning **12,600+ lines** of intertwined HTML, CSS, SVG vectors, and Vanilla JavaScript DOM manipulation.

---

## 1. 16-Dimension Technical & Product Audit

### 1.1 Frontend Framework
* **Current State:**
  * **Primary UI:** Vanilla JavaScript, HTML5, and CSS embedded in a single monolithic file: `finance/frontend/index.html` (12,680+ lines). Uses inline DOM manipulation, native `fetch()`, native Canvas API, and inline SVG iconography.
  * **Traffic Module UI:** Modern React 19 (`19.2.8`), Vite 8 (`8.2.2`), Leaflet 1.9.4 maps, Lucide React icons, and Tesseract.js OCR in `traffic/frontend` (and duplicate `finance/frontend/traffic_src`).
  * **Healthcare Module UI:** Pre-compiled React/Vite distribution assets (`index-CY3Z_5Y8.js`, `index-8e0GbzwS.css`) located in `finance/frontend/healthcare_dist/`. **Source files are missing from repository.**
* **Classification:** `PARTIAL` / `ARCHITECTURALLY FRAGMENTED`
* **Deficiencies:** Three disparate frontend paradigms running simultaneously. The main monolith lacks component modularity, state management libraries, and TypeScript type safety. Navigation between modules requires iframe embedding or cross-tab redirects.

### 1.2 Backend Framework
* **Current State:**
  * FastAPI (`>=0.100.0`) on Python 3.11/3.14 with Uvicorn ASGI server.
  * `finance/backend/main.py` serves as the central hub, mounting `traffic_core` routes (41 routes) and `healthcare_core` routes (31 routes), aggregating 243 total routes.
  * WebSocket endpoints handle real-time telemetry: `/ws`, `/api/ws`, and `/api/traffic/camera-relay-ws`.
  * Async event bus and background tasks via `asyncio`.
* **Classification:** `COMPLETE` (Core Routing) / `PARTIAL` (Integration Depth)
* **Deficiencies:** Routing is consolidated via `include_router` and FastAPI sub-apps, but error handling, logging formats, and dependency injection schemas remain inconsistent between `main.py`, `traffic_core/app.py`, and `healthcare_core/api/endpoints.py`.

### 1.3 Database & Storage Architecture
* **Current State:**
  * **Primary DB:** `finance/backend/database/securox.db` (65.6 MB). SQLite in WAL mode with 21 tables (`users`, `alerts`, `event_stream`, `risk_history`, `mitigations`, `fraud_alerts`, `incidents`, `audit_logs`, `campaigns`, `response_actions`, `simulations`, `devices`, `patients`, `medical_records`, `ambulances`, `traffic_signals`, `traffic_cameras`, `bank_accounts`, `bank_transactions`, `security_policies`, `cross_domain_threats`). Managed through custom connection helpers in `store.py`.
  * **Secondary DB:** `finance/backend/traffic_core/traffic.db` (330 KB). SQLite with 19 tables (`vehicles`, `tollgates`, `scans`, `anomalies`, `users`, `cameras`, `intersections`, `traffic_signals`, `sensors`, etc.). Managed via SQLAlchemy 2.0 ORM in `traffic_db.py`.
  * **Stale Root DB:** `database/securox.db` (0 bytes, 0 tables) is an uninitialized empty artifact in the root folder.
* **Classification:** `PARTIAL` / `ARCHITECTURAL RISK`
* **Deficiencies:** Dual-database split creates data silos. The `users`, `incidents`, `assets`, and `traffic_signals` tables are duplicated across both databases. No distributed transaction coordination or foreign key integrity between domains.

### 1.4 Authentication & Identity Management
* **Current State:**
  * JWT tokens signed using HS256 (`python-jose`).
  * Passwords hashed via PBKDF2-HMAC-SHA256 (260,000 iterations).
  * Pre-seeded database contains 41 users covering 35 distinct roles across 6 domains (Healthcare, Traffic, Finance, Cross-Domain SOC, Infrastructure, Citizen).
  * 5-tuple Access Control Engine (`auth/access_control.py`) calculates real-time risk scores from contextual attributes (device fingerprint, IP reputation, time-of-day, location, patient assignment).
* **Classification:** `PARTIAL`
* **Deficiencies:**
  * Hardcoded secret fallback in `jwt_auth.py` (`securox-super-secret-key-change-in-production-2024`).
  * `access_engine.evaluate_access` is called in only one diagnostic endpoint (`/api/access/evaluate`). Actual operational API routes do not invoke this engine to enforce RBAC/ABAC on live resource reads and mutations.
  * Over 60 routes across `healthcare_core` and `traffic_core` have no JWT authentication dependencies whatsoever.

### 1.5 Existing APIs
* **Current State:**
  * 243 active routes cataloged in FastAPI documentation (`/docs`).
  * Endpoints cover Telemetry, City Twin KPIs, Alerts, Audit Logs, ML Inference, Camera Vision Streams, Signal Overrides, Toll Gate Overrides, Patient EMR, IoMT Device Status, Hospital IT Pathways, AML Mule Detection, and Flagship Scenarios.
* **Classification:** `COMPLETE` (Surface Coverage) / `PARTIAL` (Security & Uniformity)
* **Deficiencies:** Lack of standard REST response envelopes. Some return `{"status": "ok", "data": ...}`, others return raw lists or bare dictionaries. Missing rate-limiting on sensitive data modification routes.

### 1.6 Existing Components
* **Current State:**
  * Interactive city map with Leaflet tiles and animated SVG overlays.
  * Live CCTV grid with simulated RTSP/Canvas video streams.
  * Multi-stage Attack Chain Tracker (12-stage visualization).
  * Real-time WebSocket event feed and threat ticker.
  * Persona Quick-Switcher pill bar supporting instant role impersonation for demos.
* **Classification:** `COMPLETE` (Functional Demo) / `PARTIAL` (Production Reusability)
* **Deficiencies:** Built as raw imperative JavaScript functions in `index.html` (e.g. `renderMap()`, `updateAlerts()`, `switchTab()`) rather than reusable, testable UI components.

### 1.7 Existing Dashboards
* **Current State:**
  * 9 specialized views in `index.html`:
    1. SOC Command Center (Unified Cyber-Physical Overview)
    2. Smart City Digital Twin (Infrastructure Topology & GIS)
    3. Healthcare Command & CareGuard (Hospital IT, Clinical & IoMT Security)
    4. Doctor Portal (Clinical EMR & Patient Context)
    5. Ambulance CAD Portal (Emergency Telemetry & Green Corridor Routing)
    6. Smart Traffic Ops (Signal Grid, Cameras & Toll Management)
    7. Finance & Fintech Fraud / Cyber-VaR (Banking & AML Contagion)
    8. Executive & Threat Intel (City Health & Exposure Metrics)
    9. Interactive Demo Center (One-click Scenario Launcher)
* **Classification:** `COMPLETE`
* **Deficiencies:** Tightly coupled into the monolith. Tab switches manipulate DOM element styles (`display: block` / `none`) rather than utilizing client-side routing.

### 1.8 Existing AI/ML Functionality
* **Current State:**
  * **YOLOv8n ONNX:** 12.8 MB model (`finance/backend/ml/yolov8n.onnx`) executing via OpenCV/ONNX runtime for real-time camera object detection (cars, trucks, pedestrians).
  * **Proactive Risk Classifier:** Scikit-learn Random Forest model (`proactive_classifier.joblib`) predicting threat classification from network flow features.
  * **Multi-Dataset Models:** Pre-trained models for CIC-IDS2017, NSL-KDD, and UNSW-NB15 (Classifiers, DBSCAN clusterers, Isolation Forests) in `finance/models/`.
  * **Finance & AML Models:** Indian Banking XGBoost (trained on 550k records), Isolation Forest anomaly detector, and AMLSim graph-based money laundering classifier in `finance_cyber_risk`.
  * **Time-Series Predictor:** Pure NumPy lightweight recurrent / autoencoder model (`lstm_predictor.py`) forecasting incident volume without heavy PyTorch/TensorFlow overhead.
  * **Flagship Disparity Detector:** Cross-modal disparity engine matching computer vision vehicle counts against inductive loop sensor telemetry to flag sensor spoofing.
* **Classification:** `COMPLETE`
* **Deficiencies:** Pre-trained `.joblib` files are tied to Python 3.11/3.14 Scikit-learn internal structure; deserialization warnings occur if environment versions differ. Training pipelines are separate scripts rather than automated MLOps workflows.

### 1.9 Existing Datasets
* **Current State:**
  * Network Intrusion: CSV samples for CIC-IDS2017 (946 KB), NSL-KDD (3.8 MB), UNSW-NB15 (1.06 MB), ToN-IoT (736 KB).
  * Traffic: Tollgate distances (`tollgate_distances.csv`), toll transactions (`toll_scans.csv`), camera coordinates (`cameras.json`).
  * Finance: Pre-calculated graph metrics, AMLSim transaction distributions, Indian banking transaction summaries.
  * Healthcare: MIMIC-IV-ED demo, MIMIC-IV Clinical demo, eICU demo, ONC Health-IT, and CSE-CIC-IDS2018 (36 GB).
* **Classification:** `PARTIAL`
* **Deficiencies:** High-capacity healthcare datasets are located **outside the repository** on a developer local path (`C:\Users\praja\Downloads\Healthcare\...`). When launched on a new environment without these local files, the system falls back to empty/synthetic data or throws unhandled loader warnings.

### 1.10 Existing Simulation Functionality
* **Current State:**
  * `simulation/attack_scenarios.py` (893 lines): 21 realistic attack scenarios (DDoS, Ransomware, Insider Threat, IoT Botnet, Chennai Flood, Signal Hacking, Ambulance Routing, etc.).
  * `services/flagship_scenario.py` (484 lines): 12-stage multi-domain cascading cyber-physical attack chain with dynamic risk escalation (0 -> 94) and automated mitigation verification (94 -> 18).
  * `traffic_core/services/scenario_simulator.py`: 9 traffic-specific physical & cyber fault injection scenarios.
* **Classification:** `COMPLETE`
* **Deficiencies:** Simulations generate synthetic events into memory queues. If the backend restarts during a simulation, in-flight state is lost because simulation progress is not fully journaled to the database.

### 1.11 Existing Security Controls
* **Current State:**
  * Rate limiting and anomaly tripwires on high-frequency routes.
  * Merkle Vault tamper-evident audit logging for cryptographic non-repudiation.
  * Canary honeypot endpoints (`/api/v1/treasury/backdoor_disburse`, `/api/traffic/actuators/raw_override`) that trigger automatic IP bans when probed.
  * Simulated hardware attestation and TPM verification for CCTV cameras and traffic controllers.
* **Classification:** `COMPLETE` (Feature Specification) / `PARTIAL` (Enforcement Coverage)
* **Deficiencies:** Security controls protect designated showcase endpoints, but standard operational CRUD endpoints remain unguarded against broken object-level authorization (BOLA/IDOR).

### 1.12 Existing Folder Structure
* **Current State:**
  * Deeply fragmented root with overlapping projects:
    * `/finance/`: Contains backend, frontend monolith, ML models, and reports.
    * `/finance/backend/traffic_core/`: Forked/modified copy of `/traffic/backend/`.
    * `/finance/backend/finance_cyber_risk/finance-cyber-risk/`: Nested third-party clone.
    * `/finance/frontend/traffic_src/`: Duplicate of `/traffic/frontend/`.
    * `/finance/frontend/traffic_dist/`: Compiled traffic build.
    * `/finance/frontend/healthcare_dist/`: Compiled healthcare build with missing source.
    * `/finance/scratch/`: 14 ad-hoc testing/scratch scripts left in version control.
    * `/traffic/`: Redundant legacy project directory at root.
* **Classification:** `BROKEN` / `HIGH TECHNICAL DEBT`
* **Deficiencies:** Confusing folder hierarchy makes developer onboarding difficult, balloons repository size, and causes confusion regarding which file is active at runtime.

### 1.13 Environment Configuration
* **Current State:**
  * `.env.example` in `finance/` and `finance-cyber-risk/`.
  * Runtime relies on fallback environment variables defined inside Python source files.
* **Classification:** `PARTIAL`
* **Deficiencies:** No single, unified `.env` at the repository root. Variables like `SECRET_KEY`, `SECUROX_DB_PATH`, `TRAFFIC_DB_PATH`, `HEALTHCARE_DATASETS_DIR`, and `CORS_ORIGINS` are scattered across multiple configuration classes (`config.py`, `settings.py`).

### 1.14 Deployment Configuration
* **Current State:**
  * `finance/Dockerfile`: Python 3.11-slim container building the finance backend and monolith.
  * `finance/docker-compose.yml`: Runs `securox-soc-core` on port 8000.
  * `traffic/docker-compose.yml`: Standalone Postgres container for FastTag DB (unused by default).
  * Helper scripts: `start_demo.bat` and `start_demo.sh`.
* **Classification:** `PARTIAL`
* **Deficiencies:** No unified multi-container Docker Compose file orchestrating the unified platform, frontend build pipelines, database migration, and background workers. No Kubernetes manifests, reverse proxy (Nginx/Caddy) configuration, or production HTTPS termination.

### 1.15 Existing Tests
* **Current State:**
  * `finance/tests/`: 11 test suites with 39 passing unit and integration tests (`test_api.py`, `test_assets.py`, `test_healthcare.py`, `test_ml.py`, `test_rbac_abac_security.py`, `test_smart_city_soc.py`, etc.).
  * `finance-cyber-risk`: 15 unit tests covering AML models and dynamic risk calculation.
  * `traffic_core/tests`: 4 test files duplicating `traffic/backend/tests`.
* **Classification:** `COMPLETE` (Backend Unit & Integration) / `MISSING` (Frontend & E2E)
* **Deficiencies:** Zero frontend unit tests (Jest/Vitest) and zero end-to-end browser automation tests (Playwright/Cypress). No GitHub Actions / GitLab CI pipeline definitions.

### 1.16 Existing Documentation
* **Current State:**
  * Comprehensive markdown suite in root: `README.md`, `ARCHITECTURE.md`, `RBAC.md`, `AI_MODEL.md`, `SECURITY.md`, `DEMO_GUIDE.md`, `DATASETS.md`, `DEMO_SCRIPT.md`.
* **Classification:** `COMPLETE`
* **Deficiencies:** Documentation accurately reflects the recent Master Build enhancements but does not yet document the underlying technical debt, duplicated directories, or missing healthcare frontend source code.

---

## 2. Comprehensive Feature Classification Matrix

| Feature / Subsystem | Domain | Status | Technical Notes |
|---|---|---|---|
| **Multi-Domain RBAC+ABAC Engine** | Security / Core | `COMPLETE` | 5-tuple context evaluation in `access_control.py` (Subject, Role, Action, Resource, Context). |
| **API Route Authorization Guards** | Security / Core | `PARTIAL` | Engine exists, but only 1 endpoint enforces `evaluate_access()`. Over 60 routes lack JWT dependencies. |
| **Pre-Seeded 41 Personas (35 Roles)** | Identity | `COMPLETE` | Fully seeded in `securox.db` with secure PBKDF2 hashes across 6 smart-city domains. |
| **Tamper-Evident Merkle Vault** | Security / Core | `COMPLETE` | Cryptographic SHA-256 Merkle chain auditing for critical administrative and triage actions. |
| **Canary Decoy Honeypots** | Security / Core | `COMPLETE` | `/api/v1/treasury/backdoor_disburse` and `/api/traffic/actuators/raw_override` trap attackers. |
| **Camera Hardware Attestation** | Security / Traffic | `COMPLETE` | Simulated TPM 2.0 / zero-trust cryptographic handshake for camera sensor feeds. |
| **YOLOv8n Computer Vision Engine** | AI / Traffic | `COMPLETE` | Local 12.8 MB ONNX model performing vehicle & pedestrian detection from video frames. |
| **Digital-Physical Disparity Detector** | AI / Traffic | `COMPLETE` | Correlates optical camera vehicle density against inductive loop telemetry to detect sensor spoofing. |
| **Green Corridor Ambulance Routing** | Traffic / Healthcare | `COMPLETE` | Priority signal preemption API (`/api/traffic/green-corridor`) clearing intersections for emergency transit. |
| **FastTag Automatic Number Plate Recognition** | Traffic / Vision | `PARTIAL` | OCR integration via Tesseract in React; relies on static sample video clips for toll scans. |
| **MIMIC-IV / eICU Clinical Data Ingestion** | Healthcare | `PARTIAL` | Loaders functional, but depend on hardcoded local paths (`C:\Users\praja\Downloads\Healthcare...`). |
| **IoMT Cyber-Physical Asset Security** | Healthcare | `COMPLETE` | Tracks infusion pumps, ventilators, PACs with clinical risk multipliers and recall status. |
| **Hospital IT Blast Radius Analysis** | Healthcare | `COMPLETE` | Dependency graph tracing IT system compromise to clinical department disruption (ER, ICU, OR). |
| **Healthcare Frontend UI Source** | Healthcare | `MISSING` | Only compiled distribution (`healthcare_dist`) exists in repo; source components are absent. |
| **Indian Banking XGBoost Fraud Model** | AI / Finance | `COMPLETE` | 550,000-record trained XGBoost classifier integrated via `finance_risk_engine.py`. |
| **AMLSim Graph Contagion & Mule Detection**| AI / Finance | `COMPLETE` | Weighted 3-hop BFS risk propagation identifying money mule syndicates. |
| **Cyber-VaR Monetary Loss Estimation** | Finance | `COMPLETE` | Monte Carlo / parametric financial exposure estimation computing potential loss in INR (₹). |
| **21-Scenario Cyber Attack Simulator** | Simulation | `COMPLETE` | Covers DDoS, SCADA tampering, ransomware, insider threats, and weather contingencies. |
| **12-Stage Cascading Flagship Attack Chain** | Simulation | `COMPLETE` | E-01 attack chain demonstrating cross-domain escalation from traffic to healthcare to finance. |
| **Real-Time WebSocket Telemetry Feed** | Core / Comm | `COMPLETE` | High-frequency streaming on `/ws` supporting SOC alert distribution. |
| **Unified Monolithic Frontend (12k lines)**| Frontend | `PARTIAL` | Rich and demo-ready, but unmaintainable single-file Vanilla JS architecture. |
| **Modern React Traffic Frontend** | Frontend | `COMPLETE` | High quality React 19 + Vite 8 app in `traffic_src`, but served as isolated iframe/dist. |
| **Automated Backend Test Suite** | QA / Testing | `COMPLETE` | 39 / 39 passing tests in `finance/tests/`. |
| **Frontend Automated Testing (E2E/Unit)** | QA / Testing | `MISSING` | No Playwright, Cypress, or Vitest configurations. |
| **Unified Multi-Service Docker Compose** | DevOps | `MISSING` | Separate incomplete docker-compose files; no root orchestration. |

---

## 3. Deep-Dive Anomaly & Technical Debt Identification

### 3.1 Duplicated Code & Redundant Directories
1. **`traffic/` vs `finance/backend/traffic_core/`:**
   * The root `traffic/` directory contains an entire standalone FastAPI application, database, and test suite.
   * `finance/backend/traffic_core/` is a modified copy of this exact code, modified to mount inside `main.py`.
   * **Impact:** 15+ MB of redundant code, duplicated unit tests (`test_cyber_and_correlation.py`, etc.), and confusion over which implementation is authoritative.
2. **`traffic/frontend/` vs `finance/frontend/traffic_src/`:**
   * `traffic/frontend/` and `finance/frontend/traffic_src/` are near-exact duplicates of the React 19 source code.
   * **Impact:** Any bugfix applied to one frontend is not automatically reflected in the other.
3. **`finance/backend/finance_cyber_risk/finance-cyber-risk/`:**
   * A complete Git repository cloned inside the backend folder, containing its own `requirements.txt`, `docker-compose.yml`, `data/`, and `tests/`.

### 3.2 Architectural Problems
1. **Dual Incompatible Database Engines:**
   * `securox.db` uses raw SQL with custom parameterized queries in `store.py`.
   * `traffic.db` uses SQLAlchemy declarative ORM in `traffic_db.py`.
   * Overlapping entities (`users`, `incidents`, `signals`) exist in both databases without foreign keys or synchronization. If an incident is resolved in `securox.db`, `traffic.db` remains unaware unless manually synced.
2. **Missing Healthcare Frontend Source:**
   * `finance/frontend/healthcare_dist` contains compiled Vite bundle chunks (`index-CY3Z_5Y8.js`). The original JSX/TSX source files are missing from the repository, making UI customization or branding impossible without reverse engineering or retrieving the source repository.
3. **Monolithic 12,600-Line Single File:**
   * `finance/frontend/index.html` combines styles, templates, SVG graphics, state variables, and event listeners in a single file. This introduces high cognitive overhead, eliminates code reusability, and makes concurrent team development prone to merge conflicts.

### 3.3 Security Vulnerabilities
1. **Unauthenticated Critical Action Routes:**
   * In `traffic_core/app.py`:
     * Line 441: `POST /api/traffic/signals/{signal_id}/override` depends only on `db: Session = Depends(get_db)`. No user authentication or role validation is required!
     * Line 1212: `POST /api/toll/{transaction_id}/override` depends only on `db: Session = Depends(get_db)`.
   * In `main.py`:
     * Line 4175: `PATCH /api/traffic/signals/{signal_id}/override` has zero authentication dependencies.
   * In `healthcare_core/api/endpoints.py`:
     * All 31 healthcare endpoints (`/api/devices`, `/api/incidents/{incident_id}/stage`, `/api/response`) lack route-level auth guards.
   * **Severity:** `HIGH / CRITICAL` (Allows unauthenticated attackers on the network to manipulate physical traffic signals and access clinical patient data).
2. **Hardcoded Fallback JWT Secret:**
   * `security/jwt_auth.py` contains `SECRET_KEY = os.getenv("SECRET_KEY", "securox-super-secret-key-change-in-production-2024")`. If deployed without setting `.env`, all issued tokens use a publicly known signing key.
3. **BOLA / IDOR (Broken Object-Level Authorization):**
   * Operational endpoints that accept resource IDs (`patient_id`, `account_id`, `camera_id`) do not verify if the authenticated user's department, assigned patients, or jurisdictional boundary grants access to that specific record.

### 3.4 Hard-Coded Data & External Dependencies
1. **Machine-Specific Filesystem Paths:**
   * `healthcare_core/core/config.py` hardcodes:
     ```python
     candidates = [
         Path(r"C:\Users\praja\Downloads\Healthcare\datasets"),
         Path(r"D:\HC\Healthcare\datasets"),
         Path(r"D:\Smart Horizon\Healthcare\datasets")
     ]
     ```
   * If executed on a Linux server or Docker container, these paths fail, triggering empty or unhandled dataset fallback behavior.
2. **Hardcoded CORS Origins:**
   * Permissive CORS configurations in `config.py` allow `localhost:5173`, `localhost:3000`, etc., without strict environment-based origin enforcement.

### 3.5 Fake / Mock Functionality
1. **Simulated RTSP Feeds:**
   * CCTV video feeds in `cameras.json` simulate streaming using static placeholder images or loopback HTML5 video canvas renderings rather than true RTSP/HLS IP camera ingests.
2. **Simulated Hardware Attestation:**
   * TPM 2.0 PCR register verification in `/api/cameras/attestation` generates mock cryptographic nonces rather than communicating with physical hardware security modules (HSM/TPM).

### 3.6 Unused Dependencies & Bloat
1. **Unused Dependencies in Requirements:**
   * `pytesseract` and `opencv-python-headless` are declared in `traffic/backend/requirements.txt`, but heavy CV inference is handled via `onnxruntime` or pre-calculated frames in `main.py`.
2. **Scratch Files Left in Version Control:**
   * `finance/scratch/` contains 14 development scripts (`test_api.py`, `test_rtsp.py`, `find_cameras.py`, etc.) that clutter the repository.

### 3.7 Scalability & Performance Bottlenecks
1. **Synchronous File Reads inside API Handlers:**
   * Certain endpoints read large JSON metrics files (`amlsim_graph_risk_scores.json`, 496 KB) synchronously inside request handlers, blocking the Python async event loop.
2. **SQLite Database Locking under Concurrency:**
   * While SQLite WAL mode improves read concurrency, high-frequency write operations across 243 routes during an active simulation can trigger `database is locked` errors if multiple background tasks write simultaneously.

---

## 4. Recommended Target Architecture

### 4.1 System Topology
```
                     +---------------------------------------+
                     |        Reverse Proxy (Nginx / Caddy)   |
                     |         SSL / Rate Limiting / WAF     |
                     +-------------------+-------------------+
                                         |
                         +---------------+---------------+
                         |                               |
                 /api, /ws, /docs                     /* (Static)
                         |                               |
         +---------------+---------------+   +-----------+-----------+
         |     Securox Unified FastAPI   |   |   Unified React 19    |
         |     Python 3.11 / Uvicorn     |   |   Vite Single Page    |
         |   (Async ASGI, EventBus)      |   |   Dashboard (SPA)     |
         +---------------+---------------+   +-----------------------+
                         |
       +-----------------+-----------------+
       |                 |                 |
+------+------+   +------+------+   +------+------+
|  Healthcare |   |    Smart    |   |   Finance   |
|   Module    |   |   Traffic   |   |   Cyber     |
| (MIMIC/IoMT)|   | (YOLO/ITS)  |   | (XGB/Graph) |
+------+------+   +------+------+   +------+------+
       |                 |                 |
       +-----------------+-----------------+
                         |
         +---------------+---------------+
         |    Centralized Database Layer |
         |   PostgreSQL 16 + TimescaleDB |
         |   (or Unified SQLite WAL)     |
         +-------------------------------+
```

### 4.2 Architectural Remediation Principles
1. **Single Source of Truth Persistence:**
   * Unify `securox.db` and `traffic.db` into a single consolidated database schema. Standardize on SQLAlchemy 2.0 ORM with Alembic migrations for all domains.
2. **Universal 5-Tuple Policy Enforcement Middleware:**
   * Enforce `access_engine.evaluate_access()` systematically across all operational endpoints via a FastAPI global dependency (`Security(enforce_permissions)`).
3. **Consolidated Single-Directory Architecture:**
   * Eliminate root `traffic/` and redundant sub-repos. Establish a clean, modular repository layout:
     ```
     securox/
       ├── backend/
       │   ├── app/
       │   │   ├── api/          # Unified routes (auth, soc, healthcare, traffic, finance)
       │   │   ├── core/         # Config, security, database sessions, middleware
       │   │   ├── domains/      # Business logic (healthcare, traffic, finance)
       │   │   ├── ml/           # Model loaders & inference pipelines
       │   │   ├── simulations/  # Attack scenarios & twin engines
       │   │   └── tests/        # Pytest integration & unit tests
       ├── frontend/
       │   ├── src/              # Modern unified React 19 + TypeScript SPA
       │   │   ├── components/   # Shared UI components
       │   │   ├── views/        # Healthcare, Traffic, Finance, SOC views
       ├── datasets/             # Bundled offline sample datasets
       ├── docker-compose.yml    # Single orchestrator
       └── .env.example          # Single environment template
     ```
4. **Resilient Data Fallbacks:**
   * Decouple dataset loaders from local host paths. Bundle lightweight offline sample partitions inside the repository and provide an automated downloader script (`scripts/download_datasets.py`) for full-scale MIMIC/eICU archives.

---

## 5. Migration Strategy & Implementation Order

```
[Phase 1: Security & Route Hardening]
   │  - Apply JWT & RBAC/ABAC guards to unguarded routes (traffic_core, healthcare)
   │  - Eliminate hardcoded JWT secrets & enforce strict environment config
   │  - Address BOLA/IDOR on entity IDs
   ▼
[Phase 2: Repository Pruning & De-duplication]
   │  - Remove redundant root traffic/ folder after verifying traffic_core completeness
   │  - Clean up scratch/ files and stale root database/securox.db
   │  - Standardize environment variables into a single root .env.example
   ▼
[Phase 3: Database & Model Unification]
   │  - Unify traffic.db and securox.db into a single database engine
   │  - Reconcile overlapping tables (users, incidents, signals, assets)
   │  - Ensure persistent audit trails for all simulations
   ▼
[Phase 4: Dataset Portability & Decoupling]
   │  - Remove machine-specific hardcoded paths from healthcare loaders
   │  - Implement graceful offline dataset fallbacks for container compatibility
   ▼
[Phase 5: Modern Unified Frontend Migration]
   │  - Consolidate views into a modern, unified React + TypeScript SPA
   │  - Retire the 12,600-line monolithic index.html
   ▼
[Phase 6: Production Containerization & CI/CD]
   │  - Create single root docker-compose.yml orchestrating API, UI, and Database
   │  - Add GitHub Actions workflow for automated testing and linting
```

---

*End of Technical Audit Report.*
