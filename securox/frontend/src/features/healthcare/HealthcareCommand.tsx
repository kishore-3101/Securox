import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { healthcareService } from '../../services/healthcareService';
import { Patient, IoMTDevice } from '../../types/healthcare';

// Subsystems
import { OverviewSubsystem } from './subsystems/OverviewSubsystem';
import { PatientRegistrationSubsystem } from './subsystems/PatientRegistrationSubsystem';
import { AppointmentsSubsystem } from './subsystems/AppointmentsSubsystem';
import { AdmissionsSubsystem } from './subsystems/AdmissionsSubsystem';
import { DoctorSubsystem } from './subsystems/DoctorSubsystem';
import { NurseSubsystem } from './subsystems/NurseSubsystem';
import { LabSubsystem } from './subsystems/LabSubsystem';
import { PharmacySubsystem } from './subsystems/PharmacySubsystem';
import { BillingSubsystem } from './subsystems/BillingSubsystem';
import { EmergencySubsystem } from './subsystems/EmergencySubsystem';
import { AmbulanceSubsystem } from './subsystems/AmbulanceSubsystem';
import { ParamedicSubsystem } from './subsystems/ParamedicSubsystem';
import { IoMTSubsystem } from './subsystems/IoMTSubsystem';
import { SecuritySubsystem } from './subsystems/SecuritySubsystem';

