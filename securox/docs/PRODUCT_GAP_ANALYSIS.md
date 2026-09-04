# Product Gap Analysis & Target Vision Roadmap: Securox Smart City

**Document Version:** 1.0.0  
**Analysis Date:** September 2026  
**Auditor:** Senior Software Architect & Cybersecurity Specialist  
**Product Target:** AI-Driven Cyber Risk Detection & Adaptive Access Control Platform for Smart City Digital Infrastructure  
**Target Sectors:** Healthcare, Smart Traffic / ITS, Banking & Finance, Cross-Domain SOC

---

## Executive Vision vs. Current Baseline

### Target Product Vision
The target platform is a production-grade, demo-ready Smart City Cyber-Physical Defense & Adaptive Access Control command center. It must continuously monitor critical infrastructure across **Healthcare**, **Smart Traffic**, and **Finance**, dynamically calculating risk scores, detecting anomalous and coordinated multi-stage cyber-physical attacks, enforcing fine-grained 5-tuple context-aware access policies (RBAC + ABAC), and executing automated, safety-verified mitigations without interrupting vital city services (e.g., rejecting an automated hospital power-cut or signal shutdown that could endanger life).

### Current Reality Summary
The repository has achieved significant foundational milestones:
* 41 enterprise personas pre-seeded across 35 roles.
* Authentic AI/ML models loaded and operating locally (YOLOv8n ONNX, XGBoost, Isolation Forests, DBSCAN, AMLSim Graph propagation, and pure-NumPy recurrent predictors).
* 243 active API endpoints supporting 21 attack simulations and a 12-stage cross-domain attack chain (Flagship E-01).
* High-functioning frontend monolith with real-time WebSockets, interactive maps, live CCTV feeds, and role switching.

However, a significant gap exists between this prototype and a resilient, production-ready enterprise solution due to:
1. **Security Isolation Gaps:** Over 60 routes in traffic and healthcare have zero authentication, and the 5-tuple access control engine is called in only one diagnostic endpoint rather than intercepting operational API requests.
2. **Data & Host Couplings:** External datasets depend on hardcoded local directory paths (`C:\Users\praja\Downloads\Healthcare\...`), breaking standalone portability.
3. **Dual Persistence Silos:** SQLite database is split between `securox.db` and `traffic.db`, preventing transactional consistency across domains.
4. **Disparate Frontend Architectures:** A 12,600-line Vanilla JS monolith operates alongside an isolated React 19 traffic app and an orphaned, compiled healthcare bundle missing its source code.

---

## 1. Domain-by-Domain Gap Analysis

### 1.1 Healthcare & Clinical Security (CareGuard)

| Capability / Requirement | Current Implementation Status | Gap & Required Remediation | Priority |
|---|---|---|---|
| **EHR/EMR Clinical Data Ingestion** | `PARTIAL` — MIMIC-IV-ED and MIMIC-IV Clinical loaders exist in `healthcare_core`. | Loaders depend on external hardcoded Windows user paths. If files are missing, fallback triggers empty data. Needs bundled offline demo partition. | High |
| **IoMT Cyber-Physical Asset Security** | `COMPLETE` — Infusion pumps, ventilators, PACS, and patient telemetry tracked with recall/risk status. | Device control commands lack signed cryptographic handshakes and mutual TLS (mTLS) enforcement. | Medium |
| **Hospital IT Blast Radius Modeling** | `COMPLETE` — Dependency graph in `blast_radius.py` correlates IT outages to clinical department risks (ER, ICU, OR). | Dynamic mitigation suggestions currently do not factor in real-time bed occupancy from live hospital sensors. | Medium |
| **CareGuard Doctor & Nurse Clinical Portal** | `COMPLETE` in monolith — Clinical patient records, diagnostic history, and patient context viewable. | Lacks BOLA (Broken Object-Level Authorization) checks: any authenticated doctor can read any patient's records regardless of departmental assignment. | Critical |
| **Emergency Break-Glass Access Protocol** | `COMPLETE` — `access_control.py` models `EMERGENCY` context override. | Break-glass events trigger audit logging, but do not automatically issue high-priority SMS/Pager alerts to the Hospital CISO. | High |
| **Healthcare Frontend UI Source** | `MISSING` — Only compiled Vite assets exist in `healthcare_dist`. | Zero source code in repo. Must reconstruct or integrate Healthcare views into the unified React SPA. | High |

