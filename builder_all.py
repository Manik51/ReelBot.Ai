import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def write_file(rel_path: str, content: str):
    target = BASE_DIR / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Created: {rel_path}")

# ==============================================================================
# 1. backend/config.py
# ==============================================================================
config_py = """import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Settings:
    BASE_DIR = BASE_DIR
    STORAGE_DIR = BASE_DIR / 'storage'
    TEMP_DIR = BASE_DIR / 'storage' / 'temp'
    OUTPUTS_DIR = BASE_DIR / 'storage' / 'outputs'
    ASSETS_DIR = BASE_DIR / 'backend' / 'assets'
    FONTS_DIR = ASSETS_DIR / 'fonts'
    BGM_DIR = ASSETS_DIR / 'bgm'
    SFX_DIR = ASSETS_DIR / 'sfx'

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
    PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY', '')

    # Video composition defaults
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    FPS = 30
    DEFAULT_BGM_VOLUME = 0.15

    # Supported Voices
    VOICE_PRESETS = [
        {'id': 'en-US-ChristopherNeural', 'name': 'Christopher (Male - Deep & Energetic)', 'gender': 'Male', 'lang': 'English (US)'},
        {'id': 'en-US-GuyNeural', 'name': 'Guy (Male - Storyteller / Casual)', 'gender': 'Male', 'lang': 'English (US)'},
        {'id': 'en-US-JennyNeural', 'name': 'Jenny (Female - Clear & Engaging)', 'gender': 'Female', 'lang': 'English (US)'},
        {'id': 'en-US-AriaNeural', 'name': 'Aria (Female - Dynamic & Crisp)', 'gender': 'Female', 'lang': 'English (US)'},
        {'id': 'en-GB-RyanNeural', 'name': 'Ryan (British Male - Sophisticated)', 'gender': 'Male', 'lang': 'English (UK)'},
        {'id': 'en-GB-SoniaNeural', 'name': 'Sonia (British Female - Elegant)', 'gender': 'Female', 'lang': 'English (UK)'},
        {'id': 'bn-BD-PradeepNeural', 'name': 'Pradeep (Bangla Male - Strong & Clear)', 'gender': 'Male', 'lang': 'Bengali (BD)'},
        {'id': 'bn-BD-NabanitaNeural', 'name': 'Nabanita (Bangla Female - Sweet & Expressive)', 'gender': 'Female', 'lang': 'Bengali (BD)'},
        {'id': 'bn-IN-BashkarNeural', 'name': 'Bashkar (Bangla India Male - Natural)', 'gender': 'Male', 'lang': 'Bengali (IN)'},
        {'id': 'bn-IN-TanishaaNeural', 'name': 'Tanishaa (Bangla India Female - Smooth)', 'gender': 'Female', 'lang': 'Bengali (IN)'},
        {'id': 'hi-IN-MadhurNeural', 'name': 'Madhur (Hindi Male - Deep)', 'gender': 'Male', 'lang': 'Hindi (IN)'},
        {'id': 'hi-IN-SwaraNeural', 'name': 'Swara (Hindi Female - Energetic)', 'gender': 'Female', 'lang': 'Hindi (IN)'},
    ]

    # Subtitle Styles
    SUBTITLE_STYLES = [
        {
            'id': 'hormozi_yellow',
            'name': 'Hormozi Viral Yellow',
            'primary_color': '&H00FFFFFF',      # Pure White in ASS BGR
            'highlight_color': '&H0000E5FF',    # Vibrant Yellow (&H00BBGGRR)
            'outline_color': '&H00000000',      # Black Outline
            'shadow_color': '&H80000000',       # Dark Shadow
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'hormozi_green',
            'name': 'Hormozi Neon Green',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H0066FF00',    # Neon Green
            'outline_color': '&H00000000',
            'shadow_color': '&H80000000',
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'cyber_cyan',
            'name': 'Cyber Neon Cyan',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H00FFFF00',    # Cyan
            'outline_color': '&H00000000',
            'shadow_color': '&H80000000',
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'bold_white',
            'name': 'Clean Bold White',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H00FFFFFF',
            'outline_color': '&H00000000',
            'shadow_color': '&H99000000',
            'font_size': 72,
            'font_name': 'Arial Black',
            'bold': 1,
            'max_words_per_line': 4
        }
    ]

settings = Settings()
"""
write_file("backend/config.py", config_py)

