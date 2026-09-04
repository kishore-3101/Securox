# SECUROX PLATFORM — MIGRATION INVENTORY & COMPARATIVE AUDIT
**Generated**: September 2026  
**Scope**: Comprehensive structural and functional inventory comparing duplicated subsystem implementations prior to Phase 2 cleanup.

---

## 1. Inventory Summary Table

| Subsystem Component | Location A | Location B | Authoritative Choice | Rationale |
|---|---|---|---|---|
| **Traffic Backend** | `traffic/backend/` (27 files) | `finance/backend/traffic_core/` (29 files) | **`finance/backend/traffic_core/`** | Mounted in live gateway, includes Phase 1 `require_access` authorization guards, uses modular `traffic_db.py`, contains live `traffic.db`. |
| **Traffic Frontend** | `traffic/frontend/` (53 files) | `finance/frontend/traffic_src/` (52 files) | **`finance/frontend/traffic_src/`** | `traffic/frontend/` contains 18 files with unresolved git merge conflicts (`<<<<<<< HEAD`). `traffic_src/` is clean and syntactically valid. |
| **Finance Cyber Risk** | `finance/backend/finance_cyber_risk/` | `finance/backend/finance_cyber_risk/finance-cyber-risk/` | **`finance-cyber-risk` (Un-nested)** | Contains complete trained ML models (XGBoost, Isolation Forest, AMLSim), data partitions, and Cyber-VaR quantifier. |
| **Primary Database** | `database/securox.db` (0 bytes) | `finance/backend/database/securox.db` (73.4 MB) | **`finance/backend/database/securox.db`** | `database/securox.db` is empty/stale. `finance/backend/database/securox.db` has 21 tables and all seed data. |
| **Secondary Database** | N/A | `finance/backend/traffic_core/traffic.db` (331 KB) | **`traffic_core/traffic.db`** | Seeded ITS SQLite database with cameras, signals, and event logs. |
| **Active Camera State**| `database/cameras.json` (415 B) & `camera_key.key` (44 B) | N/A | **`database/cameras.json` & `.key`** | Used actively by `CameraManager` for cryptographic camera state. |
| **Scratch Files** | `finance/scratch/` (14 files) | N/A | **Archive to `archive/scratch/`** | Legacy debugging and ad-hoc test scripts no longer used in production or test suite. |

---

## 2. Deep Dive: `traffic/` vs `finance/backend/traffic_core/`

### File Breakdown:
- `traffic/backend/` has 27 files.
- `finance/backend/traffic_core/` has 29 files.
- **Common files**: 26 files.
- **Only in `traffic/backend/`**: `database.py` (legacy monolithic DB connector).
- **Only in `traffic_core/`**:
  - `traffic_db.py` (FastAPI-compatible SQLAlchemy session factory with connection pooling).
  - `traffic_models.py` (ORM models matching platform standard).
  - `traffic.db` (331,776 bytes SQLite database with seeded intersections, road segments, signals, and cameras).

### Content Differences in Common Files:
1. **`app.py`**:
   - `traffic_core/app.py`: Hardened with universal server-side authorization:
     - `require_access(ResourceType.TRAFFIC_SIGNAL, Action.UPDATE, object_id_param="signal_id")` on signal overrides.
     - `require_access(ResourceType.TOLL_SYSTEM, Action.UPDATE)` on toll overrides and reports.
     - `require_access(ResourceType.SECURITY_INCIDENT, Action.UPDATE, object_id_param="incident_id")` on incident status mutations.
     - Mounted directly into `finance/backend/main.py` gateway.
   - `traffic/backend/app.py`: Legacy, unmounted, unhardened endpoints lacking role/BOLA checks.
2. **`models.py`**:
   - `traffic_core/models.py`: Clean facade (`from traffic_core.traffic_models import *`).
   - `traffic/backend/models.py`: Legacy direct declaration.
3. **Services**:
   - `cv_engine.py`, `incident_service.py`, `scenario_simulator.py`, `ai_assistant.py`: In `traffic_core`, imports and event bus routing are aligned with the unified gateway pub/sub.

**Conclusion**: `traffic/backend/` is superseded by `finance/backend/traffic_core/`. It will be safely preserved in `archive/legacy_traffic/`.

---

## 3. Deep Dive: `traffic/frontend/` vs `finance/frontend/traffic_src/`

### Critical Finding:
Inspection revealed that **18 files in `traffic/frontend/` have unresolved Git merge conflict markers**:
- `src/context/AuthContext.jsx`
- `src/context/TrafficContext.jsx`
- `src/context/WebSocketContext.jsx`
- `src/views/AIAssistantView.jsx`
- `src/views/AdministrationView.jsx`
- `src/views/AssetSecurityView.jsx`
- `src/views/AuditLogView.jsx`
- `src/views/CyberSecurityCenterView.jsx`
- `src/views/FastagConsoleView.jsx`
- `src/views/IncidentDetailView.jsx`
- `src/views/IntersectionsView.jsx`
- `src/views/PredictionsView.jsx`
- `src/views/RoadDetailView.jsx`
- `src/views/ScenarioSimulatorView.jsx`
- `src/views/SystemHealthView.jsx`
- `src/views/ThreatHuntingView.jsx`
- `src/views/ThreatIntelligenceView.jsx`
- `src/views/TrafficSignalsView.jsx`
- `src/views/UserSecurityView.jsx`

