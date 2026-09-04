import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, AlertTriangle, CheckCircle, ShieldAlert, Cpu, ArrowRight } from 'lucide-react';
import { useTraffic } from '../context/TrafficContext';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const ScenarioSimulatorView = () => {
  const { refreshAll, setActiveView, setSelectedIncidentId } = useTraffic();
  const [scenarios, setScenarios] = useState([]);
  const [activeScenario, setActiveScenario] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8001/api/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data))
      .catch(() => {});
  }, []);

  const handleLaunch = async (scenarioId) => {
    setLoading(true);
    setStatusMsg(`Launching ${scenarioId}... Telemetry disturbance propagating...`);
    try {
      const res = await fetch(`http://localhost:8001/api/scenarios/${scenarioId}/launch`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        setActiveScenario(scenarioId);
        setStatusMsg(`Scenario ${scenarioId} executed successfully! Generated incident: ${data.incident_id || 'INC-2026'}. Check Alert Center.`);
        refreshAll();
        if (data.incident_id) {
          setSelectedIncidentId(data.incident_id);
        }
      } else {
        setStatusMsg('Failed to launch scenario.');
      }
    } catch (e) {
      setStatusMsg('Network error executing scenario.');
    }
    setLoading(false);
  };

  const handleReset = async () => {
    setLoading(true);
    setStatusMsg('Resetting simulation state back to nominal baseline...');
    try {
      const res = await fetch('http://localhost:8001/api/scenarios/reset', { method: 'POST' });
      if (res.ok) {
        setActiveScenario(null);
        setStatusMsg('System restored to nominal baseline. All active alarms resolved.');
        refreshAll();
      }
    } catch (e) {
      setStatusMsg('Error resetting simulation.');
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>INTERACTIVE SCENARIO SIMULATOR</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Controlled Incident Injection for SOC Operator Training & Master Demonstration
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="sim-badge">DEMO / SIMULATED DATA</div>
          <button 
            className="btn btn-outline" 
            onClick={handleReset}
            disabled={loading}
            style={{ borderColor: '#34d399', color: '#34d399' }}
          >
            <RotateCcw size={14} /> Reset to Baseline
          </button>
        </div>
      </div>

      {statusMsg && (
        <div style={{ padding: '10px 14px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '6px', fontSize: '12.5px', color: '#fbbf24' }}>
          ℹ️ {statusMsg}
        </div>
      )}

      {/* Recommended Master Demo Flow Highlight (Scenario 7) */}
      <div className="soc-card" style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(15, 23, 42, 0.8) 100%)', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="badge badge-critical">RECOMMENDED MASTER DEMO</span>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>
                Scenario 7: Full Master Cyber-Physical Attack
              </span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '700px' }}>
              Triggers the complete end-to-end cascading incident lifecycle: Network Port Scan Reconnaissance → Unauthorized Traffic Signal NTCIP Override → Severe Corridor Gridlock → Multi-Source Correlation → Critical Risk Escalation → Alert Center Notification.
            </p>
          </div>

          <button 
            className="btn btn-primary"
            onClick={() => handleLaunch('scenario_7')}
            disabled={loading}
            style={{ background: '#ef4444', color: '#fff', fontWeight: 700, padding: '10px 18px' }}
          >
            <Play size={16} /> Execute Master Attack
          </button>
        </div>
      </div>

      {/* Grid of All 9 Scenarios */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
        {scenarios.map(sc => (
          <div key={sc.id} className="soc-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)', fontWeight: 600 }}>
                  {sc.id.toUpperCase()}
                </span>
                <SeverityBadge severity={sc.severity} />
              </div>

              <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
                {sc.name}
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px', minHeight: '36px' }}>
                {sc.description}
              </p>

              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '12px' }}>
                {sc.domains?.map((d, idx) => (
                  <span key={idx} className="badge badge-info" style={{ fontSize: '10px' }}>{d}</span>
                ))}
              </div>
            </div>

            <button
              className="btn btn-outline"
              onClick={() => handleLaunch(sc.id)}
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', gap: '8px' }}
            >
              <Play size={13} /> Launch Scenario
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
