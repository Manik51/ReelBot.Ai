import sys
import webbrowser
import uvicorn
from pathlib import Path

def main():
    print("=" * 65)
    print("💀 ReelBot.Ai (Beta) - AI Viral Shorts & Reels Engine")
    print("🌟 100% Free, Local-First, Neon Wine Red Edition")
    print("=" * 65)
    print("Starting Web Server at http://localhost:8000 ...")
    
    import threading
    import time
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
