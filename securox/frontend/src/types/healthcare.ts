export type TriagePriority = 'P1_CRITICAL' | 'P2_URGENT' | 'P3_DELAYED' | 'P4_EXPECTANT';
export type AmbulanceStatus = 'AVAILABLE' | 'EN_ROUTE' | 'ON_SCENE' | 'TRANSPORTING' | 'AT_HOSPITAL' | 'COMPLETED' | 'MAINTENANCE' | 'ARRIVED_ER';

export interface Patient {
  id: string;
  hospital_id?: string;
  name: string;
  age: number;
  gender: string;
  department: string;
  assigned_doctor_id?: string;
  assigned_nurse_id?: string;
  condition: string;
  diagnosis?: string;
  triage_level?: string;
  room_number?: string;
  room_bed?: string;
  vitals?: {
    heart_rate_bpm?: number;
    blood_pressure_sys?: number;
    blood_pressure_dia?: number;
    oxygen_saturation_pct?: number;
    temperature_c?: number;
    respiration_rate?: number;
    bp?: string;
    hr?: number;
    spo2?: number;
    temp?: number;
  };
  sensitivity?: 'GENERAL' | 'RESTRICTED' | 'CONFIDENTIAL';
  admission_date?: string;
  admitted_at?: string;
  created_at?: string;
}

export interface MedicalRecord {
  id: string;
  patient_id: string;
  doctor_id: string;
  doctor_name?: string;
  department?: string;
  diagnosis: string;
  treatment_plan?: string;
  prescriptions: string[] | string;
  lab_results: Record<string, any> | string;
  treatment_notes?: string;
  notes?: string;
  sensitivity?: string;
  created_at: string;
  updated_at?: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  patient_name?: string;
  hospital_id: string;
  department: string;
  doctor_id: string;
  scheduled_at: string;
  status: 'SCHEDULED' | 'CONFIRMED' | 'IN_CONSULTATION' | 'COMPLETED' | 'CANCELLED';
  reason: string;
  created_at: string;
}

export interface Admission {
  id: string;
  patient_id: string;
  patient_name?: string;
  hospital_id: string;
  department: string;
  room_bed: string;
  admission_type: 'EMERGENCY' | 'PLANNED' | 'ICU' | 'TRANSFER';
  admitting_doctor_id: string;
  assigned_nurse_id: string;
  admitted_at: string;
  discharge_date?: string;
  status: 'ADMITTED' | 'DISCHARGED' | 'TRANSFERRED';
}

export interface LabOrder {
  id: string;
  patient_id: string;
  patient_name?: string;
  doctor_id: string;
  test_name: string;
  category: string;
  priority: 'ROUTINE' | 'STAT' | 'URGENT';
  status: 'ORDERED' | 'SAMPLE_COLLECTED' | 'IN_ANALYSIS' | 'COMPLETED' | 'CANCELLED';
  result_data?: Record<string, any>;
  reference_range?: string;
  flagged_abnormal: number | boolean;
  ordered_at: string;
  completed_at?: string;
  approved_by?: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  patient_name?: string;
  doctor_id: string;
  medication: string;
  dosage: string;
  frequency: string;
  duration: string;
  status: 'PRESCRIBED' | 'DISPENSED' | 'CANCELLED';
  ddi_warning?: string;
  ordered_at: string;
  dispensed_at?: string;
  pharmacist_id?: string;
}

export interface BillingInvoice {
  id: string;
  patient_id: string;
  patient_name?: string;
  hospital_id: string;
  total_amount: number;
  insurance_claim_amount: number;
  patient_payable: number;
  status: 'PENDING' | 'INSURANCE_PREAUTH' | 'SETTLED' | 'DISPUTED';
  payment_method: string;
  line_items?: Array<{ item: string; amount: number }>;
  created_at: string;
  settled_at?: string;
}

export interface EmergencyDispatch {
  id: string;
  ambulance_id: string;
  paramedic_id: string;
  patient_id?: string;
  caller_name: string;
  emergency_type: string;
  triage_priority: TriagePriority;
  origin_location: string;
  destination_hospital: string;
  green_corridor_active: boolean | number;
  vitals?: { hr?: number; bp?: string; spo2?: number; ecg?: string };
  dispatched_at: string;
  arrived_scene_at?: string;
  arrived_hospital_at?: string;
  status: 'DISPATCHED' | 'EN_ROUTE' | 'ON_SCENE' | 'IN_TRANSIT' | 'ARRIVED_ER' | 'COMPLETED';
}

export interface BreakGlassEvent {
  id: string;
  user_id: string;
  username: string;
  role: string;
  patient_id: string;
  department: string;
  hospital_id: string;
  reason: string;
  previous_risk_score: number;
  new_risk_score: number;
  notified_security: number | boolean;
  security_incident_id: string;
  timestamp: string;
}

export interface AmbulanceCAD {
  id: string;
  call_sign: string;
  vehicle_number: string;
  status: AmbulanceStatus;
  priority: TriagePriority;
  assigned_hospital: string;
  current_latitude: number;
  current_longitude: number;
  target_latitude?: number;
  target_longitude?: number;
  eta_minutes: number;
  patient_id?: string;
  crew: string[];
  green_corridor_active: boolean;
}

export interface IoMTDevice {
  id: string;
  name: string;
  department: string;
  ip_address: string;
  mac_address: string;
  protocol: string;
  firmware: string;
  status: 'ONLINE' | 'ANOMALOUS' | 'QUARANTINED' | 'OFFLINE';
  quarantine: boolean;
  risk_score: number;
  last_heartbeat: string;
}

export interface IoMTSensor {
  id: string;
  device_type: 'INFUSION_PUMP' | 'PACEMAKER' | 'VENTILATOR' | 'ICU_MONITOR' | 'DIALYSIS' | string;
  hospital: string;
  ward: string;
  patient_id?: string;
  ip_address: string;
  firmware_version: string;
  cyber_risk_score: number;
  status: 'OPERATIONAL' | 'SUSPICIOUS' | 'ATTACK_DETECTED' | 'ISOLATED';
  flow_rate_anomaly: boolean;
  tamper_detected: boolean;
  last_ping: string;
}

