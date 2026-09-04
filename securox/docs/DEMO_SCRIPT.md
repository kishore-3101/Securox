# ⏱️ SECurox — 3-Minute Live Hackathon Demo Script (SH-FIN-05)

> **Target Audience**: Hackathon Judges, Municipal CISOs, Smart City Infrastructure Directors  
> **Target Problem**: **SH-FIN-05 — AI-Driven Cyber Risk Detection for Smart City Digital Infrastructure**  
> **Total Time**: 180 Seconds (3:00 Minutes)  
> **URL**: `http://localhost:8000` | **Login**: `admin` / `admin123`

---

## 🎬 Time-Stamped Click-by-Click Pitch

### 0:00 – 0:30 | The Hook & Executive City Posture (30s)

* **Speaker**:  
  > *"Good morning, judges. Smart cities interconnect energy, hospitals, financial gateways, and traffic systems into a single digital fabric. But when a cyber attack hits, threats don't stay in silos—they cascade. Traditional dashboards show disjointed alerts. **SECurox** is the next-generation Cyber Operations Center (SOC) that detects, correlates, predicts, and mitigates multi-sector cyber-physical assaults in real-time."*
* **Action in UI**:
  1. Login with `admin` / `admin123`.
  2. The dashboard opens in **Live SOC Mode**.
  3. Point to the topbar:
     - Show **Mode Switcher** (`[ LIVE SOC ]`, `[ ATTACK SIMULATION LAB ]`, `[ EXECUTIVE VIEW ]`, `[ ANALYST VIEW ]`).
     - Point to the **Composite City Risk Indicator**: `18.0 / 100 · NOMINAL`.
  4. Click **[ EXECUTIVE VIEW ]** in the topbar:
     - Show the **Sector Cyber Health Matrix**: Energy (25%), Telecom (20%), Healthcare (20%), Finance (15%), Water (10%), Transport (10%).
     - Highlight that the city risk is mathematically weighted by public safety criticality.

---

### 0:30 – 1:15 | Threat Injection & Attack Campaigns (45s)

* **Speaker**:  
  > *"Now, let's look at the Attack Simulation Lab. We have built 6 canonical real-world scenarios running directly through our production AI pipeline. Let's trigger Scenario 02: Power Grid SCADA Substation Manipulation."*
* **Action in UI**:
  1. Click **[ ATTACK SIMULATION LAB ]** in the topbar (or sidebar `Attack Sim Lab`).
  2. Click the card for **Scenario 02: Power Grid SCADA Manipulation**.
  3. Toast alert pops up: `SCENARIO 02 INJECTED: Power Grid SCADA Manipulation`.
  4. The topbar risk gauge immediately updates: `82.4 / 100 · CRITICAL` (glowing red).
  5. Click **Attack Campaigns** in the sidebar:
     - Show `CAMPAIGN #SEC-2026-xxxx`: The engine has correlated the isolated alert into an active multi-stage campaign!
     - Point out the MITRE kill-chain progression: `Reconnaissance → Initial Access → Lateral Movement → Impact`.
     - Show attacker origin IP: `198.51.100.44` and high confidence score (`94%`).

---

### 1:15 – 1:50 | Predictive "What-If" Cascading Blast Radius (35s)

* **Speaker**:  
  > *"Because smart cities have deep cross-sector dependencies, a power substation outage immediately jeopardizes water pumps, hospital ventilators, and traffic lights. In the SOC, analysts need to know: 'What is the cascading blast radius if this asset fails?'"*
* **Action in UI**:
  1. Click **What-If Simulator** in the sidebar.
  2. Target asset is selected: `POWER_GRID`. Failure modality: `Catastrophic Cyber Attack Outage`.
  3. Click **[ RUN SIMULATION ]**:
     - Blast Radius Gauge appears: **`BLAST RADIUS: 67%`** (8 / 12 assets impacted).
     - Show the **Dependency Propagation Breakdown**:
       - *Root Failure*: `POWER_GRID` (100% outage).
       - *Direct Cascade*: `COMM_NETWORK`, `WATER_SUPPLY`, `TRAFFIC_SYSTEM`.
       - *Secondary Cascade*: `HEALTHCARE`, `EMERGENCY_SVCS`, `FINANCE`.
       - *Unaffected Resilient*: `ENVIRONMENTAL_SENSORS`, `STREET_LIGHTING`.
     - Highlight the system's estimated recovery time (MTTR): `45 mins` and recommended action: `ISOLATE_ASSET`.

---

### 1:50 – 2:30 | Verifiable Cyber Response & State Transition (40s)

* **Speaker**:  
  > *"Detection without mitigation is useless. In SECurox's Cyber Response Center, our response actions are not cosmetic placeholders. They produce stateful, verifiable reductions in asset risk and are cryptographically signed."*
* **Action in UI**:
  1. Click **Cyber Response Center** in the sidebar.
  2. Target asset: `POWER_GRID`. Source IP: `198.51.100.44`.
  3. Show the 6 Canonical Mitigation Buttons:
     `ISOLATE_ASSET`, `BLOCK_SOURCE`, `FAILOVER_BACKUP`, `ENFORCE_MFA`, `RATE_LIMIT`, `ROLLBACK_CONFIG`.
  4. Click **`ISOLATE_ASSET`**:
     - Watch the **Verifiable State Transition Card** update live:
       - **State BEFORE**: `Risk: 88.0 · ELEVATED`
       - **Action Executed**: `ISOLATE_ASSET`
       - **State AFTER**: `Risk: 21.0 · CONTAINED`
       - **Net Risk Reduction**: **`-67.0 pts (76.1% drop)`**
     - The **Cryptographic Mitigation Audit Feed** shows: `VERIFIED · SHA-256 Merkle Hash: 0x4f8e12a9c3d0...`

---

### 2:30 – 3:00 | Forensic Audit & One-Click Incident Report (30s)

* **Speaker**:  
  > *"Finally, compliance and governance. Municipal regulations demand formal auditability. With one click, our platform compiles the forensic telemetry, SHAP XAI weights, blast analysis, and cryptographic proofs into a publication-ready incident report."*
* **Action in UI**:
  1. Click **Incident Investigation** in the sidebar.
  2. Click **[ 📄 GENERATE INCIDENT REPORT ]**:
     - The formal **Municipal Cybersecurity Incident Response Report** modal appears:
       - Classification: `TLP:AMBER / RESTRICTED`
       - Reference: `REF: INC-2026-xxxx`
       - MITRE ATT&CK matrix table (`T1190`, `T0831`, `T1021.002`, `T1498`)
       - Mitigation state transitions & Merkle proof
       - Formal sign-off lines for SOC Lead & City CISO.
     - Show the **[ Print / Save PDF ]** button.
  3. Click **Reset City** in the topbar: All 12 sectors return to nominal green baseline.

* **Closing**:  
  > *"SECurox is 100% offline-first, tested with 35 passing automated tests, and production-ready for smart cities today. Thank you!"*

---

## 💡 Quick Tips for the Presenter
- If judges ask about the AI models, click **AI Model Health** in the sidebar or open the **Data & Model Lab** to demonstrate the replay of `CIC-IDS-2017` or `UNSW-NB15`.
- If judges ask about the mathematical risk formula, click the topbar risk score pill to open the **Risk Formula Modal**.
- If judges want an interactive guided tour, click **`⚡ 13-Phase Demo Tour`** in the topbar and click through the phases.
