import os
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
