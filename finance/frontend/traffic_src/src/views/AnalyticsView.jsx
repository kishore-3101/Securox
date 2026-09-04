import React from 'react';
import { BarChart3, TrendingUp, Activity, PieChart } from 'lucide-react';
import { MiniBarChart, DonutGauge } from '../components/common/Charts';
import { useTraffic } from '../context/TrafficContext';

export const AnalyticsView = () => {
  const { roads, kpis } = useTraffic();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>TRAFFIC & SECURITY INTELLIGENCE ANALYTICS</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Historical Flow Patterns, Congestion Durations & Cyber Threat Distributions</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Hourly Volume Distribution */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <BarChart3 size={15} color="var(--cyan-accent)" />
              HOURLY VOLUME DISTRIBUTION (24-HR)
            </div>
          </div>
          <MiniBarChart data={[120, 95, 60, 45, 80, 210, 380, 450, 410, 340, 290, 310, 330, 360, 420, 480, 510, 440, 380, 320, 260, 210, 180, 140]} height={70} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-dim)', marginTop: '8px' }}>
            <span>00:00</span>
            <span>06:00 (Morning Peak)</span>
            <span>12:00</span>
            <span>18:00 (Evening Peak)</span>
            <span>23:00</span>
          </div>
        </div>

        {/* Vehicle Class Classification */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <PieChart size={15} color="var(--cyan-accent)" />
              VEHICLE CLASSIFICATION BREAKDOWN
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', padding: '10px 0' }}>
            <DonutGauge value={58} label="Passenger" color="#06b6d4" />
            <DonutGauge value={24} label="Freight" color="#f59e0b" />
            <DonutGauge value={18} label="Transit/2W" color="#10b981" />
          </div>
        </div>

        {/* Cyber Threat Vector Distribution */}
        <div className="soc-card">
          <div className="soc-card-header">
            <div className="soc-card-title">
              <Activity size={15} color="#ef4444" />
              CYBER INCIDENT VECTOR SHARES
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                <span>NTCIP Signal Timing Tampering</span>
                <strong>42%</strong>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', marginTop: '3px' }}>
                <div style={{ width: '42%', height: '100%', background: '#ef4444' }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                <span>Network Port Scanning / Recon</span>
                <strong>30%</strong>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', marginTop: '3px' }}>
                <div style={{ width: '30%', height: '100%', background: '#f59e0b' }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                <span>Camera RTSP Brute Force</span>
                <strong>18%</strong>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', marginTop: '3px' }}>
                <div style={{ width: '18%', height: '100%', background: '#06b6d4' }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                <span>Sensor Telemetry Discrepancies</span>
                <strong>10%</strong>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', marginTop: '3px' }}>
                <div style={{ width: '10%', height: '100%', background: '#8b5cf6' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
