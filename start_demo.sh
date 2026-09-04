#!/usr/bin/env bash
# ==================================================================
# SECurox: Smart City Cyber Risk Detection & Operations Center
# SH-FIN-05 Target Implementation
# ==================================================================

set -e

echo ""
echo "  =================================================================="
echo "    SECurox: Smart City Cyber Risk Detection & Operations Center"
echo "    SH-FIN-05 Target Implementation"
echo "  =================================================================="
echo ""

# Check python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 not found. Please install Python 3.9+."
    exit 1
fi

echo "[*] Python verified: $($PYTHON_CMD --version)"

# Set PYTHONPATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/finance/backend:${SCRIPT_DIR}/finance:${PYTHONPATH}"

# Check dependencies
$PYTHON_CMD -c "import fastapi, uvicorn, sklearn, pydantic" 2>/dev/null || {
    echo "[*] Installing required packages..."
    pip install -r "${SCRIPT_DIR}/finance/backend/requirements.txt"
}

echo ""
echo "=================================================================="
echo "  SECurox Smart City Operations Center Launching"
echo "=================================================================="
echo ""
echo "  Dashboard SOC:      http://localhost:8000"
echo "  API Documentation:  http://localhost:8000/docs"
echo ""
echo "  Default Credentials: admin / admin123"
echo "  Press Ctrl+C to terminate the SOC gateway."
echo "=================================================================="
echo ""

# Launch browser if supported
if command -v xdg-open &>/dev/null; then
    (sleep 3 && xdg-open "http://localhost:8000") &
elif command -v open &>/dev/null; then
    (sleep 3 && open "http://localhost:8000") &
fi

cd "${SCRIPT_DIR}/finance/backend"
exec $PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