import {
  HeartPulse,
  Activity,
  Users,
  Calendar,
  Bed,
  Stethoscope,
  UserCheck,
  TestTube,
  Pill,
  CreditCard,
  PhoneCall,
  Ambulance,
  Radio,
  ShieldCheck,
  Zap,
  Lock,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

export const HealthcareCommand: React.FC = () => {
  const { role, user, switchRole } = useAuth();
  const userRole = (role || 'admin').toLowerCase();

  // Active navigation tab
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Shared state
  const [patients, setPatients] = useState<Patient[]>([]);
  const [devices, setDevices] = useState<IoMTDevice[]>([]);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Global Break-Glass modal state
  const [breakGlassActivePatient, setBreakGlassActivePatient] = useState<string | null>(null);
  const [switchingRole, setSwitchingRole] = useState(false);

  // Seed default sample patients if backend starts empty
  const defaultSamplePatients: Patient[] = [
    {
      id: 'P-1001',
      name: 'Ramesh Patel',
      age: 58,
      gender: 'Male',
      department: 'Cardiology',
      assigned_doctor_id: 'doctor',
      assigned_nurse_id: 'nurse',
      condition: 'CRITICAL',
      diagnosis: 'Acute Inferior STEMI (Post-PCI Stent)',
      room_bed: 'ICU-Bed-04',
      vitals: { hr: 108, heart_rate_bpm: 108, bp: '148/94', blood_pressure_sys: 148, blood_pressure_dia: 94, spo2: 95, oxygen_saturation_pct: 95, temp: 37.2, temperature_c: 37.2, respiration_rate: 20 },
      sensitivity: 'CONFIDENTIAL',
    },
    {
      id: 'P-1002',
      name: 'Sunita Sharma',
      age: 44,
      gender: 'Female',
      department: 'Cardiology',
      assigned_doctor_id: 'doctor',
      assigned_nurse_id: 'nurse',
      condition: 'GUARDED',
      diagnosis: 'Paroxysmal Supraventricular Tachycardia',
      room_bed: 'Stepdown-02',
      vitals: { hr: 86, heart_rate_bpm: 86, bp: '124/80', blood_pressure_sys: 124, blood_pressure_dia: 80, spo2: 98, oxygen_saturation_pct: 98, temp: 36.8, temperature_c: 36.8, respiration_rate: 16 },
      sensitivity: 'CONFIDENTIAL',
    },
    {
      id: 'P-1003',
      name: 'Anand Verma',
      age: 63,
      gender: 'Male',
      department: 'Emergency',
      assigned_doctor_id: 'doctor',
      assigned_nurse_id: 'nurse',
      condition: 'CRITICAL',
      diagnosis: 'Acute Coronary Syndrome in Transit',
      room_bed: 'Trauma-Bay-01',
      vitals: { hr: 118, heart_rate_bpm: 118, bp: '158/94', blood_pressure_sys: 158, blood_pressure_dia: 94, spo2: 93, oxygen_saturation_pct: 93, temp: 37.4, temperature_c: 37.4, respiration_rate: 22 },
      sensitivity: 'CONFIDENTIAL',
    },
    {
      id: 'P-1004',
      name: 'Devraj Mukherjee',
      age: 62,
      gender: 'Male',
      department: 'Oncology',
      assigned_doctor_id: 'dr_sharma',
      assigned_nurse_id: 'nurse_onc',
      condition: 'STABLE',
      diagnosis: 'Multiple Myeloma Regimen Day 3',
      room_bed: 'Ward-ONC-08',
      vitals: { hr: 76, heart_rate_bpm: 76, bp: '118/76', blood_pressure_sys: 118, blood_pressure_dia: 76, spo2: 99, oxygen_saturation_pct: 99, temp: 36.9, temperature_c: 36.9, respiration_rate: 16 },
      sensitivity: 'RESTRICTED',
    },
  ];

  const defaultSampleDevices: IoMTDevice[] = [
    { id: 'IOMT-PUMP-01', name: 'Alaris Infusion Pump 4A', department: 'Cardiology ICU', ip_address: '10.20.2.14', mac_address: '00:1A:2B:3C:4D:5E', protocol: 'HL7v2 / MQTT', firmware: 'v4.2.1', status: 'ANOMALOUS', quarantine: false, risk_score: 89, last_heartbeat: new Date().toISOString() },
    { id: 'IOMT-PUMP-02', name: 'Alaris Infusion Pump 4B', department: 'Cardiology ICU', ip_address: '10.20.2.15', mac_address: '00:1A:2B:3C:4D:5F', protocol: 'HL7v2 / MQTT', firmware: 'v4.2.1', status: 'ONLINE', quarantine: false, risk_score: 12, last_heartbeat: new Date().toISOString() },
    { id: 'IOMT-VENT-01', name: 'Servo-U Ventilator #1', department: 'Surgical ICU', ip_address: '10.20.3.22', mac_address: '00:1A:2B:3C:4D:60', protocol: 'DICOM / CoAP', firmware: 'v2.8.0', status: 'ONLINE', quarantine: false, risk_score: 18, last_heartbeat: new Date().toISOString() },
    { id: 'IOMT-PACE-01', name: 'Biotronik Pacemaker Gate', department: 'Cardiology Ward 2', ip_address: '10.20.2.80', mac_address: '00:1A:2B:3C:4D:61', protocol: 'HL7 / Proprietary', firmware: 'v1.4.9', status: 'ONLINE', quarantine: false, risk_score: 42, last_heartbeat: new Date().toISOString() },
  ];

  const loadData = async () => {
    try {
      const pRes = await healthcareService.getPatients();
      if (pRes && pRes.patients && pRes.patients.length > 0) {
        setPatients(pRes.patients);
      } else {
        setPatients(defaultSamplePatients);
      }
    } catch {
      setPatients(defaultSamplePatients);
    }

    try {
      const dRes = await healthcareService.getIoMTDevices();
      if (dRes && dRes.devices && dRes.devices.length > 0) {
        setDevices(dRes.devices);
      } else {
        setDevices(defaultSampleDevices);
      }
    } catch {
      setDevices(defaultSampleDevices);
    } finally {
      setLoadingInitial(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRoleChange = async (newRole: string) => {
    setSwitchingRole(true);
    try {
      await switchRole(newRole);
      // Auto switch to role default tab
      if (newRole === 'doctor') setActiveTab('doctor');
      else if (newRole === 'nurse') setActiveTab('nurse');
      else if (newRole === 'reception') setActiveTab('patients');
      else if (newRole === 'billing_staff' || newRole === 'billing') setActiveTab('billing');
      else if (newRole === 'lab_technician') setActiveTab('lab');
      else if (newRole === 'pharmacist') setActiveTab('pharmacy');
      else if (newRole === 'paramedic') setActiveTab('paramedic');
      else if (newRole === 'ambulance_driver') setActiveTab('ambulance');
      else if (newRole === 'hospital_security') setActiveTab('security');
      else setActiveTab('overview');
    } catch (err) {
      console.error('Failed to switch role:', err);
    } finally {
      setSwitchingRole(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: HeartPulse, count: null },
    { id: 'patients', label: 'Registration', icon: Users, count: patients.length },
    { id: 'appointments', label: 'Appointments', icon: Calendar, count: null },
    { id: 'admissions', label: 'Admissions & Beds', icon: Bed, count: null },
    { id: 'doctor', label: 'Doctor EHR', icon: Stethoscope, count: null, highlight: userRole === 'doctor' },
    { id: 'nurse', label: 'Nurse Station', icon: UserCheck, count: null, highlight: userRole === 'nurse' },
    { id: 'lab', label: 'LIS Laboratory', icon: TestTube, count: null, highlight: userRole === 'lab_technician' },
    { id: 'pharmacy', label: 'Pharmacy & Pyxis', icon: Pill, count: null, highlight: userRole === 'pharmacist' },
    { id: 'billing', label: 'Billing & TPA', icon: CreditCard, count: null, highlight: userRole.includes('billing') },
    { id: 'emergency', label: 'ED CAD Triage', icon: PhoneCall, count: null },
    { id: 'ambulance', label: 'Ambulance CAD', icon: Ambulance, count: null, highlight: userRole === 'ambulance_driver' },
    { id: 'paramedic', label: 'Paramedic Uplink', icon: Radio, count: null, highlight: userRole === 'paramedic' },
    { id: 'iomt', label: 'IoMT Security', icon: Activity, count: devices.filter(d => d.status === 'ANOMALOUS' || d.risk_score > 60).length || null },
    { id: 'security', label: 'Hospital IT Sec', icon: ShieldCheck, count: null, highlight: userRole === 'hospital_security' },
  ];

  return (
    <div className="space-y-6 animate-fadeIn font-sans">
      {/* Top Suite Title & Stakeholder Persona Switcher */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-rose-600 to-red-500 flex items-center justify-center text-white shadow-lg shadow-rose-600/30">
            <HeartPulse className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wide">
                CAREGUARD HEALTHCARE COMMAND SUITE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Persona: <strong className="text-rose-300 uppercase">{userRole}</strong>
              </span>
            </div>
            <h1 className="text-xl font-bold font-mono text-slate-100">
              City General Hospital (H001) Operational Console
            </h1>
            <p className="text-xs font-mono text-slate-400">
              14 Integrated Clinical & IoMT Cyber Subsystems with Strict Role Scoping & Break-Glass Protocol
            </p>
          </div>
        </div>

        {/* 1-Click Role Switcher Bar */}
        <div className="flex flex-wrap items-center gap-1.5 p-2 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 px-2 font-bold uppercase">
            Switch Persona:
          </span>
          {[
            { id: 'doctor', label: 'Doctor' },
            { id: 'nurse', label: 'Nurse' },
            { id: 'reception', label: 'Reception' },
            { id: 'billing_staff', label: 'Billing' },
            { id: 'lab_technician', label: 'Lab Tech' },
            { id: 'pharmacist', label: 'Pharmacy' },
            { id: 'paramedic', label: 'Paramedic' },
            { id: 'ambulance_driver', label: 'Ambulance' },
            { id: 'hospital_security', label: 'Security' },
            { id: 'admin', label: 'Admin' },
          ].map((r) => (
            <button
              key={r.id}
              onClick={() => handleRoleChange(r.id)}
              disabled={switchingRole}
              className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                userRole === r.id || (r.id === 'billing_staff' && userRole === 'billing')
                  ? 'bg-rose-600 text-white font-bold shadow-md shadow-rose-950'
                  : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* 14 Subsystem Tabs Navigation Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg overflow-x-auto scrollbar-none">
        <div className="flex items-center gap-1.5 min-w-max">
          {tabs.map((t) => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;

            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-mono transition relative ${
                  isActive
                    ? 'bg-rose-600 text-white font-bold shadow-md shadow-rose-950'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                } ${t.highlight && !isActive ? 'border border-rose-500/40 text-rose-300 bg-rose-950/20' : ''}`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : t.highlight ? 'text-rose-400' : 'text-slate-400'}`} />
                <span>{t.label}</span>
                {t.count !== null && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : t.id === 'iomt' && t.count > 0
                        ? 'bg-rose-500 text-white animate-pulse'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {t.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Subsystem Render Switcher */}
      <div className="transition-all duration-200">
        {activeTab === 'overview' && (
          <OverviewSubsystem
            patients={patients}
            devices={devices}
            onNavigateTab={(t) => setActiveTab(t)}
            onOpenBreakGlass={() => {
              setActiveTab('doctor');
              setBreakGlassActivePatient('P-1004');
            }}
          />
        )}

        {activeTab === 'patients' && (
          <PatientRegistrationSubsystem
            patients={patients}
            onPatientRegistered={(newP) => setPatients((prev) => [newP, ...prev])}
            userRole={userRole}
          />
        )}

        {activeTab === 'appointments' && (
          <AppointmentsSubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'admissions' && (
          <AdmissionsSubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'doctor' && (
          <DoctorSubsystem
            patients={patients}
            userRole={userRole}
            breakGlassActiveForPatient={breakGlassActivePatient}
            onBreakGlassSuccess={(patId, newRisk, incId) => {
              setBreakGlassActivePatient(patId);
            }}
          />
        )}

        {activeTab === 'nurse' && (
          <NurseSubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'lab' && (
          <LabSubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'pharmacy' && (
          <PharmacySubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'billing' && (
          <BillingSubsystem patients={patients} userRole={userRole} />
        )}

        {activeTab === 'emergency' && (
          <EmergencySubsystem userRole={userRole} />
        )}

        {activeTab === 'ambulance' && (
          <AmbulanceSubsystem userRole={userRole} />
        )}

        {activeTab === 'paramedic' && (
          <ParamedicSubsystem userRole={userRole} />
        )}

        {activeTab === 'iomt' && (
          <IoMTSubsystem userRole={userRole} />
        )}

        {activeTab === 'security' && (
          <SecuritySubsystem userRole={userRole} />
        )}
      </div>
    </div>
  );
};

export default HealthcareCommand;
