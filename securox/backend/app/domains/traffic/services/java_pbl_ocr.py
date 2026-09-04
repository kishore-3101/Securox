import os
import subprocess
import json
import tempfile
import logging
from typing import Dict, Any

logger = logging.getLogger("securox.java_pbl_ocr")

JAVA_PBL_DIR = r"C:\Users\praja\OneDrive\Desktop\JAVA PBL\park-x"
JAR_PATH = os.path.join(JAVA_PBL_DIR, "target", "park-x-1.0.0.jar")
SRC_DIR = os.path.join(JAVA_PBL_DIR, "src", "main", "java")
CLASSPATH = f"{SRC_DIR};{JAR_PATH}"

def run_java_pbl_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Executes the Java PBL (park-x) OCR Pipeline using:
    - com.parkx.ocr.PlateBridge
    - com.parkx.ocr.TesseractOCREngine (Tess4J 5.11.0)
    - com.parkx.ocr.PlateNormalizer
    - com.parkx.camera.VehicleDetector
    - com.parkx.ocr.ImagePreprocessor
    """
    if not os.path.exists(JAR_PATH):
        logger.warning(f"Java PBL JAR not found at {JAR_PATH}")
        return {"extracted_plate": "UNKNOWN", "confidence": 0.0, "engine": "NONE"}

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_bytes)
            temp_path = f.name

        cmd = [
            "java",
            "--enable-native-access=ALL-UNNAMED",
            "-cp",
            CLASSPATH,
            "com.parkx.ocr.PlateBridge",
            temp_path
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=JAVA_PBL_DIR,
            timeout=10
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        # Parse JSON line from PlateBridge
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and "extracted_plate" in line:
                try:
                    parsed = json.loads(line)
                    plate = parsed.get("extracted_plate", "UNKNOWN")
                    conf = float(parsed.get("confidence", 0.0)) * 100.0 if parsed.get("confidence", 0) <= 1.0 else float(parsed.get("confidence", 0.0))
                    return {
                        "extracted_plate": plate,
                        "confidence": round(conf, 1),
                        "engine": "JAVA_PBL_PARK_X",
                        "status": "DETECTED" if plate not in ["UNKNOWN", "ERROR", ""] else "NO_PLATE_DETECTED"
                    }
                except Exception:
                    pass

        logger.debug(f"Java OCR raw output: {stdout} | Stderr: {stderr}")
        return {"extracted_plate": "UNKNOWN", "confidence": 0.0, "engine": "JAVA_PBL_PARK_X"}

    except Exception as e:
        logger.error(f"Java PBL OCR execution error: {e}")
        return {"extracted_plate": "ERROR", "details": str(e), "engine": "JAVA_PBL_PARK_X"}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
