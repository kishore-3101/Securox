import React, { useState, useEffect } from 'react';
import { socService } from '../../services/socService';
import { PermissionGuard } from '../../components/common/PermissionGuard';
import { StatusDot } from '../../components/common/StatusDot';
import { DigitalTwinNode } from '../../types/soc';
import {
  Network,
  RefreshCw,
  RotateCcw,
  Shield,
  Activity,
  AlertTriangle,
  Lock,
  Radio,
  Zap,
  Droplets,
  HeartPulse,
  Landmark,
  Car,
  RadioTower,
  Plane,
  Flame,
} from 'lucide-react';

interface CityAsset {
  id: string;
  name: string;
  sector: string;
  status: 'HEALTHY' | 'WARNING' | 'COMPROMISED' | 'ISOLATED';
  risk_score: number;
  anomaly_score: number;
  ip: string;
  icon: React.ElementType;
  dependencies: string[];
}

export const DigitalTwinView: React.FC = () => {
  const [nodes, setNodes] = useState<CityAsset[]>([
    { id: 'traffic_system', name: 'STIG Traffic System', sector: 'Transport', status: 'HEALTHY', risk_score: 24, anomaly_score: 0.12, ip: '10.10.1.1', icon: Car, dependencies: ['power_grid', 'communications'] },
    { id: 'public_transit', name: 'Metro & Public Transit', sector: 'Transport', status: 'HEALTHY', risk_score: 18, anomaly_score: 0.08, ip: '10.10.1.20', icon: Car, dependencies: ['power_grid', 'traffic_system'] },
    { id: 'healthcare', name: 'CAREGUARD Central Hospital', sector: 'Healthcare', status: 'WARNING', risk_score: 68, anomaly_score: 0.65, ip: '10.20.1.10', icon: HeartPulse, dependencies: ['power_grid', 'water_supply'] },
    { id: 'iomt_network', name: 'Hospital IoMT Devices', sector: 'Healthcare', status: 'WARNING', risk_score: 72, anomaly_score: 0.74, ip: '10.20.2.1', icon: HeartPulse, dependencies: ['healthcare'] },
    { id: 'finance', name: 'Core Fintech & Banking', sector: 'Finance', status: 'HEALTHY', risk_score: 31, anomaly_score: 0.19, ip: '10.30.1.5', icon: Landmark, dependencies: ['communications', 'power_grid'] },
    { id: 'water_supply', name: 'SCADA Municipal Water', sector: 'Utilities', status: 'COMPROMISED', risk_score: 88, anomaly_score: 0.89, ip: '10.40.1.100', icon: Droplets, dependencies: ['power_grid'] },
    { id: 'power_grid', name: 'Smart Power Substation', sector: 'Energy', status: 'HEALTHY', risk_score: 15, anomaly_score: 0.05, ip: '10.50.1.1', icon: Zap, dependencies: [] },
    { id: 'communications', name: 'Telecom & 5G Base Stations', sector: 'Telecom', status: 'HEALTHY', risk_score: 22, anomaly_score: 0.11, ip: '10.60.1.50', icon: RadioTower, dependencies: ['power_grid'] },
    { id: 'emergency_svcs', name: 'Civil Defense & Ambulance CAD', sector: 'Emergency', status: 'HEALTHY', risk_score: 29, anomaly_score: 0.14, ip: '10.70.1.1', icon: Flame, dependencies: ['communications', 'traffic_system'] },
    { id: 'aviation_hub', name: 'Airport Smart Terminal', sector: 'Aviation', status: 'HEALTHY', risk_score: 12, anomaly_score: 0.04, ip: '10.80.1.2', icon: Plane, dependencies: ['power_grid', 'communications'] },
    { id: 'scada_gas', name: 'Natural Gas Distribution', sector: 'Energy', status: 'HEALTHY', risk_score: 19, anomaly_score: 0.09, ip: '10.50.2.1', icon: Zap, dependencies: ['power_grid'] },
    { id: 'surveillance', name: 'Municipal CCTV Matrix', sector: 'Security', status: 'HEALTHY', risk_score: 25, anomaly_score: 0.13, ip: '10.10.3.1', icon: Radio, dependencies: ['communications'] },
  ]);

  const [selectedNode, setSelectedNode] = useState<CityAsset | null>(nodes[2]);
  const [loading, setLoading] = useState(false);

  const fetchTwin = async () => {
    try {
      setLoading(true);
      const state = await socService.getDigitalTwinState();
      if (state.assets) {
        setNodes((prev) =>
          prev.map((n) => {
            const remote = state.assets[n.id];
            if (remote) {
              const rScore = Math.round((remote.health !== undefined ? (1 - remote.health) * 100 : n.risk_score));
              const status = rScore > 75 ? 'COMPROMISED' : rScore > 40 ? 'WARNING' : 'HEALTHY';
              return { ...n, risk_score: rScore, status: remote.isolated ? 'ISOLATED' : status };
            }
            return n;
          })
        );
      }
    } catch (err) {
      console.warn('Failed to load twin state:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTwin();
    const interval = setInterval(fetchTwin, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleReset = async () => {
    try {
      await socService.resetDigitalTwin();
      await fetchTwin();
    } catch (err: any) {
      alert(`Reset error: ${err.message}`);
    }
  };

  const handleIsolateNode = (nodeId: string) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === nodeId ? { ...n, status: 'ISOLATED', risk_score: 5 } : n))
    );
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) => (prev ? { ...prev, status: 'ISOLATED', risk_score: 5 } : null));
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <Network className="w-6 h-6 text-sky-400" />
            Digital Twin Cyber-Physical Topology
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            12-Asset Interactive Pan-City Telemetry, Cascading Blast Radii & Micro-Isolation Controls
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchTwin}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 hover:bg-slate-800 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            <span>Sync</span>
          </button>

          <PermissionGuard capability="can_execute_mitigations">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-sky-400 hover:bg-slate-800 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Baseline</span>
            </button>
          </PermissionGuard>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 12-Asset Interactive Topology Matrix */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <div className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              City Asset Nodes (12 Subsystems)
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Normal</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> Warning</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" /> Critical</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-sky-400" /> Isolated</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {nodes.map((node) => {
              const Icon = node.icon;
              const isSelected = selectedNode?.id === node.id;
              let statusBorder = 'border-slate-800 hover:border-slate-700';
              if (node.status === 'COMPROMISED') statusBorder = 'border-rose-500/60 shadow-[0_0_15px_rgba(244,63,94,0.2)] bg-rose-950/20';
              else if (node.status === 'WARNING') statusBorder = 'border-amber-500/60 shadow-[0_0_15px_rgba(245,158,11,0.15)] bg-amber-950/20';
              else if (node.status === 'ISOLATED') statusBorder = 'border-sky-500/60 bg-sky-950/20';

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`flex flex-col text-left p-3.5 rounded-xl border transition-all duration-200 relative ${statusBorder} ${
                    isSelected ? 'ring-2 ring-sky-400 bg-slate-800/80' : 'bg-slate-950/60'
                  }`}
                >
                  <div className="flex items-start justify-between w-full mb-2">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      <Icon className="w-4 h-4 text-sky-400" />
                    </div>
                    <StatusDot status={node.status} size="sm" />
                  </div>

                  <span className="text-xs font-mono font-bold text-slate-200 truncate w-full">
                    {node.name}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{node.sector}</span>

                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between w-full text-[11px] font-mono">
                    <span className="text-slate-400">Risk:</span>
                    <span
                      className={`font-bold ${
                        node.risk_score > 70
                          ? 'text-rose-400'
                          : node.risk_score > 40
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {node.risk_score}%
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Node Inspection Drawer */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur flex flex-col justify-between">
          {selectedNode ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-base font-bold font-mono text-slate-100">{selectedNode.name}</h3>
                  <p className="text-xs font-mono text-sky-400">{selectedNode.id}</p>
                </div>
                <StatusDot status={selectedNode.status} size="lg" />
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Subsystem IP:</span>
                  <span className="text-slate-200">{selectedNode.ip}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Current Health:</span>
                  <span className="font-bold text-slate-200 uppercase">{selectedNode.status}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Telemetry Anomaly Score:</span>
                  <span className="text-amber-400 font-bold">{(selectedNode.anomaly_score * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Sector Boundary:</span>
                  <span className="text-slate-200">{selectedNode.sector}</span>
                </div>
              </div>

              {/* Connected Dependencies */}
              <div>
                <span className="text-xs font-mono text-slate-400 block mb-2">Connected Downstream Nodes:</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.dependencies.length > 0 ? (
                    selectedNode.dependencies.map((dep) => (
                      <span
                        key={dep}
                        className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-950 border border-slate-800 text-sky-300"
                      >
                        {dep}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 font-mono">Root Grid (No dependencies)</span>
                  )}
                </div>
              </div>

              {/* Isolation Action Control */}
              <div className="pt-4 border-t border-slate-800">
                <PermissionGuard capability="can_execute_mitigations">
                  <button
                    onClick={() => handleIsolateNode(selectedNode.id)}
                    disabled={selectedNode.status === 'ISOLATED'}
                    className="w-full py-2 px-3 rounded-lg text-xs font-mono font-bold bg-rose-600 hover:bg-rose-500 disabled:opacity-40 disabled:pointer-events-none text-white transition flex items-center justify-center gap-2"
                  >
                    <Lock className="w-4 h-4" />
                    <span>
                      {selectedNode.status === 'ISOLATED'
                        ? 'SUBNET ISOLATED'
                        : 'ENFORCE ZERO-TRUST SUBNET ISOLATION'}
                    </span>
                  </button>
                </PermissionGuard>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 font-mono text-xs">
              Select an asset node from the matrix to inspect telemetry and containment controls.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
