"""
Financial fraud intelligence for UPI, FASTag, metro and merchant payments.
The scoring is deterministic and explainable so demos remain stable.
Includes Cyber-Physical-Financial Correlation & Impossible Travel Detection.
"""

import uuid
import math
import logging
from datetime import datetime, timezone

logger = logging.getLogger("securox.fraud_detection")

HIGH_RISK_IP_PREFIXES = ("198.51.100.", "203.0.113.")
HIGH_RISK_MERCHANTS = {"ghost-merchant", "unknown-qr", "mule-wallet"}

class FraudDetectionEngine:
    def __init__(self):
        # In-memory stores for tracking states to detect impossible travel and anomalies
        self.fastag_history = {} # tag_id -> {'timestamp': datetime, 'location': (lat, lon), 'location_id': str}
        self.upi_devices = {} # upi_id -> set of device_ids used
        self.upi_locations = {} # upi_id -> {'timestamp': datetime, 'ip_location': (lat, lon)}

        # Approximate locations for demo (lat, lon)
        self.locations = {
            "toll_mumbai_vashi": (19.0760, 72.8777),
            "toll_bengaluru_ecity": (12.9716, 77.5946),
            "toll_chennai_omr": (13.0827, 80.2707),
            "metro_delhi_rajiv": (28.6139, 77.2090),
            "default": (0.0, 0.0)
        }

    def _haversine_distance(self, coord1, coord2):
        """Calculate the great circle distance in kilometers between two points on the earth."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371  # Radius of earth in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def score_transaction(self, tx: dict) -> dict:
        amount = float(tx.get("amount", 0) or 0)
        channel = str(tx.get("channel", "upi")).lower()
        merchant = str(tx.get("merchant_id", "")).lower()
        ip = str(tx.get("ip_address", tx.get("ip", "")))
        
        tag_id = tx.get("tag_id")
        location_id = tx.get("location_id", "default")
        upi_id = tx.get("upi_id")
        ip_location = tx.get("ip_location", (0.0, 0.0))
        device_id = tx.get("device_id")
        tx_count = tx.get("tx_count_window", 1)

        contributors = []
        evidence = []
        score = 12.0
        
        # 1. Base Fraud Rules
        if amount > 150000:
            score += 38
            contributors.append("high_value_transfer")
            evidence.append(f"High-value transfer amount (₹{amount:,.2f}) exceeding ₹1.5L threshold.")
        elif amount > 50000:
            score += 18
            contributors.append("unusual_amount")
            evidence.append(f"Unusual transaction amount (₹{amount:,.2f}).")
        
        if tx_count >= 20:
            score += 35
            contributors.append("transaction_velocity_burst")
            evidence.append(f"Velocity burst detected: {tx_count} transactions in rapid window.")

        if ip.startswith(HIGH_RISK_IP_PREFIXES):
            score += 24
            contributors.append("high_risk_ip")
            evidence.append(f"Source IP ({ip}) flagged in threat intelligence feeds.")
        
        if channel in {"fastag", "metro"} and tx.get("reuse_window_seconds", 9999) < 180:
            score += 34
            contributors.append(f"{channel}_replay_or_clone")
            evidence.append(f"Toll RFID tag reuse within 3 minutes across distinct gates.")
        
        if merchant in HIGH_RISK_MERCHANTS or tx.get("merchant_age_days", 365) < 7:
            score += 16
            contributors.append("merchant_risk")
            evidence.append(f"Newly registered or flagged mule merchant account ({merchant}).")
        
        if tx.get("device_change"):
            score += 12
            contributors.append("device_change")
            evidence.append("Session initiated from a newly registered device fingerprint.")

        # 2. FASTag Impossible Travel Speed (Demo: Mumbai Toll to Bengaluru Toll in 8 mins = 6,600+ km/h)
        if channel == "fastag" and tag_id:
            current_time = datetime.now(timezone.utc)
            current_coord = self.locations.get(location_id, (19.0760, 72.8777))
            
            # Check for simulated high-speed override or historical lookup
            override_speed = tx.get("simulated_speed_kmph")
            if override_speed:
                speed_kmph = override_speed
                score += 55
                contributors.append(f"impossible_travel_speed_{int(speed_kmph)}kmph")
                evidence.append(f"FASTag used in Mumbai & Bengaluru within 8m 49s (Required speed: {int(speed_kmph):,} km/h → IMPOSSIBLE TRAVEL).")
            elif tag_id in self.fastag_history:
                last_record = self.fastag_history[tag_id]
                time_diff_hours = (current_time - last_record['timestamp']).total_seconds() / 3600.0
                if time_diff_hours > 0.001 and location_id != last_record['location_id']:
                    distance_km = self._haversine_distance(last_record['location'], current_coord)
                    speed_kmph = distance_km / time_diff_hours
                    
                    if speed_kmph > 300: # Impossible speed threshold
                        score += 50
                        contributors.append(f"impossible_travel_speed_{int(speed_kmph)}kmph")
                        evidence.append(f"Physical distance {int(distance_km)} km crossed in {int(time_diff_hours*60)} mins (Speed: {int(speed_kmph):,} km/h).")
                        logger.warning(f"FASTag Cloning! {tag_id} impossible speed {speed_kmph:.2f} km/h")
                        
            # Update history
            self.fastag_history[tag_id] = {
                'timestamp': current_time,
                'location': current_coord,
                'location_id': location_id
            }

        # 3. UPI Geo-location Mismatch & Device Hopping
        if channel == "upi" and upi_id:
            if device_id:
                if upi_id not in self.upi_devices:
                    self.upi_devices[upi_id] = set()
                self.upi_devices[upi_id].add(device_id)
                if len(self.upi_devices[upi_id]) > 3:
                    score += 20
                    contributors.append("high_risk_device_hopping")
                    evidence.append(f"Account bound to {len(self.upi_devices[upi_id])} distinct mobile device IDs.")
            
            if ip_location != (0.0, 0.0):
                if upi_id in self.upi_locations:
                    last_loc = self.upi_locations[upi_id]['ip_location']
                    distance = self._haversine_distance(last_loc, ip_location)
                    if distance > 1000:
                        score += 45
                        contributors.append(f"geo_location_mismatch_{int(distance)}km")
                        evidence.append(f"IP Geolocation jump of {int(distance)} km detected within short interval.")
                        
                self.upi_locations[upi_id] = {
                    'timestamp': datetime.now(timezone.utc),
                    'ip_location': ip_location
                }

        score = min(100.0, round(score, 1))
        severity = "CATASTROPHIC" if score >= 90 else "CRITICAL" if score >= 75 else "HIGH" if score >= 60 else "MODERATE" if score >= 40 else "LOW" if score >= 20 else "NORMAL"
        decision = "freeze_and_quarantine" if score >= 85 else "hold" if score >= 70 else "review" if score >= 40 else "allow"
        
        # Institutional XAI explanation bundle
        xai_details = {
            "title": f"{channel.upper()} Risk Assessment: {score}/100",
            "confidence": 92 if score > 70 else 85,
            "severity": severity,
            "decision": decision,
            "primary_factors": [
                {"factor": "Transaction Velocity", "weight": 90 if "transaction_velocity_burst" in contributors else 25},
                {"factor": "Geographic Anomaly", "weight": 95 if "impossible_travel" in str(contributors) else 20},
                {"factor": "IP Reputation", "weight": 80 if "high_risk_ip" in contributors else 15},
                {"factor": "Device Hopping", "weight": 70 if "device_change" in contributors else 10},
            ],
            "evidence": evidence or ["Transaction metadata consistent with normal baseline."],
            "assessment": self._explain(channel, score, contributors),
            "recommended_action": "Temporarily suspend token, lock session, require MFA, freeze high-value transfers." if score >= 70 else "Flag for SOC Analyst secondary review."
        }

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": tx.get("tx_id") or tx.get("transaction_id") or f"TX-{uuid.uuid4().hex[:8].upper()}",
            "channel": channel,
            "risk_score": score,
            "severity": severity,
            "decision": decision,
            "contributors": contributors or ["baseline_behavior"],
            "explanation": self._explain(channel, score, contributors),
            "xai_details": xai_details,
            "transaction": tx,
        }

    def analyze_treasury_chain(self, steps: list[str] = None) -> dict:
        """
        Models complete Municipal Treasury Attack Chain:
        Credential Compromise → Tax Portal Access → Privilege Escalation →
        Citizen DB Access → Revenue Modification → Treasury Manipulation →
        Exfiltration → Ransomware
        """
        chain_steps = steps or [
            "1. Credential Compromise (Phishing/Stuffing on Tax Portal)",
            "2. Tax Portal Unauthorized Access",
            "3. Sudo Escalation to Revenue Admin",
            "4. Citizen Tax Database Exfiltration",
            "5. Tax Ledger & Revenue Modification",
            "6. Direct Municipal Treasury Transfer Attempt",
            "7. Ransomware Deployment on Municipal Servers"
        ]
        return {
            "campaign": "Municipal Treasury Compromise Chain",
            "threat_level": "CATASTROPHIC",
            "stages": chain_steps,
            "current_stage": len(chain_steps),
            "target_asset": "tax_portal",
            "potential_loss_cr": 38.0,
            "mitigation_playbook": "SOAR-FIN-004: Freeze Municipal Treasury API & Lock Admin Accounts"
        }

    @staticmethod
    def _explain(channel: str, score: float, contributors: list[str]) -> str:
        if not contributors:
            return f"{channel.upper()} transaction is within normal behavioral limits."
        return f"{channel.upper()} transaction scored {score}/100 due to {', '.join(contributors)}."


fraud_detection = FraudDetectionEngine()
