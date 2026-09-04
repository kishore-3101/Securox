import React, { useState } from 'react';
import { Video, ShieldCheck, AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const CamerasView = () => {
  const { cameras, setActiveView, setSelectedCameraId } = useTraffic();
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filteredCameras = cameras.filter(c => {
    if (filterStatus === 'ALL') return true;
    return c.status === filterStatus;
  });

  const handleInspectCamera = (camId) => {
    setSelectedCameraId(camId);
    setActiveView('camera-detail');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>CAMERA INTELLIGENCE & COMPUTER VISION MATRIX</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Real-time surveillance feeds, optical health, and network security integrity</p>
        </div>

        {/* Filter Buttons */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {['ALL', 'ONLINE', 'DEGRADED', 'OFFLINE', 'COMPROMISED'].map(status => (
            <button
              key={status}
              className={`btn btn-sm ${filterStatus === status ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilterStatus(status)}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Camera Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
        {filteredCameras.map(cam => (
          <div 
            key={cam.id} 
            className="soc-card"
            style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan-accent)' }}>
                  {cam.id}
                </span>
                <SeverityBadge 
                  severity={cam.status === 'ONLINE' ? 'SUCCESS' : (cam.status === 'COMPROMISED' ? 'CRITICAL' : 'HIGH')} 
                  text={cam.status}
                />
              </div>

              <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
                {cam.name}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginBottom: '12px' }}>
                📍 {cam.location}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', background: 'var(--bg-surface)', padding: '8px 10px', borderRadius: '4px', fontSize: '11px', color: 'var(--text-muted)' }}>
                <div>FPS: <strong style={{ color: '#fff' }}>{cam.fps}</strong></div>
                <div>Latency: <strong style={{ color: '#fff' }}>{cam.latency_ms} ms</strong></div>
                <div>Vehicles: <strong style={{ color: '#fff' }}>{cam.vehicle_count}</strong></div>
                <div>Security: <strong style={{ color: cam.security_health > 90 ? '#34d399' : '#f87171' }}>{cam.security_health}%</strong></div>
              </div>
            </div>

            <button 
              className="btn btn-outline btn-sm"
              onClick={() => handleInspectCamera(cam.id)}
              style={{ marginTop: '12px', width: '100%', justifyContent: 'space-between' }}
            >
              <span>View HUD Feed & CV Telemetry</span>
              <ArrowRight size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
