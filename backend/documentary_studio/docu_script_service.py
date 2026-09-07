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
        },
        "indian_true_crime": {
            "name": "🚨 Indian True Crime & Forensic Mysteries (Netflix / Crime Patrol Style)",
            "topics": [
                {"title": "The Burari Deaths: 11 Bodies, 11 Pipes, One Chilling Diary", "hook": "On July 1, 2018, Delhi Police entered a normal family home to find 11 bodies hanging in absolute silence."},
                {"title": "Abdul Karim Telgi: The ₹30,000 Crore Fake Stamp Paper Empire", "hook": "A fruit seller at a railway station bought a government printing press and shook the Indian financial system."},
                {"title": "The Cyanide Mohan Case: India's Deadliest Silent Predator", "hook": "For 5 years, 20 women vanished from Karnataka bus stands without a single drop of blood left behind."},
                {"title": "The 2008 Noida Double Murder Mystery & The Botched Investigation", "hook": "A 14-year-old girl and the household helper were murdered inside a locked apartment, baffling India's top detectives."},
                {"title": "The 1993 Bombay Blasts: How A RDX Scooter Solved India's Darkest Conspiracy", "hook": "On March 12, 1993, 12 serial bombs shook Mumbai. One unexploded scooter at Worli cracked the entire syndicate."},
                {"title": "The Akku Yadav Mob Justice: When 200 Women Stormed A Courtroom", "hook": "On August 13, 2004, a notorious predator walked into a Nagpur court surrounded by police. He never walked out alive."}
            ]
        }
    }

    THEMES = [
        {"id": "crime_noir", "name": "🚨 Crime Noir & Police Dossier (Indian Predator Look)", "bg": "#09090b", "accent": "#dc2626"},
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
                {"id": "crime_archival_drift", "name": "🔍 Real Crime Scene / Mugshot Drift", "desc": "Full-screen real archival police photo/mugshot with slow pan & VHS timestamp HUD"},
                {"id": "police_dossier_slam", "name": "📁 Confidential Police Case Dossier", "desc": "Police FIR / CBI case folder slamming on metal desk with red stamp & redacted lines"},
                {"id": "satellite_map_zoom", "name": "🛰️ Satellite Crime Location Zoom", "desc": "Satellite zoom into the Indian crime scene city/coordinates"},
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
        Supports both 60s Shorts and 3-5 Minute Investigative Deep-Dives.
        Falls back to curated modular templates if offline or API key missing.
        """
        default_metaphors = [
            "crime_archival_drift", "police_dossier_slam", "cinematic_broll",
            "newspaper_slam", "satellite_map_zoom", "financial_stat",
            "archival_photo_pan", "split_comparison"
        ]
        allowed = allowed_metaphors or default_metaphors

        # Flexible pacing: Shorts (~5s/beat) vs Long-form Deep Dives (~8.5s/beat)
        if duration_sec <= 90:
            target_beats = max(6, min(14, int(duration_sec / 5.0)))
            target_words = int(duration_sec * 2.10)
        else:
            target_beats = max(14, min(32, int(duration_sec / 8.5)))
            target_words = int(duration_sec * 1.95)

        api_key = settings.GEMINI_API_KEY
        if api_key and api_key.strip():
            client = genai.Client(api_key=api_key)
            prompt = cls._build_storyboard_prompt(topic, target_beats, target_words, duration_sec, language, allowed)
            for model_name in ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
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
    def _build_storyboard_prompt(
        cls,
        topic: str,
        target_beats: int,
        target_words: int,
        duration_sec: int,
        language: str,
        allowed: List[str]
    ) -> str:
        metaphor_str = ", ".join([f'"{m}"' for m in allowed])
        words_per_beat = "8 to 12 words" if duration_sec <= 90 else "14 to 22 words"
        is_crime = any(k in topic.lower() for k in [
            "crime", "murder", "kill", "police", "arrest", "scam", "burari", "telgi",
            "scandal", "heist", "case", "death", "cbi", "investigation", "mystery",
            "predator", "blast", "fir", "jail", "gangster", "dacoit", "court"
        ])

        crime_directive = ""
        if is_crime:
            crime_directive = """
CRITICAL TRUE CRIME & INVESTIGATIVE DIRECTIVES:
1. DIRECTOR PERSONA: You are the director of a gripping Netflix true-crime documentary series (like 'Indian Predator', 'House of Secrets: The Burari Deaths', and 'Crime Patrol').
2. LEGAL & ETHICAL GUARDRAILS (INDIAN LAW SEC 228A IPC):
   - NEVER disclose the real names or faces of victims of sexual offenses; strictly use respectful pseudonyms (e.g. 'Pooja', 'Victim A') and symbolic forensic metaphors.
   - NEVER depict or describe graphic blood, gore, or violence.
   - The psychological suspense MUST emerge from forensic evidence, police FIR contradictions, phone records, and investigative deduction.
3. TWO-TIER ASSET RETRIEVAL:
   - For every beat, provide:
     * 'primary_real_query': specific real archival photograph / mugshot / FIR / police photo (e.g. 'Burari house 11 pipes police investigation photo', 'Abdul Karim Telgi arrest Bangalore 2001 photo').
     * 'fallback_stock_query': atmospheric cinematic re-enactment B-roll query (e.g. 'dark street night police car red blue lights flashing rain', 'handcuffs on wooden table dramatic lighting', 'judge gavel strike courtroom dark', 'fingerprint dusting forensic lab').
4. ZERO CUTOUTS: Focus on full-frame archival imagery, police dossiers, satellite map zoom, and 4K atmospheric crime scenes.
"""

        return f"""You are a master investigative documentary director in the style of Netflix True Crime, Indian Predator, and Vox.
Write a 100% viral, mature, highly gripping narrative documentary storyboard about: "{topic}".

Target Duration: EXACTLY {duration_sec} SECONDS.
Total Story Beats: EXACTLY {target_beats} chronological story beats.
Language: {language}. (Write the "narration" in natural, punchy, dramatic {language}).

STRICT DURATION & WORD BUDGET (ABSOLUTE MANDATE):
- TOTAL SCRIPT WORD COUNT: Strictly {target_words} words across ALL {target_beats} beats combined (+/- 5 words max).
- EACH BEAT NARRATION: Strictly {words_per_beat}.
- This ensures voiceover playback finishes in EXACTLY {duration_sec} seconds!

MASTER INVESTIGATIVE STORYTELLING ARC (4-ACT STRUCTURE):
- ACT 1: THE CRIME & MIDNIGHT DISCOVERY (Beats 1-{max(2, target_beats // 4)}):
  * Beat 1 MUST hook the audience in the first 5 words with an impossible paradox or chilling 911/police alert.
- ACT 2: FALSE LEADS & SUSPECTS (Beats {max(2, target_beats // 4) + 1}-{max(4, target_beats // 2)}):
  * The deceptive alibi, conflicting testimonies, or massive cover-up.
- ACT 3: FORENSIC BREAKTHROUGH & INTERROGATION (Beats {max(4, target_beats // 2) + 1}-{max(6, target_beats * 3 // 4)}):
  * The single telephone ping, fingerprint anomaly, or confession breakdown.
- ACT 4: THE VERDICT & HISTORIC RECKONING (Beats {max(6, target_beats * 3 // 4) + 1}-{target_beats}):
  * The courtroom verdict, justice delivered, and haunting closing lesson.
{crime_directive}
Every beat MUST use one of these allowed visual metaphors:
[{metaphor_str}]

Output strictly a JSON object with this schema:
{{
  "title": "Clean documentary title",
  "seo_description": "2-sentence high-curiosity YouTube Shorts/Video description with #reelbot.ai",
  "primary_subject": "Name of main person, suspect, or entity",
  "beats": [
    {{
      "beat_index": 1,
      "narration": "In the dead of night, a call to the police control room changed everything.",
      "metaphor": "crime_archival_drift",
      "chapter_stamp": "[ 01 JULY 2018 · SANT NAGAR, DELHI · 07:15 AM ]",
      "visual_subject": "Delhi Police crime scene tape Sant Nagar Burari house",
      "primary_real_query": "Burari house 11 pipes police investigation photo",
      "fallback_stock_query": "dark street night police car red blue lights flashing rain",
      "newspaper_search_query": "Delhi Burari deaths front page newspaper headline",
      "publication_name": "THE HINDUSTAN TIMES",
      "primary_subject": "Lalit Bhatia",
      "subject_role_title": "PRIME SUSPECT · THE DIARY WRITER",
      "contextual_broll_query": "police car emergency lights flashing night rain",
      "broll_keywords": "police car emergency lights flashing night rain",
      "headline_text": "11 BODIES FOUND IN SANT NAGAR HOME",
      "highlight_phrase": "11 BODIES FOUND",
      "stat_number": "11 Lives",
      "stat_label": "VICTIMS FOUND",
      "delta_str": "UNSOLVED",
      "trend": "down",
      "sfx_cue": "police_siren"
    }}
  ]
}}

Sound Cue rules:
- 'police_siren': for crime scene discovery, police chase, or sirens.
- 'gavel_strike': for courtroom decisions, charges framed, or sentences.
- 'radio_static': for police dispatch, wiretap recordings, or confidential calls.
- 'dull_heartbeat': for mounting psychological suspense or stalking.
- 'camera_flash': for forensic crime scene photographer flashes or mugshots.
- 'paper_slam': for confidential case file slam or shocking headline reveal.
- 'bass_drop': for shocking twist or body discovered.
- 'whoosh': for rapid scene transitions.
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
        is_crime = ("crime" in visual_theme.lower() or "noir" in visual_theme.lower() or 
                    any(k in topic.lower() for k in [
                        "crime", "murder", "kill", "police", "arrest", "scam", "burari", "telgi",
                        "scandal", "heist", "case", "death", "cbi", "investigation", "mystery",
                        "predator", "blast", "fir", "jail", "gangster", "dacoit", "court"
                    ]))

        if is_crime:
            crime_templates = [
                ("In the dead of night, a call to the police control room changed everything.", "crime_archival_drift", "police_siren", f"POLICE CONTROL ROOM ALERT", f"POLICE ALERT", f"{topic} police crime scene photo", "police car emergency red blue lights flashing night rain", f"{topic} crime scene discovery", "[ 02:15 AM · SCENE OF OCCURRENCE ]", "DELHI POLICE · CRIME BRANCH"),
                ("First responders arrived to discover an eerie, chilling crime scene.", "crime_archival_drift", "camera_flash", "CRIME SCENE SECURED", "CHILLING SCENE", f"{topic} crime scene house tape photo", "police cordon yellow tape night street", f"{topic} forensic unit", "[ FORENSIC UNIT SECURING PREMISES ]", "SCENE OF OCCURRENCE"),
                ("The state police immediately sealed off the entire neighborhood perimeter.", "police_dossier_slam", "paper_slam", "CONFIDENTIAL CASE RECORD", "CONFIDENTIAL FILE", f"{topic} official police FIR dossier", "dark police station desk interrogation paperwork", f"{topic} FIR register", "[ CBI / SPECIAL INVESTIGATION ]", "CONFIDENTIAL POLICE DOSSIER"),
                ("Satellite coordinates pinned the investigation to this exact location.", "satellite_map_zoom", "radio_static", "SATELLITE LOCATION IDENTIFIED", "COORDINATES PINNED", f"{topic} aerial location map", "satellite surveillance aerial map", f"{topic} aerial view", "[ SATELLITE INTEL COORDINATES ]", "LOCATION SURVEILLANCE"),
                ("As word spread, shocking headlines broke across morning national newspapers.", "newspaper_slam", "paper_slam", f"MYSTERY DEEPENS: {topic[:30].upper()}", "MYSTERY DEEPENS", f"{topic} front page newspaper headline archive", "newspaper printing press rotating rollers vintage", f"{topic} news alert", "[ NATIONAL MEDIA ALERT ]", "THE HINDUSTAN TIMES"),
                ("Forensic detectives discovered glaring contradictions in early statements.", "cinematic_broll", "dull_heartbeat", "CONTRADICTIONS DISCOVERED", "FORENSIC ANOMALY", f"{topic} forensic detective investigation", "handcuffs on wooden table dramatic lighting", f"{topic} forensic analysis", "[ FORENSIC RECONSTRUCTION ]", "INVESTIGATIVE LEAD"),
                ("Phone records and call detail analysis cracked the suspect's timeline.", "crime_archival_drift", "camera_flash", "CALL RECORDS CRACK TIMELINE", "TIMELINE RECONSTRUCTED", f"{topic} primary suspect evidence", "police interrogation room dark lamp silhouette", f"{topic} suspect confession", "[ CALL DATA RECORD BREAKTHROUGH ]", "TIMELINE RECONSTRUCTED"),
                ("In a tense courtroom confrontation, the conclusive evidence was presented.", "police_dossier_slam", "gavel_strike", "CHARGESHEET FILED IN COURT", "CHARGESHEET FILED", f"{topic} courtroom trial evidence", "judge wooden gavel strike dark courtroom", f"{topic} court hearing", "[ SESSIONS COURT JUDGMENT ]", "JUDICIAL RECKONING"),
                ("The shocking investigation remains permanently etched in forensic history.", "crime_archival_drift", "whoosh", "THE FORENSIC LESSON", "HAUNTING LESSON", f"{topic} archival photograph", "dark city skyline night sirens fading rain", f"{topic} case closing", "[ CASE CLOSED · FORENSIC ARCHIVE ]", "FINAL VERDICT")
            ]
            templates = crime_templates
            metaphors = allowed if allowed else ["crime_archival_drift", "police_dossier_slam", "satellite_map_zoom", "cinematic_broll", "newspaper_slam"]
        else:
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
            metaphors = allowed if allowed else ["archival_photo_pan", "parallax_cutout", "newspaper_slam", "split_comparison", "financial_stat", "action_gif"]

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
                "primary_real_query": tmpl[5],
                "fallback_stock_query": tmpl[6],
                "newspaper_search_query": f"{topic} front page headline newspaper archive",
                "publication_name": "THE HINDUSTAN TIMES" if is_crime else "THE WALL STREET JOURNAL",
                "broll_keywords": tmpl[6],
                "contextual_broll_query": tmpl[6],
                "action_gif_query": tmpl[7],
                "primary_subject": subject,
                "secondary_elements": [subject, "Primary Suspect" if is_crime else "Industry Rival"],
                "primary_label": f"{subject.upper()}" if is_crime else f"{subject.upper()} · LEADER",
                "secondary_label": "PRIME SUSPECT" if is_crime else "INDUSTRY RIVAL",
                "headline_text": tmpl[3] if tmpl[3] else f"THE INVESTIGATION: {subject.upper()}",
                "highlight_phrase": tmpl[4] if tmpl[4] else subject.upper(),
                "stat_number": tmpl[3] if "$" in tmpl[3] or "%" in tmpl[3] else "11 LIVES",
                "stat_label": "CRIME VICTIMS" if is_crime else "TOTAL FISCAL IMPACT",
                "delta_str": "UNSOLVED" if is_crime else ("+140%" if i % 2 == 0 else "-68%"),
                "trend": "down" if is_crime else ("up" if i % 2 == 0 else "down"),
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
