"""
ReelBot TTS Service — Sarvam AI (Bulbul v3) + Kokoro ONLY.
Edge TTS and T5 have been completely removed.
"""
import re
import base64
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import soundfile as sf

from backend.config import settings


# ──────────────────────────────────────────────────────────────────────────────
# Studio mastering helpers
# ──────────────────────────────────────────────────────────────────────────────

def _apply_studio_mastering(raw_path: Path, out_path: Path) -> None:
    """Broadcast-grade EQ + compression + loudness normalisation via FFmpeg."""
    af = (
        "highpass=f=80,"
        "equalizer=f=200:t=q:w=1.4:g=3.0,"
        "equalizer=f=1200:t=q:w=1.0:g=1.5,"
        "equalizer=f=4000:t=q:w=1.2:g=2.5,"
        "acompressor=threshold=0.12:ratio=4:attack=4:release=60:makeup=2,"
        "loudnorm=I=-14:LRA=7:TP=-1.5"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-af", af,
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception:
        import shutil
        if raw_path != out_path:
            shutil.copy(raw_path, out_path)


def _build_word_timestamps(text: str, duration: float) -> List[Dict[str, Any]]:
    raw_words = text.strip().split()
    words: List[Dict[str, Any]] = []
    if not raw_words:
        return words
    tpw = duration / len(raw_words)
    for i, w in enumerate(raw_words):
        s = i * tpw
        words.append({"word": w, "start": round(s, 3), "end": round(s + tpw, 3), "duration": round(tpw, 3)})
    return words


def _audio_duration(path: Path) -> float:
    try:
        with sf.SoundFile(str(path)) as f:
            return len(f) / f.samplerate
    except Exception:
        return 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Sarvam AI – Bulbul v3
# ──────────────────────────────────────────────────────────────────────────────

VALID_BULBUL_V3 = [
    "shreya", "rahul", "amit", "aditya", "ritu",
    "ashutosh", "simran", "pooja", "dev", "rohan",
]

def _detect_lang(text: str) -> str:
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn-IN"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi-IN"
    return "en-IN"

def _clean_text(text: str) -> str:
    cleaned = re.sub(r'["""\'\(\)\[\]]', '', text).strip()
    return cleaned or text.strip()

def _sarvam_pace(rate: str) -> float:
    return {"+5%": 1.02, "+10%": 1.05, "+15%": 1.08, "+20%": 1.12, "-5%": 0.95}.get(rate, 1.0)


def generate_sarvam(
    text: str,
    voice_id: str,
    rate: str = "+10%",
    output_path: Path = None,
) -> Dict[str, Any]:
    key = settings.SARVAM_API_KEY.strip()
    if not key:
        raise ValueError(
            "Sarvam AI API key is not set. Please open Configure and add your Sarvam API key."
        )

    speaker = voice_id.replace("sarvam:", "").strip().lower()
    lang = _detect_lang(text)

    if speaker not in VALID_BULBUL_V3:
        speaker = "shreya" if lang == "bn-IN" else ("amit" if lang == "hi-IN" else "rahul")

    cleaned = _clean_text(text)

    resp = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"api-subscription-key": key, "Content-Type": "application/json"},
        json={
            "inputs": [cleaned],
            "target_language_code": lang,
            "speaker": speaker,
            "pace": _sarvam_pace(rate),
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v3",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam AI error ({resp.status_code}): {resp.text[:300]}")

    audios = resp.json().get("audios", [])
    if not audios:
        raise RuntimeError("Sarvam AI returned empty audio. Check your API quota.")

    audio_bytes = base64.b64decode(audios[0])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_wav = output_path.parent / f"_raw_{output_path.stem}.wav"
    raw_wav.write_bytes(audio_bytes)

    _apply_studio_mastering(raw_wav, output_path)
    try:
        raw_wav.unlink(missing_ok=True)
    except Exception:
        pass

    dur = _audio_duration(output_path)
    if dur < 0.5:
        dur = max(len(cleaned.split()) * 0.42, 2.5)

    return {
        "audio_path": str(output_path),
        "duration": round(dur, 3),
        "words": _build_word_timestamps(cleaned, dur),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Kokoro ONNX – English only
# ──────────────────────────────────────────────────────────────────────────────

_kokoro_instance = None

def _get_kokoro():
    global _kokoro_instance
    if _kokoro_instance is None:
        from kokoro_onnx import Kokoro
        mp = settings.BASE_DIR / "storage" / "models" / "kokoro-v0_19.onnx"
        vp = settings.BASE_DIR / "storage" / "models" / "voices-v1.0.bin"
        if not mp.exists() or not vp.exists():
            raise FileNotFoundError(
                "Kokoro model files not found in storage/models/. "
                "Please download kokoro-v0_19.onnx and voices-v1.0.bin."
            )
        _kokoro_instance = Kokoro(str(mp), str(vp))
    return _kokoro_instance


def generate_kokoro(
    text: str,
    voice_id: str,
    rate: str = "+10%",
    output_path: Path = None,
) -> Dict[str, Any]:
    kokoro_voice = voice_id.replace("kokoro:", "").strip()
    speed = {"+10%": 1.1, "+15%": 1.15, "+20%": 1.2}.get(rate, 1.0)

    import soundfile as _sf

    kokoro = _get_kokoro()
    samples, sample_rate = kokoro.create(text, voice=kokoro_voice, speed=speed, lang="en-us")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_wav = output_path.parent / f"_kraw_{output_path.stem}.wav"
    _sf.write(str(tmp_wav), samples, sample_rate)

    _apply_studio_mastering(tmp_wav, output_path)
    try:
        tmp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    dur = len(samples) / sample_rate
    return {
        "audio_path": str(output_path),
        "duration": round(dur, 3),
        "words": _build_word_timestamps(text, dur),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

class TTSService:
    """
    Routing:
      sarvam:*             → Sarvam AI Bulbul v3  (Bengali / Hindi / English Indic)
      kokoro:*             → Kokoro ONNX           (English only)
      Bengali/Hindi text   → Always Sarvam AI
      Edge TTS / T5        → REMOVED
    """

    @staticmethod
    def generate_voiceover(
        text: str,
        voice: str = "piper:bn_BD-google-medium",
        rate: str = "+10%",
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        if output_path is None:
            raise ValueError("output_path is required")

        # 1. Route Piper TTS (Local Neural Engine for Bengali, Hindi & English)
        if voice.startswith("piper:"):
            from backend.services.piper_service import PiperService
            return PiperService.generate_speech(text, voice, rate, output_path)

        # 2. Route Kokoro TTS (Local ONNX Studio Voices for English)
        if voice.startswith("kokoro:"):
            return generate_kokoro(text, voice, rate, output_path)

        has_bengali = bool(re.search(r"[\u0980-\u09FF]", text))
        has_hindi = bool(re.search(r"[\u0900-\u097F]", text))

        if has_bengali:
            from backend.services.piper_service import PiperService
            return PiperService.generate_speech(text, "piper:bn_BD-google-medium", rate, output_path)

        if has_hindi:
            from backend.services.piper_service import PiperService
            return PiperService.generate_speech(text, "piper:hi_IN-pratham-medium", rate, output_path)

        # Default English → Kokoro Adam
        return generate_kokoro(text, "kokoro:am_adam", rate, output_path)

    # Backward compat & convenience
    generate_kokoro_voiceover = staticmethod(generate_kokoro)

    @staticmethod
    def generate_audio_with_timings(
        text: str,
        voice_id: str = "kokoro:am_adam",
        speed: str = "+0%",
        output_path: Optional[Path] = None,
    ):
        res = TTSService.generate_voiceover(text=text, voice=voice_id, rate=speed, output_path=output_path)
        return Path(res.get("audio_path", str(output_path))), res.get("words", [])
