import { WorkflowDefinition } from '../types/workflow';

export const WORKFLOW_REGISTRY: Record<string, WorkflowDefinition> = {
  // ══════════════════════════════════════════════════════════════════
  // HEALTHCARE DOMAIN
  // ══════════════════════════════════════════════════════════════════
  patient: {
    roleId: 'patient',
    roleName: 'Patient (Self-Service)',
    domain: 'HEALTHCARE',
    department: 'Outpatient & Inpatient Portal',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Patient self-service portal for appointments, vitals, prescriptions, and bedside emergency communication.',
    q1_immediate: {
      headline: 'Upcoming Health Actions & Medication Reminders',
      tasks: [
        { id: 'PT-01', title: 'Cardiology Consultation with Dr. Sarah Chen', subtitle: 'Today at 10:30 AM (Room ICU-04)', urgency: 'HIGH', slaMinutes: 45, category: 'Consultation', actionLabel: 'Check In' },
        { id: 'PT-02', title: 'Medication Due: Aspirin 75mg & Metoprolol 25mg', subtitle: 'Post-breakfast dose pending', urgency: 'MEDIUM', slaMinutes: 120, category: 'Prescription', actionLabel: 'Mark Taken' },
        { id: 'PT-03', title: 'Discharge Summary Review', subtitle: 'Awaiting signature from attending physician', urgency: 'LOW', slaMinutes: 300, category: 'Administrative', actionLabel: 'View Draft' },
      ],
    },
    q2_information: {
      headline: 'My Clinical Profile & Telemetry Summary',
      metrics: [
        { label: 'Latest Heart Rate', value: '78 bpm', status: 'NORMAL', trend: 'Stable' },
        { label: 'Blood Pressure', value: '122/82', status: 'NORMAL', trend: 'Nominal' },
        { label: 'Active Prescriptions', value: '3 Rx', status: 'ACTIVE' },
        { label: 'Pending Lab Reports', value: '1 Ready', status: 'AVAILABLE' },
      ],
      keyContextList: [
        { label: 'Assigned Hospital', value: 'Manipal Central Hospital' },
        { label: 'Attending Clinician', value: 'Dr. Sarah Chen (Cardiology)' },
        { label: 'Room & Bed', value: 'ICU Stepdown Bed 04' },
        { label: 'Allergies', value: 'Penicillin (Severe Rash)' },
      ],
    },
    q3_actions: {
      headline: 'Patient Self-Service Actions',
      actions: [
        { id: 'P_CALL', label: 'Call Bedside Nurse', description: 'Triggers priority chime at nursing station', icon: 'Bell', variant: 'danger', confirmMessage: 'Call nursing station immediately?' },
        { id: 'P_REFILL', label: 'Request Rx Refill', description: 'Submit refill request to hospital pharmacy', icon: 'Pill', variant: 'primary' },
        { id: 'P_PAY', label: 'Pay Hospital Bill (UPI)', description: 'Settle outstanding balance via instant UPI gateway', icon: 'CreditCard', variant: 'success' },
        { id: 'P_EXPORT', label: 'Download Health Records', description: 'Download cryptographically signed PDF summary', icon: 'Download', variant: 'outline' },
      ],
    },
    q4_approvals: {
      headline: 'Pending Consents & Releases',
      items: [
        { id: 'APP-P-01', title: 'Consent for Echocardiogram Diagnostic Protocol', submittedBy: 'Cardiology Dept', submittedAt: 'Today 08:00', reason: 'Routine post-stent cardiac evaluation', approverRole: 'Patient / Guardian', status: 'PENDING' },
        { id: 'APP-P-02', title: 'Release of Records to Apollo Insurance TPA', submittedBy: 'Billing Desk', submittedAt: 'Yesterday', reason: 'Cashless claim pre-authorization', approverRole: 'Patient', status: 'PENDING' },
      ],
    },
    q5_escalation: {
      headline: 'Emergency & Urgent Assistance',
      procedures: [
        { name: 'Acute Chest Pain / Respiratory Distress', trigger: 'Sudden shortness of breath or radiating chest pressure', sopSteps: ['Press emergency red call button above bed', 'Stay seated in upright position', 'Emergency crash team dispatches within 60 seconds'], failsafeAction: 'Trigger Code Blue Bedside Alarm', escalationContact: 'ICU Rapid Response Desk: Ext 108' },
      ],
    },
  },

  doctor: {
    roleId: 'doctor',
    roleName: 'Dr. Sarah Chen (Attending Cardiologist)',
    domain: 'HEALTHCARE',
    department: 'Cardiology & Cardiovascular ICU',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Clinical diagnosis, bedside inpatient rounds, EHR vitals evaluation, and prescription signing within departmental BOLA boundaries.',
    q1_immediate: {
      headline: 'Immediate Inpatient Rounds & Critical Triage',
      tasks: [
        { id: 'DOC-01', title: 'Critically Elevated Troponin: Ramesh Patel (ICU-04)', subtitle: 'HR 118 bpm, SpO2 94% — Review ECG rhythm strip immediately', urgency: 'CRITICAL', slaMinutes: 15, category: 'Critical Alert', actionLabel: 'Review Vitals' },
        { id: 'DOC-02', title: 'Post-Op Stent Evaluation: Sunita Sharma (Bed 12)', subtitle: 'Routine day-2 ultrasound Doppler check', urgency: 'HIGH', slaMinutes: 60, category: 'Clinical Round', actionLabel: 'Open Chart' },
        { id: 'DOC-03', title: 'Discharge Approval: Anand Kumar (Bed 08)', subtitle: 'Cardiac rehab cleared, final medication sign-off needed', urgency: 'MEDIUM', slaMinutes: 180, category: 'Discharge', actionLabel: 'Sign Summary' },
      ],
    },
    q2_information: {
      headline: 'Cardiology Inpatient Roster & Bed Telemetry',
      metrics: [
        { label: 'Assigned Patients', value: '8 Inpatients', status: 'NORMAL' },
        { label: 'Critical ICU Vitals', value: '1 Patient Flagged', status: 'CRITICAL', trend: 'Tachycardia' },
        { label: 'Lab Reports Awaiting Sign-off', value: '4 Pending', status: 'WARNING' },
        { label: 'BOLA Scope', value: 'Cardiology Only', status: 'SECURED' },
      ],
      keyContextList: [
        { label: 'Primary Ward', value: 'Cardiovascular Care Unit (CCU)' },
        { label: 'On-Call Fellow', value: 'Dr. Vikram Rao' },
        { label: 'Echo Lab Status', value: 'Operational (Queue: 2)' },
        { label: 'Department BOLA', value: 'RESTRICTED (Oncology records locked)' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Clinical Actions',
      actions: [
        { id: 'DOC_NOTE', label: 'Write Clinical Note', description: 'Log bedside observation and treatment changes', icon: 'FileText', variant: 'primary', requiredCapability: 'can_edit_patient_records' },
        { id: 'DOC_RX', label: 'Modify Prescription', description: 'Update dosages or add cardiac medications', icon: 'Pill', variant: 'success', requiredCapability: 'can_edit_patient_records' },
        { id: 'DOC_LAB', label: 'Stat Lab Order', description: 'Order emergency blood gas and cardiac enzymes', icon: 'Activity', variant: 'warning', requiredCapability: 'can_edit_patient_records' },
        { id: 'DOC_DISCHARGE', label: 'Authorize Discharge', description: 'Sign digital medical discharge clearance', icon: 'CheckSquare', variant: 'outline', requiredCapability: 'can_edit_patient_records' },
      ],
    },
    q4_approvals: {
      headline: 'Dual-Control Clinical Approvals',
      items: [
        { id: 'APP-DOC-01', title: 'High-Dose Morphine Infusion for Ramesh Patel', submittedBy: 'Nurse Priya', submittedAt: '10 mins ago', reason: 'Severe refractory post-infarct angina', approverRole: 'Chief of Medicine Co-Sign', status: 'PENDING', riskScore: 82 },
        { id: 'APP-DOC-02', title: 'Off-Label Anti-Arrhythmic Protocol', submittedBy: 'Dr. Vikram Rao', submittedAt: '1 hr ago', reason: 'Amiodarone unresponsive VT episode', approverRole: 'Dr. Sarah Chen', status: 'PENDING', riskScore: 74 },
      ],
    },
    q5_escalation: {
      headline: 'Emergency Clinical Escalation Protocols',
      procedures: [
        { name: 'Ventricular Fibrillation / Cardiac Arrest (Code Blue)', trigger: 'Sudden loss of pulse or sustained ventricular arrhythmia', sopSteps: ['Initiate immediate CPR compressions', 'Activate Code Blue button', 'Crash cart defibrillator armed to 200J biphasic'], failsafeAction: 'Broadcast Code Blue ICU-04 to Pan-Hospital Audio', escalationContact: 'Crash Team Lead: Ext 2222' },
        { name: 'Emergency Surgical Bypass Divert', trigger: 'Failed catheterization with active hemodynamic collapse', sopSteps: ['Notify OR Suite 3 (Cardiothoracic)', 'Prepare 4 units O-Negative blood', 'Emergency perfusionist standby'], failsafeAction: 'Priority OR Bypass Clearance', escalationContact: 'OR Head: Ext 3301' },
      ],
    },
  },

  nurse: {
    roleId: 'nurse',
    roleName: 'Staff Nurse (Cardiology & ICU)',
    domain: 'HEALTHCARE',
    department: 'Inpatient Nursing Station',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Bedside patient vitals recording, IV medication administration, IoMT telemetry monitoring, and doctor escalation.',
    q1_immediate: {
      headline: 'Nursing Medication Schedule & Triage Queue',
      tasks: [
        { id: 'NUR-01', title: 'Administer IV Heparin Drip: Bed ICU-04', subtitle: 'Rate 1,200 units/hr — Verify pump calibration', urgency: 'CRITICAL', slaMinutes: 10, category: 'Medication', actionLabel: 'Confirm Dose' },
        { id: 'NUR-02', title: 'Q2H Vitals Check: Bed 12 (Sunita Sharma)', subtitle: 'Record BP, SpO2, and urine output', urgency: 'HIGH', slaMinutes: 30, category: 'Vitals', actionLabel: 'Record Vitals' },
        { id: 'NUR-03', title: 'Post-Op Wound Dressing Change: Bed 09', subtitle: 'Clean and inspect femoral puncture site', urgency: 'MEDIUM', slaMinutes: 90, category: 'Wound Care', actionLabel: 'Complete' },
      ],
    },
    q2_information: {
      headline: 'Ward Occupancy & Bedside Sensor Feeds',
      metrics: [
        { label: 'Assigned Beds', value: '4 Beds', status: 'ACTIVE' },
        { label: 'Active IV Pumps', value: '6 Alaris', status: 'NORMAL' },
        { label: 'Bedside Call Chimes', value: '0 Active', status: 'NOMINAL' },
        { label: 'IoMT Cyber Health', value: '98% Clean', status: 'HEALTHY' },
      ],
      keyContextList: [
        { label: 'Shift', value: 'Day Shift (07:00 - 19:00)' },
        { label: 'Charge Nurse', value: 'Sister Mary Thomas' },
        { label: 'Covering Doctor', value: 'Dr. Sarah Chen' },
        { label: 'Code Blue Cart', value: 'Checked & Armed (07:15)' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Nursing Actions',
      actions: [
        { id: 'N_LOG_VITALS', label: 'Log Vitals Telemetry', description: 'Record temperature, pulse, respiration, and SpO2', icon: 'Activity', variant: 'primary', requiredCapability: 'can_view_patient_records' },
        { id: 'N_GIVE_MED', label: 'Confirm Med Administration', description: 'Barcode scan patient wristband and medicine packet', icon: 'CheckCircle', variant: 'success' },
        { id: 'N_PUMP_CHECK', label: 'IoMT Pump Recalibrate', description: 'Verify infusion flow rate against physician order', icon: 'Sliders', variant: 'warning' },
        { id: 'N_PAGING', label: 'Page Attending Doctor', description: 'Direct priority page to Dr. Sarah Chen', icon: 'Phone', variant: 'danger' },
      ],
    },
    q4_approvals: {
      headline: 'Medication Dual-Sign-Offs',
      items: [
        { id: 'APP-NUR-01', title: 'Insulin Glargine 18 Units Dual-Check', submittedBy: 'Self', submittedAt: '15 mins ago', reason: 'High-alert medication protocol', approverRole: 'Second Registered Nurse', status: 'PENDING' },
      ],
    },
    q5_escalation: {
      headline: 'Emergency Deterioration Protocols',
      procedures: [
        { name: 'Unresponsive Patient / Severe Desaturation (SpO2 < 85%)', trigger: 'Patient unresponsive to voice, blue lips, or monitor alarm', sopSteps: ['Hit bedside emergency alarm immediately', 'Attach high-flow 15L non-rebreather oxygen mask', 'Begin bag-valve mask ventilation if breathing stops'], failsafeAction: 'Sound Ward Rapid Response Horn', escalationContact: 'ICU Resuscitation Team: Ext 108' },
      ],
    },
  },

  ambulance_driver: {
    roleId: 'ambulance_driver',
    roleName: 'Ambulance Driver (Unit CAD-04)',
    domain: 'HEALTHCARE',
    department: 'Mobile Emergency Medical Services',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'High-speed emergency medical navigation, patient transit, and 1-tap Green Corridor STIG traffic pre-emption.',
    q1_immediate: {
      headline: 'CURRENT ACTIVE DISPATCH MISSION',
      tasks: [
        { id: 'AMB-DISPATCH-01', title: 'DISPATCH: Severe Cardiac Trauma (Patient Ramesh Patel)', subtitle: 'Location: 44 Outer Ring Road, Bangalore ➔ Manipal Central Hospital', urgency: 'CRITICAL', slaMinutes: 8, category: 'Emergency CAD', actionLabel: 'VIEW ROUTE' },
      ],
    },
    q2_information: {
      headline: 'Route Telemetry & Destination Hospital Status',
      metrics: [
        { label: 'Estimated Arrival (ETA)', value: '6 Mins', status: 'CRITICAL' },
        { label: 'Distance Remaining', value: '4.2 km', status: 'ACTIVE' },
        { label: 'Hospital ER Status', value: 'Trauma Bay 2 Ready', status: 'NORMAL' },
        { label: 'Green Corridor Pre-emption', value: 'GRANTED (SIG 1-3)', status: 'HEALTHY' },
      ],
      keyContextList: [
        { label: 'Vehicle Call Sign', value: 'CAD-04 (Advanced Life Support)' },
        { label: 'Vehicle Number', value: 'KA-01-EA-1084' },
        { label: 'On-Board Paramedic', value: 'Paramedic Anil Rao' },
        { label: 'Destination ER', value: 'Manipal Central Trauma Desk' },
      ],
    },
    q3_actions: {
      headline: 'High-Priority 1-Tap Driver Controls',
      actions: [
        { id: 'AMB_CORRIDOR', label: '⚡ REQUEST GREEN CORRIDOR PRE-EMPTION', description: 'Pre-empts municipal traffic signals to continuous green along route', icon: 'Zap', variant: 'danger', requiredCapability: 'can_dispatch_ambulances' },
        { id: 'AMB_STEP_SCENE', label: 'ARRIVED AT SCENE', description: 'Notify dispatch that crew has reached patient location', icon: 'MapPin', variant: 'primary', requiredCapability: 'can_dispatch_ambulances' },
        { id: 'AMB_STEP_HOSPITAL', label: 'PATIENT LOADED ➔ HEADING TO ER', description: 'En route to hospital trauma bay with sirens active', icon: 'HeartPulse', variant: 'warning', requiredCapability: 'can_dispatch_ambulances' },
        { id: 'AMB_COMPLETE', label: 'ARRIVED AT HOSPITAL / HANDOVER', description: 'Patient transferred to ER trauma resuscitation bay', icon: 'CheckSquare', variant: 'success', requiredCapability: 'can_dispatch_ambulances' },
      ],
    },
    q4_approvals: {
      headline: 'Automatic Clearance & Permissions',
      items: [
        { id: 'APP-AMB-01', title: 'Expressway Toll Free Bypass Pre-Authorization', submittedBy: 'Smart City Dispatch', submittedAt: 'Automatic', reason: 'Emergency Code 1 Priority', approverRole: 'FASTag Automated Bypass', status: 'APPROVED' },
      ],
    },
    q5_escalation: {
      headline: 'Critical Route Obstruction / Breakdown Protocol',
      procedures: [
        { name: 'Corridor Road Blockage / Severe Gridlock', trigger: 'Vehicle stopped in standstill traffic or accident blocking all lanes', sopSteps: ['Tap Emergency Corridor Override button', 'Notify Dispatch to reroute via Hospital Service Flyover', 'Dispatch police escort vehicle to clear junction'], failsafeAction: 'Activate Emergency Siren Police Escort Pre-emption', escalationContact: 'Traffic Control Room: Ext 9999' },
        { name: 'Vehicle Mechanical Breakdown', trigger: 'Engine stall or tire blowout during active patient transit', sopSteps: ['Pull into safest shoulder lane', 'Keep on-board patient life support running on inverter', 'Dispatch CAD-02 immediately for roadside patient transfer'], failsafeAction: 'Auto-Dispatch Backup Unit CAD-02', escalationContact: 'Fleet Supervisor: Ext 1082' },
      ],
    },
  },

  paramedic: {
    roleId: 'paramedic',
    roleName: 'Paramedic (Mobile Emergency Crew)',
    domain: 'HEALTHCARE',
    department: 'Pre-Hospital Trauma Care',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'On-scene patient stabilization, mobile defibrillation, telemedicine vitals relay to receiving trauma surgeon.',
    q1_immediate: {
      headline: 'On-Board Patient Telemetry & Resuscitation',
      tasks: [
        { id: 'PARA-01', title: 'Stabilize Patient: Oxygen Saturation 91%', subtitle: 'Attach 100% Bag Valve Mask, initiate IV normal saline 500ml', urgency: 'CRITICAL', slaMinutes: 5, category: 'Resuscitation', actionLabel: 'Log Intervention' },
        { id: 'PARA-02', title: 'Transmit 12-Lead ECG to Manipal ER', subtitle: 'ST Elevation detected in V1-V4 (Anterior STEMI)', urgency: 'CRITICAL', slaMinutes: 3, category: 'Telemedicine', actionLabel: 'Transmit ECG' },
      ],
    },
    q2_information: {
      headline: 'Mobile Patient Monitor Live Stream',
      metrics: [
        { label: 'Heart Rate', value: '124 bpm', status: 'CRITICAL', trend: 'Sinus Tachycardia' },
        { label: 'Blood Pressure', value: '92/58', status: 'WARNING', trend: 'Hypotensive' },
        { label: 'SpO2 Saturation', value: '93%', status: 'WARNING', trend: 'Improving on O2' },
        { label: 'GCS Score', value: '13 / 15', status: 'NORMAL', trend: 'Conscious' },
      ],
      keyContextList: [
        { label: 'Patient Name', value: 'Ramesh Patel (58M)' },
        { label: 'Receiving Trauma Surgeon', value: 'Dr. Anand Mehta' },
        { label: 'Defibrillator Armed', value: 'Zoll X-Series (Pads Attached)' },
        { label: 'Telemetry Relay', value: '5G Encrypted Uplink Connected' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Paramedic Interventions',
      actions: [
        { id: 'P_RELAY_ECG', label: 'Transmit ECG to Trauma Bay', description: 'Stream full 12-lead strip to receiving cath lab', icon: 'Radio', variant: 'primary', requiredCapability: 'can_edit_patient_records' },
        { id: 'P_GIVE_MED', label: 'Administer Aspirin & Clopidogrel', description: 'Dual antiplatelet protocol for acute STEMI', icon: 'Pill', variant: 'warning', requiredCapability: 'can_edit_patient_records' },
        { id: 'P_RADIO_ER', label: 'Radio Trauma Call Ahead', description: 'Voice patch direct to receiving ER charge nurse', icon: 'Mic', variant: 'danger' },
      ],
    },
    q4_approvals: {
      headline: 'Online Medical Direction Orders',
      items: [
        { id: 'APP-PARA-01', title: 'Emergency Pre-Hospital Thrombolysis (Tenecteplase)', submittedBy: 'Self', submittedAt: '3 mins ago', reason: 'Prolonged transit time > 30 mins due to weather', approverRole: 'ER Medical Director', status: 'PENDING', riskScore: 88 },
      ],
    },
    q5_escalation: {
      headline: 'In-Transit Deterioration Protocols',
      procedures: [
        { name: 'Sudden In-Transit Cardiac Arrest', trigger: 'Loss of pulse, rhythm changes to V-Fib on mobile monitor', sopSteps: ['Shout "STOP AMBULANCE" to driver to pull over for compressions', 'Deliver immediate 200J unsynchronized shock', 'Resume CPR 30:2 while driver resumes high-priority emergency transit'], failsafeAction: 'Declare In-Transit Code Blue', escalationContact: 'Receiving ER Cath Lab: Ext 1081' },
      ],
    },
  },

  reception: {
    roleId: 'reception',
    roleName: 'Hospital Reception & Intake Staff',
    domain: 'HEALTHCARE',
    department: 'Patient Admissions Desk',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Patient registration, insurance eligibility check, department triage routing, and appointment scheduling.',
    q1_immediate: {
      headline: 'Patient Intake Queue & Walk-In Admissions',
      tasks: [
        { id: 'REC-01', title: 'Admit Emergency Arrival: Ramesh Patel', subtitle: 'Incoming via CAD-04 (Severe STEMI) — Assign trauma bay', urgency: 'CRITICAL', slaMinutes: 5, category: 'Emergency', actionLabel: 'Fast Intake' },
        { id: 'REC-02', title: 'Insurance Verification: Priya Nair', subtitle: 'Verify cashless eligibility with Star Health TPA', urgency: 'HIGH', slaMinutes: 20, category: 'Insurance', actionLabel: 'Verify TPA' },
        { id: 'REC-03', title: 'Outpatient Registration: 4 Patients Waiting', subtitle: 'Queue wait time 8 mins (Cardiology Clinic)', urgency: 'MEDIUM', slaMinutes: 30, category: 'Outpatient', actionLabel: 'Next Token' },
      ],
    },
    q2_information: {
      headline: 'Hospital Capacity & Inpatient Bed Status',
      metrics: [
        { label: 'Available ICU Beds', value: '3 Beds', status: 'WARNING' },
        { label: 'General Ward Beds', value: '18 Beds', status: 'HEALTHY' },
        { label: 'Emergency Bays', value: '2 Available', status: 'NORMAL' },
        { label: 'Today Admissions', value: '34 Patients', status: 'ACTIVE' },
      ],
      keyContextList: [
        { label: 'Duty Desk', value: 'Main Gate A Registration' },
        { label: 'Triage Nurse', value: 'Sister Deepa' },
        { label: 'Hospital ER Status', value: 'OPEN (No diversions)' },
        { label: 'Ayushman Bharat Desk', value: 'Active Counter 3' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Reception Actions',
      actions: [
        { id: 'REC_REGISTER', label: 'Register New Patient', description: 'Create verified EHR identity record and issue barcode wristband', icon: 'UserPlus', variant: 'primary', requiredCapability: 'can_view_patient_records' },
        { id: 'REC_ASSIGN_BED', label: 'Assign Ward Bed', description: 'Allocate available bed in Cardiology or Stepdown', icon: 'Home', variant: 'success' },
        { id: 'REC_ISSUE_PASS', label: 'Issue Visitor Pass', description: 'Issue 24-hr visitor badge with security NFC token', icon: 'Key', variant: 'outline' },
      ],
    },
    q4_approvals: {
      headline: 'Bed Escalation Approvals',
      items: [
        { id: 'APP-REC-01', title: 'Emergency ICU Bed Override Request', submittedBy: 'Self', submittedAt: '10 mins ago', reason: 'Direct STEMI trauma admission', approverRole: 'Hospital Medical Superintendent', status: 'APPROVED' },
      ],
    },
    q5_escalation: {
      headline: 'Mass Casualty / Surge Protocol',
      procedures: [
        { name: 'Hospital Full Capacity / Mass Casualty Surge', trigger: 'Zero remaining emergency bays or incoming mass casualty notice', sopSteps: ['Notify Chief Medical Officer to initiate code yellow surge', 'Convert Post-Anesthesia Care Unit (PACU) into overflow ICU', 'Activate citywide CAD ER diversion to neighboring Apollo Hospital'], failsafeAction: 'Declare Hospital Code Yellow Diversion', escalationContact: 'Chief of Medical Operations: Ext 5000' },
      ],
    },
  },

  pharmacist: {
    roleId: 'pharmacist',
    roleName: 'Hospital Inpatient Pharmacist',
    domain: 'HEALTHCARE',
    department: 'Central Hospital Pharmacy & Vault',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Prescription dispensing, drug-drug interaction screening, narcotic inventory custody, and IV admixture verification.',
    q1_immediate: {
      headline: 'Urgent Stat Medication Orders & Drug Dispensing Queue',
      tasks: [
        { id: 'PHARM-01', title: 'STAT Order: Alteplase (tPA) 50mg for Stroke Bay 1', subtitle: 'Ischemic stroke window < 3 hrs — Dispense within 10 mins', urgency: 'CRITICAL', slaMinutes: 10, category: 'STAT Med', actionLabel: 'Dispense' },
        { id: 'PHARM-02', title: 'Drug Interaction Warning: Patient Ramesh Patel', subtitle: 'Amiodarone + Warfarin potential interaction flagged by AI', urgency: 'HIGH', slaMinutes: 25, category: 'Safety Flag', actionLabel: 'Review Flag' },
        { id: 'PHARM-03', title: 'Daily Controlled Narcotics Vault Audit', subtitle: 'Fentanyl and Midazolam physical count verification', urgency: 'MEDIUM', slaMinutes: 120, category: 'Compliance', actionLabel: 'Audit Vault' },
      ],
    },
    q2_information: {
      headline: 'Pharmacy Vault Telemetry & Stock Levels',
      metrics: [
        { label: 'Pending STAT Orders', value: '1 Order', status: 'CRITICAL' },
        { label: 'Scheduled Doses', value: '142 Today', status: 'NORMAL' },
        { label: 'Narcotics Safe', value: 'LOCKED (Dual Key)', status: 'SECURED' },
        { label: 'Cold Chain Fridge', value: '3.8°C (Nominal)', status: 'HEALTHY' },
      ],
      keyContextList: [
        { label: 'Pharmacy Lead', value: 'Pharmacist Sneha Roy' },
        { label: 'Vault Status', value: 'Biometric Access Active' },
        { label: 'Automated Dispenser', value: 'Pyxis MedStation Online' },
        { label: 'Controlled Substance License', value: 'Verified Schedule X' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Pharmacy Actions',
      actions: [
        { id: 'PH_DISPENSE', label: 'Verify & Dispense STAT Order', description: 'Cross-check dose against patient weight and dispense to nurse', icon: 'Pill', variant: 'danger' },
        { id: 'PH_OVERRIDE_INTERACTION', label: 'Pharmacist Interaction Clear', description: 'Sign off on mild drug interaction after consulting doctor', icon: 'CheckCircle', variant: 'warning' },
        { id: 'PH_VAULT_OPEN', label: 'Open Schedule X Vault', description: 'Biometric authorization to access high-potency analgesics', icon: 'Lock', variant: 'primary' },
      ],
    },
    q4_approvals: {
      headline: 'Controlled Substance Approvals',
      items: [
        { id: 'APP-PH-01', title: 'Emergency Release: Remifentanil 2mg Ampoules', submittedBy: 'Surgical ICU Charge Nurse', submittedAt: '12 mins ago', reason: 'Open heart surgery emergency analgesia', approverRole: 'Chief Pharmacist', status: 'PENDING', riskScore: 89 },
      ],
    },
    q5_escalation: {
      headline: 'Cold Chain & Tamper Protocols',
      procedures: [
        { name: 'Refrigerated Vaccine / Biologic Temp Breach (> 8°C)', trigger: 'Pharmacy cold fridge sensor alarms temperature elevation', sopSteps: ['Immediately transfer biologics to backup emergency cooler', 'Inspect generator backup circuit', 'Quarantine medications exposed for > 30 minutes'], failsafeAction: 'Auto-Switch Backup Cold Storage', escalationContact: 'Hospital Biomedical Engineering: Ext 4004' },
      ],
    },
  },

  // ══════════════════════════════════════════════════════════════════
  // TRAFFIC DOMAIN
  // ══════════════════════════════════════════════════════════════════
  traffic_operator: {
    roleId: 'traffic_operator',
    roleName: 'STIG Corridor Traffic Operator',
    domain: 'TRAFFIC',
    department: 'Municipal Intelligent Mobility Center',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Adaptive signal cycle control, emergency green corridors, expressway tollgate bypass, and ANPR camera surveillance.',
    q1_immediate: {
      headline: 'Active Congestion Alarms & Signal Anomalies',
      tasks: [
        { id: 'TR-01', title: 'Severe Congestion Spike: Hebbal Flyover North (Road 02)', subtitle: 'Current speed 14 km/h (Nominal 60 km/h) — Queue length 1.8 km', urgency: 'CRITICAL', slaMinutes: 5, category: 'Congestion', actionLabel: 'Override Signal' },
        { id: 'TR-02', title: 'Emergency Green Corridor Request: Ambulance CAD-04', subtitle: 'Corridor MG Road ➔ Hospital Blvd (Signals SIG-01 to SIG-03)', urgency: 'CRITICAL', slaMinutes: 3, category: 'Green Corridor', actionLabel: 'Pre-Empt Grid' },
        { id: 'TR-03', title: 'Loop Sensor Telemetry Failure: Signal SIG-04', subtitle: 'Inductive loop detector #4 reporting stuck-on state', urgency: 'MEDIUM', slaMinutes: 60, category: 'Hardware', actionLabel: 'Dispatch Tech' },
      ],
    },
    q2_information: {
      headline: 'Bangalore-Hyderabad Smart Corridor Telemetry',
      metrics: [
        { label: 'Corridor Average Speed', value: '38.4 km/h', status: 'WARNING', trend: 'Down 18%' },
        { label: 'Active Connected Signals', value: '6 / 6 Online', status: 'HEALTHY' },
        { label: 'CCTV Surveillance', value: '4 Feeds Active', status: 'NORMAL' },
        { label: 'FASTag Anomaly Holds', value: '1 Suspicious', status: 'CRITICAL' },
      ],
      keyContextList: [
        { label: 'Current Corridor Mode', value: 'STIG Adaptive Dynamic Cycling' },
        { label: 'Duty Operator', value: 'Inspector Rajesh Kumar' },
        { label: 'Emergency Corridors Active', value: '1 (CAD-01 Pre-empted)' },
        { label: 'Weather Impact', value: 'Dry Road Surface (Visibility 8km)' },
      ],
    },
    q3_actions: {
      headline: 'Direct Operational Control Actions',
      actions: [
        { id: 'TR_GREEN_ALL', label: 'Pre-Empt Green Corridor', description: 'Grant priority green wave for emergency response vehicles', icon: 'Zap', variant: 'danger', requiredCapability: 'can_override_signals' },
        { id: 'TR_FORCE_GREEN', label: 'Force Green Phase (SIG-01)', description: 'Extend green cycle duration by 90s to flush Hebbal queue', icon: 'Sliders', variant: 'success', requiredCapability: 'can_override_signals' },
        { id: 'TR_FAILSAFE_AMBER', label: 'Signal Failsafe Flashing Amber', description: 'Drop intersection to caution mode during sensor glitch', icon: 'AlertTriangle', variant: 'warning', requiredCapability: 'can_override_signals' },
        { id: 'TR_FASTAG_BYPASS', label: 'Emergency Toll Gantry Lift', description: 'Bypass toll barrier for civil defense convoy', icon: 'CheckSquare', variant: 'outline', requiredCapability: 'can_override_signals' },
      ],
    },
    q4_approvals: {
      headline: 'Supervisor Override Sign-Offs',
      items: [
        { id: 'APP-TR-01', title: 'Permanent Cycle Duration Change (Hebbal Junction)', submittedBy: 'Traffic Operator', submittedAt: '30 mins ago', reason: 'Permanent 120s morning cycle adjustment', approverRole: 'Traffic Police Commissioner', status: 'PENDING', riskScore: 65 },
      ],
    },
    q5_escalation: {
      headline: 'Corridor Gridlock & SCADA Tamper Protocols',
      procedures: [
        { name: 'Hostile Signal Tamper / SCADA Cyber Manipulation', trigger: 'Unauthorized green-split packet injected from untrusted IP', sopSteps: ['Drop entire corridor to isolated analog failsafe red', 'Revoke remote operator token immediately', 'Dispatch physical traffic police constables to take manual control'], failsafeAction: 'Trigger Autonomous OT Network Micro-Isolation', escalationContact: 'Cyber SOC Command: Ext 1001' },
      ],
    },
  },

  citizen: {
    roleId: 'citizen',
    roleName: 'Citizen / Commuter',
    domain: 'TRAFFIC',
    department: 'Smart City Public Portal',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Public commuter self-service for route congestion, road hazard reporting, and civil safety alerts.',
    q1_immediate: {
      headline: 'Live Commute Advisories & Route Alerts',
      tasks: [
        { id: 'CIT-01', title: 'Hebbal Flyover Congestion Advisory', subtitle: 'Heavy traffic delay: +25 mins. Alternate route: Bellary Service Road', urgency: 'HIGH', category: 'Traffic Advisory' },
        { id: 'CIT-02', title: 'Scheduled Metro Maintenance Tonight', subtitle: 'Purple Line services terminate at 22:30 for track renewal', urgency: 'LOW', category: 'Transit' },
      ],
    },
    q2_information: {
      headline: 'Corridor Travel Times & Hazard Status',
      metrics: [
        { label: 'Airport Express Route', value: '42 mins (Normal)', status: 'HEALTHY' },
        { label: 'Outer Ring Road Route', value: '68 mins (+24m)', status: 'WARNING' },
        { label: 'Active City Weather', value: '28°C / Clear', status: 'NORMAL' },
        { label: 'Emergency Advisories', value: '0 Active', status: 'HEALTHY' },
      ],
      keyContextList: [
        { label: 'Saved Daily Commute', value: 'Indiranagar ➔ Electronic City' },
        { label: 'Preferred Mode', value: 'Car / Metro Hybrid' },
        { label: 'FASTag Balance', value: '₹1,240 (Active)' },
      ],
    },
    q3_actions: {
      headline: 'Citizen Reporting Actions',
      actions: [
        { id: 'CIT_REPORT_HAZARD', label: 'Report Road Hazard / Pothole', description: 'Submit geotagged photo of road debris or accident', icon: 'Camera', variant: 'warning' },
        { id: 'CIT_BROKEN_SIGNAL', label: 'Report Defective Traffic Light', description: 'Alert municipal traffic engineers to signal failure', icon: 'AlertTriangle', variant: 'primary' },
        { id: 'CIT_SOS', label: 'Civil SOS Emergency (112)', description: 'Direct emergency link to Bangalore Police Control', icon: 'Phone', variant: 'danger' },
      ],
    },
    q4_approvals: {
      headline: 'Citizen Permit Applications',
      items: [
        { id: 'APP-CIT-01', title: 'Residential Parking Permit Renewal', submittedBy: 'Self', submittedAt: '2 days ago', reason: 'Zone B Resident Permit 2026', approverRole: 'Transport Authority', status: 'PENDING' },
      ],
    },
    q5_escalation: {
      headline: 'Citizen Safety & Roadside Assistance',
      procedures: [
        { name: 'Vehicle Breakdown on Expressway', trigger: 'Car stalled in live traffic lane or hard shoulder', sopSteps: ['Turn on hazard lights immediately', 'Exit vehicle and stand behind metal safety barrier', 'Dial Highway Patrol assistance from app'], failsafeAction: 'Auto-Dispatch Highway Patrol Recovery Van', escalationContact: 'Expressway Patrol: 1033' },
      ],
    },
  },

  // ══════════════════════════════════════════════════════════════════
  // FINANCE DOMAIN
  // ══════════════════════════════════════════════════════════════════
  fraud_analyst: {
    roleId: 'fraud_analyst',
    roleName: 'Fraud Analyst (Fintech & Treasury)',
    domain: 'FINANCE',
    department: 'Financial Crime & Fraud Triage Unit',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Real-time pre-settlement wire screening, money-mule syndicate tracking, escrow hold enforcement, and SAR filing.',
    q1_immediate: {
      headline: 'High-Velocity Fraud Alarms & Pre-Settlement Holds',
      tasks: [
        { id: 'FRD-01', title: 'CRITICAL: ₹4.5M SWIFT Wire from Municipal Water SCADA', subtitle: 'Recipient: Brand-new offshore mule wallet in Moscow via TOR Exit — ML Score: 94%', urgency: 'CRITICAL', slaMinutes: 5, category: 'Account Takeover', actionLabel: 'Inspect Wire' },
        { id: 'FRD-02', title: 'UPI Velocity Anomaly: Syndicate Ring #AML-081', subtitle: '48 micro-transactions (₹9,990 each) smurfed in 12 minutes across 6 mule accounts', urgency: 'HIGH', slaMinutes: 20, category: 'Smurfing', actionLabel: 'Freeze Ring' },
        { id: 'FRD-03', title: 'Credential Stuffing Wave on Retail Banking API', subtitle: '1,420 failed logins from Ukrainian IP subnet targeting executive accounts', urgency: 'HIGH', slaMinutes: 45, category: 'Credential Stuffing', actionLabel: 'Block Subnet' },
      ],
    },
    q2_information: {
      headline: 'Live Fraud Scoring & Money-Mule Graph Metrics',
      metrics: [
        { label: 'Active Escrow Holds', value: '₹4.50M Held', status: 'CRITICAL' },
        { label: 'Syndicate Clusters', value: '1 Active Ring', status: 'WARNING' },
        { label: 'ML Anomaly Precision', value: '98.4%', status: 'HEALTHY' },
        { label: 'Frozen Mule Accounts', value: '3 Wallets', status: 'SECURED' },
      ],
      keyContextList: [
        { label: 'Duty Investigator', value: 'Senior Analyst Maya Sen' },
        { label: 'Active Ring Name', value: 'DarkMule Syndicate #081' },
        { label: 'Escrow Account', value: 'Reserve Bank Escrow Pool' },
        { label: 'Sanctions List Match', value: 'OFAC SDN Check: Clean' },
      ],
    },
    q3_actions: {
      headline: 'Authorized Financial Defense Controls',
      actions: [
        { id: 'FRD_HOLD', label: 'Enforce Pre-Settlement Escrow Hold', description: 'Freeze funds before settlement leaves RTGS/SWIFT gateway', icon: 'Lock', variant: 'danger', requiredCapability: 'can_freeze_accounts' },
        { id: 'FRD_FREEZE_MULE', label: 'Quarantine Money-Mule Cluster', description: 'Lock all downstream aggregator wallets in syndicate ring', icon: 'ShieldAlert', variant: 'warning', requiredCapability: 'can_freeze_accounts' },
        { id: 'FRD_FILE_SAR', label: 'File Suspicious Activity Report (SAR)', description: 'Generate regulatory audit filing for Financial Intelligence Unit (FIU)', icon: 'FileText', variant: 'primary', requiredCapability: 'can_freeze_accounts' },
        { id: 'FRD_RELEASE', label: 'Release Verified Safe Transaction', description: 'Clear escrow hold after two-factor biometric verification', icon: 'CheckCircle', variant: 'success', requiredCapability: 'can_freeze_accounts' },
      ],
    },
    q4_approvals: {
      headline: 'Escrow Release Dual-Authorizations',
      items: [
        { id: 'APP-FRD-01', title: 'Release of ₹4.5M Municipal Water SCADA Transfer', submittedBy: 'Customer Representative', submittedAt: '15 mins ago', reason: 'Customer claims legitimate vendor payment', approverRole: 'Head of Financial Crime Compliance', status: 'PENDING', riskScore: 94 },
      ],
    },
    q5_escalation: {
      headline: 'Severe Syndicate Breach Protocols',
      procedures: [
        { name: 'Active Treasury Account Takeover & Exfiltration', trigger: 'Root admin session compromised, multiple unauthorized wires outbound', sopSteps: ['Trigger Global Wire Gateway Killswitch', 'Force logout of all sessions on compromised corporate account', 'Direct liaison with Reserve Bank FIU and Cyber Cell'], failsafeAction: 'Immediate Core Banking Gateway Killswitch', escalationContact: 'CISO / FIU Emergency Hotline: Ext 8888' },
      ],
    },
  },

  customer: {
    roleId: 'customer',
    roleName: 'Banking Customer (Tony Stark)',
    domain: 'FINANCE',
    department: 'Retail & Commercial Banking',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Account balance monitoring, secure payment transfers, instant debit card freeze, and transaction dispute filing.',
    q1_immediate: {
      headline: 'Pending Approvals & Security Notifications',
      tasks: [
        { id: 'CUST-01', title: 'Confirm ₹1,200 Payment to Shell Petrol BTM', subtitle: 'Card used at Point of Sale — Confirm if authorized', urgency: 'HIGH', slaMinutes: 30, category: 'Card Security', actionLabel: 'Approve' },
        { id: 'CUST-02', title: 'Monthly Statement Ready for Download', subtitle: 'Account ending in ...33 (August 2026 Statement)', urgency: 'LOW', category: 'Statement', actionLabel: 'Download' },
      ],
    },
    q2_information: {
      headline: 'Account Balances & Security Shield Health',
      metrics: [
        { label: 'Checking Balance', value: '₹24,500,000', status: 'HEALTHY' },
        { label: 'Security Shield Score', value: '98 / 100 (High)', status: 'SECURED' },
        { label: 'Debit Card Status', value: 'ACTIVE (Shield On)', status: 'NORMAL' },
        { label: 'International Usage', value: 'DISABLED', status: 'SECURED' },
      ],
      keyContextList: [
        { label: 'Account Holder', value: 'Tony Stark' },
        { label: 'Primary Account', value: 'ACC-9001 (Treasury Savings)' },
        { label: 'Branch', value: 'Bengaluru Financial Plaza' },
        { label: 'Two-Factor Auth', value: 'Hardware Security Key (Yubikey)' },
      ],
    },
    q3_actions: {
      headline: 'Customer Self-Service Actions',
      actions: [
        { id: 'CUST_SEND', label: 'Send Money (With ML Safety Check)', description: 'Transfer funds with real-time pre-settlement fraud verification', icon: 'ArrowRight', variant: 'primary' },
        { id: 'CUST_FREEZE', label: 'Instant Card Freeze', description: 'Lock debit/credit card immediately from unauthorized charges', icon: 'Lock', variant: 'danger' },
        { id: 'CUST_DISPUTE', label: 'Dispute Unknown Transaction', description: 'Flag fraudulent charge and request instant escrow recovery', icon: 'AlertTriangle', variant: 'warning' },
      ],
    },
    q4_approvals: {
      headline: 'Pending Dual-Factor Approvals',
      items: [
        { id: 'APP-CUST-01', title: 'High-Value Beneficiary Addition (₹500,000)', submittedBy: 'Self', submittedAt: 'Yesterday', reason: 'Vendor Equipment Supplier', approverRole: 'OTP + Biometric Auth', status: 'PENDING' },
      ],
    },
    q5_escalation: {
      headline: 'Card Theft & Account Compromise Protocol',
      procedures: [
        { name: 'Lost Phone / Stolen Card / Unauthorized Charge', trigger: 'Suspicious debit notification or missing physical card', sopSteps: ['Tap Instant Card Freeze button', 'Change NetBanking password from trusted browser', 'Call 24/7 bank fraud helpline to lock NetBanking'], failsafeAction: 'Instant Emergency NetBanking Account Freeze', escalationContact: '24/7 Fraud Hotline: 1800-425-9999' },
      ],
    },
  },

  // ══════════════════════════════════════════════════════════════════
  // SECURITY DOMAIN
  // ══════════════════════════════════════════════════════════════════
  soc_analyst: {
    roleId: 'soc_analyst',
    roleName: 'SOC Threat Hunter & Incident Responder',
    domain: 'SECURITY',
    department: 'Smart City Security Operations Center',
    dutyStatus: 'INCIDENT_RESPONSE',
    summary: 'Pan-city alert correlation, MITRE kill-chain mapping, root-cause forensics, zero-trust microsegmentation, and containment.',
    q1_immediate: {
      headline: 'Active Cyber-Physical Incident Queue & High-Severity Alerts',
      tasks: [
        { id: 'SOC-01', title: 'OT Cyber-Physical Breach: Municipal Water Treatment SCADA', subtitle: 'MITRE T1059: Malicious setpoint rewrite on chlorine dosing PLC — Blast radius: 3 wards', urgency: 'CRITICAL', slaMinutes: 10, category: 'SCADA Anomaly', actionLabel: 'Isolate Subnet' },
        { id: 'SOC-02', title: 'Compromised Clinician Credential Mass Exfiltration', subtitle: 'MITRE T1078: 2,000 patient records queried from London VPN IP — Adaptive block triggered', urgency: 'CRITICAL', slaMinutes: 15, category: 'EHR Exfiltration', actionLabel: 'Revoke Session' },
        { id: 'SOC-03', title: 'Traffic Signal STIG Controller Cycle Flooding', subtitle: 'UDP packet flood targeting Hebbal signal actuators — Anomaly score 0.88', urgency: 'HIGH', slaMinutes: 30, category: 'DDoS Attack', actionLabel: 'Deploy Rule' },
      ],
    },
    q2_information: {
      headline: 'Pan-City Threat Correlation & Sensor Feeds',
      metrics: [
        { label: 'Composite City Risk', value: '28.5 / 100', status: 'NORMAL', trend: 'Elevated in Water' },
        { label: 'Open Incidents', value: '2 Active', status: 'CRITICAL' },
        { label: 'Mean Time to Contain', value: '4.2 Mins', status: 'HEALTHY', trend: 'Down 28%' },
        { label: 'Quantum Vault Health', value: '100% Armed', status: 'SECURED' },
      ],
      keyContextList: [
        { label: 'Threat Actor Group', value: 'APT-MUNICIPAL-29 (Suspected SCADA Unit)' },
        { label: 'Active Containments', value: 'Water Subnet 10.40.1.100 Micro-Isolated' },
        { label: 'Threat Feeds Active', value: 'MIMIC-IV, STIG Traffic, UPI Telemetry' },
        { label: 'Duty Lead', value: 'Lead Threat Hunter Vikram Seth' },
      ],
    },
    q3_actions: {
      headline: 'Authorized SOC Containment Controls',
      actions: [
        { id: 'SOC_ISOLATE', label: 'Enforce Subnet Microsegmentation', description: 'Sever network bridge to compromised SCADA or IoMT asset', icon: 'Lock', variant: 'danger', requiredCapability: 'can_execute_mitigations' },
        { id: 'SOC_REVOKE', label: 'Revoke Compromised User Session', description: 'Invalidate all JWT tokens and enforce step-up biometric MFA', icon: 'UserX', variant: 'warning', requiredCapability: 'can_execute_mitigations' },
        { id: 'SOC_TICKET', label: 'Escalate Incident to CERT-In', description: 'File formal cyber-physical breach disclosure report', icon: 'FileText', variant: 'primary', requiredCapability: 'can_execute_mitigations' },
        { id: 'SOC_RESET', label: 'Restore Subsystem to Baseline', description: 'Apply clean firmware golden image and clear quarantine', icon: 'RotateCcw', variant: 'outline', requiredCapability: 'can_execute_mitigations' },
      ],
    },
    q4_approvals: {
      headline: 'Dual-Key Emergency Authorizations',
      items: [
        { id: 'APP-SOC-01', title: 'Citywide SCADA Substation Failover to Island Mode', submittedBy: 'Lead Threat Hunter', submittedAt: '10 mins ago', reason: 'Prevent lateral propagation from water grid to power grid', approverRole: 'Global CISO / City Commissioner', status: 'PENDING', riskScore: 92 },
      ],
    },
    q5_escalation: {
      headline: 'Mass Cyber-Physical Catastrophe SOPs',
      procedures: [
        { name: 'Cascading Blackout / Critical Public Health Hazard', trigger: 'Multiple critical infrastructure subnets compromised simultaneously', sopSteps: ['Activate Disaster Recovery Cold Standby', 'Isolate all SCADA networks from public internet via air-gap relay', 'Convene Emergency Civil Defense Cabinet'], failsafeAction: 'Engage City Air-Gap Disconnect Switch', escalationContact: 'National Cyber Security Coordinator: Ext 1000' },
      ],
    },
  },

  admin: {
    roleId: 'admin',
    roleName: 'Global CISO / Pan-City Administrator',
    domain: 'SECURITY',
    department: 'Smart City Executive Command',
    dutyStatus: 'ACTIVE_DUTY',
    summary: 'Unrestricted pan-city visibility, policy governance, dual-key authorizations, and multi-agency crisis coordination.',
    q1_immediate: {
      headline: 'Pan-City Operational Readiness & Crisis Queue',
      tasks: [
        { id: 'ADM-01', title: 'Approve Citywide SCADA Substation Islanding Protocol', subtitle: 'Dual-key signature requested by Lead Threat Hunter Vikram Seth', urgency: 'CRITICAL', slaMinutes: 10, category: 'Emergency Authorization', actionLabel: 'Authorize' },
        { id: 'ADM-02', title: 'Review Annual UN SDG Goal 9/11 Resilience Compliance Audit', subtitle: 'Verify ISO 27001 & IEC 62443 cyber-physical controls', urgency: 'LOW', slaMinutes: 480, category: 'Governance', actionLabel: 'Review Audit' },
      ],
    },
    q2_information: {
      headline: 'Executive Multi-Sector Cyber-Physical Health',
      metrics: [
        { label: 'Pan-City Risk Index', value: '28.5 / 100', status: 'NORMAL' },
        { label: 'Value-at-Risk (95%)', value: '$2.10M', status: 'HEALTHY' },
        { label: 'Active Infrastructure', value: '12 / 12 Assets', status: 'ACTIVE' },
        { label: 'Zero-Trust Policies', value: '42 Enforced', status: 'SECURED' },
      ],
      keyContextList: [
        { label: 'Global Authority', value: 'Unrestricted Pan-City Cross-Sector' },
        { label: 'Jurisdiction', value: 'Bengaluru Metropolitan Smart Grid' },
        { label: 'Regulatory Scope', value: 'CERT-In, DPDP Act 2023, UN SDG 9/11' },
        { label: 'Dual-Key Status', value: 'Master Key Slot 1 Active' },
      ],
    },
    q3_actions: {
      headline: 'Executive Authorization Powers',
      actions: [
        { id: 'ADM_DUAL_KEY', label: 'Authorize Emergency Island Mode', description: 'Dual-key sign-off for critical infrastructure isolation', icon: 'Key', variant: 'danger', requiredCapability: 'can_edit_policies' },
        { id: 'ADM_POLICY', label: 'Deploy Zero-Trust Access Policy', description: 'Enforce dynamic ABAC rule across all 35 stakeholder roles', icon: 'Shield', variant: 'primary', requiredCapability: 'can_edit_policies' },
        { id: 'ADM_RESET', label: 'Reset Digital Twin Baseline', description: 'Restore all 12 smart city assets to nominal telemetry baseline', icon: 'RotateCcw', variant: 'warning', requiredCapability: 'can_execute_mitigations' },
      ],
    },
    q4_approvals: {
      headline: 'Pending Executive Decisions',
      items: [
        { id: 'APP-ADM-01', title: 'Citywide SCADA Substation Islanding Protocol', submittedBy: 'SOC Threat Hunter', submittedAt: '10 mins ago', reason: 'Prevent lateral propagation', approverRole: 'Global CISO (You)', status: 'PENDING', riskScore: 92 },
      ],
    },
    q5_escalation: {
      headline: 'State & National Level Emergency Coordination',
      procedures: [
        { name: 'National Critical Information Infrastructure Crisis', trigger: 'Attacks causing systemic disruption across multiple state sectors', sopSteps: ['Brief Chief Minister & National Cyber Security Coordinator', 'Activate Armed Forces Cyber Command mutual assistance pact', 'Transition critical hospitals and grids to isolated emergency power'], failsafeAction: 'Declare State Civil Defense Cyber Emergency', escalationContact: 'Prime Minister Office National Security Advisor: Ext 1' },
      ],
    },
  },
};

// Aliases for roles that share primary workflow models
WORKFLOW_REGISTRY['superadmin'] = WORKFLOW_REGISTRY['admin'];
WORKFLOW_REGISTRY['health_operator'] = WORKFLOW_REGISTRY['hospital_security'] = WORKFLOW_REGISTRY['doctor'];
WORKFLOW_REGISTRY['hospital_admin'] = WORKFLOW_REGISTRY['reception'];
WORKFLOW_REGISTRY['billing_staff'] = WORKFLOW_REGISTRY['reception'];
WORKFLOW_REGISTRY['lab_technician'] = WORKFLOW_REGISTRY['doctor'];
WORKFLOW_REGISTRY['emergency_coordinator'] = WORKFLOW_REGISTRY['reception'];
WORKFLOW_REGISTRY['traffic_supervisor'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['traffic_police'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['camera_operator'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['signal_technician'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['emergency_traffic'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['road_maintenance'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['transport_authority'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['traffic_analyst'] = WORKFLOW_REGISTRY['traffic_operator'];
WORKFLOW_REGISTRY['traffic_cybersecurity'] = WORKFLOW_REGISTRY['soc_analyst'];
WORKFLOW_REGISTRY['aml_analyst'] = WORKFLOW_REGISTRY['fraud_analyst'];
WORKFLOW_REGISTRY['risk_analyst'] = WORKFLOW_REGISTRY['fraud_analyst'];
WORKFLOW_REGISTRY['teller'] = WORKFLOW_REGISTRY['customer'];
WORKFLOW_REGISTRY['relationship_manager'] = WORKFLOW_REGISTRY['customer'];
WORKFLOW_REGISTRY['branch_manager'] = WORKFLOW_REGISTRY['fraud_analyst'];
WORKFLOW_REGISTRY['compliance_officer'] = WORKFLOW_REGISTRY['fraud_analyst'];
WORKFLOW_REGISTRY['auditor'] = WORKFLOW_REGISTRY['admin'];
WORKFLOW_REGISTRY['finance_admin'] = WORKFLOW_REGISTRY['fraud_analyst'];
WORKFLOW_REGISTRY['analyst'] = WORKFLOW_REGISTRY['security_analyst'] = WORKFLOW_REGISTRY['security_manager'] = WORKFLOW_REGISTRY['soc_analyst'];

export function getWorkflowForRole(role: string): WorkflowDefinition {
  const norm = (role || 'admin').toLowerCase().trim();
  return WORKFLOW_REGISTRY[norm] || WORKFLOW_REGISTRY['admin'];
}
