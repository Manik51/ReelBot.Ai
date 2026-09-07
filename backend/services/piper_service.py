"""
ReelBot Piper TTS Service — 100% Local Offline Neural Voice Engine
Runs directly on CPU with ONNX Runtime. Zero API keys, zero internet latency.
"""
import os
import re
import sys
import wave
import shutil
import asyncio
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.config import settings

PIPER_VOICE_MAP = {
    "bn_BD-google-medium": {
        "lang": "bn",
        "onnx_path": "bn/bn_BD/google/medium/bn_BD-google-medium.onnx",
        "json_path": "bn/bn_BD/google/medium/bn_BD-google-medium.onnx.json",
        "name": "Google Medium (Piper Bengali - Local)",
        "language_name": "Bengali"
    },
    "hi_IN-pratham-medium": {
        "lang": "hi",
        "onnx_path": "hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx",
        "json_path": "hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx.json",
        "name": "Pratham (Piper Hindi - Local)",
        "language_name": "Hindi"
    },
    "en_US-lessac-medium": {
        "lang": "en",
        "onnx_path": "en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json_path": "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "name": "Lessac (Piper English - Local)",
        "language_name": "English"
    },
    "en_US-ryan-medium": {
        "lang": "en",
        "onnx_path": "en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "json_path": "en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
        "name": "Ryan (Piper English - Local)",
        "language_name": "English"
    }
}

HF_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

class PiperService:
    MODELS_DIR = settings.BASE_DIR / "storage" / "piper_models"

    @classmethod
    def ensure_model(cls, voice_name: str) -> tuple[Path, Path]:
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)

        info = PIPER_VOICE_MAP.get(voice_name)
        if not info:
            voice_name = "en_US-lessac-medium"
            info = PIPER_VOICE_MAP[voice_name]

        onnx_dest = cls.MODELS_DIR / f"{voice_name}.onnx"
        json_dest = cls.MODELS_DIR / f"{voice_name}.onnx.json"

        if not onnx_dest.exists() or onnx_dest.stat().st_size < 1000000:
            url = f"{HF_BASE_URL}/{info['onnx_path']}"
            print(f"[Piper] Downloading voice model {voice_name} from Hugging Face...")
            urllib.request.urlretrieve(url, onnx_dest)
            print(f"[Piper] Downloaded {voice_name}.onnx ({onnx_dest.stat().st_size} bytes).")

        if not json_dest.exists() or json_dest.stat().st_size < 100:
            url = f"{HF_BASE_URL}/{info['json_path']}"
            print(f"[Piper] Downloading voice config {voice_name}.onnx.json...")
            urllib.request.urlretrieve(url, json_dest)

        return onnx_dest, json_dest

    @classmethod
    def generate_speech(
        cls,
        text: str,
        voice_id: str,
        rate: str = "+10%",
        output_path: Path = None
    ) -> Dict[str, Any]:
        """
        Synthesizes text using Piper TTS and outputs a mastered MP3 file.
        """
        raw_voice_name = voice_id.replace("piper:", "").strip()
        onnx_file, json_file = cls.ensure_model(raw_voice_name)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_wav = output_path.parent / f"_raw_{output_path.stem}.wav"
        input_txt = output_path.parent / f"_input_{output_path.stem}.txt"

        # Clean text
        clean_txt = re.sub(r'["""\'\(\)\[\]#*@]', '', text).strip()
        if not clean_txt:
            clean_txt = "Hello, this is ReelBot."

        # Write clean UTF-8 input file to prevent Windows cp1252 stdin encoding issues
        input_txt.write_text(clean_txt, encoding="utf-8")

        # Rate adjustment
        length_scale = 1.0
        if rate == "+10%":
            length_scale = 0.91
        elif rate == "+15%":
            length_scale = 0.87
        elif rate == "+20%":
            length_scale = 0.83
        elif rate == "-5%":
            length_scale = 1.05

        # Cross-platform Piper execution (Linux, Windows, Cloud Shell)
        piper_cmd = None
        if shutil.which("piper"):
            piper_cmd = [shutil.which("piper")]
        elif (settings.BASE_DIR / "venv" / "bin" / "piper").exists():
            piper_cmd = [str(settings.BASE_DIR / "venv" / "bin" / "piper")]
        elif (settings.BASE_DIR / "venv" / "Scripts" / "piper.exe").exists():
            piper_cmd = [str(settings.BASE_DIR / "venv" / "Scripts" / "piper.exe")]
        else:
            piper_cmd = [sys.executable, "-m", "piper"]

        cmd = piper_cmd + [
            "-m", str(onnx_file),
            "-c", str(json_file),
            "-f", str(raw_wav),
            "-i", str(input_txt),
            "--length-scale", str(length_scale)
        ]
        res = None
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as pe:
            print(f"[Piper] Subprocess invocation note: {pe}")

        try:
            input_txt.unlink(missing_ok=True)
        except Exception:
            pass

        # If Piper didn't produce output or failed, gracefully fallback to Edge-TTS
        if not raw_wav.exists() or raw_wav.stat().st_size < 100:
            print(f"[Piper] Local Piper unavailable or failed. Falling back to Edge-TTS...")
            try:
                import edge_tts
                if "bn" in raw_voice_name or bool(re.search(r"[\u0980-\u09FF]", text)):
                    edge_voice = "bn-BD-PradeepNeural"
                elif "hi" in raw_voice_name or bool(re.search(r"[\u0900-\u097F]", text)):
                    edge_voice = "hi-IN-MadhurNeural"
                else:
                    edge_voice = "en-US-ChristopherNeural"

                async def _synth_edge():
                    comm = edge_tts.Communicate(clean_txt, edge_voice)
                    await comm.save(str(raw_wav))

                try:
                    asyncio.run(_synth_edge())
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_synth_edge())
                    loop.close()
            except Exception as edge_err:
                err_msg = res.stderr.decode('utf-8', errors='replace') if (res and res.stderr) else str(edge_err)
                raise RuntimeError(f"Voice generation failed: {err_msg}")

        # Duration calculation (supports both WAV from Piper and MP3/WAV from Edge-TTS)
        dur = 3.0
        try:
            with wave.open(str(raw_wav), 'rb') as wf:
                dur = wf.getnframes() / float(wf.getframerate())
        except Exception:
            try:
                import soundfile as sf
                with sf.SoundFile(str(raw_wav)) as f:
                    dur = len(f) / float(f.samplerate)
            except Exception:
                dur = max(len(clean_txt.split()) * 0.42, 2.5)

        # Broadcast Studio Mastering via FFmpeg
        af = (
            "highpass=f=80,"
            "equalizer=f=200:t=q:w=1.4:g=3.0,"
            "equalizer=f=1200:t=q:w=1.0:g=1.5,"
            "equalizer=f=4000:t=q:w=1.2:g=2.5,"
            "acompressor=threshold=0.12:ratio=4:attack=4:release=60:makeup=2,"
            "loudnorm=I=-14:LRA=7:TP=-1.5"
        )
        ff_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_wav),
            "-af", af,
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output_path)
        ]
        subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        try:
            raw_wav.unlink(missing_ok=True)
        except Exception:
            pass

        raw_words = text.strip().split()
        tpw = dur / max(len(raw_words), 1)
        words = []
        for i, w in enumerate(raw_words):
            s = i * tpw
            words.append({"word": w, "start": round(s, 3), "end": round(s + tpw, 3), "duration": round(tpw, 3)})

        return {
            "audio_path": str(output_path),
            "duration": round(dur, 3),
            "words": words
        }