# ==============================================================================
# 2. backend/services/gemini_service.py
# ==============================================================================
gemini_py = """import json
import re
import requests
from typing import Dict, Any, Optional

class GeminiService:
    @staticmethod
    def generate_script(
        api_key: str,
        topic: str,
        language: str = "English",
        tone: str = "High Energy / Viral",
        target_duration_sec: int = 60
    ) -> Dict[str, Any]:
        if not api_key:
            raise ValueError("Gemini API key is required. Please set it in Settings.")

        target_words = int(target_duration_sec * 2.3)

        system_instruction = (
            "You are an elite viral short-form video creator and scriptwriter for YouTube Shorts, TikTok, and Instagram Reels.\\n"
            f"Your mission is to generate an ultra-engaging, high-retention {target_duration_sec}-second video script.\\n\\n"
            "RETENTION & PACING RULES:\\n"
            "1. 0:00-0:03 (THE HOOK): Shocking, curiosity-inducing hook that stops the user from scrolling.\\n"
            "2. 0:03-0:15 (THE SETUP): Fast-paced, punchy delivery highlighting the problem or mystery.\\n"
            "3. 0:15-0:45 (CORE VALUE/STORY): Scene-by-scene progression. Keep sentences short, conversational, and energetic.\\n"
            "4. 0:45-0:55 (THE CLIMAX/TWIST): The most impactful revelation or mind-expanding conclusion.\\n"
            "5. 0:55-1:00 (THE LOOP/CTA): A seamless transition back to the hook or strong call-to-action.\\n\\n"
            "STOCK FOOTAGE KEYWORDS:\\n"
            "- For EVERY scene, provide 3 to 4 specific, cinematic search keywords in ENGLISH (e.g. ['luxury sports car night speed', 'cyberpunk neon city', 'money cash counting', 'businessman thinking']).\\n"
            "- Keywords MUST ALWAYS be in English so Pexels & Pixabay can easily find matching HD vertical stock footage.\\n\\n"
            "OUTPUT JSON ONLY (no markdown code blocks, no backticks, no extra commentary):\\n"
            "{\\n"
            "  \\\"title\\\": \\\"Catchy 3-5 word Title\\\",\\n"
            "  \\\"hook\\\": \\\"The 3-second opening hook sentence\\\",\\n"
            f"  \\\"target_duration_sec\\\": {target_duration_sec},\\n"
            "  \\\"total_scenes\\\": 6,\\n"
            "  \\\"scenes\\\": [\\n"
            "    {\\n"
            "      \\\"scene_id\\\": 1,\\n"
            "      \\\"narration\\\": \\\"Spoken voiceover text for this scene.\\\",\\n"
            "      \\\"keywords\\\": [\\\"keyword 1\\\", \\\"keyword 2\\\", \\\"keyword 3\\\"],\\n"
            "      \\\"suggested_emoji\\\": \\\"🔥\\\",\\n"
            "      \\\"estimated_seconds\\\": 5\\n"
            "    }\\n"
            "  ]\\n"
            "}"
        )

        user_prompt = (
            f"Generate a viral {target_duration_sec}-second short video script.\\n"
            f"Topic: {topic}\\n"
            f"Language for narration: {language}\\n"
            f"Tone: {tone}\\n"
            f"Target word count: ~{target_words} words across 6 to 8 fast-paced scenes.\\n"
            "Remember: Stock footage keywords must be in English."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": system_instruction + "\\n\\n" + user_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "responseMimeType": "application/json"
            }
        }

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=45)
            if response.status_code != 200:
                url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                response = requests.post(url_fallback, json=payload, headers=headers, timeout=45)
                if response.status_code != 200:
                    raise RuntimeError(f"Gemini API Error ({response.status_code}): {response.text}")

            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            script_data = json.loads(raw_text.strip())
            return script_data
        except Exception as e:
            raise RuntimeError(f"Failed to generate script with Gemini: {str(e)}")
"""
write_file("backend/services/gemini_service.py", gemini_py)

