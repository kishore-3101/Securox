import React from 'react';
import { Map, Layers, Video, ShieldAlert, Sliders } from 'lucide-react';
import { OperationalMap } from '../components/map/OperationalMap';
import { useTraffic } from '../context/TrafficContext';

export const TrafficMapView = () => {
  const { setActiveView, setSelectedCameraId, setSelectedRoadId } = useTraffic();

  const handleEntitySelect = (entity) => {
    if (entity.type === 'CAMERA') {
      setSelectedCameraId(entity.data.id);
      setActiveView('camera-detail');
    } else if (entity.type === 'ROAD') {
      setSelectedRoadId(entity.data.id);
      setActiveView('road-detail');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>OPERATIONAL GEOGRAPHIC MAP</h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Multi-Layer Spatial Visualization of Traffic Density, Surveillance, and Cyber Incidents</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981' }}>
            ● Free Flow
          </span>
          <span style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b' }}>
            ● Moderate
          </span>
          <span style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', color: '#f97316' }}>
            ● Heavy
          </span>
          <span style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444' }}>
            ● Severe / Critical
          </span>
        </div>
      </div>

      <OperationalMap height="calc(100vh - 160px)" onSelectEntity={handleEntitySelect} />
    </div>
  );
};
