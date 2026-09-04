"""
Securox — Real-Time Dataset Replay Engine (SH-FIN-05)
Streams canonical smart-city network & IoT events from benchmark datasets
(CICIDS2017, UNSW-NB15, TON_IoT, NSL-KDD) into the live Securox platform.

Usage:
    python replay.py --dataset cicids2017 --speed 5.0 --limit 50
    python replay.py --dataset unsw_nb15 --speed 10.0
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
import pandas as pd
import requests

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.schema import CanonicalEvent
from data.normalizer import DatasetNormalizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("securox.replay")


def run_replay(
    dataset_name: str = "cicids2017",
    speed: float = 2.0,
    limit: int = 50,
    api_url: str = "http://127.0.0.1:8000/api/events",
    loop: bool = False
):
    csv_map = {
        "cicids2017": (PROJECT_ROOT / "data" / "cicids2017_sample.csv", DatasetNormalizer.normalize_cicids2017),
        "unsw_nb15": (PROJECT_ROOT / "data" / "unsw_nb15_sample.csv", DatasetNormalizer.normalize_unsw_nb15),
        "nsl_kdd": (PROJECT_ROOT / "data" / "nsl_kdd_sample.csv", DatasetNormalizer.normalize_nsl_kdd),
        "ton_iot": (PROJECT_ROOT / "data" / "ton_iot_sample.csv", DatasetNormalizer.normalize_ton_iot),
    }

    if dataset_name not in csv_map:
        logger.error("Unknown dataset '%s'. Available: %s", dataset_name, list(csv_map.keys()))
        return

    csv_path, normalizer_fn = csv_map[dataset_name]
    if not csv_path.exists():
        logger.error("Dataset file not found at %s. Please run data/download_datasets.py first.", csv_path)
        return

    print("=" * 80)
    print(f"  SECUROX REAL-TIME DATASET REPLAY ENGINE (SH-FIN-05)")
    print(f"  Dataset:     {dataset_name.upper()} ({csv_path.name})")
    print(f"  Speed Multi: {speed}x")
    print(f"  Limit:       {limit} events (loop={loop})")
    print(f"  Endpoint:    {api_url}")
    print("=" * 80)

    # Load and normalize dataset
    print(f"[*] Ingesting and normalizing {csv_path.name}...")
    df_raw = pd.read_csv(csv_path)
    total_available = len(df_raw)
    sample_to_use = df_raw.head(limit * 2 if limit else 500)
    records = [normalizer_fn(row).to_dict() for row in sample_to_use.to_dict(orient="records")]
    print(f"[+] Loaded {total_available:,} records (buffered {len(records)} for streaming).\n")

    base_delay = max(0.01, 1.0 / speed)
    sent_count = 0
    anomalies_detected = 0

    try:
        while True:
            for idx, row in enumerate(records):
                if limit and sent_count >= limit:
                    break

                t_start = time.perf_counter()
                try:
                    resp = requests.post(api_url, json=row, timeout=3.0)
                    t_latency = (time.perf_counter() - t_start) * 1000.0
                    if resp.status_code == 200:
                        res = resp.json()
                        risk_score = res.get("risk_score", 0.0)
                        severity = res.get("severity", "NORMAL")
                        attack = res.get("attack_type", "BENIGN")
                        asset = res.get("asset_id", "UNKNOWN")

                        if severity in ("CRITICAL", "HIGH", "CATASTROPHIC"):
                            anomalies_detected += 1
                            tag = f"\033[91m[{severity}]\033[0m"
                        elif severity == "MODERATE":
                            tag = f"\033[93m[{severity}]\033[0m"
                        else:
                            tag = f"\033[92m[{severity}]\033[0m"

                        print(f"  #{sent_count+1:03d} | {tag:<20} | Risk: {risk_score:>5.1f} | Asset: {asset:<18} | Attack: {attack:<14} | Latency: {t_latency:>5.2f}ms")
                    else:
                        print(f"  #{sent_count+1:03d} | [HTTP {resp.status_code}] Failed to stream record")
                except Exception as ex:
                    print(f"  #{sent_count+1:03d} | Connection Error: {ex}")

                sent_count += 1
                time.sleep(base_delay)

            if not loop or (limit and sent_count >= limit):
                break

    except KeyboardInterrupt:
        print("\n[*] Replay stopped by user.")

    print("\n" + "=" * 80)
    print(f"  REPLAY COMPLETED")
    print(f"  Total Ingested:      {sent_count} events")
    print(f"  Critical Incidents:  {anomalies_detected} flagged")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Securox Smart City Real-Time Telemetry Replay Engine")
    parser.add_argument("--dataset", type=str, default="cicids2017", choices=["cicids2017", "unsw_nb15", "nsl_kdd", "ton_iot"])
    parser.add_argument("--speed", type=float, default=5.0, help="Replay speed multiplier (default: 5.0x)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of events to replay (default: 20)")
    parser.add_argument("--target-url", type=str, default="http://127.0.0.1:8000/api/events", help="Target API endpoint")
    parser.add_argument("--loop", action="store_true", help="Loop continuously through the dataset")
    args = parser.parse_args()

    run_replay(
        dataset_name=args.dataset,
        speed=args.speed,
        limit=args.limit,
        api_url=args.target_url,
        loop=args.loop
    )
