"""
Securox — Unified Central Security Event Fabric

Every critical action across Healthcare, Traffic, Finance, and Security
feeds this canonical 14-field event architecture.

Canonical Event Schema:
  1.  event_id      (str, UUID/EVT-*)
  2.  timestamp     (str, ISO UTC)
  3.  domain        (str: HEALTHCARE, TRAFFIC, FINANCE, SECURITY, PLATFORM)
  4.  organization  (str: e.g. 'City General Hospital (H001)', 'State Apex Municipal Bank')
  5.  user          (str: username or system identity)
  6.  role          (str: user role, e.g. doctor, traffic_operator, fraud_analyst)
  7.  device        (str: client device identifier or IP host)
  8.  ip            (str: client IP address)
  9.  location      (str: physical or network facility location)
  10. resource      (str: target resource, e.g. PATIENT:P-1001, SIGNAL:SIG-01, TX:TX-9001)
  11. action        (str: LOGIN, LOGOUT, PATIENT_ACCESS, MEDICAL_RECORD_UPDATE, BREAK_GLASS,
                          AMBULANCE_ASSIGNMENT, SIGNAL_OVERRIDE, CAMERA_ACCESS, CAMERA_FAILURE,
                          TRANSACTION, FRAUD_ALERT, AML_ALERT, ACCESS_DENIED, DEVICE_REGISTERED,
                          POLICY_CHANGE, INCIDENT_CREATED)
  12. result        (str: SUCCESS, BLOCKED, FLAGGED, OVERRIDDEN, DENIED, FAILED)
  13. risk          (float: 0.0 to 100.0)
  14. metadata      (dict: structured arbitrary context payload)

Architecture Components:
  • Event Ingestion   : Ingests raw or validated event dicts / SecurityEvent objects.
  • Event Persistence : Saves to SQLite/PostgreSQL `security_events` table via DataStore.
  • Event Streaming   : Pub/Sub broker with Redis support and in-memory asyncio.Queue fallback.
  • Event Subscribers : Allows arbitrary async subscribers, risk monitors, and WebSockets to listen.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

from core.store import store

logger = logging.getLogger("securox.event_fabric")

DOMAIN_ORGANIZATIONS = {
    "HEALTHCARE": "City General Hospital (H001)",
    "TRAFFIC": "Bengaluru Smart Mobility SCADA",
    "FINANCE": "State Apex Municipal Bank",
    "SECURITY": "Pan-City Unified SOC Command",
    "PLATFORM": "Securox Core Platform",
}

CANONICAL_ACTIONS = {
    "LOGIN",
    "LOGOUT",
    "PATIENT_ACCESS",
    "MEDICAL_RECORD_UPDATE",
    "BREAK_GLASS",
    "AMBULANCE_ASSIGNMENT",
    "SIGNAL_OVERRIDE",
    "CAMERA_ACCESS",
    "CAMERA_FAILURE",
    "TRANSACTION",
    "FRAUD_ALERT",
    "AML_ALERT",
    "ACCESS_DENIED",
    "DEVICE_REGISTERED",
    "POLICY_CHANGE",
    "INCIDENT_CREATED",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:10].upper()}")
    timestamp: str = Field(default_factory=_utcnow)
    domain: str
    organization: Optional[str] = None
    user: str
    role: str
    device: Optional[str] = "DEV-CLIENT-01"
    ip: Optional[str] = Field(default="127.0.0.1", alias="IP")
    location: Optional[str] = "Universal Command"
    resource: str
    action: str
    result: str = "SUCCESS"
    risk: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


SubscriberCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class EventFabric:
    """
    Central Event Fabric connecting all domain operations,
    audit streams, risk engines, and WebSocket clients.
    """

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._callbacks: List[SubscriberCallback] = []
        self._ws_connections: Set[Any] = set()
        self._redis_client = None
        self._redis_enabled = False
        self._lock = asyncio.Lock()
        self._init_redis()

    def _init_redis(self):
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis_client = aioredis.from_url(redis_url, decode_responses=True)
                self._redis_enabled = True
                logger.info("EventFabric connected to Redis Pub/Sub: %s", redis_url)
            except Exception as e:
                logger.warning("Redis configured at %s but failed to connect: %s. Using in-memory fallback.", redis_url, e)
                self._redis_client = None
                self._redis_enabled = False
        else:
            logger.info("EventFabric using high-throughput in-memory async pub-sub (no REDIS_URL supplied).")

    # ── WebSocket Management ─────────────────────────────────────────────

    async def register_websocket(self, websocket: Any):
        async with self._lock:
            self._ws_connections.add(websocket)
        logger.info("WebSocket client registered. Total active: %d", len(self._ws_connections))

    async def unregister_websocket(self, websocket: Any):
        async with self._lock:
            self._ws_connections.discard(websocket)
        logger.info("WebSocket client unregistered. Total active: %d", len(self._ws_connections))

    async def broadcast_to_websockets(self, event_dict: Dict[str, Any]):
        if not self._ws_connections:
            return

        dead_connections = []
        payload = {
            "type": "SECURITY_EVENT",
            "event": event_dict
        }

        # Safe broadcast without holding lock during network I/O
        async with self._lock:
            active = list(self._ws_connections)

        for ws in active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_connections.append(ws)

        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    self._ws_connections.discard(ws)

    # ── In-Process Subscribers ───────────────────────────────────────────

    def subscribe_queue(self, queue: asyncio.Queue):
        self._subscribers.add(queue)

    def unsubscribe_queue(self, queue: asyncio.Queue):
        self._subscribers.discard(queue)

    def add_callback(self, callback: SubscriberCallback):
        self._callbacks.append(callback)

    # ── Ingestion & Persistence & Streaming ──────────────────────────────

    async def ingest_event(self, event: Union[SecurityEvent, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingests a security event, applies defaults, persists to DB,
        and broadcasts to streaming subscribers and WebSockets.
        """
        if isinstance(event, SecurityEvent):
            event_dict = event.model_dump(by_alias=True)
        else:
            event_dict = dict(event)

        # Standardize 14 fields
        if not event_dict.get("event_id"):
            event_dict["event_id"] = f"EVT-{uuid.uuid4().hex[:10].upper()}"
        if not event_dict.get("timestamp"):
            event_dict["timestamp"] = _utcnow()
        if "domain" in event_dict:
            event_dict["domain"] = event_dict["domain"].upper()
        else:
            event_dict["domain"] = "SECURITY"

        if not event_dict.get("organization"):
            event_dict["organization"] = DOMAIN_ORGANIZATIONS.get(
                event_dict["domain"], "Securox Smart City Infrastructure"
            )

        if not event_dict.get("user"):
            event_dict["user"] = "system"
        if not event_dict.get("role"):
            event_dict["role"] = "system"
        if not event_dict.get("device"):
            event_dict["device"] = "SEC-GW-01"
        client_ip = event_dict.get("ip") or event_dict.get("IP") or "127.0.0.1"
        event_dict["ip"] = client_ip
        event_dict["IP"] = client_ip
        if not event_dict.get("location"):
            event_dict["location"] = "Command Facility"
        if not event_dict.get("resource"):
            event_dict["resource"] = "SYSTEM"
        if not event_dict.get("action"):
            event_dict["action"] = "SYSTEM_EVENT"
        else:
            event_dict["action"] = event_dict["action"].upper()
        if not event_dict.get("result"):
            event_dict["result"] = "SUCCESS"
        else:
            event_dict["result"] = event_dict["result"].upper()

        event_dict["risk"] = float(event_dict.get("risk", 0.0))
        if "metadata" not in event_dict or not isinstance(event_dict["metadata"], dict):
            event_dict["metadata"] = {}

        # 1a. Domain AI Model Mesh Inferences (Probabilistic Inferences)
        try:
            from services.ai_models.health_monitor import ai_model_registry
            ai_eval = await ai_model_registry.evaluate_event(event_dict)
            if ai_eval.get("ai_detections"):
                event_dict["metadata"]["ai_detections"] = {
                    **event_dict.get("metadata", {}).get("ai_detections", {}),
                    **ai_eval["ai_detections"]
                }
            if ai_eval.get("inferences"):
                event_dict["metadata"]["ai_inferences"] = ai_eval["inferences"]
        except Exception as e:
            logger.debug("AI Model Registry event evaluation error: %s", e)

        # 1b. Event Persistence
        try:
            persisted = await store.save_security_event(event_dict)
        except Exception as e:
            logger.error("Failed to persist security event %s: %s", event_dict["event_id"], e)
            persisted = event_dict

        # 1b. Central Cyber-Risk Assessment (Consume Event)
        try:
            from services.cyber_risk_engine import cyber_risk_engine
            assessment = await cyber_risk_engine.consume_event(persisted)
            persisted["risk_category"] = assessment.risk_category
            persisted["assessment_id"] = assessment.assessment_id
            persisted["risk_factors"] = [f.model_dump() for f in assessment.factors]
            persisted["risk_explanation"] = assessment.explanation
            persisted["evaluated_risk"] = assessment.risk_score
            if "risk" not in event_dict or event_dict["risk"] is None:
                persisted["risk"] = assessment.risk_score
        except Exception as e:
            logger.warning("Central CyberRiskEngine consumer error: %s", e)

        # 2. Redis Pub/Sub Streaming (if available)
        if self._redis_enabled and self._redis_client:
            try:
                await self._redis_client.publish(
                    "securox:events",
                    json.dumps(persisted, default=str)
                )
            except Exception as e:
                logger.warning("Redis publish failed, falling back to local bus: %s", e)

        # 3. Stream to In-Process Queues
        for q in list(self._subscribers):
            try:
                q.put_nowait(persisted)
            except asyncio.QueueFull:
                pass

        # 4. Stream to Callbacks
        for cb in self._callbacks:
            try:
                asyncio.create_task(cb(persisted))
            except Exception as e:
                logger.error("Subscriber callback failed: %s", e)

        # 5. Broadcast to WebSockets
        try:
            await self.broadcast_to_websockets(persisted)
        except Exception as e:
            logger.error("WebSocket broadcast error: %s", e)

        return persisted

    # ── Convenience Emit Helper ──────────────────────────────────────────

    async def emit(
        self,
        action: str,
        domain: str,
        user: str,
        role: str,
        resource: str,
        result: str = "SUCCESS",
        risk: float = 0.0,
        organization: Optional[str] = None,
        device: Optional[str] = None,
        ip: Optional[str] = None,
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        One-liner convenience method to emit a canonical security event
        from any controller, endpoint, or background task.
        """
        event_dict = {
            "action": action,
            "domain": domain,
            "user": user,
            "role": role,
            "resource": resource,
            "result": result,
            "risk": risk,
            "organization": organization,
            "device": device,
            "ip": ip,
            "location": location,
            "metadata": metadata or {}
        }
        return await self.ingest_event(event_dict)



    async def _redis_listener(self):
        """Listens on Redis pub/sub channel and dispatches to local consumers."""
        if not self._redis_enabled or not self._redis_client:
            return
        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe("securox:events")
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        event_data = json.loads(msg["data"])
                        # Broadcast to local in-process queues & WebSockets
                        for q in list(self._subscribers):
                            try:
                                q.put_nowait(event_data)
                            except asyncio.QueueFull:
                                pass
                        for cb in self._callbacks:
                            try:
                                asyncio.create_task(cb(event_data))
                            except Exception:
                                pass
                        await self.broadcast_to_websockets(event_data)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Redis pub/sub listener interrupted: %s", e)


event_fabric = EventFabric()

