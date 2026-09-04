import React, { useState, useEffect } from 'react';
import { ArrowLeft, Compass, Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { MiniBarChart } from '../components/common/Charts';

export const RoadDetailView = () => {
  const { selectedRoadId, setActiveView, roads } = useTraffic();
  const roadId = selectedRoadId || roads[0]?.id || 'ROAD-NH44-01';

  const [detailData, setDetailData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8001/api/traffic/roads/${roadId}`)
      .then(res => res.json())
      .then(data => {
        setDetailData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [roadId]);

  const road = detailData?.road;
  const cong = detailData?.congestion_analysis;
  const preds = detailData?.predictions || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn btn-outline btn-sm" onClick={() => setActiveView('roads')}>
            <ArrowLeft size={14} /> Back to Roadways
          </button>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              {road?.name || roadId} <span style={{ color: 'var(--cyan-accent)' }}>({roadId})</span>
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Corridor Length: {road?.length_km} km | {road?.lanes} Physical Lanes | Route: {road?.route_id}
            </p>
          </div>
        </div>

        <SeverityBadge 
          severity={cong?.congestion_level === 'FREE_FLOW' ? 'SUCCESS' : cong?.congestion_level} 
          text={cong?.congestion_level || 'NORMAL'} 
        />
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
        <div className="soc-card">
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600 }}>CURRENT VELOCITY</span>
          <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff', margin: '4px 0' }}>
            {road?.current_speed_kmh} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>km/h</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Speed Limit: {road?.speed_limit_kmh} km/h</span>
        </div>

        <div className="soc-card">
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600 }}>VOLUME THROUGHPUT</span>
          <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff', margin: '4px 0' }}>
            {road?.current_volume} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>/ {road?.capacity} veh</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Capacity Utilized: {cong?.density_score}%</span>
        </div>

        <div className="soc-card">
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600 }}>CONGESTION INDEX</span>
          <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: cong?.color_code || '#10b981', margin: '4px 0' }}>
            {cong?.congestion_score || 0} / 100
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Risk Attribution: {cong?.risk_score}/100</span>
        </div>
      </div>

      {/* Congestion Explainability & Predictions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Cause / Explainability */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Activity size={15} color="var(--cyan-accent)" />
              CONGESTION REASON & DIAGNOSTICS
            </div>
          </div>
          <p style={{ fontSize: '13px', color: '#fff', lineHeight: 1.6, background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px' }}>
            {cong?.reason || 'Nominal traffic conditions.'}
          </p>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '8px' }}>
            Confidence: {((cong?.confidence || 0.94) * 100).toFixed(0)}% | Multi-lane capacity model
          </div>
        </div>

        {/* Predictive Horizon Mini-List */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <TrendingUp size={15} color="var(--cyan-accent)" />
              PREDICTED CONGESTION HORIZONS
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {preds.map((p, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface)', padding: '8px 12px', borderRadius: '4px', fontSize: '12px' }}>
                <span style={{ color: 'var(--cyan-accent)', fontWeight: 600 }}>+{p.horizon_minutes} Mins</span>
                <span>Volume: <strong>{p.predicted_volume} veh</strong></span>
                <span>Velocity: <strong>{p.predicted_speed_kmh} km/h</strong></span>
                <SeverityBadge severity={p.predicted_congestion === 'FREE_FLOW' ? 'SUCCESS' : p.predicted_congestion} text={p.predicted_congestion} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
