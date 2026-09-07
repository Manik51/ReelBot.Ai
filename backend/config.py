import os
from pathlib import Path
from typing import List, Dict, Any

class Settings:
    APP_NAME: str = "SkullBot.Ai"
    APP_VERSION: str = "2.6.0-beta"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    OUTPUT_DIR: Path = STORAGE_DIR / "output"
    BGM_DIR: Path = BASE_DIR / "backend" / "assets" / "bgm"
    SFX_DIR: Path = BASE_DIR / "backend" / "assets" / "sfx"

    def __init__(self):
        # Auto-load .env file if present
        env_file = self.BASE_DIR / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.strip().split("=", 1)
                        if not os.getenv(k):
                            os.environ[k] = v
            except Exception:
                pass

        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
        self.AI4BHARAT_API_KEY = os.getenv("AI4BHARAT_API_KEY", "")
        self.SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
        self.PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
        self.TENOR_API_KEY = os.getenv("TENOR_API_KEY", "")
        self.GIPHY_API_KEY = os.getenv("GIPHY_API_KEY", "")

    VOICES: List[Dict[str, Any]] = [
        # ── Piper TTS — 100% Local Offline Neural Engine (Zero API Key) ───────
        {"id": "piper:bn_BD-google-medium", "name": "🇧🇩 Piper — Google Medium · Bengali Neural (Local Offline)", "recommended_for": "Bengali"},
        {"id": "piper:hi_IN-pratham-medium", "name": "🇮🇳 Piper — Pratham · Hindi Neural Male (Local Offline)", "recommended_for": "Hindi"},
        {"id": "piper:en_US-lessac-medium",  "name": "🇺🇸 Piper — Lessac · English Clear Neutral (Local Offline)", "recommended_for": "English"},
        {"id": "piper:en_US-ryan-medium",    "name": "🇺🇸 Piper — Ryan · English Dynamic Male (Local Offline)", "recommended_for": "English"},

        # ── Kokoro ONNX — Best 3 Studio Voices (100% Local Offline) ───────────
        {"id": "kokoro:am_adam",  "name": "🇺🇸 Kokoro — Adam · Studio Deep Voice (English)",             "recommended_for": "English"},
        {"id": "kokoro:af_bella", "name": "🇺🇸 Kokoro — Bella · Expressive Cinematic Female (English)",  "recommended_for": "English"},
        {"id": "kokoro:am_echo",  "name": "🇺🇸 Kokoro — Echo · Smooth Narrator Male (English)",          "recommended_for": "English"},
    ]

    SUBTITLE_STYLES: List[Dict[str, Any]] = [
        {
            "id": "hormozi_yellow",
            "name": "🔥 Hormozi Viral Yellow (Alex Hormozi Word-POP)",
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H0000E5FF",
            "outline_color": "&H00000000",
            "shadow_color": "&H80000000",
            "font_size": 78,
            "font_name": "Impact",
            "bold": 1,
            "max_words_per_line": 3
        },
        {
            "id": "crimson_wine",
            "name": "🍷 SkullBot Crimson Wine (True Crime Red Glow)",
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H003A1EC4",
            "outline_color": "&H00000000",
            "shadow_color": "&H80000000",
            "font_size": 78,
            "font_name": "Impact",
            "bold": 1,
            "max_words_per_line": 3
        },
        {
            "id": "hormozi_green",
            "name": "💚 Beast High-Voltage Green",
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H0000FF66",
            "outline_color": "&H00000000",
            "shadow_color": "&H80000000",
            "font_size": 78,
            "font_name": "Impact",
            "bold": 1,
            "max_words_per_line": 3
        },
        {
            "id": "cyber_cyan",
            "name": "💎 Neon Cyber Cyan",
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H00FFFF00",
            "outline_color": "&H00000000",
            "shadow_color": "&H80000000",
            "font_size": 78,
            "font_name": "Impact",
            "bold": 1,
            "max_words_per_line": 3
        }
    ]

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.BGM_DIR.mkdir(parents=True, exist_ok=True)
