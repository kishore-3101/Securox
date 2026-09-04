import React from 'react';
import { 
  Activity, Video, AlertTriangle, Shield, Radio, ArrowRight,
  Play, Compass, Cpu, TrendingUp, AlertCircle
} from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { KpiCard } from '../components/common/KpiCard';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { OperationalMap } from '../components/map/OperationalMap';

export const CommandCenterView = () => {
  const { kpis, incidents, cameras, roads, setActiveView, setSelectedIncidentId, setSelectedCameraId } = useTraffic();

  const handleOpenIncident = (incId) => {
    setSelectedIncidentId(incId);
    setActiveView('incident-detail');
  };

  const handleOpenCam = (camId) => {
    setSelectedCameraId(camId);
    setActiveView('camera-detail');
  };

  const riskFactors = kpis?.risk_score?.factors || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Section: Header & Quick Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#fff' }}>
            SECUROX TRAFFIC SECURITY COMMAND CENTER
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Integrated Real-Time Physical Traffic Operations + Cyber-Physical Threat Monitoring
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            className="btn btn-primary"
            onClick={() => setActiveView('simulator')}
            style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: '#000', fontWeight: 700 }}
          >
            <Play size={14} /> SCENARIO SIMULATOR
          </button>
          <button 
            className="btn btn-outline"
            onClick={() => setActiveView('ai-assistant')}
          >
            <Cpu size={14} /> AI ASSISTANT
          </button>
        </div>
      </div>

      {/* Top-Level KPIs Grid (Requirement 3) */}
      <div className="soc-kpi-grid">
        <KpiCard
          title="ACTIVE CAMERAS"
          value={kpis?.active_cameras?.online ?? 8}
          unit={`/ ${kpis?.active_cameras?.value ?? 8}`}
          trend={kpis?.active_cameras?.trend ?? "STABLE"}
          severity={kpis?.active_cameras?.offline > 0 ? "HIGH" : "LOW"}
          icon={Video}
          onClick={() => setActiveView('cameras')}
        />
        <KpiCard
          title="TOTAL VEHICLES"
          value={kpis?.total_vehicles?.value ?? 1240}
          unit="veh/hr"
          trend={kpis?.total_vehicles?.trend ?? "+8.4%"}
          comparison="vs baseline"
          severity="INFO"
          icon={Radio}
          onClick={() => setActiveView('live-traffic')}
        />
        <KpiCard
          title="TRAFFIC DENSITY"
          value={kpis?.traffic_density?.value ?? 45.0}
          unit="%"
          trend={kpis?.traffic_density?.trend ?? "+4.2%"}
          severity={kpis?.traffic_density?.severity ?? "MEDIUM"}
          icon={Activity}
          onClick={() => setActiveView('roads')}
        />
        <KpiCard
          title="AVERAGE SPEED"
          value={kpis?.average_speed?.value ?? 74.5}
          unit="km/h"
          trend={kpis?.average_speed?.trend ?? "-3.1%"}
          severity={kpis?.average_speed?.severity ?? "INFO"}
          icon={TrendingUp}
          onClick={() => setActiveView('roads')}
        />
        <KpiCard
          title="ACTIVE INCIDENTS"
          value={kpis?.active_incidents?.value ?? 1}
          unit={`(${kpis?.active_incidents?.critical ?? 0} Crit)`}
          trend={kpis?.active_incidents?.trend ?? "+1"}
          severity={kpis?.active_incidents?.critical > 0 ? "CRITICAL" : "MEDIUM"}
          icon={AlertTriangle}
          onClick={() => setActiveView('incidents')}
        />
        <KpiCard
          title="CYBER THREATS"
          value={kpis?.cyber_threats?.value ?? 0}
          trend={kpis?.cyber_threats?.trend ?? "NOMINAL"}
          severity={kpis?.cyber_threats?.value > 0 ? "HIGH" : "INFO"}
          icon={Shield}
          onClick={() => setActiveView('cyber-center')}
        />
      </div>

      {/* Main Command Center Grid: Left Map & Right Alert Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Left: Operational Map */}
        <div className="soc-card" style={{ padding: '14px' }}>
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Compass size={15} color="var(--cyan-accent)" />
              LIVE OPERATIONAL MAP // NH44 CORRIDOR & URBAN SECTOR
            </div>
            <button 
              className="btn btn-outline btn-sm" 
              onClick={() => setActiveView('traffic-map')}
            >
              Full Screen Map <ArrowRight size={12} />
            </button>
          </div>
          <OperationalMap height="460px" onSelectEntity={(ent) => {
            if (ent.type === 'CAMERA') handleOpenCam(ent.data.id);
          }} />
        </div>

        {/* Right: Active Incidents & Threat Breakdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Incident Stream Card */}
          <div className="soc-card" style={{ flex: 1 }}>
            <div className="soc-card-header">
              <div className="soc-card-title">
                <AlertTriangle size={15} color="#ef4444" />
                ACTIVE INCIDENTS
              </div>
              <button 
                className="btn btn-outline btn-sm"
                onClick={() => setActiveView('incidents')}
              >
                View All
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {incidents.length === 0 ? (
                <div style={{ color: 'var(--text-dim)', fontSize: '12px', padding: '12px', textAlign: 'center' }}>
                  No active incidents flagged.
                </div>
              ) : (
                incidents.slice(0, 4).map(inc => (
                  <div
                    key={inc.incident_id}
                    onClick={() => handleOpenIncident(inc.incident_id)}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      padding: '10px',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)' }}>
                        {inc.incident_id}
                      </span>
                      <SeverityBadge severity={inc.severity} />
                    </div>
                    <div style={{ fontSize: '12.5px', fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
                      {inc.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      📍 {inc.location} | Status: <strong style={{ color: '#38bdf8' }}>{inc.status}</strong>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Explainable Risk Attribution Card (Requirement 19 & 28) */}
          <div className="soc-card">
            <div className="soc-card-header">
              <div className="soc-card-title">
                <Shield size={15} color="var(--amber)" />
                EXPLAINABLE RISK ATTRIBUTION
              </div>
              <span className={`badge badge-${kpis?.risk_score?.severity?.toLowerCase() || 'low'}`}>
                {kpis?.risk_score?.value?.toFixed(0) || 14} / 100
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {riskFactors.length === 0 ? (
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  All systems operating within baseline parameters.
                </p>
              ) : (
                riskFactors.map((f, i) => (
                  <div key={i} style={{ fontSize: '11.5px', background: 'var(--bg-surface)', padding: '8px 10px', borderRadius: '4px', borderLeft: '3px solid #f59e0b' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: '#fff' }}>
                      <span>{f.name}</span>
                      <span style={{ color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>+{f.impact}</span>
                    </div>
                    <div style={{ fontSize: '10.5px', color: 'var(--text-dim)', marginTop: '2px' }}>
                      {f.description}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Optical Camera Matrix Preview */}
      <div className="soc-card">
        <div className="soc-card-header">
          <div className="soc-card-title">
            <Video size={15} color="var(--cyan-accent)" />
            OPTICAL SURVEILLANCE & COMPUTER VISION MATRIX
          </div>
          <button className="btn btn-outline btn-sm" onClick={() => setActiveView('cameras')}>
            Open All Feeds
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
          {cameras.slice(0, 4).map(cam => (
            <div 
              key={cam.id}
              onClick={() => handleOpenCam(cam.id)}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '10px',
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#fff' }}>
                  {cam.id}
                </span>
                <SeverityBadge 
                  severity={cam.status === 'ONLINE' ? 'SUCCESS' : (cam.status === 'COMPROMISED' ? 'CRITICAL' : 'HIGH')} 
                  text={cam.status}
                />
              </div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>{cam.name}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
                📍 {cam.location}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', color: 'var(--text-muted)', marginTop: '8px', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                <span>FPS: {cam.fps}</span>
                <span>Vehicles: {cam.vehicle_count}</span>
                <span>Security: {cam.security_health}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
