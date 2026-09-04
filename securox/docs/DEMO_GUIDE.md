# Securox — Official Presentation & 10-Step Live Demo Guide

## 1. Quick Launch
Start the platform locally on port 8000:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Open browser: **`http://localhost:8000`**

---

## 2. Seeded Demo Accounts (All Passwords: `admin123`)

| Stakeholder Role | Username | Department / Sector | Purpose in Demonstration |
| :--- | :--- | :--- | :--- |
| **Global CISO** | `admin` | Pan-City Defense | Global security posture overview & What-If lab |
| **Super Admin** | `superadmin` | City Governance | Platform-wide control (audited and monitored) |
| **Doctor** | `doctor` | Cardiology Ward | Normal patient charts + Exfiltration simulator |
| **Ambulance Driver** | `ambulance` | Emergency Transit | Mobile-first CAD interface with 6-step mission |
| **Traffic Operator** | `traffic_operator` | TMC Central | STIG signal control & green corridors |
| **Fraud Analyst** | `fraud_analyst` | Core Banking | Suspicious wire fraud & Pre-Emptive Escrow Hold |
| **SOC Threat Hunter** | `soc_analyst` | Tier-3 SOC | Multi-sector incident correlation & XAI forensics |
| **Citizen** | `citizen` | Public Mobility | Clean, non-sensitive road closure alerts |
| **Patient** | `patient` | Inpatient Care | Simple view of personal appointments & Rx |

---

## 3. The 10-Step Official Presentation Story

You can present this story manually or click **`[▶ Auto-Play All 10 Steps]`** in the **Demo Center**:

### Step 1: Hospital Administrator Posture Overview
- **Action**: Switch to `admin` or `hospital_admin`.
- **Narration**: *"The Hospital Administrator reviews hospital bed capacity, IoMT monitor statuses, and cybersecurity health. Baseline posture is nominal (Risk: 12.0)."*

### Step 2: Doctor Normal Patient Record Access
- **Action**: Switch to `doctor` (Dr. Sarah Chen).
- **Narration**: *"Dr. Chen accesses her assigned Cardiology patient P-1001 from her enrolled hospital tablet during morning rounds. Access is granted instantly (ALLOW)."*

### Step 3: Compromised Doctor Device / Mass Exfiltration Attempt
- **Action**: Click **`[Simulate Exfiltration]`** in Doctor portal or Step 3 in Demo Center.
- **Narration**: *"An external threat actor using compromised doctor credentials attempts to export 2,000 unassigned patient records from an unregistered laptop in London at 02:45 AM."*

### Step 4: AI Behavioral Anomaly Detection & Risk Escalation
- **Narration**: *"The AI Risk Engine detects the multi-dimensional anomaly: Impossible Travel ($>800\text{ km/h}$) + Unregistered Device + Off-Hours Shift + Mass Volume Spike. Risk score spikes from 12.0 to 95.0 (CRITICAL)."*

### Step 5: Policy Engine Adaptive Block
- **Narration**: *"The Critical Risk Policy triggers an immediate ADAPTIVE BLOCK. The malicious exfiltration is severed in-flight before any record leaves the hospital database."*
- **Visual**: The glowing red **Access Restricted Modal** appears with the full additive XAI reason receipt.

### Step 6: Hospital Security Incident Dispatch
- **Narration**: *"An automated incident `INC-HC-0089` is dispatched to the Hospital IT Security Officer and City SOC with forensic evidence and recommended playbooks."*

### Step 7: Smart Traffic Signal Manipulation Reversion
- **Action**: Click Step 7 in Demo Center.
- **Narration**: *"Simultaneously, the same attacker probes the Central Zone Traffic Controller attempting an unauthorized SCADA override to turn all signals green. The command is rejected and logged."*

### Step 8: Finance Account Takeover & Pre-Emptive Escrow Freeze
- **Action**: Click Step 8 in Demo Center.
- **Narration**: *"A third strike initiates a ₹4.5M high-velocity wire diversion. The ML fraud engine evaluates the transaction in-flight and executes a Pre-Emptive Escrow Hold, freezing stolen funds."*

### Step 9: Unified Pan-City SOC Alert Integration
- **Action**: Switch to `soc_analyst` or Step 9.
- **Narration**: *"The Tier-3 SOC Analyst opens the unified Security Operations Center, observing alerts across Healthcare, Traffic, and Finance consolidated into a single pane of glass."*

### Step 10: Cross-Domain Coordinated Attack Correlation (Key Differentiator)
- **Action**: Click Step 10 in Demo Center.
- **Narration**: *"Differentiator: The Cross-Domain Correlation Engine links the common Threat Actor IP `198.51.100.77` across Hospital, Traffic, and Finance, raising a unified P1 Pan-City Coordinated Crisis Incident."*
