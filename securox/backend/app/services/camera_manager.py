"""
Securox — Secure Camera Manager Service
Handles registration of IP cameras, encrypted storage of passwords,
connection health monitoring, and camera security anomaly detection (tamper, blur, ddos, hijack).
"""

import os
import json
import logging
import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet

from core.store import store
try:
    from services.event_fabric import event_fabric
except ImportError:
    event_fabric = None

logger = logging.getLogger("securox.camera_manager")

CAMERAS_FILE = "database/cameras.json"
KEY_FILE = "database/camera_key.key"

class CameraManager:
    def __init__(self):
        self.cameras: Dict[str, dict] = {}
        self.fernet: Optional[Fernet] = None
        self._lock = asyncio.Lock()
        self._running = False
        
        # In-memory transient health/anomaly states for live cameras
        # keys: cam_id -> status dict
        self.anomaly_states: Dict[str, dict] = {}
        self._callbacks = []

        self._init_crypto()
        self._load_cameras()

    def _init_crypto(self):
        """Initializes the Fernet encryption key, creating one if not exists."""
        try:
            os.makedirs("database", exist_ok=True)
            if os.path.exists(KEY_FILE):
                with open(KEY_FILE, "rb") as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(KEY_FILE, "wb") as f:
                    f.write(key)
            self.fernet = Fernet(key)
        except Exception as e:
            logger.error("Failed to initialize camera encryption key: %s", e)
            # Fallback to ephemeral key in memory
            self.fernet = Fernet(Fernet.generate_key())

    def _load_cameras(self):
        """Loads cameras from the persisted JSON storage."""
        try:
            if os.path.exists(CAMERAS_FILE):
                with open(CAMERAS_FILE, "r") as f:
                    data = json.load(f)
                    for cam_id, cam in data.items():
                        # Initialize transient state
                        self.anomaly_states[cam_id] = {
                            "status": "online",
                            "blur_score": 15.0, # baseline
                            "is_frozen": False,
                            "is_covered": False,
                            "is_ddos": False,
                            "is_hijacked": False,
                            "last_checked": datetime.now(timezone.utc).isoformat(),
                            "anomalies": []
                        }
                    self.cameras = data
            else:
                # Pre-seed a default smart-city traffic camera
                default_id = "CAM_TRAFFIC_01"
                self.cameras[default_id] = {
                    "id": default_id,
                    "name": "Smart Highway CCTV - Sector 4",
                    "ip": "192.168.45.10",
                    "port": 8554,
                    "protocol": "rtsp",
                    "brand": "generic",
                    "username": "admin",
                    "encrypted_password": self.encrypt_password("cctvpass123"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                self.anomaly_states[default_id] = {
                    "status": "online",
                    "blur_score": 15.0,
                    "is_frozen": False,
                    "is_covered": False,
                    "is_ddos": False,
                    "is_hijacked": False,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                    "anomalies": []
                }
                self._save_cameras()
        except Exception as e:
            logger.error("Failed to load cameras: %s", e)

    def _save_cameras(self):
        """Persists registered cameras to JSON."""
        try:
            os.makedirs("database", exist_ok=True)
            with open(CAMERAS_FILE, "w") as f:
                json.dump(self.cameras, f, indent=2)
        except Exception as e:
            logger.error("Failed to save cameras: %s", e)

    def encrypt_password(self, password: str) -> str:
        if self.fernet:
            return self.fernet.encrypt(password.encode()).decode()
        return password

    def decrypt_password(self, encrypted_password: str) -> str:
        if self.fernet:
            try:
                return self.fernet.decrypt(encrypted_password.encode()).decode()
            except Exception:
                logger.error("Decryption of camera password failed.")
                return "decryption_error"
        return encrypted_password

    # ── CRUD Endpoints ────────────────────────────────────────────────────────
    async def register_camera(self, name: str, ip: str, port: int, protocol: str, username: str, password: str, brand: str = "generic", serial_number: str = "", connection_type: str = "ip") -> dict:
        async with self._lock:
            cam_id = f"CAM_{uuid.uuid4().hex[:8].upper()}"
            camera = {
                "id": cam_id,
                "name": name,
                "ip": ip or "",
                "port": port,
                "protocol": protocol,
                "brand": brand,
                "username": username,
                "serial_number": serial_number,
                "connection_type": connection_type,  # "ip" or "p2p"
                "encrypted_password": self.encrypt_password(password),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.cameras[cam_id] = camera
            self.anomaly_states[cam_id] = {
                "status": "online",
                "blur_score": 15.0,
                "is_frozen": False,
                "is_covered": False,
                "is_ddos": False,
                "is_hijacked": False,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "anomalies": []
            }
            self._save_cameras()
            return camera

    async def get_all_cameras(self) -> List[dict]:
        async with self._lock:
            # Strip passwords for security
            output = []
            for cam_id, cam in self.cameras.items():
                cam_copy = cam.copy()
                cam_copy.pop("encrypted_password", None)
                cam_copy["status"] = self.anomaly_states.get(cam_id, {}).get("status", "unknown")
                output.append(cam_copy)
            return output

    async def get_camera_status(self, cam_id: str) -> Optional[dict]:
        async with self._lock:
            if cam_id in self.cameras:
                state = self.anomaly_states.get(cam_id, {}).copy()
                cam_details = self.cameras[cam_id].copy()
                cam_details.pop("encrypted_password", None)
                return {**cam_details, "state": state}
            return None

    async def delete_camera(self, cam_id: str) -> bool:
        async with self._lock:
            if cam_id in self.cameras:
                del self.cameras[cam_id]
                if cam_id in self.anomaly_states:
                    del self.anomaly_states[cam_id]
                self._save_cameras()
                return True
            return False

    # ── Simulation & Testing Anomaly Injection ────────────────────────────────
    async def inject_anomaly(self, cam_id: str, anomaly_type: str, enable: bool) -> dict:
        """
        Simulates camera stream tamper anomalies for demo/judging flow.
        Supported types: 'blur', 'ddos', 'freeze', 'cover', 'hijack'
        """
        async with self._lock:
            if cam_id not in self.anomaly_states:
                raise ValueError("Camera not found")
            
            state = self.anomaly_states[cam_id]
            state["last_checked"] = datetime.now(timezone.utc).isoformat()
            
            if anomaly_type == "blur":
                state["blur_score"] = 95.0 if enable else 15.0
            elif anomaly_type == "ddos":
                state["is_ddos"] = enable
            elif anomaly_type == "freeze":
                state["is_frozen"] = enable
            elif anomaly_type == "cover":
                state["is_covered"] = enable
            elif anomaly_type == "hijack":
                state["is_hijacked"] = enable
            
            # Determine overall health status
            anomalies = []
            if state.get("blur_score", 15.0) > 80.0:
                anomalies.append("CAMERA_TAMPER_BLUR")
            if state.get("is_frozen"):
                anomalies.append("CAMERA_TAMPER_FREEZE")
            if state.get("is_covered"):
                anomalies.append("CAMERA_TAMPER_COVER")
            if state.get("is_ddos"):
                anomalies.append("CAMERA_DDOS_ATTACK")
            if state.get("is_hijacked"):
                anomalies.append("CAMERA_STREAM_HIJACK")
                
            state["anomalies"] = anomalies
            
            if any([state["is_ddos"], state["is_hijacked"]]):
                state["status"] = "compromised"
            elif any([state["blur_score"] > 80.0, state["is_frozen"], state["is_covered"]]):
                state["status"] = "degraded"
            else:
                state["status"] = "online"

            # Notify callbacks
            for cb in self._callbacks:
                try:
                    await cb(cam_id, state)
                except Exception as e:
                    logger.error("Error in camera state update callback: %s", e)

            return state

    def on_state_update(self, callback):
        self._callbacks.append(callback)

    # ── Background Connection Monitor ──────────────────────────────────────────
    async def start_monitoring(self):
        self._running = True
        logger.info("Camera security monitoring loop active.")
        while self._running:
            try:
                await self._monitor_cycle()
            except Exception as e:
                logger.error("Error in camera monitoring cycle: %s", e)
            await asyncio.sleep(8)

    def stop_monitoring(self):
        self._running = False

    async def _monitor_cycle(self):
        """Simulates actual camera connectivity health checks."""
        async with self._lock:
            for cam_id, cam in self.cameras.items():
                state = self.anomaly_states.setdefault(cam_id, {
                    "status": "online",
                    "blur_score": 15.0,
                    "is_frozen": False,
                    "is_covered": False,
                    "is_ddos": False,
                    "is_hijacked": False,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                    "anomalies": []
                })
                
                # Check connection status simulation
                # If a camera is simulated to have DDoS, ping might fail
                if state["is_ddos"]:
                    state["status"] = "compromised"
                    if "CAMERA_DDOS_ATTACK" not in state["anomalies"]:
                        state["anomalies"].append("CAMERA_DDOS_ATTACK")
                elif state["is_hijacked"]:
                    state["status"] = "compromised"
                    if "CAMERA_STREAM_HIJACK" not in state["anomalies"]:
                        state["anomalies"].append("CAMERA_STREAM_HIJACK")
                else:
                    # Let's say normally it's online
                    # Small random fluctuate of baseline blur score if normal
                    if not state.get("blur_score", 15.0) > 80.0:
                        state["blur_score"] = max(5.0, min(30.0, state["blur_score"] + os.urandom(1)[0] % 5 - 2))
                    
                state["last_checked"] = datetime.now(timezone.utc).isoformat()
                
                # Callback notification
                for cb in self._callbacks:
                    try:
                        await cb(cam_id, state)
                    except Exception as e:
                        logger.error("Callback error during monitoring: %s", e)

    # ── Advanced Traffic Intelligence Operations ─────────────────────────────
    async def register_traffic_camera(self, cam_data: dict) -> dict:
        """Registers a camera entity into both persistent DB store and transient monitoring."""
        cam_id = cam_data.get("id") or cam_data.get("camera_id") or f"CAM_{uuid.uuid4().hex[:6].upper()}"
        cam_data["id"] = cam_id
        cam_data["camera_id"] = cam_id

        # Save to persistent store
        saved = await store.save_traffic_camera(cam_data)

        # Track transient monitoring state
        async with self._lock:
            self.cameras[cam_id] = {
                "id": cam_id,
                "name": cam_data.get("name") or cam_data.get("camera_name", f"Camera {cam_id}"),
                "location": cam_data.get("location", "City Grid"),
                "ip": cam_data.get("ip", "10.12.4.10"),
                "port": cam_data.get("port", 554),
                "protocol": cam_data.get("protocol", "rtsp"),
                "brand": cam_data.get("brand", "generic"),
                "camera_type": cam_data.get("camera_type", "FIXED_CCTV"),
                "stream_type": cam_data.get("stream_type", "WEBRTC"),
                "stream_url": cam_data.get("stream_url", f"/api/traffic/stream/{cam_id}"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.anomaly_states[cam_id] = {
                "status": "online",
                "health": "HEALTHY",
                "blur_score": 15.0,
                "is_frozen": False,
                "is_covered": False,
                "is_ddos": False,
                "is_hijacked": False,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "anomalies": []
            }
            self._save_cameras()

        if event_fabric:
            await event_fabric.emit(
                action="CAMERA_REGISTERED",
                domain="TRAFFIC",
                user="traffic_operator",
                role="traffic_operator",
                resource=f"CAMERA:{cam_id}",
                result="SUCCESS",
                risk=0.0,
                metadata={"camera_id": cam_id, "camera_type": cam_data.get("camera_type", "FIXED_CCTV")}
            )
        return saved

    async def start_stream(self, cam_id: str) -> dict:
        """Starts live stream for a camera, transitioning status to ONLINE / STREAMING."""
        cam = await store.get_traffic_camera(cam_id)
        if not cam:
            raise ValueError(f"Camera {cam_id} not found")

        updated = await store.update_traffic_camera(cam_id, {
            "status": "ONLINE",
            "health": "HEALTHY",
            "last_seen": datetime.now(timezone.utc).isoformat()
        })

        async with self._lock:
            if cam_id in self.anomaly_states:
                self.anomaly_states[cam_id]["status"] = "online"
                self.anomaly_states[cam_id]["health"] = "HEALTHY"

        if event_fabric:
            await event_fabric.emit(
                action="CAMERA_STREAM_STARTED",
                domain="TRAFFIC",
                user="traffic_operator",
                role="traffic_operator",
                resource=f"CAMERA:{cam_id}",
                result="SUCCESS",
                risk=0.0,
                metadata={"camera_id": cam_id, "stream_type": cam.get("stream_type", "WEBRTC")}
            )
        return {
            "status": "started",
            "camera_id": cam_id,
            "stream_url": cam.get("stream_url", f"/api/traffic/stream/{cam_id}"),
            "stream_type": cam.get("stream_type", "WEBRTC"),
            "fps": cam.get("fps", 30.0),
            "resolution": cam.get("resolution", "1920x1080")
        }

    async def stop_stream(self, cam_id: str) -> dict:
        """Stops live stream for a camera."""
        cam = await store.get_traffic_camera(cam_id)
        if not cam:
            raise ValueError(f"Camera {cam_id} not found")

        updated = await store.update_traffic_camera(cam_id, {
            "status": "STANDBY",
            "last_seen": datetime.now(timezone.utc).isoformat()
        })

        if event_fabric:
            await event_fabric.emit(
                action="CAMERA_STREAM_STOPPED",
                domain="TRAFFIC",
                user="traffic_operator",
                role="traffic_operator",
                resource=f"CAMERA:{cam_id}",
                result="SUCCESS",
                risk=0.0,
                metadata={"camera_id": cam_id}
            )
        return {"status": "stopped", "camera_id": cam_id}

    async def get_stream_info(self, cam_id: str) -> dict:
        """Returns WebRTC / RTSP stream metadata, connection state and telemetry."""
        cam = await store.get_traffic_camera(cam_id)
        if not cam:
            raise ValueError(f"Camera {cam_id} not found")

        transient = self.anomaly_states.get(cam_id, {})
        return {
            "camera_id": cam_id,
            "camera_name": cam.get("name"),
            "stream_type": cam.get("stream_type", "WEBRTC"),
            "stream_url": cam.get("stream_url", f"/api/traffic/stream/{cam_id}"),
            "signaling_url": f"/ws/webrtc/{cam_id}",
            "status": transient.get("status", cam.get("status", "ONLINE")),
            "health": transient.get("health", cam.get("health", "HEALTHY")),
            "fps": cam.get("fps", 30.0),
            "resolution": cam.get("resolution", "1920x1080"),
            "latency_ms": cam.get("latency_ms", 42.0),
            "anomalies": transient.get("anomalies", []),
            "trust_status": cam.get("trust_status", "TRUSTED"),
            "risk_score": cam.get("risk_score", 0.0),
            "last_seen": cam.get("last_seen")
        }

    async def report_camera_failure(self, cam_id: str, reason: str, severity: str = "HIGH") -> dict:
        """Reports hardware, connectivity or optical failure for a camera."""
        updated = await store.update_traffic_camera(cam_id, {
            "status": "OFFLINE",
            "health": "FAILED",
            "risk_score": 75.0 if severity == "HIGH" else 90.0
        })
        async with self._lock:
            if cam_id in self.anomaly_states:
                self.anomaly_states[cam_id]["status"] = "offline"
                self.anomaly_states[cam_id]["health"] = "FAILED"
                self.anomaly_states[cam_id]["anomalies"].append(f"FAILURE_{reason.upper().replace(' ', '_')}")

        if event_fabric:
            await event_fabric.emit(
                action="CAMERA_OFFLINE",
                domain="TRAFFIC",
                user="signal_technician",
                role="signal_technician",
                resource=f"CAMERA:{cam_id}",
                result="FAILURE",
                risk=75.0,
                metadata={"camera_id": cam_id, "reason": reason, "severity": severity}
            )
        return {"status": "reported", "camera_id": cam_id, "reason": reason}

# Singleton Instance
camera_manager = CameraManager()

