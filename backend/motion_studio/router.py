import uuid
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.config import settings
from backend.services.tts_service import TTSService
from backend.services.subtitle_service import SubtitleService
from backend.motion_studio.gif_service import GifService
from backend.motion_studio.motion_composer import MotionComposer
from backend.motion_studio.motion_script_service import MotionScriptService

motion_router = APIRouter(prefix="/api/motion", tags=["Motion Studio"])

class MotionScriptGenerateRequest(BaseModel):
    topic: str
    language: Optional[str] = "Bengali"
    tone: Optional[str] = "Funny / Entertainment"
    target_duration_sec: Optional[int] = 30

class GifSearchRequest(BaseModel):
    query: str
    style_preset: Optional[str] = "meme"
    limit: Optional[int] = 6

class MotionSceneInput(BaseModel):
    scene_id: int
    time_range: Optional[str] = "0:00-0:03"
    visual_tag: Optional[str] = None
    narration: str
    subtitle_text: Optional[str] = None
    keywords: List[str]
    suggested_emoji: Optional[str] = "👾"
    estimated_seconds: Optional[float] = 3.0

class MotionVideoGenerateRequest(BaseModel):
    title: str
    scenes: List[MotionSceneInput]
    voice_id: str = "sarvam:shreya"
    voice_rate: str = "+10%"
    subtitle_style_id: str = "hormozi_yellow"
    style_preset: str = "meme"  # 'meme', 'anime', 'dark_noir', 'graphic'
    sfx_intensity: str = "cinematic"  # 'cinematic', 'minimal', 'none'
    bgm_track_id: Optional[str] = "default"
    bgm_volume: float = 0.15

