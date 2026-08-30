import os
import time
import uuid
import shutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.services.gemini_service import GeminiService
from backend.services.tts_service import TTSService
from backend.services.media_service import MediaService
from backend.services.subtitle_service import SubtitleService
from backend.services.video_composer import VideoComposer

app = FastAPI(title="ReelBot.Ai (Beta)", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks_store: Dict[str, Dict[str, Any]] = {}
tasks_payload_cache: Dict[str, Any] = {}

settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
settings.BGM_DIR.mkdir(parents=True, exist_ok=True)
settings.FONTS_DIR.mkdir(parents=True, exist_ok=True)

class ConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

class ScriptGenerateRequest(BaseModel):
    topic: str
    language: str = "English"
    tone: str = "High Energy / Viral"
    target_duration_sec: int = 60
    gemini_api_key: Optional[str] = None

class SceneItem(BaseModel):
    scene_id: int
    narration: str
    subtitle_text: Optional[str] = None
    keywords: List[str]
    suggested_emoji: Optional[str] = "🎬"
    estimated_seconds: Optional[float] = 3.0

class VideoGenerateRequest(BaseModel):
    title: str = "Viral Short"
    scenes: List[SceneItem]
    voice_id: str = "hi-IN-MadhurNeural"
    voice_rate: str = "+35%"
    subtitle_style_id: str = "hormozi_yellow"
    bgm_track_id: str = "energetic_beats"
    bgm_volume: float = 0.15
    gemini_api_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

def add_task_log(task_id: str, message: str):
    if task_id in tasks_store:
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        tasks_store[task_id]["logs"].append(entry)

def run_video_pipeline(task_id: str, payload: VideoGenerateRequest):
    try:
        task_temp_dir = settings.TEMP_DIR / task_id
        task_temp_dir.mkdir(parents=True, exist_ok=True)

        tasks_store[task_id]["status"] = "processing"
        tasks_store[task_id]["current_phase"] = "voice"

        audio_output_path = task_temp_dir / f"voiceover_{task_id}.mp3"
        ass_path = task_temp_dir / f"subtitles_{task_id}.ass"

        # 1. Voiceover Stage (with Cache / Resume Support)
        if audio_output_path.exists() and audio_output_path.stat().st_size > 1000:
            add_task_log(task_id, f"⚡ Resumed: Found cached voiceover audio ({audio_output_path.name}).")
            import soundfile as sf
            try:
                with sf.SoundFile(str(audio_output_path)) as sfile:
                    total_audio_duration = len(sfile) / sfile.samplerate
            except Exception:
                total_audio_duration = 30.0
        else:
            tasks_store[task_id]["progress"] = 15
            tasks_store[task_id]["stage"] = "Synthesizing studio voiceover with broadcast mastering EQ..."
            add_task_log(task_id, f"🎙️ Generating voiceover using '{payload.voice_id}' at speed '{payload.voice_rate}'...")

            full_narration_text = " ".join([s.narration.strip() for s in payload.scenes])
            voice_res = TTSService.generate_voiceover(
                text=full_narration_text,
                voice=payload.voice_id,
                rate=payload.voice_rate,
                output_path=audio_output_path
            )
            total_audio_duration = voice_res["duration"]
            add_task_log(task_id, f"✅ Voiceover audio synthesized: {total_audio_duration:.2f}s total duration.")

        # Calculate scene durations dynamically so cuts match voiceover 100%
        scene_durations = []
        scene_word_counts = [len(s.narration.strip().split()) for s in payload.scenes]
        total_words = sum(scene_word_counts)
        if total_words > 0:
            for count in scene_word_counts:
                dur = (count / total_words) * total_audio_duration
                scene_durations.append(dur)
        else:
            default_dur = total_audio_duration / max(len(payload.scenes), 1)
            scene_durations = [default_dur] * len(payload.scenes)

        # 2. Subtitles Stage (with Cache / Resume Support)
        tasks_store[task_id]["progress"] = 35
        tasks_store[task_id]["current_phase"] = "subtitles"
        tasks_store[task_id]["stage"] = "Generating Alex Hormozi animated ASS captions..."

        if not (ass_path.exists() and ass_path.stat().st_size > 100):
            add_task_log(task_id, "🔤 Computing word-by-word timestamp boundaries for Latin uppercase subtitles...")
            current_time_cursor = 0.0
            sub_words_timing = []
            for idx, scene in enumerate(payload.scenes):
                sc_dur = scene_durations[idx]
                sub_text = (scene.subtitle_text or scene.narration).strip()
                sub_raw_words = sub_text.split()
                if not sub_raw_words:
                    current_time_cursor += sc_dur
                    continue

                time_per_word = sc_dur / max(len(sub_raw_words), 1)
                for w_idx, w_text in enumerate(sub_raw_words):
                    w_start = current_time_cursor + (w_idx * time_per_word)
                    w_end = w_start + time_per_word
                    sub_words_timing.append({
                        "word": w_text.upper(),
                        "start": round(w_start, 3),
                        "end": round(w_end, 3),
                        "duration": round(time_per_word, 3)
                    })
                current_time_cursor += sc_dur

            SubtitleService.generate_hormozi_ass(
                words=sub_words_timing,
                output_ass_path=ass_path,
                style_preset=payload.subtitle_style_id,
                video_width=settings.VIDEO_WIDTH,
                video_height=settings.VIDEO_HEIGHT
            )
            add_task_log(task_id, f"🔥 Alex Hormozi animated captions generated with '{payload.subtitle_style_id}' style.")
        else:
            add_task_log(task_id, "⚡ Resumed: Found cached ASS subtitles.")

        # 3. Source HD Stock Footage (100% exact matching with Cache / Resume per scene)
        tasks_store[task_id]["progress"] = 45
        tasks_store[task_id]["current_phase"] = "footage"
        tasks_store[task_id]["stage"] = "Sourcing HD 9:16 vertical stock footage from Pexels & Pixabay..."

        pexels_key = payload.pexels_api_key or settings.PEXELS_API_KEY
        pixabay_key = payload.pixabay_api_key or settings.PIXABAY_API_KEY

        normalized_clips: List[Path] = []
        for idx, scene in enumerate(payload.scenes):
            scene_duration = max(scene_durations[idx], 1.5)
            norm_clip_path = task_temp_dir / f"norm_scene_{idx+1}.mp4"

            # Check if this scene clip is already cached on disk
            if norm_clip_path.exists() and norm_clip_path.stat().st_size > 5000:
                normalized_clips.append(norm_clip_path)
                add_task_log(task_id, f"⚡ Resumed: Scene {idx+1}/{len(payload.scenes)} clip cached.")
            else:
                tasks_store[task_id]["stage"] = f"Sourcing scene {idx+1}/{len(payload.scenes)}: {scene.keywords[0]}..."
                add_task_log(task_id, f"🎥 Scene {idx+1}/{len(payload.scenes)}: Sourcing HD clip for '{scene.keywords[0]}'...")

                raw_media_path = task_temp_dir / f"raw_scene_{idx+1}.mp4"
                MediaService.fetch_scene_media(
                    keywords=scene.keywords,
                    pexels_key=pexels_key,
                    pixabay_key=pixabay_key,
                    dest_path=raw_media_path,
                    duration=scene_duration,
                    scene_id=idx
                )

                VideoComposer.build_scene_clip(raw_media_path, norm_clip_path, scene_duration)
                normalized_clips.append(norm_clip_path)
                add_task_log(task_id, f"✅ Scene {idx+1}/{len(payload.scenes)} clip downloaded & normalized.")

            progress_val = 45 + int((idx + 1) / len(payload.scenes) * 35)
            tasks_store[task_id]["progress"] = progress_val

        # 4. Multi-Threaded FFmpeg Compositing & Audio Mixing
        tasks_store[task_id]["progress"] = 82
        tasks_store[task_id]["current_phase"] = "render"
        tasks_store[task_id]["stage"] = "Multi-threaded FFmpeg rendering with ducked BGM and burned captions..."
        add_task_log(task_id, "⚡ Starting multi-threaded FFmpeg compositing with smart BGM fade-out...")

        bgm_file = None
        if payload.bgm_track_id != "none":
            candidate_bgm = settings.BGM_DIR / f"{payload.bgm_track_id}.mp3"
            if candidate_bgm.exists():
                bgm_file = candidate_bgm
            else:
                all_bgm = list(settings.BGM_DIR.glob("*.mp3"))
                if all_bgm:
                    bgm_file = all_bgm[0]

        final_video_name = f"short_{task_id}.mp4"
        final_video_path = settings.OUTPUTS_DIR / final_video_name

        VideoComposer.render_final_video(
            scene_clips=normalized_clips,
            voiceover_audio=audio_output_path,
            ass_subtitles=ass_path,
            bgm_audio=bgm_file,
            output_video=final_video_path,
            bgm_volume=payload.bgm_volume,
            total_duration=total_audio_duration
        )

        try:
            shutil.rmtree(task_temp_dir, ignore_errors=True)
        except Exception:
            pass

        file_size_mb = final_video_path.stat().st_size / (1024 * 1024)
        add_task_log(task_id, f"🎉 1080x1920 Full HD Video ready! Output size: {file_size_mb:.2f} MB")

        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["progress"] = 100
        tasks_store[task_id]["stage"] = "🎉 Video Generation Complete!"
        tasks_store[task_id]["video_url"] = f"/api/videos/{final_video_name}"
        tasks_store[task_id]["filename"] = final_video_name

    except Exception as e:
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["error"] = str(e)
        tasks_store[task_id]["stage"] = f"Error: {str(e)}"
        add_task_log(task_id, f"❌ Pipeline stopped: {str(e)}")
        print(f"Task {task_id} error: {e}")

@app.get("/api/config")
def get_config():
    bgm_tracks = []
    for f in sorted(settings.BGM_DIR.glob("*.mp3")):
        bgm_tracks.append({"id": f.stem, "name": f.stem.replace("_", " ").title()})
    return {
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_pexels_key": bool(settings.PEXELS_API_KEY),
        "has_pixabay_key": bool(settings.PIXABAY_API_KEY),
        "gemini_api_key_masked": f"{settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:]}" if settings.GEMINI_API_KEY else "",
        "pexels_api_key_masked": f"{settings.PEXELS_API_KEY[:4]}...{settings.PEXELS_API_KEY[-4:]}" if settings.PEXELS_API_KEY else "",
        "pixabay_api_key_masked": f"{settings.PIXABAY_API_KEY[:4]}...{settings.PIXABAY_API_KEY[-4:]}" if settings.PIXABAY_API_KEY else "",
        "voices": settings.VOICE_PRESETS,
        "subtitle_styles": settings.SUBTITLE_STYLES,
        "bgm_tracks": bgm_tracks
    }

@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    if req.gemini_api_key is not None:
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
    if req.pexels_api_key is not None:
        settings.PEXELS_API_KEY = req.pexels_api_key.strip()
    if req.pixabay_api_key is not None:
        settings.PIXABAY_API_KEY = req.pixabay_api_key.strip()

    env_content = f"GEMINI_API_KEY={settings.GEMINI_API_KEY}\nPEXELS_API_KEY={settings.PEXELS_API_KEY}\nPIXABAY_API_KEY={settings.PIXABAY_API_KEY}\n"
    (settings.BASE_DIR / ".env").write_text(env_content, encoding="utf-8")
    return {"message": "Settings updated successfully"}

@app.get("/api/find-trends")
def get_trends():
    try:
        trends = GeminiService.find_trends(api_key=settings.GEMINI_API_KEY)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-script")
def generate_script(req: ScriptGenerateRequest):
    api_key = req.gemini_api_key or settings.GEMINI_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please configure it in settings.")
    try:
        script = GeminiService.generate_script(
            api_key=api_key,
            topic=req.topic,
            language=req.language,
            tone=req.tone,
            target_duration_sec=req.target_duration_sec
        )
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-video")
def generate_video(req: VideoGenerateRequest):
    task_id = str(uuid.uuid4())[:8]
    tasks_payload_cache[task_id] = req
    tasks_store[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "stage": "Video task queued...",
        "current_phase": "voice",
        "logs": [],
        "error": None,
        "video_url": None
    }
    
    t = threading.Thread(target=run_video_pipeline, args=(task_id, req), daemon=True)
    t.start()
    
    return {"task_id": task_id, "message": "Video generation started"}

@app.post("/api/resume-task/{task_id}")
def resume_task(task_id: str):
    if task_id not in tasks_payload_cache:
        raise HTTPException(status_code=404, detail="Task payload not cached")
    
    req = tasks_payload_cache[task_id]
    tasks_store[task_id]["status"] = "queued"
    tasks_store[task_id]["error"] = None
    tasks_store[task_id]["stage"] = "Resuming video pipeline from cached state..."
    add_task_log(task_id, "🔁 Resuming pipeline execution from last valid checkpoint...")

    t = threading.Thread(target=run_video_pipeline, args=(task_id, req), daemon=True)
    t.start()

    return {"task_id": task_id, "message": "Task resumed successfully"}

@app.get("/api/task-status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_store[task_id]

@app.get("/api/videos/{filename}")
def get_video_file(filename: str):
    video_path = settings.OUTPUTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(path=str(video_path), media_type="video/mp4", filename=filename)

@app.post("/api/upload-bgm-bulk")
async def upload_bgm_bulk(files: List[UploadFile] = File(...)):
    saved_count = 0
    for file in files:
        if file.filename and file.filename.lower().endswith(".mp3"):
            dest = settings.BGM_DIR / file.filename
            with open(dest, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_count += 1
    return {"message": f"Successfully uploaded {saved_count} music tracks", "count": saved_count}

frontend_path = settings.BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
