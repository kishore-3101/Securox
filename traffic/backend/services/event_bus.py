import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Callable
from pydantic import BaseModel, Field

from database import SessionLocal
import models

class NormalizedEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str
    severity: str = "INFO"  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    asset_id: str
    location: str
    source: str
    confidence: float = 0.95
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True

class EventBus:
    def __init__(self, max_history: int = 500):
        self.subscribers: List[Callable[[NormalizedEvent], Any]] = []
        self.history: List[NormalizedEvent] = []
        self.max_history = max_history
        self._lock = asyncio.Lock()

    def subscribe(self, callback: Callable[[NormalizedEvent], Any]):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[NormalizedEvent], Any]):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def publish(self, event: NormalizedEvent) -> NormalizedEvent:
        # 1. Update in-memory ring buffer
        async with self._lock:
            self.history.insert(0, event)
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]

        # 2. Persist asynchronously to DB
        try:
            db = SessionLocal()
            db_event = models.EventLog(
                event_id=event.event_id,
                timestamp=datetime.fromisoformat(event.timestamp.replace("Z", "+00:00")).replace(tzinfo=None),
                event_type=event.event_type,
                severity=event.severity,
                asset_id=event.asset_id,
                location=event.location,
                source=event.source,
                confidence=event.confidence,
                title=event.title,
                description=event.description,
                metadata_json=json.dumps(event.metadata),
                is_simulated=event.is_simulated
            )
            db.add(db_event)
            db.commit()
            db.close()
        except Exception as e:
            print(f"[EventBus] Error persisting event: {e}")

        # 3. Notify all subscribers (WebSockets, correlation listeners, etc.)
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    asyncio.create_task(subscriber(event))
                else:
                    subscriber(event)
            except Exception as e:
                print(f"[EventBus] Subscriber dispatch error: {e}")

        return event

    def get_recent(self, limit: int = 50, severity: str = None, event_type: str = None) -> List[NormalizedEvent]:
        events = self.history
        if severity:
            events = [e for e in events if e.severity.upper() == severity.upper()]
        if event_type:
            events = [e for e in events if e.event_type.upper() == event_type.upper()]
        return events[:limit]

# Global singleton
event_bus = EventBus()
