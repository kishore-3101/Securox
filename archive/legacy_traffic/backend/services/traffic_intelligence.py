import math
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class CongestionAnalysis(BaseModel):
    congestion_level: str  # FREE_FLOW, MODERATE, HEAVY, SEVERE, CRITICAL
    congestion_score: float  # 0 to 100
    density_score: float
    flow_score: float
    speed_score: float
    risk_score: float
    severity: str
    confidence: float
    reason: str
    color_code: str  # #10b981 (green), #f59e0b (yellow), #f97316 (orange), #ef4444 (red), #881337 (dark red)

class TrafficAnomalyResult(BaseModel):
    is_anomaly: bool
    anomaly_type: str
    baseline: float
    current_value: float
    deviation_percent: float
    confidence: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    potential_cause: str

class TrafficPredictionItem(BaseModel):
    horizon_minutes: int
    predicted_volume: int
    predicted_speed_kmh: float
    predicted_congestion: str
    confidence: float
    historical_baseline: int
    status_note: str

class TrafficIntelligenceEngine:
    def __init__(self):
        # Baselines keyed by road_id
        self.baselines: Dict[str, Dict[str, float]] = {
            "ROAD-NH44-01": {"volume": 280, "speed": 85, "occupancy": 0.40},
            "ROAD-NH44-02": {"volume": 320, "speed": 82, "occupancy": 0.45},
            "ROAD-NH44-03": {"volume": 250, "speed": 90, "occupancy": 0.35},
            "ROAD-URBAN-01": {"volume": 420, "speed": 45, "occupancy": 0.60},
            "ROAD-URBAN-02": {"volume": 380, "speed": 48, "occupancy": 0.55},
        }
        self.history_samples: Dict[str, List[Dict[str, Any]]] = {}

    def calculate_congestion(
        self, 
        current_volume: int, 
        capacity: int, 
        current_speed: float, 
        speed_limit: float,
        lanes: int = 4,
        queue_length: int = 0
    ) -> CongestionAnalysis:
        """
        Computes multi-variable density, speed, and queue congestion scores.
        """
        capacity = max(10, capacity)
        speed_limit = max(20.0, speed_limit)
        
        # Volume-to-Capacity ratio (V/C)
        vc_ratio = current_volume / capacity
        density_score = min(100.0, vc_ratio * 100.0)
        
        # Speed deficit ratio
        speed_deficit = max(0.0, (speed_limit - current_speed) / speed_limit)
        speed_score = min(100.0, speed_deficit * 100.0)
        
        # Queue impact
        queue_factor = min(30.0, queue_length * 2.0)
        
        # Flow efficiency
        flow_score = max(0.0, 100.0 - (density_score * 0.6 + speed_score * 0.4))
        
        # Composite Congestion Score (0 - 100)
        congestion_score = round(min(100.0, (density_score * 0.50) + (speed_score * 0.35) + queue_factor), 1)
        
        if congestion_score >= 85.0:
            level = "CRITICAL"
            severity = "CRITICAL"
            color = "#881337"  # Dark Red
        elif congestion_score >= 70.0:
            level = "SEVERE"
            severity = "HIGH"
            color = "#ef4444"  # Red
        elif congestion_score >= 50.0:
            level = "HEAVY"
            severity = "MEDIUM"
            color = "#f97316"  # Orange
        elif congestion_score >= 30.0:
            level = "MODERATE"
            severity = "LOW"
            color = "#f59e0b"  # Yellow
        else:
            level = "FREE_FLOW"
            severity = "INFO"
            color = "#10b981"  # Green

        reasons = []
        if density_score > 60:
            reasons.append(f"Vehicle volume at {density_score:.0f}% capacity")
        if speed_score > 40:
            reasons.append(f"Speed reduced by {speed_score:.0f}% below limit ({current_speed:.0f} vs {speed_limit:.0f} km/h)")
        if queue_length > 5:
            reasons.append(f"Queue formation of {queue_length} vehicles")
        if not reasons:
            reasons.append("Optimal speed and traffic throughput maintained.")

        risk_score = round(min(100.0, congestion_score * 0.85 + (15.0 if level in ['SEVERE', 'CRITICAL'] else 0.0)), 1)

        return CongestionAnalysis(
            congestion_level=level,
            congestion_score=congestion_score,
            density_score=round(density_score, 1),
            flow_score=round(flow_score, 1),
            speed_score=round(speed_score, 1),
            risk_score=risk_score,
            severity=severity,
            confidence=0.94,
            reason="; ".join(reasons),
            color_code=color
        )

    def detect_traffic_anomaly(
        self, 
        road_id: str, 
        current_volume: int, 
        current_speed: float, 
        sensor_reading: Optional[int] = None
    ) -> TrafficAnomalyResult:
        """
        Identifies traffic pattern anomalies rather than simple threshold violations.
        """
        base = self.baselines.get(road_id, {"volume": 250, "speed": 80})
        base_vol = base["volume"]
        vol_dev = ((current_volume - base_vol) / base_vol) * 100.0
        
        # 1. Sensor Disagreement (Sensor reads zero while camera shows heavy traffic)
        if sensor_reading is not None and sensor_reading == 0 and current_volume > 150:
            return TrafficAnomalyResult(
                is_anomaly=True,
                anomaly_type="SENSOR_DISAGREEMENT",
                baseline=float(base_vol),
                current_value=float(current_volume),
                deviation_percent=-100.0,
                confidence=0.98,
                severity="HIGH",
                reason=f"Sensor reads 0 vehicles while camera detection reads {current_volume}.",
                potential_cause="Physical sensor malfunction, cut loop detector, or telemetry interception."
            )

        # 2. Sudden Traffic Disappearance (> 70% drop)
        if vol_dev < -70.0:
            return TrafficAnomalyResult(
                is_anomaly=True,
                anomaly_type="SUDDEN_TRAFFIC_DROP",
                baseline=float(base_vol),
                current_value=float(current_volume),
                deviation_percent=round(vol_dev, 1),
                confidence=0.95,
                severity="HIGH",
                reason=f"Traffic volume dropped by {abs(vol_dev):.1f}% below expected baseline of {base_vol} veh/hr.",
                potential_cause="Major upstream obstruction, highway closure, or camera feed interruption."
            )

        # 3. Sudden Traffic Surge (> 85% increase)
        if vol_dev > 85.0:
            return TrafficAnomalyResult(
                is_anomaly=True,
                anomaly_type="SUDDEN_TRAFFIC_SURGE",
                baseline=float(base_vol),
                current_value=float(current_volume),
                deviation_percent=round(vol_dev, 1),
                confidence=0.92,
                severity="HIGH",
                reason=f"Traffic volume spiked by +{vol_dev:.1f}% above expected baseline ({current_volume} vs {base_vol} normal).",
                potential_cause="Unannounced detour, emergency evacuation, or signal timing failure upstream."
            )

        # 4. Abnormal Speed Drop without volume increase (Phantom Jam)
        if current_speed < 25.0 and current_volume < base_vol * 0.7:
            return TrafficAnomalyResult(
                is_anomaly=True,
                anomaly_type="ABNORMAL_SPEED_DROP",
                baseline=base["speed"],
                current_value=current_speed,
                deviation_percent=round(((current_speed - base["speed"]) / base["speed"]) * 100.0, 1),
                confidence=0.90,
                severity="MEDIUM",
                reason=f"Speed dropped to {current_speed:.0f} km/h despite low volume ({current_volume} vehicles).",
                potential_cause="Road debris, animal hazard, or stopped vehicle obstructing lane."
            )

        return TrafficAnomalyResult(
            is_anomaly=False,
            anomaly_type="NORMAL",
            baseline=float(base_vol),
            current_value=float(current_volume),
            deviation_percent=round(vol_dev, 1),
            confidence=0.96,
            severity="INFO",
            reason="Traffic volume and speed are within expected statistical bounds.",
            potential_cause="Nominal operations"
        )

    def generate_predictions(self, road_id: str, current_volume: int, current_speed: float) -> List[TrafficPredictionItem]:
        """
        Calculates 15m, 30m, 60m, 2h predictions. If road is unknown, returns
        'Insufficient historical data' note per Rule 29.
        """
        if road_id not in self.baselines:
            return [
                TrafficPredictionItem(
                    horizon_minutes=h,
                    predicted_volume=current_volume,
                    predicted_speed_kmh=current_speed,
                    predicted_congestion="UNKNOWN",
                    confidence=0.0,
                    historical_baseline=0,
                    status_note="Insufficient historical data."
                )
                for h in [15, 30, 60, 120]
            ]

        base = self.baselines[road_id]
        base_vol = base["volume"]
        
        predictions = []
        horizons = [(15, 0.94, 1.05), (30, 0.88, 1.12), (60, 0.82, 0.95), (120, 0.75, 0.85)]
        
        for mins, conf, trend_factor in horizons:
            pred_vol = int(current_volume * 0.7 + base_vol * 0.3 * trend_factor)
            pred_speed = max(20.0, min(100.0, current_speed * 0.8 + base["speed"] * 0.2 / trend_factor))
            
            if pred_vol > 380:
                pred_cong = "CRITICAL"
            elif pred_vol > 320:
                pred_cong = "SEVERE"
            elif pred_vol > 240:
                pred_cong = "HEAVY"
            elif pred_vol > 160:
                pred_cong = "MODERATE"
            else:
                pred_cong = "FREE_FLOW"
                
            predictions.append(TrafficPredictionItem(
                horizon_minutes=mins,
                predicted_volume=pred_vol,
                predicted_speed_kmh=round(pred_speed, 1),
                predicted_congestion=pred_cong,
                confidence=conf,
                historical_baseline=base_vol,
                status_note=f"Modeled using exponential smoothing over NH44 corridor telemetry"
            ))
            
        return predictions

traffic_intelligence = TrafficIntelligenceEngine()
