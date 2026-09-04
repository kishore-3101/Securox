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
      title: 'Incidents & Alerts',
      items: [
        { id: 'alert-center', label: 'Alert Center', icon: AlertTriangle, badge: activeAlertsCount, isDanger: activeAlertsCount > 0 },
        { id: 'incidents', label: 'Incident Management', icon: Shield, badge: critIncidentsCount, isDanger: critIncidentsCount > 0 },
        { id: 'fastag-console', label: 'FASTag Dual-Auth', icon: CheckCircle2 },
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
