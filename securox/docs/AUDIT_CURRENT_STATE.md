# Securox — Repository Intelligence & Current State Audit

**Document Version:** 1.0.0  
**Audit Timestamp:** September 2026  
**Auditor:** Senior Software Architect, Lead Security Engineer & AI/ML Specialist  
**Repository Path:** `c:\Users\praja\Downloads\Securox-main (1)\Securox-main`  
**Git Branch / Commit:** `master` (`f53bcc6`)  
**Scope:** Complete repository intelligence audit determining running applications, authoritative components, route-level security, AI invocations, simulations, and dead/duplicate code.

---

## Executive Summary & Core Determinations

1. **Which application is actually running?**
   * **Active Application:** `finance/backend/main.py` executing under Uvicorn (`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`).
   * **Mounts & Integrations:** `main.py` dynamically mounts `traffic_core` routes (41 routes) and `healthcare_core` routes (31 routes), hosting a combined total of **243 routes**.
   * **Port:** `8000` (HTTP and WebSockets).

2. **Which frontend is authoritative?**
   * **Authoritative Runtime Frontend:** `finance/frontend/index.html` (12,680+ lines). Served directly by FastAPI at `/` and `index.html`.
   * **Sub-frontends:**
     * `finance/frontend/traffic_dist/` is mounted statically at `/traffic/` (compiled React 19 build).
     * `finance/frontend/healthcare_dist/` is mounted statically at `/healthcare/` (compiled Vite build; source code missing).
   * **Non-Authoritative Frontend:** `traffic/frontend/` and `finance/frontend/traffic_src/` are dormant React source directories not directly served by the active backend process.

3. **Which backend is authoritative?**
   * **Authoritative Runtime Backend:** `finance/backend/` (specifically `main.py`, `services/`, `auth/access_control.py`, `ml/`, and `simulation/`).
   * **Mounted Sub-Backends:**
     * `finance/backend/traffic_core/` (mounted into `main.py`).
     * `finance/backend/healthcare_core/` (mounted into `main.py`).
     * `finance/backend/finance_cyber_risk/finance-cyber-risk/` (dynamically loaded into `sys.path` by `finance_risk_engine.py`).
   * **Dead Backend:** `traffic/backend/` is a completely unmounted, standalone legacy duplicate at the root.

4. **Which database is authoritative?**
   * **Primary Authoritative Database:** `finance/backend/database/securox.db` (65.6 MB, SQLite WAL mode, 21 tables).
   * **Secondary Active Database:** `finance/backend/traffic_core/traffic.db` (330 KB, SQLite, 19 tables).
   * **Dead Database:** `database/securox.db` at the repository root is an empty 0-byte file containing 0 tables.

5. **Which AI models are actually invoked?**
   * **YOLOv8n ONNX:** `finance/backend/ml/yolov8n.onnx` (12.8 MB) — Invoked for computer vision vehicle/pedestrian inference in `services/cv_engine.py`.
   * **Indian Banking XGBoost Fraud Model:** 550,000-record trained model — Invoked via `finance_risk_engine.py`.
   * **Indian Banking Isolation Forest:** Invoked for anomaly detection in `finance_risk_engine.py`.
   * **AMLSim XGBoost & Graph Risk Contagion:** Invoked for money laundering and multi-hop mule detection in `finance_risk_engine.py`.
   * **Proactive Classifier:** `finance/backend/ml/saved_models/proactive_classifier.joblib` — Invoked for streaming flow risk prediction.
   * **CIC-IDS2017, NSL-KDD, UNSW-NB15 Models:** Pre-trained Random Forests, Isolation Forests, and DBSCAN clusterers in `finance/models/` — Invoked via `services/proactive_ml.py` and `services/analytics_service.py`.
   * **NumPy LSTM Predictor:** `finance/backend/ml/lstm_predictor.py` — Invoked for time-series forecasting.
   * **Digital vs. Physical Disparity Detector:** Invoked in `services/flagship_scenario.py`.