Example excerpt from `traffic/frontend/src/views/AIAssistantView.jsx`:
```jsx
<<<<<<< HEAD
import React, { useState } from 'react';
import { HelpCircle, Send, Cpu, CheckCircle, ShieldCheck, ArrowRight } from 'lucide-react';
=======
import React, { useState, useEffect } from 'react';
...
>>>>>>> feature/ai-assistant-revamp
```

By contrast, `finance/frontend/traffic_src/` contains the resolved, clean, production-ready React Vite code where all conflict blocks were properly resolved.

**Conclusion**: `traffic/frontend/` is a broken artifact of an incomplete Git merge. `finance/frontend/traffic_src/` is the single authoritative source for the Smart Traffic React interface.

---

## 4. Deep Dive: Finance Cyber Risk Copies

The repository contains a nested directory structure:
`finance/backend/finance_cyber_risk/finance-cyber-risk/`

### Unique Functionality Identified:
- **Trained Machine Learning Models (`artifacts/models/`)**:
  - `xgb_fraud.joblib`: 550,000-record trained Indian Banking XGBoost fraud classifier.
  - `isolation_forest.joblib`: High-dimensional unsupervised anomaly detector.
  - `aml_model.joblib`: AMLSim money laundering typology classifier.
- **Risk Engine (`src/risk_engine/`)**:
  - `unified_risk.py`: Synthesizes anomaly score, fraud probability, and AML risk into composite score ($0 - 100$).
  - `cyber_var.py`: Cyber Value-at-Risk monetary exposure quantifier (calculating expected monetary loss in ₹).
  - `dynamic_risk.py`: Time-decay weighted risk accumulator.
- **Service Integration (`finance/backend/services/finance_risk_engine.py`)**:
  - Bridge service loaded by `main.py` for `/api/finance/assess-unified` and `/api/finance/engine-status`.

**Conclusion**: The nested sub-repository `finance-cyber-risk` contains core IP and will be elevated to `securox/backend/app/domains/finance/`.

---

## 5. Stale Database & Scratch Files

### Stale Database Artifacts:
- `database/securox.db`: Size = **0 bytes**. Created as an empty file placeholder. Safe to remove.
- `database/cameras.json` (415 B) & `database/camera_key.key` (44 B): Active encryption keys and camera metadata. Must be preserved.
- `finance/backend/database/securox.db`: 73.4 MB SQLite database containing 21 tables, 41 seeded users, 5 patients, 3 traffic signals, 3 bank accounts, audit logs, and security policies. Authoritative primary database.

### Scratch Files:
`finance/scratch/` contains 14 temporary test and inspection scripts:
- `find_cameras.py`, `inject_img.py`, `test_api.py`, `test_api_get.py`, `test_api_status.py`, `test_generator.py`, `test_http.py`, `test_ports.py`, `test_public_rtsp.py`, `test_rtsp.py`, `test_stig.py`, `test_stream_frame.jpg`, `test_stream_local.py`, `test_stream_response.py`.
- None of these are imported by application code or executed by pytest.
- Action: Safely move to `archive/scratch/`.

---

## 6. Action Plan for Authoritative Consolidation

1. **Create `archive/`** at repository root:
   - Move `traffic/` $\rightarrow$ `archive/legacy_traffic/`.
   - Move `finance/scratch/` $\rightarrow$ `archive/scratch/`.
   - Remove `database/securox.db` (0-byte empty file).
2. **Establish `securox/` target architecture**:
   - `securox/backend/app/domains/traffic/` $\leftarrow$ `finance/backend/traffic_core/`
   - `securox/backend/app/domains/healthcare/` $\leftarrow$ `finance/backend/healthcare_core/`
   - `securox/backend/app/domains/finance/` $\leftarrow$ `finance/backend/finance_cyber_risk/finance-cyber-risk/`
   - `securox/backend/app/security/` $\leftarrow$ `finance/backend/auth/`
   - `securox/backend/app/core/` $\leftarrow$ `finance/backend/database/` + config
   - `securox/backend/app/api/` $\leftarrow$ `finance/backend/main.py` gateway
   - `securox/frontend/` $\leftarrow$ `finance/frontend/`
   - `securox/datasets/` $\leftarrow$ `finance/data/`
   - `securox/models/` $\leftarrow$ `finance/models/`
   - `securox/tests/` $\leftarrow$ `finance/tests/`
3. **Preserve Compatibility**:
   - Keep import bridges so that running tests from `finance/` or `securox/` both succeed 100%.
4. **Verification**:
   - Execute full 60-test pytest suite.
   - Verify server startup and route integration.
