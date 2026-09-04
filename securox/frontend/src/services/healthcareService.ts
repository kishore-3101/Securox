import { api } from './api';
import {
  Patient,
  MedicalRecord,
  Appointment,
  Admission,
  LabOrder,
  Prescription,
  BillingInvoice,
  EmergencyDispatch,
  BreakGlassEvent,
  AmbulanceCAD,
  IoMTDevice,
} from '../types/healthcare';

export const healthcareService = {
  // 1. Patient Management
  async getPatients(assignedDoctor?: string, department?: string): Promise<{ status: string; total: number; patients: Patient[] }> {
    const params = new URLSearchParams();
    if (assignedDoctor) params.append('assigned_doctor', assignedDoctor);
    if (department) params.append('department', department);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/patients${query}`);
  },

  async getPatientDetail(patientId: string): Promise<{ status: string; patient: Patient; medical_records: MedicalRecord[] }> {
    return api.get(`/healthcare/patients/${patientId}`);
  },

  async createPatient(payload: {
    name: string;
    age: number;
    gender: string;
    department: string;
    condition?: string;
    diagnosis?: string;
    room_bed?: string;
    assigned_doctor_id?: string;
    assigned_nurse_id?: string;
    vitals?: Record<string, any>;
    hospital_id?: string;
  }): Promise<{ status: string; patient: Patient }> {
    return api.post('/healthcare/patients', payload);
  },

  async updatePatient(patientId: string, updates: Partial<Patient>): Promise<{ status: string; patient: Patient }> {
    return api.patch(`/healthcare/patients/${patientId}`, updates);
  },

  // 2. Emergency Break-Glass Access
  async triggerBreakGlass(patientId: string, reason: string): Promise<{
    status: string;
    patient: Patient;
    medical_records: MedicalRecord[];
    new_user_risk: number;
    incident_id: string;
    message: string;
  }> {
    return api.post('/healthcare/break-glass', { patient_id: patientId, reason });
  },

  async getBreakGlassLogs(): Promise<{ status: string; total: number; logs: BreakGlassEvent[] }> {
    return api.get('/healthcare/break-glass/logs');
  },

  // 3. Appointments
  async getAppointments(status?: string, department?: string): Promise<{ status: string; total: number; appointments: Appointment[] }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (department) params.append('department', department);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/appointments${query}`);
  },

  async createAppointment(payload: {
    patient_id: string;
    department: string;
    doctor_id: string;
    scheduled_at?: string;
    reason: string;
    hospital_id?: string;
  }): Promise<{ status: string; appointment: Appointment }> {
    return api.post('/healthcare/appointments', payload);
  },

  async updateAppointmentStatus(appointmentId: string, status: string): Promise<{ status: string; appointment_id: string; new_status: string }> {
    return api.patch(`/healthcare/appointments/${appointmentId}/status`, { status });
  },

  // 4. Inpatient Admissions & Bed Allocation
  async getAdmissions(status?: string, department?: string): Promise<{ status: string; total: number; admissions: Admission[] }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (department) params.append('department', department);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/admissions${query}`);
  },

  async createAdmission(payload: {
    patient_id: string;
    hospital_id?: string;
    department: string;
    room_bed: string;
    admission_type?: string;
    admitting_doctor_id: string;
    assigned_nurse_id?: string;
  }): Promise<{ status: string; admission: Admission }> {
    return api.post('/healthcare/admissions', payload);
  },

  async dischargeAdmission(admissionId: string): Promise<{ status: string; admission_id: string; discharged_at: string }> {
    return api.post(`/healthcare/admissions/${admissionId}/discharge`);
  },

  // 5. LIS Laboratory Workflow
  async getLabOrders(patientId?: string, status?: string): Promise<{ status: string; total: number; lab_orders: LabOrder[] }> {
    const params = new URLSearchParams();
    if (patientId) params.append('patient_id', patientId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/labs${query}`);
  },

  async createLabOrder(payload: {
    patient_id: string;
    test_name: string;
    category?: string;
    priority?: string;
    doctor_id: string;
    reference_range?: string;
  }): Promise<{ status: string; lab_order: LabOrder }> {
    return api.post('/healthcare/labs', payload);
  },

  async updateLabResult(
    labId: string,
    resultData: Record<string, any>,
    flaggedAbnormal: boolean,
    approvedBy?: string
  ): Promise<{ status: string; lab_id: string; completed_at: string }> {
    return api.patch(`/healthcare/labs/${labId}/result`, {
      result_data: resultData,
      flagged_abnormal: flaggedAbnormal,
      approved_by: approvedBy,
    });
  },

  // 6. Pharmacy & Pyxis Workflow
  async getPrescriptions(patientId?: string, status?: string): Promise<{ status: string; total: number; prescriptions: Prescription[] }> {
    const params = new URLSearchParams();
    if (patientId) params.append('patient_id', patientId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/prescriptions${query}`);
  },

  async createPrescription(payload: {
    patient_id: string;
    doctor_id: string;
    medication: string;
    dosage: string;
    frequency: string;
    duration: string;
    ddi_warning?: string;
  }): Promise<{ status: string; prescription: Prescription }> {
    return api.post('/healthcare/prescriptions', payload);
  },

  async dispensePrescription(prescriptionId: string, pharmacistId?: string): Promise<{ status: string; prescription_id: string; dispensed_at: string }> {
    return api.patch(`/healthcare/prescriptions/${prescriptionId}/dispense`, { pharmacist_id: pharmacistId });
  },

  // 7. Billing & TPA Claims
  async getBillingInvoices(patientId?: string, status?: string): Promise<{ status: string; total: number; invoices: BillingInvoice[] }> {
    const params = new URLSearchParams();
    if (patientId) params.append('patient_id', patientId);
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/billing${query}`);
  },

  async createBillingInvoice(payload: {
    patient_id: string;
    hospital_id?: string;
    total_amount: number;
    insurance_claim_amount: number;
    patient_payable: number;
    payment_method?: string;
    line_items?: Array<{ item: string; amount: number }>;
  }): Promise<{ status: string; invoice: BillingInvoice }> {
    return api.post('/healthcare/billing', payload);
  },

  async settleBillingInvoice(invoiceId: string, paymentMethod?: string): Promise<{ status: string; invoice_id: string; settled_at: string }> {
    return api.post(`/healthcare/billing/${invoiceId}/settle`, { payment_method: paymentMethod || 'CASHLESS_TPA' });
  },

  // 8. Emergency CAD & Paramedic Uplink
  async getEmergencyDispatches(status?: string): Promise<{ status: string; total: number; dispatches: EmergencyDispatch[] }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/healthcare/emergency/dispatches${query}`);
  },

  async createEmergencyDispatch(payload: {
    ambulance_id: string;
    paramedic_id: string;
    patient_id?: string;
    caller_name: string;
    emergency_type: string;
    triage_priority: string;
    origin_location: string;
    destination_hospital: string;
    green_corridor_active?: boolean;
    vitals?: Record<string, any>;
  }): Promise<{ status: string; dispatch: EmergencyDispatch }> {
    return api.post('/healthcare/emergency/dispatch', payload);
  },

  async updateEmergencyDispatch(
    dispatchId: string,
    updates: {
      status?: string;
      vitals?: Record<string, any>;
      arrived_scene_at?: string;
      arrived_hospital_at?: string;
      green_corridor_active?: boolean;
    }
  ): Promise<{ status: string; dispatch_id: string; updates: any }> {
    return api.patch(`/healthcare/emergency/dispatches/${dispatchId}`, updates);
  },

  // 9. Fleet Ambulances CAD
  async getAmbulances(): Promise<{ status: string; total: number; ambulances: AmbulanceCAD[] }> {
    return api.get('/healthcare/ambulances');
  },

  async updateAmbulanceStatus(
    ambulanceId: string,
    status: string,
    location?: string,
    etaMinutes?: number
  ): Promise<{ status: string; ambulance_id: string; mission_status: string }> {
    return api.patch(`/healthcare/ambulances/${ambulanceId}/status`, {
      status,
      location,
      eta_minutes: etaMinutes,
    });
  },

  // 10. Bedside IoMT Devices & Microsegmentation
  async getIoMTDevices(): Promise<{ status: string; total: number; devices: IoMTDevice[] }> {
    return api.get('/healthcare/iomt/devices');
  },

  async isolateIoMTDevice(
    deviceId: string,
    vlanId?: string,
    reason?: string
  ): Promise<{ status: string; device_id: string; quarantine_vlan: string }> {
    return api.post(`/healthcare/iomt/devices/${deviceId}/isolate`, {
      vlan_id: vlanId || 'QUARANTINE_VLAN_99',
      reason: reason || 'Bedside IoMT anomaly manual/automated isolation',
    });
  },

  async scanIoMTDevices(): Promise<{
    status: string;
    scan_timestamp: string;
    devices_scanned: number;
    anomalies_detected: number;
    devices: IoMTDevice[];
  }> {
    return api.get('/healthcare/iomt/scan');
  },

  // 11. Security Demo Simulation
  async simulateExfiltration(): Promise<any> {
    return api.post('/healthcare/simulate-exfiltration');
  },
};
