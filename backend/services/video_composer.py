import subprocess
from pathlib import Path
from typing import List, Optional

class VideoComposer:
    @staticmethod
    def build_scene_clip(raw_video: Path, output_clip: Path, duration: float) -> Path:
        output_clip.parent.mkdir(parents=True, exist_ok=True)
        vf_filter = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1,"
            "fps=30,"
            "eq=contrast=1.12:brightness=-0.02:saturation=1.18"
        )
        cmd = [
            "ffmpeg", "-y",
            "-threads", "0",
            "-stream_loop", "-1",
            "-i", str(raw_video),
            "-t", f"{duration:.2f}",
            "-vf", vf_filter,
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            str(output_clip)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_clip

    @classmethod
    def render_final_video(
        cls,
        scene_clips: List[Path],
        voiceover_audio: Path,
        ass_subtitles: Path,
        bgm_audio: Optional[Path],
        output_video: Path,
        bgm_volume: float = 0.15,
        total_duration: Optional[float] = None
    ) -> Path:
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        concat_file = output_video.parent / ("concat_" + output_video.stem + ".txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                clean_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        clean_ass = str(ass_subtitles.resolve()).replace("\\", "/").replace(":", "\\:")
        video_filter = f"subtitles='{clean_ass}'"

        if bgm_audio and bgm_audio.exists():
            # Smart music trimming starting at 5s (where beat drops) with smooth fade-in and 1.5s fade-out
            fade_start = max((total_duration or 60.0) - 1.5, 1.0)
            bgm_filter = f"[2:a]atrim=start=5,asetpts=PTS-STARTPTS,volume={bgm_volume},afade=t=in:st=0:d=0.5,afade=t=out:st={fade_start:.2f}:d=1.5[bgm]"
            
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(voiceover_audio),
                "-stream_loop", "-1", "-i", str(bgm_audio),
                "-filter_complex",
                f"[0:v]{video_filter}[v];{bgm_filter};[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "faster",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                str(output_video)
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-threads", "0",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(voiceover_audio),
                "-vf", video_filter,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-preset", "faster",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                str(output_video)
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg render error:\n{res.stderr}")

        if concat_file.exists():
            concat_file.unlink()

        return output_video
