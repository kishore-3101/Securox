"""
Securox — Data & Model Lab Service (SH-FIN-05 Sections 6, 7, 8, 40)
Handles dataset ingestion, column auto-mapping, data quality validation,
and controlled real-time dataset replay streaming.
"""

import os
import sys
import io
import json
import time
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
backend_dir = PROJECT_ROOT / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from data.schema import CanonicalEvent
from data.normalizer import DatasetNormalizer
from database.store import store

logger = logging.getLogger("securox.data_lab")
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Canonical Column Alias Mapping Dictionary
COLUMN_SYNONYMS = {
    "timestamp": ["timestamp", "time", "date", "datetime", "flow_start", "ts"],
    "source_ip": ["source_ip", "src_ip", "srcip", "source ip", "src_addr", "ip.src"],
    "destination_ip": ["destination_ip", "dst_ip", "dstip", "destination ip", "dst_addr", "ip.dst"],
    "source_port": ["source_port", "src_port", "sport", "source port", "srcport"],
    "destination_port": ["destination_port", "dst_port", "dport", "destination port", "dstport"],
    "protocol": ["protocol", "proto", "transport", "ip.proto"],
    "bytes_in": ["bytes_in", "bytes in", "fwd_bytes", "total length of fwd packets", "bwd_bytes", "tot_bytes", "bytes"],
    "bytes_out": ["bytes_out", "bytes out", "bwd_bytes", "total length of bwd packets", "out_bytes"],
    "packets": ["packets", "packet_count", "tot_pkts", "total fwd packets", "pkts", "spkts", "dpkts"],
    "duration": ["duration", "flow duration", "dur", "flow_duration"],
    "user": ["user", "username", "account", "user_id"],
    "asset_id": ["asset_id", "asset", "target", "host", "service", "destination"],
    "attack_type": ["attack_type", "attack", "label", "attack_cat", "threat", "class"],
    "label": ["label", "is_attack", "target", "class_label", "binary_label"]
}


class ReplayState:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.is_paused = False
        self.dataset_name = ""
        self.speed = 2.0
        self.events_processed = 0
        self.threats_detected = 0
        self.critical_incidents = 0
        self.avg_risk = 0.0
        self.peak_risk = 0.0
        self.detection_latency_ms = 1.2
        self.start_time = None
        self.total_target_events = 0


