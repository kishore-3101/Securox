import React, { useState, useEffect } from 'react';
import { TrendingUp, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const PredictionsView = () => {
  const { roads } = useTraffic();
  const [selectedRoad, setSelectedRoad] = useState(roads[0]?.id || 'ROAD-NH44-01');
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedRoad) {
      setLoading(true);
      fetch(`http://localhost:8001/api/traffic/predictions/${selectedRoad}`)
        .then(res => res.json())
        .then(data => {
          setPredictions(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [selectedRoad]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>PREDICTIVE TRAFFIC & CONGESTION HORIZONS</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Exponential Smoothing & Machine Learning Forecasts over 15m, 30m, 60m & 2-Hour Intervals
          </p>
        </div>

        {/* Road selector */}
        <select
          className="soc-input"
          value={selectedRoad}
          onChange={(e) => setSelectedRoad(e.target.value)}
        >
          {roads.map(r => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </div>

      {/* Horizon Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        {predictions.map((p, idx) => {
          const hasData = p.status_note !== "Insufficient historical data.";
          return (
            <div key={idx} className="soc-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan-accent)' }}>
                  +{p.horizon_minutes} MINUTES HORIZON
                </span>
                {hasData && (
                  <SeverityBadge 
                    severity={p.predicted_congestion === 'FREE_FLOW' ? 'SUCCESS' : p.predicted_congestion} 
                    text={p.predicted_congestion}
                  />
                )}
              </div>

              {hasData ? (
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff', margin: '8px 0' }}>
                    {p.predicted_volume} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>veh/hr</span>
                  </div>

                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Predicted Velocity: <strong style={{ color: '#fff' }}>{p.predicted_speed_kmh} km/h</strong>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                    <div>Baseline: <strong>{p.historical_baseline} veh/hr</strong></div>
                    <div>Model Confidence: <strong>{(p.confidence * 100).toFixed(0)}%</strong></div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '16px 0', textAlign: 'center', color: '#f59e0b', fontSize: '12px' }}>
                  <AlertCircle size={20} style={{ margin: '0 auto 6px' }} />
                  {p.status_note}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
