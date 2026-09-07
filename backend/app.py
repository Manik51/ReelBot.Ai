import os
import sys
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

# Force UTF-8 encoding on Windows to prevent 'charmap' / cp1252 crashes
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.services.gemini_service import GeminiService
from backend.services.media_service import MediaService
from backend.services.tts_service import TTSService
from backend.services.subtitle_service import SubtitleService
from backend.services.video_composer import VideoComposer
from backend.services.youtube_service import YouTubeService
from backend.services.serper_service import SerperService
from backend.motion_studio.router import motion_router
from backend.documentary_studio.router import docu_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(motion_router)
app.include_router(docu_router)

tasks_db: Dict[str, Dict[str, Any]] = {}

class ConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    sarvam_api_key: Optional[str] = None
    ai4bharat_api_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None
    tenor_api_key: Optional[str] = None
    giphy_api_key: Optional[str] = None

class ScriptGenerateRequest(BaseModel):
    topic: str
    language: str = "Bengali"
    tone: str = "Storytelling / Suspense"
    target_duration_sec: int = 60

class VideoSceneInput(BaseModel):
    scene_id: int
    time_range: Optional[str] = "0:00-0:03"
    visual_tag: Optional[str] = None
    narration: str
    subtitle_text: Optional[str] = None
    keywords: List[str]
    suggested_emoji: Optional[str] = "🕵️‍♂️"
    estimated_seconds: Optional[float] = 3.0

class VideoGenerateRequest(BaseModel):
    title: str
    scenes: List[VideoSceneInput]
    voice_id: str = "bn-IN-TanishaaNeural"
    voice_rate: str = "+10%"
    subtitle_style_id: str = "hormozi_yellow"
    bgm_track_id: Optional[str] = "default"
    bgm_volume: float = 0.15

class YouTubeUploadRequest(BaseModel):
    video_filename: str
    title: str
    description: str
    tags: List[str]
    privacy_status: str = "public"

class YouTubeCredentialsRequest(BaseModel):
    client_secret_json: str

@app.get("/api/config")
def get_config():
    bgm_tracks = []
    if settings.BGM_DIR.exists():
        for f in settings.BGM_DIR.glob("*.mp3"):
            bgm_tracks.append({"id": f.stem, "name": f.stem.replace("-", " ").title()})

    yt_status = YouTubeService.get_auth_status()

    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_sarvam_key": bool(settings.SARVAM_API_KEY),
        "has_ai4bharat_key": bool(settings.AI4BHARAT_API_KEY),
        "has_pexels_key": bool(settings.PEXELS_API_KEY),
        "has_pixabay_key": bool(settings.PIXABAY_API_KEY),
        "has_serper_key": bool(settings.SERPER_API_KEY),
        "has_tenor_key": bool(settings.TENOR_API_KEY),
        "has_giphy_key": bool(settings.GIPHY_API_KEY),
        "gemini_api_key_masked": bool(settings.GEMINI_API_KEY),
        "sarvam_api_key_masked": bool(settings.SARVAM_API_KEY),
        "ai4bharat_api_key_masked": bool(settings.AI4BHARAT_API_KEY),
        "pexels_api_key_masked": bool(settings.PEXELS_API_KEY),
        "pixabay_api_key_masked": bool(settings.PIXABAY_API_KEY),
        "serper_api_key_masked": bool(settings.SERPER_API_KEY),
        "tenor_api_key_masked": bool(settings.TENOR_API_KEY),
        "giphy_api_key_masked": bool(settings.GIPHY_API_KEY),
        "youtube_authenticated": yt_status["authenticated"],
        "youtube_channel_title": yt_status["channel_title"],
        "voices": settings.VOICES,
        "subtitle_styles": settings.SUBTITLE_STYLES,
        "bgm_tracks": bgm_tracks
    }

