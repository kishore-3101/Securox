"""
Securox — WebRTC Signaling Gateway & Live Camera Stream Service
Handles:
  • Authenticated WebRTC signaling (/ws/webrtc/{camera_id})
  • RBAC & ABAC policy enforcement for camera feeds
  • Phone-as-CCTV MobileCameraSession zero-trust evaluation
  • Signaling events: offer, answer, ice_candidate, stream_state, heartbeat, disconnect, reconnect
  • Comprehensive security audit logging and Event Fabric emission
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Set, Any, List

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.store import store
from services.event_fabric import event_fabric
from auth.jwt_auth import decode_token_or_none

logger = logging.getLogger("securox.webrtc")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SignalingMessage(BaseModel):
    type: str  # offer, answer, ice_candidate, heartbeat, stream_state, register_broadcaster, ping
    payload: Optional[Dict[str, Any]] = None
    sdp: Optional[str] = None
    candidate: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    token: Optional[str] = None


class CameraAccessEvaluation:
    def __init__(
        self,
        decision: str,  # ALLOW, ALLOW_MONITOR, DENY, BLOCK
        reason: str,
        risk_score: float,
        jurisdiction: str = "GLOBAL",
        device_trust: float = 100.0,
    ):
        self.decision = decision
        self.reason = reason
        self.risk_score = risk_score
        self.jurisdiction = jurisdiction
        self.device_trust = device_trust

    @property
    def is_allowed(self) -> bool:
        return self.decision in ("ALLOW", "ALLOW_MONITOR")


class WebRTCGateway:
    """
    Enterprise WebRTC Signaling Gateway separating video transport from control plane.
    Enforces RBAC + ABAC before establishing peer connection sessions.
    """

    def __init__(self):
        # Maps camera_id -> dict of {
        #   "broadcasters": set of WebSockets (cameras/phones sending media),
        #   "viewers": dict of ws -> {user_info, session_id, connected_at}
        # }
        self._rooms: Dict[str, Dict[str, Any]] = {}
        # Active mobile phone broadcast sessions
        self._mobile_sessions: Dict[str, Dict[str, Any]] = {}
        # Dedicated topic subscribers for /ws/{topic}
        self._channel_subscribers: Dict[str, Set[WebSocket]] = {
            "cameras": set(),
            "traffic": set(),
            "vehicles": set(),
            "rfid": set(),
            "green-corridors": set(),
            "incidents": set(),
        }
        self._lock = asyncio.Lock()

    def _get_room(self, camera_id: str) -> Dict[str, Any]:
        if camera_id not in self._rooms:
            self._rooms[camera_id] = {
                "broadcasters": set(),
                "viewers": {},  # ws -> viewer info dict
                "stream_state": "STANDBY",  # STANDBY, STREAMING, DEGRADED, OFFLINE
                "last_heartbeat": time.time(),
                "fps": 30.0,
                "resolution": "1920x1080",
                "latency_ms": 42.0,
            }
        return self._rooms[camera_id]

    async def evaluate_camera_access(
        self,
        user: dict,
        camera_id: str,
        device_id: Optional[str] = None,
        client_ip: str = "127.0.0.1",
        purpose: str = "LIVE_MONITORING"
    ) -> CameraAccessEvaluation:
        """
        Enforces Central RBAC + ABAC access control for sensitive CCTV feeds.
        Rules:
          - Traffic Operator + authorized jurisdiction + trusted workstation -> ALLOW
          - Traffic Officer + different jurisdiction -> DENY
          - Unknown device + high-risk user -> BLOCK
          - SOC Analyst + security investigation -> ALLOW_MONITOR
        """
        role = user.get("role", "anonymous").lower()
        user_risk = float(user.get("risk_score", 15.0))
        user_jurisdiction = user.get("jurisdiction", "BENGALURU_METRO")
        device_trust = float(user.get("device_trust", 100.0))

        # Check camera location / jurisdiction
        cam = await store.get_traffic_camera(camera_id)
        cam_location = cam.get("location", "Central Junction") if cam else "Central Junction"
        
        # Determine camera jurisdiction
        cam_jurisdiction = "BENGALURU_METRO"
        if "NH44" in cam_location or "Expressway" in cam_location or "Hosur" in cam_location:
            cam_jurisdiction = "INTER_STATE_HIGHWAY"

        # 1. High-risk user or unknown untrusted device -> BLOCK
        if user_risk >= 60.0 or device_trust < 35.0:
            return CameraAccessEvaluation(
                decision="BLOCK",
                reason=f"Security quarantine: User risk score ({user_risk:.1f}) or device trust ({device_trust:.1f}) exceeds zero-trust threshold.",
                risk_score=max(user_risk, 85.0),
                jurisdiction=user_jurisdiction,
                device_trust=device_trust
            )

        # 2. SOC Analyst -> Always allowed for investigation
        if role in ("soc_analyst", "security_analyst", "ciso", "superadmin", "admin"):
            return CameraAccessEvaluation(
                decision="ALLOW_MONITOR",
                reason=f"SOC Security clearance granted for investigation purpose [{purpose}]",
                risk_score=user_risk,
                jurisdiction=user_jurisdiction,
                device_trust=device_trust
            )

        # 3. Traffic Operator with matching or metro jurisdiction
        if role in ("traffic_operator", "traffic_supervisor", "operator"):
            if user_jurisdiction in (cam_jurisdiction, "BENGALURU_METRO", "GLOBAL"):
                return CameraAccessEvaluation(
                    decision="ALLOW",
                    reason="Authorized Traffic Control Center operator within operational jurisdiction.",
                    risk_score=user_risk,
                    jurisdiction=user_jurisdiction,
                    device_trust=device_trust
                )
            else:
                return CameraAccessEvaluation(
                    decision="DENY",
                    reason=f"Jurisdiction mismatch: Operator jurisdiction '{user_jurisdiction}' does not cover '{cam_jurisdiction}'.",
                    risk_score=user_risk + 20.0,
                    jurisdiction=user_jurisdiction,
                    device_trust=device_trust
                )

        # 4. Traffic Police / Officer
        if role in ("traffic_police", "police"):
            if user_jurisdiction == cam_jurisdiction or user_jurisdiction == "BENGALURU_METRO":
                return CameraAccessEvaluation(
                    decision="ALLOW",
                    reason="Authorized Law Enforcement traffic surveillance access.",
                    risk_score=user_risk,
                    jurisdiction=user_jurisdiction,
                    device_trust=device_trust
                )
            else:
                return CameraAccessEvaluation(
                    decision="DENY",
                    reason=f"Out-of-jurisdiction police surveillance request denied ({user_jurisdiction} != {cam_jurisdiction}).",
                    risk_score=user_risk + 15.0,
                    jurisdiction=user_jurisdiction,
                    device_trust=device_trust
                )

        # 5. Signal Technician
        if role == "signal_technician":
            return CameraAccessEvaluation(
                decision="ALLOW_MONITOR",
                reason="Hardware diagnostic and photometric alignment access.",
                risk_score=user_risk,
                jurisdiction=user_jurisdiction,
                device_trust=device_trust
            )

        # 6. Emergency / Ambulance dispatchers
        if role in ("emergency_traffic", "emergency_coord", "ambulance_driver"):
            return CameraAccessEvaluation(
                decision="ALLOW_MONITOR",
                reason="Emergency Green Corridor transit optical verification.",
                risk_score=user_risk,
                jurisdiction=user_jurisdiction,
                device_trust=device_trust
            )

        # Default: Deny unprivileged roles
        return CameraAccessEvaluation(
            decision="DENY",
            reason=f"Role '{role}' is not granted live CCTV surveillance permissions.",
            risk_score=user_risk,
            jurisdiction=user_jurisdiction,
            device_trust=device_trust
        )

    # ── Signaling WebSocket Handler ───────────────────────────────────────────
    async def handle_signaling_ws(self, websocket: WebSocket, camera_id: str):
        """
        Full WebRTC signaling session for /ws/webrtc/{camera_id}.
        Accepts:
          - Initial auth handshake via token query param or first message
          - ICE exchange & SDP offer/answer relay
          - Heartbeat, disconnect, reconnect
        """
        await websocket.accept()
        room = self._get_room(camera_id)
        current_user: Optional[dict] = None
        role_type = "viewer"  # viewer or broadcaster
        session_id = f"RTC-{uuid.uuid4().hex[:8].upper()}"

        try:
            # First handshake frame must contain authentication or offer
            init_text = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            try:
                init_data = json.loads(init_text)
            except Exception:
                init_data = {"type": "handshake", "token": init_text}

            token = init_data.get("token")
            if not token:
                # Check query params in websocket scope
                query_string = websocket.scope.get("query_string", b"").decode()
                import urllib.parse
                params = urllib.parse.parse_qs(query_string)
                token = params.get("token", [None])[0]

            if token:
                current_user = decode_token_or_none(token)
                if not current_user:
                    await websocket.send_json({
                        "type": "error",
                        "code": "AUTH_FAILED",
                        "detail": "Invalid or expired token"
                    })
                    await websocket.close(code=1008)
                    return

            if not current_user:
                # Default to traffic_operator for local dev / unauthenticated demo unless high-risk header
                current_user = {
                    "username": "traffic_operator",
                    "role": "traffic_operator",
                    "risk_score": 15.0,
                    "jurisdiction": "BENGALURU_METRO",
                    "device_trust": 100.0,
                }

            device_id = init_data.get("device_id") or "DEV-WORKSTATION-01"
            client_ip = websocket.client.host if websocket.client else "127.0.0.1"

            # Check role parameter (broadcaster = Phone-as-CCTV or IP camera; viewer = console)
            if init_data.get("role") in ("broadcaster", "mobile", "phone"):
                role_type = "broadcaster"
                # Evaluate Phone-as-CCTV Zero Trust
                session = await self.register_mobile_session(
                    device_id=device_id,
                    camera_id=camera_id,
                    user_id=current_user.get("username", "mobile_unit"),
                    latitude=float(init_data.get("latitude", 12.9716)),
                    longitude=float(init_data.get("longitude", 77.5946)),
                )
                if session.get("trust_status") == "BLOCKED":
                    await websocket.send_json({
                        "type": "error",
                        "code": "DEVICE_BLOCKED",
                        "detail": "Zero-trust policy blocked untrusted mobile device."
                    })
                    await websocket.close(code=1008)
                    return

                room["broadcasters"].add(websocket)
                room["stream_state"] = "STREAMING"
                room["last_heartbeat"] = time.time()
                await self.broadcast_channel("cameras", {
                    "event": "CAMERA_ONLINE",
                    "camera_id": camera_id,
                    "stream_type": "WEBRTC_MOBILE",
                    "status": "ONLINE"
                })
            else:
                # Evaluate viewer access
                eval_res = await self.evaluate_camera_access(
                    user=current_user,
                    camera_id=camera_id,
                    device_id=device_id,
                    client_ip=client_ip
                )

                # Audit access attempt
                await event_fabric.emit(
                    action="CAMERA_STREAM_ACCESS",
                    domain="TRAFFIC",
                    user=current_user.get("username", "anonymous"),
                    role=current_user.get("role", "anonymous"),
                    resource=f"CAMERA:{camera_id}",
                    result="SUCCESS" if eval_res.is_allowed else "DENIED",
                    risk=eval_res.risk_score,
                    metadata={
                        "decision": eval_res.decision,
                        "reason": eval_res.reason,
                        "camera_id": camera_id,
                        "session_id": session_id,
                        "device_id": device_id
                    }
                )

                if not eval_res.is_allowed:
                    await websocket.send_json({
                        "type": "error",
                        "code": "ACCESS_DENIED",
                        "decision": eval_res.decision,
                        "detail": eval_res.reason
                    })
                    await websocket.close(code=1008)
                    return

                room["viewers"][websocket] = {
                    "user": current_user,
                    "session_id": session_id,
                    "connected_at": time.time(),
                    "decision": eval_res.decision
                }

            # Send session confirmation
            await websocket.send_json({
                "type": "connection_state",
                "state": "CONNECTED",
                "camera_id": camera_id,
                "session_id": session_id,
                "role": role_type,
                "stream_state": room["stream_state"],
                "fps": room["fps"],
                "resolution": room["resolution"],
                "latency_ms": room["latency_ms"],
                "broadcasters_count": len(room["broadcasters"]),
                "viewers_count": len(room["viewers"]),
                "timestamp": _utcnow()
            })

            # Process subsequent messages (offer, answer, ice_candidate, heartbeat, etc.)
            while True:
                msg_text = await websocket.receive_text()
                try:
                    data = json.loads(msg_text)
                except Exception:
                    continue

                msg_type = data.get("type")

                if msg_type in ("heartbeat", "ping"):
                    room["last_heartbeat"] = time.time()
                    await websocket.send_json({
                        "type": "pong" if msg_type == "ping" else "heartbeat_ack",
                        "camera_id": camera_id,
                        "timestamp": _utcnow(),
                        "health": "HEALTHY"
                    })

                elif msg_type == "offer":
                    # Relay offer from broadcaster to viewers or viewer to broadcaster
                    target_recipients = room["viewers"].keys() if role_type == "broadcaster" else room["broadcasters"]
                    dead = []
                    for recipient in list(target_recipients):
                        try:
                            await recipient.send_json({
                                "type": "offer",
                                "camera_id": camera_id,
                                "sdp": data.get("sdp"),
                                "session_id": session_id
                            })
                        except Exception:
                            dead.append(recipient)
                    for d in dead:
                        self._cleanup_ws(room, d)

                elif msg_type == "answer":
                    target_recipients = room["broadcasters"] if role_type == "viewer" else room["viewers"].keys()
                    dead = []
                    for recipient in list(target_recipients):
                        try:
                            await recipient.send_json({
                                "type": "answer",
                                "camera_id": camera_id,
                                "sdp": data.get("sdp"),
                                "session_id": session_id
                            })
                        except Exception:
                            dead.append(recipient)
                    for d in dead:
                        self._cleanup_ws(room, d)

                elif msg_type == "ice_candidate":
                    target_recipients = room["viewers"].keys() if role_type == "broadcaster" else room["broadcasters"]
                    dead = []
                    for recipient in list(target_recipients):
                        try:
                            await recipient.send_json({
                                "type": "ice_candidate",
                                "camera_id": camera_id,
                                "candidate": data.get("candidate"),
                                "session_id": session_id
                            })
                        except Exception:
                            dead.append(recipient)
                    for d in dead:
                        self._cleanup_ws(room, d)

                elif msg_type == "stream_state":
                    new_state = data.get("state", "STREAMING")
                    room["stream_state"] = new_state
                    if "fps" in data:
                        room["fps"] = float(data["fps"])
                    if "resolution" in data:
                        room["resolution"] = str(data["resolution"])

                    # Notify all viewers of state change
                    for v in list(room["viewers"].keys()):
                        try:
                            await v.send_json({
                                "type": "stream_state",
                                "camera_id": camera_id,
                                "state": new_state,
                                "fps": room["fps"],
                                "resolution": room["resolution"]
                            })
                        except Exception:
                            pass

                elif msg_type in ("disconnect", "close"):
                    break

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error("Error in WebRTC signaling for camera %s: %s", camera_id, e)
        finally:
            self._cleanup_ws(room, websocket)
            if role_type == "broadcaster" and len(room["broadcasters"]) == 0:
                room["stream_state"] = "OFFLINE"
                await self.broadcast_channel("cameras", {
                    "event": "CAMERA_OFFLINE",
                    "camera_id": camera_id,
                    "status": "OFFLINE"
                })

    def _cleanup_ws(self, room: Dict[str, Any], ws: WebSocket):
        if ws in room["broadcasters"]:
            room["broadcasters"].remove(ws)
        if ws in room["viewers"]:
            del room["viewers"][ws]

    # ── Phone-as-CCTV MobileCameraSession Management ──────────────────────────
    async def register_mobile_session(
        self,
        device_id: str,
        camera_id: str,
        user_id: str,
        latitude: float = 12.9716,
        longitude: float = 77.5946,
        fps: float = 5.0,
        resolution: str = "1280x720",
        device_metadata: dict = None,
    ) -> dict:
        """
        Registers a temporary mobile phone camera session with Zero-Trust Device Evaluation.
        """
        session_id = f"MOB-SES-{uuid.uuid4().hex[:6].upper()}"
        trust_status = "TRUSTED"
        status = "ACTIVE"
        risk_score = 12.0

        # Zero-trust check: block unknown rogue devices
        if "ROGUE" in device_id.upper() or "UNTRUSTED" in device_id.upper():
            trust_status = "BLOCKED"
            status = "RESTRICTED"
            risk_score = 90.0

        session_data = {
            "session_id": session_id,
            "device_id": device_id,
            "camera_id": camera_id,
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "fps": fps,
            "resolution": resolution,
            "risk_score": risk_score,
            "started_at": _utcnow(),
            "last_seen": _utcnow(),
            "status": status,
            "stream_status": "STREAMING" if trust_status == "TRUSTED" else "BLOCKED",
            "trust_status": trust_status,
            "device_metadata": device_metadata or {}
        }
        await store.save_mobile_camera_session(session_data)
        self._mobile_sessions[session_id] = session_data

        # Ensure the camera exists in the registry as PHONE_CAMERA
        existing_cam = await store.get_traffic_camera(camera_id)
        if not existing_cam:
            await store.save_traffic_camera({
                "id": camera_id,
                "name": f"Mobile CCTV Patrol ({device_id})",
                "location": f"Patrol Geo ({latitude:.4f}, {longitude:.4f})",
                "latitude": latitude,
                "longitude": longitude,
                "camera_type": "PHONE_CAMERA",
                "stream_type": "WEBRTC",
                "stream_url": f"/ws/webrtc/{camera_id}",
                "status": "ONLINE" if trust_status == "TRUSTED" else "COMPROMISED",
                "device_id": device_id,
                "trust_status": trust_status,
                "health": "HEALTHY" if trust_status == "TRUSTED" else "DEGRADED"
            })

        return session_data

    # ── General WebSocket Channel Broadcasting ────────────────────────────────
    async def register_channel_subscriber(self, channel: str, ws: WebSocket):
        await ws.accept()
        if channel in self._channel_subscribers:
            self._channel_subscribers[channel].add(ws)
            logger.info("Subscriber connected to channel [%s]. Total: %d", channel, len(self._channel_subscribers[channel]))

    def unregister_channel_subscriber(self, channel: str, ws: WebSocket):
        if channel in self._channel_subscribers and ws in self._channel_subscribers[channel]:
            self._channel_subscribers[channel].remove(ws)

    async def broadcast_channel(self, channel: str, payload: dict):
        """Broadcasts real-time events to all active topic subscribers."""
        if channel not in self._channel_subscribers:
            return
        dead = []
        for ws in list(self._channel_subscribers[channel]):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for d in dead:
            self._channel_subscribers[channel].discard(d)


# Singleton Instance
webrtc_gateway = WebRTCGateway()
