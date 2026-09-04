export type SignalPhase = 'RED' | 'YELLOW' | 'GREEN' | 'FLASHING_RED' | string;

export interface TrafficSignal {
  id: string;
  name?: string;
  intersection?: string;
  intersection_id?: string;
  zone?: string;
  controller_id?: string;
  current_phase?: SignalPhase;
  current_state?: SignalPhase;
  phase_duration_seconds?: number;
  time_in_current_phase?: number;
  cycle_time_sec?: number;
  timing_plan?: string;
  mode: 'AUTO' | 'ADAPTIVE' | 'MANUAL' | 'MANUAL_OVERRIDE' | 'GREEN_CORRIDOR' | 'FAILSAFE' | string;
  status?: 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'MAINTENANCE_LOCK' | string;
  is_active?: boolean;
  is_tampered?: boolean | number;
  is_compromised?: boolean | number;
  last_override_by?: string;
  last_command_time?: string;
  conflict_group?: string;
  latitude?: number;
  longitude?: number;
  road_name?: string;
  last_updated?: string;
  updated_at?: string;
}

export interface CameraFeed {
  id: string;
  name: string;
  location: string;
  latitude?: number;
  longitude?: number;
  status: 'ONLINE' | 'OFFLINE' | 'TAMPERED' | 'DEGRADED' | 'MAINTENANCE' | string;
  camera_type?: 'FIXED' | 'PTZ' | 'THERMAL' | 'ANPR' | 'MOBILE_APP' | string;
  stream_type?: 'RTSP' | 'WEBRTC' | 'HLS' | 'SIMULATED' | string;
  stream_url?: string;
  vehicles_detected?: number;
  speed_average_kmh?: number;
  anomalies_detected?: number;
  last_plate_detected?: string;
  fps?: number;
  resolution?: string;
  incident_count?: number;
  intersection_id?: string;
  road_id?: string;
  health?: string;
  last_seen?: string;
  device_id?: string;
  trust_status?: string;
  risk_score?: number;
  webrtc_active?: boolean;
  subscribers_count?: number;
  created_at?: string;
  updated_at?: string;
  metadata_json?: Record<string, any>;
}

export interface MobileCameraSession {
  session_id: string;
  device_id: string;
  camera_id: string;
  operator_id: string;
  trust_status: 'PENDING' | 'TRUSTED' | 'UNTRUSTED' | 'REVOKED' | string;
  risk_score: number;
  fps: number;
  resolution: string;
  battery_level?: number;
  signal_strength?: number;
  status: 'INITIALIZING' | 'STREAMING' | 'PAUSED' | 'TERMINATED' | string;
  created_at: string;
  expires_at?: string;
}

export interface VehicleDetection {
  id: string;
  camera_id: string;
  tracking_id: string;
  vehicle_type: 'SEDAN' | 'SUV' | 'TRUCK' | 'BUS' | 'MOTORCYCLE' | 'AMBULANCE' | string;
  plate_number: string;
  plate_confidence: number;
  ocr_status: 'CONFIRMED' | 'OCR_UNCERTAIN' | 'LOW_CONFIDENCE' | string;
  speed_kmh: number;
  timestamp: string;
  metadata_json?: Record<string, any>;
}

export interface RFIDReader {
  id: string;
  name: string;
  location: string;
  intersection_id?: string;
  road_id?: string;
  tollgate_id?: string;
  frequency_mhz: number;
  status: 'ONLINE' | 'OFFLINE' | 'TAMPERED' | string;
  last_heartbeat?: string;
}

export interface RFIDRead {
  id: string;
  reader_id: string;
  tag_id: string;
  epc: string;
  signal_rssi: number;
  timestamp: string;
  lane_id?: string;
}

export interface FastagRecord {
  tag_id: string;
  registered_plate: string;
  vehicle_class: string;
  owner_name: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'BLACKLISTED' | 'LOW_BALANCE' | string;
  balance: number;
  issuer_bank: string;
}

export interface VehicleVerificationRecord {
  id: string;
  timestamp: string;
  location: string;
  camera_id?: string;
  rfid_reader_id?: string;
  tracking_id?: string;
  ocr_plate: string;
  rfid_tag_id: string;
  rfid_registered_plate: string;
  ocr_confidence: number;
  rfid_rssi: number;
  verification_status:
    | 'VERIFIED'
    | 'MISMATCH'
    | 'NO_RFID_DETECTED'
    | 'MANUALLY_APPROVED_NO_RFID'
    | 'REJECTED_NO_RFID'
    | 'OCR_ONLY'
    | 'RFID_ONLY'
    | 'UNKNOWN_TAG'
    | 'UNKNOWN_PLATE'
    | 'LOW_CONFIDENCE'
    | 'DUPLICATE_READ'
    | 'STALE_READ'
    | string;
  repeated_mismatch_count: number;
  risk_score: number;
  escalation_status: 'NONE' | 'FLAGGED' | 'ESCALATED_TO_SOC' | string;
  action_taken: string;
  journey_cameras?: string[];
  manual_approved?: boolean;
  operator_reason?: string;
}

export interface Intersection {
  id: string;
  name: string;
  corridor: string;
  latitude: number;
  longitude: number;
  congestion_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'GRIDLOCK' | string;
  average_wait_time_sec: number;
  queue_length?: number;
  risk_score?: number;
  status?: string;
  signal_phase?: string;
  signals?: TrafficSignal[];
}

