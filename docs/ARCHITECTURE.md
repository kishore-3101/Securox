# 🏗️ SECurox Platform Architecture

## 1. Architectural Overview

SECurox is built on a modular, decoupled cyber-physical architecture designed for high-throughput smart-city telemetry processing, real-time threat intelligence correlation, cascading blast radius forecasting, and verifiable automated response.

```
                      ┌────────────────────────────────────────────────┐
                      │          DATA & MODEL INGESTION LAB             │
                      │  CIC-IDS-2017 · UNSW-NB15 · ToN-IoT · NSL-KDD  │
                      └───────────────────────┬────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────┐
                      │          CANONICAL EVENT NORMALIZER            │
                      │  Standardizes all telemetry to 12 Core Vectors │
                      └───────────────────────┬────────────────────────┘
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
      ┌───────────────────────────┐                      ┌───────────────────────────┐
      │   UNSUPERVISED ANOMALY    │                      │   SUPERVISED CLASSIFIER   │
      │     Isolation Forest      │                      │    Multi-Class RF Model   │
      └─────────────┬─────────────┘                      └─────────────┬─────────────┘
                    │                                                  │
                    └─────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────┐
                      │            SHAP EXPLAINABILITY (XAI)           │
                      │     Computes Feature Contribution Attribution   │
                      └───────────────────────┬────────────────────────┘
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
      ┌───────────────────────────┐                      ┌───────────────────────────┐
      │   CAMPAIGN ENGINE CORR.   │                      │    TEMPORAL PREDICTOR     │
      │ Multi-Stage Kill-Chain    │                      │  LSTM Neural Network (5-s)│
      └─────────────┬─────────────┘                      └─────────────┬─────────────┘
                    │                                                  │
                    └─────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────┐
                      │       SMART CITY DIGITAL TWIN (12 ASSETS)      │
                      │    Cascading Failure & Blast Radius Engine     │
                      └───────────────────────┬────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────┐
                      │       VERIFIABLE CYBER RESPONSE CENTER         │
                      │  6 Mitigations · Before/After · Merkle Hash    │
                      └────────────────────────────────────────────────┘
```

---

## 2. Ingestion & Canonical Normalization Layer

Smart city sensors produce disparate data formats—Modbus/TCP register dumps, optical NetFlow, HL7 clinical logs, FastTag toll records, and REST API calls.

The `DatasetNormalizer` transforms any arbitrary input dictionary or CSV row into a standardized `CanonicalEvent`:
- `event_id`: Unique identifier (`EVT-XXXXXXXX`)
- `timestamp`: UTC ISO-8601 timestamp
- `source_ip` / `destination_ip`: IPv4 or IPv6 endpoints
- `source_port` / `destination_port`: TCP/UDP port numbers
- `protocol`: Protocol identification (`TCP`, `UDP`, `MODBUS`, `DNP3`, `HL7`, etc.)
- `bytes_in` / `bytes_out`: Ingress/egress bandwidth
- `packets`: Packet count
- `duration`: Flow duration in seconds
- `request_rate`: Inbound request frequency (req/sec)
- `error_rate`: Connection reset / error ratio (0.0 to 1.0)
- `asset_id`: Targeted smart city node
- `behavior_score`: Entity behavioral deviation metric (0.0 to 1.0)
- `anomaly_score`: Raw sensor out-of-bounds metric
- `threat_intelligence`: Local threat feed lookup (reputation, known hostile CIDRs)

---

## 3. Hybrid Multi-Layer AI Pipeline

### 3.1 Unsupervised Anomaly Detection (`IsolationForest`)
- **Role**: Identifies zero-day deviations without requiring attack labels.
- **Parameters**: 100 decision trees, 0.08 contamination factor.
- **Input Features**: `[bytes_in, bytes_out, packets, duration, request_rate, error_rate]`.

