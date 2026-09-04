"""
Securox — Dataset Normalization Layer
Converts disparate raw cybersecurity datasets (CICIDS2017, UNSW-NB15, TON_IoT, NSL-KDD)
into the unified CanonicalEvent schema.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd
from data.schema import CanonicalEvent, ATTACK_CLASSES


def _map_port_to_smart_city_asset(port: int, service: str = "") -> tuple[str, str]:
    """Infers smart city infrastructure asset from destination port and service."""
    p = int(port) if port and str(port).isdigit() else 80
    svc = str(service).lower()

    if p in (554, 8554, 8080) or "rtsp" in svc:
        return "CAM_CORRIDOR_01", "traffic_camera"
    elif p in (502, 47808, 102) or "modbus" in svc or "scada" in svc:
        return "POWER_GRID_SUBSTATION_A", "power_grid"
    elif p in (8443, 9443) or "fin" in svc or "bank" in svc:
        return "FIN_PAYMENT_GW", "financial_services"
    elif p in (1883, 8883) or "mqtt" in svc:
        return "IOT_SENSOR_MESH", "iot_sensors"
    elif p in (80, 443) or "http" in svc:
        return "CITIZEN_PORTAL", "citizen_portal"
    elif p in (22, 23) or "ssh" in svc or "telnet" in svc:
        return "TRAFFIC_CTRL_ZONE1", "traffic_control"
    elif p in (53, 67, 68) or "dns" in svc:
        return "TELCO_FIBER_RING", "communications"
    else:
        return "TRAFFIC_CTRL_ZONE1", "traffic_control"


class DatasetNormalizer:
    """Normalizes heterogenous dataset rows into CanonicalEvent objects."""

    @staticmethod
    def normalize_cicids2017(row: Dict[str, Any]) -> CanonicalEvent:
        """Adapts a Canadian Institute for Cybersecurity (CIC-IDS-2017) record."""
        raw_label = str(row.get("Label") or row.get("label") or "BENIGN").strip()
        label_upper = raw_label.upper()

        if "BENIGN" in label_upper:
            attack_type = "BENIGN"
            label = 0
        elif "DDOS" in label_upper:
            attack_type = "DDOS"
            label = 1
        elif "DOS" in label_upper:
            attack_type = "DOS"
            label = 1
        elif "PORT" in label_upper or "SCAN" in label_upper:
            attack_type = "PORT_SCAN"
            label = 1
        elif "PATATOR" in label_upper or "BRUTE" in label_upper or "SSH" in label_upper or "FTP" in label_upper:
            attack_type = "BRUTE_FORCE"
            label = 1
        elif "BOT" in label_upper:
            attack_type = "BOTNET"
            label = 1
        elif "INFILTRATION" in label_upper or "HEARTBLEED" in label_upper:
            attack_type = "INFILTRATION"
            label = 1
        elif "WEB" in label_upper or "XSS" in label_upper or "SQL" in label_upper:
            attack_type = "WEB_ATTACK"
            label = 1
        else:
            attack_type = "OTHER"
            label = 1

        dst_port = int(float(row.get("Destination Port", row.get("dst_port", 80))))
        asset_id, asset_type = _map_port_to_smart_city_asset(dst_port)

        dur_micros = float(row.get("Flow Duration", row.get("duration", 1000)))
        dur_sec = max(0.0001, dur_micros / 1_000_000.0)
        fwd_pkts = int(float(row.get("Total Fwd Packets", row.get("fwd_pkts", 1))))
        bwd_pkts = int(float(row.get("Total Backward Packets", row.get("bwd_pkts", 0))))
        tot_pkts = max(1, fwd_pkts + bwd_pkts)

        fwd_bytes = float(row.get("Total Length of Fwd Packets", row.get("fwd_bytes", 128)))
        bwd_bytes = float(row.get("Total Length of Bwd Packets", row.get("bwd_bytes", 64)))
        req_rate = float(row.get("Flow Packets/s", tot_pkts / dur_sec))
        if math.isnan(req_rate) or math.isinf(req_rate):
            req_rate = float(tot_pkts / dur_sec)

        return CanonicalEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_ip=str(row.get("Source IP", row.get("src_ip", "192.168.10.50"))),
            destination_ip=str(row.get("Destination IP", row.get("dst_ip", "172.16.0.1"))),
            source_port=int(float(row.get("Source Port", row.get("src_port", 49152)))),
            destination_port=dst_port,
            protocol="TCP",
            bytes_in=bwd_bytes,
            bytes_out=fwd_bytes,
            packets=tot_pkts,
            duration=round(dur_sec, 6),
            request_rate=round(min(50_000.0, max(0.1, req_rate)), 2),
            error_rate=0.0 if attack_type == "BENIGN" else 0.45,
            asset_id=asset_id,
            asset_type=asset_type,
            location="Bengaluru Transit Corridor",
            attack_type=attack_type,
            label=label,
            metadata={"raw_attack": raw_label, "dataset": "CICIDS2017"}
        )

    @staticmethod
    def normalize_unsw_nb15(row: Dict[str, Any]) -> CanonicalEvent:
        """Adapts a UNSW-NB15 flow record."""
        cat = str(row.get("attack_cat") or row.get("attack_category") or "Normal").strip().capitalize()
        bin_label = int(row.get("label", 0))

        if cat in ("Normal", "") or bin_label == 0:
            attack_type = "BENIGN"
            label = 0
        elif "Dos" in cat:
            attack_type = "DOS"
            label = 1
        elif "Reconnaissance" in cat or "Scan" in cat:
            attack_type = "PORT_SCAN"
            label = 1
        elif "Backdoor" in cat or "Exploit" in cat or "Shellcode" in cat:
            attack_type = "INFILTRATION"
            label = 1
        elif "Worm" in cat:
            attack_type = "BOTNET"
            label = 1
        elif "Fuzzer" in cat or "Generic" in cat:
            attack_type = "OTHER"
            label = 1
        else:
            attack_type = "OTHER"
            label = 1

        dst_port = int(float(row.get("dsport", row.get("dst_port", 80))))
        asset_id, asset_type = _map_port_to_smart_city_asset(dst_port, str(row.get("proto", "")))
        dur = float(row.get("dur", row.get("duration", 0.05)))
        sbytes = float(row.get("sbytes", 256))
        dbytes = float(row.get("dbytes", 128))
        spkts = int(float(row.get("Spkts", 2)))
        dpkts = int(float(row.get("Dpkts", 1)))
        tot_pkts = max(1, spkts + dpkts)

        return CanonicalEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_ip=str(row.get("srcip", "10.40.0.12")),
            destination_ip=str(row.get("dstip", "149.171.126.1")),
            source_port=int(float(row.get("sport", 34210))),
            destination_port=dst_port,
            protocol=str(row.get("proto", "tcp")).upper(),
            bytes_in=dbytes,
            bytes_out=sbytes,
            packets=tot_pkts,
            duration=round(max(0.0001, dur), 6),
            request_rate=round(tot_pkts / max(0.001, dur), 2),
            error_rate=0.0 if label == 0 else 0.5,
            asset_id=asset_id,
            asset_type=asset_type,
            location="Smart City Central Grid",
            attack_type=attack_type,
            label=label,
            metadata={"raw_attack": cat, "dataset": "UNSW-NB15"}
        )

    @staticmethod
    def normalize_nsl_kdd(row: Dict[str, Any]) -> CanonicalEvent:
        """Adapts an NSL-KDD network intrusion record."""
        cls_name = str(row.get("class", "normal")).lower().strip()

        dos_attacks = {"neptune", "smurf", "back", "teardrop", "pod", "land", "apache2"}
        probe_attacks = {"satan", "ipsweep", "portsweep", "nmap", "mscan", "saint"}
        r2l_attacks = {"guess_passwd", "ftp_write", "imap", "phf", "multihop", "warezmaster", "warezclient"}
        u2r_attacks = {"buffer_overflow", "rootkit", "loadmodule", "perl", "ps", "xterm"}

        if cls_name == "normal":
            attack_type = "BENIGN"
            label = 0
        elif cls_name in dos_attacks:
            attack_type = "DOS"
            label = 1
        elif cls_name in probe_attacks:
            attack_type = "PORT_SCAN"
            label = 1
        elif cls_name in r2l_attacks:
            attack_type = "BRUTE_FORCE"
            label = 1
        elif cls_name in u2r_attacks:
            attack_type = "INFILTRATION"
            label = 1
        else:
            attack_type = "OTHER"
            label = 1

        service = str(row.get("service", "http")).lower()
        dst_port = 80
        if "ftp" in service: dst_port = 21
        elif "ssh" in service: dst_port = 22
        elif "telnet" in service: dst_port = 23
        elif "smtp" in service: dst_port = 25
        elif "dns" in service or "domain" in service: dst_port = 53
        elif "http" in service: dst_port = 80
        elif "ssl" in service or "https" in service: dst_port = 443

        asset_id, asset_type = _map_port_to_smart_city_asset(dst_port, service)
        dur = float(row.get("duration", 0.0))
        src_bytes = float(row.get("src_bytes", 150))
        dst_bytes = float(row.get("dst_bytes", 120))
        count = max(1, int(float(row.get("count", 1))))
        serror_rate = float(row.get("serror_rate", 0.0))

        return CanonicalEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_ip="192.168.1.105",
            destination_ip="10.0.0.5",
            source_port=51200,
            destination_port=dst_port,
            protocol=str(row.get("protocol_type", "tcp")).upper(),
            bytes_in=dst_bytes,
            bytes_out=src_bytes,
            packets=count,
            duration=max(0.001, dur),
            request_rate=float(count),
            error_rate=round(serror_rate, 4),
            asset_id=asset_id,
            asset_type=asset_type,
            location="Municipal Administration Core",
            attack_type=attack_type,
            label=label,
            metadata={"raw_attack": cls_name, "dataset": "NSL-KDD"}
        )

    @staticmethod
    def normalize_ton_iot(row: Dict[str, Any]) -> CanonicalEvent:
        """Adapts a TON_IoT telemetry record."""
        raw_type = str(row.get("type", "normal")).lower().strip()
        raw_label = int(row.get("label", 0))

        if raw_type == "normal" or raw_label == 0:
            attack_type = "BENIGN"
            label = 0
        elif "ddos" in raw_type:
            attack_type = "DDOS"
            label = 1
        elif "dos" in raw_type:
            attack_type = "DOS"
            label = 1
        elif "scan" in raw_type:
            attack_type = "PORT_SCAN"
            label = 1
        elif "password" in raw_type or "bruteforce" in raw_type:
            attack_type = "BRUTE_FORCE"
            label = 1
        elif "injection" in raw_type or "xss" in raw_type:
            attack_type = "WEB_ATTACK"
            label = 1
        else:
            attack_type = "OTHER"
            label = 1

        dst_port = int(row.get("dst_port", 80))
        src_port = int(row.get("src_port", 45000))
        dur = max(0.0001, float(row.get("duration", 0.05)))
        src_bytes = float(row.get("src_bytes", 100))
        dst_bytes = float(row.get("dst_bytes", 200))
        tot_bytes = src_bytes + dst_bytes

        asset_id, asset_type = _map_port_to_smart_city_asset(dst_port)

        return CanonicalEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_ip=str(row.get("src_ip", "192.168.1.112")),
            destination_ip=str(row.get("dst_ip", "10.0.0.2")),
            source_port=src_port,
            destination_port=dst_port,
            protocol=str(row.get("proto", "tcp")).upper(),
            bytes_in=dst_bytes,
            bytes_out=src_bytes,
            packets=max(1, int(tot_bytes / 64)),
            duration=dur,
            request_rate=max(1.0, 1.0 / dur),
            error_rate=0.0 if label == 0 else 0.4,
            asset_id=asset_id,
            asset_type=asset_type,
            location="Smart Water & SCADA Substation",
            attack_type=attack_type,
            label=label,
            metadata={"raw_attack": raw_type, "dataset": "TON_IoT"}
        )


# Convenience module-level aliases
normalize_cicids2017 = DatasetNormalizer.normalize_cicids2017
normalize_unsw_nb15 = DatasetNormalizer.normalize_unsw_nb15
normalize_ton_iot = DatasetNormalizer.normalize_ton_iot
normalize_nsl_kdd = DatasetNormalizer.normalize_nsl_kdd
