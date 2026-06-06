#!/bin/bash

# Engineering Chatbot - Startup Script for Linux/Mac

echo ""
echo "============================================"
echo "  Engineering Chatbot Startup"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "[1/4] Installing dependencies..."
pip install -r requirements_packages.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "[2/4] Initializing database..."
python3 initialize.py
if [ $? -ne 0 ]; then
    echo "Error: Initialization failed"
    exit 1
fi

echo ""
echo "[3/4] Starting Backend API (Port 8000)..."
echo "Starting: python3 backend/main.py"
python3 backend/main.py &
BACKEND_PID=$!

sleep 3

echo "[4/4] Starting Frontend UI (Port 8501)..."
echo "Starting: streamlit run frontend/app.py"
streamlit run frontend/app.py &
FRONTEND_PID=$!

echo ""
echo "============================================"
echo "  Chatbot is starting..."
echo "  Backend API: http://localhost:8000"
echo "  Frontend UI: http://localhost:8501"
echo "  Admin Password: admin123"
echo "============================================"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
