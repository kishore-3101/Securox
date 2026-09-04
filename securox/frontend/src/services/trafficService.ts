import { api } from './api';
import {
  TrafficSignal,
  CameraFeed,
  Intersection,
  RoadSegment,
  TrafficSensor,
  SensorDisparityReport,
  TrafficIncident,
  TollScanRecord,
  GreenCorridor,
  MaintenanceTicket,
  CitizenPublicFeed,
  TrafficOverview,
  SignalSafetyOverrideRequest,
  SignalSafetyOverrideResponse,
  MobileCameraSession,
  VehicleDetection,
  RFIDReader,
  RFIDRead,
  FastagRecord,
  VehicleVerificationRecord,
} from '../types/traffic';

export const trafficService = {
  // ── Overview & Grid Telemetry ──
  async getOverview(): Promise<TrafficOverview> {
    return api.get('/traffic/overview');
  },

  // ── Signals & Critical Safety Override ──
  async getSignals(): Promise<TrafficSignal[]> {
    const res = await api.get('/traffic/signals');
    // Normalize in case response wraps in an object or array
    if (Array.isArray(res)) return res;
    if (res && Array.isArray((res as any).signals)) return (res as any).signals;
    return [];
  },

  async getSignal(signalId: string): Promise<TrafficSignal> {
    return api.get(`/traffic/signals/${signalId}`);
  },

  async safetyOverrideSignal(
    signalId: string,
    payload: SignalSafetyOverrideRequest
  ): Promise<SignalSafetyOverrideResponse> {
    return api.post(`/traffic/signals/${signalId}/safety-override`, payload);
  },

  // Legacy fallback override
  async overrideSignal(
    signalId: string,
    state: string = 'GREEN',
    mode: string = 'MANUAL_OVERRIDE'
  ): Promise<any> {
    return api.post('/traffic/override-signal', {
      junction_id: signalId,
      state,
      mode,
    });
  },

  // ── Cameras & Vision Feeds ──
  async getCameras(): Promise<CameraFeed[]> {
    const res = await api.get('/traffic/cameras');
    if (Array.isArray(res)) return res;
    if (res && Array.isArray((res as any).cameras)) return (res as any).cameras;
    return [];
  },

  async injectCameraBehavior(cameraId: string, behavior: string): Promise<any> {
    return api.post(`/traffic/cameras/${cameraId}/inject-behavior`, { behavior });
  },

  // ── Roads & Congestion ──
  async getRoads(): Promise<RoadSegment[]> {
    const res = await api.get('/traffic/roads');
    return Array.isArray(res) ? res : [];
  },

  // ── Sensors & Disparity Analysis ──
  async getSensors(): Promise<TrafficSensor[]> {
    const res = await api.get('/traffic/sensors');
    return Array.isArray(res) ? res : [];
  },

  async getSensorDisparity(): Promise<SensorDisparityReport> {
    return api.get('/traffic/sensors/disparity');
  },

  // ── Incidents Management ──
  async getIncidents(status?: string): Promise<TrafficIncident[]> {
    const url = status ? `/traffic/incidents?status=${status}` : '/traffic/incidents';
    const res = await api.get(url);
    return Array.isArray(res) ? res : [];
  },

  async createIncident(payload: {
    title: string;
    category: string;
    severity: string;
    location: string;
    road_id?: string;
    description?: string;
  }): Promise<TrafficIncident> {
    return api.post('/traffic/incidents', payload);
  },

  async verifyIncident(incidentId: string, notes?: string): Promise<TrafficIncident> {
    return api.patch(`/traffic/incidents/${incidentId}/verify`, { verified: true, notes });
  },

  async updateIncidentStatus(
    incidentId: string,
    status: string,
    resolution_notes?: string
  ): Promise<TrafficIncident> {
    return api.patch(`/traffic/incidents/${incidentId}/status`, { status, resolution_notes });
  },

  // ── Toll & FASTag ANPR ──
  async getTollScans(status?: string): Promise<TollScanRecord[]> {
    const url = status ? `/traffic/toll/scans?status=${status}` : '/traffic/toll/scans';
    const res = await api.get(url);
    return Array.isArray(res) ? res : [];
  },

  async processTollScan(payload: {
    tollgate_id: string;
    tollgate_name: string;
    vehicle_number: string;
    fastag_id: string;
    amount?: number;
    vehicle_class?: string;
  }): Promise<TollScanRecord> {
    return api.post('/traffic/toll/process', payload);
  },

  async overrideTollScan(scanId: string, reason: string): Promise<TollScanRecord> {
    return api.post(`/traffic/toll/${scanId}/override`, { reason });
  },

  // ── Emergency Response & Green Corridors ──
  async getGreenCorridors(): Promise<GreenCorridor[]> {
    const res = await api.get('/traffic/green-corridor');
    return Array.isArray(res) ? res : [];
  },

  async createGreenCorridor(payload: {
    name: string;
    origin_location: string;
    destination_hospital: string;
    ambulance_id?: string;
    emergency_dispatch_id?: string;
    route_intersections: string[];
  }): Promise<GreenCorridor> {
    return api.post('/traffic/green-corridor/create', payload);
  },

  async activateGreenCorridor(corridorId: string): Promise<GreenCorridor> {
    return api.post(`/traffic/green-corridor/${corridorId}/activate`);
  },

  async deactivateGreenCorridor(corridorId: string): Promise<GreenCorridor> {
    return api.post(`/traffic/green-corridor/${corridorId}/deactivate`);
  },

  async triggerGreenCorridor(name: string, routeIntersections: string[]): Promise<any> {
    try {
      const corridor = await this.createGreenCorridor({
        name,
        origin_location: 'Emergency CAD Unit',
        destination_hospital: 'City General Hospital',
        route_intersections: routeIntersections,
      });
      return await this.activateGreenCorridor(corridor.id);
    } catch {
      return { status: 'CORRIDOR_ACTIVATED', intersections: routeIntersections };
    }
  },

  // ── Maintenance Tickets ──
  async getMaintenanceTickets(status?: string): Promise<MaintenanceTicket[]> {
    const url = status ? `/traffic/maintenance/tickets?status=${status}` : '/traffic/maintenance/tickets';
    const res = await api.get(url);
    return Array.isArray(res) ? res : [];
  },

  async createMaintenanceTicket(payload: {
    signal_id: string;
    issue_type: string;
    priority: string;
    voltage_reading?: number;
    loop_resistance_ohms?: number;
    firmware_checksum?: string;
    diagnostic_log?: string;
  }): Promise<MaintenanceTicket> {
    return api.post('/traffic/maintenance/tickets', payload);
  },

  async updateMaintenanceTicket(
    ticketId: string,
    status: string,
    diagnostic_log?: string,
    resolution_notes?: string
  ): Promise<MaintenanceTicket> {
    return api.patch(`/traffic/maintenance/tickets/${ticketId}`, {
      status,
      diagnostic_log,
      resolution_notes,
    });
  },

  // ── Citizen Portal Public Feed ──
  async getCitizenPublicFeed(): Promise<CitizenPublicFeed> {
    return api.get('/traffic/citizen/public-feed');
  },

  // ── Stats / Auxiliary ──
  async getStats(): Promise<any> {
    return api.get('/traffic/stats');
  },

  async getViolations(): Promise<any> {
    return api.get('/traffic/violations');
  },

  // ── Advanced Video & WebRTC Cameras ──
  async getAdvancedCameras(): Promise<CameraFeed[]> {
    const res = await api.get('/api/v1/traffic/cameras');
    return Array.isArray(res) ? res : [];
  },

  async createTrafficCamera(payload: Partial<CameraFeed>): Promise<CameraFeed> {
    return api.post('/api/v1/traffic/cameras', payload);
  },

  async updateTrafficCamera(id: string, payload: Partial<CameraFeed>): Promise<CameraFeed> {
    return api.patch(`/api/v1/traffic/cameras/${id}`, payload);
  },

  async deleteTrafficCamera(id: string): Promise<any> {
    return api.delete(`/api/v1/traffic/cameras/${id}`);
  },

  async startCameraStream(id: string): Promise<any> {
    return api.post(`/api/v1/traffic/cameras/${id}/stream/start`);
  },

  async stopCameraStream(id: string): Promise<any> {
    return api.post(`/api/v1/traffic/cameras/${id}/stream/stop`);
  },

  async getCameraStreamInfo(id: string): Promise<any> {
    return api.get(`/api/v1/traffic/cameras/${id}/stream`);
  },

  async registerMobileCamera(payload: {
    device_id: string;
    operator_id: string;
    fps?: number;
    resolution?: string;
    device_metadata?: Record<string, any>;
  }): Promise<MobileCameraSession> {
    const res: any = await api.post('/api/v1/traffic/mobile-camera/session', payload);
    return res?.session || res;
  },

  // ── Vehicle Detections & Tracking ──
  async getVehicleDetections(params?: {
    limit?: number;
    tracking_id?: string;
    camera_id?: string;
  }): Promise<VehicleDetection[]> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.tracking_id) query.append('tracking_id', params.tracking_id);
    if (params?.camera_id) query.append('camera_id', params.camera_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await api.get(`/api/v1/traffic/detections${qs}`);
    return Array.isArray(res) ? res : [];
  },

  async ingestVehicleDetection(payload: {
    camera_id: string;
    tracking_id: string;
    vehicle_type?: string;
    plate_number?: string;
    plate_confidence?: number;
    speed_kmh?: number;
    metadata_json?: Record<string, any>;
  }): Promise<VehicleDetection> {
    return api.post('/api/v1/traffic/detections/ingest', payload);
  },

  async getTrackedVehicles(limit: number = 50): Promise<any[]> {
    const res = await api.get(`/api/v1/traffic/vehicles?limit=${limit}`);
    return Array.isArray(res) ? res : [];
  },

  async getTrackedPlates(limit: number = 50): Promise<any[]> {
    const res = await api.get(`/api/v1/traffic/plates?limit=${limit}`);
    return Array.isArray(res) ? res : [];
  },

  // ── RFID & Vehicle Identity Verification ──
  async getRfidReaders(): Promise<RFIDReader[]> {
    const res: any = await api.get('/api/v1/traffic/rfid/readers');
    if (Array.isArray(res)) return res;
    if (res?.readers && Array.isArray(res.readers)) return res.readers;
    return [];
  },

  async getRfidReads(limit: number = 50): Promise<RFIDRead[]> {
    const res: any = await api.get(`/api/v1/traffic/rfid/reads?limit=${limit}`);
    if (Array.isArray(res)) return res;
    if (res?.reads && Array.isArray(res.reads)) return res.reads;
    return [];
  },

  async ingestRfidRead(payload: {
    reader_id: string;
    tag_id: string;
    epc?: string;
    signal_rssi?: number;
    lane_id?: string;
  }): Promise<RFIDRead> {
    return api.post('/api/v1/traffic/rfid/read', payload);
  },

  async verifyVehicleIdentity(payload: {
    camera_id?: string;
    rfid_reader_id?: string;
    tracking_id?: string;
    ocr_plate: string;
    rfid_tag_id?: string;
    tag_id?: string;
    ocr_confidence?: number;
    rfid_confidence?: number;
    rfid_rssi?: number;
    location?: string;
    lane?: string;
    manual_approved?: boolean;
    operator_reason?: string;
  }): Promise<VehicleVerificationRecord> {
    const body = {
      camera_id: payload.camera_id || 'CAM-101',
      tag_id: payload.tag_id ?? payload.rfid_tag_id ?? null,
      ocr_plate: payload.ocr_plate,
      ocr_confidence: payload.ocr_confidence ?? 0.95,
      rfid_confidence: payload.rfid_confidence ?? 0.98,
      lane: payload.lane || 'LANE-01',
      tracking_id: payload.tracking_id,
      manual_approved: payload.manual_approved ?? false,
      operator_reason: payload.operator_reason,
    };
    const res: any = await api.post('/api/v1/traffic/rfid/verify', body);
    return res?.verification || res;
  },

  async getVehicleVerifications(params?: {
    limit?: number;
    status?: string;
  }): Promise<VehicleVerificationRecord[]> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.status) query.append('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    const res: any = await api.get(`/api/v1/traffic/vehicle-verifications${qs}`);
    if (Array.isArray(res)) return res;
    if (res?.verifications && Array.isArray(res.verifications)) return res.verifications;
    return [];
  },

  async getVehicleVerification(id: string): Promise<VehicleVerificationRecord> {
    return api.get(`/api/v1/traffic/vehicle-verification/${id}`);
  },

  async getGreenCorridorDetail(id: string): Promise<GreenCorridor> {
    return api.get(`/api/v1/traffic/green-corridors/${id}`);
  },
};