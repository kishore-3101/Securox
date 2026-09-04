"""
FASTag Toll Scan Data Generator & Anomaly Injector

This script generates synthetic FASTag toll scan events along highway route NH44 
and injects realistic tag cloning anomalies for testing anomaly detection logic.

Outputs created:
1. tollgate_distances.csv - Pairwise highway distances and minimum travel times.
2. toll_scans.csv           - Chronological FASTag scan log with 6 injected cloning anomalies.
"""

import random
import pandas as pd
from datetime import datetime, timedelta

# Set random seed for reproducible dataset generation
random.seed(42)

def generate_tollgate_distances():
    """
    Creates 8 tollgates (TG-01 to TG-08) along highway NH44.
    Distances between adjacent gates are randomized between 40 km and 60 km.
    Computes pairwise distances and minimum travel times assuming 100 km/h max speed limit.
    """
    gate_names = [f"TG-0{i}" for i in range(1, 9)]
    
    # Generate random distances between adjacent gates (40 to 60 km)
    adjacent_distances = [round(random.uniform(40.0, 60.0), 1) for _ in range(7)]
    
    # Calculate cumulative positions (in km) along NH44 starting at TG-01 = 0 km
    positions = {gate_names[0]: 0.0}
    current_pos = 0.0
    for i in range(7):
        current_pos += adjacent_distances[i]
        positions[gate_names[i+1]] = round(current_pos, 1)
        
    # Generate distance matrix for all pairs of tollgates
    distances_data = []
    for g1 in gate_names:
        for g2 in gate_names:
            if g1 != g2:
                dist_km = round(abs(positions[g2] - positions[g1]), 1)
                # min_travel_time_min assumes max speed limit of 100 km/h
                min_time_min = round((dist_km / 100.0) * 60.0, 2)
                distances_data.append({
                    "from_gate": g1,
                    "to_gate": g2,
                    "distance_km": dist_km,
                    "min_travel_time_min": min_time_min
                })
                
    df_distances = pd.DataFrame(distances_data)
    df_distances.to_csv("tollgate_distances.csv", index=False)
    print("Created 'tollgate_distances.csv' successfully.")
    return gate_names, positions, df_distances


def generate_vehicles(count=50):
    """
    Generates 50 unique vehicles with TAG IDs and vehicle registration plates.
    """
    vehicles = []
    state_codes = ["KA", "MH", "DL", "TN", "HR", "UP", "GJ", "TS"]
    
    for i in range(1, count + 1):
        tag_id = f"TAG-{1000 + i}"
        state = random.choice(state_codes)
        rto = f"{random.randint(1, 99):02d}"
        series = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
        num = f"{random.randint(1000, 9999)}"
        plate = f"{state}{rto}{series}{num}"
        vehicles.append({"tag_id": tag_id, "vehicle_plate": plate})
        
    return vehicles


