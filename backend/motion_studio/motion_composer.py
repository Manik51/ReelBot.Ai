import subprocess
from pathlib import Path
from typing import List, Optional

from backend.motion_studio.sfx_manager import SfxManager

class MotionComposer:
    """
    Composes animated GIF/MP4 loops into 1080x1920 9:16 vertical short videos
    using dual-layer blurred background framing, SFX mixing, auto-ducked music,
    and Alex Hormozi word-pop subtitles.
    """

    @staticmethod
    def build_motion_scene_clip(raw_media: Path, output_clip: Path, duration: float, scene_id: int = 0) -> Path:
        """
        Takes an animated MP4 or GIF loop and builds a vertical 1080x1920 clip
        with high-definition dual-layer styling:
        - Background: Zoomed, frosted-glass blurred to fill 1080x1920 with deep dark vignette.
        - Foreground: Crisp, Lanczos-upscaled centered loop with bright contrast and vibrance boost.
        """
        output_clip.parent.mkdir(parents=True, exist_ok=True)

        # High-definition dual-layer filtergraph
        # [0:v] split into [bg] and [fg]
        # [bg] scaled with bicubic, boxblur=24:4, darkened vignette
        # [fg] scaled with lanczos to fit within 980x1100, centered
        filter_complex = (
            "[0:v]split=2[v_bg][v_fg];"
            "[v_bg]scale=1080:1920:force_original_aspect_ratio=increase:flags=bicubic,crop=1080:1920,"
            "boxblur=24:4,eq=brightness=-0.1:contrast=1.15:saturation=1.25,vignette=PI/3.5[bg_layer];"
            "[v_fg]scale=980:1100:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1,"
            "eq=contrast=1.12:saturation=1.2:brightness=0.02[fg_layer];"
            "[bg_layer][fg_layer]overlay=(W-w)/2:(H-h)/2:format=auto,fps=30,format=yuv420p[final_v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-stream_loop", "-1",
            "-i", str(raw_media),
            "-t", f"{duration:.2f}",
            "-filter_complex", filter_complex,
            "-map", "[final_v]",
            "-an",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(output_clip)
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_clip

    @classmethod
    def render_final_motion_video(
        cls,
        scene_clips: List[Path],
        voiceover_audio: Path,
        ass_subtitles: Path,
        bgm_audio: Optional[Path],
        output_video: Path,
        scene_durations: List[float],
        bgm_volume: float = 0.15,
        sfx_intensity: str = "cinematic",
        total_duration: Optional[float] = None
    ) -> Path:
        """
        Concatenates motion scene clips, mixes audio with SFX & ducked BGM,
        and burns Alex Hormozi word-pop ASS captions.
        """
        output_video.parent.mkdir(parents=True, exist_ok=True)
        work_dir = output_video.parent

        # 1. Prepare video concatenation list
        concat_file = work_dir / f"concat_motion_{output_video.stem}.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                clean_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        # 2. Mix multi-track audio (Voiceover + Ducked BGM + SFX Whooshes & Hits)
        mixed_audio_path = work_dir / f"mixed_audio_{output_video.stem}.mp3"
        mix_cmd = SfxManager.build_audio_mix_command(
            voiceover_path=voiceover_audio,
            bgm_path=bgm_audio,
            scene_durations=scene_durations,
            output_audio_path=mixed_audio_path,
            bgm_volume=bgm_volume,
            sfx_intensity=sfx_intensity,
            total_duration=total_duration
        )

        try:
            subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"SFX audio mixing fallback to voiceover: {e}")
            import shutil
            shutil.copy(voiceover_audio, mixed_audio_path)

        # 3. Final assemble: concat video + mixed audio + burn subtitles
        clean_ass = str(ass_subtitles.resolve()).replace("\\", "/").replace(":", "\\:")
        video_filter = f"subtitles='{clean_ass}'"

        render_cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-i", str(mixed_audio_path),
            "-vf", video_filter,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_video)
        ]

        if total_duration and total_duration > 1.0:
            render_cmd.insert(-1, "-t")
            render_cmd.insert(-1, f"{total_duration:.2f}")

        subprocess.run(render_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Clean up temporary concat file
        try:
            concat_file.unlink(missing_ok=True)
            mixed_audio_path.unlink(missing_ok=True)
        except Exception:
            pass

        return output_video