6. **Which simulations are actually functional?**
   * `finance/backend/simulation/attack_scenarios.py`: 21 attack scenarios (DDoS, Ransomware, Insider Threat, IoT Botnet, Metro Fraud, Chennai Flood, Signal Hacking, etc.) — **100% Functional**.
   * `finance/backend/services/flagship_scenario.py`: 12-stage Flagship E-01 multi-domain cascading attack chain — **100% Functional**.
   * `finance/backend/traffic_core/services/scenario_simulator.py`: 9 traffic fault injection scenarios — **100% Functional**.

7. **Which dashboards are actually functional?**
   * All 9 dashboards implemented in `finance/frontend/index.html` are operational:
     1. SOC Command Center (Unified Overview)
     2. Smart City Digital Twin (Topology & GIS Map)
     3. Healthcare Command & CareGuard (Hospital IT & IoMT)
     4. Doctor Portal (Clinical EMR & Patient Context)
     5. Ambulance CAD Portal (Emergency Telemetry & Green Corridor)
     6. Smart Traffic Ops (Signals, Cameras, Toll Gates)
     7. Finance & Fintech Fraud / Cyber-VaR (Banking & AML Contagion)
     8. Executive & Threat Intel (City Health & Exposure Metrics)
     9. Interactive Demo Center (One-click Scenario Launcher)

---

## 2. Complete API Route & Security Inventory (243 Routes)

Every mounted endpoint was inspected for route-level dependencies, parameter models, decorator guards, and handler source code.

### Route Classification Summary
* **`AUTHENTICATED`**: 31 routes (Requires valid JWT via `get_current_user`, but lacks role/context restrictions).
* **`RBAC PROTECTED`**: 9 routes (Enforces specific roles like `ADMIN`, `SOC_ANALYST`, etc.).
* **`ABAC PROTECTED`**: 5 routes (Enforces 5-tuple context evaluation via `access_engine`).
* **`UNAUTHENTICATED`**: 120 routes (Public documentation, Swagger UI, health checks, login, public telemetry feeds).
* **`UNPROTECTED`**: 70 routes (**HIGH RISK:** Operational data routes in traffic, healthcare, devices, and tolling that lack authentication guards).
* **`UNKNOWN`**: 8 routes (WebSockets and static file mounts).

### Full Route Map

