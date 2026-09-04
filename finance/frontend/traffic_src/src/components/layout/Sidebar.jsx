import React from 'react';
import { 
  Activity, Map, Video, AlertTriangle, Shield, Terminal, 
  Cpu, Layers, FileText, Database, Compass, Eye, 
  Play, Settings, HelpCircle, Radio, BarChart3, TrendingUp,
  Server, Lock, CheckCircle2, Sliders
} from 'lucide-react';
import { useTraffic } from '../../context/TrafficContext';

export const Sidebar = () => {
  const { activeView, setActiveView, incidents, alerts, kpis } = useTraffic();

  const critIncidentsCount = incidents?.filter(i => i.status !== 'RESOLVED' && i.severity === 'CRITICAL').length || 0;
  const activeAlertsCount = alerts?.length || 0;

  const navSections = [
    {
      title: 'Command & Operations',
      items: [
        { id: 'command-center', label: 'Command Center', icon: Activity },
        { id: 'live-traffic', label: 'Live Traffic Flow', icon: Radio },
        { id: 'traffic-map', label: 'Operational Map', icon: Map },
        { id: 'cameras', label: 'Camera Intelligence', icon: Video, badge: kpis?.active_cameras?.online },
        { id: 'roads', label: 'Roadways & Corridors', icon: Compass },
        { id: 'intersections', label: 'Intersections', icon: Layers },
        { id: 'traffic-signals', label: 'Traffic Signals', icon: Sliders },
      ]
    },
    {
      title: 'Incidents & Alerts',
      items: [
        { id: 'alert-center', label: 'Alert Center', icon: AlertTriangle, badge: activeAlertsCount, isDanger: activeAlertsCount > 0 },
        { id: 'incidents', label: 'Incident Management', icon: Shield, badge: critIncidentsCount, isDanger: critIncidentsCount > 0 },
        { id: 'fastag-console', label: 'FASTag Dual-Auth', icon: CheckCircle2 },
      ]
    },
    {
      title: 'Cybersecurity SOC',
      items: [
        { id: 'cyber-center', label: 'Cyber Security Center', icon: Lock },
        { id: 'threat-intel', label: 'Threat Intelligence', icon: Terminal },
        { id: 'asset-security', label: 'Asset Security', icon: Database },
        { id: 'network-anomalies', label: 'Network Telemetry', icon: Server },
        { id: 'user-security', label: 'User & Account Risk', icon: Eye },
        { id: 'threat-hunting', label: 'Threat Hunting', icon: Compass },
        { id: 'forensics', label: 'Digital Forensics', icon: FileText },
      ]
    },
    {
      title: 'Analytics & AI',
      items: [
        { id: 'analytics', label: 'Traffic Analytics', icon: BarChart3 },
        { id: 'predictions', label: 'Predictive Horizons', icon: TrendingUp },
        { id: 'ai-assistant', label: 'AI Security Assistant', icon: HelpCircle },
      ]
    },
    {
      title: 'System & Simulation',
      items: [
        { id: 'simulator', label: 'Scenario Simulator', icon: Play, isHighlight: true },
        { id: 'system-health', label: 'System Health', icon: Cpu },
        { id: 'audit-log', label: 'Audit Log', icon: FileText },
        { id: 'admin', label: 'Administration', icon: Settings },
      ]
    }
  ];

  return (
    <aside className="soc-sidebar">
      {navSections.map((section, idx) => (
        <div key={idx} className="soc-sidebar-section">
          <div className="soc-sidebar-label">{section.title}</div>
          {section.items.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                className={`soc-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveView(item.id)}
              >
                <div className="soc-nav-item-left">
                  <Icon size={16} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge !== null && (
                  <span className={`soc-nav-badge ${item.isDanger ? 'danger' : ''}`}>
                    {item.badge}
                  </span>
                )}
                {item.isHighlight && (
                  <span style={{ fontSize: '9px', background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', padding: '1px 5px', borderRadius: '4px' }}>
                    DEMO
                  </span>
                )}
              </button>
            );
          })}
        </div>
      ))}
    </aside>
  );
};
