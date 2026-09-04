#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Securox — Quick Start Script
# Supports: local Python | Docker
# Usage:  ./start.sh           (local)
#         ./start.sh docker    (docker-compose)
# ─────────────────────────────────────────────────────────────────────────────
set -e

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'

banner() {
  echo -e "${CYAN}"
  echo "  ███████╗███████╗██████╗ ██╗   ██╗██████╗ ██████╗ ██╗  ██╗"
  echo "  ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔═══██╗╚██╗██╔╝"
  echo "  ███████╗█████╗  ██║     ██║   ██║██████╔╝██║   ██║ ╚███╔╝"
  echo "  ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██║   ██║ ██╔██╗"
  echo "  ███████║███████╗╚██████╗╚██████╔╝██║  ██║╚██████╔╝██╔╝ ██╗"
  echo "  ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝"
  echo -e "${NC}"
  echo -e "  ${BOLD}Autonomous Cyber Risk Intelligence Platform for Smart Cities${NC}"
  echo "  ─────────────────────────────────────────────────────────────"
}

banner

MODE=${1:-local}

# ── DOCKER MODE ───────────────────────────────────────────────────────────────
if [ "$MODE" = "docker" ]; then
  echo -e "${CYAN}[Docker] Building and starting containers…${NC}"
  if ! command -v docker &>/dev/null; then
    echo -e "${RED}Error: Docker not found. Install Docker Desktop first.${NC}"; exit 1
  fi
  docker compose up --build -d
  echo -e "${GREEN}✓ Securox running via Docker${NC}"
  echo -e "  API:       ${CYAN}http://localhost:8000${NC}"
  echo -e "  Dashboard: ${CYAN}http://localhost:80${NC}"
  echo -e "  API Docs:  ${CYAN}http://localhost:8000/docs${NC}"
  exit 0
fi

# ── LOCAL MODE ────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[Local] Setting up Python environment…${NC}"

# Check Python version
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo -e "${RED}Error: Python 3.9+ required.${NC}"; exit 1
fi

PY_VER=$($PYTHON -c "import sys; print(sys.version_info.minor)")
if [ "$PY_VER" -lt 9 ]; then
  echo -e "${RED}Error: Python 3.9+ required (found 3.$PY_VER).${NC}"; exit 1
fi
echo -e "${GREEN}✓ Python OK${NC}"

# Virtualenv
if [ ! -d "venv" ]; then
  echo -e "${CYAN}Creating virtual environment…${NC}"
  $PYTHON -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo -e "${CYAN}Installing dependencies (this takes ~60s first time)…${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Launch
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${BOLD}🚀 Starting Securox…${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Dashboard:  ${CYAN}http://localhost:8000${NC}  (open in browser)"
echo -e "  API Docs:   ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  WebSocket:  ${CYAN}ws://localhost:8000/ws${NC}"
echo ""
echo -e "  Demo login: ${YELLOW}admin / admin123${NC}"
echo ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop."
echo ""

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
