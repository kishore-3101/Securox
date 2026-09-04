"""
Securox — Attack Simulation Engine
Generates realistic attack telemetry for all four scenario types.
Each scenario returns a sequence of events that can be injected
into the ingestion pipeline to drive the ML models and risk engine.
"""

import asyncio
import logging
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Optional, List, Dict, Any

logger = logging.getLogger("securox.simulation")

SCENARIOS = {
    "SCENARIO_01": "DDoS Against Traffic Control Infrastructure",
    "SCENARIO_02": "Power Grid Substation SCADA Intrusion",
    "SCENARIO_03": "Financial & Municipal Treasury Cyber Attack",
    "SCENARIO_04": "Healthcare & Hospital IoMT Telemetry Incursion",
    "SCENARIO_05": "Water Reservoir SCADA & Pump Tampering",
    "SCENARIO_06": "Coordinated Multi-Stage Smart City Attack Campaign (Showcase)",
    "CUSTOM_BUILDER": "Interactive Custom Attack Scenario Builder",
    "FIN-001": "UPI Credential Stuffing & Rate Abuse",
    "FIN-002": "Account Takeover & High-Velocity Burst",
    "FIN-003": "FASTag Cloning & 6600 km/h Impossible Speed",
    "FIN-004": "Municipal Treasury Manipulation & Ransomware",
    "FIN-005": "Tax Database Exfiltration",
    "FIN-006": "Payment API Gateway Abuse",
    "FIN-007": "Money Mule Network Fan-In / Fan-Out Burst",
    "FIN-008": "Smart Utility Billing Tariff Manipulation",
    "FIN-009": "Metro Transit Ticketing Fraud",
    "FIN-010": "Hospital Insurance Billing Fraud",
    "FIN-011": "Ransomware + Municipal Treasury Disruption",
    "FIN-012": "Cross-Domain Cyber-Financial Cascading Attack",
    "CHAINED_FINANCIAL": "Coordinated Smart City Cyber-Financial Campaign (FIN-001 to FIN-005)",
    "ddos":              "DDoS Attack",
    "ransomware":        "Ransomware Propagation",
    "financial_fraud":   "Financial Fraud Burst",
    "insider_threat":    "Insider Threat Scenario",
    "iot_botnet":        "IoT Botnet Propagation",
    "toll_cyberattack":  "Smart Toll Cyberattack",
    "metro_fraud":       "Metro Ticketing Fraud",
}

# Attacker IP pools
ATTACKER_IPS = [f"198.51.100.{i}" for i in range(1, 80)]
INTERNAL_IPS = [f"10.0.{i}.{j}" for i in range(1, 10) for j in range(1, 30)]
BOTNET_IPS   = [f"203.0.113.{i}" for i in range(1, 120)]
STATE_CODES = ["KA", "MH", "DL", "TN", "TS", "AP", "HR", "UP"]
REGISTRATION_NUMS = [
    f"{random.choice(STATE_CODES)}-{random.randint(1,99):02d}-"
    f"{chr(random.randint(65,90))}{chr(random.randint(65,90))}-{random.randint(1000,9999)}"
    for _ in range(200)
]


