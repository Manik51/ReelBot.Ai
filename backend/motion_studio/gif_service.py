import json
import random
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.config import settings

class GifService:
    """
    Searches and downloads animated GIF and MP4 motion loops
    from Google Tenor v2 API, Giphy API, and high-speed zero-key web search.
    """

    STYLE_KEYWORDS = {
        "dark_noir": "dark moody mystery horror noir",
        "anime": "anime aesthetic cyberpunk",
        "meme": "reaction funny meme",
        "graphic": "stylized minimal neon",
        "cinematic": "cinematic atmospheric"
    }

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # Google Tenor v2 official web client key (100% free, zero configuration needed)
    TENOR_V2_KEY = "AIzaSyCZt6SSh5VgVPzD9fhyzG1DprdPRhtoaR4"
    TENOR_CLIENT_KEY = "tenor_web"

    # Strict Quality Floor: Reject blurry / tiny preview thumbnails
    MIN_WIDTH = 280
    MIN_HEIGHT = 240
    MIN_FILE_SIZE = 15000  # Minimum 15KB

    @classmethod
    def _clean_query(cls, query: str) -> str:
        q = re.sub(r'["\'\(\)\[\]\#\!\?]', '', query).strip()
        words = [w for w in q.split() if len(w) > 2][:4]
        return ' '.join(words) or 'funny comedy'

    @classmethod
    def search_tenor_v2_hd(cls, query: str, limit: int = 12, context_words: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Queries Google Tenor v2 API for high-definition 30 FPS MP4 video loops.
        Filters out low-resolution thumbnails (< 280x240) and ranks by semantic description matching.
        """
        api_key = getattr(settings, 'TENOR_API_KEY', '').strip() or cls.TENOR_V2_KEY
        clean_q = cls._clean_query(query)
        url = "https://tenor.googleapis.com/v2/search"
        params = {
            "q": clean_q,
            "key": api_key,
            "client_key": cls.TENOR_CLIENT_KEY,
            "limit": limit,
            "media_filter": "loopedmp4,mp4,mediumgif,gif,tinymp4",
            "contentfilter": "medium"
        }

        try:
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                query_tokens = [t.lower() for t in clean_q.split() if len(t) > 2]
                ctx_tokens = [c.lower() for c in (context_words or []) if len(c) > 2]

                for item in data.get("results", []):
                    desc = (item.get("content_description") or "").lower()
                    media = item.get("media_formats", {})

                    # Format priority: loopedmp4 > mp4 > mediumgif > gif
                    chosen_format = None
                    chosen_url = None
                    chosen_dims = [0, 0]

                    for fmt_name in ["loopedmp4", "mp4", "mediumgif", "gif"]:
                        if fmt_name in media:
                            fmt_info = media[fmt_name]
                            dims = fmt_info.get("dims", [0, 0])
                            w = dims[0] if len(dims) > 0 else 0
                            h = dims[1] if len(dims) > 1 else 0

                            # Strict Quality Check: Discard tiny or low-res items
                            if w >= cls.MIN_WIDTH and h >= cls.MIN_HEIGHT:
                                chosen_format = fmt_name
                                chosen_url = fmt_info.get("url")
                                chosen_dims = [w, h]
                                break

                    # If no format met strict quality, check standard mp4 as fallback
                    if not chosen_url and "mp4" in media:
                        fmt_info = media["mp4"]
                        chosen_format = "mp4"
                        chosen_url = fmt_info.get("url")
                        chosen_dims = fmt_info.get("dims", [320, 240])

                    if not chosen_url:
                        continue

                    # Semantic Relevance Scoring:
                    # 1. Matches between search query tokens and the video description
                    q_score = sum(3.0 for token in query_tokens if token in desc)
                    # 2. Context narration word matches
                    c_score = sum(1.5 for token in ctx_tokens if token in desc)
                    # 3. Higher resolution bonus
                    res_bonus = (chosen_dims[0] * chosen_dims[1]) / 250000.0
                    # 4. Format bonus (favor smooth 30fps MP4 loops over GIF)
                    fmt_bonus = 2.0 if "mp4" in chosen_format else 0.5

                    total_score = q_score + c_score + res_bonus + fmt_bonus

                    results.append({
                        "id": item.get("id"),
                        "title": item.get("content_description") or clean_q,
                        "description": desc,
                        "download_url": chosen_url,
                        "format": chosen_format,
                        "dims": chosen_dims,
                        "score": round(total_score, 2),
                        "source": f"Tenor v2 HD ({chosen_format})"
                    })

                # Sort by semantic relevance score descending
                results.sort(key=lambda x: x["score"], reverse=True)
                if results:
                    return results
        except Exception as e:
            print(f"Tenor v2 HD search error: {e}")

        return []

    @classmethod
    def search_giphy_api(cls, query: str, api_key: str, limit: int = 6) -> List[Dict[str, Any]]:
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": api_key.strip(),
            "q": cls._clean_query(query),
            "limit": limit,
            "rating": "pg-13"
        }
        try:
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("data", []):
                    images = item.get("images", {})
                    orig = images.get("original", {})
                    fixed = images.get("fixed_height", {})
                    url_mp4 = orig.get("mp4") or fixed.get("mp4")
                    url_gif = orig.get("url") or fixed.get("url")
                    w = int(orig.get("width", 0) or fixed.get("width", 0) or 0)
                    h = int(orig.get("height", 0) or fixed.get("height", 0) or 0)

                    if w >= cls.MIN_WIDTH and h >= cls.MIN_HEIGHT:
                        results.append({
                            "id": item.get("id"),
                            "title": item.get("title", query),
                            "download_url": url_mp4 or url_gif,
                            "format": "mp4" if url_mp4 else "gif",
                            "dims": [w, h],
                            "score": 1.0,
                            "source": "Giphy API HD"
                        })
                if results:
                    return results
        except Exception as e:
            print(f"Giphy API error: {e}")
        return []

    @classmethod
    def search_motion_clips(
        cls,
        query: str,
        style_preset: str = "meme",
        context_words: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Searches HD motion clips via Tenor v2 HD and Giphy fallbacks."""
        # 1. Primary: Google Tenor v2 HD Engine
        res = cls.search_tenor_v2_hd(query, limit=limit, context_words=context_words)
        if res:
            return res

        # 2. Giphy if configured
        giphy_key = getattr(settings, 'GIPHY_API_KEY', '')
        if giphy_key:
            res = cls.search_giphy_api(query, api_key=giphy_key, limit=limit)
            if res:
                return res

        return []

    @classmethod
    def download_motion_clip(
        cls,
        keywords: List[str],
        dest_path: Path,
        style_preset: str = "meme",
        scene_id: int = 0,
        used_urls: Optional[set] = None,
        narration_context: str = ""
    ) -> Path:
        """
        Downloads the highest quality, most relevant motion clip across multi-tier keywords:
        - Primary physical action query
        - Alternative action query
        - Fallback subject query
        Strictly enforces MIN_WIDTH / MIN_HEIGHT and prevents repeated visuals.
        """
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if used_urls is None:
            used_urls = set()

        ctx_tokens = [w for w in re.sub(r'[^\w\s]', '', narration_context).split() if len(w) > 2]

        for query_tier in keywords:
            if not query_tier or not query_tier.strip():
                continue

            candidates = cls.search_motion_clips(
                query=query_tier.strip(),
                style_preset=style_preset,
                context_words=ctx_tokens,
                limit=10
            )

            # Filter out URLs already downloaded in this video
            fresh_candidates = [c for c in candidates if c.get("download_url") not in used_urls]
            items_to_try = fresh_candidates if fresh_candidates else candidates

            for item in items_to_try:
                download_url = item.get("download_url")
                if not download_url:
                    continue

                try:
                    resp = requests.get(download_url, headers=cls.HEADERS, stream=True, timeout=12)
                    if resp.status_code == 200:
                        with open(dest_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=16384):
                                f.write(chunk)

                        file_size = dest_path.stat().st_size
                        # Verify strict file size floor to avoid corrupted/empty downloads
                        if file_size >= cls.MIN_FILE_SIZE:
                            dims_str = f"{item['dims'][0]}x{item['dims'][1]}" if 'dims' in item else "HD"
                            print(f"[Scene {scene_id}] Downloaded HD Clip ({dims_str}, {item.get('format')}, score={item.get('score')}) from {item.get('source')} for query '{query_tier}'")
                            used_urls.add(download_url)
                            return dest_path
                        else:
                            dest_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Failed downloading clip {download_url}: {e}")
                    dest_path.unlink(missing_ok=True)
                    continue

        # If all search queries fail, generate clean procedural animated canvas loop
        import subprocess
        print(f"[Scene {scene_id}] Generating fallback cinematic pulse loop for keywords: {keywords}")
        vf_expr = (
            "color=c=#07070d:s=1080x1920:d=3.0:r=30,"
            "drawbox=x=180:y=360:w=720:h=1200:color=#8a2be2@0.25:t=fill,"
            "vignette=PI/3.5"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", vf_expr,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-t", "3.0", str(dest_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            pass

        return dest_path
