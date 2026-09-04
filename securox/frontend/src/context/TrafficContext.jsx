import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './WebSocketContext';

const TrafficContext = createContext(null);

export const TrafficProvider = ({ children }) => {
  const { lastMessage } = useWebSocket();
  const [kpis, setKpis] = useState(null);
  const [roads, setRoads] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [activeView, setActiveView] = useState('command-center');
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [selectedRoadId, setSelectedRoadId] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchKpis = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8001/api/command-center/kpis');
      if (res.ok) {
        const data = await res.json();
        setKpis(data);
      }
    } catch (e) {}
  }, []);

  const fetchRoads = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8001/api/traffic/roads');
      if (res.ok) {
        const data = await res.json();
        setRoads(Array.isArray(data) ? data : (data.roads || []));
      }
    } catch (e) {}
  }, []);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8001/api/cameras');
      if (res.ok) {
        const data = await res.json();
        setCameras(Array.isArray(data) ? data : (data.cameras || []));
      }
    } catch (e) {}
  }, []);

  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8001/api/incidents');
      if (res.ok) {
        const data = await res.json();
        setIncidents(Array.isArray(data) ? data : (data.incidents || []));
      }
    } catch (e) {}
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8001/api/alerts');
      if (res.ok) {
        const data = await res.json();
        setAlerts(Array.isArray(data) ? data : (data.alerts || []));
      }
    } catch (e) {}
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchKpis(),
      fetchRoads(),
      fetchCameras(),
      fetchIncidents(),
      fetchAlerts()
    ]);
    setLoading(false);
  }, [fetchKpis, fetchRoads, fetchCameras, fetchIncidents, fetchAlerts]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 6000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  // Handle live WebSocket messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'TELEMETRY_TICK') {
      fetchKpis();
    } else if (lastMessage && lastMessage.type === 'NEW_EVENT') {
      fetchAlerts();
      fetchIncidents();
    }
  }, [lastMessage, fetchKpis, fetchAlerts, fetchIncidents]);

  return (
    <TrafficContext.Provider
      value={{
        kpis,
        roads,
        cameras,
        incidents,
        alerts,
        activeView,
        setActiveView,
        selectedIncidentId,
        setSelectedIncidentId,
        selectedCameraId,
        setSelectedCameraId,
        selectedRoadId,
        setSelectedRoadId,
        loading,
        refreshAll
      }}
    >
      {children}
    </TrafficContext.Provider>
  );
};

export const useTraffic = () => {
  const ctx = useContext(TrafficContext);
  if (!ctx) {
    return {
      kpis: null,
      roads: [],
      cameras: [],
      incidents: [],
      alerts: [],
      activeView: 'command-center',
      setActiveView: () => {},
      selectedIncidentId: null,
      setSelectedIncidentId: () => {},
      selectedCameraId: null,
      setSelectedCameraId: () => {},
      selectedRoadId: null,
      setSelectedRoadId: () => {},
      loading: false,
      refreshAll: () => {}
    };
  }
  return ctx;
};
