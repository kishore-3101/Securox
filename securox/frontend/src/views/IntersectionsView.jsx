import React, { useState, useEffect } from 'react';
import { Layers, Sliders, ArrowRight } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { useTraffic } from '../context/TrafficContext';

export const IntersectionsView = () => {
  const [intersections, setIntersections] = useState([]);
  const { setActiveView } = useTraffic();

  useEffect(() => {
    fetch('http://localhost:8001/api/traffic/intersections')
      .then(res => res.json())
      .then(data => setIntersections(data))
      .catch(() => {});
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>INTERSECTION & CONVERGENCE NODES</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Junction Queue Lengths, Signal Phases & Associated NTCIP Field Controllers
          </p>
        </div>
      </div>

      <div className="soc-card">
        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Intersection ID</th>
                <th>Name / Junction</th>
                <th>Coordinates</th>
                <th>Controller ID</th>
                <th>Signal Phase</th>
                <th>Queue Length</th>
                <th>Risk Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {intersections.map(item => (
                <tr key={item.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                    {item.id}
                  </td>
                  <td>
                    <strong style={{ color: '#fff' }}>{item.name}</strong>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                    {item.latitude.toFixed(3)}, {item.longitude.toFixed(3)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{item.controller_id}</td>
                  <td><span className="badge badge-info">{item.signal_phase}</span></td>
                  <td><strong>{item.queue_length} vehicles</strong></td>
                  <td>
                    <strong style={{ color: item.risk_score > 60 ? '#ef4444' : '#34d399', fontFamily: 'var(--font-mono)' }}>
                      {item.risk_score.toFixed(0)} / 100
                    </strong>
                  </td>
                  <td><SeverityBadge severity={item.status === 'NORMAL' ? 'SUCCESS' : 'CRITICAL'} text={item.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