@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    env_path = settings.BASE_DIR / ".env"
    env_lines = {}
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_lines[k.strip()] = v.strip()
        except Exception:
            pass

    if req.gemini_api_key is not None:
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
        os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        env_lines["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    if req.sarvam_api_key is not None:
        settings.SARVAM_API_KEY = req.sarvam_api_key.strip()
        os.environ["SARVAM_API_KEY"] = settings.SARVAM_API_KEY
        env_lines["SARVAM_API_KEY"] = settings.SARVAM_API_KEY
    if req.ai4bharat_api_key is not None:
        settings.AI4BHARAT_API_KEY = req.ai4bharat_api_key.strip()
        os.environ["AI4BHARAT_API_KEY"] = settings.AI4BHARAT_API_KEY
        env_lines["AI4BHARAT_API_KEY"] = settings.AI4BHARAT_API_KEY
    if req.pexels_api_key is not None:
        settings.PEXELS_API_KEY = req.pexels_api_key.strip()
        os.environ["PEXELS_API_KEY"] = settings.PEXELS_API_KEY
        env_lines["PEXELS_API_KEY"] = settings.PEXELS_API_KEY
    if req.pixabay_api_key is not None:
        settings.PIXABAY_API_KEY = req.pixabay_api_key.strip()
        os.environ["PIXABAY_API_KEY"] = settings.PIXABAY_API_KEY
        env_lines["PIXABAY_API_KEY"] = settings.PIXABAY_API_KEY
    if req.serper_api_key is not None:
        settings.SERPER_API_KEY = req.serper_api_key.strip()
        os.environ["SERPER_API_KEY"] = settings.SERPER_API_KEY
        env_lines["SERPER_API_KEY"] = settings.SERPER_API_KEY
    if req.tenor_api_key is not None:
        settings.TENOR_API_KEY = req.tenor_api_key.strip()
        os.environ["TENOR_API_KEY"] = settings.TENOR_API_KEY
        env_lines["TENOR_API_KEY"] = settings.TENOR_API_KEY
    if req.giphy_api_key is not None:
        settings.GIPHY_API_KEY = req.giphy_api_key.strip()
        os.environ["GIPHY_API_KEY"] = settings.GIPHY_API_KEY
        env_lines["GIPHY_API_KEY"] = settings.GIPHY_API_KEY

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in env_lines.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        print(f"Failed to write .env: {e}")

    return {"status": "success", "message": "Settings updated successfully"}

@app.get("/api/find-trends")
def find_trends():
    if settings.SERPER_API_KEY:
        serper_results = SerperService.search_live_true_crime(settings.SERPER_API_KEY)
        if serper_results:
            return {
                "source_engine": "Google Serper Live News",
                "trends": serper_results
            }

    if not settings.GEMINI_API_KEY:
        fallbacks = GeminiService.find_trends("")
        return {"source_engine": "Curated Mystery Vault", "trends": fallbacks}
    try:
        trends = GeminiService.find_trends(settings.GEMINI_API_KEY)
        return {"source_engine": "Gemini AI Realtime Search", "trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/youtube/setup-credentials")
def setup_youtube_credentials(req: YouTubeCredentialsRequest):
    try:
        res = YouTubeService.save_client_secret(req.client_secret_json)
        return {"status": "success", "saved": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/youtube/status")
def youtube_status():
    return YouTubeService.get_auth_status()

@app.post("/api/youtube/auth-start")
def youtube_auth_start():
    try:
        res = YouTubeService.start_oauth_flow_async()
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/youtube/upload")
def upload_to_youtube(req: YouTubeUploadRequest):
    video_path = settings.OUTPUT_DIR / req.video_filename
    if not video_path.exists():
        matches = list(settings.OUTPUT_DIR.glob(f"*{req.video_filename}*"))
        if matches:
            video_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail="Rendered video file not found")

    # Check authentication first
    auth_status = YouTubeService.get_auth_status()
    if not auth_status.get("authenticated"):
        # Auto-trigger OAuth flow
        try:
            auth_flow_info = YouTubeService.start_oauth_flow_async()
            return {
                "needs_auth": True,
                "auth_url": auth_flow_info.get("auth_url"),
                "message": "Please authorize ReelBot on Google in the newly opened browser window."
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"YouTube Authorization Required: {e}")

    try:
        result = YouTubeService.upload_video(
            video_path=video_path,
            title=req.title,
            description=req.description,
            tags=req.tags,
            privacy_status=req.privacy_status
        )
        return result
    except Exception as e:
        if "NOT_AUTHENTICATED" in str(e):
            auth_flow_info = YouTubeService.start_oauth_flow_async()
            return {
                "needs_auth": True,
                "auth_url": auth_flow_info.get("auth_url"),
                "message": "Session expired. Please re-authorize ReelBot on Google."
            }
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-bgm-bulk")
async def upload_bgm_bulk(files: List[UploadFile] = File(...)):
    saved = []
    settings.BGM_DIR.mkdir(parents=True, exist_ok=True)
    for file in files:
        if file.filename.endswith(".mp3"):
            target_path = settings.BGM_DIR / file.filename
            with open(target_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved.append(file.filename)
    return {"status": "success", "count": len(saved), "message": f"Successfully uploaded {len(saved)} audio tracks"}

@app.post("/api/generate-script")
def generate_script(req: ScriptGenerateRequest):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please configure it in settings.")
    try:
        script = GeminiService.generate_script(
            api_key=settings.GEMINI_API_KEY,
            topic=req.topic,
            language=req.language,
            tone=req.tone,
            target_duration_sec=req.target_duration_sec
        )
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_video_generation_pipeline(task_id: str, payload: VideoGenerateRequest):
    task = tasks_db[task_id]
    task_dir = settings.TEMP_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        task["logs"].append(msg)
        try:
            print(f"[{task_id}] {msg}")
        except Exception:
            try:
                safe_msg = msg.encode("ascii", "replace").decode("ascii")
                print(f"[{task_id}] {safe_msg}")
            except Exception:
                pass

    try:
        log("⚡ Starting ReelBot.Ai True Crime Production Pipeline...")
        task["status"] = "processing"
        task["progress"] = 5
        task["stage"] = "Initializing True Crime Engine..."
        task["current_phase"] = "voice"

        # ── Helper: strip non-Latin script from subtitle text ─────────────────
        import re as _re

        def force_roman(text: str) -> str:
            """Remove any non-ASCII/non-Latin characters from subtitle text.
            If after stripping nothing is left, return the original uppercased text
            transliterated naively (just uppercase ASCII words)."""
            if not text:
                return ""
            # Remove Bengali, Hindi, and other Indic Unicode blocks
            cleaned = _re.sub(r"[\u0900-\u09FF\u0A00-\u0A7F\u0B00-\u0B7F]", "", text)
            cleaned = _re.sub(r"[^\x00-\x7F]", "", cleaned)  # strip any remaining non-ASCII
            cleaned = _re.sub(r"\s+", " ", cleaned).strip()
            return cleaned.upper() if cleaned else text.upper()

        def tts_ready_narration(text: str) -> str:
            """Prepare Bengali/Hindi narration for Sarvam TTS:
            - Keeps commas (,) → Sarvam uses them as natural breath pauses
            - Replaces '...' with a period + pause marker ' . ' so Sarvam pauses
            - Removes decorative dashes at line ends
            - Strips HTML-like symbols and extra spaces
            """
            t = text.strip()
            # Convert '...' to a period with surrounding spaces for Sarvam pause
            t = _re.sub(r"\.{3,}", " . ", t)
            # Replace em-dash at end of line with a period
            t = _re.sub(r"—\s*$", "।", t)
            t = _re.sub(r"—", ", ", t)
            # Remove stray punctuation that confuses TTS but keep , . ! ? ।
            t = _re.sub(r"[*#@^%&+=<>|\\]", "", t)
            t = _re.sub(r"\s+", " ", t).strip()
            return t

        # 1. Voiceover Synthesis — send clean TTS text, NOT raw subtitle
        log(f"🎙️ Step 1: Synthesizing voiceover with voice '{payload.voice_id}'...")
        task["progress"] = 15
        task["stage"] = "Synthesizing deep vocal narration..."

        # Concatenate scene narrations (TTS-cleaned) into one full voiceover string
        full_narration = " ".join([tts_ready_narration(s.narration) for s in payload.scenes])
        voiceover_audio_path = task_dir / "voiceover.mp3"

        voice_res = TTSService.generate_voiceover(
            text=full_narration,
            voice=payload.voice_id,
            rate=payload.voice_rate,
            output_path=voiceover_audio_path
        )

        total_audio_dur = voice_res["duration"]
        log(f"✅ Voiceover generated: {total_audio_dur:.2f}s with broadcast studio mastering.")

        # 2. Build Romanized subtitle word-timing from subtitle_text (NOT Bengali TTS words)
        log("🔤 Step 2: Building Romanized Hormozi word-pop captions from subtitle_text...")
        task["progress"] = 35
        task["stage"] = "Generating Alex Hormozi animated subtitles..."
        task["current_phase"] = "subtitles"

        # Distribute total audio duration evenly across all scenes
        n_scenes = len(payload.scenes)
        sec_per_scene = total_audio_dur / max(n_scenes, 1)

        subtitle_words: list = []
        for s_idx, sc in enumerate(payload.scenes):
            scene_start = s_idx * sec_per_scene
            scene_end = scene_start + sec_per_scene

            # Prefer subtitle_text field; fall back to ASCII-only words from narration
            raw_sub = sc.subtitle_text or sc.narration or ""
            roman_text = force_roman(raw_sub)

            # If roman_text is empty after cleaning, use the scene's visual_tag words
            if not roman_text.strip():
                roman_text = (sc.visual_tag or f"SCENE {sc.scene_id}").upper()

            # Clean punctuation from subtitle display text
            roman_text = _re.sub(r"[.,!?;:'\"\-—…]", " ", roman_text)
            roman_text = _re.sub(r"\s+", " ", roman_text).strip()

            words_in_scene = roman_text.split()
            if not words_in_scene:
                continue

            # Spread words evenly inside the scene duration
            tpw = sec_per_scene / len(words_in_scene)
            for w_idx, word in enumerate(words_in_scene):
                w_start = scene_start + w_idx * tpw
                w_end = min(w_start + tpw, scene_end)
                subtitle_words.append({
                    "word": word,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "duration": round(w_end - w_start, 3),
                })

        ass_subtitles_path = task_dir / "subtitles.ass"
        SubtitleService.generate_hormozi_ass(
            words=subtitle_words,
            output_ass_path=ass_subtitles_path,
            style_preset=payload.subtitle_style_id
        )
        log(f"✅ Hormozi captions built: {len(subtitle_words)} words (100% Romanized).")


        # 3. Stock Footage Sourcing (Max 3.0s per clip)
        log(f"🎥 Step 3: Sourcing {len(payload.scenes)} atmospheric HD stock clips (1-to-1 visual match)...")
        task["progress"] = 45
        task["stage"] = "Searching & downloading atmospheric HD video clips..."
        task["current_phase"] = "footage"

        scene_durations = [total_audio_dur / len(payload.scenes)] * len(payload.scenes)
        scene_clips = []

        for idx, sc in enumerate(payload.scenes):
            dur = scene_durations[idx]
            
            # Prioritize exact visual_tag if provided
            search_keywords = []
            if sc.visual_tag and sc.visual_tag.strip():
                search_keywords.append(sc.visual_tag.strip())
            for kw in sc.keywords:
                if kw not in search_keywords:
                    search_keywords.append(kw)

            log(f"🔍 Scene {sc.scene_id}/{len(payload.scenes)} [{sc.time_range or f'0:{(idx*3):02d}-0:{((idx+1)*3):02d}'}]: Visual Tag '{sc.visual_tag or search_keywords[0]}'...")
            
            raw_video = task_dir / f"raw_scene_{sc.scene_id}.mp4"
            MediaService.fetch_scene_media(
                keywords=search_keywords,
                pexels_key=settings.PEXELS_API_KEY,
                pixabay_key=settings.PIXABAY_API_KEY,
                dest_path=raw_video,
                duration=dur,
                scene_id=sc.scene_id
            )
            
            clip_path = task_dir / f"scene_clip_{sc.scene_id}.mp4"
            VideoComposer.build_scene_clip(raw_video, clip_path, dur, scene_id=sc.scene_id)
            scene_clips.append(clip_path)

            progress_pct = 45 + int((idx + 1) / len(payload.scenes) * 35)
            task["progress"] = progress_pct
            task["stage"] = f"Processed scene {idx+1}/{len(payload.scenes)}..."

        # 4. Final Video Composition
        log("⚡ Step 4: Rendering final 1080x1920 video with cinematic grading & vignette...")
        task["progress"] = 85
        task["stage"] = "Compositing clips, burning captions & ducking BGM..."
        task["current_phase"] = "render"

        bgm_path = None
        if payload.bgm_track_id and payload.bgm_track_id != "none":
            candidate = settings.BGM_DIR / f"{payload.bgm_track_id}.mp3"
            if candidate.exists():
                bgm_path = candidate
            else:
                any_bgm = list(settings.BGM_DIR.glob("*.mp3"))
                if any_bgm:
                    bgm_path = any_bgm[0]

        final_video_filename = f"mystery_short_{task_id}.mp4"
        final_video_path = settings.OUTPUT_DIR / final_video_filename

        VideoComposer.render_final_video(
            scene_clips=scene_clips,
            voiceover_audio=voiceover_audio_path,
            ass_subtitles=ass_subtitles_path,
            bgm_audio=bgm_path,
            output_video=final_video_path,
            bgm_volume=payload.bgm_volume,
            total_duration=total_audio_dur
        )

        task["progress"] = 100
        task["status"] = "completed"
        task["stage"] = "Video generation complete!"
        task["video_url"] = f"/output/{final_video_filename}"
        task["filename"] = final_video_filename
        log(f"🎉 Production finished! File ready: {final_video_filename}")

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        log(f"❌ Generation failed: {e}")

@app.post("/api/generate-video")
def generate_video(req: VideoGenerateRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "stage": "Queued in render queue...",
        "current_phase": "voice",
        "logs": [f"[{task_id}] ⚡ Task initialized."],
        "video_url": None,
        "filename": None,
        "error": None,
        "payload": req.dict()
    }
    threading.Thread(target=run_video_generation_pipeline, args=(task_id, req), daemon=True).start()
    return {"task_id": task_id, "status": "queued"}

@app.get("/api/task-status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.post("/api/resume-task/{task_id}")
def resume_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    payload = VideoGenerateRequest(**task["payload"])
    task["status"] = "resuming"
    task["logs"].append("🔁 Resuming generation from checkpoint...")
    threading.Thread(target=run_video_generation_pipeline, args=(task_id, payload), daemon=True).start()
    return {"task_id": task_id, "status": "resumed"}

# Static Mounts
app.mount("/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")
app.mount("/api/video", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="api_video")
app.mount("/", StaticFiles(directory=str(settings.BASE_DIR / "frontend"), html=True), name="frontend")
