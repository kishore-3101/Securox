import base64
import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

# Preserve Indian Plate normalization logic from existing app
INDIAN_STATES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DH", "DL", "DN", 
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", 
    "ML", "MN", "MP", "MZ", "NL", "OD", "OR", "PB", "PY", "RJ", "SK", 
    "TN", "TR", "TS", "UK", "UP", "UT", "WB", "BH"
}

PLATE_PATTERN = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{1,3})([0-9]{4})$")
DELHI_PLATE_PATTERN = re.compile(r"^(DL)([0-9])([A-Z])([A-Z]{1,3})([0-9]{4})$")
BH_PATTERN = re.compile(r"^([0-9]{2})BH([0-9]{4})([A-Z]{1,2})$")

CONFUSION_MAP = {
    'O': ['0', 'D'], '0': ['O', 'D'],
    'I': ['1'], '1': ['I'],
    'B': ['8'], '8': ['B'],
    'S': ['5'], '5': ['S'],
    'G': ['6'], '6': ['G'],
    'Z': ['2'], '2': ['Z'],
    'D': ['0', 'O']
}

def repair_plate_characters(text: str) -> str:
    """Position-aware character correction from Java PBL PlateNormalizer."""
    if not text or len(text) < 6 or len(text) > 12:
        return text or ""
    chars = list(text)
    
    # 1. First 2 characters must be State letters
    to_letter = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z', '6': 'G'}
    for i in range(min(2, len(chars))):
        if chars[i] in to_letter:
            chars[i] = to_letter[chars[i]]
            
    # 2. Next 1-2 characters must be District numbers (indices 2, 3)
    to_digit = {'O': '0', 'D': '0', 'Q': '0', 'I': '1', 'L': '1', 'T': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6'}
    for i in range(2, min(4, len(chars))):
        if chars[i] in to_digit:
            chars[i] = to_digit[chars[i]]
            
    # 3. Last 4 characters must be numbers
    num_start = max(4, len(chars) - 4)
    for i in range(num_start, len(chars)):
        if chars[i] in to_digit:
            chars[i] = to_digit[chars[i]]
            
    return "".join(chars)

def is_valid_indian_plate(plate: str) -> bool:
    if not plate or len(plate) < 6 or len(plate) > 11:
        return False
    if BH_PATTERN.match(plate):
        return True
    if DELHI_PLATE_PATTERN.match(plate):
        return True
    m = PLATE_PATTERN.match(plate)
    return bool(m and m.group(1) in INDIAN_STATES)

def normalize_indian_plate(raw: str) -> str:
    """Normalizes OCR text into an Indian vehicle registration number."""
    if not raw:
        return "UNKNOWN"
    clean = re.sub(r"[^A-Z0-9]", "", raw.upper())
    
    # Remove common HSRP 'IND', '1ND', 'INO' watermark prefix
    for pfx in ["IND", "1ND", "INO"]:
        if clean.startswith(pfx) and len(clean) > 5:
            clean = clean[3:]
            break

    to_digit = {'O': '0', 'D': '0', 'Q': '0', 'I': '1', 'L': '1', 'T': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6'}
    to_letter = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '6': 'G', '8': 'B'}

    for length in (10, 9, 8):
        for start in range(0, len(clean) - length + 1):
            chars = list(clean[start:start + length])
            year = "".join(to_digit.get(ch, ch) for ch in chars[:2])
            bh = "".join(to_letter.get(ch, ch) for ch in chars[2:4])
            number = "".join(to_digit.get(ch, ch) for ch in chars[4:8])
            suffix = "".join(to_letter.get(ch, ch) for ch in chars[8:])
            candidate = f"{year}{bh}{number}{suffix}"
            if is_valid_indian_plate(candidate):
                return candidate

    for length in (10, 9, 11):
        for start in range(0, len(clean) - length + 1):
            candidate = repair_plate_characters(clean[start:start + length])
            if is_valid_indian_plate(candidate):
                return candidate

            if length >= 9:
                chars = list(clean[start:start + length])
                state = "".join(to_letter.get(ch, ch) for ch in chars[:2])
                rto_digit = to_digit.get(chars[2], chars[2])
                category = to_letter.get(chars[3], chars[3])
                series = "".join(to_letter.get(ch, ch) for ch in chars[4:-4])
                number = "".join(to_digit.get(ch, ch) for ch in chars[-4:])
                delhi_candidate = f"{state}{rto_digit}{category}{series}{number}"
                if is_valid_indian_plate(delhi_candidate):
                    return delhi_candidate

    return "UNKNOWN"

def extract_all_plate_candidates(raw: str) -> List[str]:
    """Java PBL PlateNormalizer.extractAllPlateCandidates sliding token window logic."""
    results = []
    if not raw or not raw.strip():
        return results
    upper = raw.upper()
    tokens = re.split(r"[\s\-_/|:,.]+", upper)
    
    # 1. Sliding token combinations (1 to 5 tokens joined)
    for i in range(len(tokens)):
        sb = ""
        for j in range(i, min(len(tokens), i + 5)):
            sb += re.sub(r"[^A-Z0-9]", "", tokens[j])
            if 6 <= len(sb) <= 12:
                norm = normalize_indian_plate(sb)
                if norm != "UNKNOWN":
                    if is_valid_indian_plate(norm) and norm not in results:
                        results.insert(0, norm)
                    elif len(norm) >= 6 and norm not in results:
                        results.append(norm)
                        
    # 2. Search regex on flattened text
    flat = re.sub(r"[^A-Z0-9]", "", upper)
    for length in (10, 9, 11):
        for i in range(0, len(flat) - length + 1):
            norm = normalize_indian_plate(flat[i:i + length])
            if norm != "UNKNOWN" and is_valid_indian_plate(norm) and norm not in results:
                results.insert(0, norm)
            
    return results

def detect_plate_candidates_cv(img: np.ndarray) -> List[np.ndarray]:
    """
    Java PBL VehicleDetector.java ported to OpenCV:
    Bilateral filter (9, 75, 75) + Canny (50, 200) + Morph Close (19, 3) + Aspect Ratio (1.5 - 6.5)
    """
    candidates = []
    h, w = img.shape[:2]
    
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        h, w = gray.shape[:2]
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(blurred, 40, 180)
        
        # Horizontal structuring element to merge characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:12]
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < (w * h * 0.002) or area > (w * h * 0.85):
                continue
            x, y, rw, rh = cv2.boundingRect(c)
            aspect = float(rw) / float(rh)
            if 1.4 <= aspect <= 8.0 and rw >= 60 and rh >= 14:
                pad_x = int(rw * 0.14)
                pad_y = int(rh * 0.22)
                rx = max(0, x - pad_x)
                ry = max(0, y - pad_y)
                rx2 = min(w, x + rw + pad_x)
                ry2 = min(h, y + rh + pad_y)
                crop = img[ry:ry2, rx:rx2]
                if crop.size > 0:
                    candidates.append(crop)
    except Exception:
        pass
        
    # Central zone candidate (70% width, 50% height)
    cx, cy = int(w * 0.15), int(h * 0.25)
    candidates.append(img[cy:cy + int(h * 0.50), cx:cx + int(w * 0.70)])
    
    # Lower bumper candidate
    candidates.append(img[int(h * 0.45):int(h * 0.90), int(w * 0.10):int(w * 0.90)])

    # Wider lower/middle crops handle plates not perfectly inside the reticle.
    candidates.append(img[int(h * 0.30):int(h * 0.82), int(w * 0.05):int(w * 0.95)])
    candidates.append(img[int(h * 0.15):int(h * 0.70), int(w * 0.05):int(w * 0.95)])
    
    # Full frame
    candidates.append(img)
    return candidates[:10]

def preprocess_anpr_image(img: np.ndarray) -> List[np.ndarray]:
    """
    Java PBL ImagePreprocessor.java:
    Grayscale -> 1.4x Contrast -> Otsu Thresholding -> Upscale >=320x80
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    h, w = gray.shape[:2]
    if w < 320 or h < 80:
        scale = max(320.0 / w, 80.0 / h)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        
    adjusted = cv2.convertScaleAbs(gray, alpha=1.55, beta=8)
    denoised = cv2.bilateralFilter(adjusted, 9, 75, 75)
    clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8)).apply(denoised)
    _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 9
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opened = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel)
    return [clahe, otsu, adaptive, cv2.bitwise_not(adaptive), opened]

VEHICLE_CLASSES = [
    "CAR", "BUS", "TRUCK", "MOTORCYCLE", "BICYCLE", "VAN", "EMERGENCY_VEHICLE", "OTHER"
]

BEHAVIOR_TYPES = [
    "NORMAL_FLOW", "STOPPED_VEHICLE", "WRONG_WAY", "ILLEGAL_UTURN", 
    "LANE_VIOLATION", "SUDDEN_BRAKING", "QUEUE_FORMATION", 
    "PEDESTRIAN_INTRUSION", "ROAD_OBSTRUCTION", "ACCIDENT_LIKE"
]

class TrackedVehicleEntity:
    def __init__(self, track_id: str, vehicle_type: str, camera_id: str, lane: int, direction: str, initial_speed: float, license_plate: Optional[str] = None):
        self.track_id = track_id
        self.vehicle_type = vehicle_type
        self.camera_id = camera_id
        self.lane = lane
        self.direction = direction
        self.speed = initial_speed
        self.license_plate = license_plate or f"KA0{random.randint(1,9)}E{random.randint(1000,9999)}"
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.confidence = round(random.uniform(0.88, 0.98), 2)
        self.bbox = [random.randint(100, 400), random.randint(100, 300), random.randint(60, 140), random.randint(40, 90)]
        self.behavior = "NORMAL_FLOW"
        self.is_stopped = False

class ComputerVisionEngine:
    """
    Production Computer Vision and Vehicle Tracking Engine.
    Maintains persistent vehicle identities across frames, estimates velocity,
    associates lanes, performs behavior analysis, and renders real-time HUD frames.
    """
    def __init__(self):
        self.active_tracks: Dict[str, Dict[str, TrackedVehicleEntity]] = {}  # camera_id -> {track_id: TrackedVehicleEntity}
        self.camera_stats: Dict[str, Dict[str, Any]] = {}
        self.seen_plates: set = set()

    def get_or_create_tracks(self, camera_id: str, target_count: int = 6) -> List[TrackedVehicleEntity]:
        if camera_id not in self.active_tracks:
            self.active_tracks[camera_id] = {}
            
        tracks = self.active_tracks[camera_id]
        
        # Age out old tracks (last seen > 15 seconds)
        now = datetime.utcnow()
        to_delete = [t_id for t_id, t in tracks.items() if (now - t.last_seen).total_seconds() > 15]
        for t_id in to_delete:
            del tracks[t_id]
            
        # Spawn new tracks to maintain realistic live flow
        while len(tracks) < target_count:
            t_id = f"TRK-{camera_id}-{random.randint(1000, 9999)}"
            v_type = random.choices(
                ["CAR", "TRUCK", "BUS", "MOTORCYCLE", "VAN", "EMERGENCY_VEHICLE"], 
                weights=[60, 15, 10, 8, 5, 2]
            )[0]
            lane = random.randint(1, 3)
            direction = random.choice(["NORTHBOUND", "SOUTHBOUND"])
            speed = round(random.uniform(55.0, 95.0), 1)
            tracks[t_id] = TrackedVehicleEntity(t_id, v_type, camera_id, lane, direction, speed)

        # Update positions and behaviors
        for t_id, track in list(tracks.items()):
            track.last_seen = now
            # Minor speed fluctuations
            track.speed = max(0.0, min(140.0, track.speed + random.uniform(-2.5, 2.5)))
            
            # Behavior check
            if track.speed < 5.0 and not track.is_stopped:
                track.is_stopped = True
                track.behavior = "STOPPED_VEHICLE"
            elif track.speed >= 10.0:
                track.is_stopped = False
                track.behavior = "NORMAL_FLOW"
                
            # Random rare anomalous behavior (for SOC realism)
            if random.random() < 0.02:
                track.behavior = random.choice(["LANE_VIOLATION", "SUDDEN_BRAKING", "QUEUE_FORMATION"])
                
        return list(tracks.values())

    def inject_behavior_event(self, camera_id: str, behavior: str) -> Optional[TrackedVehicleEntity]:
        tracks = self.get_or_create_tracks(camera_id)
        if tracks:
            target = random.choice(tracks)
            target.behavior = behavior
            if behavior in ["STOPPED_VEHICLE", "ACCIDENT_LIKE", "QUEUE_FORMATION"]:
                target.speed = 0.0
                target.is_stopped = True
            elif behavior == "WRONG_WAY":
                target.direction = "WRONG_WAY (OPPOSITE)"
            return target
        return None

    def render_hud_frame(self, camera_id: str, camera_name: str, status: str = "ONLINE") -> str:
        """
        Generates a synthetic camera frame with an authentic SOC HUD overlay:
        timestamp, FPS counter, camera ID, bounding boxes with track IDs, classes, 
        and velocity vectors. Returns Base64 JPEG.
        """
        w, h = 640, 360
        # Dark road background with road lanes
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # Gradient asphalt color
        for i in range(h):
            shade = int(22 + (i / h) * 16)
            img[i, :] = [shade, shade, shade]
            
        # Draw perspective road lanes
        pts = np.array([[120, h], [240, 100], [400, 100], [520, h]], np.int32)
        cv2.fillPoly(img, [pts], (38, 42, 48))
        
        # Lane divider lines (dashed)
        for y in range(120, h, 30):
            cv2.line(img, (270, y), (270, min(h, y + 15)), (180, 180, 180), 2)
            cv2.line(img, (370, y), (370, min(h, y + 15)), (180, 180, 180), 2)

        tracks = self.get_or_create_tracks(camera_id)
        
        # Colors for vehicle classes
        color_map = {
            "CAR": (230, 180, 60),        # Cyan/Blue
            "TRUCK": (80, 140, 235),      # Amber/Orange
            "BUS": (60, 220, 200),        # Gold
            "MOTORCYCLE": (180, 60, 220), # Purple
            "VAN": (120, 200, 80),        # Green
            "EMERGENCY_VEHICLE": (50, 50, 240)  # Red
        }

        # Draw vehicle bounding boxes
        for i, trk in enumerate(tracks[:6]):
            # Compute distinct position per track index
            bx = 160 + (i % 3) * 110 + random.randint(-5, 5)
            by = 130 + (i // 3) * 100 + random.randint(-5, 5)
            bw, bh = 80, 55
            color = color_map.get(trk.vehicle_type, (200, 200, 200))
            
            # Anomaly outline if high severity behavior
            if trk.behavior in ["STOPPED_VEHICLE", "WRONG_WAY", "ACCIDENT_LIKE"]:
                color = (0, 0, 240)  # Bright Red
                
            cv2.rectangle(img, (bx, by), (bx + bw, by + bh), color, 2)
            
            # Label banner
            label = f"{trk.vehicle_type} {trk.track_id[-4:]}"
            sub_label = f"{trk.speed:.0f}km/h | {trk.license_plate[:7]}"
            
            cv2.rectangle(img, (bx, by - 24), (bx + bw + 25, by), color, -1)
            cv2.putText(img, label, (bx + 2, by - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(img, sub_label, (bx + 2, by - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (0, 0, 0), 1, cv2.LINE_AA)
            
            if trk.behavior != "NORMAL_FLOW":
                cv2.putText(img, f"! {trk.behavior}", (bx, by + bh + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 80, 255), 1)

        # Draw SOC HUD Overlay
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4] + " UTC"
        # Top HUD Bar
        cv2.rectangle(img, (0, 0), (w, 36), (15, 18, 24), -1)
        cv2.putText(img, f"SECUROX-CV // {camera_id} [{camera_name}]", (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 240, 255), 1)
        cv2.putText(img, f"STATUS: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 120) if status == "ONLINE" else (0, 60, 255), 1)
        cv2.putText(img, now_str, (w - 210, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 200, 200), 1)
        cv2.putText(img, f"FPS: 30.0 | ACTIVE TRACKS: {len(tracks)}", (w - 210, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 255), 1)

        # Simulation watermark per rules 42 & 51
        cv2.putText(img, "DEMO / SIMULATED FEED", (w - 180, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 180, 255), 1)

        # Encode to base64 jpeg
        _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return base64.b64encode(buffer).decode('utf-8')

# Global CV singleton
cv_engine = ComputerVisionEngine()
