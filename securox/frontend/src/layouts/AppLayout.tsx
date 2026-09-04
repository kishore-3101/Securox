import React, { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Topbar } from '../components/layout/Topbar';
import { SectorBanner } from '../components/layout/SectorBanner';
import { useAuth } from '../hooks/useAuth';
import { authStore } from '../stores/authStore';

export const AppLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    authStore.init();
  }, []);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar />
        <SectorBanner />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950/40">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