---

### 1.2 Smart Traffic & Intelligent Transportation Systems (ITS)

| Capability / Requirement | Current Implementation Status | Gap & Required Remediation | Priority |
|---|---|---|---|
| **YOLOv8n CCTV Computer Vision** | `COMPLETE` — Real-time vehicle/pedestrian inference via ONNX model on live/simulated video streams. | Camera feeds are simulated via static images or canvas loops; lacks native RTSP/WebRTC hardware IP camera stream ingestion. | Medium |
| **Digital vs. Physical Disparity Detection**| `COMPLETE` — Flags discrepancies between optical vehicle counts and inductive loop sensor telemetry. | Disparity threshold is static (constant delta); needs dynamic adaptive thresholding based on historical time-of-day traffic patterns. | Medium |
| **Green Corridor Emergency Signal Preemption**| `COMPLETE` — `/api/traffic/green-corridor` computes shortest path and turns route intersections green for ambulances. | Signal changes occur instantly without progressive amber transition timing, creating a simulated physical hazard. | High |
| **FastTag / ANPR Toll Anomaly Detection**| `PARTIAL` — Toll scan CSVs and Tesseract OCR OCR exist in React frontend. | OCR executes in browser client-side; backend lacks a server-side plate extraction pipeline for automated fraud detection. | Medium |
| **Actuator & Signal Override Security** | `BROKEN` — `POST /api/traffic/signals/{signal_id}/override` has no authentication check! | Any anonymous user can override city signals. Must immediately mandate `Security(enforce_access)` with `TRAFFIC_OPERATOR` role verification. | Critical |

---

### 1.3 Banking, Fintech & Cyber-VaR Financial Exposure

| Capability / Requirement | Current Implementation Status | Gap & Required Remediation | Priority |
|---|---|---|---|
| **Indian Banking Fraud Detection** | `COMPLETE` — XGBoost model trained on 550k records predicting fraud probability and confidence. | Inference happens via pre-computed cached metrics or synchronous Python calls; needs async batched queue for high TPS. | Medium |
| **AMLSim Graph Mule Contagion** | `COMPLETE` — 3-hop weighted BFS contagion engine identifying smurfing, layering, and mule accounts. | Graph updates do not persist to database; contagion state is recomputed in-memory on every request. | Medium |
| **Cyber-VaR Monetary Exposure Engine** | `COMPLETE` — Quantifies potential monetary loss in INR (₹) across breach scenarios. | Does not dynamically incorporate business interruption insurance payouts or regulatory fine ceilings. | Low |
| **Treasury Canary Honeypots** | `COMPLETE` — `/api/v1/treasury/backdoor_disburse` traps attackers attempting unauthorized wire transfers. | Automatic IP ban is stored in-memory; server restart flushes the ban list. Must persist to SQLite/Postgres firewall table. | High |

---

### 1.4 Cross-Domain SOC & Unified Incident Response

| Capability / Requirement | Current Implementation Status | Gap & Required Remediation | Priority |
|---|---|---|---|
| **Universal 5-Tuple RBAC+ABAC Engine** | `PARTIAL` — Engine logic is complete in `access_control.py`, but not hooked into live REST API routes. | Only 1 diagnostic endpoint calls `evaluate_access()`. Over 200 operational endpoints bypass ABAC evaluation. | Critical |
| **12-Stage Cascading Flagship Attack Chain**| `COMPLETE` — E-01 simulation demonstrates cascading failure (Traffic -> Hospital -> Grid -> Finance). | Simulation runs strictly sequentially; lacks branch-decision points where user interventions alter the attack outcome. | Medium |
| **Tamper-Evident Merkle Vault** | `COMPLETE` — SHA-256 cryptographic chaining of audit logs with root hash verification. | Merkle tree recalculation runs on single-node SQLite; needs read-only public notary or external hash anchoring for compliance. | Low |
| **Cross-Domain Threat Correlation** | `COMPLETE` — DBSCAN and rule-based correlation linking traffic signal faults to hospital ambulance delays. | Correlation engine runs periodically; should transition to an event-driven pub/sub architecture (e.g. Redis / Kafka). | Medium |

