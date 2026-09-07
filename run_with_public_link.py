import os
import re
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

# Configure UTF-8 for console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

def start_server():
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="warning")

def start_tunnel():
    cloudflared_exe = BASE_DIR / "cloudflared.exe"
    if not cloudflared_exe.exists():
        print("⚠️ cloudflared.exe not found.")
        return

    cmd = [str(cloudflared_exe), "tunnel", "--url", "http://127.0.0.1:8000"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read stderr where Cloudflare logs the tunnel URL
    for line in proc.stderr:
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        print("\n" + "=" * 65)
        print("🎉 YOUR 100% FREE PUBLIC ONLINE LINK IS LIVE!")
        print("=" * 65)
        print(f"\n🌐 Public HTTPS URL: {public_url}")
        print(f"🏠 Local URL:        http://localhost:8000")
        print("\n📱 You can now open this link on your Mobile, Tablet, or PC anywhere in the world!")
        print("=" * 65 + "\n")
        
        # Open in browser after a short delay
        time.sleep(1)
        webbrowser.open(public_url)

def main():
    print("=" * 65)
    print("💀 ReelBot.Ai (Beta) - 1-Click Instant Free Online Launcher")
    print("=================================================================")
    print("Starting local server & generating your free public HTTPS link...\n")

    # Start Uvicorn in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1.5)
    # Start Cloudflare tunnel
    start_tunnel()

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down ReelBot.Ai...")

if __name__ == "__main__":
    main()
