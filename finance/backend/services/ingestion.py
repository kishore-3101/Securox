"""
Securox — Data Ingestion & Feature Engineering
Accepts IoT telemetry, system logs, and network summaries.
Normalises and extracts features used by the ML engine.
"""

import hashlib
import ipaddress
import logging
import math
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("securox.ingestion")

# ── known malicious IP prefixes (demo threat intel) ───────────────────────────
THREAT_IP_RANGES = [
    "192.0.2.",   "198.51.100.", "203.0.113.",   # RFC 5737 documentation blocks (demo)
    "10.66.",     "172.31.255.",
]

# ── known C2 / suspicious domain patterns ────────────────────────────────────
SUSPICIOUS_DOMAIN_RE = re.compile(
    r"(\.ru|\.cn|\.tk|\.xyz|pastebin|ngrok|\.onion)", re.I
)


class IngestionService:
    """Validates, normalises and extracts features from raw events."""

    # ── IoT telemetry ─────────────────────────────────────────────────────────
    def process_iot(self, raw: dict) -> dict:
        """
        Expected raw keys:
            device_id, asset_type, timestamp, readings: {temp, pressure, voltage, ...},
            request_count, error_count, source_ip, payload_bytes
        """
        features = {}
        ts = self._parse_ts(raw.get("timestamp"))

        features["asset_type"]      = raw.get("asset_type", "unknown")
        features["device_id"]       = str(raw.get("device_id", "unknown"))
        features["request_rate"]    = float(raw.get("request_count", 0))
        features["error_rate"]      = self._safe_ratio(
            raw.get("error_count", 0), raw.get("request_count", 1)
        )
        features["payload_size_avg"]= float(raw.get("payload_bytes", 512))
        features["hour_sin"]        = math.sin(2 * math.pi * ts.hour / 24)
        features["hour_cos"]        = math.cos(2 * math.pi * ts.hour / 24)
        features["geo_anomaly_score"] = self._geo_anomaly(raw.get("source_ip", ""))
        features["unique_ips"]      = 1
        features["port_entropy"]    = float(raw.get("port_entropy", 3.0))
        features["pkt_size_variance"] = float(raw.get("pkt_variance", 200))
        features["conn_duration_avg"] = float(raw.get("conn_duration", 0.8))

        # Threat flags
        flags = []
        if features["geo_anomaly_score"] > 0.7:
            flags.append("GEO_ANOMALY")
        if features["error_rate"] > 0.3:
            flags.append("HIGH_ERROR_RATE")
        if features["request_rate"] > 500:
            flags.append("DDoS")

        # Smart City / Traffic specific checks
        readings = raw.get("readings", {})
        if readings.get("congestion_level", 0.0) > 85.0:
            flags.append("TRAFFIC_CONGESTION")
        if readings.get("crowd_density_sqm", 0.0) > 7.0 or readings.get("passenger_density", 0.0) > 90.0:
            flags.append("CROWD_PANIC")
        if readings.get("crowd_panic_index", 0.0) > 0.5:
            flags.append("CROWD_PANIC")

        features["threat_flags"] = flags
        features["source"]       = "iot_telemetry"
        features["raw_hash"]     = self._hash(raw)
        return features

    # ── system logs ───────────────────────────────────────────────────────────
    def process_log(self, raw: dict) -> dict:
        """
        Expected raw keys:
            timestamp, level, service, message, source_ip, user_agent, endpoint
        """
        features = {}
        ts = self._parse_ts(raw.get("timestamp"))
        msg = str(raw.get("message", "")).lower()

        features["asset_type"]       = raw.get("service", "unknown")
        features["request_rate"]     = 1.0
        features["error_rate"]       = 1.0 if raw.get("level") in ("ERROR", "CRITICAL") else 0.0
        features["payload_size_avg"] = float(len(str(raw.get("message", ""))))
        features["hour_sin"]         = math.sin(2 * math.pi * ts.hour / 24)
        features["hour_cos"]         = math.cos(2 * math.pi * ts.hour / 24)
        features["geo_anomaly_score"]= self._geo_anomaly(raw.get("source_ip", ""))
        features["unique_ips"]       = 1
        features["port_entropy"]     = 3.0
        features["pkt_size_variance"]= 200.0
        features["conn_duration_avg"]= 0.5

        flags = []
        if "failed" in msg and "login" in msg:
            flags.append("BRUTE_FORCE")
        if "privilege" in msg or "sudo" in msg or "escalat" in msg:
            flags.append("INSIDER_THREAT")
        if "exfil" in msg or "upload" in msg and "large" in msg:
            flags.append("DATA_EXFILTRATION")
        if self._suspicious_domain(raw.get("message", "")):
            flags.append("C2_COMMUNICATION")

        # Smart city alerts
        if "fastag" in msg or "rfid" in msg or "cloned tag" in msg or "toll" in msg:
            flags.append("FASTAG_CLONING")
        if "upi" in msg or "transaction" in msg or "wire transfer" in msg or "payment" in msg or "double debit" in msg:
            flags.append("FINANCIAL_FRAUD")
        if "metro" in msg or "ticketing" in msg or "transit" in msg:
            flags.append("METRO_ATTACK")
        if "congestion" in msg or "flood" in msg or "water logging" in msg or "accident" in msg:
            flags.append("TRAFFIC_CONGESTION")
        if "panic" in msg or "stampede" in msg or "crowd" in msg:
            flags.append("CROWD_PANIC")
        if "controller" in msg or "conflict monitor" in msg or "signal" in msg:
            flags.append("SIGNAL_HACKING")

        features["threat_flags"] = flags
        features["source"]       = "system_log"
        features["raw_hash"]     = self._hash(raw)
        return features

    # ── network traffic ───────────────────────────────────────────────────────
    def process_network(self, raw: dict) -> dict:
        """
        Expected raw keys:
            timestamp, src_ip, dst_ip, src_port, dst_port,
            protocol, bytes_sent, bytes_recv, packet_count,
            conn_duration, flags (list of TCP flags)
        """
        features = {}
        ts = self._parse_ts(raw.get("timestamp"))

        pkt = max(raw.get("packet_count", 1), 1)
        features["asset_type"]       = "network"
        features["request_rate"]     = float(raw.get("packet_count", 0))
        features["error_rate"]       = 0.1
        features["payload_size_avg"] = (
            (float(raw.get("bytes_sent", 0)) + float(raw.get("bytes_recv", 0))) / pkt
        )
        features["hour_sin"]         = math.sin(2 * math.pi * ts.hour / 24)
        features["hour_cos"]         = math.cos(2 * math.pi * ts.hour / 24)
        features["geo_anomaly_score"]= self._geo_anomaly(raw.get("src_ip", ""))
        features["unique_ips"]       = 1
        features["port_entropy"]     = self._port_entropy(raw.get("dst_port", 80))
        features["pkt_size_variance"]= float(raw.get("pkt_variance", 200))
        features["conn_duration_avg"]= float(raw.get("conn_duration", 1.0))

        flags = raw.get("flags", [])
        threat_flags = []
        if "SYN" in flags and "ACK" not in flags and pkt > 1000:
            threat_flags.append("DDoS")
        if float(raw.get("bytes_sent", 0)) > 100_000_000:
            threat_flags.append("DATA_EXFILTRATION")
        if raw.get("dst_port") in (4444, 1337, 31337, 6667, 6697):
            threat_flags.append("IOT_BOTNET")

        features["threat_flags"] = threat_flags
        features["source"]       = "network_traffic"
        features["raw_hash"]     = self._hash(raw)
        return features

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_ts(ts_val: Any) -> datetime:
        if isinstance(ts_val, datetime):
            return ts_val
        try:
            return datetime.fromisoformat(str(ts_val))
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def _safe_ratio(num: Any, den: Any) -> float:
        try:
            return min(float(num) / max(float(den), 1), 1.0)
        except Exception:
            return 0.0

    @staticmethod
    def _geo_anomaly(ip_str: str) -> float:
        """Returns 0–1 anomaly score based on IP classification."""
        if not ip_str:
            return 0.0
        for prefix in THREAT_IP_RANGES:
            if ip_str.startswith(prefix):
                return 0.95
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback:
                return 0.05
            # Simulate: non-RFC1918 public IPs have moderate geo risk
            return 0.3
        except ValueError:
            return 0.5

    @staticmethod
    def _suspicious_domain(text: str) -> bool:
        return bool(SUSPICIOUS_DOMAIN_RE.search(text))

    @staticmethod
    def _port_entropy(port: Any) -> float:
        """High entropy means many different ports → scanning."""
        COMMON = {80, 443, 22, 25, 53, 110, 143, 8080, 3306, 5432}
        try:
            return 2.0 if int(port) in COMMON else 4.5
        except Exception:
            return 3.0

    @staticmethod
    def _hash(obj: dict) -> str:
        return hashlib.md5(str(sorted(obj.items())).encode()).hexdigest()[:12]


# ── singleton ─────────────────────────────────────────────────────────────────
ingestion = IngestionService()