---

### 1.5 Architecture, Frontend & Infrastructure

| Capability / Requirement | Current Implementation Status | Gap & Required Remediation | Priority |
|---|---|---|---|
| **Repository Structure & Duplication** | `BROKEN` — Redundant `traffic/` folder, duplicate `traffic_src`, nested `finance-cyber-risk` git repo, 14 scratch scripts. | Eliminate redundant directories, archive scratch scripts, and organize into a unified `backend/` and `frontend/` hierarchy. | High |
| **Database Architecture** | `PARTIAL` — Two separate SQLite DBs (`securox.db` and `traffic.db`) with duplicated tables and inconsistent access layers. | Consolidate into a single database with unified SQLAlchemy ORM models and Alembic schema migrations. | High |
| **Frontend Architecture** | `PARTIAL` — Monolithic 12,600-line `index.html` alongside separate React 19 app and compiled-only healthcare bundle. | Migrate all views into a modern, componentized React 19 + TypeScript Single Page Application (SPA). | High |
| **Production Containerization** | `PARTIAL` — Fragmented docker-compose files with no root-level multi-service orchestration. | Author a production-ready root `docker-compose.yml` defining `api`, `web`, `db`, and `redis` services with healthchecks. | High |
| **Automated Testing & CI/CD** | `PARTIAL` — 39 backend tests passing; zero frontend tests; no CI/CD automation pipelines. | Add Vitest/Playwright tests for frontend authentication flows, and configure GitHub Actions for automated linting and testing. | Medium |

---

## 2. Target Architecture Specifications

```
                              [ Internet / Public Clients ]
                                            │
                                            ▼
                           +──────────────────────────────────+
                           |     Reverse Proxy (Nginx / Caddy)|
                           |     TLS Termination / WAF / Rate |
                           +────────────────┬─────────────────+
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    │                                               │
             [ /api/*, /ws ]                                    [ /* (SPA) ]
                    │                                               │
                    ▼                                               ▼
+───────────────────────────────────────+       +───────────────────────────────────+
|     Unified Securox Backend (FastAPI) |       |   Unified Securox Frontend (React)|
|  • Python 3.11 / Uvicorn ASGI Worker  |       |  • React 19 + TypeScript + Vite   |
|  • 5-Tuple RBAC+ABAC Interceptor      |       |  • Tailwind CSS / Lucide / Leaflet|
|  • Async Event Bus & WebSockets       |       |  • Global Auth & Incident State   |
+───────────────────┬───────────────────+       +───────────────────────────────────+
                    │
   ┌────────────────┼────────────────┐
   │                │                │
   ▼                ▼                ▼
[ Healthcare ]  [ Traffic ]     [ Finance ]
• MIMIC-IV      • YOLOv8n ONNX  • XGBoost
• IoMT Security • Signal Grid   • AML Graph
• Blast Radius  • Disparity     • Cyber-VaR
   │                │                │
   └────────────────┼────────────────┘
                    │
                    ▼
+───────────────────────────────────────+
|      Unified Persistence Layer        |
|  • PostgreSQL 16 (or Unified SQLite)  |
|  • SQLAlchemy 2.0 ORM + Alembic       |
|  • Cryptographic Merkle Audit Vault   |
+───────────────────────────────────────+
```

---

## 3. Concrete Phased Implementation Roadmap