class DataLabService:
    def __init__(self):
        self.replay_state = ReplayState()
        self._cached_datasets: Dict[str, pd.DataFrame] = {}

    def auto_detect_mapping(self, columns: List[str]) -> Dict[str, str]:
        """Auto-detects mapping from raw CSV columns to CanonicalEvent fields."""
        mapping = {}
        cols_lower = {c.strip().lower(): c for c in columns}
        for canon_field, synonyms in COLUMN_SYNONYMS.items():
            for syn in synonyms:
                if syn in cols_lower:
                    mapping[canon_field] = cols_lower[syn]
                    break
        return mapping

    def validate_and_normalize_row(self, row: dict, mapping: dict) -> Tuple[Optional[CanonicalEvent], Optional[str]]:
        """Validates a single dataset record and builds a CanonicalEvent."""
        try:
            src_ip = str(row.get(mapping.get("source_ip", "source_ip"), "192.168.1.100")).strip()
            dst_ip = str(row.get(mapping.get("destination_ip", "destination_ip"), "10.0.0.1")).strip()
            if not src_ip or src_ip.lower() == "nan" or src_ip == "":
                return None, "Missing source IP"

            dst_port = int(float(row.get(mapping.get("destination_port", "destination_port"), 80) or 80))
            src_port = int(float(row.get(mapping.get("source_port", "source_port"), 49152) or 49152))
            proto = str(row.get(mapping.get("protocol", "protocol"), "TCP")).upper()

            bytes_in = float(row.get(mapping.get("bytes_in", "bytes_in"), 1024) or 1024)
            bytes_out = float(row.get(mapping.get("bytes_out", "bytes_out"), 512) or 512)
            packets = int(float(row.get(mapping.get("packets", "packets"), 20) or 20))
            duration = max(0.0001, float(row.get(mapping.get("duration", "duration"), 0.1) or 0.1))

            attack_val = str(row.get(mapping.get("attack_type", "attack_type"), "BENIGN")).strip().upper()
            label_val = int(float(row.get(mapping.get("label", "label"), 0 if "BENIGN" in attack_val else 1) or 0))

            asset_val = str(row.get(mapping.get("asset_id", "asset_id"), "TRAFFIC_CONTROL")).strip()
            if not asset_val or asset_val.lower() == "nan":
                asset_val = "TRAFFIC_CONTROL"

            evt = CanonicalEvent(
                timestamp=str(row.get(mapping.get("timestamp", "timestamp"), datetime.now(timezone.utc).isoformat())),
                source_ip=src_ip,
                destination_ip=dst_ip,
                source_port=src_port,
                destination_port=dst_port,
                protocol=proto,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                packets=packets,
                duration=duration,
                request_rate=round(packets / duration, 2),
                error_rate=0.0,
                asset_id=asset_val.upper(),
                asset_type=asset_val.lower(),
                attack_type=attack_val,
                label=label_val,
            )
            return evt, None
        except Exception as e:
            return None, str(e)

    def process_dataset_file(self, content: bytes, filename: str, custom_mapping: Optional[dict] = None) -> dict:
        """
        Parses CSV/JSON dataset, performs auto-detection, validates data quality,
        and caches the validated records.
        """
        if filename.endswith(".json") or filename.endswith(".jsonl"):
            try:
                data = json.loads(content.decode("utf-8"))
                df = pd.DataFrame(data if isinstance(data, list) else [data])
            except Exception:
                df = pd.read_json(io.BytesIO(content), lines=True)
        else:
            df = pd.read_csv(io.BytesIO(content))

        total_rows = len(df)
        mapping = custom_mapping or self.auto_detect_mapping(list(df.columns))

        valid_events = []
        rejected_count = 0
        duplicate_count = 0
        seen_keys = set()
        unknown_asset_count = 0

        sample_rows = df.head(500).to_dict(orient="records")
        for r in sample_rows:
            key = f"{r.get(mapping.get('source_ip'))}-{r.get(mapping.get('destination_ip'))}-{r.get(mapping.get('destination_port'))}"
            if key in seen_keys:
                duplicate_count += 1
            else:
                seen_keys.add(key)

            evt, err = self.validate_and_normalize_row(r, mapping)
            if evt:
                valid_events.append(evt.to_dict())
                if evt.asset_id in ("UNKNOWN", "TRAFFIC_CONTROL") and mapping.get("asset_id") not in r:
                    unknown_asset_count += 1
            else:
                rejected_count += 1

        # Save to uploads
        dest_path = UPLOAD_DIR / filename
        with open(dest_path, "wb") as f:
            f.write(content)

        dataset_id = f"DS-{uuid.uuid4().hex[:6].upper()}"
        self._cached_datasets[dataset_id] = df

        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "total_records": total_rows,
            "sample_tested": len(sample_rows),
            "valid_records": len(valid_events),
            "rejected_records": rejected_count,
            "duplicates_detected": duplicate_count,
            "unknown_assets_mapped": unknown_asset_count,
            "detected_mapping": mapping,
            "preview": valid_events[:5]
        }

    def list_datasets(self) -> List[dict]:
        """Lists built-in benchmark datasets and uploaded custom files."""
        benchmarks = [
            {
                "id": "cicids2017",
                "name": "CICIDS2017 Benchmark Flow Capture",
                "records": "3,000 Partitioned / 50,000 Total",
                "file": "data/cicids2017_sample.csv",
                "types": ["DDoS", "DoS", "Port Scan", "Brute Force", "Benign"],
                "data_provenance": "Canadian Institute for Cybersecurity (CIC)",
                "data_tag": "REAL DATASET",
                "status": "READY"
            },
            {
                "id": "unsw_nb15",
                "name": "UNSW-NB15 Modern Threat Benchmark",
                "records": "3,000 Partitioned / 45,000 Total",
                "file": "data/unsw_nb15_sample.csv",
                "types": ["Fuzzers", "Exploits", "Reconnaissance", "Generic"],
                "data_provenance": "UNSW Canberra Cyber Range",
                "data_tag": "REAL DATASET",
                "status": "READY"
            },
            {
                "id": "ton_iot",
                "name": "TON_IoT Industrial & SCADA Telemetry",
                "records": "2,500 Sample / 30,000 Total",
                "file": "data/ton_iot_sample.csv",
                "types": ["MQTT Broker Abuse", "Modbus Infiltration", "Telemetry Drop"],
                "data_provenance": "UNSW Cyber IoT Testbed",
                "data_tag": "REAL DATASET",
                "status": "READY"
            },
            {
                "id": "nsl_kdd",
                "name": "NSL-KDD Internet Service Telemetry",
                "records": "5,000 Sample / 125,973 Total",
                "file": "data/nsl_kdd_sample.csv",
                "types": ["Probe", "R2L", "U2R", "DoS", "Normal"],
                "data_provenance": "University of New Brunswick",
                "data_tag": "REAL DATASET",
                "status": "READY"
            }
        ]

        # Scan upload dir
        for f in UPLOAD_DIR.glob("*.*"):
            benchmarks.append({
                "id": f.stem,
                "name": f"Custom Upload: {f.name}",
                "records": f"{os.path.getsize(f) // 1024} KB",
                "file": str(f.relative_to(PROJECT_ROOT)),
                "types": ["Custom User Schema"],
                "data_provenance": "Analyst Upload",
                "data_tag": "USER DATASET",
                "status": "READY"
            })

        return benchmarks


data_lab = DataLabService()
