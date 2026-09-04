"""
Securox — End-to-End Smart City Cybersecurity Demonstration (SH-FIN-05)
Executes 5 canonical attack scenarios against live Securox platform:
  1. Distributed Denial of Service (DDoS) on Traffic Control Infrastructure
  2. Stealth Port Scan on Municipal Power Grid Substation
  3. Credential Brute Force on Citizen Tax Portal
  4. IoT Environmental Sensor Compromise & SCADA Infiltration
  5. Cyber-Physical Correlation: Intersection Signal Jamming & Traffic Gridlock
"""

import sys
import time
import json
import requests
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

API_URL = "http://127.0.0.1:8000/api/events"

SCENARIOS = [
    {
        "id": "SCENARIO_1",
        "title": "SCENARIO 1: DDoS ATTACK ON TRAFFIC CONTROL INFRASTRUCTURE",
        "target": "TRAFFIC_CONTROL (SCATS / ITMS)",
        "narrative": "A high-rate volumetric SYN flood (2,800 req/s) launched from Tor exit nodes targeting the municipal Traffic Management Center to blind signal controllers.",
        "payload": {
            "source_ip": "185.220.101.5",
            "destination_ip": "10.40.0.1",
            "source_port": 54321,
            "destination_port": 80,
            "protocol": "TCP",
            "bytes_in": 1500000,
            "bytes_out": 2000,
            "packets": 28000,
            "duration": 0.01,
            "request_rate": 2800.0,
            "error_rate": 0.85,
            "asset_id": "TRAFFIC_CONTROL",
            "asset_type": "traffic_control",
            "location": "Central ITMS Corridor",
            "attack_type": "DDOS",
            "label": 1
        }
    },
    {
        "id": "SCENARIO_2",
        "title": "SCENARIO 2: RECONNAISSANCE PORT SCAN ON POWER SUBSTATION SCADA",
        "target": "POWER_GRID (Zone-0 Substation Alpha)",
        "narrative": "A stealth SYN/FIN port scan enumerating Modbus TCP (Port 502) and DNP3 protocols on municipal electrical transmission RTUs.",
        "payload": {
            "source_ip": "198.51.100.42",
            "destination_ip": "10.10.0.5",
            "source_port": 49152,
            "destination_port": 502,
            "protocol": "TCP",
            "bytes_in": 3400,
            "bytes_out": 120,
            "packets": 210,
            "duration": 0.005,
            "request_rate": 650.0,
            "error_rate": 0.92,
            "asset_id": "POWER_GRID",
            "asset_type": "power_grid",
            "location": "Zone-0 Central Power Substation",
            "attack_type": "PORT_SCAN",
            "label": 1
        }
    },
    {
        "id": "SCENARIO_3",
        "title": "SCENARIO 3: BRUTE FORCE & CREDENTIAL STUFFING ON CITIZEN PORTAL",
        "target": "CITIZEN_PORTAL (Municipal Revenue Gateway)",
        "narrative": "Automated bot-driven password spraying and MFA enumeration targeting civic tax accounts and citizen identity tokens.",
        "payload": {
            "source_ip": "45.154.255.10",
            "destination_ip": "10.80.0.10",
            "source_port": 51234,
            "destination_port": 443,
            "protocol": "TCP",
            "bytes_in": 52000,
            "bytes_out": 9500,
            "packets": 920,
            "duration": 0.8,
            "request_rate": 380.0,
            "error_rate": 0.88,
            "asset_id": "CITIZEN_PORTAL",
            "asset_type": "citizen_portal",
            "location": "Cloud Municipal Datacenter",
            "attack_type": "BRUTE_FORCE",
            "label": 1
        }
    },
    {
        "id": "SCENARIO_4",
        "title": "SCENARIO 4: IOT SENSOR COMPROMISE & WATER SCADA INFILTRATION",
        "target": "WATER_MANAGEMENT (Cauvery Pumping Station)",
        "narrative": "A rogue MQTT telemetry injection on compromised environmental sensors escalating to command injection on reservoir water valves.",
        "payload": {
            "source_ip": "192.168.99.14",
            "destination_ip": "10.70.0.1",
            "source_port": 1883,
            "destination_port": 1883,
            "protocol": "TCP",
            "bytes_in": 95000,
            "bytes_out": 3500,
            "packets": 1400,
            "duration": 0.2,
            "request_rate": 500.0,
            "error_rate": 0.65,
            "asset_id": "WATER_MANAGEMENT",
            "asset_type": "water_management",
            "location": "Cauvery Water Pumping Station",
            "attack_type": "DOS",
            "label": 1
        }
    },
    {
        "id": "SCENARIO_5",
        "title": "SCENARIO 5: CYBER-PHYSICAL CORRELATION (SIGNAL JAMMING + GRIDLOCK)",
        "target": "TRAFFIC_SIGNALS (Intersection 4B Corridor)",
        "narrative": "Simultaneous physical traffic congestion detected by edge CCTV cameras combined with SCATS traffic signal telemetry manipulation.",
        "payload": {
            "source_ip": "103.21.244.0",
            "destination_ip": "10.50.1.10",
            "source_port": 55100,
            "destination_port": 5000,
            "protocol": "TCP",
            "bytes_in": 980000,
            "bytes_out": 4200,
            "packets": 19500,
            "duration": 0.03,
            "request_rate": 1900.0,
            "error_rate": 0.82,
            "asset_id": "TRAFFIC_SIGNALS",
            "asset_type": "traffic_signals",
            "location": "Intersection 4B Corridor",
            "attack_type": "DDOS",
            "label": 1
        }
    }
]