| Method | Path | Endpoint / Module | Security Classification | Notes |
|---|---|---|---|---|
| `GET` | `/` | `main.serve_index` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/access/evaluate` | `main.evaluate_access_endpoint` | **`ABAC PROTECTED`** | ABAC Engine; RBAC Role |
| `POST` | `/api/ai-assistant/query` | `traffic_core.app.consult_ai_assistant` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/alerts` | `traffic_core.app.get_alerts` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/alerts` | `main.get_alerts` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/alerts/stats` | `main.alert_stats` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/anomalies` | `main.anomalies` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/assets` | `main.get_all_smart_city_assets` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/assets/{asset_id}` | `main.get_smart_city_asset_detail` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/assets/{asset_id}/blast-radius` | `main.get_asset_blast_radius` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/audit-logs` | `main.audit_logs` | **`UNAUTHENTICATED`** | Deps: require_admin |
| `POST` | `/api/auth/login` | `traffic_core.app.login` | **`UNAUTHENTICATED`** | RBAC Role; Deps: get_db |
| `POST` | `/api/auth/login` | `main.login` | **`UNAUTHENTICATED`** | RBAC Role; Deps: OAuth2PasswordRequestForm |
| `GET` | `/api/auth/me` | `traffic_core.app.get_me` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/auth/roles` | `main.list_rbac_roles` | **`UNAUTHENTICATED`** | RBAC Role |
| `POST` | `/api/auth/switch-role` | `main.switch_rbac_role` | **`UNAUTHENTICATED`** | RBAC Role |
| `GET` | `/api/cameras` | `traffic_core.app.get_cameras` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/cameras` | `main.list_cameras` | **`UNPROTECTED`** | - |
| `POST` | `/api/cameras` | `main.register_camera` | **`UNPROTECTED`** | - |
| `DELETE` | `/api/cameras/{cam_id}` | `main.delete_camera` | **`UNPROTECTED`** | - |
| `GET` | `/api/cameras/{cam_id}` | `main.get_camera` | **`UNPROTECTED`** | - |
| `POST` | `/api/cameras/{cam_id}/anomaly` | `main.inject_camera_anomaly` | **`UNPROTECTED`** | - |
| `GET` | `/api/cameras/{cam_id}/stream` | `main.get_camera_stream` | **`UNPROTECTED`** | - |
| `GET` | `/api/cameras/{camera_id}` | `traffic_core.app.get_camera_details` | **`UNPROTECTED`** | Deps: get_db |
| `POST` | `/api/cameras/{camera_id}/inject-behavior` | `traffic_core.app.inject_camera_behavior` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/cameras/{camera_id}/live-frame` | `traffic_core.app.get_camera_live_frame` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/campaigns` | `main.get_attack_campaigns` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/campaigns/{campaign_id}` | `main.get_attack_campaign_detail` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/campaigns/{campaign_id}/resolve` | `main.resolve_attack_campaign` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/cascade/forecast` | `main.cascade_forecast` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/city-health` | `main.city_health` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/clusters` | `main.cluster_summary` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/command-center/kpis` | `traffic_core.app.get_command_center_kpis` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/command-center/summary` | `traffic_core.app.get_command_center_summary` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/correlation/correlations` | `traffic_core.app.get_active_correlations` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/correlation/status` | `main.get_cyber_physical_correlation_status` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/cyber-weather` | `main.get_city_cyber_weather` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/cyber/asset-security` | `traffic_core.app.get_asset_security` | **`UNAUTHENTICATED`** | Deps: get_db |
| `POST` | `/api/cyber/threat-hunting` | `traffic_core.app.execute_threat_hunt` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/cyber/threats` | `traffic_core.app.get_cyber_threats` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/datasets` | `main.list_available_datasets` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/inject-predict` | `main.inject_and_predict_endpoint` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/replay` | `main.start_dataset_replay_endpoint` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/replay/pause` | `main.pause_replay` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/replay/resume` | `main.resume_replay` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/replay/start` | `main.start_dataset_replay_endpoint` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/datasets/replay/status` | `main.get_replay_status` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/replay/stop` | `main.stop_replay` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/datasets/upload` | `main.upload_dataset_endpoint` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/demo/run` | `main.run_competition_demo_scenarios` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/demo/run-scenario/{scenario_step}` | `main.run_demo_story_step` | **`UNAUTHENTICATED`** | RBAC Role |
| `GET` | `/api/events` | `main.event_stream` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/events` | `main.ingest_smart_city_events` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/events/recent` | `main.get_recent_smart_city_events` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/explain` | `main.explain` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/explanations/{alert_id}` | `main.get_alert_explanation` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/finance/accounts` | `main.list_bank_accounts` | **`UNPROTECTED`** | - |
| `POST` | `/api/finance/assess-unified` | `main.assess_unified_transaction_endpoint` | **`UNPROTECTED`** | - |
| `GET` | `/api/finance/dbscan` | `main.get_dbscan_incident_clusters` | **`UNPROTECTED`** | - |
| `GET` | `/api/finance/engine-status` | `main.get_finance_engine_status` | **`UNPROTECTED`** | - |
| `GET` | `/api/finance/examples` | `main.get_finance_examples` | **`UNPROTECTED`** | - |
| `GET` | `/api/finance/propagation` | `main.get_risk_propagation` | **`UNPROTECTED`** | - |
| `POST` | `/api/finance/simulate-account-takeover` | `main.simulate_finance_takeover` | **`ABAC PROTECTED`** | ABAC Engine; RBAC Role |
| `GET` | `/api/finance/transactions` | `main.list_bank_transactions` | **`UNPROTECTED`** | - |
| `POST` | `/api/finance/transactions` | `main.create_transaction_endpoint` | **`ABAC PROTECTED`** | ABAC Engine; RBAC Role |
| `GET` | `/api/fintech/fraud` | `main.get_fintech_fraud_alerts` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/fintech/metrics` | `main.get_fintech_metrics` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/flagship/decisions` | `main.get_decision_simulation` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/flagship/disparity` | `main.get_digital_physical_disparity` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/flagship/pause` | `main.pause_flagship_scenario` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/flagship/reset` | `main.reset_flagship_scenario` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/flagship/resume` | `main.resume_flagship_scenario` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/flagship/run` | `main.run_flagship_scenario` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/flagship/state` | `main.get_flagship_state` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/flagship/verification` | `main.get_flagship_verification` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/fraud/detect` | `main.detect_fraud` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/fraud/network` | `main.fraud_network` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/fraud/replay` | `main.fraud_replay` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/graph/mule` | `main.get_mule_network_graph` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/health/platform` | `main.get_platform_health` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/healthcare/ambulances` | `main.list_ambulances` | **`UNPROTECTED`** | - |
| `PATCH` | `/api/healthcare/ambulances/{ambulance_id}/status` | `main.update_ambulance` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/assets` | `healthcare_core.api.endpoints.get_assets` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/assets/{asset_id}` | `healthcare_core.api.endpoints.get_asset_detail` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/blast-radius` | `healthcare_core.api.endpoints.get_blast_radius` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/coverage` | `healthcare_core.api.endpoints.get_data_coverage` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/accounting` | `healthcare_core.api.endpoints.get_cyber_accounting` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/categories` | `healthcare_core.api.endpoints.get_cyber_categories` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/cicflowmeter` | `healthcare_core.api.endpoints.get_cyber_cicflowmeter` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/cicids2017` | `healthcare_core.api.endpoints.get_cyber_cicids2017` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/csecicids2018` | `healthcare_core.api.endpoints.get_cyber_csecicids2018` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/devices` | `healthcare_core.api.endpoints.get_cyber_devices` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/hospital-threats` | `healthcare_core.api.endpoints.get_cyber_hospital_threats` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/inventory` | `healthcare_core.api.endpoints.get_cyber_inventory` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/lanl-redteam` | `healthcare_core.api.endpoints.get_cyber_lanl_redteam` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/cyber/overview` | `healthcare_core.api.endpoints.get_cyber_overview` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/datasets` | `healthcare_core.api.endpoints.get_datasets` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/dependencies` | `healthcare_core.api.endpoints.get_dependencies` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/devices` | `healthcare_core.api.endpoints.get_devices` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/evidence` | `healthcare_core.api.endpoints.get_evidence` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/exposure` | `healthcare_core.api.endpoints.get_exposure` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/health` | `healthcare_core.api.endpoints.get_health` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/health-it` | `healthcare_core.api.endpoints.get_health_it` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/incidents` | `healthcare_core.api.endpoints.get_all_incidents` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/incidents/{incident_id}` | `healthcare_core.api.endpoints.get_incident` | **`UNPROTECTED`** | - |
| `POST` | `/api/healthcare/incidents/{incident_id}/stage` | `healthcare_core.api.endpoints.advance_incident_stage` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/infrastructure/status` | `healthcare_core.api.endpoints.get_infrastructure_status` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/overview` | `healthcare_core.api.endpoints.get_overview` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/pathways` | `healthcare_core.api.endpoints.get_pathways` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/pathways/{pathway_id}` | `healthcare_core.api.endpoints.get_pathway_detail` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/patients` | `main.list_patients` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/patients/{patient_id}` | `main.get_patient_detail` | **`UNPROTECTED`** | - |
| `POST` | `/api/healthcare/response` | `healthcare_core.api.endpoints.execute_response_action` | **`UNPROTECTED`** | - |
| `GET` | `/api/healthcare/risk` | `healthcare_core.api.endpoints.get_risk` | **`UNPROTECTED`** | - |
| `POST` | `/api/healthcare/simulate-exfiltration` | `main.simulate_healthcare_exfiltration` | **`ABAC PROTECTED`** | ABAC Engine; RBAC Role |
| `GET` | `/api/healthcare/threats` | `healthcare_core.api.endpoints.get_threats` | **`UNPROTECTED`** | - |
| `GET` | `/api/incidents` | `traffic_core.app.list_incidents` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/incidents` | `main.list_incidents` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `POST` | `/api/incidents` | `main.create_incident` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/incidents/{incident_id}` | `traffic_core.app.get_incident_detail` | **`UNPROTECTED`** | Deps: get_db |
| `PATCH` | `/api/incidents/{incident_id}` | `main.update_incident` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/incidents/{incident_id}/status` | `traffic_core.app.update_incident_status` | **`UNPROTECTED`** | Deps: get_db |
| `POST` | `/api/ingest/camera` | `main.ingest_camera_frame` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/integrations` | `main.get_integrations_history` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/login` | `main.login_alias` | **`UNAUTHENTICATED`** | Deps: OAuth2PasswordRequestForm |
| `GET` | `/api/me` | `main.me` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/metrics` | `main.get_model_evaluation_metrics` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/mitigate` | `main.mitigate` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/mitigations` | `main.get_mitigations` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `POST` | `/api/mitigations/execute` | `main.execute_mitigation` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/ml/core4/evaluate` | `main.evaluate_core4_endpoint` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/ml/core4/status` | `main.get_core4_status` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/model-health` | `main.get_model_health` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/nodes` | `main.nodes` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/playbooks` | `main.playbooks` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/predict` | `main.predict` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/proactive/evaluate` | `main.evaluate_pre_transaction` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/proactive/interceptions` | `main.get_proactive_interceptions` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/proactive/metrics` | `main.get_proactive_metrics` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/proactive/radar` | `main.get_proactive_radar` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/proactive/train` | `main.train_on_real_data` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/real-world/status` | `main.real_world_status` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/recommendations` | `main.recommendations` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/register` | `main.register_user` | **`UNAUTHENTICATED`** | RBAC Role; Deps: require_admin |
| `GET` | `/api/replay` | `main.replay` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/reports/incident` | `main.generate_incident_report_endpoint` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/reports/incident/{incident_id}` | `main.generate_incident_report_endpoint` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/response/actions` | `main.get_response_actions_history` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/response/execute` | `main.execute_response_mitigation` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/risk/city` | `main.city_risk` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/risk/current` | `traffic_core.app.get_current_risk_report` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/risk/history` | `main.risk_history` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/risk/lstm` | `main.lstm_forecast` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/scenarios` | `traffic_core.app.get_scenarios` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/scenarios/reset` | `traffic_core.app.reset_simulation` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/scenarios/{scenario_id}/launch` | `traffic_core.app.launch_scenario` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/sdg/impact` | `main.get_sdg_impact` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/search` | `main.search_endpoint` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/bayes` | `main.get_bayesian_threat_inference` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/canaries` | `main.get_canary_incidents` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/counterfactual` | `main.get_counterfactual_explanation` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/cross-domain-threats` | `main.list_cross_domain_threats` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/devices` | `main.list_devices` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/firmware` | `main.get_firmware_attestation` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/merkle` | `main.get_merkle_audit_ledger` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/policies` | `main.list_security_policies` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/posture-score` | `main.get_security_posture_score` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/security/user-risk-profile/{username}` | `main.get_user_profile` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate` | `main.run_simulation` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/simulate/chained` | `main.run_chained_simulation` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate/custom` | `main.run_custom_scenario` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate/normal` | `main.reset_to_normal_city_operations` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate/normal-operations` | `main.reset_to_normal_city_operations` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate/scenario/{scenario_id}` | `main.run_scenario_by_id` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/simulate/scenarios` | `main.list_scenarios` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/simulate/what-if` | `main.run_what_if_analysis` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/stats` | `main.system_stats` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/system/audit-logs` | `traffic_core.app.get_audit_logs` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/system/health` | `traffic_core.app.get_system_health` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/api/team/validation` | `main.get_team_validation` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/telemetry` | `main.ingest_smart_city_events` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/threat-intel/lookup/{indicator}` | `main.lookup_threat_indicator` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/threat-intel/stats` | `main.get_threat_intel_stats` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/threats` | `main.threats` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `POST` | `/api/toll/{transaction_id}/override` | `traffic_core.app.override_toll` | **`UNPROTECTED`** | Deps: get_db |
| `POST` | `/api/toll/{transaction_id}/report` | `traffic_core.app.report_toll` | **`UNPROTECTED`** | Deps: get_db |
| `POST` | `/api/traffic/actuators/raw_override` | `main.honeypot_canary_trap` | **`UNPROTECTED`** | - |
| `GET` | `/api/traffic/analytics` | `main.traffic_analytics` | **`AUTHENTICATED`** | Deps: get_current_user |
| `WS/MOUNT` | `/api/traffic/camera-relay-ws` | `main.camera_relay_ws` | **`UNKNOWN`** | RBAC Role |
| `GET` | `/api/traffic/cameras` | `main.list_traffic_cameras` | **`UNPROTECTED`** | - |
| `POST` | `/api/traffic/green-corridor` | `main.trigger_green_corridor` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/traffic/intersections` | `traffic_core.app.get_intersections` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/live` | `main.traffic_live` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/traffic/mobile-cam-info` | `main.get_mobile_cam_info` | **`UNPROTECTED`** | - |
| `POST` | `/api/traffic/override-signal` | `main.override_signal` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/traffic/predictions/{road_id}` | `traffic_core.app.get_road_predictions` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/roads` | `traffic_core.app.get_roads` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/roads/{road_id}` | `traffic_core.app.get_road_detail` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/sensors` | `traffic_core.app.get_sensors` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/signals` | `traffic_core.app.get_traffic_signals` | **`UNPROTECTED`** | Deps: get_db |
| `GET` | `/api/traffic/signals` | `main.list_traffic_signals` | **`UNPROTECTED`** | - |
| `PATCH` | `/api/traffic/signals/{signal_id}/override` | `main.override_traffic_signal` | **`UNPROTECTED`** | RBAC Role |
| `POST` | `/api/traffic/signals/{signal_id}/override` | `traffic_core.app.override_traffic_signal` | **`UNPROTECTED`** | Deps: get_db |
| `POST` | `/api/traffic/simulate-signal-tamper` | `main.simulate_traffic_signal_tamper` | **`ABAC PROTECTED`** | ABAC Engine; RBAC Role |
| `GET` | `/api/traffic/stats` | `main.get_traffic_stats` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/traffic/upload-video` | `main.upload_traffic_video` | **`UNPROTECTED`** | - |
| `GET` | `/api/traffic/violations` | `main.get_traffic_violations` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/transactions/live` | `main.transactions_live` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/transactions/risk` | `main.transaction_risk` | **`AUTHENTICATED`** | Deps: get_current_user |
| `POST` | `/api/twin/reset` | `main.twin_reset` | **`AUTHENTICATED`** | Deps: get_current_user |
| `GET` | `/api/twin/state` | `main.twin_state` | **`RBAC PROTECTED`** | RBAC Role; Deps: get_current_user |
| `GET` | `/api/users` | `traffic_core.app.list_users` | **`UNAUTHENTICATED`** | RBAC Role; Deps: get_db |
| `GET` | `/api/users/{username}/risk` | `traffic_core.app.get_user_risk_profile` | **`UNAUTHENTICATED`** | RBAC Role; Deps: get_db |
| `POST` | `/api/v1/treasury/backdoor_disburse` | `main.honeypot_canary_trap` | **`UNAUTHENTICATED`** | - |
| `POST` | `/api/webrtc/signal` | `main.handle_webrtc_signal` | **`UNAUTHENTICATED`** | - |
| `GET` | `/api/webrtc/signals/{session_id}` | `main.get_webrtc_signals` | **`UNAUTHENTICATED`** | - |
| `WS/MOUNT` | `/api/ws` | `traffic_core.app.websocket_endpoint` | **`UNKNOWN`** | - |
| `WS/MOUNT` | `/api/ws` | `main.websocket_endpoint` | **`UNKNOWN`** | - |
| `GET` | `/api/xai/summary` | `main.get_xai_summary` | **`UNAUTHENTICATED`** | - |
| `WS/MOUNT` | `/assets` | `N/A.N/A` | **`UNKNOWN`** | - |
| `GET/HEAD` | `/docs` | `fastapi.applications.swagger_ui_html` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/docs` | `fastapi.applications.swagger_ui_html` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/docs/oauth2-redirect` | `fastapi.applications.swagger_ui_redirect` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/docs/oauth2-redirect` | `fastapi.applications.swagger_ui_redirect` | **`UNAUTHENTICATED`** | - |
| `POST` | `/extract-plate` | `traffic_core.app.extract_plate` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/favicon.svg` | `main.serve_favicon` | **`UNAUTHENTICATED`** | - |
| `GET` | `/healthcare` | `main.serve_healthcare_portal` | **`UNAUTHENTICATED`** | - |
| `GET` | `/healthcare-portal` | `main.serve_healthcare_portal` | **`UNAUTHENTICATED`** | - |
| `WS/MOUNT` | `/healthcare/assets` | `N/A.N/A` | **`UNKNOWN`** | - |
| `GET` | `/mobile-cam` | `main.serve_mobile_cam` | **`UNAUTHENTICATED`** | - |
| `GET` | `/mobile-camera` | `main.serve_mobile_cam` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/openapi.json` | `fastapi.applications.openapi` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/openapi.json` | `fastapi.applications.openapi` | **`UNAUTHENTICATED`** | - |
| `POST` | `/process-toll` | `traffic_core.app.process_toll` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET/HEAD` | `/redoc` | `fastapi.applications.redoc_html` | **`UNAUTHENTICATED`** | - |
| `GET/HEAD` | `/redoc` | `fastapi.applications.redoc_html` | **`UNAUTHENTICATED`** | - |
| `POST` | `/resolve-anomaly` | `traffic_core.app.resolve_anomaly` | **`UNAUTHENTICATED`** | Deps: get_db |
| `GET` | `/scans` | `traffic_core.app.get_recent_scans` | **`UNAUTHENTICATED`** | Deps: get_db |
| `WS/MOUNT` | `/static` | `N/A.N/A` | **`UNKNOWN`** | - |
| `GET` | `/traffic` | `main.serve_traffic_portal` | **`UNAUTHENTICATED`** | - |
| `GET` | `/traffic-portal` | `main.serve_traffic_portal` | **`UNAUTHENTICATED`** | - |
| `WS/MOUNT` | `/uploads` | `N/A.N/A` | **`UNKNOWN`** | - |
| `WS/MOUNT` | `/ws` | `main.websocket_endpoint` | **`UNKNOWN`** | - |

