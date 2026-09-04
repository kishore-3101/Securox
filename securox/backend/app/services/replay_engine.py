"""
Threat replay and timeline reconstruction.
"""


class ReplayEngine:
    def build_timeline(self, events: list[dict]) -> dict:
        ordered = sorted(events, key=lambda e: e.get("timestamp", ""))
        frames = [
            {
                "frame": index,
                "timestamp": event.get("timestamp"),
                "type": event.get("type", event.get("source_type", "event")),
                "data": event.get("data", event),
            }
            for index, event in enumerate(ordered)
        ]
        return {"frames": frames, "frame_count": len(frames)}


replay_engine = ReplayEngine()