def generate_normal_scans(vehicles, gate_names, positions):
    """
    Simulates each vehicle traveling through 3-6 consecutive tollgates 
    at realistic speeds (60-90 km/h) over a single day.
    """
    scans = []
    base_date = datetime(2026, 9, 3)
    
    for vehicle in vehicles:
        tag_id = vehicle["tag_id"]
        plate = vehicle["vehicle_plate"]
        
        # 3 to 6 consecutive gates
        num_gates = random.randint(3, 6)
        # Random direction: True for forward (TG-01 -> TG-08), False for reverse
        forward = random.choice([True, False])
        
        if forward:
            start_idx = random.randint(0, len(gate_names) - num_gates)
            route_gate_indices = list(range(start_idx, start_idx + num_gates))
        else:
            start_idx = random.randint(num_gates - 1, len(gate_names) - 1)
            route_gate_indices = list(range(start_idx, start_idx - num_gates, -1))
            
        # Random departure time between 05:00 and 17:00
        current_time = base_date + timedelta(
            hours=random.randint(5, 17),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        for k in range(len(route_gate_indices)):
            gate_idx = route_gate_indices[k]
            gate_id = gate_names[gate_idx]
            
            if k > 0:
                prev_gate_idx = route_gate_indices[k - 1]
                dist_km = abs(positions[gate_names[gate_idx]] - positions[gate_names[prev_gate_idx]])
                
                # Speed between 60 km/h and 90 km/h with minor random noise
                speed_kmh = random.uniform(60.0, 90.0)
                travel_minutes = (dist_km / speed_kmh) * 60.0 + random.uniform(0.5, 3.0)
                current_time += timedelta(minutes=travel_minutes)
                
            scans.append({
                "tag_id": tag_id,
                "vehicle_plate": plate,
                "tollgate_id": gate_id,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "route_id": "NH44"
            })
            
    return scans


def inject_tag_cloning_anomalies(scans, gate_names, positions, count=6):
    """
    Injects tag cloning anomalies:
    Selects 6 tag_ids and inserts an extra scan event at the NEXT tollgate 
    in 5-10 minutes (violating the minimum travel time threshold).
    """
    # Group scans by tag_id to find suitable candidate scans
    tag_scans_map = {}
    for s in scans:
        tag_scans_map.setdefault(s["tag_id"], []).append(s)
        
    # Select 6 unique tag_ids
    candidate_tags = random.sample(list(tag_scans_map.keys()), count)
    injected_anomalies_info = []
    
    for tag_id in candidate_tags:
        tag_scans = tag_scans_map[tag_id]
        # Choose a reference normal scan event
        ref_scan = random.choice(tag_scans)
        ref_gate = ref_scan["tollgate_id"]
        ref_time = datetime.strptime(ref_scan["timestamp"], "%Y-%m-%d %H:%M:%S")
        
        ref_gate_idx = gate_names.index(ref_gate)
        # Determine the next tollgate along the highway (forward if possible, else backward)
        if ref_gate_idx < len(gate_names) - 1:
            next_gate_idx = ref_gate_idx + 1
        else:
            next_gate_idx = ref_gate_idx - 1
            
        next_gate = gate_names[next_gate_idx]
        
        # Calculate true distance and minimum possible travel time (at 100 km/h)
        dist_km = abs(positions[next_gate] - positions[ref_gate])
        min_time_required = (dist_km / 100.0) * 60.0
        
        # Inject cloned scan in 5 to 10 minutes (impossible travel time)
        anomaly_minutes = random.uniform(5.0, 10.0)
        anomaly_time = ref_time + timedelta(minutes=anomaly_minutes)
        
        anomalous_scan = {
            "tag_id": tag_id,
            "vehicle_plate": ref_scan["vehicle_plate"],
            "tollgate_id": next_gate,
            "timestamp": anomaly_time.strftime("%Y-%m-%d %H:%M:%S"),
            "route_id": "NH44"
        }
        
        scans.append(anomalous_scan)
        
        injected_anomalies_info.append({
            "tag_id": tag_id,
            "vehicle_plate": ref_scan["vehicle_plate"],
            "ref_gate": ref_gate,
            "ref_time": ref_scan["timestamp"],
            "next_gate": next_gate,
            "anomaly_time": anomalous_scan["timestamp"],
            "elapsed_minutes": round(anomaly_minutes, 2),
            "min_travel_time_min": round(min_time_required, 2),
            "distance_km": round(dist_km, 1)
        })
        
    return scans, injected_anomalies_info


def main():
    print("--- FASTag Synthetic Data Generator & Anomaly Injector ---")
    
    # 1. Setup Tollgates and Distances
    gate_names, positions, df_distances = generate_tollgate_distances()
    
    # 2. Setup 50 Unique Vehicles
    vehicles = generate_vehicles(count=50)
    
    # 3. Generate Normal Scans
    scans = generate_normal_scans(vehicles, gate_names, positions)
    normal_count = len(scans)
    print(f"Generated {normal_count} normal toll scan events.")
    
    # 4. Inject 6 Tag Cloning Anomalies
    scans, injected_anomalies = inject_tag_cloning_anomalies(scans, gate_names, positions, count=6)
    
    # 5. Sort Scans Chronologically and Save
    df_scans = pd.DataFrame(scans)
    df_scans["dt"] = pd.to_datetime(df_scans["timestamp"])
    df_scans = df_scans.sort_values("dt").drop(columns=["dt"])
    df_scans.to_csv("toll_scans.csv", index=False)
    print(f"Saved total {len(df_scans)} scan events to 'toll_scans.csv'.\n")
    
    # 6. Print Summary of Injected Anomalies
    print("=" * 85)
    print("INJECTED CLONING ANOMALIES (Use this list to verify your detection logic):")
    print("=" * 85)
    print(f"{'TAG ID':<10} | {'PLATE':<12} | {'FROM GATE':<9} -> {'TO GATE':<9} | {'ORIGINAL TIME':<19} | {'ANOMALY TIME':<19} | {'ELAPSED':<8} | {'MIN REQUIRED'}")
    print("-" * 85)
    for a in injected_anomalies:
        print(f"{a['tag_id']:<10} | {a['vehicle_plate']:<12} | {a['ref_gate']:<9} -> {a['next_gate']:<9} | {a['ref_time']:<19} | {a['anomaly_time']:<19} | {a['elapsed_minutes']:>5.1f} min | {a['min_travel_time_min']:>6.1f} min")
    print("=" * 85)


if __name__ == "__main__":
    main()
