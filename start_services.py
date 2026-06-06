#!/usr/bin/env python3
"""Start both backend and frontend services"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    # Get project root
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(backend_dir) + os.pathsep + str(project_root)
    
    print("🚀 Starting Engineering Chatbot Services...")
    print(f"📁 Project root: {project_root}")
    print()
    
    # Start backend
    print("1️⃣  Starting Backend API on port 8000...")
    backend_cmd = [sys.executable, str(project_root / "run_backend.py")]
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"   ✅ Backend process started (PID: {backend_process.pid})")
    time.sleep(3)
    
    # Start frontend
    print("\n2️⃣  Starting Frontend on port 8501...")
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", str(project_root / "frontend" / "app.py")]
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"   ✅ Frontend process started (PID: {frontend_process.pid})")
    
    print("\n" + "="*60)
    print("✨ Both services are running!")
    print("="*60)
    print("🌐 Frontend: http://localhost:8501")
    print("🔌 Backend API: http://localhost:8000")
    print("🔐 Admin Password: admin123")
    print("="*60)
    print("\nPress Ctrl+C to stop all services...\n")
    
    # Keep both processes running
    try:
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process exited!")
            if frontend_process.poll() is not None:
                print("❌ Frontend process exited!")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        time.sleep(1)
        if backend_process.poll() is None:
            backend_process.kill()
        if frontend_process.poll() is None:
            frontend_process.kill()
        print("✅ Services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
