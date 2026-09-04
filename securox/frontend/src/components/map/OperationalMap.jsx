import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, ShieldAlert, Video, Radio, Ambulance as AmbulanceIcon, RefreshCw, CreditCard } from 'lucide-react';



const CARTO_API_KEY = "cb1_2xfg_1_792bddf56d1033d79bd5ff20";



const DEFAULT_SIGNALS = [
  { id: 'SIG-01', name: 'Silk Board Junction Hub', current_phase: 'GREEN', mode: 'ADAPTIVE', intersection_id: 'J-101', latitude: 12.9176, longitude: 77.6238 },
  { id: 'SIG-02', name: 'Dairy Circle Coordinated Hub', current_phase: 'RED', mode: 'COORDINATED', intersection_id: 'J-102', latitude: 12.9385, longitude: 77.5960 },
  { id: 'SIG-03', name: 'Town Hall Safety Override', current_phase: 'YELLOW', mode: 'SAFETY_OVERRIDE', intersection_id: 'J-103', latitude: 12.9678, longitude: 77.5872 },
  { id: 'SIG-04', name: 'Majestic Central Terminus', current_phase: 'GREEN', mode: 'ADAPTIVE', intersection_id: 'J-104', latitude: 12.9779, longitude: 77.5724 },
  { id: 'SIG-05', name: 'Indiranagar 100ft Radial', current_phase: 'GREEN', mode: 'ADAPTIVE', intersection_id: 'J-105', latitude: 12.9784, longitude: 77.6408 },
  { id: 'SIG-06', name: 'Hebbal Flyover North Axis', current_phase: 'RED', mode: 'ADAPTIVE', intersection_id: 'J-106', latitude: 13.0358, longitude: 77.5970 },
];

const DEFAULT_CAMERAS = [
  { id: 'CAM-101', name: 'Silk Board Gantry CCTV & ANPR', location: 'Silk Board Junction', status: 'ONLINE', stream_type: 'WEBRTC', fps: 15, vehicles_detected: 42, latitude: 12.9176, longitude: 77.6238 },
  { id: 'CAM-102', name: 'Hosur Road Toll Gantry Alpha', location: 'Toll Plaza Gantry Alpha - Lane 1', status: 'ONLINE', stream_type: 'WEBRTC', fps: 20, vehicles_detected: 35, latitude: 12.8450, longitude: 77.6600 },
  { id: 'CAM-105', name: 'Town Hall Approach Camera', location: 'Town Hall North Axis', status: 'ONLINE', stream_type: 'WEBRTC', fps: 12, vehicles_detected: 18, latitude: 12.9678, longitude: 77.5872 },
  { id: 'CAM-108', name: 'Majestic Terminal Surveillance', location: 'Majestic Hub Radial', status: 'ONLINE', stream_type: 'WEBRTC', fps: 15, vehicles_detected: 56, latitude: 12.9779, longitude: 77.5724 },
  { id: 'CAM-109', name: 'Indiranagar Metro Axis CCTV', location: '100ft Road Radial', status: 'ONLINE', stream_type: 'WEBRTC', fps: 15, vehicles_detected: 27, latitude: 12.9784, longitude: 77.6408 },
];

const DEFAULT_TOLLS = [
  { id: 'TOLL-01', name: 'Toll Plaza Gantry Alpha (Electronic City)', location: 'Hosur Elevated Expressway - Lane 1', status: 'ONLINE', camera_id: 'CAM-101', reader_id: 'RFID-READER-01', barrier: 'OPERATIONAL', latitude: 12.8450, longitude: 77.6600 },
  { id: 'TOLL-02', name: 'Hebbal Airport Express Tollway', location: 'Bellary Road North Radial - Lane 2', status: 'ONLINE', camera_id: 'CAM-01', reader_id: 'RFID-READER-02', barrier: 'OPERATIONAL', latitude: 13.0450, longitude: 77.5950 },
];

