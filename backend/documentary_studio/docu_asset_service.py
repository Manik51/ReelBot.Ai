import os
import io
import json
import math
import hashlib
import requests
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import scipy.ndimage

from backend.config import settings

class DocuAssetService:
    """
    Dedicated asset generation and cutout pipeline for Documentary & Business Analysis Studio.
    Handles local subject cutouts, dynamic newspaper clippings, archival photos, stock b-roll, and brand logos.
    """

    ASSETS_DIR = settings.BASE_DIR / "backend" / "documentary_studio" / "assets"
    LOGOS_DIR = ASSETS_DIR / "logos"
    CACHE_DIR = settings.TEMP_DIR / "docu_assets"

    _rembg_session = None

    @classmethod
    def initialize(cls):
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_rembg_session(cls):
        if cls._rembg_session is None:
            try:
                import rembg
                # Prioritize human-optimized segmentation model
                cls._rembg_session = rembg.new_session("u2net_human_seg")
            except Exception as e:
                print(f"[DocuAsset] Could not load u2net_human_seg ({e}), falling back to silueta")
                try:
                    import rembg
                    cls._rembg_session = rembg.new_session("silueta")
                except Exception as e2:
                    print(f"[DocuAsset] Could not load rembg session: {e2}")
        return cls._rembg_session

    @classmethod
    def get_silueta_session(cls):
        return cls.get_rembg_session()

    # ── 1. STUDIO-GRADE SUBJECT CUTOUT PIPELINE (U2NET + COMPONENT ISOLATION + POLISH) ───
    @classmethod
    def fetch_subject_cutout(cls, subject_query: str, fallback_logo_name: str = "") -> Path:
        """
        Fetches a studio-grade single-subject cutout:
        1. Searches Google Images for high-resolution unwatermarked solo portraits
        2. Filters out collages, group photos, and stock agency watermarks
        3. Downloads full-resolution original image (>= 400x500, vertical/square)
        4. Extracts foreground using u2net_human_seg
        5. Runs connected-component analysis to isolate the SINGLE main subject (removes secondary people/artifacts)
        6. Crops transparent edges with padding
        7. Applies studio polish: subtle amber/white rim light, bottom 22% alpha fade, dual-stage 3D drop shadow
        """
        cls.initialize()
        if not subject_query or not subject_query.strip():
            return cls.get_brand_logo(fallback_logo_name or "Entity")

        q_clean = subject_query.strip()
        c_hash = hashlib.md5(f"{q_clean}_v3_studio".lower().encode()).hexdigest()[:12]
        out_path = cls.CACHE_DIR / f"cutout_{c_hash}.png"
        if out_path.exists() and out_path.stat().st_size > 5000:
            return out_path

        serper_key = getattr(settings, "SERPER_API_KEY", "")
        if serper_key:
            try:
                headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
                search_queries = [
                    f"{q_clean} portrait photo isolated",
                    f"{q_clean} official portrait photograph",
                    f"{q_clean} solo portrait press photo",
                    f"{q_clean} press conference portrait",
                    f"{q_clean} portrait"
                ]
                
                forbidden_terms = [
                    "collage", "timeline", "vs", "versus", "evolution",
                    "young and old", "before and after", "comparison", "group", "family"
                ]
                watermark_domains = [
                    "dreamstime", "shutterstock", "gettyimages", "alamy", "istockphoto", "123rf", "stock.adobe"
                ]

                selected_img = None
                fallback_thumb = None

                for sq in search_queries:
                    payload = json.dumps({"q": sq, "num": 8})
                    r = requests.post("https://google.serper.dev/images", headers=headers, data=payload, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        imgs = data.get("images", [])
                        for im_data in imgs:
                            title = im_data.get("title", "").lower()
                            img_url = im_data.get("imageUrl", "")
                            t_url = im_data.get("thumbnailUrl", "")

                            # Skip collages / comparisons
                            if any(term in title or term in img_url.lower() for term in forbidden_terms):
                                continue

                            # Try high-resolution image URL first (skip known watermarked stock domains)
                            if img_url and not any(wd in img_url.lower() for wd in watermark_domains):
                                try:
                                    r_img = requests.get(img_url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
                                    if r_img.status_code == 200 and len(r_img.content) > 15000:
                                        check_im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                                        w, h = check_im.size
                                        aspect = w / max(1, h)
                                        # Strict solo portrait aspect ratio and resolution
                                        if w >= 400 and h >= 500 and 0.45 <= aspect <= 1.08:
                                            selected_img = check_im
                                            break
                                except Exception:
                                    pass

                            # Save fallback thumbnail if no direct image succeeded yet
                            if not fallback_thumb and t_url:
                                try:
                                    r_t = requests.get(t_url, timeout=5)
                                    if r_t.status_code == 200 and len(r_t.content) > 2000:
                                        t_im = Image.open(io.BytesIO(r_t.content)).convert("RGB")
                                        if 0.45 <= (t_im.width / max(1, t_im.height)) <= 1.10:
                                            fallback_thumb = t_im
                                except Exception:
                                    pass

                    if selected_img:
                        break

                img_to_cut = selected_img or fallback_thumb
                if img_to_cut:
                    import rembg
                    session = cls.get_rembg_session()

                    # Run background removal
                    buf = io.BytesIO()
                    img_to_cut.save(buf, format="PNG")
                    cutout_bytes = rembg.remove(buf.getvalue(), session=session)
                    raw_cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

                    # Isolate SINGLE largest subject component using scipy
                    try:
                        arr = np.array(raw_cutout)
                        alpha = arr[:, :, 3]
                        binary_mask = (alpha > 30).astype(np.uint8)
                        labeled, num_features = scipy.ndimage.label(binary_mask)
                        if num_features > 1:
                            sizes = scipy.ndimage.sum(binary_mask, labeled, range(1, num_features + 1))
                            largest_label = int(np.argmax(sizes)) + 1
                            keep_mask = (labeled == largest_label)
                            arr[:, :, 3] = arr[:, :, 3] * keep_mask
                            raw_cutout = Image.fromarray(arr, mode="RGBA")
                    except Exception as e_comp:
                        print(f"[DocuAsset] Component isolation skipped ({e_comp})")

                    # Crop transparent borders with padding
                    bbox = raw_cutout.getbbox()
                    if bbox:
                        pad = 20
                        w, h = raw_cutout.size
                        crop_box = (
                            max(0, bbox[0] - pad),
                            max(0, bbox[1] - pad),
                            min(w, bbox[2] + pad),
                            min(h, bbox[3] + pad)
                        )
                        raw_cutout = raw_cutout.crop(crop_box)

                    # Polish with studio lighting, bottom fade, and dual-layer drop shadow
                    final_cutout = cls._polish_studio_cutout(raw_cutout)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    final_cutout.save(str(out_path), "PNG")
                    print(f"[DocuAsset] Studio cutout generated for '{q_clean}' ({out_path.name})")
                    return out_path
            except Exception as e:
                print(f"[DocuAsset] Error generating studio cutout for '{q_clean}': {e}")

        # Fallback to brand logo badge
        return cls.get_brand_logo(fallback_logo_name or q_clean)

    @classmethod
    def _polish_studio_cutout(cls, img: Image.Image) -> Image.Image:
        """Applies subtle rim lighting, bottom 22% alpha fade, and dual-tier 3D drop shadow."""
        w, h = img.size
        arr = np.array(img, dtype=np.float32)

        # 1. Bottom 22% alpha fade so cutout dissolves into background & lower margins
        fade_h = int(h * 0.22)
        if fade_h > 0:
            ramp = np.linspace(1.0, 0.0, fade_h, dtype=np.float32)
            arr[h - fade_h:h, :, 3] = arr[h - fade_h:h, :, 3] * ramp[:, np.newaxis]

        base_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGBA")

        # 2. Subtle Cinematic Rim Light (1.5px soft glow along silhouette)
        alpha = base_img.split()[3]
        dilated_alpha = alpha.filter(ImageFilter.MaxFilter(3))
        edge_mask = ImageOps.invert(alpha)
        rim_mask = Image.composite(dilated_alpha, Image.new("L", (w, h), 0), edge_mask)
        rim_mask = rim_mask.filter(ImageFilter.GaussianBlur(1.2))

        rim_color = Image.new("RGBA", (w, h), (255, 245, 220, 130))
        rim_layer = Image.composite(rim_color, Image.new("RGBA", (w, h), (0, 0, 0, 0)), rim_mask)

        # 3. Dual-Tier 3D Drop Shadow
        # Tier 1: Crisp Contact Shadow
        shadow_alpha_1 = alpha.point(lambda p: int(p * 0.55))
        black = Image.new("L", (w, h), 0)
        shadow_1 = Image.merge("RGBA", (black, black, black, shadow_alpha_1)).filter(ImageFilter.GaussianBlur(8))

        # Tier 2: Diffuse Ambient Deep Shadow
        shadow_alpha_2 = alpha.point(lambda p: int(p * 0.35))
        shadow_2 = Image.merge("RGBA", (black, black, black, shadow_alpha_2)).filter(ImageFilter.GaussianBlur(24))

        # Composite onto padded canvas
        pad = 40
        cw = w + pad * 2
        ch = h + pad * 2
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

        # Paste ambient shadow (offset 16, 20)
        canvas.paste(shadow_2, (pad + 16, pad + 20), shadow_2)
        # Paste contact shadow (offset 6, 8)
        canvas.paste(shadow_1, (pad + 6, pad + 8), shadow_1)
        # Paste subject
        canvas.paste(base_img, (pad, pad), base_img)
        return canvas

    @classmethod
    def _add_drop_shadow(
        cls,
        img: Image.Image,
        offset: Tuple[int, int] = (14, 18),
        blur_radius: int = 16,
        shadow_opacity: float = 0.60
    ) -> Image.Image:
        """Composites a soft realistic Gaussian drop shadow behind an image."""
        r, g, b, a = img.split()
        black = Image.new("L", img.size, 0)
        shadow_alpha = a.point(lambda p: int(p * shadow_opacity))
        shadow_img = Image.merge("RGBA", (black, black, black, shadow_alpha))
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(blur_radius))

        pad_x = abs(offset[0]) + blur_radius * 2
        pad_y = abs(offset[1]) + blur_radius * 2
        cw = img.size[0] + pad_x * 2
        ch = img.size[1] + pad_y * 2

        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.paste(shadow_img, (pad_x + offset[0], pad_y + offset[1]), shadow_img)
        canvas.paste(img, (pad_x, pad_y), img)
        return canvas

    # ── 2. ARCHIVAL & HISTORICAL PHOTOGRAPH PIPELINE (KEN BURNS) ──────────
    @classmethod
    def fetch_archival_photo(cls, query: str) -> Path:
        """
        Fetches a real historical / archival photograph from Google Serper.
        Saves as a high-quality JPEG for smooth Ken Burns pan/zoom.
        """
        cls.initialize()
        q_clean = (query or "historical document archive").strip()
        p_hash = hashlib.md5(q_clean.lower().encode()).hexdigest()[:12]
        out_path = cls.CACHE_DIR / f"photo_{p_hash}.jpg"
        if out_path.exists() and out_path.stat().st_size > 5000:
            return out_path

        serper_key = getattr(settings, "SERPER_API_KEY", "")
        if serper_key:
            try:
                headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
                search_queries = [
                    f"{q_clean} archival photograph",
                    f"{q_clean} historical photo",
                    q_clean
                ]
                img_url = None
                thumb_url = None
                for sq in search_queries:
                    payload = json.dumps({"q": sq, "num": 5})
                    r = requests.post("https://google.serper.dev/images", headers=headers, data=payload, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        imgs = data.get("images", [])
                        if imgs:
                            img_url = imgs[0].get("imageUrl")
                            thumb_url = imgs[0].get("thumbnailUrl")
                            if thumb_url or img_url:
                                break

                downloaded = False
                if img_url:
                    try:
                        r_img = requests.get(img_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                        if r_img.status_code == 200 and len(r_img.content) > 5000:
                            test_im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                            test_im.save(str(out_path), "JPEG", quality=92)
                            downloaded = True
                    except Exception:
                        downloaded = False

                if not downloaded and thumb_url:
                    r_thumb = requests.get(thumb_url, timeout=6)
                    if r_thumb.status_code == 200 and len(r_thumb.content) > 1000:
                        test_im = Image.open(io.BytesIO(r_thumb.content)).convert("RGB")
                        test_im.save(str(out_path), "JPEG", quality=92)
                        downloaded = True

                if downloaded:
                    print(f"[DocuAsset] Successfully fetched archival photo for '{q_clean}' ({out_path.name})")
                    return out_path
            except Exception as e:
                print(f"[DocuAsset] Error fetching archival photo for '{q_clean}': {e}")

        # Fallback to generated high-contrast archival placeholder card
        return cls._generate_fallback_archival_photo(q_clean, out_path)

    @classmethod
    def _generate_fallback_archival_photo(cls, query: str, out_path: Path) -> Path:
        """Generates a high-contrast vintage sepia archival photo card when offline."""
        w, h = 1080, 1920
        img = Image.new("RGB", (w, h), (18, 16, 14))
        draw = ImageDraw.Draw(img)
        # Vignette lines
        draw.rectangle((40, 40, w - 40, h - 40), outline=(80, 70, 55), width=3)
        try:
            font = ImageFont.truetype("arialbd.ttf", 52)
        except Exception:
            font = ImageFont.load_default()
        draw.text((w // 2, h // 2), f"ARCHIVAL RECORD:\n{query[:40].upper()}", fill=(200, 185, 160), font=font, anchor="mm", align="center")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "JPEG", quality=90)
        return out_path

    # ── 3. STOCK FOOTAGE B-ROLL PIPELINE (PEXELS / PIXABAY - ENVIRONMENTAL ONLY) ──
    @classmethod
    def sanitize_environmental_broll(cls, keywords: str) -> str:
        """
        Ensures stock b-roll is environmental/atmospheric texture only.
        Strips human-face inducing keywords and replaces with cinematic background terms.
        """
        human_terms = [
            "man", "woman", "person", "businessman", "businesswoman", "people", "crowd",
            "face", "talking", "portrait", "worker", "employee", "guy", "human"
        ]
        words = keywords.lower().split()
        filtered = [w for w in words if w not in human_terms]

        if len(filtered) < 2:
            return "dark bokeh light leaks abstract"

        clean_q = " ".join(filtered)
        if not any(k in clean_q for k in ["dark", "blur", "cinematic", "night", "lights", "abstract"]):
            clean_q += " dark bokeh cinematic"
        return clean_q

    @classmethod
    def resolve_contextual_query(
        cls,
        keywords: str,
        metaphor: str = "",
        primary_subject: str = "",
        contextual_broll: str = ""
    ) -> str:
        """
        Determines the most accurate, context-locked environmental video query:
        - If newspaper_slam -> newspaper printing press industrial rotating rollers
        - If Steve Jobs / Apple -> Apple headquarters building Cupertino exterior or corporate tech campus night
        - If Bill Gates / Microsoft -> 1990s vintage computer server room laboratory or Microsoft corporate campus
        - If financial_stat -> stock market ticker numbers wall dark or Wall Street trading floor panic vintage
        """
        if contextual_broll and contextual_broll.strip():
            return cls.sanitize_environmental_broll(contextual_broll)

        s_lower = (primary_subject or "").lower()
        m_lower = (metaphor or "").lower()

        if m_lower == "newspaper_slam":
            return "newspaper printing press industrial rotating rollers"
        elif "apple" in s_lower or "jobs" in s_lower:
            return "corporate technology glass building night"
        elif "microsoft" in s_lower or "gates" in s_lower:
            return "vintage computer servers technology laboratory"
        elif "netflix" in s_lower or "blockbuster" in s_lower:
            return "video rental store vintage vhs shelves archive"
        elif m_lower == "financial_stat":
            return "stock market ticker numbers wall dark"

        return cls.sanitize_environmental_broll(keywords or "dark corporate skyscraper night")

    @classmethod
    def fetch_broll_background(
        cls,
        keywords: str,
        theme: str = "dark_slate",
        beat_idx: int = 0,
        metaphor: str = "",
        primary_subject: str = "",
        contextual_broll: str = ""
    ) -> Path:
        """
        Retrieves a 1080x1920 portrait stock video loop matching the beat keywords.
        Strictly context-locked and sanitized from conflicting human faces.
        Falls back to atmospheric animated motion if offline or no match.
        """
        cls.initialize()
        k_clean = cls.resolve_contextual_query(keywords, metaphor, primary_subject, contextual_broll)
        b_hash = hashlib.md5(f"{k_clean}_{theme}".lower().encode()).hexdigest()[:12]
        out_path = cls.CACHE_DIR / f"broll_{b_hash}.mp4"
        if out_path.exists() and out_path.stat().st_size > 50000:
            return out_path

        from backend.services.media_service import MediaService
        video_url = None
        if getattr(settings, "PEXELS_API_KEY", ""):
            video_url = MediaService.search_pexels_video(settings.PEXELS_API_KEY, k_clean)
        if not video_url and getattr(settings, "PIXABAY_API_KEY", ""):
            video_url = MediaService.search_pixabay_video(settings.PIXABAY_API_KEY, k_clean)

        if video_url:
            try:
                r = requests.get(video_url, stream=True, timeout=25)
                if r.status_code == 200:
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                    if out_path.exists() and out_path.stat().st_size > 50000:
                        print(f"[DocuAsset] Downloaded context-locked b-roll for '{k_clean}' ({out_path.stat().st_size} bytes)")
                        return out_path
            except Exception as e:
                print(f"[DocuAsset] Failed to download stock video for '{k_clean}': {e}")

        # Fallback to atmospheric moving background
        return cls._generate_atmospheric_background(theme, beat_idx, out_path)

    @classmethod
    def _generate_atmospheric_background(cls, theme: str, beat_idx: int, out_path: Path) -> Path:
        """Generates a dynamic 1080x1920 background clip with color shifting and subtle grid."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        theme_colors = {
            "dark_slate": ("0x0b1120", "0x1e293b"),
            "vintage_archive": ("0x1c1917", "0x292524"),
            "cyber_tech": ("0x030712", "0x0f172a"),
            "wall_street": ("0x022c22", "0x064e3b")
        }
        c1, c2 = theme_colors.get(theme, ("0x0b1120", "0x1e293b"))
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={c1}:s=1080x1920:d=4.0:r=30",
            "-vf", f"drawbox=y=ih/3:color={c2}@0.45:width=iw:height=ih/3:t=fill,vignette=PI/4",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(out_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path

    # ── 3. ACTION GIF / ARCHIVAL LOOP PIPELINE (TENOR V2 HD) ──────────────
    @classmethod
    def fetch_action_clip(cls, query: str) -> Optional[Path]:
        """Fetches a high-energy looping MP4 reaction or event clip from Tenor."""
        cls.initialize()
        if not query or not query.strip():
            return None
        q_clean = query.strip()
        a_hash = hashlib.md5(q_clean.lower().encode()).hexdigest()[:12]
        out_path = cls.CACHE_DIR / f"action_{a_hash}.mp4"
        if out_path.exists() and out_path.stat().st_size > 10000:
            return out_path

        try:
            from backend.motion_studio.gif_service import GifService
            results = GifService.search_tenor_v2_hd(q_clean, limit=4)
            for item in results:
                url = item.get("download_url")
                if url and "mp4" in url:
                    r = requests.get(url, stream=True, timeout=12)
                    if r.status_code == 200:
                        with open(out_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=65536):
                                f.write(chunk)
                        if out_path.stat().st_size > 10000:
                            print(f"[DocuAsset] Fetched Tenor action clip for '{q_clean}'")
                            return out_path
        except Exception as e:
            print(f"[DocuAsset] Error fetching action clip for '{q_clean}': {e}")
        return None

    @classmethod
    def create_cutout(cls, image_path: Path, output_path: Path) -> Path:
        """Extracts subject foreground as transparent PNG."""
        cls.initialize()
        if not image_path.exists():
            raise FileNotFoundError(f"Input image does not exist: {image_path}")

        try:
            import rembg
            input_bytes = image_path.read_bytes()
            session = cls.get_silueta_session()
            output_bytes = rembg.remove(input_bytes, session=session)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(output_bytes)
            return output_path
        except Exception as e:
            print(f"[DocuAsset] rembg failed ({e}). Using feathered vignette fallback.")
            return cls._fallback_feathered_cutout(image_path, output_path)

    @classmethod
    def _fallback_feathered_cutout(cls, image_path: Path, output_path: Path) -> Path:
        """Creates a professional soft circular/oval feathered cutout."""
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        pad_x = int(w * 0.08)
        pad_y = int(h * 0.05)
        draw.ellipse((pad_x, pad_y, w - pad_x, h - pad_y), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=min(w, h) // 18))
        img.putalpha(mask)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path), "PNG")
        return output_path

    # ── 2. REAL ARCHIVAL NEWSPAPER PIPELINE (GOOGLE SERPER) ────────────────
    @classmethod
    def fetch_real_archival_newspaper(
        cls,
        query: str,
        headline: str,
        highlight_phrase: str = "",
        publication_name: str = "THE WALL STREET JOURNAL",
        theme: str = "dark_slate"
    ) -> Tuple[Path, Optional[Tuple[int, int, int, int]]]:
        """
        Searches Google Serper for the real historical newspaper front page / clipping.
        Frames it onto an authentic vintage newspaper canvas with realistic drop shadow.
        Returns (clipping_png_path, highlight_bounding_box).
        Falls back to procedural generation if no specific real newspaper image is found.
        """
        cls.initialize()
        q_clean = (query or headline).strip()
        h_hash = hashlib.md5(f"{q_clean}_{headline}_{publication_name}_{theme}".encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"real_news_{h_hash}.png"
        if out_path.exists() and out_path.stat().st_size > 15000:
            hl_box = (140, 480, 800, 110)
            return out_path, hl_box

        serper_key = getattr(settings, "SERPER_API_KEY", "")
        real_img_bytes = None
        if serper_key:
            try:
                headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
                search_queries = [
                    f"{q_clean} newspaper front page headline archive clipping",
                    f"{headline} vintage newspaper article archive",
                    f"{publication_name} {q_clean} newspaper"
                ]
                for sq in search_queries:
                    payload = json.dumps({"q": sq, "num": 5})
                    r = requests.post("https://google.serper.dev/images", headers=headers, data=payload, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        imgs = data.get("images", [])
                        for im_data in imgs:
                            t_url = im_data.get("thumbnailUrl") or im_data.get("imageUrl")
                            if t_url:
                                try:
                                    r_t = requests.get(t_url, timeout=5)
                                    if r_t.status_code == 200 and len(r_t.content) > 2000:
                                        test_im = Image.open(io.BytesIO(r_t.content))
                                        asp = test_im.width / max(1, test_im.height)
                                        if 0.55 <= asp <= 1.40:
                                            real_img_bytes = r_t.content
                                            break
                                except Exception:
                                    continue
                        if real_img_bytes:
                            break
            except Exception as e:
                print(f"[DocuAsset] Error fetching real archival newspaper: {e}")

        if real_img_bytes:
            try:
                raw_news = Image.open(io.BytesIO(real_img_bytes)).convert("RGBA")
                canvas_w, canvas_h = 960, 960
                raw_news.thumbnail((880, 880), Image.Resampling.LANCZOS)

                is_dark = "dark" in theme or "slate" in theme
                canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(canvas)

                paste_x = (canvas_w - raw_news.width) // 2
                paste_y = (canvas_h - raw_news.height) // 2

                border_color = (71, 85, 105, 255) if is_dark else (180, 170, 150, 255)
                draw.rectangle((paste_x - 12, paste_y - 12, paste_x + raw_news.width + 12, paste_y + raw_news.height + 12),
                               fill=(15, 20, 25, 240) if is_dark else (238, 232, 218, 255),
                               outline=border_color, width=3)
                canvas.paste(raw_news, (paste_x, paste_y), raw_news)

                canvas_with_shadow = cls._add_drop_shadow(canvas, offset=(14, 18), blur_radius=16, shadow_opacity=0.60)
                canvas_with_shadow.save(str(out_path), "PNG")

                hl_h = max(60, int(raw_news.height * 0.14))
                hl_y = paste_y + int(raw_news.height * 0.22)
                hl_box = (paste_x + 10, hl_y, raw_news.width - 20, hl_h)
                print(f"[DocuAsset] Successfully framed real archival newspaper clipping for '{q_clean}'")
                return out_path, hl_box
            except Exception as e:
                print(f"[DocuAsset] Framing archival newspaper failed: {e}")

        # Fallback to procedural generator with exact publication masthead
        return cls.generate_newspaper_clipping(
            headline=headline,
            highlight_phrase=highlight_phrase,
            newspaper_name=publication_name or "THE WALL STREET JOURNAL",
            theme=theme
        )

    # ── 3. PROCEDURAL NEWSPAPER CLIPPING GENERATOR ─────────────────────────
    @classmethod
    def generate_newspaper_clipping(
        cls,
        headline: str,
        highlight_phrase: str = "",
        date_str: str = "SPECIAL INVESTIGATION",
        newspaper_name: str = "THE FINANCIAL CHRONICLE",
        theme: str = "dark_slate"
    ) -> Tuple[Path, Optional[Tuple[int, int, int, int]]]:
        """
        Renders an authentic newspaper clipping card (1080x1080).
        Returns (clipping_png_path, highlight_bounding_box [x, y, w, h]).
        """
        cls.initialize()
        h_hash = hashlib.md5(f"{headline}_{date_str}_{newspaper_name}_{theme}".encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"news_{h_hash}.png"

        width, height = 1080, 1080
        
        is_dark = "dark" in theme or "slate" in theme
        bg_color = (22, 27, 34, 255) if is_dark else (244, 240, 230, 255)
        paper_tint = (15, 20, 25) if is_dark else (238, 232, 218)
        ink_color = (255, 255, 255) if is_dark else (20, 20, 20)
        accent_color = (217, 119, 6) if is_dark else (160, 30, 30)
        rule_color = (60, 70, 85) if is_dark else (180, 170, 150)

        img = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Subtle paper noise texture
        noise = Image.effect_noise((width, height), 12).convert("L")
        noise = ImageOps.colorize(noise, black=paper_tint, white=bg_color[:3])
        img = Image.blend(img.convert("RGB"), noise, alpha=0.18).convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Newspaper outer borders
        draw.rectangle((40, 40, width - 40, height - 40), outline=rule_color, width=3)
        draw.rectangle((46, 46, width - 46, height - 46), outline=rule_color, width=1)

        # Masthead header
        try:
            font_masthead = ImageFont.truetype("arialbd.ttf", 46)
            font_sub = ImageFont.truetype("arial.ttf", 22)
            font_headline = ImageFont.truetype("arialbd.ttf", 64)
            font_body = ImageFont.truetype("georgia.ttf", 24)
        except Exception:
            font_masthead = ImageFont.load_default()
            font_sub = font_masthead
            font_headline = font_masthead
            font_body = font_masthead

        # Draw Masthead
        masthead_text = newspaper_name.upper()
        draw.text((width // 2, 90), masthead_text, fill=ink_color, font=font_masthead, anchor="mm")
        
        # Date & Issue Bar
        draw.line((60, 135, width - 60, 135), fill=rule_color, width=2)
        draw.text((70, 150), f"VOL. XLVIII ... NO. 18,402", fill=rule_color, font=font_sub)
        draw.text((width // 2, 150), date_str.upper(), fill=accent_color, font=font_sub, anchor="mt")
        draw.text((width - 70, 150), "LATE CITY EDITION", fill=rule_color, font=font_sub, anchor="rt")
        draw.line((60, 185, width - 60, 185), fill=rule_color, width=2)

        # Headline word wrap & calculation
        words = headline.split()
        lines = []
        cur_line = []
        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = draw.textbbox((0, 0), test_line, font=font_headline)
            if (bbox[2] - bbox[0]) > (width - 160):
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        # Draw Headline & compute highlight bounding box
        y_pos = 230
        highlight_box = None

        for line in lines:
            draw.text((width // 2, y_pos), line, fill=ink_color, font=font_headline, anchor="ma")
            line_bbox = draw.textbbox((width // 2, y_pos), line, font=font_headline, anchor="ma")
            
            # Check if highlight phrase matches
            if highlight_phrase and highlight_phrase.lower() in line.lower() and not highlight_box:
                highlight_box = (
                    int(line_bbox[0] - 12),
                    int(line_bbox[1] - 4),
                    int(line_bbox[2] - line_bbox[0] + 24),
                    int(line_bbox[3] - line_bbox[1] + 12)
                )
            y_pos += 80

        # If no specific phrase matched, highlight the first headline line
        if not highlight_box and lines:
            first_bbox = draw.textbbox((width // 2, 230), lines[0], font=font_headline, anchor="ma")
            highlight_box = (
                int(first_bbox[0] - 12),
                int(first_bbox[1] - 4),
                int(first_bbox[2] - first_bbox[0] + 24),
                int(first_bbox[3] - first_bbox[1] + 12)
            )

        # Horizontal rule below headline
        draw.line((60, y_pos + 20, width - 60, y_pos + 20), fill=rule_color, width=2)

        # 3-Column simulated archival news body
        col_y = y_pos + 45
        col_w = (width - 180) // 3
        filler_para = (
            "Inside confidential corporate boardrooms, sources confirm high-stakes negotiations "
            "as billions in equity hang in the balance. Internal memos disclose unprecedented shifts "
            "in capital structure, leaving industry titans scrambling for market survival."
        )
        for c in range(3):
            col_x = 70 + c * (col_w + 20)
            draw.rectangle((col_x, col_y, col_x + col_w, height - 80), outline=None)
            # Simulated text lines
            cur_cy = col_y
            while cur_cy < (height - 90):
                line_len = col_w if (cur_cy < height - 120) else (col_w * 0.6)
                draw.line((col_x, cur_cy, col_x + line_len, cur_cy), fill=rule_color, width=3)
                cur_cy += 16

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path, highlight_box

    # ── 3. ORBIT RING & GLOW GENERATOR ─────────────────────────────────────
    @classmethod
    def generate_orbit_ring(cls, diameter: int = 720, color_hex: str = "#d97706") -> Path:
        """Renders transparent circular orbit with dashed nodes."""
        cls.initialize()
        out_path = cls.CACHE_DIR / f"orbit_{diameter}_{color_hex.replace('#', '')}.png"
        if out_path.exists():
            return out_path

        size = diameter + 100
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        center = size // 2
        r = diameter // 2

        # Convert hex to RGB
        hex_clean = color_hex.lstrip('#')
        rgb = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))

        # Glowing outer ring
        for offset in range(8, 0, -1):
            alpha = int(35 * (1.0 - offset / 8.0))
            draw.ellipse((center - r - offset, center - r - offset, center + r + offset, center + r + offset),
                         outline=(*rgb, alpha), width=2)

        # Primary sharp ring
        draw.ellipse((center - r, center - r, center + r, center + r), outline=(*rgb, 220), width=4)

        # Orbit anchor nodes (4 celestial points)
        for angle_deg in [0, 90, 180, 270]:
            rad = math.radians(angle_deg)
            nx = center + int(r * math.cos(rad))
            ny = center + int(r * math.sin(rad))
            # Glowing node dot
            draw.ellipse((nx - 14, ny - 14, nx + 14, ny + 14), fill=(*rgb, 100))
            draw.ellipse((nx - 8, ny - 8, nx + 8, ny + 8), fill=(255, 255, 255, 255))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    # ── 4. FINANCIAL STAT & TICKER CARD GENERATOR ──────────────────────────
    @classmethod
    def generate_financial_card(
        cls,
        stat_number: str,
        stat_label: str,
        delta_str: str = "+142%",
        trend: str = "up"
    ) -> Path:
        """Renders a sleek 900x500 financial case study metric card."""
        cls.initialize()
        h_hash = hashlib.md5(f"{stat_number}_{stat_label}_{delta_str}_{trend}".encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"stat_{h_hash}.png"
        if out_path.exists():
            return out_path

        w, h = 920, 520
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded dark glassmorphic container
        draw.rounded_rectangle((10, 10, w - 10, h - 10), radius=28, fill=(15, 23, 42, 235), outline=(51, 65, 85, 255), width=3)

        # Trend color (Emerald green for up / Crimson red for down)
        is_up = trend.lower() == "up" or "+" in delta_str
        trend_rgb = (16, 185, 129) if is_up else (239, 68, 68)
        trend_arrow = "▲" if is_up else "▼"

        try:
            font_val = ImageFont.truetype("arialbd.ttf", 84)
            font_lbl = ImageFont.truetype("arialbd.ttf", 32)
            font_pill = ImageFont.truetype("arialbd.ttf", 34)
        except Exception:
            font_val = ImageFont.load_default()
            font_lbl = font_val
            font_pill = font_val

        # Label at top
        draw.text((50, 50), stat_label.upper(), fill=(148, 163, 184), font=font_lbl)

        # Stat Value (Massive)
        draw.text((50, 120), stat_number, fill=(255, 255, 255), font=font_val)

        # Delta Badge Pill
        pill_text = f"{trend_arrow} {delta_str}"
        pill_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
        pill_w = pill_bbox[2] - pill_bbox[0] + 36
        pill_h = 56
        draw.rounded_rectangle((50, 250, 50 + pill_w, 250 + pill_h), radius=16, fill=(*trend_rgb, 40), outline=(*trend_rgb, 200), width=2)
        draw.text((68, 260), pill_text, fill=(*trend_rgb, 255), font=font_pill)

        # Mini vector trendline curve at bottom
        curve_pts = []
        start_y = 440 if is_up else 340
        end_y = 330 if is_up else 450
        for i in range(12):
            cx = 50 + i * (w - 100) // 11
            progress = i / 11.0
            jitter = (math.sin(i * 1.5) * 20)
            cy = start_y + (end_y - start_y) * progress + jitter
            curve_pts.append((cx, cy))
        
        for i in range(len(curve_pts) - 1):
            draw.line([curve_pts[i], curve_pts[i+1]], fill=(*trend_rgb, 240), width=6)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    # ── 5. SPLIT-SCREEN COMPARISON BADGE & DIVIDER ────────────────────────
    @classmethod
    def generate_split_overlay(
        cls,
        label1: str,
        label2: str
    ) -> Path:
        """Renders a 1080x1920 transparent overlay with glowing vertical laser line, center VS badge, and name banners."""
        cls.initialize()
        h_hash = hashlib.md5(f"{label1}_{label2}".encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"split_overlay_{h_hash}.png"
        if out_path.exists():
            return out_path

        w, h = 1080, 1920
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Center laser line (glowing amber)
        center_x = w // 2
        for offset in range(6, 0, -1):
            alpha = int(45 * (1.0 - offset / 6.0))
            draw.line([(center_x - offset, 200), (center_x - offset, 1500)], fill=(217, 119, 6, alpha), width=2)
            draw.line([(center_x + offset, 200), (center_x + offset, 1500)], fill=(217, 119, 6, alpha), width=2)
        draw.line([(center_x, 200), (center_x, 1500)], fill=(245, 158, 11, 240), width=6)

        # Center VS circular badge
        vs_y = h // 2 - 100
        draw.ellipse([(center_x - 55, vs_y - 55), (center_x + 55, vs_y + 55)], fill=(15, 23, 42, 245), outline=(245, 158, 11, 255), width=4)
        try:
            f_vs = ImageFont.truetype("arialbd.ttf", 46)
            f_lbl = ImageFont.truetype("arialbd.ttf", 28)
        except Exception:
            f_vs = ImageFont.load_default()
            f_lbl = f_vs

        draw.text((center_x, vs_y), "VS", fill=(255, 255, 255), font=f_vs, anchor="mm")

        # Left label pill
        p1_text = label1.strip().upper()
        if p1_text:
            bb1 = draw.textbbox((0, 0), p1_text, font=f_lbl)
            pw1 = bb1[2] - bb1[0] + 36
            draw.rounded_rectangle([(w // 4 - pw1 // 2, 1420), (w // 4 + pw1 // 2, 1480)], radius=14, fill=(15, 23, 42, 230), outline=(51, 65, 85, 255), width=2)
            draw.text((w // 4, 1450), p1_text, fill=(255, 255, 255), font=f_lbl, anchor="mm")

        # Right label pill
        p2_text = label2.strip().upper()
        if p2_text:
            bb2 = draw.textbbox((0, 0), p2_text, font=f_lbl)
            pw2 = bb2[2] - bb2[0] + 36
            draw.rounded_rectangle([(3 * w // 4 - pw2 // 2, 1420), (3 * w // 4 + pw2 // 2, 1480)], radius=14, fill=(15, 23, 42, 230), outline=(51, 65, 85, 255), width=2)
            draw.text((3 * w // 4, 1450), p2_text, fill=(255, 255, 255), font=f_lbl, anchor="mm")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    # ── 6. SILENT COMPREHENSION: CHAPTER STAMPS & ROLE BADGES ──────────────
    @classmethod
    def generate_chapter_stamp(cls, text: str) -> Path:
        """
        Renders an on-screen location & time stamp badge for silent viewing (1080x1920 overlay).
        e.g. '[ AUGUST 1997 · CUPERTINO, CA ]' or '[ 90 DAYS UNTIL EXTINCTION ]'.
        """
        cls.initialize()
        clean_text = (text or "").strip().upper()
        if not clean_text:
            clean_text = "[ INVESTIGATIVE CASE STUDY ]"
        s_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"stamp_{s_hash}.png"
        if out_path.exists():
            return out_path

        w, h = 1080, 1920
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arialbd.ttf", 32)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), clean_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        pw = tw + 48
        ph = 64
        px = (w - pw) // 2
        py = 135

        # Glowing amber pill container
        draw.rounded_rectangle((px - 2, py - 2, px + pw + 2, py + ph + 2), radius=14, outline=(245, 158, 11, 90), width=2)
        draw.rounded_rectangle((px, py, px + pw, py + ph), radius=12, fill=(15, 23, 42, 235), outline=(245, 158, 11, 220), width=2)
        draw.text((w // 2, py + ph // 2), clean_text, fill=(255, 255, 255), font=font, anchor="mm")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    @classmethod
    def generate_role_badge(cls, role_title: str) -> Optional[Path]:
        """
        Renders a subject identity/role banner above subtitles for silent comprehension.
        e.g. 'STEVE JOBS · INTERIM CEO (1997)'
        """
        cls.initialize()
        clean_title = (role_title or "").strip().upper()
        if not clean_title:
            return None
        r_hash = hashlib.md5(clean_title.encode()).hexdigest()[:10]
        out_path = cls.CACHE_DIR / f"role_{r_hash}.png"
        if out_path.exists():
            return out_path

        w, h = 1080, 1920
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arialbd.ttf", 28)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), clean_title, font=font)
        tw = bbox[2] - bbox[0]
        pw = tw + 40
        ph = 56
        px = (w - pw) // 2
        py = 1450

        draw.rounded_rectangle((px, py, px + pw, py + ph), radius=12, fill=(15, 23, 42, 230), outline=(51, 65, 85, 240), width=2)
        draw.text((w // 2, py + ph // 2), clean_title, fill=(255, 255, 255), font=font, anchor="mm")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    # ── 7. BRAND LOGO RESOLVER ────────────────────────────────────────────
    @classmethod
    def get_brand_logo(cls, brand_name: str) -> Optional[Path]:
        """
        Retrieves or dynamically creates a clean vector-style logo for major companies.
        """
        cls.initialize()
        b_clean = brand_name.strip().lower().replace(" ", "_").replace(".", "")
        existing = cls.LOGOS_DIR / f"{b_clean}.png"
        if existing.exists():
            return existing

        # Dynamically render iconic brand badge if not present
        return cls._render_brand_badge(brand_name, existing)

    @classmethod
    def _render_brand_badge(cls, brand_name: str, out_path: Path) -> Path:
        w, h = 320, 320
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Color schemes for top business giants
        palette_map = {
            "apple": ((245, 245, 247), (20, 20, 20), ""),
            "tesla": ((232, 33, 39), (255, 255, 255), "T"),
            "spacex": ((15, 23, 42), (255, 255, 255), "X"),
            "meta": ((0, 129, 251), (255, 255, 255), "∞"),
            "facebook": ((24, 119, 242), (255, 255, 255), "f"),
            "google": ((255, 255, 255), (66, 133, 244), "G"),
            "microsoft": ((30, 41, 59), (0, 164, 239), "■"),
            "amazon": ((35, 47, 62), (255, 153, 0), "a"),
            "netflix": ((0, 0, 0), (229, 9, 20), "N"),
            "nokia": ((18, 101, 235), (255, 255, 255), "NOKIA"),
            "tata": ((0, 90, 160), (255, 255, 255), "TATA"),
            "reliance": ((200, 16, 46), (255, 255, 255), "RIL"),
            "nvidia": ((118, 185, 0), (0, 0, 0), "NV"),
            "twitter": ((29, 155, 240), (255, 255, 255), "𝕏"),
        }

        b_key = brand_name.lower().strip()
        bg_rgb, text_rgb, monogram = palette_map.get(b_key, ((30, 41, 59), (217, 119, 6), brand_name[:3].upper()))

        # Circular outer badge with border
        draw.ellipse((10, 10, w - 10, h - 10), fill=(*bg_rgb, 255), outline=(255, 255, 255, 80), width=4)

        try:
            f_size = 110 if len(monogram) <= 2 else 54
            font = ImageFont.truetype("arialbd.ttf", f_size)
        except Exception:
            font = ImageFont.load_default()

        draw.text((w // 2, h // 2), monogram, fill=(*text_rgb, 255), font=font, anchor="mm")
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path