---

## 3. Production vs. Demo vs. Simulated Logic Breakdown

### 3.1 Genuinely Production Logic
* **Access Control Engine (`auth/access_control.py`):** Enterprise-grade 5-tuple evaluation algorithm computing risk scores, emergency multipliers, and policy evaluation.
* **Merkle Vault (`security/merkle_vault.py`):** Authentic cryptographic SHA-256 Merkle chain anchoring audit log integrity.
* **ML Model Inference Pipelines:** Native Scikit-learn, ONNX Runtime, and XGBoost model inference pipelines executing on real feature vectors.
* **Database Persistence Layer (`store.py`):** Parametric SQLite operations running in WAL mode with connection management.
* **Authentication Infrastructure (`jwt_auth.py`):** PBKDF2-HMAC-SHA256 password hashing with 260,000 rounds and HS256 JWT generation.

### 3.2 Demo-Only Logic
* **Persona Quick-Switcher:** Floating topbar pill interface that allows instant 1-click role impersonation without entering passwords.
* **Instant Green Corridor Preemption:** Intersections switch instantly to green without standard amber transition clearing phases.
* **Canary IP Banning:** Honeytokens trigger mock in-memory IP bans rather than writing iptables/nftables firewall rules.
* **Auto-Refreshing Attack Scenario Loop:** Scenarios produce simulated events into memory queues for continuous visual dashboard activity.

