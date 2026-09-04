import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { SocDashboardPage } from './pages/SocDashboardPage';
import { DigitalTwinPage } from './pages/DigitalTwinPage';
import { HealthcareCommandPage } from './pages/HealthcareCommandPage';
import { DoctorPortalPage } from './pages/DoctorPortalPage';
import { AmbulanceCadPage } from './pages/AmbulanceCadPage';
import { TrafficOperationsPage } from './pages/TrafficOperationsPage';
import { FinanceCyberVarPage } from './pages/FinanceCyberVarPage';
import { ExecutiveDashboardPage } from './pages/ExecutiveDashboardPage';
import { DemoCenterPage } from './pages/DemoCenterPage';
import { WorkflowWorkspacePage } from './pages/WorkflowWorkspacePage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Authenticated App Layout */}
        <Route path="/" element={<AppLayout />}>
          <Route index element={<WorkflowWorkspacePage />} />
          <Route path="workspace" element={<WorkflowWorkspacePage />} />
          <Route path="soc" element={<SocDashboardPage />} />
          <Route path="twin" element={<DigitalTwinPage />} />
          <Route path="healthcare" element={<HealthcareCommandPage />} />
          <Route path="doctor" element={<DoctorPortalPage />} />
          <Route path="ambulance" element={<AmbulanceCadPage />} />
          <Route path="traffic" element={<TrafficOperationsPage />} />
          <Route path="finance" element={<FinanceCyberVarPage />} />
          <Route path="executive" element={<ExecutiveDashboardPage />} />
          <Route path="demo" element={<DemoCenterPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
