import os
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.config import settings
from backend.services.youtube_service import YouTubeService
from backend.documentary_studio.docu_script_service import DocuScriptService
from backend.documentary_studio.docu_composer import DocuComposer

docu_router = APIRouter(prefix="/api/documentary", tags=["Documentary & Business Studio"])

# Dedicated Task Store for Documentary Studio
docu_tasks_db: Dict[str, Dict[str, Any]] = {}

# ── REQUEST MODELS ─────────────────────────────────────────────────────────
class StoryboardRequest(BaseModel):
    topic: str
    duration_sec: int = 60
    language: str = "English"
    visual_theme: str = "dark_slate"
    allowed_metaphors: Optional[List[str]] = None

class DocumentaryRenderRequest(BaseModel):
    storyboard: Dict[str, Any]
    voice_id: str = "kokoro:am_adam"
    voice_speed: str = "+0%"
    subtitle_color: str = "yellow"
    font_name: str = "Space Grotesk"
    visual_theme: str = "crime_noir"
    bgm_id: Optional[str] = "dark_investigative"
    bgm_volume: float = 0.15
    sfx_volume: float = 0.60
    sfx_enabled: bool = True

class DocuYouTubeUploadRequest(BaseModel):
    task_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy_status: str = "public"

# ── ENDPOINTS ──────────────────────────────────────────────────────────────
@docu_router.get("/presets")
def get_presets():
    """Returns curated documentary presets, voices, themes, and subtitle styles."""
    presets = DocuScriptService.get_presets()
    presets["voices"] = settings.VOICES
    presets["subtitle_colors"] = [
        {"id": "yellow", "name": "🟡 Hormozi Neon Yellow (Alex Hormozi Word-POP)"},
        {"id": "cyan", "name": "🔵 Cyberpunk Cyan (Clean Tech POP)"},
        {"id": "gold", "name": "🥇 Luxury Gold (Documentary Prestige)"},
        {"id": "red", "name": "🔴 Crimson Alert (Dramatic Crime/Crash)"}
    ]
    presets["fonts"] = [
        {"id": "Space Grotesk", "name": "Space Grotesk (Modern Tech Bold)"},
        {"id": "Impact", "name": "Impact (Classic Viral Hormozi)"},
        {"id": "Montserrat", "name": "Montserrat (Documentary Minimal)"},
        {"id": "Arial Black", "name": "Arial Black (High Punch)"}
    ]
    presets["bgm_options"] = [
        {"id": "dark_investigative", "name": "🚨 True Crime Noir & Investigation (Dark Ambient Drone)"},
        {"id": "corporate_power", "name": "💼 Corporate Power & Ambition (Cinematic Pulse)"},
        {"id": "financial_doom", "name": "📉 Financial Doom & Tension (Low Strings)"},
        {"id": "none", "name": "🔇 Mute Background Music (Voice + SFX Only)"}
    ]
    return presets

@docu_router.post("/generate-storyboard")
def generate_storyboard(req: StoryboardRequest):
    """Generates an editable 18-20 beat storyboard JSON based on user topic & duration."""
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    try:
        storyboard = DocuScriptService.generate_storyboard(
            topic=req.topic.strip(),
            duration_sec=req.duration_sec,
            language=req.language,
            visual_theme=req.visual_theme,
            allowed_metaphors=req.allowed_metaphors
        )
        return storyboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storyboard generation failed: {str(e)}")

