import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import settings

class SfxManager:
    """
    Manages sound effects (Whoosh, Bass Hit, Glitch, Heartbeat)
    and constructs FFmpeg audio filter graphs for auto-ducked BGM + SFX mixing.
    """

    SFX_DIR = settings.BASE_DIR / "backend" / "assets" / "sfx"

    @classmethod
    def get_sfx_path(cls, name: str) -> Optional[Path]:
        p = cls.SFX_DIR / f"{name}.mp3"
        return p if p.exists() else None

    @classmethod
    def build_audio_mix_command(
        cls,
        voiceover_path: Path,
        bgm_path: Optional[Path],
        scene_durations: List[float],
        output_audio_path: Path,
        bgm_volume: float = 0.15,
        sfx_intensity: str = "cinematic",
        total_duration: Optional[float] = None
    ) -> List[str]:
        inputs = ["-i", str(voiceover_path)]
        next_input_idx = 1
        filter_complex_parts = []

        # 1. Voiceover vocal
        filter_complex_parts.append("[0:a]volume=1.0,aformat=channel_layouts=stereo:sample_rates=44100[vocal]")

        # 2. BGM with auto-ducking
        has_bgm = False
        if bgm_path and bgm_path.exists():
            bgm_idx = next_input_idx
            next_input_idx += 1
            has_bgm = True
            inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
            fade_out_time = (total_duration - 1.5) if total_duration and total_duration > 3.0 else 25.0
            filter_complex_parts.append(
                f"[{bgm_idx}:a]volume={bgm_volume:.2f},"
                f"afade=t=in:ss=0:d=1.0,"
                f"afade=t=out:st={fade_out_time:.1f}:d=1.5,"
                f"aformat=channel_layouts=stereo:sample_rates=44100[bgm]"
            )

        # 3. Sound Effects (Whooshes at cuts)
        sfx_labels = []
        whoosh_file = cls.get_sfx_path("whoosh")
        bass_file = cls.get_sfx_path("bass_thud")

        if sfx_intensity != "none" and whoosh_file and whoosh_file.exists():
            current_time = 0.0
            for idx, dur in enumerate(scene_durations):
                if idx > 0:
                    delay_ms = int(round(current_time * 1000))
                    w_idx = next_input_idx
                    next_input_idx += 1
                    inputs.extend(["-i", str(whoosh_file)])
                    sfx_label = f"sfx_w_{idx}"
                    filter_complex_parts.append(
                        f"[{w_idx}:a]volume=0.35,adelay={delay_ms}|{delay_ms},aformat=channel_layouts=stereo:sample_rates=44100[{sfx_label}]"
                    )
                    sfx_labels.append(f"[{sfx_label}]")
                current_time += dur

        # 4. Bass Thud at 0s hook
        if sfx_intensity == "cinematic" and bass_file and bass_file.exists():
            b_idx = next_input_idx
            next_input_idx += 1
            inputs.extend(["-i", str(bass_file)])
            filter_complex_parts.append(
                f"[{b_idx}:a]volume=0.45,adelay=100|100,aformat=channel_layouts=stereo:sample_rates=44100[sfx_bass]"
            )
            sfx_labels.append("[sfx_bass]")

        # 5. Assemble Mix
        streams_to_mix = ["[vocal]"]
        if has_bgm:
            streams_to_mix.append("[bgm]")
        streams_to_mix.extend(sfx_labels)

        mix_filter = (
            f"{''.join(streams_to_mix)}amix=inputs={len(streams_to_mix)}:duration=first:dropout_transition=2,"
            f"alimiter=limit=0.95:level=true[final_audio]"
        )
        filter_complex_parts.append(mix_filter)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_complex_parts),
            "-map", "[final_audio]",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output_audio_path)
        ]
        return cmd
