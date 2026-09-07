import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from backend.config import settings

class DocuScriptService:
    """
    Specialized Script & Storyboard Generator for 60s Documentary & Business Analysis Shorts.
    Tuned for high retention, dramatic narrative beats, and modular visual metaphor assignment.
    """

    PRESETS = {
        "corporate_rise_fall": {
            "name": "🏢 Corporate Rise & Fall",
            "topics": [
                {"title": "How Nokia Killed Its Own Smartphone Empire", "hook": "In 2007, Nokia owned 50% of the world's phones. 5 years later, they were worthless."},
                {"title": "Why Apple Was 90 Days Away From Bankruptcy in 1997", "hook": "Before becoming a $3 Trillion giant, Steve Jobs had to beg his arch-rival for $150 Million."},
                {"title": "How Netflix Destroyed Blockbuster With A Single Meeting", "hook": "In 2000, Blockbuster laughed Netflix out of the boardroom. It cost them $6 Billion."},
                {"title": "The Fall of Kodak: Invented Digital Cameras Then Hid Them", "hook": "Kodak literally invented the first digital camera in 1975, then buried it out of pure fear."},
                {"title": "How BlackBerry's Arrogance Crushed Their Entire Dynasty", "hook": "BlackBerry executives literally believed the iPhone was a toy for teenagers until it was too late."}
            ]
        },
        "tech_titans": {
            "name": "🚀 Tech Titans & Billionaire Secrets",
            "topics": [
                {"title": "The Dark Secret Behind Elon Musk's 5-Company Empire", "hook": "Elon Musk sleeps on factory floors not for publicity, but because Tesla was 3 days from bankruptcy."},
                {"title": "How Mark Zuckerberg Legally Took Full Control of Facebook", "hook": "At age 20, Mark Zuckerberg engineered a dual-class stock loophole that makes him impossible to fire."},
                {"title": "Ratan Tata's Legendary Revenge On Ford Motor Company", "hook": "When Ford humiliated Ratan Tata in 1999, he said nothing. 9 years later, he bought Jaguar from them."},
                {"title": "How Steve Jobs Was Humiliated & Fired From His Own Creation", "hook": "In 1985, Apple's board voted to strip Steve Jobs of all power in an emergency meeting."}
            ]
        },
        "market_crashes": {
            "name": "📉 Financial Heists & Market Crashes",
            "topics": [
                {"title": "How The 2010 Flash Crash Erased $1 Trillion In 12 Minutes", "hook": "At 2:42 PM, the US Stock Market suddenly plunged 1,000 points due to a single suburban trader."},
                {"title": "The Lehman Brothers Collapse That Shook Global Banking", "hook": "On September 15, 2008, a 158-year-old financial titan evaporated overnight with $600 Billion in debt."},
                {"title": "How George Soros Broke The Bank of England in One Day", "hook": "On Black Wednesday, one man bet against the British Pound and walked away with $1 Billion in pure cash."}
            ]
        },
        "scandals_history": {
            "name": "🔍 Scandals & Unknown History",
            "topics": [
                {"title": "How Pepsi Briefly Commanded The 6th Largest Navy On Earth", "hook": "In 1989, the Soviet Union had so little cash they traded 17 submarines and 3 warships to Pepsi."},
                {"title": "The $24 Million McDonald's Monopoly Game Fraud", "hook": "For 12 years, every single winning game piece was stolen by one security auditor named Uncle Jerry."},
                {"title": "The Secret Shoe War That Divided A German Town Forever", "hook": "Two brothers hated each other so fiercely they split their town and created Adidas and Puma."}
            ]
        }
    }

    THEMES = [
        {"id": "dark_slate", "name": "🌑 Dark Slate & Amber Gold (MagnatesMedia Style)", "bg": "#0f172a", "accent": "#d97706"},
        {"id": "vintage_archive", "name": "🗞️ Vintage Archive & 90s Paper (Vox Style)", "bg": "#1c1917", "accent": "#f59e0b"},
        {"id": "cyber_tech", "name": "💻 Cyber Blue & Clean Grid (Silicon Valley Look)", "bg": "#030712", "accent": "#0ea5e9"},
        {"id": "wall_street", "name": "📈 Wall Street Emerald & Crimson (Financial Look)", "bg": "#022c22", "accent": "#10b981"},
    ]

    @classmethod
    def get_presets(cls) -> Dict[str, Any]:
        return {
            "categories": cls.PRESETS,
            "themes": cls.THEMES,
            "metaphors": [
                {"id": "archival_photo_pan", "name": "📸 Archival Photo Ken Burns", "desc": "Full-screen iconic historical photo with cinematic camera drift and grain"},
                {"id": "parallax_cutout", "name": "🖼️ 2.5D Grounded Cutout", "desc": "Half-body subject cutout with bottom fade & 3D shadow over atmospheric b-roll"},
                {"id": "newspaper_slam", "name": "📰 Newspaper Slam & Highlighter", "desc": "Archive headline slams into view + neon yellow marker wipes text"},
                {"id": "split_comparison", "name": "⚖️ Rivalry Split-Screen (VS)", "desc": "Two real titans side-by-side with names, logos and laser divider"},
                {"id": "financial_stat", "name": "💰 Bloomberg Financial Card", "desc": "Giant bold valuation counter with trend pill & live ticker b-roll"},
                {"id": "action_gif", "name": "⚡ Action GIF & Archival Loop", "desc": "Dynamic high-retention archival reaction or event loop"},
                {"id": "cinematic_broll", "name": "🎥 4K Cinematic B-Roll Push-In", "desc": "Full-screen atmospheric 4K video shot with slow cinematic push-in & chapter stamp"},
            ]
        }

    @classmethod
    def generate_storyboard(
        cls,
        topic: str,
        duration_sec: int = 60,
        language: str = "English",
        visual_theme: str = "dark_slate",
        allowed_metaphors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calls Gemini to create a structured beat-by-beat storyboard.
        Falls back to curated modular templates if offline or API key missing.
        """
        allowed = allowed_metaphors or ["archival_photo_pan", "parallax_cutout", "newspaper_slam", "split_comparison", "financial_stat", "action_gif"]
        # Calm, mature pacing: ~4.5 - 5.2 seconds per visual beat (10-12 beats for 60s)
        target_beats = max(6, min(14, int(duration_sec / 4.8)))
        # Strictly budgeted words: 2.15 words per second (129 words for 60s)
        target_words = int(duration_sec * 2.15)

        api_key = settings.GEMINI_API_KEY
        if api_key and api_key.strip():
            client = genai.Client(api_key=api_key)
            prompt = cls._build_storyboard_prompt(topic, target_beats, target_words, duration_sec, language, allowed)
            for model_name in ["gemini-3.6-flash", "gemini-flash-latest"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.7,
                        )
                    )
                    data = json.loads(response.text)
                    if isinstance(data, dict) and "beats" in data and data["beats"]:
                        data["duration_sec"] = duration_sec
                        data["visual_theme"] = visual_theme
                        data["language"] = language
                        print(f"[DocuScript] Storyboard successfully generated using {model_name} ({len(data['beats'])} beats).")
                        return data
                except Exception as e:
                    print(f"[DocuScript] Model {model_name} attempt error: {e}")

        return cls._generate_fallback_storyboard(topic, target_beats, duration_sec, language, visual_theme, allowed)

    @classmethod
    def _build_storyboard_prompt(cls, topic: str, target_beats: int, target_words: int, duration_sec: int, language: str, allowed_metaphors: List[str]) -> str:
        metaphor_str = ", ".join(allowed_metaphors)
        return f"""You are a master investigative documentary director in the style of MagnatesMedia, Vox, and James Jani.
Write a 100% viral, mature, highly gripping narrative documentary storyboard about: "{topic}".

Target Duration: EXACTLY {duration_sec} SECONDS.
Total Story Beats: EXACTLY {target_beats} chronological story beats (~4.5 to 5.0 seconds per beat).
Language: {language}. (Write the "narration" in natural, punchy, dramatic {language}).

STRICT DURATION & WORD BUDGET (ABSOLUTE MANDATE):
- TOTAL SCRIPT WORD COUNT: Strictly {target_words} words across ALL {target_beats} beats combined (+/- 5 words max).
- EACH BEAT NARRATION: Strictly 8 to 11 words. NEVER exceed 12 words in any beat!
- This ensures voiceover playback finishes in EXACTLY {duration_sec} seconds! Any extra words will cause the video to exceed time!

MASTER INVESTIGATIVE STORYTELLING ARC (4-ACT STRUCTURE):
- ACT 1: THE FATAL CRISIS (Beats 1-3):
  * Beat 1 MUST hook the audience in the first 5 words with an impossible paradox or extreme disaster.
  * Establish high urgency, active verbs, and imminent collapse.
- ACT 2: THE RUTHLESS PIVOT (Beats 4-6):
  * The shocking counter-intuitive decision, savage cuts, unlikely alliance, or treasonous move.
- ACT 3: THE HIGH-STAKES CLIMAX (Beats 7-9):
  * The billion-dollar gamble, pivotal confrontation, audience shock, or masterstroke.
- ACT 4: THE LEGACY & VICTORY (Beats 10-12):
  * The historic resurrection, legendary takeaway, and enduring empire.

Every beat MUST use one of these allowed visual metaphors:
[{metaphor_str}]

CRITICAL PRODUCTION RULES FOR MATURE, STUDIO-GRADE CINEMA:
1. VIRAL HOOK SCRIPTING:
   - Beat 1 MUST immediately arrest attention with an impossible paradox or extreme disaster within the first 5 words. (e.g. "In 1997, Apple was 90 days from total extinction.").
   - Short, punchy, high-tension sentences. No corporate fluff. Every beat must feel like an intense page-turner.

2. CONTEXT-LOCKED B-ROLL PAIRING (ZERO IRRELEVANCE):
   - Background video MUST physically match the foreground story entity!
   - If "newspaper_slam": "contextual_broll_query" MUST be "newspaper printing press industrial rotating rollers" or "vintage newspaper press printing".
   - If subject is Steve Jobs / Apple: "contextual_broll_query" MUST be "Apple headquarters building Cupertino exterior" or "tech keynote stage dark lights".
   - If subject is Bill Gates / Microsoft: "contextual_broll_query" MUST be "1990s vintage computer monitor laboratory" or "Microsoft corporate campus".
   - If financial crash: "contextual_broll_query" MUST be "Wall street stock exchange floor trading panic vintage".
   - NEVER put random human faces in the background!

3. REAL ARCHIVAL NEWSPAPER SEARCH:
   - For "newspaper_slam", specify "newspaper_search_query" to find the REAL historical press front page (e.g. "Apple 1997 bankruptcy Wall Street Journal front page clipping", "Blockbuster bankruptcy New York Times headline").
   - Specify "publication_name" (e.g. "THE WALL STREET JOURNAL", "THE NEW YORK TIMES", "SAN JOSE MERCURY NEWS").

4. SILENT COMPREHENSION (STORY WORKS EVEN ON MUTE):
   - "chapter_stamp": Location & time header for silent viewers (e.g. "[ 1997 · CUPERTINO, CA ]", "[ 90 DAYS UNTIL EXTINCTION ]", "[ MACWORLD · BOSTON 1997 ]").
   - "subject_role_title": Role badge under character (e.g. "STEVE JOBS · RETURN OF THE FOUNDER", "BILL GATES · UNLIKELY ALLY").

Output strictly a JSON object with this schema:
{{
  "title": "Clean documentary title",
  "seo_description": "2-sentence high-curiosity YouTube Shorts description with #reelbot.ai",
  "primary_subject": "Name of main person or company",
  "beats": [
    {{
      "beat_index": 1,
      "narration": "In 1997, Apple was officially 90 days away from vanishing forever.",
      "metaphor": "newspaper_slam",
      "chapter_stamp": "[ 1997 · 90 DAYS TO EXTINCTION ]",
      "visual_subject": "Apple 1997 bankruptcy Wall Street Journal front page headline",
      "newspaper_search_query": "Apple 1997 bankruptcy Wall Street Journal headline archive clipping",
      "publication_name": "THE WALL STREET JOURNAL",
      "primary_subject": "Steve Jobs",
      "subject_role_title": "STEVE JOBS · INTERIM CEO",
      "secondary_subject": "Bill Gates",
      "primary_label": "STEVE JOBS · APPLE",
      "secondary_label": "BILL GATES · MICROSOFT",
      "contextual_broll_query": "newspaper printing press industrial rotating rollers",
      "broll_keywords": "newspaper printing press industrial rotating rollers",
      "headline_text": "APPLE WAS 90 DAYS FROM COMPLETE COLLAPSE",
      "highlight_phrase": "90 DAYS FROM COMPLETE COLLAPSE",
      "stat_number": "$1.04 Billion",
      "stat_label": "Q1 1997 NET LOSS",
      "delta_str": "-84%",
      "trend": "down",
      "action_gif_query": "shocked businessman market crash",
      "sfx_cue": "paper_slam"
    }}
  ]
}}

Sound Cue rules:
- 'camera_shutter': for archival photos, vintage images & character reveals.
- 'paper_slam': for shocking headline / document reveals.
- 'cash_kaching': for high valuation, bankruptcy debt, or investments.
- 'bass_drop': for dramatic turning points or catastrophic crashes.
- 'whoosh': for rapid transitions.
"""

    @classmethod
    def _generate_fallback_storyboard(
        cls,
        topic: str,
        target_beats: int,
        duration_sec: int,
        language: str,
        visual_theme: str,
        allowed: List[str]
    ) -> Dict[str, Any]:
        """Procedural documentary generator if Gemini is offline."""
        beats = []
        cues = ["paper_slam", "camera_shutter", "whoosh", "cash_kaching", "bass_drop"]
        metaphors = allowed if allowed else ["archival_photo_pan", "parallax_cutout", "newspaper_slam", "split_comparison", "financial_stat", "action_gif"]

        words = topic.split()
        subject = words[1] if len(words) > 1 else words[0]

        templates = [
            ("Behind closed doors, an unprecedented catastrophe was secretly unfolding.", "newspaper_slam", "paper_slam", "SECRET CRISIS MEETING DISCLOSED", "SECRET CRISIS MEETING", f"{subject} corporate headquarters archive", "newspaper printing press industrial rotating rollers", "shocked businessman", "[ THE BOARDROOM CRISIS ]", f"{subject.upper()} · EMERGENCY MEETING"),
            (f"At the height of their global reign, {subject} seemed totally invincible.", "archival_photo_pan", "whoosh", "", "", f"{subject} historic launch archive 1990s", "modern corporate glass skyscraper timelapse", "crowd cheering victory", "[ GLOBAL DOMINANCE ]", f"{subject.upper()} · PEAK MARKET CAP"),
            ("Their global valuation had skyrocketed into the hundreds of billions.", "financial_stat", "cash_kaching", "$45.8 Billion", "PEAK GLOBAL VALUATION", "luxury money vault cash", "Wall Street stock exchange floor trading panic vintage", "money flying rain", "[ FINANCIAL METRICS ]", f"{subject.upper()} · RECORD VALUATION"),
            ("Yet deep inside executive leadership, fatal complacency was taking hold.", "parallax_cutout", "camera_shutter", "", "", f"{subject} CEO serious portrait", "empty modern corporate boardroom night wide", "worried executive face", "[ INTERNAL COLLAPSE ]", f"{subject.upper()} · CHIEF EXECUTIVE"),
            ("In an instant, an aggressive rival launched a devastating surprise attack.", "split_comparison", "whoosh", "", "", f"{subject} vintage product", "technology lab glowing server monitors", "two people confrontation", "[ THE RIVALRY SHOWDOWN ]", f"{subject.upper()} VS RIVAL TITAN"),
            ("Leaked internal audit reports exposed catastrophic financial bleeding.", "newspaper_slam", "paper_slam", "INTERNAL LOSSES SURPASS RECORD HIGH", "CATASTROPHIC FINANCIAL BLEEDING", f"{subject} financial loss leaked memo", "newspaper printing press rotating rollers vintage", "panic trading floor", "[ CONFIDENTIAL AUDIT ]", f"{subject.upper()} · AUDIT LEAK"),
            ("Their stock value plunged like a stone across international markets.", "financial_stat", "bass_drop", "-74.2%", "MARKET CAPITALIZATION PLUNGE", "Wall Street panic floor", "red stock chart falling digital wall", "stock trader hands on head", "[ THE MARKET CRASH ]", f"{subject.upper()} · FREEFALL"),
            ("A daring multimillion-dollar lifeline was their single remaining salvation.", "parallax_cutout", "cash_kaching", "", "", f"investor signing contract {subject}", "luxury bank boardroom corridor", "handshake deal business", "[ THE RESCUE GAMBLE ]", f"{subject.upper()} · EMERGENCY LIFELINE"),
            ("The emergency restructuring forever redefined modern business history.", "archival_photo_pan", "whoosh", "", "", f"{subject} historic press conference archive", "modern tech campus glass reflection night", "futuristic server room", "[ THE PHOENIX MOMENT ]", f"{subject.upper()} · REBIRTH"),
            (f"And that is how {subject} pulled off the greatest resurrection in history.", "newspaper_slam", "paper_slam", "SURVIVING THE IMPOSSIBLE BATTLE", "SURVIVING THE IMPOSSIBLE", f"{subject} triumphant leader portrait", "cinematic sunrise over modern corporate city", "applause standing ovation", "[ THE FINAL VERDICT ]", f"{subject.upper()} · THE VICTORY")
        ]

        for i in range(target_beats):
            tmpl = templates[i % len(templates)]
            meta = tmpl[1] if tmpl[1] in metaphors else metaphors[i % len(metaphors)]
            cue = tmpl[2]

            beat = {
                "beat_index": i + 1,
                "narration": tmpl[0],
                "metaphor": meta,
                "chapter_stamp": tmpl[8],
                "subject_role_title": tmpl[9],
                "visual_subject": tmpl[5],
                "newspaper_search_query": f"{subject} historical newspaper front page headline archive",
                "publication_name": "THE WALL STREET JOURNAL",
                "broll_keywords": tmpl[6],
                "contextual_broll_query": tmpl[6],
                "action_gif_query": tmpl[7],
                "primary_subject": subject,
                "secondary_elements": [subject, "Industry Rival"],
                "primary_label": f"{subject.upper()} · LEADER",
                "secondary_label": "INDUSTRY RIVAL",
                "headline_text": tmpl[3] if tmpl[3] else f"THE UNTOLD TRUTH ABOUT {subject.upper()}",
                "highlight_phrase": tmpl[4] if tmpl[4] else subject.upper(),
                "stat_number": tmpl[3] if "$" in tmpl[3] or "%" in tmpl[3] else "$12.4 Billion",
                "stat_label": "TOTAL FISCAL IMPACT",
                "delta_str": "+140%" if i % 2 == 0 else "-68%",
                "trend": "up" if i % 2 == 0 else "down",
                "sfx_cue": cue
            }
            beats.append(beat)

        return {
            "title": f"The Untold Rise & Fall: {topic}",
            "seo_description": f"The hidden business breakdown of {topic}. Full case study analysis. #reelbot.ai #business #documentary",
            "primary_subject": subject,
            "duration_sec": duration_sec,
            "visual_theme": visual_theme,
            "language": language,
            "beats": beats
        }