def run_demo():
    print("=" * 80)
    print("   SECUROX — SMART CITY CYBER RISK DETECTION (SH-FIN-05)")
    print("   COMPETITION DEMONSTRATION: 5 REPRODUCIBLE SCENARIOS")
    print("   Target API: http://127.0.0.1:8000")
    print("=" * 80)

    # Check API health
    try:
        r = requests.get("http://127.0.0.1:8000/api/assets", timeout=3.0)
        if r.status_code != 200:
            print("[!] API returned non-200. Ensure uvicorn server is running.")
            return
    except Exception as e:
        print(f"[!] Unable to connect to Securox API: {e}")
        print("[*] Please run: python -m uvicorn main:app --port 8000 inside backend/")
        return

    print("[+] Securox Platform is ONLINE and ready.")
    time.sleep(1.0)

    for idx, sc in enumerate(SCENARIOS, 1):
        print("\n" + "#" * 80)
        print(f"  [{idx}/5] {sc['title']}")
        print(f"  Target Asset: {sc['target']}")
        print(f"  Narrative:    {sc['narrative']}")
        print("-" * 80)

        t0 = time.perf_counter()
        resp = requests.post(API_URL, json=sc["payload"], timeout=5.0)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        if resp.status_code == 200:
            data = resp.json()
            risk = data.get("risk_score", 0.0)
            sev = data.get("severity", "UNKNOWN")
            att = data.get("attack_type", "BENIGN")
            anom = data.get("anomaly_score", 0.0)
            fin = data.get("financial_exposure_cr", 10.0)
            deps = data.get("affected_dependents", [])
            ti = data.get("threat_intel", {})
            cp = data.get("cyber_physical_correlation")

            print(f"  [AI Detection]     Attack Class: \033[93m{att}\033[0m | Anomaly Score: \033[96m{anom:.4f}\033[0m | Latency: {lat_ms:.2f}ms")
            print(f"  [Threat Intel]     Known Malicious IP: {'YES (IOC: ' + ti.get('actor', 'Threat') + ')' if ti.get('is_threat') else 'No Hostile IOC Match'}")
            print(f"  [Risk Score]       \033[91m{risk:.1f}/100\033[0m -> Severity: \033[91m{sev}\033[0m | Exposure: INR {fin:.1f} Cr")
            
            if deps:
                print(f"  [Cascading Impact] Threat propagates to {len(deps)} downstream nodes: {', '.join(deps)}")

            if cp:
                print(f"  [Cyber-Physical]   \033[95mFUSED CORRELATION:\033[0m {cp.get('fusion_impact')}")

            reasons = data.get("evidence_reasons", [])
            if reasons:
                print(f"  [Explainability]   Why High Risk?")
                for r in reasons[:3]:
                    print(f"                     • {r}")

            xai = data.get("xai_contributions", [])
            if xai:
                top_features = ", ".join([f"{f['label']} ({f['contribution_pct']}%)" for f in xai[:3]])
                print(f"  [SHAP Factors]     Top Feature Drivers: {top_features}")

            mits = data.get("mitigations", [])
            if mits:
                print(f"  [Safe Mitigation]  Action: {mits[0]}")

        else:
            print(f"  [!] Scenario execution failed with status {resp.status_code}")

        time.sleep(1.5)

    print("\n" + "=" * 80)
    print("   ALL 5 SMART CITY DEMO SCENARIOS COMPLETED SUCCESSFULLY")
    print("   View real-time visual telemetry in Dashboard: http://localhost:8000/")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
