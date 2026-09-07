import os
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from backend.config import settings

class WatermarkService:
    _cached_path: Optional[Path] = None

    @classmethod
    def get_watermark_image(cls) -> Path:
        """
        Generates and returns the official SkullBot.Ai semi-transparent watermark badge PNG.
        Dimensions: 340x68 px, RGBA, featuring the skull logo and SKULLBOT.AI branding.
        """
        out_dir = settings.TEMP_DIR / 'watermarks'
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / 'skullbot_watermark.png'
        if out_file.exists() and out_file.stat().st_size > 500:
            return out_file

        w, h = 340, 68
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((2, 2, w - 2, h - 2), radius=16, fill=(12, 12, 18, 115), outline=(220, 38, 38, 150), width=2)

        skull_drawn = False
        for font_name in ['seguiemj.ttf', 'seguiem.ttf', 'arial.ttf']:
            try:
                f_skull = ImageFont.truetype(font_name, 32)
                draw.text((32, h // 2), chr(0x2620), font=f_skull, fill=(255, 255, 255, 220), anchor='mm')
                skull_drawn = True
                break
            except Exception:
                continue

        if not skull_drawn:
            try:
                f_sb = ImageFont.truetype('arialbd.ttf', 22)
                draw.text((32, h // 2), 'SB', font=f_sb, fill=(239, 68, 68, 220), anchor='mm')
            except Exception:
                pass

        try:
            f_brand = ImageFont.truetype('arialbd.ttf', 22)
            f_sub = ImageFont.truetype('arialbd.ttf', 10)
        except Exception:
            f_brand = ImageFont.load_default()
            f_sub = f_brand

        draw.text((64, 14), 'SKULLBOT.AI', fill=(255, 255, 255, 220), font=f_brand)
        draw.text((66, 42), 'TRUE CRIME INVESTIGATIVE STUDIO', fill=(239, 68, 68, 200), font=f_sub)
        img.save(str(out_file), 'PNG')
        cls._cached_path = out_file
        return out_file

    @classmethod
    def get_floating_overlay_filter(
        cls,
        video_in_label: str = '[graded]',
        watermark_in_idx: int = 2,
        out_label: str = '[vwater]'
    ) -> str:
        x_expr = "clip((main_w-overlay_w)*(0.5+0.46*sin(t*0.50)),40,main_w-overlay_w-40)"
        y_expr = "clip((main_h-overlay_h-360)*(0.5+0.46*cos(t*0.37))+160,160,main_h-overlay_h-220)"
        return f"{video_in_label}[{watermark_in_idx}:v]overlay=x='{x_expr}':y='{y_expr}'{out_label}"