class AttackSimulator:

    # ── DDoS ──────────────────────────────────────────────────────────────────
    async def ddos_attack(self, target_asset: str = "traffic_system",
                          duration_steps: int = 30) -> AsyncGenerator[dict, None]:
        """
        Simulates volumetric DDoS: request rate ramps up 10× over duration_steps.
        """
        logger.info("Starting DDoS simulation on %s", target_asset)
        base_rate = 100
        for step in range(duration_steps):
            multiplier = 1 + (step / duration_steps) * 9   # ramp 1× → 10×
            n_sources  = random.randint(5, 20)
            for _ in range(n_sources):
                src_ip = random.choice(ATTACKER_IPS)
                event  = {
                    "event_id":     str(uuid.uuid4()),
                    "type":         "network_traffic",
                    "timestamp":    datetime.now(timezone.utc).isoformat(),
                    "asset_type":   target_asset,
                    "src_ip":       src_ip,
                    "dst_ip":       f"10.0.1.{random.randint(1,10)}",
                    "src_port":     random.randint(1024, 65535),
                    "dst_port":     80,
                    "protocol":     "TCP",
                    "packet_count": int(base_rate * multiplier * random.uniform(0.8, 1.2)),
                    "bytes_sent":   int(64 * base_rate * multiplier),
                    "bytes_recv":   random.randint(0, 100),
                    "conn_duration": random.uniform(0.001, 0.05),
                    "flags":        ["SYN"],
                    "pkt_variance": random.uniform(10, 50),
                    "attack_step":  step,
                    "scenario":     "DDoS",
                }
                yield event
            await asyncio.sleep(0.02)

    # ── Insider Threat ────────────────────────────────────────────────────────
    async def insider_threat(self, target_asset: str = "finance",
                              duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        """
        Simulates a malicious insider: off-hours access, privilege escalation,
        bulk data reads.
        """
        logger.info("Starting insider threat simulation on %s", target_asset)
        victim_ip  = random.choice(INTERNAL_IPS)
        off_hour   = 3   # 3 AM

        for step in range(duration_steps):
            sim_hour = (off_hour + step // 5) % 24
            event_type = random.choice([
                "failed_sudo", "bulk_read", "config_access",
                "credential_reuse", "large_export"
            ])

            event = {
                "event_id":   str(uuid.uuid4()),
                "type":       "system_log",
                "timestamp":  (datetime.now(timezone.utc)
                               .replace(hour=sim_hour)).isoformat(),
                "asset_type": target_asset,
                "source_ip":  victim_ip,
                "service":    target_asset,
                "level":      "WARNING" if step < 10 else "CRITICAL",
                "message":    self._insider_message(event_type, step),
                "user":       f"employee_{random.randint(100, 999)}",
                "endpoint":   f"/api/v1/{random.choice(['records','export','admin','config'])}",
                "scenario":   "INSIDER_THREAT",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── IoT Botnet ────────────────────────────────────────────────────────────
    async def iot_botnet(self, target_asset: str = "power_grid",
                          duration_steps: int = 25) -> AsyncGenerator[dict, None]:
        """
        Simulates a Mirai-style IoT botnet: large fleet of devices phoning home
        and launching coordinated attacks.
        """
        logger.info("Starting IoT botnet simulation on %s", target_asset)
        bot_fleet = random.sample(BOTNET_IPS, min(50, len(BOTNET_IPS)))

        for step in range(duration_steps):
            active_bots = bot_fleet[:max(2, int(len(bot_fleet) * step / duration_steps))]
            for bot_ip in random.sample(active_bots, min(5, len(active_bots))):
                event = {
                    "event_id":     str(uuid.uuid4()),
                    "type":         "iot_telemetry",
                    "timestamp":    datetime.now(timezone.utc).isoformat(),
                    "asset_type":   target_asset,
                    "device_id":    f"iot_{bot_ip.replace('.','_')}",
                    "source_ip":    bot_ip,
                    "request_count": random.randint(200, 800),
                    "error_count":  random.randint(50, 200),
                    "payload_bytes": random.randint(128, 512),
                    "port_entropy": random.uniform(4.0, 5.5),
                    "pkt_variance": random.uniform(800, 2000),
                    "conn_duration": random.uniform(0.001, 0.1),
                    "readings":     {"voltage": random.uniform(0, 5),
                                     "temp":    random.uniform(20, 90)},
                    "scenario":     "IOT_BOTNET",
                    "attack_step":   step,
                }
                yield event
            await asyncio.sleep(0.02)

    # ── Ransomware Propagation ────────────────────────────────────────────────
    async def ransomware(self, target_asset: str = "healthcare",
                         duration_steps: int = 25) -> AsyncGenerator[dict, None]:
        """
        Simulates ransomware: lateral movement via SMB, followed by massive
        file modification logs and high CPU/encryption alerts.
        """
        logger.info("Starting ransomware simulation on %s", target_asset)
        infected_ip = random.choice(INTERNAL_IPS)

        for step in range(duration_steps):
            if step < duration_steps // 2:
                # Phase 1: Lateral Movement
                event = {
                    "event_id":     str(uuid.uuid4()),
                    "type":         "network_traffic",
                    "timestamp":    datetime.now(timezone.utc).isoformat(),
                    "asset_type":   target_asset,
                    "src_ip":       infected_ip,
                    "dst_ip":       f"10.0.1.{random.randint(10, 50)}",
                    "src_port":     random.randint(40000, 65000),
                    "dst_port":     445, # SMB port
                    "protocol":     "TCP",
                    "packet_count": random.randint(50, 150),
                    "bytes_sent":   random.randint(1000, 5000),
                    "bytes_recv":   random.randint(1000, 5000),
                    "conn_duration": random.uniform(0.1, 1.0),
                    "flags":        ["PSH", "ACK"],
                    "pkt_variance": random.uniform(10, 50),
                    "attack_step":  step,
                    "scenario":     "RANSOMWARE",
                }
            else:
                # Phase 2: Mass Encryption
                event = {
                    "event_id":   str(uuid.uuid4()),
                    "type":       "system_log",
                    "timestamp":  datetime.now(timezone.utc).isoformat(),
                    "asset_type": target_asset,
                    "source_ip":  infected_ip,
                    "service":    target_asset,
                    "level":      "CRITICAL",
                    "message":    f"Mass file encryption attack: {random.randint(100, 500)} patient healthcare billing records encrypted (.locked extension). Service disrupted.",
                    "endpoint":   "/storage/volumes",
                    "scenario":   "RANSOMWARE",
                    "attack_step": step,
                }
            yield event
            await asyncio.sleep(0.03)

    # ── Financial Fraud Burst ─────────────────────────────────────────────────
    async def financial_fraud(self, target_asset: str = "finance",
                              duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        """
        Simulates a burst of fraudulent API transactions from varied foreign IPs.
        """
        logger.info("Starting financial fraud simulation on %s", target_asset)

        for step in range(duration_steps):
            fraud_ip = f"198.51.100.{random.randint(100, 200)}"
            event = {
                "event_id":   str(uuid.uuid4()),
                "type":       "system_log",
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "source_ip":  fraud_ip,
                "service":    target_asset,
                "level":      "CRITICAL",
                "message":    f"Anomalous transaction: Unauthorized digital payment wire transfer of ${random.randint(50000, 999999)} to foreign offshore account.",
                "user":       f"service_account_{random.randint(10, 99)}",
                "endpoint":   "/api/v2/transactions/wire",
                "scenario":   "FINANCIAL_FRAUD",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _insider_message(event_type: str, step: int) -> str:
        msgs = {
            "failed_sudo":      f"Administrative SSH login: auth failure on primary tax portal gateway; attempt {step+1}",
            "bulk_read":        f"User read {random.randint(500,5000)} citizen billing ledger entries in a single query",
            "config_access":    "Accessed shadow configuration — unauthorized privilege escalation attempt on payments gateway",
            "credential_reuse": "Login from offshore IP address; mismatch with active employee session token",
            "large_export":     f"Bulk database dump of {random.randint(10,500)}MB citizen tax records initiated via /api/export",
        }
        return msgs.get(event_type, "Suspicious smart city system activity detected")

    # ── Chennai Flood Traffic Diversion ───────────────────────────────────────
    async def chennai_flood(self, target_asset: str = "traffic_system",
                            duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Chennai Flood simulation on %s", target_asset)
        junctions = ["majestic", "silk_board", "dairy_circle", "kr_puram"]
        for step in range(duration_steps):
            j = junctions[step % len(junctions)]
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "monsoon_response",
                "level": "WARNING" if step < 10 else "CRITICAL",
                "message": f"Chennai Flood Warning: Water logging at {j.replace('_',' ').title()} junction. Lane occupancy spiked to 95%. Suggesting automatic diversion.",
                "scenario": "chennai_flood",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Bengaluru Peak Hour Congestion ────────────────────────────────────────
    async def bengaluru_congestion(self, target_asset: str = "traffic_system",
                                   duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Bengaluru Congestion simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "iot_telemetry",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "device_id": "silk_board_sensor_01",
                "request_count": 800 + step * 10,
                "error_count": 0,
                "payload_bytes": 256,
                "port_entropy": 2.5,
                "pkt_variance": 50,
                "conn_duration": 0.5,
                "readings": {
                    "congestion_level": 90.0 + (step * 0.4),
                    "lane_occupancy": 0.90 + (step * 0.004),
                    "avg_speed_kmh": max(5, 15 - step * 0.5)
                },
                "scenario": "bengaluru_congestion",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Mumbai Local Crowd Overflow ───────────────────────────────────────────
    async def mumbai_crowd(self, target_asset: str = "public_transit",
                           duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Mumbai Crowd simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "iot_telemetry",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "device_id": "mumbai_station_gate_c",
                "request_count": 1200 + step * 50,
                "error_count": random.randint(10, 50),
                "payload_bytes": 128,
                "port_entropy": 3.0,
                "pkt_variance": 100,
                "conn_duration": 0.8,
                "readings": {
                    "passenger_density": 85 + step * 0.8,
                    "crowd_panic_index": 0.1 + (step * 0.04),
                    "gate_throughput": random.randint(150, 300)
                },
                "scenario": "mumbai_crowd",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Delhi Emergency Green Corridor ────────────────────────────────────────
    async def delhi_corridor(self, target_asset: str = "emergency_svcs",
                             duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Delhi Corridor simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "emergency_routing",
                "level": "INFO",
                "message": f"Delhi Green Corridor: AIIMS Ambulance routing via Town Hall. Signal status set to green. ETA: {max(2, 10 - step)} minutes.",
                "scenario": "delhi_corridor",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Smart Toll Cyberattack ────────────────────────────────────────────────
    async def toll_cyberattack(self, target_asset: str = "finance",
                               duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Toll Cyberattack simulation on %s", target_asset)
        for step in range(duration_steps):
            if step % 2 == 0:
                # FASTag clone alert
                event = {
                    "event_id": str(uuid.uuid4()),
                    "type": "system_log",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "asset_type": target_asset,
                    "service": "fastag_toll_gate",
                    "level": "CRITICAL",
                    "message": f"FASTag Cloning Suspected: Tag ID FT-940382-A detected at Toll KA-02 and Toll MH-12 within 45 seconds.",
                    "scenario": "toll_cyberattack",
                    "attack_step": step,
                }
            else:
                # UPI anomaly
                event = {
                    "event_id": str(uuid.uuid4()),
                    "type": "system_log",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "asset_type": target_asset,
                    "service": "upi_payment_gateway",
                    "level": "WARNING",
                    "message": f"UPI Transaction Anomaly: Account upi-user-2938@okaxis attempted high-value transfer of ₹180,000 from suspicious external IP 198.51.100.99.",
                    "scenario": "toll_cyberattack",
                    "attack_step": step,
                }
            yield event
            await asyncio.sleep(0.03)

    # ── Metro Ticketing Fraud ─────────────────────────────────────────────────
    async def metro_fraud(self, target_asset: str = "public_transit",
                          duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Metro Fraud simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "metro_gate_api",
                "level": "WARNING" if step < 10 else "CRITICAL",
                "message": f"Metro ticketing gateway API credentials brute force: 45 authentication failures in 5 seconds from source IP {random.choice(ATTACKER_IPS)}.",
                "scenario": "metro_fraud",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Festival Crowd Panic Detection ────────────────────────────────────────
    async def festival_panic(self, target_asset: str = "emergency_svcs",
                             duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Festival Panic simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "iot_telemetry",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "device_id": "temple_quad_camera_2",
                "request_count": 600,
                "error_count": 10,
                "payload_bytes": 512,
                "port_entropy": 2.5,
                "pkt_variance": 20,
                "conn_duration": 0.5,
                "readings": {
                    "crowd_density_sqm": 8.5 + (step * 0.2),
                    "abnormal_velocity_m_s": 1.2 + (step * 0.15),
                    "panic_probability": 0.1 + (step * 0.04)
                },
                "scenario": "festival_panic",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Signal Hacking Attempt ────────────────────────────────────────────────
    async def signal_hacking(self, target_asset: str = "traffic_system",
                             duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Signal Hacking simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "stig_controller",
                "level": "CRITICAL",
                "message": f"Junction Controller Hack: Conflict monitor triggered at Silk Board Junction. Unauthorized firmware override attempted to force all lanes to GREEN.",
                "scenario": "signal_hacking",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Ambulance Priority Routing ────────────────────────────────────────────
    async def ambulance_routing(self, target_asset: str = "emergency_svcs",
                                duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Ambulance Routing simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "emergency_routing",
                "level": "INFO",
                "message": f"Ambulance Green Corridor Active: Clearing Majestic Interchange signal. Priority path scheduled. ETA: {max(1, 8 - step // 2)} min.",
                "scenario": "ambulance_routing",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── Vehicle Theft Tracking ────────────────────────────────────────────────
    async def vehicle_theft(self, target_asset: str = "traffic_system",
                            duration_steps: int = 20) -> AsyncGenerator[dict, None]:
        logger.info("Starting Vehicle Theft tracking simulation on %s", target_asset)
        for step in range(duration_steps):
            event = {
                "event_id": str(uuid.uuid4()),
                "type": "system_log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset_type": target_asset,
                "service": "anpr_scanner",
                "level": "HIGH",
                "message": f"ANPR Alert: Blacklisted plate {random.choice(REGISTRATION_NUMS)} (Linked to Active Police Case #V-30489) scanned at KR Puram Bridge.",
                "scenario": "vehicle_theft",
                "attack_step": step,
            }
            yield event
            await asyncio.sleep(0.03)

    # ── SCENARIO 01: DDoS Against Traffic Control (SH-FIN-05 Section 4) ────────
    async def scenario_01_traffic_ddos(self, duration_steps: int = 15, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 01: Network Flood -> Traffic Control Degradation ->
        Signal Communication Failure -> Traffic Congestion -> Emergency Route Disruption.
        """
        logger.info("Executing Scenario 01: DDoS Against Traffic Control Infrastructure")
        delay = max(0.01, 0.2 / speed_factor)
        campaign_id = f"CAMPAIGN-SEC-2026-TRF-{uuid.uuid4().hex[:4].upper()}"

        # Chain: TRAFFIC_CONTROL -> TRAFFIC_SIGNALS -> EMERGENCY_SERVICES
        for step in range(duration_steps):
            multiplier = 1.0 + (step / max(1, duration_steps - 1)) * 9.0
            is_peak = step >= (duration_steps // 2)

            # Target 1: Traffic Control Gateway (SYN Flood)
            yield {
                "event_id": f"EVT-01-TC-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": random.choice(ATTACKER_IPS),
                "destination_ip": "10.40.0.1",
                "source_port": random.randint(40000, 65000),
                "destination_port": 80,
                "protocol": "TCP",
                "bytes_in": 800000.0 * multiplier,
                "bytes_out": 1500.0,
                "packets": int(1200 * multiplier),
                "duration": 0.05,
                "request_rate": 2400.0 * multiplier,
                "error_rate": min(0.95, 0.40 + 0.05 * step),
                "asset_id": "TRAFFIC_CONTROL",
                "asset_type": "traffic_control",
                "location": "Central ITMS Corridor",
                "attack_type": "DDOS",
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_01",
                "stage": "Traffic Control Flood" if not is_peak else "Signal Telemetry Failure",
                "message": f"Volumetric SYN flood saturating SCATS traffic control ingress ({int(2400 * multiplier)} req/s).",
                "is_cyber_physical": is_peak,
                "physical_impact": {
                    "junction": "majestic",
                    "congestion_index": min(98.0, 45.0 + step * 3.5),
                    "vehicle_queue_length": int(20 + step * 4),
                    "emergency_corridor_blocked": is_peak
                }
            }

            # Secondary cascading effect: Traffic Signals & Emergency Route
            if is_peak:
                yield {
                    "event_id": f"EVT-01-SIG-{step}-{uuid.uuid4().hex[:4].upper()}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_ip": "10.40.0.1",
                    "destination_ip": "10.45.0.12",
                    "source_port": 80,
                    "destination_port": 502,
                    "protocol": "TCP",
                    "bytes_in": 450.0,
                    "bytes_out": 200.0,
                    "packets": 5,
                    "duration": 0.8,
                    "request_rate": 6.2,
                    "error_rate": 0.90,
                    "asset_id": "TRAFFIC_SIGNALS",
                    "asset_type": "traffic_signals",
                    "location": "Majestic & Silk Board Grid",
                    "attack_type": "DOS",
                    "label": 1,
                    "campaign_id": campaign_id,
                    "scenario": "SCENARIO_01",
                    "stage": "Intersection Controller Failure",
                    "message": "Traffic signals failing heartbeat checks; emergency green corridor disrupted."
                }
            await asyncio.sleep(delay)

    # ── SCENARIO 02: Power Grid Substation SCADA Intrusion ────────────────────
    async def scenario_02_power_grid(self, duration_steps: int = 15, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 02: External Access -> Credential Abuse -> SCADA Intrusion ->
        Control System Compromise -> Power Grid Risk -> Downstream cascading (Hospitals, Traffic, Water, Telco).
        """
        logger.info("Executing Scenario 02: Power Grid Intrusion")
        delay = max(0.01, 0.2 / speed_factor)
        campaign_id = f"CAMPAIGN-SEC-2026-PWR-{uuid.uuid4().hex[:4].upper()}"

        stages = [
            ("Reconnaissance", "PORT_SCAN", 0.05),
            ("Credential Abuse", "BRUTE_FORCE", 0.40),
            ("SCADA Intrusion", "INFILTRATION", 0.75),
            ("Control Manipulation", "DOS", 0.92),
            ("Cascading Grid Failure", "DDOS", 0.98),
        ]

        for step in range(duration_steps):
            st_idx = min(len(stages) - 1, int((step / max(1, duration_steps - 1)) * len(stages)))
            stage_name, atk_type, err_rate = stages[st_idx]

            yield {
                "event_id": f"EVT-02-PWR-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "198.51.100.42",
                "destination_ip": "10.10.0.5",
                "source_port": random.randint(49152, 65535),
                "destination_port": 502,
                "protocol": "TCP",
                "bytes_in": 12000.0 * (st_idx + 1),
                "bytes_out": 4500.0,
                "packets": int(80 * (st_idx + 1)),
                "duration": 0.08,
                "request_rate": 500.0 * (st_idx + 1),
                "error_rate": err_rate,
                "asset_id": "POWER_GRID",
                "asset_type": "power_grid",
                "location": "Zone-0 Central Power Substation",
                "attack_type": atk_type,
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_02",
                "stage": stage_name,
                "message": f"Modbus SCADA telemetry manipulation targeting Zone-0 220kV switchgear RTUs ({stage_name})."
            }

            # Downstream impact on Healthcare, Traffic, and Water
            if st_idx >= 3:
                yield {
                    "event_id": f"EVT-02-DOWN-{step}-{uuid.uuid4().hex[:4].upper()}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_ip": "10.10.0.5",
                    "destination_ip": "10.30.0.2",
                    "source_port": 502,
                    "destination_port": 443,
                    "protocol": "TCP",
                    "bytes_in": 2500.0,
                    "bytes_out": 800.0,
                    "packets": 35,
                    "duration": 0.12,
                    "request_rate": 220.0,
                    "error_rate": 0.75,
                    "asset_id": "HEALTHCARE",
                    "asset_type": "healthcare",
                    "location": "Victoria Super-Speciality Hospital",
                    "attack_type": "DOS",
                    "label": 1,
                    "campaign_id": campaign_id,
                    "scenario": "SCENARIO_02",
                    "stage": "Downstream Power Fluctuation",
                    "message": "Hospital backup generator transfer switch activated due to upstream substation telemetry drop."
                }
            await asyncio.sleep(delay)

    # ── SCENARIO 03: Financial Infrastructure Attack ─────────────────────────
    async def scenario_03_financial_attack(self, duration_steps: int = 15, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 03: Reconnaissance -> Credential Attack -> Unauthorized Access ->
        Suspicious Transaction Behaviour -> Financial Service Risk.
        """
        logger.info("Executing Scenario 03: Financial Infrastructure Attack")
        delay = max(0.01, 0.2 / speed_factor)
        campaign_id = f"CAMPAIGN-SEC-2026-FIN-{uuid.uuid4().hex[:4].upper()}"

        for step in range(duration_steps):
            is_late = step >= (duration_steps // 2)
            atk_type = "BRUTE_FORCE" if not is_late else "INFILTRATION"

            yield {
                "event_id": f"EVT-03-FIN-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "45.154.255.10",
                "destination_ip": "10.70.0.1",
                "source_port": random.randint(50000, 62000),
                "destination_port": 443,
                "protocol": "TCP",
                "bytes_in": 150000.0 if is_late else 32000.0,
                "bytes_out": 45000.0,
                "packets": 450 if is_late else 180,
                "duration": 0.15,
                "request_rate": 1200.0 if is_late else 450.0,
                "error_rate": 0.65 if not is_late else 0.88,
                "asset_id": "FINANCIAL_SERVICES",
                "asset_type": "financial_services",
                "location": "Municipal Financial Clearinghouse",
                "attack_type": atk_type,
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_03",
                "stage": "Credential Abuse" if not is_late else "Unauthorized Treasury Disbursement",
                "message": "High-velocity API credential stuffing targeting municipal escrow ledger."
            }
            await asyncio.sleep(delay)

    # ── SCENARIO 04: Healthcare Infrastructure Attack ─────────────────────────
    async def scenario_04_healthcare_attack(self, duration_steps: int = 15, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 04: Network Intrusion -> Hospital System -> Patient Infrastructure -> Critical Service Risk.
        """
        logger.info("Executing Scenario 04: Healthcare Infrastructure Attack")
        delay = max(0.01, 0.2 / speed_factor)
        campaign_id = f"CAMPAIGN-SEC-2026-HLT-{uuid.uuid4().hex[:4].upper()}"

        for step in range(duration_steps):
            yield {
                "event_id": f"EVT-04-HLT-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "185.220.101.99",
                "destination_ip": "10.30.0.15",
                "source_port": random.randint(45000, 60000),
                "destination_port": 8443,
                "protocol": "TCP",
                "bytes_in": 68000.0,
                "bytes_out": 22000.0,
                "packets": 310,
                "duration": 0.2,
                "request_rate": 820.0,
                "error_rate": 0.72,
                "asset_id": "HEALTHCARE",
                "asset_type": "healthcare",
                "location": "Zone-2 Victoria Super-Speciality Hospital",
                "attack_type": "WEB_ATTACK",
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_04",
                "stage": "HL7 & Patient EHR Infiltration",
                "message": "Unauthorized SQL/REST injection targeting intensive care infusion pump telemetry and EHR."
            }
            await asyncio.sleep(delay)

    # ── SCENARIO 05: Water SCADA Attack ──────────────────────────────────────
    async def scenario_05_water_scada(self, duration_steps: int = 15, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 05: Network Intrusion -> Water SCADA -> Control Manipulation -> Water Infrastructure Risk.
        """
        logger.info("Executing Scenario 05: Water SCADA Attack")
        delay = max(0.01, 0.2 / speed_factor)
        campaign_id = f"CAMPAIGN-SEC-2026-WTR-{uuid.uuid4().hex[:4].upper()}"

        for step in range(duration_steps):
            yield {
                "event_id": f"EVT-05-WTR-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "194.26.29.112",
                "destination_ip": "10.60.0.8",
                "source_port": random.randint(48000, 64000),
                "destination_port": 502,
                "protocol": "TCP",
                "bytes_in": 14500.0,
                "bytes_out": 3200.0,
                "packets": 95,
                "duration": 0.1,
                "request_rate": 450.0,
                "error_rate": 0.81,
                "asset_id": "WATER_MANAGEMENT",
                "asset_type": "water_management",
                "location": "T.K. Halli Water Treatment Plant",
                "attack_type": "INFILTRATION",
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_05",
                "stage": "Reservoir PLC Manipulation",
                "message": "Unauthorized Modbus command sequences modifying reservoir sluice gate pressure setpoints."
            }
            await asyncio.sleep(delay)

    # ── SCENARIO 06: Multi-Stage Smart City Attack (SHOWCASE SCENARIO) ─────────
    async def scenario_06_showcase_multi_stage(self, duration_steps: int = 21, speed_factor: float = 1.0) -> AsyncGenerator[dict, None]:
        """
        Scenario 06 Showcase: Reconnaissance -> Credential Abuse -> Network Intrusion ->
        Lateral Movement -> Traffic Control -> Power Infrastructure -> Physical Traffic Anomaly.
        Tied together as one coordinated attack campaign.
        """
        logger.info("Executing Scenario 06: Multi-Stage Smart City Attack (SHOWCASE)")
        delay = max(0.01, 0.25 / speed_factor)
        campaign_id = "CAMPAIGN-SEC-2026-SHOWCASE"

        phases = [
            ("Phase 1: External Reconnaissance", "PUBLIC_WIFI", "PORT_SCAN", "185.220.101.5", 80, 2500, 30, 0.05, "Port scanning civic Wi-Fi gateways to enumerate entrypoints."),
            ("Phase 2: Credential Abuse", "CITIZEN_PORTAL", "BRUTE_FORCE", "185.220.101.5", 443, 35000, 240, 0.65, "Credential stuffing on civic authentication endpoints."),
            ("Phase 3: Core Network Intrusion", "COMM_NETWORK", "INFILTRATION", "10.80.0.1", 22, 95000, 680, 0.78, "Compromised telco fiber ring gateway establishing reverse shell."),
            ("Phase 4: Lateral Movement to OT", "TRAFFIC_CONTROL", "INFILTRATION", "10.20.0.5", 80, 240000, 1100, 0.82, "Lateral movement from telco management subnet into SCATS traffic controllers."),
            ("Phase 5: Traffic Signal Disruption", "TRAFFIC_SIGNALS", "DOS", "10.40.0.1", 502, 500000, 3200, 0.89, "Adaptive traffic signals forced into fixed red / timing desync."),
            ("Phase 6: Power SCADA Tampering", "POWER_GRID", "DOS", "10.20.0.5", 502, 380000, 2400, 0.91, "Substation load shedding tripped via rogue Modbus control frames."),
            ("Phase 7: Cyber-Physical Sabotage", "EMERGENCY_SERVICES", "DDOS", "185.220.101.5", 80, 950000, 4800, 0.95, "Simultaneous physical traffic gridlock & emergency 112 dispatch incursion."),
        ]

        for step in range(duration_steps):
            phase_idx = min(len(phases) - 1, (step * len(phases)) // duration_steps)
            phase_name, asset, attack, src_ip, port, bytes_val, pkts, err_rate, desc = phases[phase_idx]

            yield {
                "event_id": f"EVT-06-SHOWCASE-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": src_ip,
                "destination_ip": f"10.{phase_idx * 10 + 10}.0.1",
                "source_port": random.randint(40000, 65000),
                "destination_port": port,
                "protocol": "TCP",
                "bytes_in": float(bytes_val),
                "bytes_out": float(bytes_val // 4),
                "packets": pkts,
                "duration": 0.05,
                "request_rate": float(pkts * 15),
                "error_rate": err_rate,
                "asset_id": asset,
                "asset_type": asset.lower(),
                "location": "Smart City Core Grid",
                "attack_type": attack,
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "SCENARIO_06",
                "stage": phase_name,
                "message": desc,
                "is_cyber_physical": phase_idx >= 4,
                "physical_impact": {
                    "congestion_index": 88.5 if phase_idx >= 4 else 35.0,
                    "affected_junctions": ["majestic", "silk_board"] if phase_idx >= 4 else [],
                    "power_reserve_mw": 140.0 if phase_idx >= 5 else 480.0
                }
            }
            await asyncio.sleep(delay)

    # ── CUSTOM ATTACK SCENARIO BUILDER (SH-FIN-05 Section 5) ──────────────────
    async def build_custom_scenario(
        self,
        target_asset: str,
        attack_type: str,
        source: str = "External Network",
        intensity: float = 0.8,
        duration: float = 20.0,
        secondary_target: Optional[str] = None,
        physical_impact: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Executes a user-configured attack scenario and injects telemetry into
        the actual production detection pipeline.
        """
        logger.info("Executing Custom Scenario Builder: %s -> %s (intensity=%.2f)", attack_type, target_asset, intensity)
        steps = max(5, int(duration / 1.5))
        delay = duration / float(steps)
        campaign_id = f"CAMPAIGN-SEC-CUSTOM-{uuid.uuid4().hex[:4].upper()}"

        src_ip = "198.51.100.88" if "External" in source else "10.90.0.45"
        base_rate = int(500 * intensity)
        base_bytes = 100000.0 * intensity

        for step in range(steps):
            cur_intensity = 0.5 + 0.5 * (step / max(1, steps - 1)) * intensity
            yield {
                "event_id": f"EVT-CUSTOM-{step}-{uuid.uuid4().hex[:4].upper()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": src_ip,
                "destination_ip": "10.0.1.10",
                "source_port": random.randint(45000, 65000),
                "destination_port": 80 if attack_type.upper() in ("DDOS", "DOS") else 502,
                "protocol": "TCP",
                "bytes_in": base_bytes * cur_intensity,
                "bytes_out": base_bytes * 0.2,
                "packets": int(base_rate * cur_intensity),
                "duration": 0.05,
                "request_rate": float(base_rate * 2 * cur_intensity),
                "error_rate": min(0.95, 0.30 + 0.60 * cur_intensity),
                "asset_id": target_asset,
                "asset_type": target_asset.lower(),
                "location": "Configured Target Zone",
                "attack_type": attack_type.upper(),
                "label": 1,
                "campaign_id": campaign_id,
                "scenario": "CUSTOM_BUILDER",
                "stage": f"Custom Attack ({attack_type})",
                "message": f"Custom simulated attack on {target_asset} at {int(intensity*100)}% intensity."
            }

            if secondary_target and step >= (steps // 2):
                yield {
                    "event_id": f"EVT-CUSTOM-SEC-{step}-{uuid.uuid4().hex[:4].upper()}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source_ip": src_ip,
                    "destination_ip": "10.0.2.20",
                    "source_port": random.randint(45000, 65000),
                    "destination_port": 443,
                    "protocol": "TCP",
                    "bytes_in": base_bytes * 0.4,
                    "bytes_out": 2000.0,
                    "packets": int(base_rate * 0.3),
                    "duration": 0.08,
                    "request_rate": float(base_rate * 0.5),
                    "error_rate": 0.70,
                    "asset_id": secondary_target,
                    "asset_type": secondary_target.lower(),
                    "location": "Secondary Impact Zone",
                    "attack_type": attack_type.upper(),
                    "label": 1,
                    "campaign_id": campaign_id,
                    "scenario": "CUSTOM_BUILDER",
                    "stage": f"Secondary Propagation ({secondary_target})",
                    "message": f"Secondary propagation to {secondary_target} resulting from {target_asset} compromise."
                }
            await asyncio.sleep(min(0.2, delay))

    def list_scenarios(self) -> dict:
        return {k: {"name": v, "id": k} for k, v in SCENARIOS.items()}


# ── singleton ─────────────────────────────────────────────────────────────────
simulator = AttackSimulator()
