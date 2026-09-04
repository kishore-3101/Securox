import React, { useState } from 'react';
import { MaintenanceTicket } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import { Wrench, CheckCircle2, Plus, RefreshCw } from 'lucide-react';

interface Props {
  tickets: MaintenanceTicket[];
  onRefresh: () => void;
}

export const MaintenanceSubsystem: React.FC<Props> = ({ tickets, onRefresh }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [completeTicketId, setCompleteTicketId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [signalId, setSignalId] = useState('SIG-03');
  const [issueType, setIssueType] = useState('LOOP_IMPEDANCE_DRIFT');
  const [priority, setPriority] = useState('HIGH');
  const [voltage, setVoltage] = useState(230.0);
  const [loopOhms, setLoopOhms] = useState(4.2);
  const [diagLog, setDiagLog] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await trafficService.createMaintenanceTicket({
        signal_id: signalId,
        issue_type: issueType,
        priority,
        voltage_reading: Number(voltage),
        loop_resistance_ohms: Number(loopOhms),
        diagnostic_log: diagLog || 'Technician diagnostic check',
      });
      setShowCreateModal(false);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Error creating maintenance ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async (tktId: string) => {
    try {
      await trafficService.updateMaintenanceTicket(tktId, 'COMPLETED', undefined, resolutionNotes || 'Hardware validated and returned to service');
      setCompleteTicketId(null);
      setResolutionNotes('');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Error closing ticket');
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Wrench className="w-5 h-5 text-blue-400" />
            Signal Engineering & Hardware Maintenance Console
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Loop impedance diagnostics, controller AC voltage telemetry, and firmware SHA-256 integrity verification
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs font-mono transition shadow"
          >
            <Plus className="w-3.5 h-3.5" /> New Work Order
          </button>
        </div>
      </div>

      {/* Tickets Board */}
      <div className="space-y-3">
        {tickets.map((tkt) => (
          <div
            key={tkt.id}
            className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs"
          >
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-blue-400 font-bold">{tkt.id}</span>
                <span className="text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                  Target: {tkt.signal_id}
                </span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    tkt.priority === 'CRITICAL'
                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                      : tkt.priority === 'HIGH'
                      ? 'bg-amber-950 text-amber-400 border border-amber-800'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {tkt.priority}
                </span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    tkt.status === 'COMPLETED'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-blue-950 text-blue-400 border border-blue-800'
                  }`}
                >
                  {tkt.status}
                </span>
              </div>
              <h4 className="text-sm font-bold text-slate-200">{tkt.issue_type}</h4>
              <div className="text-slate-400 text-[11px] flex flex-wrap gap-4 pt-1">
                <span>Voltage: <strong className="text-slate-200">{tkt.voltage_reading} V</strong></span>
                <span>Loop Resistance: <strong className="text-slate-200">{tkt.loop_resistance_ohms} Ω</strong></span>
                <span>Firmware: <strong className="text-slate-300">{tkt.firmware_checksum}</strong></span>
              </div>
              {tkt.diagnostic_log && (
                <div className="text-slate-400 text-[11px] bg-slate-950 p-2 rounded border border-slate-800 mt-1">
                  Log: {tkt.diagnostic_log}
                </div>
              )}
              {tkt.resolution_notes && (
                <div className="text-emerald-400 text-[11px] bg-emerald-950/40 p-2 rounded border border-emerald-900 mt-1">
                  Resolution: {tkt.resolution_notes}
                </div>
              )}
            </div>

            {/* Action */}
            <div className="shrink-0">
              {tkt.status !== 'COMPLETED' ? (
                <button
                  onClick={() => setCompleteTicketId(tkt.id)}
                  className="px-3.5 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700 font-bold text-xs transition"
                >
                  Close Work Order
                </button>
              ) : (
                <span className="text-slate-500 text-[11px] flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Resolved
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Close Ticket Modal */}
      {completeTicketId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono text-xs animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-3 shadow-2xl">
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Close Maintenance Ticket: {completeTicketId}
            </h4>
            <p className="text-slate-400">
              Record hardware diagnostic measurements and final resolution log.
            </p>
            <div>
              <label className="block text-slate-400 mb-1">Resolution Notes *</label>
              <textarea
                rows={3}
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="e.g. Replaced inductive loop amplifier card. Resistance normalized to 4.1 ohms."
                className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setCompleteTicketId(null)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleComplete(completeTicketId)}
                className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold"
              >
                Commit Closure
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono text-xs animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Wrench className="w-5 h-5 text-blue-400" />
              Dispatch Signal Maintenance Work Order
            </h4>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Signal Junction ID *</label>
                  <input
                    type="text"
                    value={signalId}
                    onChange={(e) => setSignalId(e.target.value)}
                    placeholder="SIG-01"
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="NORMAL">NORMAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Issue Type</label>
                <select
                  value={issueType}
                  onChange={(e) => setIssueType(e.target.value)}
                  className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                >
                  <option value="LOOP_IMPEDANCE_DRIFT">LOOP_IMPEDANCE_DRIFT</option>
                  <option value="CONTROLLER_POWER_FAULT">CONTROLLER_POWER_FAULT</option>
                  <option value="LED_MODULE_OUTAGE">LED_MODULE_OUTAGE</option>
                  <option value="FIRMWARE_CHECKSUM_MISMATCH">FIRMWARE_CHECKSUM_MISMATCH</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Voltage Reading (V)</label>
                  <input
                    type="number"
                    value={voltage}
                    onChange={(e) => setVoltage(Number(e.target.value))}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Loop Resistance (Ω)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={loopOhms}
                    onChange={(e) => setLoopOhms(Number(e.target.value))}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Diagnostic Log</label>
                <textarea
                  rows={2}
                  value={diagLog}
                  onChange={(e) => setDiagLog(e.target.value)}
                  placeholder="Telemetry findings or physical inspection..."
                  className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded bg-slate-800 text-slate-300 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold"
                >
                  {submitting ? 'Dispatching...' : 'Dispatch Work Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
