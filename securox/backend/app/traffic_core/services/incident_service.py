import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from traffic_core import traffic_models as models
from traffic_core.services.event_bus import NormalizedEvent

VALID_STATUSES = [
    "DETECTED", "TRIAGED", "ACKNOWLEDGED", "INVESTIGATING", "CONTAINED", "RESOLVED", "CLOSED"
]

class IncidentService:
    def create_incident_from_correlation(
        self, 
        db: Session, 
        title: str, 
        incident_type: str, 
        severity: str, 
        asset_id: str, 
        location: str, 
        risk_score: float,
        evidence: Dict[str, Any],
        root_cause: str
    ) -> models.Incident:
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        incident = models.Incident(
            incident_id=incident_id,
            title=title,
            severity=severity,
            type=incident_type,
            status="DETECTED",
            asset_id=asset_id,
            location=location,
            risk_score=risk_score,
            detected_at=datetime.utcnow(),
            evidence_json=json.dumps(evidence),
            action_log_json=json.dumps([{
                "action": "DETECTED",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "CORRELATION_ENGINE",
                "note": "Incident automatically created and triaged by multi-source correlation engine."
            }]),
            root_cause=root_cause
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Add initial timeline event
        self.add_timeline_entry(
            db=db,
            incident_id=incident_id,
            title="Incident Triggered and Logged",
            description=root_cause,
            event_type="INCIDENT_DETECTION",
            severity=severity,
            source="CORRELATION_ENGINE"
        )
        return incident

    def add_timeline_entry(
        self,
        db: Session,
        incident_id: str,
        title: str,
        description: str,
        event_type: str = "STATUS_CHANGE",
        severity: str = "INFO",
        source: str = "SOC_OPERATOR"
    ) -> models.IncidentTimeline:
        timeline = models.IncidentTimeline(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            title=title,
            description=description,
            event_type=event_type,
            severity=severity,
            source=source
        )
        db.add(timeline)
        db.commit()
        db.refresh(timeline)
        return timeline

    def update_incident_status(
        self,
        db: Session,
        incident_id: str,
        new_status: str,
        operator_name: str = "Operator",
        note: str = ""
    ) -> models.Incident:
        incident = db.query(models.Incident).filter(models.Incident.incident_id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")

        prev_status = incident.status
        incident.status = new_status

        if new_status == "ACKNOWLEDGED" and not incident.acknowledged_at:
            incident.acknowledged_at = datetime.utcnow()
            incident.assigned_to = operator_name

        if new_status in ["RESOLVED", "CLOSED"] and not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()
            incident.resolution_notes = note or "Incident mitigated and verified normal operations restored."

        # Append action log
        try:
            action_log = json.loads(incident.action_log_json or "[]")
        except:
            action_log = []
            
        action_log.append({
            "action": f"STATUS_CHANGE_{new_status}",
            "from_status": prev_status,
            "to_status": new_status,
            "timestamp": datetime.utcnow().isoformat(),
            "actor": operator_name,
            "note": note
        })
        incident.action_log_json = json.dumps(action_log)

        db.commit()
        db.refresh(incident)

        self.add_timeline_entry(
            db=db,
            incident_id=incident_id,
            title=f"Incident Status Changed: {prev_status} -> {new_status}",
            description=f"Action taken by {operator_name}. {note}".strip(),
            event_type="STATUS_UPDATE",
            severity="INFO",
            source=operator_name
        )

        return incident

    def get_forensic_dossier(self, db: Session, incident_id: str) -> Dict[str, Any]:
        """
        Builds a comprehensive forensic reconstruction (What, When, Where, How, Impact, Timeline, Evidence).
        """
        incident = db.query(models.Incident).filter(models.Incident.incident_id == incident_id).first()
        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        timelines = db.query(models.IncidentTimeline).filter(
            models.IncidentTimeline.incident_id == incident_id
        ).order_by(models.IncidentTimeline.timestamp.asc()).all()

        try:
            evidence = json.loads(incident.evidence_json or "{}")
        except:
            evidence = {}

        try:
            actions = json.loads(incident.action_log_json or "[]")
        except:
            actions = []

        # Find affected asset details
        asset = db.query(models.Asset).filter(models.Asset.id == incident.asset_id).first()

        return {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "verdict": "CONFIRMED" if incident.severity == "CRITICAL" else "SUSPECTED",
            "severity": incident.severity,
            "type": incident.type,
            "status": incident.status,
            "location": incident.location,
            "risk_score": incident.risk_score,
            "timestamps": {
                "detected": incident.detected_at.isoformat() if incident.detected_at else None,
                "acknowledged": incident.acknowledged_at.isoformat() if incident.acknowledged_at else None,
                "resolved": incident.resolved_at.isoformat() if incident.resolved_at else None
            },
            "what": incident.title,
            "when": incident.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC") if incident.detected_at else "Unknown",
            "where": incident.location,
            "how": incident.root_cause or "Correlated multi-domain telemetry violation",
            "impact": (
                f"Severe degradation to traffic velocity and safety controls. Affected asset: {incident.asset_id}."
            ),
            "assigned_to": incident.assigned_to or "Unassigned",
            "resolution_notes": incident.resolution_notes or "Pending final forensic signoff",
            "asset_details": {
                "id": asset.id if asset else incident.asset_id,
                "name": asset.name if asset else "Traffic Infrastructure Node",
                "ip": asset.ip_address if asset else "Unknown",
                "type": asset.asset_type if asset else "CONTROLLER",
                "criticality": asset.criticality if asset else "HIGH"
            } if asset else None,
            "timeline": [
                {
                    "timestamp": t.timestamp.strftime("%H:%M:%S UTC"),
                    "title": t.title,
                    "description": t.description,
                    "severity": t.severity,
                    "source": t.source
                }
                for t in timelines
            ],
            "evidence": evidence,
            "action_log": actions
        }

incident_service = IncidentService()
