# Securox — Safe Migration & Modernization Plan

**Document Version:** 1.0.0  
**Plan Date:** September 2026  
**Auditor & Strategist:** Senior Software Architect & DevSecOps Lead  
**Execution Constraint:** Strictly non-destructive. No code rewriting or deletions prior to approval.

---

## 1. Guiding Principles & Safety Guarantees

1. **Preserve What Works:** The 39 existing unit and integration tests in `finance/tests/` must pass with 100% success at every step.
2. **Zero Regressions on Running Application:** The running application on `http://localhost:8000` must remain fully operational, serving all 9 dashboards, real-time WebSockets, and AI inference models.
3. **No Blind Deletions:** Dead code and duplicate directories (`traffic/`, scratch scripts, stale databases) will be safely quarantined or archived before deletion.
4. **Gradual Decoupling:** Unify databases and authorization middleware using non-breaking additive patterns before retiring legacy endpoints.

---

## 2. Definitive Component Disposition Categorization

### 2.1 What Must Be Preserved (High Value, Tested, Functional)
* **Access Control Engine (`finance/backend/auth/access_control.py`):** The 523-line 5-tuple RBAC+ABAC engine.
* **Flagship Scenario Engine (`finance/backend/services/flagship_scenario.py`):** The 12-stage E-01 attack chain and digital-physical disparity detector.
* **Attack Simulator (`finance/backend/simulation/attack_scenarios.py`):** All 21 realistic attack scenarios.
* **AI/ML Model Suite:**
  * `finance/backend/ml/yolov8n.onnx` (YOLOv8n computer vision model).
  * `finance/backend/ml/saved_models/` (Proactive classifier and scaler).
  * `finance/models/` (CIC-IDS2017, NSL-KDD, UNSW-NB15 models).
  * `finance/backend/services/finance_risk_engine.py` (Indian banking XGBoost & AMLSim graph models).
  * `finance/backend/ml/lstm_predictor.py` (Lightweight NumPy autoencoder).
* **Security Subsystem:** Merkle Vault (`security/merkle_vault.py`), PBKDF2 hashing, and Canary honeypot logic.
* **41 Seeded Enterprise Personas:** Retain all user credentials, roles, and domain mappings in `securox.db`.
* **39 Automated Integration Tests:** `finance/tests/` test suites.

### 2.2 What Must Be Migrated (Technical Debt to Modernize)
* **Monolithic `index.html` (12,680 lines):** Migrate into a modern, componentized React 19 + TypeScript Single Page Application (SPA).
* **Dual Database Split (`securox.db` + `traffic.db`):** Migrate `traffic.db` tables into `securox.db` (or a single PostgreSQL database), consolidating redundant `users`, `incidents`, `signals`, and `audit_logs` tables.
* **Healthcare Frontend:** Reconstruct the source code for the orphaned `healthcare_dist` bundle within the unified React SPA.
* **Ad-Hoc Dataset Loaders:** Remove machine-specific hardcoded local Windows paths (`C:\Users\praja\Downloads\Healthcare...`) from `healthcare_core/core/config.py` and replace with portable bundled offline fixtures.

### 2.3 What Can Be Deleted Later (After Verification)
* **Root `traffic/` Directory:** Delete the redundant root `/traffic` directory once all traffic routes and database models in `finance/backend/traffic_core` are confirmed authoritative.
* **Duplicate `traffic/frontend/` & `finance/frontend/traffic_src/`:** Delete duplicate React copies once unified in `frontend/`.
* **Empty Root Database:** Safely delete `database/securox.db` (0 bytes) and `database/cameras.json` (415 bytes).
* **Scratch Debugging Scripts:** Delete or archive the 14 one-off scripts in `finance/scratch/`.
* **Stale Root Scripts:** Clean up unreferenced batch files after standardizing launch commands.

### 2.4 What Must Be Fixed Immediately (Critical Security Vulnerabilities)
* **Unauthenticated Signal & Toll Overrides (HIGH RISK):**
  * `POST /api/traffic/signals/{signal_id}/override` (traffic_core)
  * `PATCH /api/traffic/signals/{signal_id}/override` (main.py)
  * `POST /api/toll/{transaction_id}/override` (traffic_core)
  * `POST /api/traffic/actuators/raw_override` (main.py)
  * **Fix:** Mandate `Depends(get_current_user)` and `Security(enforce_access)` with required role `TRAFFIC_OPERATOR`.
* **Unauthenticated Healthcare Endpoints (HIGH RISK):**
  * All 31 endpoints in `finance/backend/healthcare_core/api/endpoints.py` (patient records, IoMT devices, incidents).
  * **Fix:** Attach authentication dependencies.
* **Hardcoded JWT Secret Fallback (MEDIUM RISK):**
  * `security/jwt_auth.py` fallback string `"securox-super-secret-key-change-in-production-2024"`.
  * **Fix:** Enforce environment variable check and raise an error in production if unset.
* **Broken Object-Level Authorization (BOLA/IDOR):**
  * Ensure doctors can only query patients assigned to their department, and traffic operators can only override signals in their jurisdiction.

### 2.5 What Can Wait (Secondary Enhancements)
* Replacing SQLite WAL with PostgreSQL / TimescaleDB.
* Live RTSP camera streaming hardware ingestion (current canvas/video simulation is sufficient for demonstrations).
* Full CI/CD GitHub Actions pipelines and Kubernetes Helm charts.
* Formal microservices decoupling (current monolithic FastAPI hub is performant and simple to run).

---

## 3. Phased Implementation Roadmap

```
[Phase 1: Security Hardening & Zero-Trust Route Enforcement]
   │  - Attach JWT & RBAC/ABAC guards to 70 unprotected operational routes
   │  - Eliminate hardcoded JWT secrets & enforce strict environment config
   │  - Enforce BOLA/IDOR checks on patient, signal, and account IDs
   ▼
[Phase 2: Repository Pruning & De-duplication]
   │  - Quarantine and remove redundant root traffic/ folder
   │  - Clean up scratch/ files and stale root database/securox.db
   │  - Standardize environment variables into a single root .env.example
   ▼
[Phase 3: Database & State Unification]
   │  - Merge traffic.db tables into securox.db
   │  - Reconcile overlapping schemas (users, incidents, signals, assets)
   │  - Standardize on SQLAlchemy 2.0 ORM across all modules
   ▼
[Phase 4: Dataset Portability & Decoupling]
   │  - Remove machine-specific hardcoded paths from healthcare loaders
   │  - Implement graceful offline dataset fallbacks for container compatibility
   ▼
[Phase 5: Modern Unified SPA Frontend Migration]
   │  - Build unified React 19 + TypeScript Single Page Application
   │  - Port all 9 dashboards from index.html into modular React components
   │  - Retire 12,680-line monolithic index.html
   ▼
[Phase 6: Production Containerization & CI/CD]
   │  - Author production multi-stage Dockerfile and root docker-compose.yml
   │  - Set up automated GitHub Actions workflow for pytest and vitest
```

---

*End of Safe Migration Plan.*
