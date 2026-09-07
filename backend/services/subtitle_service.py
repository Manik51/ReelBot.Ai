from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from backend.config import settings

class SubtitleService:
    """
    Production Hormozi-Style Subtitle Engine
    Implements sliding context window (1 context word before + active pop word + 1 context word after)
    with scale punch animation, dimmed context alpha, and bold 92pt mobile-optimized typography.
    """

    @staticmethod
    def format_ass_time(val: Union[int, float]) -> str:
        """Converts seconds (or ms if > 600) to ASS timestamp format H:MM:SS.CC"""
        if isinstance(val, (int, float)) and val > 600:
            seconds = val / 1000.0
        else:
            seconds = float(val)

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
            "primary_color": "&H00FFFFFF",      # White
            "highlight_color": "&H0000E5FF",    # Vibrant Yellow (&HAABBGGRR: Yellow is 00E5FF)
            "outline_color": "&H00000000",      # Solid Black outline
            "shadow_color": "&H80000000",       # Semi-transparent black shadow
            "font_size": 92,
            "font_name": "Impact",
            "outline_size": 7.0,
            "shadow_size": 3.0,
            "margin_bottom": 220,
            "pop_scale": 118,
            "pop_duration_ms": 160
        }

        if isinstance(style_input, dict):
            merged = default_style.copy()
            merged.update(style_input)
            return merged

        if isinstance(style_input, str):
            for s in settings.SUBTITLE_STYLES:
                if s["id"] == style_input:
                    merged = default_style.copy()
                    merged.update(s)
                    merged["font_size"] = max(merged.get("font_size", 92), 88)
                    merged["outline_size"] = 7.0
                    merged["shadow_size"] = 3.0
                    merged["margin_bottom"] = 220
                    return merged

        return default_style

    @classmethod
    def generate_hormozi_ass(
        cls,
        words: List[Dict[str, Any]],
        output_ass_path: Path,
        style_preset: Optional[Union[str, Dict[str, Any]]] = None,
        subtitle_style: Optional[Union[str, Dict[str, Any]]] = None,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """
        Generates production-ready Alex Hormozi ASS subtitle file using Claude's
        signature sliding context window technique:
        - Each spoken word has its own dialogue event
        - Current spoken word: Hot style + punch scale animation (118% -> 100%)
        - Context words: Normal style with dimmed alpha (&H55&)
        - 1 word before + active word + 1 word after displayed simultaneously
        """
        raw_preset = style_preset or subtitle_style
        preset = cls._resolve_style(raw_preset)

        font_name = preset.get("font_name", "Impact")
        font_size = preset.get("font_size", 92)
        color_normal = preset.get("primary_color", "&H00FFFFFF")
        color_highlight = preset.get("highlight_color", "&H0000E5FF")
        color_outline = preset.get("outline_color", "&H00000000")
        color_shadow = preset.get("shadow_color", "&H80000000")
        outline_size = preset.get("outline_size", 7.0)
        shadow_size = preset.get("shadow_size", 3.0)
        margin_bottom = preset.get("margin_bottom", 220)
        pop_scale = preset.get("pop_scale", 118)
        pop_dur = preset.get("pop_duration_ms", 160)
        ctx = 1  # 1 word before + active + 1 word after

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,{font_name},{font_size},{color_normal},{color_normal},{color_outline},{color_shadow},-1,0,0,0,100,100,3,0,1,{outline_size},{shadow_size},2,80,80,{margin_bottom},1
Style: Hot,{font_name},{font_size},{color_highlight},{color_highlight},{color_outline},{color_shadow},-1,0,0,0,{pop_scale},{pop_scale},3,0,1,{outline_size},{shadow_size},2,80,80,{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        if not words:
            output_ass_path.parent.mkdir(parents=True, exist_ok=True)
            output_ass_path.write_text(header, encoding="utf-8")
            return output_ass_path

        n = len(words)
        for i, w in enumerate(words):
            raw_start = w.get("start", 0)
            raw_end = w.get("end", 0)
            t_start = cls.format_ass_time(raw_start)
            t_end = cls.format_ass_time(raw_end)

            # Sliding context window: 1 word before + current + 1 word after
            win_start = max(0, i - ctx)
            win_end = min(n, i + ctx + 1)
            window = words[win_start:win_end]
            cur_idx = i - win_start

            parts = []
            for j, ww in enumerate(window):
                clean_text = str(ww.get("word", "")).replace("{", "").replace("}", "").strip().upper()
                if not clean_text:
                    continue

                if j == cur_idx:
                    # Current active word: Hot style + bouncy punch animation
                    anim = r"{\rHot\fscx" + str(pop_scale) + r"\fscy" + str(pop_scale) + r"\t(0," + str(pop_dur) + r",\fscx100\fscy100)}" + clean_text
                    parts.append(anim)
                else:
                    # Context words: Normal style with dimmed alpha (&H55&)
                    parts.append(r"{\rNormal\alpha&H55&}" + clean_text)

            line_text = "  ".join(parts)
            events.append(f"Dialogue: 0,{t_start},{t_end},Normal,,0,0,0,,{line_text}")

        full_content = header + "\n".join(events) + "\n"
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        output_ass_path.write_text(full_content, encoding="utf-8")
        return output_ass_path
