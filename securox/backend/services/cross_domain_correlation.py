"""
Securox — Cross-Domain Threat Correlation Engine
Correlates security telemetry across:
  - user (identity)
  - device (fingerprint / hardware ID)
  - IP (network coordinates)
  - location (facilities, GeoIP)
  - time (temporal clustering & sliding windows)
  - behavior (action patterns, privilege boundaries, velocity)
  - events (Healthcare, Traffic, Finance, Infrastructure)

Identifies:
  1. RELATED SECURITY EVENTS
  2. COORDINATED ATTACK INDICATOR

Invariants:
  - Do NOT automatically claim attribution (explicit probabilistic telemetry linkage with disclaimer).
  - Generates graph visualization (nodes & edges) for SOC investigation.
  - Automatically spawns a unified SOC incident when correlation thresholds are satisfied.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from core.store import store
from services.event_fabric import event_fabric

logger = logging.getLogger("securox.cross_domain_correlation")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class CorrelatedEvent(BaseModel):
    event_id: str
    domain: str
    action: str
    resource: str
    user: str
    device: str
    ip: Optional[str] = None
    location: Optional[str] = None
    risk_score: float = 0.0
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "entity", "domain", "event", "threat_indicator"
    domain: Optional[str] = None
    risk_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # "CROSS_DOMAIN_CORRELATION", "GENERATED_EVENT", "TARGETS_DOMAIN", "SHARED_DEVICE", "SHARED_USER"
    weight: float = 1.0
    label: Optional[str] = None


class GraphVisualization(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class CrossDomainCorrelationCluster(BaseModel):
    cluster_id: str
    shared_pivot_type: str  # "device", "user", "ip", "location"
    shared_pivot_value: str
    affected_domains: List[str]
    correlation_confidence: float  # 0.0 - 1.0
    coordinated_attack_indicator: bool
    attribution_disclaimer: str = (
        "Probabilistic cross-domain telemetry correlation. Does not constitute definitive "
        "adversary attribution without independent forensic and behavioral verification."
    )
    related_security_events: List[CorrelatedEvent]
    evidence: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    shared_entities: Dict[str, Any]
    graph_visualization: GraphVisualization
    created_incident_id: Optional[str] = None
    timestamp: str = Field(default_factory=_utcnow)


class CrossDomainCorrelationEngine:
    """
    Central Cross-Domain Threat Correlation Engine.
    Discovers multi-stage, cross-sector cyber-physical campaigns.
    """

    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold

    def calculate_confidence(
        self,
        domain_count: int,
        event_count: int,
        avg_risk: float,
        has_shared_device: bool,
        has_shared_ip: bool,
        hours_spread: float
    ) -> float:
        """
        Calculates mathematical correlation confidence without random numbers:
          - Base: 0.50 for 2 domains, +0.20 for 3+ domains
          - Shared physical device: +0.15
          - Shared IP: +0.10
          - High-risk severity: +0.10 (if avg_risk >= 60)
          - Temporal proximity penalty: decays if spread > 12h
        """
        conf = 0.50
        if domain_count >= 3:
            conf += 0.20
        elif domain_count == 2:
            conf += 0.10

        if has_shared_device:
            conf += 0.15
        if has_shared_ip:
            conf += 0.08
        if avg_risk >= 60.0:
            conf += 0.10

        # Temporal proximity decay
        if hours_spread > 12.0:
            penalty = min(0.15, (hours_spread - 12.0) * 0.01)
            conf -= penalty

        return round(min(0.99, max(0.20, conf)), 2)

    def build_graph_visualization(
        self,
        pivot_type: str,
        pivot_val: str,
        events: List[CorrelatedEvent],
        domains: List[str],
        confidence: float
    ) -> GraphVisualization:
        """Generates topological nodes and edges for SOC visualization."""
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # 1. Central Pivot Entity Node
        entity_node_id = f"entity_{pivot_val.replace(' ', '_')}"
        nodes.append(GraphNode(
            id=entity_node_id,
            label=f"{pivot_type.upper()}: {pivot_val}",
            type="entity",
            domain="CROSS_DOMAIN",
            metadata={"pivot_type": pivot_type, "value": pivot_val}
        ))

        # 2. Domain Nodes
        for d in domains:
            d_node_id = f"domain_{d}"
            nodes.append(GraphNode(
                id=d_node_id,
                label=f"Domain: {d}",
                type="domain",
                domain=d
            ))
            edges.append(GraphEdge(
                source=entity_node_id,
                target=d_node_id,
                type="OPERATES_IN_DOMAIN",
                weight=confidence,
                label=f"Cross-Domain Link ({int(confidence*100)}%)"
            ))

        # 3. Event Nodes & Edges
        for ev in events:
            ev_node_id = f"ev_{ev.event_id}"
            nodes.append(GraphNode(
                id=ev_node_id,
                label=f"{ev.domain}: {ev.action} on {ev.resource}",
                type="event",
                domain=ev.domain,
                risk_score=ev.risk_score,
                metadata={
                    "timestamp": ev.timestamp,
                    "action": ev.action,
                    "resource": ev.resource,
                    "risk": ev.risk_score
                }
            ))
            # Edge from Entity to Event
            edges.append(GraphEdge(
                source=entity_node_id,
                target=ev_node_id,
                type="GENERATED_EVENT",
                weight=1.0,
                label="Initiated"
            ))
            # Edge from Event to Domain
            edges.append(GraphEdge(
                source=ev_node_id,
                target=f"domain_{ev.domain}",
                type="TARGETS_DOMAIN",
                weight=1.0,
                label="Impacts"
            ))

        # 4. Cross-Domain Correlation Edges between events across domains
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                if events[i].domain != events[j].domain:
                    edges.append(GraphEdge(
                        source=f"ev_{events[i].event_id}",
                        target=f"ev_{events[j].event_id}",
                        type="CROSS_DOMAIN_CORRELATION",
                        weight=confidence,
                        label=f"Coordinated ({int(confidence*100)}%)"
                    ))

        return GraphVisualization(nodes=nodes, edges=edges)

    async def correlate_events(
        self,
        raw_events: List[Dict[str, Any]],
        window_hours: float = 24.0,
        create_incident: bool = True
    ) -> List[CrossDomainCorrelationCluster]:
        """
        Core correlation logic.
        Clusters events by shared pivots (device, user, IP) across multiple domains.
        """
        if not raw_events:
            return []

        # Convert to standardized CorrelatedEvent objects
        parsed_events: List[CorrelatedEvent] = []
        for e in raw_events:
            eid = str(e.get("event_id") or e.get("id") or f"EV-{uuid.uuid4().hex[:6].upper()}")
            dom = str(e.get("domain", "GLOBAL")).upper()
            act = str(e.get("action", "ACCESS")).upper()
            res = str(e.get("resource") or e.get("target_asset") or e.get("asset") or "CORE_RESOURCE")
            usr = str(e.get("user") or e.get("identity") or "unknown_actor")
            dev = str(e.get("device") or e.get("device_id") or "DEV-UNKNOWN")
            ip = e.get("ip") or e.get("client_ip")
            loc = e.get("location") or e.get("geo_location")
            r_score = float(e.get("risk") or e.get("risk_score") or 0.0)
            ts = str(e.get("timestamp") or _utcnow())

            parsed_events.append(CorrelatedEvent(
                event_id=eid,
                domain=dom,
                action=act,
                resource=res,
                user=usr,
                device=dev,
                ip=ip,
                location=loc,
                risk_score=r_score,
                timestamp=ts,
                details=e
            ))

        clusters: List[CrossDomainCorrelationCluster] = []

        # Pivot index maps
        device_map: Dict[str, List[CorrelatedEvent]] = {}
        user_map: Dict[str, List[CorrelatedEvent]] = {}
        ip_map: Dict[str, List[CorrelatedEvent]] = {}

        for pe in parsed_events:
            if pe.device and pe.device != "DEV-UNKNOWN":
                device_map.setdefault(pe.device, []).append(pe)
            if pe.user and pe.user != "unknown_actor":
                user_map.setdefault(pe.user, []).append(pe)
            if pe.ip and pe.ip != "127.0.0.1":
                ip_map.setdefault(pe.ip, []).append(pe)

        # Process each pivot type
        processed_clusters: Set[str] = set()

        for pivot_type, mapping in [("device", device_map), ("user", user_map), ("ip", ip_map)]:
            for pivot_val, ev_list in mapping.items():
                domains = sorted(list(set(e.domain for e in ev_list)))
                # Cross-domain invariant: MUST touch >= 2 distinct sectors
                if len(domains) < 2:
                    continue

                cluster_key = f"{pivot_type}:{pivot_val}:{'-'.join(domains)}"
                if cluster_key in processed_clusters:
                    continue
                processed_clusters.add(cluster_key)

                # Calculate temporal spread
                timestamps = []
                for e in ev_list:
                    try:
                        clean_ts = e.timestamp.replace("Z", "+00:00")
                        timestamps.append(datetime.fromisoformat(clean_ts))
                    except Exception:
                        pass

                spread_hours = 1.0
                if timestamps:
                    min_t = min(timestamps)
                    max_t = max(timestamps)
                    spread_hours = max(0.1, (max_t - min_t).total_seconds() / 3600.0)

                # Skip if events exceed correlation window
                if spread_hours > window_hours:
                    continue

                avg_risk = sum(e.risk_score for e in ev_list) / max(1, len(ev_list))
                has_shared_dev = pivot_type == "device" or len(set(e.device for e in ev_list if e.device != "DEV-UNKNOWN")) == 1
                has_shared_ip = pivot_type == "ip" or len(set(e.ip for e in ev_list if e.ip)) == 1

                confidence = self.calculate_confidence(
                    domain_count=len(domains),
                    event_count=len(ev_list),
                    avg_risk=avg_risk,
                    has_shared_device=has_shared_dev,
                    has_shared_ip=has_shared_ip,
                    hours_spread=spread_hours
                )

                # Coordinated attack indicator condition
                is_coordinated = (
                    len(domains) >= 2 and
                    (any(e.risk_score >= 60.0 for e in ev_list) or confidence >= self.confidence_threshold or len(ev_list) >= 3)
                )

                # Build Evidence List
                evidence = [
                    {
                        "type": f"SHARED_{pivot_type.upper()}",
                        "description": f"Common pivot '{pivot_val}' active across {len(domains)} domains ({', '.join(domains)})",
                        "value": pivot_val,
                        "domain_count": len(domains)
                    },
                    {
                        "type": "TEMPORAL_COINCIDENCE",
                        "description": f"All {len(ev_list)} cross-sector events occurred within {spread_hours:.1f} hours",
                        "hours_spread": round(spread_hours, 1)
                    }
                ]
                if avg_risk >= 50.0:
                    evidence.append({
                        "type": "ELEVATED_AGGREGATE_RISK",
                        "description": f"Average risk score across linked events is {avg_risk:.1f}/100",
                        "average_risk": round(avg_risk, 1)
                    })

                # Build Chronological Timeline
                sorted_events = sorted(ev_list, key=lambda x: x.timestamp)
                timeline = [
                    {
                        "timestamp": e.timestamp,
                        "domain": e.domain,
                        "action": e.action,
                        "resource": e.resource,
                        "user": e.user,
                        "device": e.device,
                        "risk_score": e.risk_score,
                        "summary": f"[{e.domain}] {e.action} requested on {e.resource} (Risk: {int(e.risk_score)})"
                    }
                    for e in sorted_events
                ]

                # Shared Entities Dict
                shared_entities = {
                    "pivot_type": pivot_type,
                    "pivot_value": pivot_val,
                    "users": list(set(e.user for e in ev_list if e.user)),
                    "devices": list(set(e.device for e in ev_list if e.device)),
                    "ips": list(set(e.ip for e in ev_list if e.ip)),
                    "locations": list(set(e.location for e in ev_list if e.location))
                }

                # Graph Visualization
                graph_viz = self.build_graph_visualization(
                    pivot_type=pivot_type,
                    pivot_val=pivot_val,
                    events=sorted_events,
                    domains=domains,
                    confidence=confidence
                )

                cluster_id = f"CORR-{pivot_val.replace(' ', '_').replace('-', '_')}-{uuid.uuid4().hex[:4].upper()}"

                # Auto-create Unified Incident in SOC if threshold satisfied
                created_inc_id = None
                if create_incident and confidence >= self.confidence_threshold and is_coordinated:
                    from services.soc_engine import soc_engine
                    try:
                        inc_payload = {
                            "title": f"Coordinated Multi-Domain Threat: {pivot_type.upper()} '{pivot_val}' across {', '.join(domains)}",
                            "description": (
                                f"Correlated {len(ev_list)} suspicious security events across {len(domains)} distinct domains "
                                f"({', '.join(domains)}) sharing {pivot_type} '{pivot_val}'. "
                                f"Correlation confidence: {int(confidence * 100)}%."
                            ),
                            "status": "DETECTED",
                            "severity": "CRITICAL" if len(domains) >= 3 or avg_risk >= 70 else "HIGH",
                            "domain": "CROSS_DOMAIN",
                            "asset": f"MULTI_ASSET_{pivot_val}",
                            "identity": shared_entities["users"][0] if shared_entities["users"] else "unknown_actor",
                            "device": shared_entities["devices"][0] if shared_entities["devices"] else "DEV-UNKNOWN",
                            "attack_type": "Coordinated Cross-Domain Attack",
                            "risk_score": round(avg_risk, 1),
                            "mitre_tactics": ["Initial Access", "Lateral Movement", "Cross-Domain Impact"],
                            "evidence": evidence,
                            "related_event_ids": [e.event_id for e in ev_list]
                        }
                        created_inc = await soc_engine.create_incident(inc_payload)
                        created_inc_id = created_inc.get("id")
                    except Exception as ex:
                        logger.warning(f"Failed to auto-spawn unified incident for cluster {cluster_id}: {ex}")

                cluster = CrossDomainCorrelationCluster(
                    cluster_id=cluster_id,
                    shared_pivot_type=pivot_type,
                    shared_pivot_value=pivot_val,
                    affected_domains=domains,
                    correlation_confidence=confidence,
                    coordinated_attack_indicator=is_coordinated,
                    related_security_events=sorted_events,
                    evidence=evidence,
                    timeline=timeline,
                    shared_entities=shared_entities,
                    graph_visualization=graph_viz,
                    created_incident_id=created_inc_id
                )
                clusters.append(cluster)

        return clusters

    async def analyze_cross_domain_telemetry(self, window_hours: float = 24.0) -> List[CrossDomainCorrelationCluster]:
        """Queries actual events from SQLite WAL and executes correlation."""
        # Ingest events from security_events table and auth_decisions
        events = await store.get_security_events(limit=200)
        auth_decisions = await store.get_auth_decisions(limit=100)

        all_events = list(events)
        for ad in auth_decisions:
            all_events.append({
                "event_id": ad.get("id") or ad.get("event_id"),
                "domain": ad.get("domain"),
                "action": ad.get("action"),
                "resource": ad.get("resource"),
                "user": ad.get("identity"),
                "device": ad.get("context_payload", {}).get("device_id") or "DEV-UNKNOWN",
                "risk": ad.get("risk_score"),
                "timestamp": ad.get("timestamp")
            })

        return await self.correlate_events(all_events, window_hours=window_hours, create_incident=True)


cross_domain_correlator = CrossDomainCorrelationEngine()
