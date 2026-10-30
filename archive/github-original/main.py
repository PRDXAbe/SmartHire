"""SmartHire Main Entry Point — Run all backend services."""
import os
import sys
import subprocess
import threading
import time


def run_server(module_path: str, port: int, name: str):
    """Run a Flask server in a separate thread."""
    print(f"[{name}] Starting on port {port}...")
    try:
        subprocess.run([sys.executable, module_path], check=True)
    except KeyboardInterrupt:
        print(f"\n[{name}] Stopped.")
    except Exception as e:
        print(f"[{name}] Error: {e}")


def main():
    """Start all SmartHire services."""
    print("=" * 60)
    print("  SmartHire — AI Recruitment Platform")
    print("  Phase 2 & 3 Backend Services")
    print("=" * 60)
    print()

    # Check prerequisites
    print("Checking prerequisites...")

    # MongoDB
    mongo_available = False
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✓ MongoDB connected (data will persist)")
        mongo_available = True
    except Exception as e:
        print("⚠ MongoDB not available — using demo mode (in-memory storage)")
        print(f"  Reason: {e}")
        print("  Note: Data will be lost when services stop. Install MongoDB for persistence.")

    # Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.ok:
            print("✓ Ollama running")
        else:
            print("✗ Ollama not responding")
    except:
        print("✗ Ollama not running")
        print("  Install Ollama: https://ollama.com/download")
        print("  Run: ollama pull mistral")

    print()
    print("Starting services...")
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Start Phase 2: Aptitude Backend (port 5001)
    aptitude_path = os.path.join(base_dir, "phase2_test_portal", "aptitude_backend", "app.py")
    threading.Thread(target=run_server, args=(aptitude_path, 5001, "Aptitude API"), daemon=True).start()
    time.sleep(1)

    # Start Phase 2: Coding Backend (port 5002)
    coding_path = os.path.join(base_dir, "phase2_test_portal", "coding_backend", "app.py")
    threading.Thread(target=run_server, args=(coding_path, 5002, "Coding API"), daemon=True).start()
    time.sleep(1)

    # Start Phase 3: Interview Backend (port 5003)
    interview_path = os.path.join(base_dir, "phase3_ai_interview", "interview_backend", "app.py")
    threading.Thread(target=run_server, args=(interview_path, 5003, "Interview API"), daemon=True).start()
    time.sleep(1)

    print()
    print("=" * 60)
    print("  Services Running!")
    print("=" * 60)
    print()
    print("  Aptitude API:   http://localhost:5001")
    print("  Coding API:     http://localhost:5002")
    print("  Interview API:  http://localhost:5003 (WebSocket)")
    print()
    print("  Frontend files:")
    print(f"    - {os.path.join(base_dir, 'phase2_test_portal', 'aptitude_frontend', 'index.html')}")
    print(f"    - {os.path.join(base_dir, 'phase2_test_portal', 'coding_frontend', 'index.html')}")
    print(f"    - {os.path.join(base_dir, 'phase2_test_portal', 'dashboard', 'index.html')}")
    print(f"    - {os.path.join(base_dir, 'phase3_ai_interview', 'interview_frontend', 'index.html')}")
    print()
    print("  Press Ctrl+C to stop all services.")
    print()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down all services...")
        sys.exit(0)


if __name__ == "__main__":
    main()