# ==============================================================================
# 3. backend/services/tts_service.py
# ==============================================================================
tts_py = """import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import edge_tts
import soundfile as sf

class TTSService:
    @staticmethod
    async def generate_voiceover_async(
        text: str,
        voice: str = "en-US-ChristopherNeural",
        rate: str = "+10%",
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
        with open(output_path, "wb") as f:
            f.write(audio_data)

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

    @classmethod
    def generate_voiceover(
        cls,
        text: str,
        voice: str = "en-US-ChristopherNeural",
        rate: str = "+10%",
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        return asyncio.run(cls.generate_voiceover_async(text, voice, rate, output_path))
"""
write_file("backend/services/tts_service.py", tts_py)

# ==============================================================================
# 4. backend/services/media_service.py
# ==============================================================================
media_py = """import os
import random
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class MediaService:
    @staticmethod
    def search_pexels_video(api_key: str, query: str) -> Optional[str]:
        if not api_key:
            return None
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": api_key}
        params = {
            "query": query,
            "orientation": "portrait",
            "per_page": 8,
            "size": "medium"
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=12)
            if r.status_code == 200:
                data = r.json()
                videos = data.get("videos", [])
                if videos:
                    chosen = random.choice(videos)
                    video_files = chosen.get("video_files", [])
                    portrait_files = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
                    if portrait_files:
                        portrait_files.sort(key=lambda x: x.get("height", 0), reverse=True)
                        return portrait_files[0].get("link")
                    elif video_files:
                        video_files.sort(key=lambda x: x.get("height", 0), reverse=True)
                        return video_files[0].get("link")
        except Exception as e:
            print(f"Pexels search error for '{query}': {e}")
        return None

    @staticmethod
    def search_pixabay_video(api_key: str, query: str) -> Optional[str]:
        if not api_key:
            return None
        url = "https://pixabay.com/api/videos/"
        params = {
            "key": api_key,
            "q": query,
            "video_type": "film",
            "per_page": 8
        }
        try:
            r = requests.get(url, params=params, timeout=12)
            if r.status_code == 200:
                data = r.json()
                hits = data.get("hits", [])
                if hits:
                    chosen = random.choice(hits)
                    videos = chosen.get("videos", {})
                    for q in ["large", "medium", "small"]:
                        if q in videos and videos[q].get("url"):
                            return videos[q]["url"]
        except Exception as e:
            print(f"Pixabay search error for '{query}': {e}")
        return None

    @classmethod
    def create_fallback_clip(cls, output_path: Path, duration: float, scene_id: int) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gradients = [
            ("0x0d1117", "0x161b22"),
            ("0x1a0b2e", "0x11001c"),
            ("0x00172d", "0x00264d"),
            ("0x1f1105", "0x381e05"),
            ("0x0a192f", "0x020c1b")
        ]
        c1, c2 = gradients[scene_id % len(gradients)]
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={c1}:s=1080x1920:d={duration:.2f}:r=30",
            "-vf", f"drawbox=y=ih/2:color={c2}@0.4:width=iw:height=ih/2:t=fill,format=yuv420p",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path

    @classmethod
    def fetch_scene_media(
        cls,
        keywords: List[str],
        pexels_key: str,
        pixabay_key: str,
        dest_path: Path,
        duration: float,
        scene_id: int
    ) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        video_url = None

        for kw in keywords:
            video_url = cls.search_pexels_video(pexels_key, kw)
            if video_url:
                break
            video_url = cls.search_pixabay_video(pixabay_key, kw)
            if video_url:
                break

        if video_url:
            try:
                r = requests.get(video_url, stream=True, timeout=25)
                if r.status_code == 200:
                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                    return dest_path
            except Exception as e:
                print(f"Failed to download video from {video_url}: {e}")

        return cls.create_fallback_clip(dest_path, duration, scene_id)
"""
write_file("backend/services/media_service.py", media_py)

