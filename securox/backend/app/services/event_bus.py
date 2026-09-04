"""
Securox X v7.0 event bus.

Small in-process async bus for the modular FastAPI monolith. It normalizes
domain events, keeps a replay buffer, and lets the websocket gateway subscribe
without coupling every service directly to ConnectionManager.
"""

import asyncio
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Awaitable, Callable

from database.store import store

EVENT_ALIASES = {
    "alert": "threat_update",
    "risk_update": "threat_update",
    "stig_update": "traffic_update",
    "green_corridor_active": "emergency_update",
    "camera_security_update": "camera_update",
    "propagation": "cascade_update",
    "mitigation": "mitigation_update",
    "mitigation_step_executed": "mitigation_update",
    "incident_update": "incident_update",
}


Subscriber = Callable[[dict], Awaitable[None]]


class EventBus:
    def __init__(self, max_events: int = 1000):
        self._events = deque(maxlen=max_events)
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, handler: Subscriber) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: dict | list | None = None, **metadata) -> dict:
        normalized_type = EVENT_ALIASES.get(event_type, event_type)
        event = {
            "id": str(uuid.uuid4()),
            "type": normalized_type,
            "source_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data if data is not None else {},
            "metadata": metadata,
        }
        async with self._lock:
            self._events.appendleft(event)
        await store.add_event(event)

        handlers = list(self._subscribers.get(normalized_type, []))
        handlers += self._subscribers.get("*", [])
        for handler in handlers:
            asyncio.create_task(handler(event))
        return event

    async def replay(self, event_type: str | None = None, limit: int = 100) -> list[dict]:
        persisted = await store.get_events(limit=limit, event_type=event_type)
        if persisted:
            return persisted
        async with self._lock:
            events = list(self._events)
        if event_type:
            events = [e for e in events if e["type"] == event_type or e["source_type"] == event_type]
        return events[:limit]


event_bus = EventBus()