### 3.3 Hard-Coded Functionality
* **Default JWT Secret:** `jwt_auth.py` falls back to `"securox-super-secret-key-change-in-production-2024"` if the `SECRET_KEY` environment variable is not defined.
* **External Dataset Paths:** `healthcare_core/core/config.py` hardcodes local Windows filesystem paths (`C:\Users\praja\Downloads\Healthcare\datasets`).
* **Fixed Sensor Coordinates:** Camera locations, intersections, and hospital coordinates in `cameras.json` and `city_twin.py` are static geospatial constants.

### 3.4 Simulated Functionality
* **CCTV Video Feeds:** Simulated using static JPEG frames and Canvas loop renderers rather than live RTSP/WebRTC hardware IP camera streams.
* **TPM 2.0 Hardware Attestation:** Simulated using cryptographically random hashes rather than physical TPM PCR registers.
* **Inductive Road Loop Sensors:** Telemetry vehicle counts are generated based on mathematical density distributions.

### 3.5 Genuinely Data-Driven Functionality
* **Network Threat Ingestion:** Ingests authentic CIC-IDS2017 (2.09M flows), UNSW-NB15, and NSL-KDD datasets.
* **Clinical Health Records:** Loads organic MIMIC-IV-ED, MIMIC-IV Clinical, and eICU database demo records.
* **Banking Transactions & AML Contagion:** Real Indian banking transaction features and AMLSim graph network topology.
* **Toll Transactions:** Authentic FastTag toll scans and distance matrices loaded from CSV files.

