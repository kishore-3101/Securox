import React from 'react';
import { Radio, Activity, TrendingUp, AlertTriangle, ArrowRight } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { MiniBarChart } from '../components/common/Charts';

export const LiveTrafficView = () => {
  const { roads, setActiveView, setSelectedRoadId } = useTraffic();
  const roadList = Array.isArray(roads) ? roads : (roads?.roads || []);

  const handleSelectRoad = (roadId) => {
    setSelectedRoadId(roadId);
    setActiveView('road-detail');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>LIVE TRAFFIC FLOW & ROAD NETWORK</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Real-time throughput, velocity, and congestion scoring across arterial highways</p>
        </div>
        <div className="sim-badge">DEMO / SIMULATED DATA</div>
      </div>

      {/* Summary Table */}
      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Corridor Segment</th>
                <th>Route ID</th>
                <th>Length</th>
                <th>Lanes</th>
                <th>Speed Limit</th>
                <th>Current Speed</th>
                <th>Current Volume</th>
                <th>Capacity</th>
                <th>Congestion Index</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {roadList.map(r => (
                <tr key={r.id}>
                  <td>
                    <strong style={{ color: '#fff' }}>{r.name}</strong><br/>
                    <span style={{ fontSize: '10px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>{r.id}</span>
                  </td>
                  <td><span className="badge badge-info">{r.route_id}</span></td>
                  <td>{r.length_km} km</td>
                  <td>{r.lanes}</td>
                  <td>{r.speed_limit_kmh} km/h</td>
                  <td>
                    <strong style={{ color: r.current_speed_kmh < 40 ? '#ef4444' : '#34d399' }}>
                      {r.current_speed_kmh} km/h
                    </strong>
                  </td>
                  <td>{r.current_volume} veh</td>
                  <td>{r.capacity} veh</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '60px', height: '6px', background: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(100, r.density_score)}%`,
                          height: '100%',
                          background: r.density_score > 75 ? '#ef4444' : (r.density_score > 50 ? '#f59e0b' : '#10b981')
                        }} />
                      </div>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }}>{r.density_score.toFixed(0)}%</span>
                    </div>
                  </td>
                  <td>
                    <SeverityBadge 
                      severity={r.congestion_level === 'FREE_FLOW' ? 'SUCCESS' : r.congestion_level} 
                      text={r.congestion_level}
                    />
                  </td>
                  <td>
                    <button 
                      className="btn btn-outline btn-sm"
                      onClick={() => handleSelectRoad(r.id)}
                    >
                      Inspect <ArrowRight size={11} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
