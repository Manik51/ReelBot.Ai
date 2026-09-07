import os
import re
import sys
import uuid
import math
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable

from backend.config import settings
from backend.services.tts_service import TTSService
from backend.services.subtitle_service import SubtitleService
from backend.documentary_studio.docu_asset_service import DocuAssetService
from backend.documentary_studio.docu_sfx_service import DocuSfxService

class DocuComposer:
    """
    Dedicated 2.5D Motion Graphics Compositor for Documentary & Business Analysis (60s).
    Renders 5 modular visual metaphors, burns Hormozi ASS subtitles, and mixes multi-track SFX audio.
    """

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30

    @classmethod
    def render_documentary_video(
        cls,
        storyboard: Dict[str, Any],
        voice_id: str,
        voice_speed: str = "+0%",
        subtitle_color: str = "yellow",
        font_name: str = "Space Grotesk",
        visual_theme: str = "dark_slate",
        bgm_id: Optional[str] = "dark_investigative",
        bgm_volume: float = 0.15,
        sfx_volume: float = 0.60,
        sfx_enabled: bool = True,
        task_id: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        def log(msg: str):
            try:
                print(f"[DocuComposer] {msg}")
            except UnicodeEncodeError:
                print(f"[DocuComposer] {msg.encode('ascii', 'replace').decode('ascii')}")
            if log_callback:
                try:
                    log_callback(msg)
                except Exception:
                    pass

        work_dir = settings.TEMP_DIR / f"docu_render_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)
        final_output = settings.OUTPUT_DIR / f"docu_{uuid.uuid4().hex[:8]}.mp4"
        final_output.parent.mkdir(parents=True, exist_ok=True)

        try:
            beats = storyboard.get("beats", [])
            if not beats:
                raise ValueError("Storyboard contains no narrative beats.")

            # ── 1. GENERATE MASTER VOICEOVER ──────────────────────────────
            log("🎙️ Step 1/5: Synthesizing master documentary narration...")
            full_script_text = " ".join([b.get("narration", "").strip() for b in beats if b.get("narration")])
            voiceover_audio = work_dir / "voiceover.mp3"
            
            # TTSService handles Piper or Kokoro seamlessly
            v_path, word_timings = TTSService.generate_audio_with_timings(
                text=full_script_text,
                voice_id=voice_id,
                speed=voice_speed,
                output_path=voiceover_audio
            )
            total_audio_duration = cls._get_media_duration(voiceover_audio)
            log(f"🎙️ Master voiceover ready: {total_audio_duration:.2f}s across {len(beats)} beats.")

            # ── 1.1 EXACT DURATION ENFORCEMENT ───────────────────────────
            target_duration = float(storyboard.get("duration_sec", 60))
            if total_audio_duration > target_duration + 1.0:
                speed_factor = total_audio_duration / max(10.0, (target_duration - 0.5))
                speed_factor = min(1.22, max(1.02, speed_factor))
                log(f"⏱️ Clamping narration tempo by {speed_factor:.3f}x to guarantee exact {target_duration:.0f}s duration...")
                clamped_audio = work_dir / "voiceover_clamped.mp3"
                cmd_tempo = [
                    "ffmpeg", "-y",
                    "-i", str(voiceover_audio),
                    "-filter:a", f"atempo={speed_factor:.4f}",
                    "-c:a", "libmp3lame", "-q:a", "2",
                    str(clamped_audio)
                ]
                cls._run_ffmpeg(cmd_tempo)
                voiceover_audio = clamped_audio
                total_audio_duration = cls._get_media_duration(voiceover_audio)
                time_scale = 1.0 / speed_factor
                adjusted_timings = []
                for wt in word_timings:
                    adjusted_timings.append((
                        wt[0],
                        round(wt[1] * time_scale, 3),
                        round(wt[2] * time_scale, 3)
                    ))
                word_timings = adjusted_timings
                log(f"🎙️ Enforced voiceover duration: {total_audio_duration:.2f}s.")

            # ── 2. CALCULATE BEAT TIMINGS ─────────────────────────────────
            log("⏱️ Step 2/5: Synchronizing visual beat durations with narration...")
            beat_durations = cls._calculate_beat_durations(beats, total_audio_duration)
            sfx_cues = [b.get("sfx_cue", "whoosh") for b in beats]

            # ── 3. RENDER MODULAR 2.5D BEAT CLIPS ─────────────────────────
            log("🎬 Step 3/5: Rendering 2.5D modular visual metaphors...")
            clip_paths = []
            for idx, (beat, dur) in enumerate(zip(beats, beat_durations)):
                clip_out = work_dir / f"beat_{idx:03d}.mp4"
                log(f"   ↳ [Beat {idx+1}/{len(beats)}] Metaphor: {beat.get('metaphor', 'parallax_cutout')} ({dur:.2f}s)")
                cls._render_single_beat(beat, dur, visual_theme, clip_out, work_dir, idx)
                clip_paths.append(clip_out)

            # Concatenate beat clips
            log("🎞️ Stitching visual timeline into master 1080x1920 stream...")
            concat_list_file = work_dir / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for cp in clip_paths:
                    f.write(f"file '{cp.resolve().as_posix()}'\n")

            video_concat = work_dir / "video_concat.mp4"
            cmd_concat = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list_file),
                "-c", "copy", str(video_concat)
            ]
            cls._run_ffmpeg(cmd_concat)

            # ── 4. MULTI-TRACK AUDIO MIXING (VOICE + SFX + BGM) ───────────
            log("🔊 Step 4/5: Mixing multi-track documentary audio & cinematic SFX...")
            mixed_audio = work_dir / "mixed_audio.wav"
            bgm_file = cls._resolve_bgm_track(bgm_id)
            
            cmd_audio = DocuSfxService.build_audio_mix_command(
                voiceover_path=voiceover_audio,
                bgm_path=bgm_file,
                beat_durations=beat_durations,
                beat_sfx_cues=sfx_cues,
                output_audio_path=mixed_audio,
                bgm_volume=bgm_volume,
                sfx_volume=sfx_volume,
                sfx_enabled=sfx_enabled,
                total_duration=total_audio_duration
            )
            cls._run_ffmpeg(cmd_audio)

            # ── 5. HORMOZI 3-WORD SUBTITLES & FINAL MASTERING ─────────────
            log("🔥 Step 5/5: Generating Hormozi 3-word dynamic subtitles & mastering final MP4...")
            sub_ass_path = work_dir / "subtitles.ass"
            cls._generate_hormozi_subtitles(word_timings, sub_ass_path, subtitle_color, font_name)

            # Burn subtitles & finalize with unified 35mm film grain, moody contrast & vignette
            escaped_sub = str(sub_ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
            if "crime" in visual_theme.lower() or "noir" in visual_theme.lower():
                master_grade = "eq=contrast=1.18:brightness=-0.04:saturation=0.82,noise=alls=10:allf=t+u,vignette=PI/3.5"
            else:
                master_grade = "eq=contrast=1.12:brightness=-0.03:saturation=0.90,noise=alls=10:allf=t+u,vignette=PI/3.6"
            
            # Dynamic roaming SkullBot.Ai watermark
            from backend.services.watermark_service import WatermarkService
            watermark_img = WatermarkService.get_watermark_image()
            watermark_filter = WatermarkService.get_floating_overlay_filter(
                video_in_label="[graded]",
                watermark_in_idx=2,
                out_label="[vwater]"
            )

            filter_master = (
                f"[0:v]{master_grade}[graded];"
                f"{watermark_filter};"
                f"[vwater]subtitles='{escaped_sub}'[vfinal]"
            )
            cmd_master = [
                "ffmpeg", "-y",
                "-i", str(video_concat),
                "-i", str(mixed_audio),
                "-loop", "1", "-i", str(watermark_img),
                "-filter_complex", filter_master,
                "-map", "[vfinal]",
                "-map", "1:a",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(final_output)
            ]
            cls._run_ffmpeg(cmd_master)

            log(f"✅ Documentary short rendered successfully in 1080x1920: {final_output.name}")
            return final_output

        finally:
            # Clean up intermediate clips safely
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    # ── METAPHOR RENDER ROUTER ─────────────────────────────────────────────
    @classmethod
    def _render_single_beat(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        metaphor = beat.get("metaphor", "parallax_cutout")
        is_crime_mode = ("crime" in theme.lower() or "noir" in theme.lower() or 
                         any(m in metaphor for m in ["crime", "police", "dossier", "satellite"]))

        if metaphor == "crime_archival_drift":
            cls._render_crime_archival_drift(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "police_dossier_slam":
            cls._render_police_dossier_slam(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "satellite_map_zoom":
            cls._render_satellite_map_zoom(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "cinematic_broll" or metaphor == "cinematic_crime_broll":
            cls._render_cinematic_broll(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "newspaper_slam":
            cls._render_newspaper_slam(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif is_crime_mode:
            # ZERO CUTOUTS GUARANTEE: In True Crime mode, eliminate cutouts, cartoons, and split stickers
            cls._render_crime_archival_drift(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "archival_photo_pan":
            cls._render_archival_photo_pan(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "financial_stat":
            cls._render_financial_stat(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "split_comparison":
            cls._render_split_comparison(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "action_gif":
            cls._render_action_gif(beat, duration, theme, output_clip, work_dir, beat_idx)
        elif metaphor == "orbit_network":
            cls._render_orbit_network(beat, duration, theme, output_clip, work_dir, beat_idx)
        else:
            cls._render_parallax_cutout(beat, duration, theme, output_clip, work_dir, beat_idx)

    # ── METAPHOR: CRIME ARCHIVAL DRIFT (REAL EVIDENCE & MUGSHOT DRIFT) ─────
    @classmethod
    def _render_crime_archival_drift(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        asset_info = DocuAssetService.resolve_crime_asset(beat, theme, beat_idx)
        asset_type = asset_info.get("type", "image")
        asset_path = asset_info.get("path")
        
        hud_png = DocuAssetService.generate_crime_timestamp_overlay(
            chapter_stamp=beat.get("chapter_stamp", ""),
            location_subtext=beat.get("visual_subject") or beat.get("primary_subject", "")
        )

        if asset_type == "image":
            filter_str = (
                "[0:v]scale=1080*2:1920*2:force_original_aspect_ratio=increase,"
                "crop=1080*2:1920*2,"
                "zoompan=z='min(zoom+0.0013,1.26)':x='iw/2-(iw/zoom/2)+sin(on/50)*22':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                "eq=brightness=-0.04:contrast=1.18:saturation=0.82,"
                "noise=alls=10:allf=t+u,"
                "vignette=PI/3.5[pan];"
                "[1:v]scale=1080:1920[hud];"
                "[pan][hud]overlay=0:0[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(asset_path),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(hud_png),
                "-filter_complex", filter_str,
                "-map", "[outv]",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-r", str(cls.FPS),
                str(output_clip)
            ]
        else:
            filter_str = (
                "[0:v]scale=1080*2:1920*2:force_original_aspect_ratio=increase,crop=1080*2:1920*2,"
                "zoompan=z='min(zoom+0.0010,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                "eq=brightness=-0.04:contrast=1.20:saturation=0.84,"
                "noise=alls=8:allf=t+u,"
                "vignette=PI/3.5[vid];"
                "[1:v]scale=1080:1920[hud];"
                "[vid][hud]overlay=0:0[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", str(asset_path),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(hud_png),
                "-filter_complex", filter_str,
                "-map", "[outv]",
                "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-r", str(cls.FPS),
                str(output_clip)
            ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR: POLICE DOSSIER SLAM (CONFIDENTIAL CASE RECORD) ────────────
    @classmethod
    def _render_police_dossier_slam(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        broll_kw = beat.get("broll_keywords") or "dark police station desk interrogation files"
        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="police_dossier_slam",
            contextual_broll=beat.get("contextual_broll_query", "police interrogation desk lamp paperwork")
        )
        dossier_card = DocuAssetService.generate_police_dossier_card(
            case_title=beat.get("headline_text") or beat.get("visual_subject") or "CRIME CASE RECORD",
            subject_name=beat.get("primary_subject") or "CONFIDENTIAL SUSPECT",
            case_no=beat.get("delta_str") or "FIR-2018/SEC-302",
            police_station=beat.get("publication_name") or "DELHI POLICE · CRIME BRANCH",
            theme=theme
        )
        hud_png = DocuAssetService.generate_crime_timestamp_overlay(
            chapter_stamp=beat.get("chapter_stamp", ""),
            location_subtext="CLASSIFIED CASE DOSSIER // CONFIDENTIAL"
        )

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=7,eq=brightness=-0.22:contrast=1.22:saturation=0.75,vignette=PI/3.2[bg];"
            "[1:v]scale=920:-1[card];"
            f"[bg][card]overlay=x='(W-w)/2':y='if(lt(t,0.16),(H-h)/2-60-(0.16-t)*2600,(H-h)/2-60)':eval=frame[slam];"
            "[slam][2:v]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(dossier_card),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(hud_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS),
            str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR: SATELLITE MAP ZOOM (INDIAN CRIME LOCATION RETICLE) ───────
    @classmethod
    def _render_satellite_map_zoom(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        loc_name = beat.get("visual_subject") or beat.get("chapter_stamp", "DELHI, INDIA")
        clean_loc = re.sub(r"[\[\]·\d:]", "", loc_name).strip() or "New Delhi India"
        query = f"{clean_loc} aerial satellite view map"

        photo_path = DocuAssetService.fetch_archival_photo(query)
        reticle_png = DocuAssetService.generate_satellite_reticle(
            coordinates_str="28.7532° N, 77.1983° E",
            location_name=loc_name[:30]
        )

        filter_str = (
            "[0:v]scale=1080*2:1920*2:force_original_aspect_ratio=increase,"
            "crop=1080*2:1920*2,"
            "zoompan=z='min(zoom+0.0020,1.38)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
            "eq=brightness=-0.08:contrast=1.22:saturation=0.65,"
            "noise=alls=12:allf=t+u,"
            "vignette=PI/3.2[sat];"
            "[1:v]scale=1080:1920[reticle];"
            "[sat][reticle]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(photo_path),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(reticle_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS),
            str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR: ARCHIVAL PHOTO PAN (KEN BURNS HISTORICAL PHOTOGRAPH) ─────
    @classmethod
    def _render_archival_photo_pan(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        v_subj = beat.get("visual_subject") or beat.get("primary_subject", "historical archival photograph")
        photo_path = DocuAssetService.fetch_archival_photo(v_subj)
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080*2:1920*2:force_original_aspect_ratio=increase,"
            "crop=1080*2:1920*2,"
            "zoompan=z='min(zoom+0.0014,1.25)':x='iw/2-(iw/zoom/2)+sin(on/45)*28':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
            "eq=brightness=-0.05:contrast=1.16:saturation=0.92,"
            "vignette=PI/3.8[pan];"
            "[1:v]scale=1080:1920[stamp];"
            "[pan][stamp]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(photo_path),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS),
            str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 1: NEWSPAPER SLAM & REAL ARCHIVAL CLIPPING ────────────────
    @classmethod
    def _render_newspaper_slam(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        headline = beat.get("headline_text") or beat.get("narration", "HISTORIC BREAKDOWN")
        highlight = beat.get("highlight_phrase", "")
        broll_kw = beat.get("broll_keywords") or "newspaper printing press industrial rotating rollers"
        context_broll = beat.get("contextual_broll_query", "newspaper printing press industrial rotating rollers")
        news_q = beat.get("newspaper_search_query") or beat.get("visual_subject") or headline
        pub_name = beat.get("publication_name", "THE WALL STREET JOURNAL")

        # Context-locked printing press background + real archival newspaper clipping
        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="newspaper_slam",
            contextual_broll=context_broll
        )
        paper_path, hl_box = DocuAssetService.fetch_real_archival_newspaper(
            query=news_q,
            headline=headline,
            highlight_phrase=highlight,
            publication_name=pub_name,
            theme=theme
        )
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        offset_y = (cls.HEIGHT - 920) // 2 - 80
        if hl_box:
            bx, by, bw, bh = hl_box
            actual_x = (cls.WIDTH - 920) // 2 + int(bx * 920 / 1080)
            actual_y = offset_y + int(by * 920 / 1080)
            actual_w = int(bw * 920 / 1080)
            actual_h = int(bh * 920 / 1080)
            hl_filter = (
                f";[slam]drawbox=x={actual_x}:y={actual_y}:"
                f"w={actual_w}:h={actual_h}:"
                f"color=0xFFE600@0.60:t=fill:enable='gte(t,0.30)'[with_hl];"
                f"[with_hl][2:v]overlay=0:0[outv]"
            )
        else:
            hl_filter = ";[slam][2:v]overlay=0:0[outv]"

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=8,eq=brightness=-0.22:contrast=1.2,vignette=PI/3[bg];"
            "[1:v]scale=920:920[paper];"
            f"[bg][paper]overlay=x='(W-w)/2':y='if(lt(t,0.15),(H-h)/2-80-(0.15-t)*2600,(H-h)/2-80)':eval=frame[slam]{hl_filter}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(paper_path),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 2: ORBIT / EMPIRE NETWORK ─────────────────────────────────
    @classmethod
    def _render_orbit_network(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        v_subj = beat.get("visual_subject") or beat.get("primary_subject", "Titan")
        sec_logos = beat.get("secondary_elements", ["Tech", "Finance", "Global"])
        broll_kw = beat.get("broll_keywords") or "technology network space dark"

        bg_vid = DocuAssetService.fetch_broll_background(broll_kw, theme, beat_idx)
        center_cutout = DocuAssetService.fetch_subject_cutout(v_subj, beat.get("primary_subject", ""))
        orbit_ring = DocuAssetService.generate_orbit_ring(diameter=740, color_hex="#d97706")
        node_logo_1 = DocuAssetService.get_brand_logo(sec_logos[0] if len(sec_logos) > 0 else "Google")
        node_logo_2 = DocuAssetService.get_brand_logo(sec_logos[1] if len(sec_logos) > 1 else "Apple")
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "eq=brightness=-0.20:contrast=1.18,vignette=PI/3[bg];"
            "[1:v]rotate=a='2*PI*t/14':c=none[orbit];"
            "[2:v]scale=340:-1[center_b];"
            "[3:v]scale=130:130[node1];"
            "[4:v]scale=130:130[node2];"
            "[bg][orbit]overlay=(W-w)/2:(H-h)/2-80[bg_orbit];"
            "[bg_orbit][center_b]overlay=(W-w)/2:(H-h)/2-80[with_center];"
            "[with_center][node1]overlay=(W-w)/2+280:(H-h)/2-260[with_node1];"
            "[with_node1][node2]overlay=(W-w)/2-280:(H-h)/2+100[with_nodes];"
            "[with_nodes][5:v]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(orbit_ring),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(center_cutout),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(node_logo_1),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(node_logo_2),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 3: 2.5D PARALLAX CUTOUT (GROUNDED REAL SUBJECT + CONTEXTUAL B-ROLL) ──
    @classmethod
    def _render_parallax_cutout(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        v_subj = beat.get("visual_subject") or beat.get("primary_subject", "Executive")
        broll_kw = beat.get("broll_keywords") or "press conference camera flashes dark blur"
        context_broll = beat.get("contextual_broll_query", "")

        # Context-locked background (e.g. Apple headquarters / tech campus)
        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="parallax_cutout",
            primary_subject=beat.get("primary_subject", ""),
            contextual_broll=context_broll
        )

        cutout = DocuAssetService.fetch_subject_cutout(v_subj, beat.get("primary_subject", ""))
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))
        role_badge = DocuAssetService.generate_role_badge(beat.get("subject_role_title", ""))

        if role_badge and role_badge.exists():
            filter_str = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "boxblur=5,eq=brightness=-0.20:contrast=1.20:saturation=0.85,"
                "vignette=PI/3.5[bg];"
                "[1:v]scale=-1:1080[fg];"
                "[bg][fg]overlay=x='(W-w)/2+sin(t*1.2)*14':y='H-h-120-(t*16)':eval=frame[with_fg];"
                "[with_fg][2:v]overlay=0:0[with_stamp];"
                "[with_stamp][3:v]overlay=x='(W-w)/2':y='H-170'[outv]"
            )
            inputs = [
                "-stream_loop", "-1", "-i", str(bg_vid),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(cutout),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(role_badge),
            ]
        else:
            filter_str = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "boxblur=5,eq=brightness=-0.20:contrast=1.20:saturation=0.85,"
                "vignette=PI/3.5[bg];"
                "[1:v]scale=-1:1080[fg];"
                "[bg][fg]overlay=x='(W-w)/2+sin(t*1.2)*14':y='H-h-120-(t*16)':eval=frame[with_fg];"
                "[with_fg][2:v]overlay=0:0[outv]"
            )
            inputs = [
                "-stream_loop", "-1", "-i", str(bg_vid),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(cutout),
                "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            ]

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 4: FINANCIAL STAT & CASH COUNTER ──────────────────────────
    @classmethod
    def _render_financial_stat(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        stat_num = beat.get("stat_number", "$10 Billion")
        stat_lbl = beat.get("stat_label", "MARKET VALUATION")
        delta = beat.get("delta_str", "+142%")
        trend = beat.get("trend", "up")
        broll_kw = beat.get("broll_keywords") or "stock market ticker numbers wall"
        context_broll = beat.get("contextual_broll_query", "stock market ticker numbers wall dark")

        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="financial_stat",
            contextual_broll=context_broll
        )
        card_path = DocuAssetService.generate_financial_card(stat_num, stat_lbl, delta, trend)
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=6,eq=brightness=-0.22:contrast=1.2,vignette=PI/3[bg];"
            "[1:v]scale=920:520[card];"
            "[bg][card]overlay=x='(W-w)/2':y='if(lt(t,0.20),(H-h)/2-80+(0.20-t)*1200,(H-h)/2-80)':eval=frame[with_card];"
            "[with_card][2:v]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(card_path),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 5: SPLIT-SCREEN COMPARISON (VS SHOWDOWN) ──────────────────
    @classmethod
    def _render_split_comparison(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        primary = beat.get("primary_subject")
        secondary = beat.get("secondary_subject")
        if not primary or not secondary:
            elements = beat.get("secondary_elements", ["Apple", "Microsoft"])
            primary = primary or (elements[0] if len(elements) > 0 else "Entity A")
            secondary = secondary or (elements[1] if len(elements) > 1 else "Entity B")

        label1 = beat.get("primary_label") or primary.upper()
        label2 = beat.get("secondary_label") or secondary.upper()

        broll_kw = beat.get("broll_keywords") or "abstract dark split contrast light leaks"
        context_broll = beat.get("contextual_broll_query", "abstract dark split contrast light leaks")
        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="split_comparison",
            contextual_broll=context_broll
        )
        cutout1 = DocuAssetService.fetch_subject_cutout(primary, primary)
        cutout2 = DocuAssetService.fetch_subject_cutout(secondary, secondary)
        split_overlay = DocuAssetService.generate_split_overlay(label1, label2)
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=8,eq=brightness=-0.22,vignette=PI/3[bg];"
            "[1:v]scale=-1:850[c1];"
            "[2:v]scale=-1:850[c2];"
            f"[bg][c1]overlay=({cls.WIDTH}/4)-(w/2):H-h-240[left_done];"
            f"[left_done][c2]overlay=(3*{cls.WIDTH}/4)-(w/2):H-h-240[both_chars];"
            "[3:v]scale=1080:1920[overlay_png];"
            "[both_chars][overlay_png]overlay=0:0[with_split];"
            "[with_split][4:v]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(cutout1),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(cutout2),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(split_overlay),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 6: ACTION GIF & ARCHIVAL LOOP ─────────────────────────────
    @classmethod
    def _render_action_gif(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        query = beat.get("action_gif_query") or beat.get("visual_subject") or "market crash shocked businessman"
        action_clip = DocuAssetService.fetch_action_clip(query)

        # If no action gif found, fallback to parallax cutout smoothly
        if not action_clip or not action_clip.exists():
            cls._render_parallax_cutout(beat, duration, theme, output_clip, work_dir, beat_idx)
            return

        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "eq=contrast=1.15:saturation=1.1,vignette=PI/4[gif];"
            "[1:v]scale=1080:1920[stamp];"
            "[gif][stamp]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(action_clip),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── METAPHOR 7: CINEMATIC B-ROLL (FULL SCREEN 4K ATMOSPHERIC PUSH-IN) ──
    @classmethod
    def _render_cinematic_broll(
        cls,
        beat: Dict[str, Any],
        duration: float,
        theme: str,
        output_clip: Path,
        work_dir: Path,
        beat_idx: int
    ):
        broll_kw = beat.get("broll_keywords") or beat.get("visual_subject") or "dark corporate skyscraper night"
        context_broll = beat.get("contextual_broll_query", broll_kw)
        bg_vid = DocuAssetService.fetch_broll_background(
            keywords=broll_kw,
            theme=theme,
            beat_idx=beat_idx,
            metaphor="cinematic_broll",
            primary_subject=beat.get("primary_subject", ""),
            contextual_broll=context_broll
        )
        stamp_png = DocuAssetService.generate_chapter_stamp(beat.get("chapter_stamp", ""))

        filter_str = (
            "[0:v]scale=1080*2:1920*2:force_original_aspect_ratio=increase,crop=1080*2:1920*2,"
            "zoompan=z='min(zoom+0.0010,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
            "eq=contrast=1.18:saturation=0.88,vignette=PI/3.5[broll];"
            "[1:v]scale=1080:1920[stamp];"
            "[broll][stamp]overlay=0:0[outv]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(bg_vid),
            "-loop", "1", "-t", f"{duration:.2f}", "-i", str(stamp_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-t", f"{duration:.2f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(cls.FPS), str(output_clip)
        ]
        cls._run_ffmpeg(cmd)

    # ── TIMINGS & HORMOZI SUBTITLES ────────────────────────────────────────
    @classmethod
    def _calculate_beat_durations(cls, beats: List[Dict[str, Any]], total_audio_dur: float) -> List[float]:
        n = len(beats)
        if n == 0:
            return []
        
        # Word counts per beat for proportional duration assignment
        word_counts = [max(1, len(b.get("narration", "").split())) for b in beats]
        total_words = sum(word_counts)

        durations = []
        for wc in word_counts:
            dur = (wc / total_words) * total_audio_dur
            durations.append(max(1.8, dur))

        # Re-scale to match exact total duration
        current_sum = sum(durations)
        if current_sum > 0:
            ratio = total_audio_dur / current_sum
            durations = [d * ratio for d in durations]

        return durations

    @classmethod
    def _generate_hormozi_subtitles(
        cls,
        word_timings: List[Dict[str, Any]],
        output_ass_path: Path,
        color_theme: str = "yellow",
        font_name: str = "Space Grotesk"
    ):
        """Builds 3-word sliding context window ASS subtitles."""
        palette = {
            "yellow": ("&H0000E5FF", "&H00FFFFFF"), # BGR Yellow highlight, White context
            "cyan": ("&H00FFFF00", "&H00FFFFFF"),   # BGR Cyan highlight
            "gold": ("&H000677D9", "&H00FFFFFF"),   # BGR Gold highlight
            "red": ("&H000000FF", "&H00FFFFFF"),    # BGR Red highlight
        }
        hl_color, norm_color = palette.get(color_theme.lower(), palette["yellow"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,{font_name},74,{norm_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,4.5,2.0,2,60,60,260,1
Style: Hot,{font_name},74,{hl_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,4.5,2.0,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for i, item in enumerate(word_timings):
            word = item.get("word", "").upper().strip()
            start = item.get("start", 0.0)
            end = item.get("end", start + 0.3)
            
            # Sliding 3-word context window
            prev_w = word_timings[i - 1].get("word", "").upper().strip() if i > 0 else ""
            next_w = word_timings[i + 1].get("word", "").upper().strip() if i < len(word_timings) - 1 else ""

            # Hot active word with pop-zoom animation
            active_text = f"{{\\rHot\\fscx118\\fscy118\\t(0,160,\\fscx100\\fscy100)}}{word}"
            
            parts = []
            if prev_w:
                parts.append(f"{{\\rNormal\\alpha&H55&}}{prev_w}")
            parts.append(active_text)
            if next_w:
                parts.append(f"{{\\rNormal\\alpha&H55&}}{next_w}")

            line_text = " ".join(parts)
            events.append(f"Dialogue: 0,{cls._fmt_ass_time(start)},{cls._fmt_ass_time(end)},Normal,,0,0,0,,{line_text}")

        output_ass_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))

    @staticmethod
    def _fmt_ass_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds * 100) % 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @classmethod
    def _resolve_bgm_track(cls, bgm_id: Optional[str]) -> Optional[Path]:
        if not bgm_id or bgm_id == "none":
            return None
        bgm_dir = settings.BGM_DIR
        if not bgm_dir.exists():
            return None
        # Try matching any track in bgm dir
        tracks = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        return tracks[0] if tracks else None

    @staticmethod
    def _get_media_duration(path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 60.0

    @staticmethod
    def _run_ffmpeg(cmd: List[str]):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            err_msg = res.stderr[-800:] if res.stderr else "Unknown FFmpeg error"
            raise RuntimeError(f"FFmpeg execution failed:\n{err_msg}")