@motion_router.get("/random-hook")
def get_random_motion_hook(category: Optional[str] = "all"):
    """Returns an instant viral hook topic."""
    try:
        hook = MotionScriptService.get_random_viral_hook(category=category or "all")
        return hook
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@motion_router.get("/find-trends")
def find_motion_trends(category: Optional[str] = "all"):
    """Returns viral funny, entertainment, and mind-blowing fun facts."""
    try:
        trends = MotionScriptService.find_motion_trends(category=category or "all")
        return {
            "source_engine": "ReelBot Motion Viral Entertainment Trends",
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@motion_router.post("/generate-script")
def generate_motion_script(req: MotionScriptGenerateRequest):
    """Generates entertaining short scripts with GIF & meme visual tags."""
    try:
        script = MotionScriptService.generate_motion_script(
            topic=req.topic,
            language=req.language or "Bengali",
            tone=req.tone or "Funny / Entertainment",
            target_duration_sec=req.target_duration_sec or 30
        )
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@motion_router.post("/search-gifs")
def search_gifs(req: GifSearchRequest):
    try:
        results = GifService.search_motion_clips(
            query=req.query,
            style_preset=req.style_preset or "meme",
            limit=req.limit or 6
        )
        return {"query": req.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_motion_generation_pipeline(task_id: str, payload: MotionVideoGenerateRequest, tasks_db: Dict[str, Any]):
    task = tasks_db[task_id]
    task_dir = settings.TEMP_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        task["logs"].append(msg)
        try:
            print(f"[{task_id}][Motion] {msg}")
        except Exception:
            try:
                safe_msg = msg.encode("ascii", "replace").decode("ascii")
                print(f"[{task_id}][Motion] {safe_msg}")
            except Exception:
                pass

    try:
        log("👾 Initializing ReelBot Motion Studio Engine...")
        task["status"] = "processing"
        task["progress"] = 5
        task["stage"] = "Initializing Motion Studio..."
        task["current_phase"] = "voice"

        import re as _re

        def force_roman(text: str) -> str:
            if not text:
                return ""
            cleaned = _re.sub(r"[\u0900-\u09FF\u0A00-\u0A7F\u0B00-\u0B7F]", "", text)
            cleaned = _re.sub(r"[^\x00-\x7F]", "", cleaned)
            cleaned = _re.sub(r"\s+", " ", cleaned).strip()
            return cleaned.upper() if cleaned else text.upper()

        def tts_ready_narration(text: str) -> str:
            t = text.strip()
            t = _re.sub(r"\.{3,}", " . ", t)
            t = _re.sub(r"—\s*$", "।", t)
            t = _re.sub(r"—", ", ", t)
            t = _re.sub(r"[*#@^%&+=<>|\\]", "", t)
            t = _re.sub(r"\s+", " ", t).strip()
            return t

        # 1. Voiceover Synthesis
        log(f"🎙️ Step 1: Synthesizing voiceover with voice '{payload.voice_id}'...")
        task["progress"] = 15
        task["stage"] = "Synthesizing vocal narration..."

        full_narration = " ".join([tts_ready_narration(s.narration) for s in payload.scenes])
        voiceover_audio_path = task_dir / "voiceover.mp3"

        voice_res = TTSService.generate_voiceover(
            text=full_narration,
            voice=payload.voice_id,
            rate=payload.voice_rate,
            output_path=voiceover_audio_path
        )

        total_audio_dur = voice_res["duration"]
        log(f"✅ Voiceover generated: {total_audio_dur:.2f}s.")

        # 2. Hormozi ASS Subtitles
        log("🔤 Step 2: Building Romanized Hormozi word-pop captions...")
        task["progress"] = 30
        task["stage"] = "Generating animated captions..."
        task["current_phase"] = "subtitles"

        n_scenes = len(payload.scenes)
        sec_per_scene = total_audio_dur / max(n_scenes, 1)

        subtitle_words: list = []
        scene_durations: list = [sec_per_scene] * n_scenes

        for s_idx, sc in enumerate(payload.scenes):
            scene_start = s_idx * sec_per_scene
            scene_end = scene_start + sec_per_scene

            raw_sub = sc.subtitle_text or sc.narration or ""
            roman_text = force_roman(raw_sub)
            if not roman_text.strip():
                roman_text = (sc.visual_tag or f"SCENE {sc.scene_id}").upper()

            roman_text = _re.sub(r"[.,!?;:'\"\-—…]", " ", roman_text)
            roman_text = _re.sub(r"\s+", " ", roman_text).strip()
            words_in_scene = roman_text.split()
            if not words_in_scene:
                continue

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
        log("✅ Burned Hormozi subtitles.")

        # 3. Sourcing Animated GIFs / MP4 Motion Loops
        log(f"👾 Step 3: Sourcing {len(payload.scenes)} Animated Motion Clips ({payload.style_preset} style)...")
        task["progress"] = 45
        task["stage"] = "Searching & downloading animated motion loops..."
        task["current_phase"] = "footage"

        scene_clips = []
        used_clip_urls: set = set()
        for idx, sc in enumerate(payload.scenes):
            dur = sec_per_scene
            search_keywords = []
            if sc.visual_tag and sc.visual_tag.strip():
                search_keywords.append(sc.visual_tag.strip())
            for kw in sc.keywords:
                if kw not in search_keywords:
                    search_keywords.append(kw)

            log(f"🔍 Scene {sc.scene_id}/{len(payload.scenes)}: Motion Tag '{sc.visual_tag or search_keywords[0]}'...")
            raw_media = task_dir / f"raw_motion_{sc.scene_id}.mp4"

            GifService.download_motion_clip(
                keywords=search_keywords,
                dest_path=raw_media,
                style_preset=payload.style_preset,
                scene_id=sc.scene_id,
                used_urls=used_clip_urls,
                narration_context=sc.narration
            )

            clip_path = task_dir / f"motion_clip_{sc.scene_id}.mp4"
            MotionComposer.build_motion_scene_clip(raw_media, clip_path, dur, scene_id=sc.scene_id)
            scene_clips.append(clip_path)

            progress_pct = 45 + int((idx + 1) / len(payload.scenes) * 35)
            task["progress"] = progress_pct
            task["stage"] = f"Processed motion scene {idx+1}/{len(payload.scenes)}..."

        # 4. Final Video Composition with Dual-Layer Blur, SFX & Auto-Ducked BGM
        log(f"⚡ Step 4: Compositing dual-layer 9:16 video with {payload.sfx_intensity.upper()} SFX & ducked BGM...")
        task["progress"] = 85
        task["stage"] = "Mixing audio, whooshes, ducking BGM & rendering..."
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

        final_video_filename = f"motion_short_{task_id}.mp4"
        final_video_path = settings.OUTPUT_DIR / final_video_filename

        MotionComposer.render_final_motion_video(
            scene_clips=scene_clips,
            voiceover_audio=voiceover_audio_path,
            ass_subtitles=ass_subtitles_path,
            bgm_audio=bgm_path,
            output_video=final_video_path,
            scene_durations=scene_durations,
            bgm_volume=payload.bgm_volume,
            sfx_intensity=payload.sfx_intensity,
            total_duration=total_audio_dur
        )

        # 5. Zero-Cache Auto Cleanup: purge temporary clips and scratch files
        try:
            import shutil
            shutil.rmtree(task_dir, ignore_errors=True)
            log("🧹 Auto-cleaned all temporary clips and scratch files (0 bytes cached).")
        except Exception:
            pass

        task["progress"] = 100
        task["status"] = "completed"
        task["stage"] = "Motion video generation complete!"
        task["video_url"] = f"/output/{final_video_filename}"
        task["filename"] = final_video_filename
        log(f"🎉 SUCCESS! Rendered 1080x1920 Motion Video -> {final_video_filename}")

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        log(f"❌ Motion Generation failed: {e}")
        import traceback
        traceback.print_exc()

@motion_router.post("/generate-video")
def generate_motion_video(payload: MotionVideoGenerateRequest):
    from backend.app import tasks_db

    task_id = uuid.uuid4().hex[:8]
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
        "stage": "Queued in ReelBot Motion Studio...",
        "logs": [f"⚡ Task {task_id} initialized in ReelBot Motion Studio."],
        "video_url": None,
        "error": None,
        "is_motion": True
    }

    t = threading.Thread(
        target=run_motion_generation_pipeline,
        args=(task_id, payload, tasks_db),
        daemon=True
    )
    t.start()

    return {"task_id": task_id, "status": "queued"}