export interface RoadSegment {
  id: string;
  name: string;
  route_id?: string;
  start_node?: string;
  end_node?: string;
  corridor?: string;
  length_km: number;
  lanes?: number;
  speed_limit_kmh: number;
  current_speed_kmh: number;
  free_flow_speed_kmh?: number;
  current_volume?: number;
  congestion_index?: number; // 0.0 - 1.0
  congestion_level: 'LOW' | 'MODERATE' | 'HEAVY' | 'CRITICAL' | string;
  active_incidents?: number;
  incident_count?: number;
  density_score?: number;
  status?: string;
  coordinates?: [number, number][];
  last_updated?: string;
}

export interface TrafficSensor {
  id: string;
  type: 'INDUCTIVE_LOOP' | 'RADAR_SPEED' | 'BLUETOOTH' | string;
  location: string;
  latitude: number;
  longitude: number;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'TAMPERED';
  last_reading: number;
  expected_range_min: number;
  expected_range_max: number;
  confidence: number;
  anomaly_detected: boolean | number;
  last_heartbeat?: string;
}

export interface SensorDisparityRecord {
  junction: string;
  sensor_id: string;
  sensor_type: string;
  sensor_count: number;
  camera_id: string;
  camera_detected_count: number;
  disparity_delta: number;
  disparity_pct: number;
  status: 'NOMINAL' | 'ANOMALOUS_DISPARITY';
  confidence: number;
  diagnosis: string;
}

export interface SensorDisparityReport {
  status: string;
  timestamp: string;
  pairs_analyzed: number;
  anomalies_detected: number;
  systemic_integrity_score: number;
  disparity_pairs: SensorDisparityRecord[];
  disparity_alerts: SensorDisparityRecord[];
  cross_comparison: SensorDisparityRecord[];
}

export interface TrafficIncident {
  id: string;
  title: string;
  category: 'COLLISION' | 'VEHICLE_BREAKDOWN' | 'WRONG_WAY' | 'HAZARD' | 'SENSOR_FAILURE' | string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'REPORTED' | 'VERIFIED' | 'DISPATCHED' | 'RESOLVED';
  location: string;
  road_id?: string;
  intersection_id?: string;
  reported_by: string;
  assigned_officer?: string;
  verified: boolean | number;
  verified_by?: string;
  verified_at?: string;
  resolution_notes?: string;
  reported_at: string;
  resolved_at?: string;
}

export interface TollScanRecord {
  id: string;
  tollgate_id: string;
  tollgate_name: string;
  vehicle_number: string;
  fastag_id: string;
  timestamp: string;
  status: 'CLEARED' | 'SUSPECT' | 'BLACKLISTED' | 'CLONED' | 'OVERRIDDEN_CLEARED';
  amount: number;
  flag_reason?: string;
  override_by?: string;
  override_reason?: string;
}

export interface GreenCorridor {
  id: string;
  name: string;
  emergency_dispatch_id?: string;
  ambulance_id?: string;
  status: 'STANDBY' | 'ACTIVE' | 'COMPLETED';
  origin_location: string;
  destination_hospital: string;
  route_intersections: string[];
  active_signal_id?: string;
  cleared_signals?: string[];
  corridor_cameras?: string[];
  camera_coverage?: string;
  estimated_duration_sec?: number;
  congestion_level?: number;
  activated_at?: string;
  cleared_at?: string;
}

export interface MaintenanceTicket {
  id: string;
  signal_id: string;
  technician_id: string;
  issue_type: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED';
  voltage_reading: number;
  loop_resistance_ohms: number;
  firmware_checksum: string;
  diagnostic_log?: string;
  resolution_notes?: string;
  created_at: string;
  completed_at?: string;
}

export interface CitizenPublicFeed {
  city: string;
  timestamp: string;
  overall_traffic_status: string;
  average_transit_speed_kmh: number;
  active_green_corridors_advisories: Array<{
    corridor_name: string;
    advisory: string;
  }>;
  corridors: Array<{
    corridor: string;
    congestion_level: string;
    speed_kmh: number;
    travel_delay_minutes: number;
  }>;
  public_incidents: Array<{
    title: string;
    category: string;
    location: string;
    reported_at: string;
  }>;
}

export interface TrafficOverview {
  grid_status: string;
  total_signals: number;
  total_roads: number;
  total_sensors: number;
  active_incidents_count: number;
  active_green_corridors: number;
  sensor_disparity_alerts: number;
  average_speed_kmh: number;
  grid_congestion_index: string;
  timestamp: string;
}

export interface SignalSafetyOverrideRequest {
  target_state: 'RED' | 'YELLOW' | 'GREEN';
  mode?: string;
  reason: string;
  context_type: 'EMERGENCY_PREEMPTION' | 'INCIDENT_CLEARANCE' | 'SCHEDULED_MAINTENANCE' | 'CONGESTION_MITIGATION' | 'MANUAL_OVERRIDE';
  context_ref?: string;
}

export interface SafetyTransitionStage {
  stage: number;
  phase: string;
  duration_seconds: number;
  action: string;
}

export interface SignalSafetyOverrideResponse {
  allowed: boolean;
  status: string;
  signal_id: string;
  previous_state: string;
  target_state: string;
  mode: string;
  conflict_detected: boolean;
  conflicting_signal_cleared?: string;
  safety_transition_plan: SafetyTransitionStage[];
  audit_id: string;
  executed_by: string;
  timestamp: string;
  detail?: string;
}