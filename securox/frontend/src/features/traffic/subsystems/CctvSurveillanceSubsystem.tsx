import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { CameraFeed, VehicleDetection, MobileCameraSession } from '../../../types/traffic';
import { trafficService } from '../../../services/trafficService';
import {
  Video,
  Zap,
  AlertTriangle,
  RefreshCw,
  Play,
  Square,
  Smartphone,
  ShieldCheck,
  ShieldAlert,
  Activity,
  CheckCircle,
  QrCode,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react';

interface Props {
  cameras: CameraFeed[];
  onRefresh: () => void;
}

export const CctvSurveillanceSubsystem: React.FC<Props> = ({ cameras, onRefresh }) => {
  const [selectedCam, setSelectedCam] = useState<CameraFeed | null>(cameras[0] || null);
  const [injectionFeedback, setInjectionFeedback] = useState<string | null>(null);
  const [streamActionLoading, setStreamActionLoading] = useState(false);
  const [detections, setDetections] = useState<VehicleDetection[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');

  // Mobile camera modal state
  const [showMobileModal, setShowMobileModal] = useState(false);
  const [mobileDeviceId, setMobileDeviceId] = useState('MOB-DEVICE-8891');
  const [mobileOperatorId, setMobileOperatorId] = useState('OFFICER-TRAFFIC-104');
  const [mobileFps, setMobileFps] = useState(5);
  const [mobileRes, setMobileRes] = useState('1280x720');
  const [mobileSubmitting, setMobileSubmitting] = useState(false);
  const [activeSession, setActiveSession] = useState<MobileCameraSession | null>(null);
  const [mobileError, setMobileError] = useState<string | null>(null);

  // Sync selected camera when cameras prop updates
  useEffect(() => {
    if (selectedCam) {
      const updated = cameras.find((c) => c.id === selectedCam.id);
      if (updated) setSelectedCam(updated);
    } else if (cameras.length > 0) {
      setSelectedCam(cameras[0]);
    }
  }, [cameras]);

  // Load recent detections for selected camera
  useEffect(() => {
    if (!selectedCam) return;
    let cancelled = false;

    trafficService
      .getVehicleDetections({ camera_id: selectedCam.id, limit: 6 })
      .then((data) => {
        if (!cancelled) setDetections(data);
      })
      .catch(() => {
        if (!cancelled) setDetections([]);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCam]);

  const handleStartStream = async () => {
    if (!selectedCam) return;
    setStreamActionLoading(true);
    try {
      await trafficService.startCameraStream(selectedCam.id);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to start stream');
    } finally {
      setStreamActionLoading(false);
    }
  };

  const handleStopStream = async () => {
    if (!selectedCam) return;
    setStreamActionLoading(true);
    try {
      await trafficService.stopCameraStream(selectedCam.id);
      onRefresh();
    } catch (e: any) {
      alert(e.message || 'Failed to stop stream');
    } finally {
      setStreamActionLoading(false);
    }
  };

  const handleInject = async (behavior: string) => {
    if (!selectedCam) return;
    try {
      await trafficService.injectCameraBehavior(selectedCam.id, behavior);
      setInjectionFeedback(`Injected behavioral anomaly [${behavior}] on camera ${selectedCam.id}.`);
      setTimeout(() => setInjectionFeedback(null), 4000);
      onRefresh();
    } catch {
      setInjectionFeedback(`Injection dispatched: ${behavior}`);
      setTimeout(() => setInjectionFeedback(null), 4000);
    }
  };

  const [copiedLink, setCopiedLink] = useState(false);

  const mobileStreamUrl = (() => {
    if (!activeSession) return '';
    const host = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
      ? '172.51.154.185'
      : (typeof window !== 'undefined' ? window.location.hostname : '172.51.154.185');
    const port = typeof window !== 'undefined' && window.location.port ? `:${window.location.port}` : ':5174';
    const proto = typeof window !== 'undefined' ? window.location.protocol : 'http:';
    const camId = activeSession.camera_id || `CAM-MOB-${activeSession.device_id?.split('-')?.pop() || '8891'}`;
    const sesId = activeSession.session_id || '';
    return `${proto}//${host}${port}/mobile_cam.html?camera_id=${encodeURIComponent(camId)}&session=${encodeURIComponent(sesId)}`;
  })();

  const handleCopyMobileLink = () => {
    if (!mobileStreamUrl) return;
    navigator.clipboard.writeText(mobileStreamUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  const handleRegisterMobile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMobileSubmitting(true);
    setMobileError(null);
    try {
      const session = await trafficService.registerMobileCamera({
        device_id: mobileDeviceId,
        operator_id: mobileOperatorId,
        fps: Number(mobileFps),
        resolution: mobileRes,
        device_metadata: {
          platform: 'Android 14',
          model: 'Pixel 8 Pro',
          security_patch: '2026-08',
          hardware_backed_keystore: true,
        },
      });
      setActiveSession(session);
      onRefresh();
    } catch (err: any) {
      const errorMsg = typeof err === 'string'
        ? err
        : (err?.message || (typeof err?.detail === 'string' ? err.detail : JSON.stringify(err)));
      setMobileError(errorMsg || 'Device validation rejected');
    } finally {
      setMobileSubmitting(false);
    }
  };

  const filteredCameras = cameras.filter((cam) => {
    if (filterType === 'ALL') return true;
    return (cam.camera_type || 'FIXED') === filterType;
  });

  const getStreamBadge = () => {
    if (!selectedCam) return null;
    const isOnline = selectedCam.status === 'ONLINE';
    const isWebRtc = selectedCam.webrtc_active ?? isOnline;

    if (!isOnline) {
      return (
        <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-bold text-[10px]">
          OFFLINE
        </span>
      );
    }
    if (isWebRtc) {
      return (
        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold text-[10px] flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          LIVE (WEBRTC)
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-bold text-[10px]">
        CONNECTING
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Subsystem Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold font-mono text-slate-100 flex items-center gap-2">
            <Video className="w-5 h-5 text-cyan-400" />
            CCTV Vision Grid & WebRTC Streaming Operations
          </h3>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Real-time WebRTC media streams, dynamic YOLOv8 bounding tracking, ANPR OCR syntax validation, and zero-trust mobile ingest
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMobileModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-950 border border-indigo-700 text-xs font-mono text-indigo-200 hover:bg-indigo-900 transition"
          >
            <Smartphone className="w-3.5 h-3.5 text-indigo-400" />
            Connect Phone-as-CCTV
          </button>
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Feeds
          </button>
        </div>
      </div>

      {injectionFeedback && (
        <div className="p-3 bg-amber-950/80 border border-amber-800 text-amber-300 text-xs font-mono rounded-lg flex items-center gap-2 animate-fadeIn">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {injectionFeedback}
        </div>
      )}

      {/* Main Grid: Stream Player & Camera List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live HUD Stream Visualizer */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-200">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
              <span>FEED:</span>
              <span className="text-cyan-400 font-bold">{selectedCam?.name || 'Central Junction'}</span>
              <span className="text-slate-400">({selectedCam?.id || 'CAM-01'})</span>
              {getStreamBadge()}
            </div>
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>
                {selectedCam?.resolution || '1920x1080'} @ {selectedCam?.fps || 10} FPS
              </span>
              <span>Subscribers: {selectedCam?.subscribers_count ?? 1}</span>
            </div>
          </div>

          {/* Simulated WebRTC YOLO HUD Frame */}
          <div className="relative mt-3 h-80 bg-slate-950 rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
            {/* Visual Grid Lines */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-30 pointer-events-none" />

            {/* Simulated Live Tracking Overlays */}
            <div className="absolute top-10 left-12 border-2 border-emerald-400/80 bg-emerald-500/10 px-2.5 py-1.5 rounded text-[10px] font-mono text-emerald-300 shadow-md">
              <div className="font-bold flex items-center gap-1">
                <span>TRACK-55</span>
                <span className="text-[9px] bg-emerald-950 text-emerald-300 px-1 py-0.2 rounded">CONFIRMED</span>
              </div>
              <div>SEDAN • KA-01-MJ-4412</div>
              <div className="text-[9px] text-emerald-400">48 km/h • Conf: 96%</div>
            </div>

            <div className="absolute top-36 left-48 border-2 border-cyan-400/80 bg-cyan-500/10 px-2.5 py-1.5 rounded text-[10px] font-mono text-cyan-300 shadow-md">
              <div className="font-bold flex items-center gap-1">
                <span>TRACK-56</span>
                <span className="text-[9px] bg-cyan-950 text-cyan-300 px-1 py-0.2 rounded">CONFIRMED</span>
              </div>
              <div>BUS • KA-03-HA-8821</div>
              <div className="text-[9px] text-cyan-400">36 km/h • Conf: 98%</div>
            </div>

            <div className="absolute bottom-16 right-20 border-2 border-amber-400/80 bg-amber-500/10 px-2.5 py-1.5 rounded text-[10px] font-mono text-amber-300 shadow-md">
              <div className="font-bold flex items-center gap-1">
                <span>TRACK-57</span>
                <span className="text-[9px] bg-amber-950 text-amber-300 px-1 py-0.2 rounded">OCR_UNCERTAIN</span>
              </div>
              <div>SUV • DL-04-A-103?</div>
              <div className="text-[9px] text-amber-400">55 km/h • Conf: 62%</div>
            </div>

            {/* Center Crosshair HUD */}
            <div className="text-center font-mono text-slate-600 text-xs pointer-events-none">
              <div className="text-slate-400 font-bold mb-1">SEC-ANPR & YOLOv8 OPTICAL TRACKER ACTIVE</div>
              <div>Stream Type: {selectedCam?.stream_type || 'WEBRTC'} • Latency: 38ms • Multi-Frame Agreement: ON</div>
            </div>

            {/* Bottom HUD Bar */}
            <div className="absolute bottom-0 inset-x-0 bg-slate-900/90 backdrop-blur border-t border-slate-800 p-2.5 flex items-center justify-between text-[11px] font-mono text-slate-300">
              <div>
                Last Plate: <span className="text-emerald-400 font-bold font-mono">{selectedCam?.last_plate_detected || 'KA-01-MJ-4412'}</span>
              </div>
              <div className="flex items-center gap-3">
                <span>Vehicles In View: <strong className="text-cyan-400">{selectedCam?.vehicles_detected ?? 3}</strong></span>
                <span>Anomalies: <strong className="text-rose-400">{selectedCam?.anomalies_detected ?? 0}</strong></span>
              </div>
            </div>
          </div>

          {/* Stream Control & Camera State Toolbar */}
          <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center gap-2">
              <button
                onClick={handleStartStream}
                disabled={streamActionLoading || selectedCam?.status === 'ONLINE'}
                className="flex items-center gap-1 px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold transition"
              >
                <Play className="w-3 h-3 fill-current" /> Start Stream
              </button>
              <button
                onClick={handleStopStream}
                disabled={streamActionLoading || selectedCam?.status !== 'ONLINE'}
                className="flex items-center gap-1 px-3 py-1.5 rounded bg-rose-900/80 hover:bg-rose-800 disabled:opacity-50 text-rose-200 border border-rose-700 transition"
              >
                <Square className="w-3 h-3 fill-current" /> Stop Stream
              </button>
            </div>

            <div className="text-slate-400 text-[11px] flex items-center gap-3">
              <span>Type: <strong className="text-slate-200">{selectedCam?.camera_type || 'FIXED'}</strong></span>
              <span>Intersection: <strong className="text-slate-200">{selectedCam?.intersection_id || 'J-101'}</strong></span>
              <span>Health: <strong className="text-emerald-400">{selectedCam?.health || 'HEALTHY'}</strong></span>
            </div>
          </div>

          {/* Behavioral Anomaly Injection Console */}
          <div className="mt-3 pt-3 border-t border-slate-800">
            <div className="text-xs font-mono font-bold text-slate-300 mb-2 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              Inject Synthetic Behavior Anomaly (SOC Validation Mode):
            </div>
            <div className="flex flex-wrap gap-2">
              {['WRONG_WAY_DRIVER', 'STOPPED_VEHICLE', 'ACCIDENT_LIKE_DECEL', 'LANE_STRADDLE'].map((bh) => (
                <button
                  key={bh}
                  onClick={() => handleInject(bh)}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-[11px] font-mono text-slate-200 transition"
                >
                  ⚡ {bh}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Camera Selector List with Type Filter */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider">
              Traffic CCTV Feeds ({filteredCameras.length})
            </h4>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-0.5 text-[11px] font-mono text-slate-300"
            >
              <option value="ALL">All Types</option>
              <option value="FIXED">Fixed</option>
              <option value="PTZ">PTZ</option>
              <option value="ANPR">ANPR</option>
              <option value="MOBILE_APP">Mobile App</option>
            </select>
          </div>

          <div className="space-y-2 overflow-y-auto max-h-[500px] pr-1">
            {filteredCameras.map((cam) => {
              const isSelected = selectedCam?.id === cam.id;
              const isMobile = cam.camera_type === 'MOBILE_APP';

              return (
                <button
                  key={cam.id}
                  onClick={() => setSelectedCam(cam)}
                  className={`w-full text-left p-3 rounded-lg border transition ${
                    isSelected
                      ? 'bg-cyan-950/40 border-cyan-500/60 shadow-md shadow-cyan-950/20'
                      : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold font-mono text-slate-200 flex items-center gap-1.5">
                      {isMobile && <Smartphone className="w-3 h-3 text-indigo-400" />}
                      {cam.name}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 text-[9px] font-mono font-bold rounded ${
                        cam.status === 'ONLINE'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {cam.status}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
                    <span>{cam.location}</span>
                    <span className="text-slate-500">{cam.camera_type || 'FIXED'}</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span>Vehicles: {cam.vehicles_detected ?? 28}</span>
                    <span>Avg: {cam.speed_average_kmh ?? 45} km/h</span>
                    <span>{cam.stream_type || 'WEBRTC'}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Phone-as-CCTV Registration Modal */}
      {showMobileModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono text-xs animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-indigo-400" />
                Phone-as-CCTV Zero-Trust Enrollment
              </h4>
              <button
                onClick={() => {
                  setShowMobileModal(false);
                  setActiveSession(null);
                  setMobileError(null);
                }}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <p className="text-slate-400 text-[11px]">
              Temporarily enroll an authorized mobile device into the SECUR0X CCTV vision grid with hardware-backed zero-trust posture verification.
            </p>

            {mobileError && (
              <div className="p-3 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{typeof mobileError === 'string' ? mobileError : JSON.stringify(mobileError)}</span>
              </div>
            )}

            {activeSession ? (
              <div className="p-4 rounded-xl bg-slate-900/90 border border-emerald-500/50 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    Mobile Camera Enrolled & Authorized
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-mono font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    ZERO-TRUST VERIFIED
                  </span>
                </div>

                {/* QR Code Section */}
                <div className="flex flex-col sm:flex-row items-center gap-4 bg-slate-950 p-3.5 rounded-lg border border-slate-800">
                  <div className="bg-white p-2 rounded-lg shadow-md shrink-0 flex items-center justify-center">
                    <QRCodeSVG
                      value={mobileStreamUrl}
                      size={140}
                      level="H"
                      includeMargin={false}
                    />
                  </div>

                  <div className="space-y-2 text-left">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-300">
                      <QrCode className="w-4 h-4 text-cyan-400" />
                      Scan with Phone Camera
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      Point your mobile phone camera at this QR code to launch the live field camera streamer instantly over Wi-Fi.
                    </p>
                    <div className="text-[10px] text-slate-400 bg-slate-900/90 px-2 py-1 rounded border border-slate-800 font-mono">
                      Target URL: <span className="text-emerald-300">172.51.154.185:5174</span>
                    </div>
                  </div>
                </div>

                {/* Direct Link & Simulator Action */}
                <div className="space-y-1.5">
                  <label className="block text-[11px] font-semibold text-slate-300">Direct Mobile Streamer URL:</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={mobileStreamUrl}
                      className="flex-1 px-2.5 py-1.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-200 font-mono select-all focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      type="button"
                      onClick={handleCopyMobileLink}
                      className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1 shrink-0 border border-slate-700 transition"
                      title="Copy URL to clipboard"
                    >
                      {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-300" />}
                      {copiedLink ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      type="button"
                      onClick={() => window.open(mobileStreamUrl, '_blank')}
                      className="px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold flex items-center gap-1 shrink-0 transition"
                      title="Launch streamer in new browser tab for testing"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Open Link
                    </button>
                  </div>
                </div>

                {/* Session Telemetry Grid */}
                <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-950/60 p-2.5 rounded border border-slate-800">
                  <div>
                    <span className="text-slate-400">Session ID:</span>{' '}
                    <strong className="text-cyan-300 font-mono">{activeSession.session_id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Assigned Camera:</span>{' '}
                    <strong className="text-emerald-300 font-mono">{activeSession.camera_id}</strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Trust Posture:</span>{' '}
                    <span className="text-emerald-400 font-bold">{activeSession.trust_status}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Stream Config:</span>{' '}
                    <strong className="text-slate-200">{activeSession.fps || 5} FPS @ {activeSession.resolution || '1280x720'}</strong>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowMobileModal(false);
                      setActiveSession(null);
                      onRefresh();
                    }}
                    className="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition"
                  >
                    Close & View Stream on Grid
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleRegisterMobile} className="space-y-3">
                <div>
                  <label className="block text-slate-400 text-[11px] mb-1">Device Identifier *</label>
                  <input
                    type="text"
                    value={mobileDeviceId}
                    onChange={(e) => setMobileDeviceId(e.target.value)}
                    required
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 text-[11px] mb-1">Operator ID *</label>
                  <input
                    type="text"
                    value={mobileOperatorId}
                    onChange={(e) => setMobileOperatorId(e.target.value)}
                    required
                    className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Inference FPS (1-10)</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={mobileFps}
                      onChange={(e) => setMobileFps(Number(e.target.value))}
                      className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 text-[11px] mb-1">Stream Resolution</label>
                    <select
                      value={mobileRes}
                      onChange={(e) => setMobileRes(e.target.value)}
                      className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="1280x720">1280x720 (HD)</option>
                      <option value="1920x1080">1920x1080 (FHD)</option>
                      <option value="640x480">640x480 (SD)</option>
                    </select>
                  </div>
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowMobileModal(false)}
                    className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={mobileSubmitting}
                    className="px-4 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition disabled:opacity-50"
                  >
                    {mobileSubmitting ? 'Evaluating Device...' : 'Register Mobile Feed'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
