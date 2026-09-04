import React, { useState, useEffect } from 'react';
import { KpiCard } from '../../components/common/KpiCard';
import { SeverityBadge } from '../../components/common/SeverityBadge';
import { StatusDot } from '../../components/common/StatusDot';
import { PermissionGuard } from '../../components/common/PermissionGuard';
import { DataTable, Column } from '../../components/common/DataTable';
import { socService } from '../../services/socService';
import { useWebSocket } from '../../hooks/useWebSocket';
import { usePermissions } from '../../hooks/usePermissions';
import { Alert, Incident } from '../../types/soc';
import {
  ShieldAlert,
  AlertTriangle,
  FileText,
  Activity,
  CheckCircle2,
  RefreshCw,
  Eye,
  Sliders,
} from 'lucide-react';

export const SocCommandCenter: React.FC = () => {
  const { alerts: wsAlerts, incidents: wsIncidents } = useWebSocket();
  const { can } = usePermissions();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<{ total: number; by_severity: Record<string, number> }>({
    total: 0,
    by_severity: {},
  });
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [alertList, incidentList, statData] = await Promise.all([
        socService.getAlerts(100),
        socService.getIncidents(50),
        socService.getAlertStats(),
      ]);
      setAlerts(alertList);
      setIncidents(incidentList);
      setStats(statData);
    } catch (err) {
      console.error('Failed to load SOC data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 30000);
    return () => clearInterval(timer);
  }, []);

  // Merge WebSocket alerts into list
  const allAlerts = wsAlerts.length > 0 ? [...wsAlerts, ...alerts] : alerts;
  const filteredAlerts = selectedSeverity === 'ALL'
    ? allAlerts
    : allAlerts.filter((a) => (a.severity || '').toUpperCase() === selectedSeverity);

  const allIncidents = wsIncidents.length > 0 ? [...wsIncidents, ...incidents] : incidents;

  const handleUpdateIncidentStatus = async (incidentId: string, status: any) => {
    try {
      await socService.updateIncidentStatus(incidentId, status);
      setIncidents((prev) =>
        prev.map((inc) => (inc.id === incidentId ? { ...inc, status } : inc))
      );
    } catch (err: any) {
      alert(`Error updating incident: ${err.message}`);
    }
  };

  const alertColumns: Column<Alert>[] = [
    {
      header: 'Timestamp',
      accessor: (row) => (
        <span className="font-mono text-[11px] text-slate-400">
          {row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : 'NOW'}
        </span>
      ),
    },
    {
      header: 'Target Asset',
      accessor: (row) => (
        <span className="font-mono font-semibold text-slate-200">{row.asset}</span>
      ),
    },
    {
      header: 'Attack Type',
      accessor: (row) => (
        <span className="text-sky-300 font-mono text-[11px]">{row.attack_type || 'Anomaly Detection'}</span>
      ),
    },
    {
      header: 'Severity',
      accessor: (row) => <SeverityBadge severity={row.severity} />,
    },
    {
      header: 'Anomaly Score',
      accessor: (row) => (
        <span className="font-mono text-xs text-amber-400">
          {row.anomaly_score !== undefined ? `${(row.anomaly_score * 100).toFixed(0)}%` : 'N/A'}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusDot status={row.status || 'ALERT'} size="sm" />
          <span className="text-[11px] font-mono text-slate-300">{row.status || 'Active'}</span>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-sky-400" />
            SOC Command Center
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Pan-City Autonomous Threat Correlation & Incident Response Hub
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 hover:bg-slate-800 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Processed Alerts"
          value={stats.total || allAlerts.length}
          subtitle="Real-time event stream"
          icon={Activity}
          accentColor="blue"
        />
        <KpiCard
          title="Critical Threats"
          value={stats.by_severity?.CRITICAL || allAlerts.filter((a) => (a.severity || '').toUpperCase() === 'CRITICAL').length}
          subtitle="Immediate containment priority"
          icon={AlertTriangle}
          accentColor="red"
        />
        <KpiCard
          title="Active Incidents"
          value={allIncidents.filter((i) => i.status !== 'RESOLVED').length}
          subtitle="Under active triage"
          icon={FileText}
          accentColor="amber"
        />
        <KpiCard
          title="Automated Mitigations"
          value={38}
          subtitle="Zero-trust containment active"
          icon={CheckCircle2}
          accentColor="green"
        />
      </div>

      {/* Live Incident Queue */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
              Active Incident Queue & Triage
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {allIncidents.length} Registered Cases
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allIncidents.slice(0, 6).map((inc) => (
            <div
              key={inc.id}
              className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-3 hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-mono font-bold text-slate-200">
                  {inc.title || inc.id}
                </span>
                <SeverityBadge severity={inc.severity} />
              </div>

              <div className="text-xs font-mono space-y-1 text-slate-400">
                <div>Asset: <span className="text-slate-200 font-semibold">{inc.asset}</span></div>
                <div>Status: <span className="text-amber-400 uppercase font-bold">{inc.status}</span></div>
                <div>Owner: <span className="text-slate-300">{(inc as any).owner || 'Unassigned'}</span></div>
              </div>

              {/* Status Action Buttons with PermissionGuard */}
              <div className="pt-2 border-t border-slate-800 flex items-center gap-2">
                <PermissionGuard capability="can_execute_mitigations">
                  <button
                    onClick={() => handleUpdateIncidentStatus(inc.id, 'contained')}
                    className="px-2 py-1 rounded text-[11px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition"
                  >
                    Contain
                  </button>
                </PermissionGuard>

                <PermissionGuard capability="can_execute_mitigations">
                  <button
                    onClick={() => handleUpdateIncidentStatus(inc.id, 'resolved')}
                    className="px-2 py-1 rounded text-[11px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition"
                  >
                    Resolve
                  </button>
                </PermissionGuard>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live Alerts Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
              Live Pan-City Alert Feed
            </h3>
          </div>

          {/* Severity Filter Pills */}
          <div className="flex items-center gap-1.5">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  selectedSeverity === sev
                    ? 'bg-sky-500 text-white font-bold'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        <DataTable
          columns={alertColumns}
          data={filteredAlerts}
          searchPlaceholder="Search alerts by asset, IP, or attack type..."
          pageSize={10}
        />
      </div>
    </div>
  );
};
