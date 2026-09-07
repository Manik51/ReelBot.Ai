import os
import math
import wave
import struct
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import settings

class DocuSfxService:
    """
    Independent SFX & Audio Mixing Engine for Documentary & Business Analysis.
    Provides procedural generation for missing SFX and constructs multi-track FFmpeg audio graphs.
    """

    DOCU_SFX_DIR = settings.BASE_DIR / "backend" / "assets" / "sfx" / "docu"

    @classmethod
    def ensure_sfx_assets(cls):
        """Ensures all essential documentary SFX files exist, generating procedural high-fidelity WAVs if missing."""
        cls.DOCU_SFX_DIR.mkdir(parents=True, exist_ok=True)
        
        generators = {
            "paper_slam.wav": cls._synth_paper_slam,
            "camera_shutter.wav": cls._synth_camera_shutter,
            "cash_kaching.wav": cls._synth_cash_kaching,
            "bass_drop.wav": cls._synth_bass_drop,
            "whoosh_cinematic.wav": cls._synth_whoosh,
            "typewriter_hit.wav": cls._synth_typewriter,
        }

        for filename, synth_func in generators.items():
            dest = cls.DOCU_SFX_DIR / filename
            if not dest.exists() or dest.stat().st_size < 100:
                try:
                    synth_func(dest)
                except Exception as e:
                    print(f"[DocuSfx] Warning: could not synthesize {filename}: {e}")

    @classmethod
    def get_sfx_path(cls, cue_name: str) -> Optional[Path]:
        cls.ensure_sfx_assets()
        cue_map = {
            "slam": "paper_slam.wav",
            "paper_slam": "paper_slam.wav",
            "shutter": "camera_shutter.wav",
            "camera": "camera_shutter.wav",
            "camera_shutter": "camera_shutter.wav",
            "cash": "cash_kaching.wav",
            "kaching": "cash_kaching.wav",
            "money": "cash_kaching.wav",
            "bass": "bass_drop.wav",
            "bass_drop": "bass_drop.wav",
            "impact": "bass_drop.wav",
            "whoosh": "whoosh_cinematic.wav",
            "typewriter": "typewriter_hit.wav",
        }
        fname = cue_map.get(cue_name.lower())
        if fname:
            p = cls.DOCU_SFX_DIR / fname
            if p.exists():
                return p
        # Check standard sfx dir fallback
        std_p = settings.BASE_DIR / "backend" / "assets" / "sfx" / f"{cue_name}.mp3"
        return std_p if std_p.exists() else None

    # ── PROCEDURAL SOUND SYNTHESIZERS ──────────────────────────────────────
    @staticmethod
    def _write_wav(path: Path, samples: np.ndarray, sample_rate: int = 44100):
        samples = np.clip(samples, -1.0, 1.0)
        int_samples = (samples * 32767).astype(np.int16)
        with wave.open(str(path), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int_samples.tobytes())

    @classmethod
    def _synth_paper_slam(cls, path: Path):
        sr = 44100
        dur = 0.6
        t = np.linspace(0, dur, int(sr * dur), False)
        # Low frequency impact thump (80Hz down to 40Hz)
        thump = np.sin(2 * np.pi * (80 - 40 * t / dur) * t) * np.exp(-12 * t)
        # Paper flutter/friction noise burst
        noise = np.random.uniform(-1, 1, len(t)) * np.exp(-22 * t)
        samples = 0.7 * thump + 0.4 * noise
        cls._write_wav(path, samples, sr)

    @classmethod
    def _synth_camera_shutter(cls, path: Path):
        sr = 44100
        dur = 0.35
        t = np.linspace(0, dur, int(sr * dur), False)
        samples = np.zeros_like(t)
        # Mirror click at t=0
        click1 = np.random.uniform(-1, 1, len(t)) * np.exp(-70 * np.maximum(0, t - 0.01))
        # Curtain snap at t=0.06
        click2 = np.random.uniform(-1, 1, len(t)) * np.exp(-50 * np.maximum(0, t - 0.07))
        # Metallic spring ring
        ring = np.sin(2 * np.pi * 1800 * t) * np.exp(-20 * np.maximum(0, t - 0.07))
        samples = 0.6 * click1 + 0.7 * click2 + 0.2 * ring
        cls._write_wav(path, samples, sr)

    @classmethod
    def _synth_cash_kaching(cls, path: Path):
        sr = 44100
        dur = 0.8
        t = np.linspace(0, dur, int(sr * dur), False)
        # Bell frequencies: 2400Hz and 3600Hz chime
        bell1 = np.sin(2 * np.pi * 2380 * t) * np.exp(-4.5 * t)
        bell2 = np.sin(2 * np.pi * 3560 * t) * np.exp(-5.5 * t)
        bell3 = np.sin(2 * np.pi * 4800 * t) * np.exp(-7.0 * t)
        # Metallic latch sound at start
        latch = np.random.uniform(-1, 1, len(t)) * np.exp(-80 * t)
        samples = 0.45 * bell1 + 0.35 * bell2 + 0.2 * bell3 + 0.3 * latch
        cls._write_wav(path, samples, sr)

    @classmethod
    def _synth_bass_drop(cls, path: Path):
        sr = 44100
        dur = 1.2
        t = np.linspace(0, dur, int(sr * dur), False)
        # Deep pitch drop 90Hz -> 30Hz
        freq = 90.0 - 55.0 * (t / dur)
        sub = np.sin(2 * np.pi * freq * t) * np.exp(-3.0 * t)
        # Warm saturation
        sub = np.tanh(1.5 * sub)
        cls._write_wav(path, 0.9 * sub, sr)

    @classmethod
    def _synth_whoosh(cls, path: Path):
        sr = 44100
        dur = 0.5
        t = np.linspace(0, dur, int(sr * dur), False)
        envelope = np.sin(np.pi * t / dur) ** 2
        noise = np.random.uniform(-1, 1, len(t))
        # Pitch modulated noise sweep
        carrier = np.sin(2 * np.pi * (250 + 400 * np.sin(np.pi * t / dur)) * t)
        samples = noise * envelope * 0.5 + carrier * envelope * 0.3
        cls._write_wav(path, samples, sr)

    @classmethod
    def _synth_typewriter(cls, path: Path):
        sr = 44100
        dur = 0.2
        t = np.linspace(0, dur, int(sr * dur), False)
        noise = np.random.uniform(-1, 1, len(t)) * np.exp(-60 * t)
        ring = np.sin(2 * np.pi * 2100 * t) * np.exp(-35 * t)
        samples = 0.7 * noise + 0.3 * ring
        cls._write_wav(path, samples, sr)

    # ── FFmpeg MULTI-TRACK AUDIO MIXER ─────────────────────────────────────
    @classmethod
    def build_audio_mix_command(
        cls,
        voiceover_path: Path,
        bgm_path: Optional[Path],
        beat_durations: List[float],
        beat_sfx_cues: List[str],
        output_audio_path: Path,
        bgm_volume: float = 0.15,
        sfx_volume: float = 0.60,
        sfx_enabled: bool = True,
        total_duration: Optional[float] = None
    ) -> List[str]:
        cls.ensure_sfx_assets()
        inputs = ["-i", str(voiceover_path)]
        filter_complex_parts = []

        # 1. Vocal Master
        filter_complex_parts.append("[0:a]volume=1.0,aformat=channel_layouts=stereo:sample_rates=44100[vocal]")

        # 2. Documentary BGM with auto-ducking
        has_bgm = False
        next_idx = 1
        if bgm_path and bgm_path.exists():
            bgm_idx = next_idx
            next_idx += 1
            has_bgm = True
            inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
            fade_out = (total_duration - 2.0) if total_duration and total_duration > 4.0 else 55.0
            filter_complex_parts.append(
                f"[{bgm_idx}:a]volume={bgm_volume:.2f},"
                f"afade=t=in:ss=0:d=1.5,"
                f"afade=t=out:st={fade_out:.1f}:d=2.0,"
                f"aformat=channel_layouts=stereo:sample_rates=44100[bgm]"
            )

        # 3. Beat SFX Cues
        sfx_labels = []
        if sfx_enabled and sfx_volume > 0.01:
            current_time = 0.0
            for idx, (dur, cue) in enumerate(zip(beat_durations, beat_sfx_cues)):
                sfx_file = cls.get_sfx_path(cue) if cue else None
                if sfx_file and sfx_file.exists():
                    sfx_idx = next_idx
                    next_idx += 1
                    inputs.extend(["-i", str(sfx_file)])
                    delay_ms = int(current_time * 1000)
                    out_lbl = f"sfx_{idx}"
                    filter_complex_parts.append(
                        f"[{sfx_idx}:a]volume={sfx_volume:.2f},adelay={delay_ms}|{delay_ms},"
                        f"aformat=channel_layouts=stereo:sample_rates=44100[{out_lbl}]"
                    )
                    sfx_labels.append(f"[{out_lbl}]")
                current_time += dur

        # 4. Master Amix
        mix_inputs = ["[vocal]"]
        if has_bgm:
            mix_inputs.append("[bgm]")
        mix_inputs.extend(sfx_labels)

        num_tracks = len(mix_inputs)
        if num_tracks == 1:
            filter_complex_parts.append("[vocal]aformat=channel_layouts=stereo:sample_rates=44100[outa]")
        else:
            joined_inputs = "".join(mix_inputs)
            filter_complex_parts.append(
                f"{joined_inputs}amix=inputs={num_tracks}:duration=first:dropout_transition=2,"
                f"volume={1.0 + 0.15 * min(num_tracks - 1, 3):.2f},"
                f"aformat=channel_layouts=stereo:sample_rates=44100[outa]"
            )

        cmd = ["ffmpeg", "-y"]
        cmd.extend(inputs)
        cmd.extend(["-filter_complex", ";".join(filter_complex_parts), "-map", "[outa]"])
        if total_duration:
            cmd.extend(["-t", f"{total_duration:.2f}"])
        if str(output_audio_path).lower().endswith(".wav"):
            cmd.extend(["-c:a", "pcm_s16le", str(output_audio_path)])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", "192k", str(output_audio_path)])
        return cmd