const DEFAULT_AMBULANCES = [
  { id: 'CAD-AMB-01', call_sign: 'MEDIC-ONE (CAD-108)', status: 'EN_ROUTE', priority: 'CODE_RED', eta_minutes: 4, assigned_hospital: 'City General Hospital', latitude: 12.9420, longitude: 77.6080 },
  { id: 'CAD-AMB-02', call_sign: 'TRAUMA-ALPHA', status: 'DISPATCHED', priority: 'CODE_AMBER', eta_minutes: 8, assigned_hospital: 'Apollo Specialty Center', latitude: 12.9810, longitude: 77.6320 },
];

const DEFAULT_INCIDENTS = [
  { id: 'INC-101', title: 'Rear-End Collision Obstruction', category: 'COLLISION', severity: 'MEDIUM', location: 'Hosur Road Corridor near Toll Alpha', latitude: 12.8620, longitude: 77.6510 },
  { id: 'INC-102', title: 'Construction Vehicle Lane Block', category: 'ROADWORK', severity: 'LOW', location: 'Outer Ring Road Silk Board Ramp', latitude: 12.9190, longitude: 77.6290 },
];

export const OperationalMap = ({
  height = '500px',
  interactive = true,
  signals = [],
  cameras = [],
  ambulances = [],
  incidents = [],
  onSelectEntity,
}) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef(null);

  const [layers, setLayers] = useState({
    signals: true,
    cameras: true,
    tolls: true,
    ambulances: true,
    incidents: true,
  });

  const DEFAULT_CENTER = [12.955, 77.605];

  // Initialize Leaflet Map
  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(container, {
      center: DEFAULT_CENTER,
      zoom: 12,
      zoomControl: interactive,
      dragging: interactive,
      scrollWheelZoom: interactive ? 'center' : false,
      attributionControl: false,
    });

    const tileUrl = `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_API_KEY}`;
    const tileLayer = L.tileLayer(tileUrl, {
      maxZoom: 19,
      subdomains: 'abcd',
    });

    tileLayer.on('tileerror', () => {
      console.warn('[Leaflet] Carto tile load warning, maintaining cached layer');
    });

    tileLayer.addTo(map);

    const signalGroup = L.layerGroup().addTo(map);
    const cameraGroup = L.layerGroup().addTo(map);
    const tollGroup = L.layerGroup().addTo(map);
    const ambulanceGroup = L.layerGroup().addTo(map);
    const incidentGroup = L.layerGroup().addTo(map);

    layersRef.current = {
      signals: signalGroup,
      cameras: cameraGroup,
      tolls: tollGroup,
      ambulances: ambulanceGroup,
      incidents: incidentGroup,
    };

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      layersRef.current = null;
    };
  }, [interactive]);

  // Update Signals Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.signals) return;
    const group = layersRef.current.signals;
    group.clearLayers();

    if (!layers.signals) return;

    const activeList = signals.length > 0 ? signals : DEFAULT_SIGNALS;

    activeList.forEach((sig, idx) => {
      const lat = (sig ).latitude || (12.92 + (idx % 5) * 0.025);
      const lng = (sig ).longitude || (77.58 + (idx % 5) * 0.02);
      const phase = ((sig ).current_phase || (sig ).current_state || 'GREEN').toUpperCase();
      const color = phase === 'RED' ? '#ef4444' : phase === 'YELLOW' ? '#f59e0b' : '#10b981';

      const icon = L.divIcon({
        className: 'custom-signal-icon',
        html: `
          <div style="
            width: 26px; height: 26px;
            background: #0f172a;
            border: 2.5px solid ${color};
            box-shadow: 0 0 12px ${color};
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: ${color}; font-size: 11px; font-weight: bold;
            cursor: pointer;
          ">
            🚦
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([lat, lng], { icon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; font-family:monospace; font-size:12px; border:1px solid ${color};">
          <strong style="color:${color}; font-size:13px;">${sig.name || sig.id}</strong><br/>
          <span>Current Phase: <b style="color:${color};">${phase}</b></span><br/>
          <span>Operational Mode: ${(sig ).mode || 'ADAPTIVE'}</span><br/>
          <span>Junction ID: ${(sig ).intersection_id || 'J-101'}</span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'SIGNAL', data: sig });
      });

      group.addLayer(marker);
    });
  }, [signals, layers.signals, onSelectEntity]);

  // Update Cameras Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.cameras) return;
    const group = layersRef.current.cameras;
    group.clearLayers();

    if (!layers.cameras) return;

    const activeList = cameras.length > 0 ? cameras : DEFAULT_CAMERAS;

    activeList.forEach((cam, idx) => {
      const lat = (cam ).latitude || (12.925 + (idx % 5) * 0.018);
      const lng = (cam ).longitude || (77.585 + (idx % 5) * 0.015);
      const isOnline = cam.status === 'ONLINE';
      const color = isOnline ? '#38bdf8' : '#f87171';

      const icon = L.divIcon({
        className: 'custom-cam-icon',
        html: `
          <div style="
            width: 24px; height: 24px;
            background: #0f172a;
            border: 2px solid ${color};
            box-shadow: 0 0 10px ${color};
            border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px;
            cursor: pointer;
          ">
            📷
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([lat, lng], { icon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; font-family:monospace; font-size:12px; border:1px solid ${color};">
          <strong style="color:#38bdf8; font-size:13px;">${cam.name || cam.id}</strong><br/>
          <span>Location: ${cam.location || 'Metro Radial Sector'}</span><br/>
          <span>Status: <b style="color:${color};">${cam.status}</b></span><br/>
          <span>Stream: ${(cam ).stream_type || 'WEBRTC'} @ ${(cam ).fps || 15} FPS</span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'CAMERA', data: cam });
      });

      group.addLayer(marker);
    });
  }, [cameras, layers.cameras, onSelectEntity]);

  // Update Toll Gantries Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.tolls) return;
    const group = layersRef.current.tolls;
    group.clearLayers();

    if (!layers.tolls) return;

    DEFAULT_TOLLS.forEach((toll) => {
      const icon = L.divIcon({
        className: 'custom-toll-icon',
        html: `
          <div style="
            width: 26px; height: 26px;
            background: #064e3b;
            border: 2px solid #34d399;
            box-shadow: 0 0 12px #34d399;
            border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            color: #34d399; font-size: 12px;
            cursor: pointer;
          ">
            💳
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([toll.latitude, toll.longitude], { icon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; font-family:monospace; font-size:12px; border:1px solid #34d399;">
          <strong style="color:#34d399; font-size:13px;">TOLL GANTRY: ${toll.name}</strong><br/>
          <span>Location: ${toll.location}</span><br/>
          <span>Optical ANPR: <b>${toll.camera_id}</b></span><br/>
          <span>RFID Reader: <b>${toll.reader_id}</b></span><br/>
          <span>Boom Barrier: <b style="color:#10b981;">${toll.barrier}</b></span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'TOLL', data: toll });
      });

      group.addLayer(marker);
    });
  }, [layers.tolls, onSelectEntity]);

  // Update Ambulances Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.ambulances) return;
    const group = layersRef.current.ambulances;
    group.clearLayers();

    if (!layers.ambulances) return;

    const activeList = ambulances.length > 0 ? ambulances : DEFAULT_AMBULANCES;

    activeList.forEach((amb, idx) => {
      const lat = (amb ).latitude || (12.94 + (idx % 2) * 0.035);
      const lng = (amb ).longitude || (77.60 + (idx % 2) * 0.025);

      const icon = L.divIcon({
        className: 'custom-amb-icon',
        html: `
          <div style="
            width: 26px; height: 26px;
            background: #881337;
            border: 2px solid #f43f5e;
            box-shadow: 0 0 12px #f43f5e;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-size: 11px;
            cursor: pointer;
            animation: pulse 1.5s infinite;
          ">
            🚑
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([lat, lng], { icon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; font-family:monospace; font-size:12px; border:1px solid #e11d48;">
          <strong style="color:#f43f5e; font-size:13px;">EMERGENCY CAD: ${amb.call_sign}</strong><br/>
          <span>Status: <b style="color:#10b981;">${amb.status}</b></span><br/>
          <span>Priority: <b>${amb.priority}</b></span><br/>
          <span>Corridor ETA: <b>${amb.eta_minutes} min</b></span><br/>
          <span>Target Hospital: ${amb.assigned_hospital}</span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'AMBULANCE', data: amb });
      });

      group.addLayer(marker);
    });
  }, [ambulances, layers.ambulances, onSelectEntity]);

  // Update Incidents Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.incidents) return;
    const group = layersRef.current.incidents;
    group.clearLayers();

    if (!layers.incidents) return;

    const activeList = incidents.length > 0 ? incidents : DEFAULT_INCIDENTS;

    activeList.forEach((inc, idx) => {
      const lat = (inc ).latitude || (12.86 + (idx % 3) * 0.03);
      const lng = (inc ).longitude || (77.65 + (idx % 3) * 0.015);

      const icon = L.divIcon({
        className: 'custom-inc-icon',
        html: `
          <div style="
            width: 24px; height: 24px;
            background: #b45309;
            border: 2px solid #fbbf24;
            box-shadow: 0 0 10px #fbbf24;
            border-radius: 6px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px;
            cursor: pointer;
          ">
            ⚠️
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const marker = L.marker([lat, lng], { icon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#f8fafc; padding:10px; border-radius:8px; font-family:monospace; font-size:12px; border:1px solid #fbbf24;">
          <strong style="color:#fbbf24; font-size:13px;">${inc.title || 'Traffic Incident'}</strong><br/>
          <span>Category: ${inc.category || 'COLLISION'}</span><br/>
          <span>Severity: <b style="color:#ef4444;">${inc.severity || 'HIGH'}</b></span><br/>
          <span>Location: ${inc.location || 'Metro Radial Sector'}</span>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'INCIDENT', data: inc });
      });

      group.addLayer(marker);
    });
  }, [incidents, layers.incidents, onSelectEntity]);

  const resetView = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(DEFAULT_CENTER, 12);
    }
  };

  return (
    <div className="relative font-mono text-xs rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
      {/* Top Floating Control Bar */}
      <div className="absolute top-3 left-3 z-[1000] flex items-center gap-2 bg-slate-900/90 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-800 shadow-xl">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <span className="font-bold text-slate-200">CARTO Dark Matter Live Feed</span>
        <span className="text-[10px] text-slate-400 hidden sm:inline">| Bangalore Urban Grid (12.955°N, 77.605°E)</span>
      </div>

      {/* Layer Toggles & Reset Controls */}
      <div className="absolute top-3 right-3 z-[1000] flex items-center gap-1.5 bg-slate-900/90 backdrop-blur p-1 rounded-lg border border-slate-800 shadow-xl">
        <button
          onClick={() => setLayers((l) => ({ ...l, signals: !l.signals }))}
          className={`px-2 py-1 rounded text-[10px] font-bold transition ${
            layers.signals ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Signals
        </button>
        <button
          onClick={() => setLayers((l) => ({ ...l, cameras: !l.cameras }))}
          className={`px-2 py-1 rounded text-[10px] font-bold transition ${
            layers.cameras ? 'bg-sky-950 text-sky-300 border border-sky-700' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          CCTVs
        </button>
        <button
          onClick={() => setLayers((l) => ({ ...l, tolls: !l.tolls }))}
          className={`px-2 py-1 rounded text-[10px] font-bold transition ${
            layers.tolls ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Toll Gantries
        </button>
        <button
          onClick={() => setLayers((l) => ({ ...l, ambulances: !l.ambulances }))}
          className={`px-2 py-1 rounded text-[10px] font-bold transition ${
            layers.ambulances ? 'bg-rose-950 text-rose-300 border border-rose-700' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Ambulances
        </button>
        <button
          onClick={() => setLayers((l) => ({ ...l, incidents: !l.incidents }))}
          className={`px-2 py-1 rounded text-[10px] font-bold transition ${
            layers.incidents ? 'bg-amber-950 text-amber-300 border border-amber-700' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          Incidents
        </button>
        <button
          onClick={resetView}
          title="Reset View"
          className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Map Container */}
      <div ref={mapContainerRef} style={{ height, width: '100%' }} />
    </div>
  );
};
