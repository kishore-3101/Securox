"""
Securox — Traffic Intelligence Grid (STIG)
Manages mixed Indian traffic conditions, adaptive signal timing, emergency routing,
traffic violations, and transport cybersecurity analytics.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("securox.stig")

# --- Indian Smart City Junction Definitions (Bengaluru coordinates) ---
JUNCTIONS = {
    "majestic": {
        "id": "majestic",
        "name": "Majestic Interchange",
        "lat": 12.9779,
        "lng": 77.5724,
        "congestion_index": 45.0,
        "avg_speed": 32.0,
        "signal_state": "GREEN",
        "signal_duration": 40,
        "lane_occupancy": 0.50,
        "vehicle_counts": {"bike": 150, "auto": 60, "car": 80, "bus": 25, "truck": 5, "emergency": 0},
    },
    "silk_board": {
        "id": "silk_board",
        "name": "Silk Board Junction",
        "lat": 12.9172,
        "lng": 77.6228,
        "congestion_index": 82.0,
        "avg_speed": 12.0,
        "signal_state": "RED",
        "signal_duration": 90,
        "lane_occupancy": 0.88,
        "vehicle_counts": {"bike": 320, "auto": 120, "car": 210, "bus": 40, "truck": 15, "emergency": 0},
    },
    "hebbal": {
        "id": "hebbal",
        "name": "Hebbal Flyover",
        "lat": 13.0358,
        "lng": 77.5970,
        "congestion_index": 55.0,
        "avg_speed": 45.0,
        "signal_state": "GREEN",
        "signal_duration": 30,
        "lane_occupancy": 0.60,
        "vehicle_counts": {"bike": 180, "auto": 50, "car": 140, "bus": 18, "truck": 22, "emergency": 0},
    },
    "kr_puram": {
        "id": "kr_puram",
        "name": "KR Puram Hanging Bridge",
        "lat": 13.0005,
        "lng": 77.6837,
        "congestion_index": 70.0,
        "avg_speed": 22.0,
        "signal_state": "RED",
        "signal_duration": 75,
        "lane_occupancy": 0.78,
        "vehicle_counts": {"bike": 240, "auto": 90, "car": 120, "bus": 35, "truck": 30, "emergency": 0},
    },
    "dairy_circle": {
        "id": "dairy_circle",
        "name": "Dairy Circle Junction",
        "lat": 12.9382,
        "lng": 77.6059,
        "congestion_index": 62.0,
        "avg_speed": 26.0,
        "signal_state": "GREEN",
        "signal_duration": 45,
        "lane_occupancy": 0.68,
        "vehicle_counts": {"bike": 190, "auto": 75, "car": 95, "bus": 22, "truck": 8, "emergency": 0},
    },
    "town_hall": {
        "id": "town_hall",
        "name": "Town Hall Junction",
        "lat": 12.9641,
        "lng": 77.5854,
        "congestion_index": 50.0,
        "avg_speed": 30.0,
        "signal_state": "GREEN",
        "signal_duration": 30,
        "lane_occupancy": 0.55,
        "vehicle_counts": {"bike": 160, "auto": 65, "car": 110, "bus": 30, "truck": 2, "emergency": 0},
    },
    "indiranagar": {
        "id": "indiranagar",
        "name": "Indiranagar 100ft Rd Crossing",
        "lat": 12.9784,
        "lng": 77.6408,
        "congestion_index": 58.0,
        "avg_speed": 28.0,
        "signal_state": "RED",
        "signal_duration": 60,
        "lane_occupancy": 0.65,
        "vehicle_counts": {"bike": 210, "auto": 80, "car": 130, "bus": 15, "truck": 1, "emergency": 0},
    },
    "whitefield": {
        "id": "whitefield",
        "name": "Whitefield ITPL Road",
        "lat": 12.9866,
        "lng": 77.7335,
        "congestion_index": 78.0,
        "avg_speed": 18.0,
        "signal_state": "RED",
        "signal_duration": 80,
        "lane_occupancy": 0.82,
        "vehicle_counts": {"bike": 280, "auto": 105, "car": 170, "bus": 38, "truck": 12, "emergency": 0},
    }
}

# Real-world Indian number plate letters/formats
STATE_CODES = ["KA", "MH", "DL", "TN", "TS", "AP", "HR", "UP"]
REGISTRATION_NUMS = [f"{random.choice(STATE_CODES)}-{random.randint(1,99):02d}-{chr(random.randint(65,90))}{chr(random.randint(65,90))}-{random.randint(1000,9999)}" for _ in range(200)]


class TrafficIntelligenceGrid:
    def __init__(self):
        self._junctions = JUNCTIONS
        for j in self._junctions.values():
            j["override_active"] = False
        self._violations = []
        self._corridors = {}
        self._lock = asyncio.Lock()
        
        # Financial logs (FASTag / UPI)
        self._fastag_logs = []
        self._upi_logs = []
        self._last_fastag_times = {} # maps tag_id -> (timestamp, toll_id)
        
        # AI Chat History
        self._chat_history = []

    def _map_junction_id(self, jid: str) -> str:
        # Standardize ID mapping to local JUNCTIONS
        norm = jid.lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "junction_a": "silk_board",
            "junction_b": "dairy_circle",
            "junction_c": "town_hall",
        }
        return mapping.get(norm, norm)

    async def override_signal(self, junction_id: str, state: str) -> bool:
        mapped_id = self._map_junction_id(junction_id)
        async with self._lock:
            if mapped_id in self._junctions:
                self._junctions[mapped_id]["signal_state"] = state
                self._junctions[mapped_id]["signal_duration"] = 60 # Set duration of override
                self._junctions[mapped_id]["override_active"] = True
                return True
            return False

    async def generate_green_corridor(self, ambulance_id: str, route: list[str]) -> dict:
        mapped_route = [self._map_junction_id(r) for r in route]
        async with self._lock:
            corridor_id = f"GC-{uuid.uuid4().hex[:6].upper()}"
            c = {
                "id": corridor_id,
                "ambulance_id": ambulance_id,
                "route": route,  # Keep original labels for UI
                "route_nodes": mapped_route,
                "current_node": mapped_route[0],
                "active_signals_cleared": [mapped_route[0]],
                "eta_minutes": len(mapped_route) * 2,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._corridors[corridor_id] = c
            
            # Force all junctions along the route to GREEN override immediately
            for node in mapped_route:
                if node in self._junctions:
                    self._junctions[node]["signal_state"] = "GREEN"
                    self._junctions[node]["signal_duration"] = 60
                    self._junctions[node]["override_active"] = True
                    
            return c

    async def get_recent_violations(self, limit: int = 30) -> list:
        async with self._lock:
            if not self._violations:
                # Lazy populate some mock violations for realistic demo
                for _ in range(15):
                    plate = random.choice(REGISTRATION_NUMS)
                    v_type = random.choice(["helmet_violation", "overspeeding", "wrong_side", "signal_jumping"])
                    v_vehicle = random.choice(["bike", "auto", "car"])
                    fine_map = {"helmet_violation": 500, "overspeeding": 1000, "wrong_side": 1500, "signal_jumping": 1000}
                    self._violations.append({
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "junction_id": random.choice(list(self._junctions.keys())),
                        "vehicle_id": f"VEH-{random.randint(1000,9999)}",
                        "speed": random.randint(70, 115),
                        "speed_limit": 60,
                        "camera_id": f"CAM_{random.randint(100,999)}",
                        "vehicle_type": v_vehicle,
                        "license_plate": plate,
                        "violation_type": v_type,
                        "fine_amount": fine_map[v_type],
                        "status": "detected"
                    })
            return self._violations[-limit:]

    async def get_stats(self) -> dict:
        async with self._lock:
            # Map internal junction schemas to frontend-compatible field names
            frontend_junctions = {}
            for jid, j in self._junctions.items():
                queue_count = sum(j.get("vehicle_counts", {}).values())
                frontend_junctions[jid] = {
                    "id": j["id"],
                    "name": j["name"],
                    "state": j["signal_state"],
                    "timer": j["signal_duration"],
                    "queue_count": queue_count,
                    "average_speed": j["avg_speed"],
                    "congestion_index": j["congestion_index"],
                    "override_active": j.get("override_active", False)
                }
            return {
                "junctions": frontend_junctions,
                "active_corridors": list(self._corridors.values()),
                "recent_violations": self._violations[-30:],
                "fastag_stats": self._get_fastag_summary(),
                "upi_stats": self._get_upi_summary()
            }

    async def get_violations(self) -> list:
        return await self.get_recent_violations(limit=50)

    async def get_corridors(self) -> list:
        async with self._lock:
            return list(self._corridors.values())

    async def tick(self) -> list[dict]:
        """Runs periodic updates of mixed traffic volumes and signal cycles."""
        new_alerts = []
        async with self._lock:
            for jid, j in self._junctions.items():
                # Randomize traffic fluctuation representing unstructured lane movement
                noise = random.uniform(-0.03, 0.03)
                j["lane_occupancy"] = round(max(0.20, min(0.98, j["lane_occupancy"] + noise)), 2)
                
                # Derive congestion index and speed dynamically based on density
                j["congestion_index"] = round(j["lane_occupancy"] * 100.0, 1)
                j["avg_speed"] = round(max(5.0, 60.0 - j["lane_occupancy"] * 50.0), 1)
                
                # Signal countdown / state flip
                j["signal_duration"] -= 1
                if j["signal_duration"] <= 0:
                    j["signal_state"] = "GREEN" if j["signal_state"] == "RED" else "RED"
                    j["signal_duration"] = random.choice([30, 45, 60, 90])
                
                # Check for critical congestion alerts
                if j["congestion_index"] >= 85.0 and random.random() < 0.15:
                    new_alerts.append({
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "asset": "traffic_system",
                        "severity": "high",
                        "risk_score": float(j["congestion_index"]),
                        "risk_category": "HIGH",
                        "anomaly_score": 0.88,
                        "confidence": 0.92,
                        "explanation": f"STIG: Critical peak gridlock detected at {j['name']} (Bengaluru). Avg speed dropped to {j['avg_speed']} KM/H.",
                        "scenario": "bengaluru_congestion",
                        "threat_flags": ["TRAFFIC_CONGESTION"],
                        "mitigation_plan": None
                    })
                    
            # Move active emergency priority corridors
            completed_corridors = []
            for cid, c in self._corridors.items():
                nodes = c["route_nodes"]
                curr_idx = nodes.index(c["current_node"])
                if curr_idx < len(nodes) - 1:
                    # Move to next node
                    next_node = nodes[curr_idx + 1]
                    c["current_node"] = next_node
                    c["eta_minutes"] = max(1, c["eta_minutes"] - 2)
                    c["active_signals_cleared"].append(next_node)
                    
                    # Force signal at current node to green
                    if next_node in self._junctions:
                        self._junctions[next_node]["signal_state"] = "GREEN"
                        self._junctions[next_node]["signal_duration"] = 40
                else:
                    completed_corridors.append(cid)
                    
            for cid in completed_corridors:
                del self._corridors[cid]
                
        return new_alerts

    # --- Emergency Prioritization & Green Corridors ---
    async def create_green_corridor(self, route_name: str, origin: str, destination: str) -> dict:
        async with self._lock:
            # Map simple route paths based on junctions
            route_paths = {
                "Ambulance Priority Route (Silk Board -> Town Hall)": ["silk_board", "dairy_circle", "town_hall"],
                "Convoy VIP Corridor (Hebbal -> Indiranagar)": ["hebbal", "majestic", "town_hall", "indiranagar"],
                "Emergency Dispatch (Majestic -> Whitefield)": ["majestic", "town_hall", "indiranagar", "whitefield"]
            }
            
            nodes = route_paths.get(route_name, [origin, "town_hall", destination])
            corridor_id = str(uuid.uuid4())[:8]
            
            c = {
                "id": corridor_id,
                "name": route_name,
                "vehicle_type": "ambulance" if "Ambulance" in route_name else "convoy",
                "origin": origin,
                "destination": destination,
                "route_nodes": nodes,
                "current_node": nodes[0],
                "active_signals_cleared": [nodes[0]],
                "eta_minutes": len(nodes) * 3,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._corridors[corridor_id] = c
            
            # Force starting junction signal to green
            if nodes[0] in self._junctions:
                self._junctions[nodes[0]]["signal_state"] = "GREEN"
                self._junctions[nodes[0]]["signal_duration"] = 45
                
            return c

    # --- Traffic Violations & Enforcement ---
    async def log_violation(self, camera_id: str, violation_type: str, vehicle_type: str) -> dict:
        async with self._lock:
            plate = random.choice(REGISTRATION_NUMS)
            fine_map = {
                "helmet_violation": 500,
                "overspeeding": 1000,
                "wrong_side": 1500,
                "signal_jumping": 1000,
                "triple_riding": 1000,
                "illegal_parking": 500
            }
            
            v = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "camera_id": camera_id,
                "vehicle_type": vehicle_type,
                "license_plate": plate,
                "violation_type": violation_type,
                "fine_amount": fine_map.get(violation_type, 1000),
                "status": "detected"
            }
            self._violations.append(v)
            if len(self._violations) > 100:
                self._violations.pop(0)
            return v

    # --- FASTag & UPI Financial Monitoring ---
    async def process_fastag(self, toll_id: str, tag_id: str, vehicle_type: str, amount: float) -> dict | None:
        """Processes FASTag logs and detects cloning anomalies (impossible speed travel)."""
        anomaly = None
        now = datetime.now(timezone.utc)
        
        async with self._lock:
            # Check if this tag has a recent reading
            if tag_id in self._last_fastag_times:
                last_time, last_toll = self._last_fastag_times[tag_id]
                elapsed = (now - last_time).total_seconds()
                
                # Check for impossible speed travel (e.g. MH to KA in under 5 minutes)
                if last_toll != toll_id and elapsed < 180: # less than 3 minutes between different tolls
                    # Flag tag cloning anomaly
                    anomaly = {
                        "id": str(uuid.uuid4()),
                        "timestamp": now.isoformat(),
                        "asset": "finance",
                        "severity": "critical",
                        "risk_score": 95.0,
                        "risk_category": "CRITICAL",
                        "anomaly_score": 0.98,
                        "confidence": 0.95,
                        "explanation": f"FASTag FRAUD: Cloning detected for tag_id {tag_id}. Tag read at {last_toll} and then {toll_id} within {elapsed:.0f} seconds (impossible speed travel).",
                        "scenario": "smart_toll_attack",
                        "threat_flags": ["FASTAG_CLONING", "FINANCIAL_FRAUD"],
                        "mitigation_plan": {
                            "id": str(uuid.uuid4()),
                            "timestamp": now.isoformat(),
                            "asset": "finance",
                            "risk_score": 95.0,
                            "risk_category": "CRITICAL",
                            "playbook": "FINANCIAL_FRAUD",
                            "auto_execute": True,
                            "notify": ["SOC", "CISO"],
                            "primary_actions": [
                                {"action": "suspend_credentials", "target": "fastag_gateway", "params": {"tag_id": tag_id}},
                                {"action": "block_ip_range", "target": "firewall", "params": {"auto_detect": True}}
                            ],
                            "secondary_actions": [
                                {"action": "alert_soc", "target": "security_ops", "params": {"priority": "P1"}}
                            ],
                            "estimated_containment_minutes": 5,
                            "confidence": 0.95
                        }
                    }
            
            # Save log
            self._last_fastag_times[tag_id] = (now, toll_id)
            self._fastag_logs.append({
                "tag_id": tag_id,
                "toll_id": toll_id,
                "vehicle_type": vehicle_type,
                "amount": amount,
                "timestamp": now.isoformat(),
                "status": "anomaly" if anomaly else "success"
            })
            if len(self._fastag_logs) > 100:
                self._fastag_logs.pop(0)
                
        return anomaly

    async def process_upi(self, tx_id: str, user_id: str, amount: float, ip_address: str) -> dict | None:
        """Processes UPI logs and detects wire transfer anomalies."""
        anomaly = None
        now = datetime.now(timezone.utc)
        
        async with self._lock:
            # Check for anomalously high UPI amount
            if amount > 150000.0 or ip_address.startswith("198.51.100."):
                anomaly = {
                    "id": str(uuid.uuid4()),
                    "timestamp": now.isoformat(),
                    "asset": "finance",
                    "severity": "high",
                    "risk_score": 78.0,
                    "risk_category": "HIGH",
                    "anomaly_score": 0.85,
                    "confidence": 0.90,
                    "explanation": f"UPI ANOMALY: Unauthorized payment attempt of ₹{amount:.2f} detected from high-risk external IP {ip_address} on account {user_id}.",
                    "scenario": "smart_toll_attack",
                    "threat_flags": ["UPI_FRAUD", "FINANCIAL_FRAUD"],
                    "mitigation_plan": {
                        "id": str(uuid.uuid4()),
                        "timestamp": now.isoformat(),
                        "asset": "finance",
                        "risk_score": 78.0,
                        "risk_category": "HIGH",
                        "playbook": "FINANCIAL_FRAUD",
                        "auto_execute": False,
                        "notify": ["SOC"],
                        "primary_actions": [
                            {"action": "suspend_credentials", "target": "upi_gateway", "params": {"user_id": user_id}},
                            {"action": "increase_logging", "target": "siem", "params": {"verbosity": "DEBUG"}}
                        ],
                        "secondary_actions": [
                            {"action": "enable_mfa", "target": "iam", "params": {"scope": "affected_account"}}
                        ],
                        "estimated_containment_minutes": 10,
                        "confidence": 0.90
                    }
                }
                
            self._upi_logs.append({
                "tx_id": tx_id,
                "user_id": user_id,
                "amount": amount,
                "ip": ip_address,
                "timestamp": now.isoformat(),
                "status": "anomaly" if anomaly else "success"
            })
            if len(self._upi_logs) > 100:
                self._upi_logs.pop(0)
                
        return anomaly

    def _get_fastag_summary(self) -> dict:
        recent = self._fastag_logs[-20:]
        anomalies = sum(1 for x in recent if x["status"] == "anomaly")
        return {
            "total_transactions": len(self._fastag_logs),
            "anomalous_tags": anomalies,
            "logs": recent
        }

    def _get_upi_summary(self) -> dict:
        recent = self._upi_logs[-20:]
        anomalies = sum(1 for x in recent if x["status"] == "anomaly")
        return {
            "total_transactions": len(self._upi_logs),
            "anomalous_txs": anomalies,
            "logs": recent
        }


# --- Module Singleton ---
stig = TrafficIntelligenceGrid()