# ==============================================================================
# 5. backend/services/subtitle_service.py
# ==============================================================================
subtitle_py = """from pathlib import Path
from typing import List, Dict, Any

class SubtitleService:
    @staticmethod
    def format_ass_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    @classmethod
    def generate_hormozi_ass(
        cls,
        words: List[Dict[str, Any]],
        output_ass_path: Path,
        style_preset: Dict[str, Any],
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        font_name = style_preset.get("font_name", "Impact")
        font_size = style_preset.get("font_size", 76)
        primary_color = style_preset.get("primary_color", "&H00FFFFFF")
        highlight_color = style_preset.get("highlight_color", "&H0000E5FF")
        outline_color = style_preset.get("outline_color", "&H00000000")
        shadow_color = style_preset.get("shadow_color", "&H80000000")
        max_words = style_preset.get("max_words_per_line", 3)

        header = f\"\"\"[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HormoziStyle,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{shadow_color},-1,0,0,0,100,100,2,0,1,5.5,3.0,2,60,60,440,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
\"\"\"
        events = []
        if not words:
            output_ass_path.parent.mkdir(parents=True, exist_ok=True)
            output_ass_path.write_text(header, encoding="utf-8")
            return output_ass_path

        chunks = []
        for i in range(0, len(words), max_words):
            chunks.append(words[i:i + max_words])

        for chunk in chunks:
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"] + 0.15

            for active_idx, active_word in enumerate(chunk):
                w_start = active_word["start"]
                if active_idx + 1 < len(chunk):
                    w_end = chunk[active_idx + 1]["start"]
                else:
                    w_end = chunk_end

                line_parts = []
                for idx, w in enumerate(chunk):
                    word_str = w["word"].upper().strip()
                    if idx == active_idx:
                        line_parts.append(f"{\\\\c" + highlight_color + "}" + word_str + "{\\\\c" + primary_color + "}")
                    else:
                        line_parts.append(word_str)

                text_content = " ".join(line_parts)
                start_str = cls.format_ass_time(w_start)
                end_str = cls.format_ass_time(w_end)

                events.append(f"Dialogue: 0,{start_str},{end_str},HormoziStyle,,0,0,0,,{text_content}")

        ass_content = header + "\\n".join(events) + "\\n"
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        output_ass_path.write_text(ass_content, encoding="utf-8")
        return output_ass_path
"""
write_file("backend/services/subtitle_service.py", subtitle_py)

# ==============================================================================
# 6. backend/services/video_composer.py
# ==============================================================================
composer_py = """import subprocess
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
            "fps=30"
        )
        cmd = [
            "ffmpeg", "-y",
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
        bgm_volume: float = 0.15
    ) -> Path:
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        concat_file = output_video.parent / f"concat_{output_video.stem}.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                clean_path = str(clip.resolve()).replace("\\\\", "/")
                f.write(f"file '{clean_path}'\\n")

        clean_ass = str(ass_subtitles.resolve()).replace("\\\\", "/").replace(":", "\\\\:")
        video_filter = f"subtitles='{clean_ass}'"

        if bgm_audio and bgm_audio.exists():
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(voiceover_audio),
                "-stream_loop", "-1", "-i", str(bgm_audio),
                "-filter_complex",
                f"[0:v]{video_filter}[v];[2:a]volume={bgm_volume}[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "medium",
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
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(voiceover_audio),
                "-vf", video_filter,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                str(output_video)
            ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg render error:\\n{res.stderr}")

        if concat_file.exists():
            concat_file.unlink()

        return output_video
"""
write_file("backend/services/video_composer.py", composer_py)

print("Core services generated successfully!")
