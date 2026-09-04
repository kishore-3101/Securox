import React, { useState } from 'react';
import { TrafficIncident } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import { AlertTriangle, ShieldCheck, Plus, RefreshCw, BadgeCheck } from 'lucide-react';

interface Props {
  incidents: TrafficIncident[];
  onRefresh: () => void;
}

export const IncidentsSubsystem: React.FC<Props> = ({ incidents, onRefresh }) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [verifyIncidentId, setVerifyIncidentId] = useState<string | null>(null);
  const [verifyNotes, setVerifyNotes] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('COLLISION');
  const [severity, setSeverity] = useState('MEDIUM');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await trafficService.createIncident({
        title,
        category,
        severity,
        location,
        description,
      });
      setShowCreateModal(false);
      setTitle('');
      setLocation('');
      setDescription('');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Error creating incident');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (incidentId: string) => {
    try {
      await trafficService.verifyIncident(incidentId, verifyNotes || 'Verified by Traffic Police Officer on scene.');
      setVerifyIncidentId(null);
      setVerifyNotes('');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Verification error');
    }
  };

  const handleUpdateStatus = async (incidentId: string, status: string) => {
    try {
      await trafficService.updateIncidentStatus(incidentId, status, 'Operational status transition');
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Status transition error');
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Traffic Incidents & Police Verification Board
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Incident lifecycle triage, Traffic Police on-scene verification, and rapid clearance dispatch
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs font-mono transition shadow"
          >
            <Plus className="w-3.5 h-3.5" /> Report Incident
          </button>
        </div>
      </div>

      {/* Incidents Board */}
      <div className="space-y-3">
        {incidents.map((inc) => (
          <div
            key={inc.id}
            className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow flex flex-col md:flex-row md:items-center justify-between gap-4 font-mono text-xs"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-bold">{inc.id}</span>
                <span
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    inc.severity === 'CRITICAL'
                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                      : inc.severity === 'HIGH'
                      ? 'bg-orange-950 text-orange-400 border border-orange-800'
                      : 'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}
                >
                  {inc.severity}
                </span>
                <span className="px-2 py-0.5 text-[10px] rounded bg-slate-800 text-slate-300">
                  {inc.category}
                </span>
                {Boolean(inc.verified) ? (
                  <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                    <BadgeCheck className="w-3 h-3" /> POLICE VERIFIED
                  </span>
                ) : (
                  <span className="text-[10px] text-amber-400 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800">
                    AWAITING VERIFICATION
                  </span>
                )}
              </div>
              <h4 className="text-sm font-bold text-slate-200">{inc.title}</h4>
              <div className="text-slate-400 text-[11px]">
                Location: <span className="text-slate-300">{inc.location}</span> | Reported By: {inc.reported_by} | Reported At: {inc.reported_at?.slice(0, 19)}
              </div>
              {inc.resolution_notes && (
                <div className="text-slate-400 text-[11px] bg-slate-950 p-2 rounded border border-slate-800 mt-1">
                  Notes: {inc.resolution_notes}
                </div>
              )}
            </div>

            {/* Police Actions */}
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {!Boolean(inc.verified) && (
                <button
                  onClick={() => setVerifyIncidentId(inc.id)}
                  className="px-3 py-1.5 rounded bg-blue-950 hover:bg-blue-900 text-blue-300 border border-blue-700 font-bold text-xs flex items-center gap-1 transition"
                >
                  <ShieldCheck className="w-3.5 h-3.5" /> Police Verify
                </button>
              )}
              {inc.status !== 'RESOLVED' ? (
                <>
                  {inc.status === 'REPORTED' && (
                    <button
                      onClick={() => handleUpdateStatus(inc.id, 'DISPATCHED')}
                      className="px-3 py-1.5 rounded bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-700 text-xs transition"
                    >
                      Dispatch Unit
                    </button>
                  )}
                  <button
                    onClick={() => handleUpdateStatus(inc.id, 'RESOLVED')}
                    className="px-3 py-1.5 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700 font-bold text-xs transition"
                  >
                    Mark Resolved
                  </button>
                </>
              ) : (
                <span className="px-2.5 py-1 text-slate-500 bg-slate-950 rounded border border-slate-800">
                  Closed
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Police Verify Modal */}
      {verifyIncidentId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono text-xs animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-3 shadow-2xl">
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
              Traffic Police On-Scene Incident Verification
            </h4>
            <p className="text-slate-400">
              Confirming on-scene physical verification for incident <span className="text-cyan-400 font-bold">{verifyIncidentId}</span>.
            </p>
            <div>
              <label className="block text-slate-400 mb-1">Verification / Clearance Notes</label>
              <textarea
                rows={3}
                value={verifyNotes}
                onChange={(e) => setVerifyNotes(e.target.value)}
                placeholder="e.g. Officer Badge #4012 on scene. Vehicles moved to shoulder; traffic flowing."
                className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setVerifyIncidentId(null)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleVerify(verifyIncidentId)}
                className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold"
              >
                Confirm Verification
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Incident Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono text-xs animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Report New Traffic Incident
            </h4>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-slate-400 mb-1">Incident Title *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. 2-Vehicle Collision on Flyover Ramp"
                  className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="COLLISION">COLLISION</option>
                    <option value="VEHICLE_BREAKDOWN">VEHICLE_BREAKDOWN</option>
                    <option value="WRONG_WAY">WRONG_WAY</option>
                    <option value="HAZARD">HAZARD</option>
                    <option value="SENSOR_FAILURE">SENSOR_FAILURE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Physical Location *</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Grand Ave & 4th St (Lane 1)"
                  className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Additional context or vehicle descriptions..."
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
                  className="px-4 py-2 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold"
                >
                  {submitting ? 'Reporting...' : 'Submit Incident'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