### 3.2 Supervised Multi-Class Classifier (`RandomForestClassifier`)
- **Role**: Categorizes anomalous flows into specific attack techniques:
  - `DDoS` / `Volumetric Flood`
  - `SCADA_INJECTION` / `Modbus Protocol Tamper`
  - `RANSOMWARE` / `Lateral Encryption`
  - `CREDENTIAL_STUFFING` / `Brute Force`
  - `DATA_EXFILTRATION` / `Data Theft`
- **Trained On**: Real-world intrusion benchmarks (`CIC-IDS-2017`, `UNSW-NB15`).

### 3.3 Temporal Risk Trajectory Forecasting (`LSTM`)
- **Role**: Predicts 5-step future risk trajectories from a rolling window of the last 10 telemetry observations.
- **Architecture**: 2-layer Recurrent LSTM with Dropout (0.2) and Dense linear activation head.

### 3.4 Explainable AI (`SHAP`)
- **Role**: Translates black-box ML decisions into plain-English operator briefings and exact feature attribution percentages.

---

## 4. Multi-Stage Attack Campaign Correlation Engine

Rather than inundating SOC analysts with hundreds of disconnected alerts, the `CampaignEngine`:
1. **Groups alerts** by common source IP subnets, targeted dependency corridors, or overlapping time windows.
2. **Maps tactics** across the MITRE ATT&CK kill-chain:
   - `Reconnaissance` → `Initial Access` → `Lateral Movement` → `Impact`
3. **Calculates a Campaign Confidence Score**:
   $$\text{Confidence} = \min\left(0.99, 0.60 + 0.08 \times N_{\text{alerts}} + 0.10 \times N_{\text{stages}}\right)$$
4. **Assigns Unique Campaign IDs**: e.g. `CAMPAIGN #SEC-2026-0042`.

---

## 5. Cascading Failure & Blast Radius Engine

Smart city assets do not fail in isolation. The `CascadeEngine` uses the canonical 12-asset dependency graph with Breadth-First Search (BFS) and depth attenuation:

$$\text{Next\_Impact} = \text{Current\_Score} \times \left(0.80 - \text{Depth} \times 0.08\right)$$

- **Propagation terminates** when impact drops below 0.15 or exceeds maximum depth (4 tiers).
- **Blast Radius Calculation**:
  $$\text{Blast Radius \%} = \frac{\text{Impacted Assets Count}}{12} \times 100$$
- **Evaluates recovery time (MTTR)** and economic disruption metrics dynamically.

---

## 6. Verifiable Cyber Response Center

SECurox replaces passive alerting with **active, stateful mitigation**:
1. `ISOLATE_ASSET`: Quarantines network interfaces while preserving physical life-safety loops.
2. `BLOCK_SOURCE`: Pushes immediate CIDR null-route entries to edge SDN routers.
3. `FAILOVER_BACKUP`: Initiates redundant control takeover to secondary cloud availability zones.
4. `ENFORCE_MFA`: Invalidates active sessions and mandates step-up hardware authentication.
5. `RATE_LIMIT`: Enforces ingress throttling (100 req/s threshold) to suppress volumetric spikes.
6. `ROLLBACK_CONFIG`: Reverts PLC/SCADA configurations to last-known-good Merkle checkpoint.

### Verifiable State Transition
Every execution computes:
- Pre-Mitigation Asset Risk ($R_{\text{before}}$)
- Post-Mitigation Asset Risk ($R_{\text{after}} = \max(12.0, R_{\text{before}} \times (1 - \text{Reduction Ratio}))$)
- Cryptographic SHA-256 Merkle root hash anchoring the transition immutably in SQLite audit store.

---

## 7. Storage & Persistence

All platform states are persisted locally in SQLite (`finance/backend/database/store.db`):
- `alerts`: Historical anomaly alerts with severity and feature payload
- `incidents`: High-severity correlated incident tickets
- `campaigns`: Active and historical multi-stage attack campaigns
- `response_actions`: Verifiable mitigation execution records with before/after metrics
- `simulations`: Audit history of injected scenarios and parameters
- `audit_logs`: Append-only, tamper-evident cryptographic Merkle log
