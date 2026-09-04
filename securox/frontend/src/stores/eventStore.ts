import { wsClient } from '../services/websocket';
import { Alert, Incident, CityRiskMetric } from '../types/soc';

interface EventState {
  isConnected: boolean;
  alerts: Alert[];
  incidents: Incident[];
  cityRisk: number; // 0 - 100
  activeThreatCount: number;
  lastEventTimestamp: string;
}

let state: EventState = {
  isConnected: false,
  alerts: [],
  incidents: [],
  cityRisk: 28.5,
  activeThreatCount: 3,
  lastEventTimestamp: new Date().toISOString(),
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

let initialized = false;

export const eventStore = {
  getState(): EventState {
    return state;
  },

  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  init(): void {
    if (initialized) return;
    initialized = true;

    wsClient.connect();

    wsClient.on('_status', (payload: { connected: boolean }) => {
      state = { ...state, isConnected: payload.connected };
      notify();
    });

    wsClient.on('alert', (alert: Alert) => {
      state = {
        ...state,
        alerts: [alert, ...state.alerts.slice(0, 99)],
        lastEventTimestamp: new Date().toISOString(),
      };
      notify();
    });

    wsClient.on('risk_update', (data: any) => {
      const risk = data.city_score ?? data.risk_score ?? state.cityRisk;
      state = {
        ...state,
        cityRisk: Math.round(risk * 10) / 10,
        lastEventTimestamp: new Date().toISOString(),
      };
      notify();
    });

    wsClient.on('incident_update', (incident: Incident) => {
      const existingIdx = state.incidents.findIndex((i) => i.id === incident.id);
      let updated: Incident[];
      if (existingIdx >= 0) {
        updated = [...state.incidents];
        updated[existingIdx] = incident;
      } else {
        updated = [incident, ...state.incidents];
      }
      state = {
        ...state,
        incidents: updated,
        lastEventTimestamp: new Date().toISOString(),
      };
      notify();
    });
  },

  setAlerts(alerts: Alert[]): void {
    state = { ...state, alerts };
    notify();
  },

  setIncidents(incidents: Incident[]): void {
    state = { ...state, incidents };
    notify();
  },

  setCityRisk(risk: number): void {
    state = { ...state, cityRisk: risk };
    notify();
  },
};
