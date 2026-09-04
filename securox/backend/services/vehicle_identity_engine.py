"""
Securox — Vehicle Identity Verification Engine
Unifies:
  • CCTV Frame Sampling & Vehicle Detection (car, truck, bus, motorcycle, auto, ambulance)
  • Sequential Tracking ID Assignment (TRACK-XX) across frames
  • ANPR / License Plate OCR with Indian plate normalization & multi-frame agreement (OCR_UNCERTAIN)
  • FASTag RFID Reader ingestion and registry lookup
  • RFID + OCR Cross-Verification Engine (VERIFIED, MISMATCH, OCR_ONLY, RFID_ONLY, LOW_CONFIDENCE, etc.)
  • Multi-Camera Vehicle Journey Tracking (CAM-101 -> CAM-102 -> CAM-108)
  • Explainable Mismatch Intelligence & Cyber-Risk Escalation to SOC
"""

import asyncio
import json
import logging
import random
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from core.store import store
from services.event_fabric import event_fabric

logger = logging.getLogger("securox.vehicle_identity")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}


def normalize_plate(raw_plate: str) -> str:
    """Standardizes Indian vehicle registration plates (e.g. 'KA-01-AB-1234' -> 'KA01AB1234')."""
    if not raw_plate:
        return ""
    clean = re.sub(r"[^A-Z0-9]", "", raw_plate.upper())
    return clean


def is_valid_plate_syntax(plate: str) -> bool:
    """Validates standard Indian registration syntax: 2 letters (state) + 2 digits + 1-2 letters + 4 digits."""
    norm = normalize_plate(plate)
    if len(norm) < 8 or len(norm) > 10:
        return False
    state = norm[:2]
    if state not in INDIAN_STATE_CODES:
        return False
    # Check digits for district code
    if not norm[2:4].isdigit():
        return False
    # Last 4 should be numbers
    if not norm[-4:].isdigit():
        return False
    return True


