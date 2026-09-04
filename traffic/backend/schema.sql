-- Database: fastag

CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    tag_id VARCHAR UNIQUE NOT NULL,      -- EPC ID from RFID
    vehicle_plate VARCHAR UNIQUE NOT NULL -- Actual Number Plate
);
CREATE INDEX ix_vehicles_tag_id ON vehicles (tag_id);
CREATE INDEX ix_vehicles_vehicle_plate ON vehicles (vehicle_plate);

CREATE TABLE IF NOT EXISTS tollgates (
    id SERIAL PRIMARY KEY,
    gate_id VARCHAR UNIQUE NOT NULL,
    route VARCHAR
);
CREATE INDEX ix_tollgates_gate_id ON tollgates (gate_id);

CREATE TABLE IF NOT EXISTS tollgate_distances (
    id SERIAL PRIMARY KEY,
    from_gate VARCHAR NOT NULL,
    to_gate VARCHAR NOT NULL,
    distance_km FLOAT,
    min_travel_time_min FLOAT
);
CREATE INDEX ix_tollgate_distances_from_gate ON tollgate_distances (from_gate);
CREATE INDEX ix_tollgate_distances_to_gate ON tollgate_distances (to_gate);

CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    tag_id VARCHAR NOT NULL,
    vehicle_plate VARCHAR,          -- OCR Plate
    tollgate_id VARCHAR NOT NULL,
    direction VARCHAR,              -- IN / OUT
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    route_id VARCHAR
);
CREATE INDEX ix_scans_tag_id ON scans (tag_id);
CREATE INDEX ix_scans_vehicle_plate ON scans (vehicle_plate);
CREATE INDEX ix_scans_tollgate_id ON scans (tollgate_id);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    tag_id VARCHAR NOT NULL,
    vehicle_plate VARCHAR,
    from_gate VARCHAR,
    to_gate VARCHAR,
    actual_time_min FLOAT,
    min_travel_time_min FLOAT,
    reason VARCHAR,
    severity VARCHAR,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE
);
CREATE INDEX ix_anomalies_tag_id ON anomalies (tag_id);
