@echo off
REM Engineering Chatbot - Startup Script for Windows

echo.
echo ============================================
echo   Engineering Chatbot Startup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements_packages.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    exit /b 1
)

echo [2/4] Initializing database...
python initialize.py
if %errorlevel% neq 0 (
    echo Error: Initialization failed
    exit /b 1
)

echo.
echo [3/4] Starting Backend API (Port 8000)...
echo Starting: python run_backend.py
start cmd /k python run_backend.py

timeout /t 3 /nobreak

echo [4/4] Starting Frontend UI (Port 8501)...
echo Starting: streamlit run frontend/app.py
start cmd /k streamlit run frontend/app.py

echo.
echo ============================================
echo   Chatbot is starting...
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:8501
echo   Admin Password: admin123
echo ============================================
echo.

pause