@docu_router.post("/render")
def render_documentary(req: DocumentaryRenderRequest, background_tasks: BackgroundTasks):
    """Spawns an asynchronous background task to render the documentary video."""
    beats = req.storyboard.get("beats", [])
    if not beats:
        raise HTTPException(status_code=400, detail="Storyboard contains no beats.")

    task_id = f"docu_{uuid.uuid4().hex[:12]}"
    docu_tasks_db[task_id] = {
        "status": "processing",
        "progress": 5,
        "stage": "Initializing documentary render...",
        "logs": ["[00:00.00] ⚡ Documentary Studio Engine Initialized."],
        "video_url": None,
        "video_path": None,
        "seo": {
            "title": req.storyboard.get("title", "The Untold Business Story #shorts"),
            "description": req.storyboard.get("seo_description", "Full documentary case study. #reelbot.ai #business"),
            "tags": ["shorts", "business", "documentary", "history", "reelbot.ai"]
        },
        "error": None
    }

    def run_render():
        t_data = docu_tasks_db[task_id]
        def log_cb(msg: str):
            t_data["logs"].append(msg)
            # Rough progress estimation based on keywords
            if "Step 1" in msg:
                t_data["progress"] = 20
                t_data["stage"] = "Voiceover synthesis..."
            elif "Step 2" in msg:
                t_data["progress"] = 35
                t_data["stage"] = "Beat synchronization..."
            elif "Step 3" in msg:
                t_data["progress"] = 55
                t_data["stage"] = "2.5D visual composition..."
            elif "Step 4" in msg:
                t_data["progress"] = 75
                t_data["stage"] = "Multi-track audio & SFX mixing..."
            elif "Step 5" in msg:
                t_data["progress"] = 90
                t_data["stage"] = "Burning Hormozi captions & mastering MP4..."

        try:
            out_file = DocuComposer.render_documentary_video(
                storyboard=req.storyboard,
                voice_id=req.voice_id,
                voice_speed=req.voice_speed,
                subtitle_color=req.subtitle_color,
                font_name=req.font_name,
                visual_theme=req.visual_theme,
                bgm_id=req.bgm_id,
                bgm_volume=req.bgm_volume,
                sfx_volume=req.sfx_volume,
                sfx_enabled=req.sfx_enabled,
                task_id=task_id,
                log_callback=log_cb
            )
            t_data["status"] = "completed"
            t_data["progress"] = 100
            t_data["stage"] = "Ready to download & publish!"
            t_data["video_path"] = str(out_file)
            t_data["video_url"] = f"/output/{out_file.name}"
            t_data["logs"].append(f"[DONE] 🚀 Video ready at {t_data['video_url']}")
        except Exception as e:
            t_data["status"] = "failed"
            t_data["error"] = str(e)
            t_data["logs"].append(f"[ERROR] ❌ Render failed: {str(e)}")

    background_tasks.add_task(run_render)
    return {"task_id": task_id, "status": "processing"}

@docu_router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Polls real-time progress and logs for a documentary render task."""
    if task_id not in docu_tasks_db:
        raise HTTPException(status_code=404, detail="Task not found.")
    return docu_tasks_db[task_id]

@docu_router.post("/upload-youtube")
def upload_youtube(req: DocuYouTubeUploadRequest):
    """Direct 1-click YouTube Shorts upload for rendered documentary."""
    t_data = docu_tasks_db.get(req.task_id)
    if not t_data or not t_data.get("video_path"):
        raise HTTPException(status_code=400, detail="Valid rendered video not found for this task.")

    v_path = Path(t_data["video_path"])
    if not v_path.exists():
        raise HTTPException(status_code=404, detail="Video file missing from disk.")

    title = req.title or t_data.get("seo", {}).get("title", "Documentary Short")
    if "#reelbot.ai" not in title:
        title = f"{title} #reelbot.ai"

    desc = req.description or t_data.get("seo", {}).get("description", "")
    if "#reelbot.ai" not in desc:
        desc = f"{desc}\n\nCreated with #reelbot.ai"

    tags = req.tags or t_data.get("seo", {}).get("tags", ["documentary", "shorts"])
    if "reelbot.ai" not in tags:
        tags.append("reelbot.ai")

    try:
        yt = YouTubeService()
        result = yt.upload_video(
            video_path=v_path,
            title=title,
            description=desc,
            tags=tags,
            privacy_status=req.privacy_status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube upload error: {str(e)}")
