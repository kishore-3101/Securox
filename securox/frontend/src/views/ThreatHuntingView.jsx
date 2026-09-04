import React, { useState } from 'react';
import { Terminal, Search, Filter, RefreshCw } from 'lucide-react';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { istFormat } from '../utils/dateUtils';

export const ThreatHuntingView = () => {
  const [queryText, setQueryText] = useState('');
  const [selectedAsset, setSelectedAsset] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8001/api/cyber/threat-hunting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_text: queryText || null,
          asset_id: selectedAsset || null,
          severity: selectedSeverity || null,
          limit: 50
        })
      });
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (e) {}
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>CONTROLLED THREAT HUNTING CONSOLE</h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Forensic investigation query layer over normalized OT events, camera telemetry, and controller logs
        </p>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleSearch} className="soc-card" style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text"
          className="soc-input"
          placeholder="Search by keywords (e.g. 'port scan', 'Intersection 12', 'camera blackout')..."
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          style={{ flex: 2, minWidth: '220px' }}
        />

        <input
          type="text"
          className="soc-input"
          placeholder="Asset ID (e.g. CAM-04, CTRL-INT12)"
          value={selectedAsset}
          onChange={(e) => setSelectedAsset(e.target.value)}
          style={{ flex: 1, minWidth: '150px' }}
        />

        <select
          className="soc-input"
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          style={{ flex: 1, minWidth: '130px' }}
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          <Search size={14} /> {loading ? 'Hunting...' : 'Run Query'}
        </button>
      </form>

      {/* Results Table */}
      <div className="soc-card">
        <div className="soc-card-header">
          <div className="soc-card-title">
            <Terminal size={15} color="var(--cyan-accent)" />
            CORRELATED TELEMETRY RECORDS ({results.length})
          </div>
        </div>

        <div className="soc-table-container">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Severity</th>
                <th>Asset ID</th>
                <th>Location</th>
                <th>Title / Description</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '24px' }}>
                    Enter query parameters above to execute threat hunting across normalized event logs.
                  </td>
                </tr>
              ) : (
                results.map(r => (
                  <tr key={r.event_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-accent)' }}>{r.event_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                      {istFormat(r.timestamp)}
                    </td>
                    <td><span className="badge badge-info">{r.event_type}</span></td>
                    <td><SeverityBadge severity={r.severity} /></td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.asset_id}</td>
                    <td>{r.location}</td>
                    <td>
                      <strong style={{ color: '#fff' }}>{r.title}</strong>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{r.description}</div>
                    </td>
                    <td>{(r.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
