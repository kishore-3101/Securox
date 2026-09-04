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
from typing import AsyncGenerator

logger = logging.getLogger("securox.simulation")

# ── scenario registry ─────────────────────────────────────────────────────────
SCENARIOS = {
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

    def list_scenarios(self) -> dict:
        return {k: {"name": v, "id": k} for k, v in SCENARIOS.items()}


# ── singleton ─────────────────────────────────────────────────────────────────
simulator = AttackSimulator()
