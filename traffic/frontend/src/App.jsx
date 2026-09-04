import React from 'react';
import './styles/commandCenter.css';

// Contexts
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { TrafficProvider, useTraffic } from './context/TrafficContext';

// Layout
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';

// Views
import { CommandCenterView } from './views/CommandCenterView';
import { LiveTrafficView } from './views/LiveTrafficView';
import { TrafficMapView } from './views/TrafficMapView';
import { CamerasView } from './views/CamerasView';
import { CameraDetailView } from './views/CameraDetailView';
import { RoadDetailView } from './views/RoadDetailView';
import { IntersectionsView } from './views/IntersectionsView';
import { TrafficSignalsView } from './views/TrafficSignalsView';
import { IncidentsView } from './views/IncidentsView';
import { IncidentDetailView } from './views/IncidentDetailView';
import { AlertCenterView } from './views/AlertCenterView';
import { FastagConsoleView } from './views/FastagConsoleView';
import { CyberSecurityCenterView } from './views/CyberSecurityCenterView';
import { ThreatIntelligenceView } from './views/ThreatIntelligenceView';
import { AssetSecurityView } from './views/AssetSecurityView';
import { NetworkAnomaliesView } from './views/NetworkAnomaliesView';
import { UserSecurityView } from './views/UserSecurityView';
import { ThreatHuntingView } from './views/ThreatHuntingView';
import { ForensicsView } from './views/ForensicsView';
import { AnalyticsView } from './views/AnalyticsView';
import { PredictionsView } from './views/PredictionsView';
import { AIAssistantView } from './views/AIAssistantView';
import { ScenarioSimulatorView } from './views/ScenarioSimulatorView';
import { SystemHealthView } from './views/SystemHealthView';
import { AuditLogView } from './views/AuditLogView';
import { AdministrationView } from './views/AdministrationView';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("[SECUROX-UI-ERROR]", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '30px', color: '#f87171', background: '#070b14', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#ef4444', marginBottom: '8px' }}>
            ⚠️ SECUROX Interface Recovery
          </h2>
          <p style={{ color: '#94a3b8', margin: '10px 0', fontFamily: 'monospace', maxWidth: '600px', textAlign: 'center' }}>
            {this.state.error?.toString()}
          </p>
          <button 
            className="btn btn-primary" 
            onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
            style={{ marginTop: '14px' }}
          >
            Reload Command Center
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const MainRouter = () => {
  const { activeView } = useTraffic();

  const renderActiveView = () => {
    switch (activeView) {
      case 'command-center': return <CommandCenterView />;
      case 'live-traffic':
      case 'roads': return <LiveTrafficView />;
      case 'road-detail': return <RoadDetailView />;
      case 'traffic-map': return <TrafficMapView />;
      case 'cameras': return <CamerasView />;
      case 'camera-detail': return <CameraDetailView />;
      case 'intersections': return <IntersectionsView />;
      case 'traffic-signals': return <TrafficSignalsView />;
      case 'incidents': return <IncidentsView />;
      case 'incident-detail': return <IncidentDetailView />;
      case 'alert-center': return <AlertCenterView />;
      case 'fastag-console': return <FastagConsoleView />;
      case 'cyber-center': return <CyberSecurityCenterView />;
      case 'threat-intel': return <ThreatIntelligenceView />;
      case 'asset-security': return <AssetSecurityView />;
      case 'network-anomalies': return <NetworkAnomaliesView />;
      case 'user-security': return <UserSecurityView />;
      case 'threat-hunting': return <ThreatHuntingView />;
      case 'forensics': return <ForensicsView />;
      case 'analytics': return <AnalyticsView />;
      case 'predictions': return <PredictionsView />;
      case 'ai-assistant': return <AIAssistantView />;
      case 'simulator': return <ScenarioSimulatorView />;
      case 'system-health': return <SystemHealthView />;
      case 'audit-log': return <AuditLogView />;
      case 'admin': return <AdministrationView />;
      default: return <AlertCenterView />;
    }
  };

  return (
    <div className="soc-app-container">
      <Navbar />
      <div className="soc-main-layout">
        <Sidebar />
        <main className="soc-content-area">
          <ErrorBoundary>
            {renderActiveView()}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <WebSocketProvider>
          <TrafficProvider>
            <MainRouter />
          </TrafficProvider>
        </WebSocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
