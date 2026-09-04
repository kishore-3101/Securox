import sys
import os
import asyncio
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.traffic_engine import stig
from services.ingestion import ingestion

async def test_stig_functions():
    print("=== Testing STIG Smart Traffic Intelligence Grid ===")
    
    # 1. Check baseline junctions
    status = await stig.get_stats()
    print(f"Junctions loaded: {list(status['junctions'].keys())}")
    
    # 2. Check signal override
    print("\nTesting signal manual override on Junction-A...")
    ok = await stig.override_signal("Junction-A", "RED")
    assert ok, "Override should succeed"
    status_override = await stig.get_stats()
    j_a = status_override["junctions"]["silk_board"]
    print(f"silk_board state: {j_a['state']}, override_active: {j_a['override_active']}")
    assert j_a["state"] == "RED", "State should be overridden to RED"
    assert j_a["override_active"] is True
    
    # 3. Check green corridor generation
    print("\nTesting green corridor emergency router...")
    route = ["Junction-A", "Junction-B", "Junction-C"]
    corridor = await stig.generate_green_corridor("AMB-100", route)
    print(f"Corridor generated: {corridor}")
    assert corridor["ambulance_id"] == "AMB-100"
    assert corridor["route"] == route
    
    # Check if junctions are overridden
    status_corridor = await stig.get_stats()
    for jid in ["silk_board", "dairy_circle", "town_hall"]:
        j = status_corridor["junctions"][jid]
        print(f"{jid} state during green corridor: {j['state']}, override_active: {j['override_active']}")
        assert j["state"] == "GREEN", f"{jid} state should be GREEN"
        assert j["override_active"] is True
        
    # 4. Check traffic violations tracking
    print("\nChecking traffic violations feed...")
    violations = await stig.get_recent_violations(limit=5)
    print(f"Recent violations fetched: {len(violations)}")
    for v in violations:
        print(f" - [{v['timestamp']}] Junction {v['junction_id']} - Vehicle {v['vehicle_id']} speed: {v['speed']} km/h (Limit: {v['speed_limit']})")
        
    # 5. Check Ingestion and Risk Scoring of custom threat flags
    print("\n=== Testing Log Ingestion Threat Flags ===")
    test_logs = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "cctv",
            "message": "Traffic Congestion level: CRITICAL. Objects detected: pedestrian, accident.",
            "metadata": {"camera_id": "CAM_F7482B4E"}
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "transit",
            "message": "FASTag scan transaction successful.",
            "metadata": {"toll_id": "TOLL_MUM_02", "rfid": "FT-883921-X"}
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "transit",
            "message": "Double debit or cloned RFID signature detected.",
            "metadata": {"toll_id": "TOLL_MUM_02", "rfid": "FT-883921-X"}
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "financial",
            "message": "UPI payment of INR 50,000 to merchant transport_ticketing failed due to mismatching IP geo-location.",
            "metadata": {"account_id": "ACC_9921", "upi_id": "pay@okaxis"}
        }
    ]
    
    for idx, log in enumerate(test_logs):
        res = ingestion.process_log(log)
        print(f"\nIngested log {idx + 1}:")
        print(f" Message: {log['message']}")
        print(f" Threat Flags Detected: {res.get('threat_flags')}")
        print(f" Risk Component Score: {res.get('risk_score')}")
        
    print("\n=== Verification Successful ===")

if __name__ == "__main__":
    asyncio.run(test_stig_functions())