### Phase 1: Security Hardening & Zero-Trust Route Enforcement (Immediate)
* **Goal:** Eliminate high-severity security vulnerabilities and enforce authorization.
* **Key Tasks:**
  1. Patch unauthenticated critical routes (`POST /api/traffic/signals/{signal_id}/override`, `POST /api/toll/{transaction_id}/override`, and all 31 `healthcare_core` endpoints) by attaching `Depends(get_current_user)` and `Security(enforce_permissions)`.
  2. Implement a global FastAPI dependency that maps HTTP request tuples `(Subject, Role, Action, Resource, Context)` directly to `AccessControlEngine.evaluate_access()`.
  3. Remove hardcoded fallback JWT secrets in `jwt_auth.py` and enforce dynamic loading from environment variables.
  4. Implement Object-Level Access Control (BOLA/IDOR protection) ensuring medical records, signal overrides, and bank transactions can only be manipulated by authorized role-resource pairs.

### Phase 2: Repository Pruning & De-duplication
* **Goal:** Clean up technical debt and establish an authoritative single source of truth.
* **Key Tasks:**
  1. Verify all features from root `/traffic` exist in `/finance/backend/traffic_core/`, then safely delete the redundant `/traffic` directory.
  2. Consolidate `traffic/frontend` and `finance/frontend/traffic_src` into a single authoritative frontend source directory.
  3. Relocate and archive all 14 ad-hoc scratch scripts from `/finance/scratch/` into an ignored diagnostic directory or delete them.
  4. Remove the uninitialized, empty `database/securox.db` (0 bytes) from the root.
  5. Create a unified `.env.example` at the repository root defining all server, security, database, and model parameters.

### Phase 3: Database & State Unification
* **Goal:** Merge disparate database layers into a cohesive persistence engine.
* **Key Tasks:**
  1. Merge `traffic.db` tables (`vehicles`, `scans`, `tollgates`, `intersections`) into `securox.db`.
  2. Reconcile overlapping schemas: use a single `users` table, a single `incidents` table, and a single `audit_logs` table across all domains.
  3. Standardize database access on SQLAlchemy 2.0 declarative models, deprecating raw SQL helpers in `store.py`.
  4. Persist in-flight simulation states, canary ban-lists, and AML graph contagion flags directly into the unified database.

### Phase 4: Dataset Decoupling & Portability
* **Goal:** Ensure the entire platform runs out-of-the-box on any developer workstation or Docker container.
* **Key Tasks:**
  1. Remove hardcoded paths (`C:\Users\praja\Downloads\Healthcare...`) from `healthcare_core/core/config.py`.
  2. Package lightweight offline sample CSVs and Parquet fixtures for MIMIC-IV-ED, eICU, and CSE-CIC-IDS2018 inside the repository.
  3. Provide an automated download and verify script (`scripts/download_datasets.py`) with MD5 checksums for developers requiring full-scale production research datasets.

### Phase 5: Modern Unified SPA Frontend
* **Goal:** Replace the 12,600-line monolithic `index.html` with a modern, modular React 19 Single Page Application.
* **Key Tasks:**
  1. Initialize a unified React 19 + TypeScript + Vite project in `frontend/`.
  2. Port all 9 dashboard views (SOC, Digital Twin, Healthcare, Doctor EMR, CAD Ambulance, Traffic Ops, Finance Cyber-VaR, Executive, Demo Center) into clean, modular React components.
  3. Unify navigation with React Router, eliminating DOM manipulation and iframe hacks.
  4. Standardize real-time WebSocket state management using a centralized React Context or Zustand store.
  5. Add unit and component tests using Vitest and React Testing Library.

### Phase 6: Production Containerization & CI/CD
* **Goal:** Achieve turn-key production deployment and automated testing.
* **Key Tasks:**
  1. Write a root multi-stage `Dockerfile` building the React frontend into static assets and packaging the Python FastAPI backend.
  2. Create a root `docker-compose.yml` orchestrating:
     * `securox-api`: FastAPI backend worker.
     * `securox-web`: Nginx serving the built React SPA and proxying `/api` and `/ws`.
     * `securox-db`: PostgreSQL 16 container (with optional SQLite fallback).
  3. Set up a GitHub Actions workflow (`.github/workflows/ci.yml`) executing:
     * Python linting (`ruff` / `black`) and automated backend tests (`pytest`).
     * TypeScript type checking and frontend tests (`vitest`).
     * Docker container build verification.

---

*End of Product Gap Analysis & Roadmap.*
