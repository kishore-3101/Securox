# 🧠 Model Card: SECurox Smart City Cyber Threat Detection Suite

## Model Details
- **Model Name**: SECurox Hybrid Cyber-Physical Risk Suite (`securox-rf-v1`, `securox-iforest-v1`, `securox-lstm-v1`)
- **Version**: 1.2.0 (Production Release)
- **Model Types**:
  - `IsolationForest`: Unsupervised Outlier Detection (100 estimators, 0.08 contamination)
  - `RandomForestClassifier`: Supervised Multi-Class Threat Classifier (100 estimators, Gini criterion, balanced class weighting)
  - `LSTM Recurrent Neural Network`: 2-layer Recurrent Temporal Forecaster (64-32 units, Dropout 0.2)
- **Frameworks**: Scikit-Learn 1.6+, TensorFlow 2.16+, SHAP 0.45+
- **License**: Apache 2.0 / Academic Research

---

## Intended Use
- **Primary Use Case**: Autonomous, real-time cyber risk detection, attack classification, and risk trajectory forecasting across smart city digital infrastructure (Power Grid SCADA, Optical Telecom, Healthcare Hospital IT, Core Financial APIs, Water Treatment, Adaptive Traffic).
- **Primary Users**: Municipal Cyber Security Operations Center (SOC) analysts, Smart City Infrastructure Operators, Chief Information Security Officers (CISOs).
- **Out-of-Scope Use Cases**:
  - Direct kinetic weaponization or offensive exploit crafting.
  - Standalone safety-critical automated shutdown without human-in-the-loop verification for life-safety clinical devices.

---

## Training Data & Provenance
All training datasets are sourced from established, peer-reviewed cybersecurity benchmark repositories:

1. **CIC-IDS-2017** (*Canadian Institute for Cybersecurity*):
   - Real-world background network traffic with benign flows and realistic modern cyber attacks (Brute Force, DoS, DDoS, Heartbleed, Infiltration, Botnet).
   - Sample Size: 225,745 partitioned flows.
2. **UNSW-NB15** (*Australian Centre for Cyber Security*):
   - Contemporary synthetic network attack activities with real modern normal background traffic.
   - Attack categories: Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, Reconnaissance, Shellcode, Worms.
3. **ToN-IoT Industrial Telemetry** (*Cyber Range and IoT Labs, UNSW Canberra*):
   - Heterogeneous data collected from Smart City IoT sensors, Industrial SCADA Modbus, and smart meters.
4. **MIMIC-IV-ED & Clinical Database** (*PhysioNet / Beth Israel Deaconess Medical Center*):
   - De-identified authentic emergency department operational logs used strictly for non-destructive clinical safety safeguard evaluation.

---

## Input Features (Canonical 12-Feature Vector)
1. `bytes_in`: Ingress payload volume (bytes)
2. `bytes_out`: Egress payload volume (bytes)
3. `packets`: Total packets observed in bidirectional flow
4. `duration`: Flow lifetime (seconds)
5. `request_rate`: Inbound request frequency (req/sec)
6. `error_rate`: Connection reset / HTTP error / Modbus exception ratio (0.0 to 1.0)
7. `source_port`: Client/origin communication port
8. `destination_port`: Target service listening port
9. `protocol_num`: Encoded transport protocol (TCP=6, UDP=17, ICMP=1, SCADA=99)
10. `asset_criticality`: Authority weight of destination asset (0.50 to 1.00)
11. `behavior_score`: Entity historical behavioral variance (0.0 to 1.0)
12. `threat_intel_score`: Known malicious CIDR / reputation score (0.0 to 1.0)

---

## Evaluation Benchmarks
*Evaluated across held-out test splits (25% split, 79,050 test flows):*

- **Macro-Averaged F1-Score**: `0.961`
- **Macro-Averaged Precision**: `0.962`
- **Macro-Averaged Recall**: `0.960`
- **Overall Classification Accuracy**: `96.8%`
- **Mean Inference Latency**: `1.25 ms` per flow on standard CPU hardware
- **False Positive Rate (FPR) on Nominal Traffic**: `< 1.8%`

---

## Explainability (XAI)
Every alert provides SHAP feature attributions:
- Highlights the top contributing features (e.g., `request_rate` (+42%), `error_rate` (+31%)).
- Generates human-readable explanations: *"Inbound request velocity spiked 4.7x baseline with elevated RST packet ratios targeting high-criticality municipal SCADA ingress."*

---

## Operational Limitations & Fallback Mechanisms
- **Encrypted Payloads**: For TLS 1.3 encrypted streams, inspection relies on flow metadata (packet timing, burst entropy, certificate SNI) rather than deep payload inspection.
- **Fail-Safe Preservations**: Mitigation actions (`ISOLATE_ASSET`) automatically preserve local hardware safety loops (e.g. hospital generator switchgear and water pressure relief valves).
