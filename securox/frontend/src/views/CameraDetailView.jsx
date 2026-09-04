import React, { useState, useEffect } from 'react';
import { Video, Shield, ArrowLeft, RefreshCw, AlertTriangle, Play } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const CameraDetailView = () => {
  const { selectedCameraId, setActiveView } = useTraffic();
  const camId = selectedCameraId || 'CAM-01';

  const [cameraData, setCameraData] = useState(null);
  const [liveImage, setLiveImage] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const fetchFrame = async () => {
    try {
      const res = await fetch(`http://localhost:8001/api/cameras/${camId}/live-frame`);
      if (res.ok) {
        const data = await res.json();
        setLiveImage(data.image_base64);
      }
    } catch (e) {}
  };

  const fetchDetails = async () => {
    try {
      const res = await fetch(`http://localhost:8001/api/cameras/${camId}`);
      if (res.ok) {
        const data = await res.json();
        setCameraData(data);
      }
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchDetails();
    fetchFrame();

    let interval = null;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchFrame();
        fetchDetails();
      }, 1800);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [camId, autoRefresh]);

  const handleInjectBehavior = async (behavior) => {
    try {
      setActionMsg(`Injecting ${behavior}...`);
      const res = await fetch(`http://localhost:8001/api/cameras/${camId}/inject-behavior`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ behavior })
      });
      if (res.ok) {
        setActionMsg(`Behavior '${behavior}' injected successfully. New event logged.`);
        fetchFrame();
        fetchDetails();
      }
    } catch (e) {
      setActionMsg('Failed to inject behavior.');
    }
  };

  const cam = cameraData?.camera;
  const tracks = cameraData?.tracked_vehicles || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top bar with back button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn btn-outline btn-sm" onClick={() => setActiveView('cameras')}>
            <ArrowLeft size={14} /> Back to Cameras
          </button>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              {cam?.name || `Camera ${camId}`} <span style={{ color: 'var(--cyan-accent)' }}>({camId})</span>
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>📍 {cam?.location || 'Highway Sector'}</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            className={`btn btn-sm ${autoRefresh ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw size={12} className={autoRefresh ? 'pulse-icon' : ''} />
            {autoRefresh ? 'Auto-Streaming (1.8s)' : 'Paused'}
          </button>
          <div className="sim-badge">DEMO / SIMULATED FEED</div>
        </div>
      </div>

      {actionMsg && (
        <div style={{ padding: '8px 12px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid var(--border-accent)', borderRadius: '4px', fontSize: '12px', color: '#38bdf8' }}>
          {actionMsg}
        </div>
      )}

      {/* Main Content Layout: Live Frame Left & Telemetry Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '20px' }}>
        {/* Left: Live HUD Feed */}
        <div className="soc-card" style={{ padding: '12px' }}>
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Video size={15} color="var(--cyan-accent)" />
              LIVE COMPUTER VISION HUD STREAM
            </div>
            <SeverityBadge 
              severity={cam?.status === 'ONLINE' ? 'SUCCESS' : 'CRITICAL'} 
              text={cam?.status || 'ONLINE'} 
            />
          </div>

          <div style={{ 
            width: '100%', 
            minHeight: '360px', 
            background: '#070b14', 
            borderRadius: '6px', 
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid var(--border-subtle)'
          }}>
            {liveImage ? (
              <img 
                src={liveImage} 
                alt="Camera HUD Stream" 
                style={{ width: '100%', height: 'auto', display: 'block' }}
              />
            ) : (
              <div style={{ color: 'var(--text-dim)', fontSize: '13px' }}>Loading HUD Stream...</div>
            )}
          </div>

          {/* Behavior Anomaly Injection Controls */}
          <div style={{ marginTop: '14px', background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
              ⚡ Interactive Behavior Anomaly Injector (SOC Realism Demonstration):
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button className="btn btn-outline btn-sm" onClick={() => handleInjectBehavior('STOPPED_VEHICLE')}>
                🚨 Stopped Vehicle
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => handleInjectBehavior('WRONG_WAY')}>
                ⚠️ Wrong-Way Driving
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => handleInjectBehavior('SUDDEN_BRAKING')}>
                🛑 Sudden Braking
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => handleInjectBehavior('ACCIDENT_LIKE')}>
                💥 Collision / Hazard
              </button>
            </div>
          </div>
        </div>

        {/* Right: Camera Health & Tracked Objects List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Health Telemetry */}
          <div className="soc-card">
            <div className="soc-card-header">
              <div className="soc-card-title">
                <Shield size={15} color="var(--cyan-accent)" />
                HARDWARE & NETWORK TELEMETRY
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
              <div style={{ background: 'var(--bg-surface)', padding: '8px', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '10.5px' }}>STREAM FPS</span>
                <strong style={{ color: '#fff' }}>{cam?.fps} FPS</strong>
              </div>
              <div style={{ background: 'var(--bg-surface)', padding: '8px', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '10.5px' }}>ROUND-TRIP LATENCY</span>
                <strong style={{ color: '#fff' }}>{cam?.latency_ms} ms</strong>
              </div>
              <div style={{ background: 'var(--bg-surface)', padding: '8px', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '10.5px' }}>OPTICAL RESOLUTION</span>
                <strong style={{ color: '#fff' }}>{cam?.resolution || '1920x1080'}</strong>
              </div>
              <div style={{ background: 'var(--bg-surface)', padding: '8px', borderRadius: '4px' }}>
                <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '10.5px' }}>SECURITY INTEGRITY</span>
                <strong style={{ color: cam?.security_health > 90 ? '#34d399' : '#ef4444' }}>{cam?.security_health}%</strong>
              </div>
            </div>
          </div>

          {/* Active Tracked Vehicles in Field-of-View */}
          <div className="soc-card" style={{ flex: 1 }}>
            <div className="soc-card-header">
              <div className="soc-card-title">
                TRACKED VEHICLES IN SCENE ({tracks.length})
              </div>
            </div>

            <div className="soc-table-container" style={{ maxHeight: '250px' }}>
              <table className="soc-table">
                <thead>
                  <tr>
                    <th>Track ID</th>
                    <th>Class</th>
                    <th>Speed</th>
                    <th>Lane</th>
                    <th>Plate</th>
                    <th>Behavior</th>
                  </tr>
                </thead>
                <tbody>
                  {tracks.map(t => (
                    <tr key={t.track_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)' }}>{t.track_id}</td>
                      <td>{t.vehicle_type}</td>
                      <td>{t.speed.toFixed(0)} km/h</td>
                      <td>Lane {t.lane}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{t.license_plate}</td>
                      <td>
                        <span style={{ 
                          fontSize: '10.5px', 
                          fontWeight: 600,
                          color: t.behavior === 'NORMAL_FLOW' ? '#34d399' : '#ef4444'
                        }}>
                          {t.behavior}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
