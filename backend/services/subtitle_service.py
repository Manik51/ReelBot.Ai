import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from backend.config import settings

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
    def _resolve_style(cls, style_input: Optional[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
        default_style = {
            "id": "hormozi_yellow",
            "name": "Hormozi Viral Yellow",
            "primary_color": "&H00FFFFFF",
            "highlight_color": "&H0000E5FF",  # Yellow Highlight in ASS format
            "outline_color": "&H00000000",
            "shadow_color": "&H80000000",
            "font_size": 76,
            "font_name": "Impact",
            "bold": 1,
            "max_words_per_line": 3
        }

        if isinstance(style_input, dict):
            return style_input

        if isinstance(style_input, str):
            for s in settings.SUBTITLE_STYLES:
                if s["id"] == style_input:
                    return s

        return default_style

    @classmethod
    def align_subtitle_words(
        cls,
        tts_words: List[Dict[str, Any]],
        custom_subtitle_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Gemini-র দেওয়া Banglish/Hinglish টেক্সটকে TTS-এর নিখুঁত টাইমস্ট্যাম্পের সাথে সিঙ্ক করে।
        """
        if not custom_subtitle_text or not custom_subtitle_text.strip():
            return tts_words

        clean_custom = re.sub(r"[^\w\s]", "", custom_subtitle_text).strip().upper()
        custom_tokens = clean_custom.split()

        if not custom_tokens or not tts_words:
            return tts_words

        # শব্দ সংখ্যা সমান হলে সরাসরি রিপ্লেস করা
        if len(custom_tokens) == len(tts_words):
            aligned = []
            for idx, w in enumerate(tts_words):
                aligned.append({
                    "word": custom_tokens[idx],
                    "start": w["start"],
                    "end": w["end"],
                    "duration": w.get("duration", round(w["end"] - w["start"], 3))
                })
            return aligned

        # শব্দ সংখ্যা ভিন্ন হলে টাইম ফ্রেম সমানুপাতিক হারে ভাগ করা
        total_duration = tts_words[-1]["end"]
        start_offset = tts_words[0]["start"]
        active_time = max(total_duration - start_offset, 0.5)
        time_per_word = active_time / len(custom_tokens)

        aligned = []
        for idx, token in enumerate(custom_tokens):
            w_start = start_offset + (idx * time_per_word)
            w_end = w_start + time_per_word
            aligned.append({
                "word": token,
                "start": round(w_start, 3),
                "end": round(w_end, 3),
                "duration": round(time_per_word, 3)
            })

        return aligned

    @classmethod
    def generate_hormozi_ass(
        cls,
        words: List[Dict[str, Any]],
        output_ass_path: Path,
        style_preset: Optional[Union[str, Dict[str, Any]]] = None,
        subtitle_style: Optional[Union[str, Dict[str, Any]]] = None,
        custom_subtitle_text: Optional[str] = None,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        raw_preset = style_preset or subtitle_style
        preset = cls._resolve_style(raw_preset)

        font_name = preset.get("font_name", "Impact")
        font_size = preset.get("font_size", 76)
        primary_color = preset.get("primary_color", "&H00FFFFFF")
        highlight_color = preset.get("highlight_color", "&H0000E5FF")
        outline_color = preset.get("outline_color", "&H00000000")
        shadow_color = preset.get("shadow_color", "&H80000000")
        max_words = preset.get("max_words_per_line", 3)

        # Banglish/Hinglish কাস্টম টেক্সট সিঙ্ক করা
        aligned_words = cls.align_subtitle_words(words, custom_subtitle_text)

        header_lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: HormoziStyle,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{shadow_color},-1,0,0,0,100,100,2,0,1,6.0,3.5,2,60,60,480,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        header = "\n".join(header_lines) + "\n"

        events = []
        if not aligned_words:
            output_ass_path.parent.mkdir(parents=True, exist_ok=True)
            output_ass_path.write_text(header, encoding="utf-8")
            return output_ass_path

        chunks = []
        for i in range(0, len(aligned_words), max_words):
            chunks.append(aligned_words[i:i + max_words])

        for chunk in chunks:
            for active_idx, active_word in enumerate(chunk):
                start_time = cls.format_ass_time(active_word["start"])
                end_time = cls.format_ass_time(active_word["end"])

                line_parts = []
                for w_idx, w in enumerate(chunk):
                    clean_w = str(w["word"]).replace("{", "").replace("}", "").strip().upper()
                    if w_idx == active_idx:
                        # Active Word Pop Animation (Hormozi Neon Highlight + Scale Pop)
                        line_parts.append(r"{\c" + highlight_color + r"\b1\fscx112\fscy112}" + clean_w + r"{\r}")
                    else:
                        # Regular Word
                        line_parts.append(r"{\c" + primary_color + r"\b1}" + clean_w + r"{\r}")

                dialogue_text = " ".join(line_parts)
                event_line = f"Dialogue: 0,{start_time},{end_time},HormoziStyle,,0,0,0,,{dialogue_text}"
                events.append(event_line)

        full_ass_content = header + "\n".join(events) + "\n"
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        output_ass_path.write_text(full_ass_content, encoding="utf-8")
        return output_ass_path
