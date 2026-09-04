#!/usr/bin/env bash
# Render build script for Securox Smart City Cybersecurity Platform
# This script installs dependencies and builds the frontend

set -o errexit

echo "=== SECUROX BUILD START ==="

# 1. Install Python dependencies
echo "--- Installing Python dependencies ---"
pip install --upgrade pip
pip install -r securox/requirements.txt

# 2. Install ONNX Runtime for YOLOv8 inference (optional, graceful fail)
pip install onnxruntime || echo "WARN: onnxruntime not installed, YOLO inference will be simulated"

# 3. Install Node.js dependencies and build frontend
echo "--- Building frontend ---"
cd securox/frontend
npm install
npm run build
cd ../..

# 4. Copy built frontend to where the backend expects it
echo "--- Deploying frontend build ---"
if [ -d "securox/frontend/dist" ]; then
    echo "Frontend build successful: $(ls securox/frontend/dist)"
else
    echo "ERROR: Frontend build directory not found!"
    exit 1
fi

echo "=== SECUROX BUILD COMPLETE ==="
