import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, Eye, ShieldAlert, Video, Sliders, Radio, AlertTriangle } from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const OperationalMap = ({ height = '520px', interactive = true, onSelectEntity }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef(null);
  const [mapError, setMapError] = useState(null);

  const { roads, cameras, incidents } = useTraffic();

  const safeRoads = Array.isArray(roads) ? roads : (roads?.roads || []);
  const safeCameras = Array.isArray(cameras) ? cameras : (cameras?.cameras || []);
  const safeIncidents = Array.isArray(incidents) ? incidents : (incidents?.incidents || []);

  const [layers, setLayers] = useState({
    trafficFlow: true,
    cameras: true,
    signals: true,
    cyberThreats: true
  });

  // Initialize Leaflet Map safely
  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container) return;

    try {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      if (container._leaflet_id) {
        delete container._leaflet_id;
      }

      // Centered around Bangalore-Hyderabad corridor (13.20, 77.61)
      const map = L.map(container, {
        center: [13.20, 77.61],
        zoom: 12,
        zoomControl: interactive,
        dragging: interactive,
        scrollWheelZoom: interactive ? 'center' : false,
        attributionControl: false
      });

      // Dark Matter CartoDB tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map);

      // Create and attach layer groups
      const roadGroup = L.layerGroup().addTo(map);
      const camGroup = L.layerGroup().addTo(map);
      const signalGroup = L.layerGroup().addTo(map);
      const threatGroup = L.layerGroup().addTo(map);

      layersRef.current = {
        roads: roadGroup,
        cameras: camGroup,
        signals: signalGroup,
        threats: threatGroup
      };

      mapInstanceRef.current = map;
      setMapError(null);
    } catch (err) {
      console.warn('[Leaflet] Map init error caught:', err);
      setMapError(err.message);
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {}
        mapInstanceRef.current = null;
      }
      if (container && container._leaflet_id) {
        delete container._leaflet_id;
      }
      layersRef.current = null;
    };
  }, [interactive]);

  // Update Road Polylines Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.roads) return;
    const roadLayer = layersRef.current.roads;
    roadLayer.clearLayers();

    if (!layers.trafficFlow) return;

    safeRoads.forEach(road => {
      if (!road.coordinates || road.coordinates.length < 2) return;

      let color = '#10b981'; // Green
      if (road.congestion_level === 'CRITICAL') color = '#991b1b';
      else if (road.congestion_level === 'SEVERE') color = '#ef4444';
      else if (road.congestion_level === 'HEAVY') color = '#f97316';
      else if (road.congestion_level === 'MODERATE') color = '#f59e0b';

      const polyline = L.polyline(road.coordinates, {
        color: color,
        weight: 6,
        opacity: 0.85,
        lineCap: 'round',
        lineJoin: 'round'
      });

      polyline.bindPopup(`
        <div style="background:#0f172a; color:#fff; padding:8px; border-radius:6px; font-family:sans-serif; font-size:12px; min-width:180px;">
          <strong style="color:#06b6d4;">${road.name}</strong><br/>
          <span style="color:#94a3b8;">Route: ${road.route_id} | ${road.lanes} Lanes</span><hr style="border-color:#334155; margin:6px 0;"/>
          <div>Current Speed: <strong>${road.current_speed_kmh} km/h</strong></div>
          <div>Volume: <strong>${road.current_volume} / ${road.capacity}</strong></div>
          <div>Congestion: <span style="color:${color}; font-weight:700;">${road.congestion_level}</span></div>
        </div>
      `);

      polyline.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'ROAD', data: road });
      });

      roadLayer.addLayer(polyline);
    });
  }, [safeRoads, layers.trafficFlow, onSelectEntity]);

  // Update Cameras Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.cameras) return;
    const camLayer = layersRef.current.cameras;
    camLayer.clearLayers();

    if (!layers.cameras) return;

    const CAM_COORDS = {
      'CAM-NH44-01': [13.125, 77.585],
      'CAM-NH44-02': [13.155, 77.595],
      'CAM-NH44-03': [13.185, 77.608],
      'CAM-NH44-04': [13.215, 77.620],
      'CAM-NH44-05': [13.250, 77.635],
      'CAM-URBAN-01': [13.205, 77.610],
      'CAM-URBAN-02': [13.208, 77.615],
      'CAM-TOLL-01': [13.182, 77.606],
    };

    safeCameras.forEach((cam, idx) => {
      const isOnline = cam.status === 'ONLINE';
      const isCompromised = cam.status === 'COMPROMISED';
      const pinColor = isCompromised ? '#ef4444' : (isOnline ? '#06b6d4' : '#64748b');

      const lat = cam.latitude ?? CAM_COORDS[cam.id]?.[0] ?? (13.125 + (idx % 6) * 0.03);
      const lng = cam.longitude ?? CAM_COORDS[cam.id]?.[1] ?? (77.585 + (idx % 6) * 0.015);
      if (typeof lat !== 'number' || typeof lng !== 'number' || isNaN(lat) || isNaN(lng)) return;

      const customIcon = L.divIcon({
        className: 'custom-cam-pin',
        html: `
          <div style="
            width: 22px; 
            height: 22px; 
            background: ${pinColor}; 
            border: 2px solid #fff; 
            border-radius: 50%; 
            box-shadow: 0 0 10px ${pinColor};
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 10px;
            font-weight: bold;
          ">
            📷
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      const marker = L.marker([lat, lng], { icon: customIcon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#fff; padding:8px; border-radius:6px; font-family:sans-serif; font-size:12px; min-width:180px;">
          <strong style="color:#06b6d4;">${cam.id} // ${cam.name}</strong><br/>
          <span style="color:#94a3b8;">Location: ${cam.location}</span><hr style="border-color:#334155; margin:6px 0;"/>
          <div>Status: <span style="font-weight:700; color:${isOnline ? '#34d399' : '#f87171'};">${cam.status}</span></div>
          <div>FPS: ${cam.fps || 30} | Latency: ${cam.latency_ms || 18}ms</div>
          <div>Active Vehicles: ${cam.vehicle_count || 12}</div>
          <div>Security Health: ${cam.security_health || 98}%</div>
        </div>
      `);

      marker.on('click', () => {
        if (onSelectEntity) onSelectEntity({ type: 'CAMERA', data: cam });
      });

      camLayer.addLayer(marker);
    });
  }, [safeCameras, layers.cameras, onSelectEntity]);

  // Update Cyber Threats & Critical Incident Breach Rings
  useEffect(() => {
    if (!mapInstanceRef.current || !layersRef.current?.threats) return;
    const threatLayer = layersRef.current.threats;
    threatLayer.clearLayers();

    if (!layers.cyberThreats) return;

    // Show pulsing breach ring at critical incident location
    const criticalIncidents = safeIncidents.filter(i => i.severity === 'CRITICAL' && i.status !== 'RESOLVED');
    criticalIncidents.forEach(inc => {
      const lat = 13.205;
      const lng = 77.610;

      const circle = L.circle([lat, lng], {
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.25,
        radius: 650,
        weight: 2
      });

      const pulseIcon = L.divIcon({
        className: 'cyber-breach-pulse',
        html: `
          <div style="
            width: 28px; 
            height: 28px; 
            background: rgba(239, 68, 68, 0.3); 
            border: 2px solid #ef4444; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            box-shadow: 0 0 15px #ef4444;
          ">
            ⚠️
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const marker = L.marker([lat, lng], { icon: pulseIcon });
      marker.bindPopup(`
        <div style="background:#0f172a; color:#fff; padding:8px; border-radius:6px; font-family:sans-serif; font-size:12px; min-width:200px;">
          <strong style="color:#ef4444;">CYBER-PHYSICAL INCIDENT DETECTED</strong><br/>
          <span style="color:#fff; font-weight:600;">${inc.title}</span><hr style="border-color:#334155; margin:6px 0;"/>
          <div>Location: ${inc.location}</div>
          <div>Risk Score: <strong style="color:#ef4444;">${inc.risk_score} / 100</strong></div>
          <div>Verdict: <strong style="color:#f97316;">CONFIRMED</strong></div>
        </div>
      `);

      threatLayer.addLayer(circle);
      threatLayer.addLayer(marker);
    });
  }, [safeIncidents, layers.cyberThreats]);

  const toggleLayer = (key) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: height, borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
      {/* Map Layer Controls Bar */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '12px',
        zIndex: 1000,
        background: 'rgba(15, 23, 42, 0.88)',
        backdropFilter: 'blur(6px)',
        border: '1px solid var(--border-medium)',
        borderRadius: '6px',
        padding: '6px 10px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        boxShadow: 'var(--shadow-md)'
      }}>
        <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Layers size={13} /> LAYERS:
        </span>
        <button
          className={`btn btn-sm ${layers.trafficFlow ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => toggleLayer('trafficFlow')}
          style={{ fontSize: '11px', padding: '3px 8px' }}
        >
          Traffic Flow
        </button>
        <button
          className={`btn btn-sm ${layers.cameras ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => toggleLayer('cameras')}
          style={{ fontSize: '11px', padding: '3px 8px' }}
        >
          Cameras
        </button>
        <button
          className={`btn btn-sm ${layers.cyberThreats ? 'btn-danger' : 'btn-outline'}`}
          onClick={() => toggleLayer('cyberThreats')}
          style={{ fontSize: '11px', padding: '3px 8px' }}
        >
          Cyber Threats
        </button>
      </div>

      {/* Map Canvas Container */}
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', background: '#070b14' }} />
    </div>
  );
};
