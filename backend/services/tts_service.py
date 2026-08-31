import asyncio
import base64
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import edge_tts
import requests
import soundfile as sf

from backend.config import settings

class TTSService:
    _kokoro_instance = None

    @classmethod
    def _get_kokoro(cls):
        if cls._kokoro_instance is None:
            from kokoro_onnx import Kokoro
            model_path = settings.MODELS_DIR / "kokoro-v0_19.onnx"
            voices_path = settings.MODELS_DIR / "voices-v1.0.bin"
            if not model_path.exists() or not voices_path.exists():
                raise FileNotFoundError("Kokoro ONNX models not found in storage/models")
            cls._kokoro_instance = Kokoro(str(model_path), str(voices_path))
        return cls._kokoro_instance

    @staticmethod
    def _apply_studio_mastering(raw_audio_path: Path, output_audio_path: Path):
        """Applies broadcast-grade vocal mastering (warm bass EQ, studio compression, loudness boost)."""
        filter_str = (
            "highpass=f=80,"
            "equalizer=f=220:t=q:w=1.5:g=2.8,"
            "equalizer=f=3600:t=q:w=1.4:g=2.2,"
            "acompressor=threshold=0.15:ratio=3.2:attack=5:release=50,"
            "volume=1.35"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_audio_path),
            "-af", filter_str,
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output_audio_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception:
            if raw_audio_path != output_audio_path:
                import shutil
                shutil.copy(raw_audio_path, output_audio_path)

    # ==========================================================
    # ১. Sarvam AI Engine (Hyper-Realistic Hindi & Bengali)
    # ==========================================================
    @classmethod
    def _generate_sarvam_voiceover(
        cls,
        text: str,
        language_code: str,
        output_path: Path,
        speaker: str = "meera"
    ) -> Dict[str, Any]:
        api_key = os.getenv("SARVAM_API_KEY")
        if not api_key:
            raise ValueError("SARVAM_API_KEY environment variable is missing!")

        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": 1.05,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Sarvam AI Error: {response.text}")

        audio_base64 = response.json()["audios"][0]
        audio_bytes = base64.b64decode(audio_base64)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_audio = output_path.parent / f"raw_{output_path.stem}.wav"
        with open(raw_audio, "wb") as f:
            f.write(audio_bytes)

        cls._apply_studio_mastering(raw_audio, output_path)
        try:
            raw_audio.unlink(missing_ok=True)
        except Exception:
            pass

        duration = 0.0
        try:
            with sf.SoundFile(str(output_path)) as sound_file:
                duration = len(sound_file) / sound_file.samplerate
        except Exception:
            duration = max(len(text.split()) * 0.35, 1.0)

        raw_words = text.strip().split()
        words = []
        if raw_words:
            time_per_word = duration / max(len(raw_words), 1)
            for idx, w in enumerate(raw_words):
                start = idx * time_per_word
                words.append({
                    "word": w,
                    "start": round(start, 3),
                    "end": round(start + time_per_word, 3),
                    "duration": round(time_per_word, 3)
                })

        return {
            "audio_path": str(output_path),
            "duration": round(duration, 3),
            "words": words
        }

    # ==========================================================
    # ২. F5-TTS Engine (Local Zero-Shot Cloning)
    # ==========================================================
    @classmethod
    def _generate_f5_voiceover(
        cls,
        text: str,
        output_path: Path,
        ref_audio_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        from f5_tts.api import F5TTS
        import torchaudio

        tts = F5TTS()
        if not ref_audio_path or not Path(ref_audio_path).exists():
            ref_audio_path = settings.STORAGE_DIR / "ref_audio" / "sample.wav"

        raw_wav = output_path.parent / f"raw_{output_path.stem}.wav"
        wav, sr, _ = tts.infer(
            ref_file=str(ref_audio_path) if Path(ref_audio_path).exists() else "",
            ref_text="",
            gen_text=text
        )
        torchaudio.save(str(raw_wav), wav, sr)

        cls._apply_studio_mastering(raw_wav, output_path)
        try:
            raw_wav.unlink(missing_ok=True)
        except Exception:
            pass

        duration = 0.0
        with sf.SoundFile(str(output_path)) as sound_file:
            duration = len(sound_file) / sound_file.samplerate

        raw_words = text.strip().split()
        words = []
        if raw_words:
            time_per_word = duration / max(len(raw_words), 1)
            for idx, w in enumerate(raw_words):
                start = idx * time_per_word
                words.append({
                    "word": w,
                    "start": round(start, 3),
                    "end": round(start + time_per_word, 3),
                    "duration": round(time_per_word, 3)
                })

        return {
            "audio_path": str(output_path),
            "duration": round(duration, 3),
            "words": words
        }

    # ==========================================================
    # ৩. Kokoro Voiceover
    # ==========================================================
    @classmethod
    def _generate_kokoro_voiceover(
        cls,
        text: str,
        voice_id: str,
        rate: str,
        output_path: Path
    ) -> Dict[str, Any]:
        kokoro_voice = voice_id.replace("kokoro:", "").strip()
        speed = 1.1 if rate == "+10%" else (1.2 if rate == "+20%" else 1.0)
        
        kokoro = cls._get_kokoro()
        samples, sample_rate = kokoro.create(text, voice=kokoro_voice, speed=speed, lang="en-us")
        
        temp_wav = output_path.parent / f"temp_{output_path.stem}.wav"
        sf.write(str(temp_wav), samples, sample_rate)
        
        cls._apply_studio_mastering(temp_wav, output_path)
        try:
            temp_wav.unlink(missing_ok=True)
        except Exception:
            pass

        duration = len(samples) / sample_rate
        raw_words = text.strip().split()
        words = []
        if raw_words:
            time_per_word = duration / max(len(raw_words), 1)
            for idx, w in enumerate(raw_words):
                start = idx * time_per_word
                words.append({
                    "word": w,
                    "start": round(start, 3),
                    "end": round(start + time_per_word, 3),
                    "duration": round(time_per_word, 3)
                })

        return {
            "audio_path": str(output_path),
            "duration": round(duration, 3),
            "words": words
        }

    # ==========================================================
    # ৪. Edge-TTS (Fallback Engine)
    # ==========================================================
    @staticmethod
    async def generate_edge_voiceover_async(
        text: str,
        voice: str = "hi-IN-MadhurNeural",
        rate: str = "+5%",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        words: List[Dict[str, Any]] = []
        audio_data = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                offset_sec = chunk["offset"] / 10000000.0
                duration_sec = chunk["duration"] / 10000000.0
                word_text = chunk["text"]
                words.append({
                    "word": word_text,
                    "start": round(offset_sec, 3),
                    "end": round(offset_sec + duration_sec, 3),
                    "duration": round(duration_sec, 3)
                })

        if not audio_data:
            raise RuntimeError("Failed to generate TTS audio data.")

        if output_path is None:
            raise ValueError("output_path is required")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_mp3 = output_path.parent / f"raw_{output_path.name}"
        with open(raw_mp3, "wb") as f:
            f.write(audio_data)

        TTSService._apply_studio_mastering(raw_mp3, output_path)
        try:
            raw_mp3.unlink(missing_ok=True)
        except Exception:
            pass

        duration = 0.0
        try:
            with sf.SoundFile(str(output_path)) as sound_file:
                duration = len(sound_file) / sound_file.samplerate
        except Exception:
            if words:
                duration = words[-1]["end"] + 0.3

        if not words:
            raw_words = text.strip().split()
            if raw_words:
                time_per_word = duration / max(len(raw_words), 1)
                for idx, w in enumerate(raw_words):
                    start = idx * time_per_word
                    words.append({
                        "word": w,
                        "start": round(start, 3),
                        "end": round(start + time_per_word, 3),
                        "duration": round(time_per_word, 3)
                    })

        return {
            "audio_path": str(output_path),
            "duration": round(duration, 3),
            "words": words
        }

    # ==========================================================
    # ৫. Main Unified Orchestrator
    # ==========================================================
    @classmethod
    def generate_voiceover(
        cls,
        text: str,
        voice: str = "hi-IN-MadhurNeural",
        rate: str = "+5%",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        if output_path is None:
            raise ValueError("output_path is required")

        # স্ক্রিপ্ট ডিটেকশন (হিন্দি ও বাংলা বর্ণমালা)
        has_hindi = bool(re.search(r"[\u0900-\u097F]", text))
        has_bengali = bool(re.search(r"[\u0980-\u09FF]", text))

        # ১. Sarvam AI মোড (যদি SARVAM_API_KEY থাকে অথবা voice-এ 'sarvam' উল্লেখ থাকে)
        if (os.getenv("SARVAM_API_KEY") and (has_hindi or has_bengali)) or "sarvam" in voice.lower():
            target_lang = "bn-IN" if has_bengali else "hi-IN"
            speaker = "meera" if "female" in voice.lower() else "amol"
            try:
                return cls._generate_sarvam_voiceover(text, target_lang, output_path, speaker=speaker)
            except Exception as e:
                print(f"Sarvam AI fallback due to: {e}")

        # ২. F5-TTS মোড
        if "f5" in voice.lower():
            try:
                return cls._generate_f5_voiceover(text, output_path)
            except Exception as e:
                print(f"F5-TTS fallback due to: {e}")

        # ৩. Kokoro (English) মোড
        if voice.startswith("kokoro:"):
            if has_hindi:
                voice = "hi-IN-MadhurNeural"
                return asyncio.run(cls.generate_edge_voiceover_async(text, voice, rate, output_path))
            elif has_bengali:
                voice = "bn-IN-TanishaaNeural"
                return asyncio.run(cls.generate_edge_voiceover_async(text, voice, rate, output_path))
            else:
                try:
                    return cls._generate_kokoro_voiceover(text, voice, rate, output_path)
                except Exception:
                    fallback_voice = "en-US-AndrewMultilingualNeural"
                    return asyncio.run(cls.generate_edge_voiceover_async(text, fallback_voice, rate, output_path))

        # ৪. ডিফল্ট Edge-TTS ফলব্যাক
        return asyncio.run(cls.generate_edge_voiceover_async(text, voice, rate, output_path))