class VehicleIdentityEngine:
    """
    Core AI Perception, Multi-Frame Plate Agreement, and RFID Cross-Verification Engine.
    """

    def __init__(self):
        self.inference_fps = 5.0  # Configurable 1-10 FPS
        self._lock = asyncio.Lock()

        # In-memory tracking state: camera_id -> dict of track_id -> vehicle_state
        self._active_tracks: Dict[str, Dict[str, Any]] = {}
        # Multi-frame plate history: track_id -> list of raw OCR readings with confidences
        self._plate_frame_buffer: Dict[str, List[Tuple[str, float]]] = {}
        # Multi-camera journeys: plate -> list of detection events across cameras
        self._journeys: Dict[str, List[Dict[str, Any]]] = {}
        # Mismatch history: plate/tag -> count of observed mismatches across cameras
        self._mismatch_history: Dict[str, Set[str]] = {}  # key -> set of camera_ids where mismatched

    # ── Inference Frame Sampler & Vehicle Detection ───────────────────────────
    async def process_frame(
        self,
        camera_id: str,
        detected_objects: Optional[List[Dict[str, Any]]] = None,
        location: Optional[str] = None
    ) -> List[dict]:
        """
        Samples a video frame and produces persistent VehicleDetection records with TRACK-XX IDs.
        """
        now = _utcnow()
        if not location:
            cam = await store.get_traffic_camera(camera_id)
            location = cam.get("location", "City Traffic Intersection") if cam else "City Traffic Intersection"

        async with self._lock:
            if camera_id not in self._active_tracks:
                self._active_tracks[camera_id] = {}

            room_tracks = self._active_tracks[camera_id]
            detections = []

            # Use provided objects or simulate realistic vehicle detections
            objs = detected_objects or [
                {"vehicle_class": "car", "confidence": 0.94, "plate": "KA01AB1234"},
                {"vehicle_class": "bus", "confidence": 0.96, "plate": "KA01MJ3344"},
                {"vehicle_class": "motorcycle", "confidence": 0.89, "plate": "KA05MK9821"}
            ]

            for idx, obj in enumerate(objs):
                track_id = obj.get("tracking_id") or f"TRACK-{(idx + 1) * 10 + 5}"
                v_class = obj.get("vehicle_class", "car")
                conf = float(obj.get("confidence", 0.92))
                raw_plate = obj.get("plate")
                lane = int(obj.get("lane", idx + 1))
                speed = float(obj.get("speed_estimate", random.randint(35, 65)))

                # Update or initialize tracking state
                if track_id not in room_tracks:
                    room_tracks[track_id] = {
                        "track_id": track_id,
                        "vehicle_class": v_class,
                        "first_seen": now,
                        "last_seen": now,
                        "lane": lane,
                        "speed": speed,
                        "frame_count": 1
                    }
                else:
                    room_tracks[track_id]["last_seen"] = now
                    room_tracks[track_id]["frame_count"] += 1
                    room_tracks[track_id]["speed"] = speed

                det_record = {
                    "detection_id": f"DET-{uuid.uuid4().hex[:8].upper()}",
                    "camera_id": camera_id,
                    "timestamp": now,
                    "vehicle_class": v_class,
                    "confidence": conf,
                    "bounding_box": obj.get("bounding_box", [100, 80 + idx * 40, 240, 160]),
                    "tracking_id": track_id,
                    "location": location,
                    "direction": "NORTH",
                    "speed_estimate": speed,
                    "lane": lane,
                    "metadata": {"raw_plate": raw_plate}
                }

                await store.save_vehicle_detection(det_record)
                detections.append(det_record)

                # Emit VEHICLE_DETECTED
                await event_fabric.emit(
                    action="VEHICLE_DETECTED",
                    domain="TRAFFIC",
                    user="ai_video_pipeline",
                    role="system",
                    resource=f"CAMERA:{camera_id}",
                    result="SUCCESS",
                    risk=0.0,
                    metadata={
                        "detection_id": det_record["detection_id"],
                        "camera_id": camera_id,
                        "tracking_id": track_id,
                        "vehicle_class": v_class,
                        "confidence": conf,
                        "lane": lane,
                        "speed": speed
                    }
                )

                # If license plate detected, process ANPR/OCR pipeline
                if raw_plate:
                    await self.process_anpr_plate(
                        camera_id=camera_id,
                        tracking_id=track_id,
                        raw_plate=raw_plate,
                        initial_confidence=conf
                    )

            return detections

    # ── ANPR / Number Plate OCR Pipeline & Quality Control ────────────────────
    async def process_anpr_plate(
        self,
        camera_id: str,
        tracking_id: str,
        raw_plate: str,
        initial_confidence: float = 0.90
    ) -> dict:
        """
        Runs license plate extraction, Indian plate syntax repair, and multi-frame agreement.
        Flags conflicting or unconfident readings as OCR_UNCERTAIN.
        """
        now = _utcnow()
        norm_plate = normalize_plate(raw_plate)
        valid_syntax = is_valid_plate_syntax(norm_plate)

        # Buffer readings for multi-frame agreement
        if tracking_id not in self._plate_frame_buffer:
            self._plate_frame_buffer[tracking_id] = []
        self._plate_frame_buffer[tracking_id].append((norm_plate, initial_confidence))

        # Evaluate multi-frame agreement across recent frames
        recent_frames = self._plate_frame_buffer[tracking_id][-5:]
        plate_votes = {}
        for p, c in recent_frames:
            plate_votes[p] = plate_votes.get(p, 0) + 1

        most_frequent_plate, vote_count = max(plate_votes.items(), key=lambda item: item[1])
        agreement_ratio = vote_count / len(recent_frames)

        # Boost confidence if sequential frames agree
        if agreement_ratio >= 0.8 and len(recent_frames) >= 2:
            final_conf = min(0.99, initial_confidence + 0.05)
            ocr_status = "RECOGNIZED"
        elif not valid_syntax or initial_confidence < 0.60:
            final_conf = initial_confidence
            ocr_status = "OCR_UNCERTAIN"
        else:
            final_conf = initial_confidence
            ocr_status = "RECOGNIZED"

        # Record journey event
        if most_frequent_plate not in self._journeys:
            self._journeys[most_frequent_plate] = []
        self._journeys[most_frequent_plate].append({
            "camera_id": camera_id,
            "tracking_id": tracking_id,
            "timestamp": now,
            "confidence": final_conf,
            "status": ocr_status
        })

        # Emit events
        await event_fabric.emit(
            action="NUMBER_PLATE_DETECTED",
            domain="TRAFFIC",
            user="anpr_pipeline",
            role="system",
            resource=f"CAMERA:{camera_id}",
            result="SUCCESS",
            risk=0.0,
            metadata={"camera_id": camera_id, "tracking_id": tracking_id, "raw_plate": raw_plate}
        )

        await event_fabric.emit(
            action="NUMBER_PLATE_RECOGNIZED",
            domain="TRAFFIC",
            user="anpr_pipeline",
            role="system",
            resource=f"PLATE:{most_frequent_plate}",
            result="SUCCESS" if ocr_status == "RECOGNIZED" else "UNCERTAIN",
            risk=10.0 if ocr_status == "OCR_UNCERTAIN" else 0.0,
            metadata={
                "camera_id": camera_id,
                "tracking_id": tracking_id,
                "plate": most_frequent_plate,
                "confidence": final_conf,
                "ocr_status": ocr_status,
                "multi_frame_agreement": f"{vote_count}/{len(recent_frames)}"
            }
        )

        return {
            "camera_id": camera_id,
            "tracking_id": tracking_id,
            "plate": most_frequent_plate,
            "confidence": final_conf,
            "status": ocr_status,
            "agreement_ratio": agreement_ratio,
            "timestamp": now
        }

    # ── FASTag RFID Reader Ingestion ──────────────────────────────────────────
    async def process_rfid_read(
        self,
        reader_id: str,
        tag_id: str,
        lane: str = "LANE-01",
        signal_strength: float = -58.0,
        confidence: float = 0.98,
        vehicle_association: Optional[str] = None
    ) -> dict:
        """
        Ingests a radio read from a physical/simulated toll plaza RFID gantry.
        Publishes RFID_TAG_DETECTED and queries FASTag registry.
        """
        now = _utcnow()
        read_record = {
            "read_id": f"READ-{uuid.uuid4().hex[:8].upper()}",
            "reader_id": reader_id,
            "timestamp": now,
            "tag_id": tag_id,
            "lane": lane,
            "signal_strength": signal_strength,
            "vehicle_association": vehicle_association,
            "confidence": confidence,
            "metadata": {"frequency": "865-867 MHz (UHF EPC Gen2)"}
        }
        await store.save_rfid_read(read_record)

        # Lookup in FASTag registry
        fastag = await store.get_fastag(tag_id)

        await event_fabric.emit(
            action="RFID_TAG_DETECTED",
            domain="TRAFFIC",
            user="rfid_gateway",
            role="system",
            resource=f"RFID_READER:{reader_id}",
            result="SUCCESS",
            risk=0.0,
            metadata={
                "read_id": read_record["read_id"],
                "reader_id": reader_id,
                "tag_id": tag_id,
                "lane": lane,
                "confidence": confidence,
                "fastag_found": fastag is not None,
                "registered_vehicle": fastag.get("vehicle_registration") if fastag else None
            }
        )

        return {
            "read": read_record,
            "fastag": fastag
        }

    # ── RFID + OCR Cross-Verification Engine ──────────────────────────────────
    async def cross_verify_vehicle_identity(
        self,
        camera_id: str,
        ocr_plate: Optional[str] = None,
        tag_id: Optional[str] = None,
        ocr_confidence: float = 0.95,
        rfid_confidence: float = 0.98,
        tracking_id: Optional[str] = None,
        lane: str = "LANE-01",
        manual_approved: bool = False,
        operator_reason: Optional[str] = None,
    ) -> dict:
        """
        Cross-correlates RFID FASTag credential with CCTV OCR license plate.
        Supports automatic NO_RFID_DETECTED handling and operator manual approval flow.
        """
        now = _utcnow()
        norm_ocr = normalize_plate(ocr_plate) if ocr_plate else None
        fastag = await store.get_fastag(tag_id) if tag_id else None
        registered_plate = normalize_plate(fastag.get("vehicle_registration")) if fastag else None
        action_taken = "ALLOW_PASSAGE"

        # 1. Evaluate State
        if manual_approved:
            status = "MANUALLY_APPROVED_NO_RFID"
            identity_conf = ocr_confidence
            risk_score = 0.0
            explanation = f"Manual clearance approved by operator for vehicle [{norm_ocr}]. Reason: {operator_reason or 'Visual plate verification; no physical RFID scanner detected.'}"
            action_taken = "BARRIER_OPENED_OPERATOR_APPROVAL"

        elif operator_reason == "OPERATOR_REJECTED":
            status = "REJECTED_NO_RFID"
            identity_conf = ocr_confidence
            risk_score = 75.0
            explanation = f"Manual clearance REJECTED by operator for vehicle [{norm_ocr}]. Barrier kept locked."
            action_taken = "BARRIER_LOCKED_FLAGGED_FOR_INSPECTION"

        elif (not tag_id or tag_id == "NO_TAG" or tag_id == "NO_TAG_MANUAL_PASS") and norm_ocr:
            status = "NO_RFID_DETECTED"
            identity_conf = ocr_confidence
            risk_score = 25.0
            explanation = f"Vehicle plate [{norm_ocr}] detected via optical ANPR, but NO RFID scanner or FASTag signal detected at gantry. Manual operator authorization required."
            action_taken = "PROMPT_OPERATOR_MANUAL_APPROVAL"

        elif not norm_ocr and tag_id:
            status = "RFID_ONLY"
            identity_conf = rfid_confidence
            risk_score = 20.0
            explanation = "FASTag RFID read recorded at gantry; license plate obscured from CCTV view."
            action_taken = "FLAG_FOR_SECONDARY_INSPECTION"

        elif tag_id and not fastag:
            status = "UNKNOWN_TAG"
            identity_conf = 0.30
            risk_score = 65.0
            explanation = f"FASTag tag_id [{tag_id}] is unregistered or counterfeit in National NETC Registry."
            action_taken = "BARRIER_LOCK_SUSPECT_TAG"

        elif ocr_confidence < 0.60 or rfid_confidence < 0.60:
            status = "LOW_CONFIDENCE"
            identity_conf = (ocr_confidence + rfid_confidence) / 2.0
            risk_score = 25.0
            explanation = f"Sensor uncertainty: OCR confidence ({ocr_confidence*100:.0f}%) or RFID ({rfid_confidence*100:.0f}%) below trust threshold."
            action_taken = "RETRY_SENSOR_CAPTURE"

        elif norm_ocr and not is_valid_plate_syntax(norm_ocr):
            status = "UNKNOWN_PLATE"
            identity_conf = 0.40
            risk_score = 30.0
            explanation = f"OCR extracted plate [{norm_ocr}] does not conform to standardized registration grammar."
            action_taken = "FLAG_OCR_UNCERTAIN"

        elif registered_plate and norm_ocr:
            if registered_plate == norm_ocr:
                status = "VERIFIED"
                identity_conf = round(rfid_confidence * 0.5 + ocr_confidence * 0.5, 3)
                risk_score = 0.0
                explanation = f"Identity Confirmed: RFID credential ({tag_id}) matches CCTV visual plate ({norm_ocr})."
                action_taken = "BARRIER_OPENED_AUTOMATIC"
            else:
                status = "MISMATCH"
                identity_conf = round(abs(rfid_confidence - ocr_confidence), 3)

                key = f"{tag_id}:{norm_ocr}"
                if key not in self._mismatch_history:
                    self._mismatch_history[key] = set()
                self._mismatch_history[key].add(camera_id)

                distinct_cameras_count = len(self._mismatch_history[key])

                if ocr_confidence >= 0.90 and rfid_confidence >= 0.90 and distinct_cameras_count >= 2:
                    risk_score = min(98.0, 70.0 + distinct_cameras_count * 10.0)
                    explanation = (
                        f"CRITICAL IDENTITY MISMATCH: RFID tag registered to [{registered_plate}] but CCTV OCR confirmed [{norm_ocr}] "
                        f"(OCR Conf: {ocr_confidence*100:.0f}%, RFID Conf: {rfid_confidence*100:.0f}%). "
                        f"Repeated across {distinct_cameras_count} cameras: {list(self._mismatch_history[key])}."
                    )
                    action_taken = "ESCALATE_TO_SOC_BARRIER_LOCK"
                elif ocr_confidence < 0.80:
                    risk_score = 35.0
                    explanation = f"Potential OCR visual disparity: RFID ({registered_plate}) vs OCR ({norm_ocr}). Confidence {ocr_confidence*100:.0f}% suggests dirty plate or poor lighting."
                    action_taken = "FLAG_FOR_OPERATOR_REVIEW"
                else:
                    risk_score = 65.0
                    explanation = f"Single-camera identity mismatch: RFID ({registered_plate}) vs OCR ({norm_ocr}). Monitoring subsequent cameras."
                    action_taken = "FLAG_FOR_OPERATOR_REVIEW"
        else:
            status = "LOW_CONFIDENCE"
            identity_conf = 0.50
            risk_score = 20.0
            explanation = "Insufficient sensor telemetry to verify identity."
            action_taken = "FLAG_FOR_OPERATOR_REVIEW"

        # Track journey cameras
        cameras_seen = list(self._mismatch_history.get(f"{tag_id}:{norm_ocr}", [camera_id]))
        repeated_count = len(cameras_seen) if status == "MISMATCH" else 0
        v_id = f"VVERIF-{uuid.uuid4().hex[:8].upper()}"

        # Save verification record
        verif_data = {
            "verification_id": v_id,
            "id": v_id,
            "rfid_read_id": None,
            "detection_id": None,
            "camera_id": camera_id,
            "tag_id": tag_id,
            "rfid_tag_id": tag_id or "NO_TAG_DETECTED",
            "registered_plate": registered_plate,
            "rfid_registered_plate": registered_plate or "NO_TAG_REGISTERED",
            "ocr_plate": norm_ocr,
            "rfid_confidence": rfid_confidence,
            "ocr_confidence": ocr_confidence,
            "identity_confidence": identity_conf,
            "status": status,
            "verification_status": status,
            "risk_score": risk_score,
            "action_taken": action_taken,
            "escalation_status": "ESCALATED_TO_SOC" if (repeated_count >= 2 and status == "MISMATCH") else "NONE",
            "repeated_mismatch_count": repeated_count,
            "cameras_seen": cameras_seen,
            "timestamp": now,
            "details": {
                "explanation": explanation,
                "lane": lane,
                "tracking_id": tracking_id,
                "fastag_status": fastag.get("status") if fastag else "NOT_FOUND"
            }
        }
        await store.save_vehicle_verification(verif_data)

        # Publish Canonical Events
        if status == "VERIFIED":
            await event_fabric.emit(
                action="VEHICLE_IDENTITY_VERIFIED",
                domain="TRAFFIC",
                user="vehicle_identity_engine",
                role="system",
                resource=f"VEHICLE:{norm_ocr}",
                result="SUCCESS",
                risk=0.0,
                metadata={
                    "verification_id": verif_data["verification_id"],
                    "tag_id": tag_id,
                    "plate": norm_ocr,
                    "confidence": identity_conf,
                    "camera_id": camera_id
                }
            )
        elif status == "MISMATCH":
            await event_fabric.emit(
                action="VEHICLE_IDENTITY_MISMATCH",
                domain="TRAFFIC",
                user="vehicle_identity_engine",
                role="system",
                resource=f"VEHICLE:{norm_ocr or tag_id}",
                result="WARNING",
                risk=risk_score,
                metadata={
                    "verification_id": verif_data["verification_id"],
                    "tag_id": tag_id,
                    "registered_plate": registered_plate,
                    "ocr_plate": norm_ocr,
                    "risk_score": risk_score,
                    "repeated_cameras": repeated_count,
                    "explanation": explanation
                }
            )

            # High-Risk Escalation to SOC
            if risk_score >= 80.0:
                await event_fabric.emit(
                    action="TRAFFIC_SECURITY_ALERT",
                    domain="TRAFFIC",
                    user="vehicle_identity_engine",
                    role="system",
                    resource=f"CLONED_TAG:{tag_id}",
                    result="CRITICAL_ALERT",
                    risk=risk_score,
                    metadata={
                        "threat": "FASTAG_CLONING_OR_STOLEN_PLATE",
                        "registered_plate": registered_plate,
                        "observed_plate": norm_ocr,
                        "cameras_observed": cameras_seen,
                        "recommendation": "Dispatch traffic police interceptor; lock toll plaza boom barriers."
                    }
                )

        return verif_data

    # ── Multi-Camera Journey Correlation ──────────────────────────────────────
    async def get_vehicle_journey(self, plate: str) -> dict:
        """Retrieves correlated multi-camera progression (e.g. CAM-101 -> CAM-102 -> CAM-108)."""
        norm = normalize_plate(plate)
        journey = self._journeys.get(norm, [])
        return {
            "plate": norm,
            "observations_count": len(journey),
            "camera_sequence": [j["camera_id"] for j in journey],
            "timeline": journey
        }


# Singleton Instance
vehicle_identity_engine = VehicleIdentityEngine()