---

## 4. Duplicate Files & Dead Code Inventory

### 4.1 Duplicate Directories & Files
1. **`traffic/backend/` vs `finance/backend/traffic_core/`:**
   * `traffic/backend/` is an exact legacy precursor to `finance/backend/traffic_core/`.
   * **Status:** `finance/backend/traffic_core/` is active and mounted; `traffic/backend/` is DEAD.
2. **`traffic/frontend/` vs `finance/frontend/traffic_src/`:**
   * Exact copies of React 19 source code.
   * **Status:** Neither is directly served (pre-built `traffic_dist` is served). Both are duplicates.
3. **`traffic/backend/tests/` vs `finance/backend/traffic_core/tests/`:**
   * Identical 4 test files (`test_cyber_and_correlation.py`, `test_density_and_anomaly.py`, `test_e2e_soc_flow.py`, `test_incident_and_auth.py`).

### 4.2 Dead Code & Stale Artifacts
1. **`database/securox.db` (Root):** 0 bytes, 0 tables. Stale initialization artifact.
2. **`database/cameras.json` (Root):** 415 bytes. Superseded by `finance/backend/database/cameras.json` (3,146 bytes).
3. **`finance/scratch/`:** 14 ad-hoc testing scripts left in version control:
   * `find_cameras.py`, `inject_img.py`, `test_api.py`, `test_api_get.py`, `test_api_status.py`, `test_generator.py`, `test_http.py`, `test_ports.py`, `test_public_rtsp.py`, `test_rtsp.py`, `test_stig.py`, `test_stream_frame.jpg`, `test_stream_local.py`, `test_stream_response.py`.

---

*End of Current State Audit.*
