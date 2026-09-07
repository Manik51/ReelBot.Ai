"""
ReelBot Gemini Script Generator — v3.0
Produces cinematic, human-sounding Bengali/Hindi/English shorts scripts
optimised for Sarvam AI Bulbul v3 TTS pronunciation.
"""
import json
import re
import time
import random
from typing import Dict, Any, List
from google import genai
from google.genai import types


MODELS_ORDER = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
]

MYSTERY_NICHES = [
    "Chilling Unsolved Crime Files & Real Life Cold Cases",
    "Bizarre Deep Ocean Abyss Mysteries & Sea Monster Signals",
    "Mysterious Disappearances in Dense Forests & Bermuda Triangle",
    "Classified Cold War CIA & Military Secret Experiments",
    "Terrifying Ancient Ruins, Cursed Relics & Tomb Inscriptions",
    "Parallel Dimension Travelers & Glitches in the Matrix",
    "Eerie Unexplained Radio Signals from Deep Space & Ghost Stations",
    "Unsolved Heists & Masterminds Who Vanished into Thin Air",
]

BENGALI_SCRIPT_EXAMPLES = """
━━━ PERFECT BENGALI SCRIPT EXAMPLE (True Crime topic) ━━━
Topic: "D.B. Cooper: The Man Who Jumped From a Plane With $200,000"

Scene 1 [0:00-0:03]: "উনিশশো একাত্তর সালের, ... এক রহস্যময় রাতে,"
Scene 2 [0:03-0:06]: "একজন অচেনা মানুষ, ... বিমানে উঠলেন।"
Scene 3 [0:06-0:09]: "তার হাতে ছিল, ... একটি কালো ব্যাগ।"
Scene 4 [0:09-0:12]: "মাঝ আকাশে হঠাৎ, ... সে হুমকি দিল!"
Scene 5 [0:12-0:15]: "দুই লাখ ডলার চাই, ... নইলে সর্বনাশ।"
Scene 6 [0:15-0:18]: "বিমান নামল। টাকা দেওয়া হলো।"
Scene 7 [0:18-0:21]: "আবার আকাশে উড়ল, ... সেই রহস্যময় বিমান।"
Scene 8 [0:21-0:24]: "রাতের অন্ধকারে, ... দশ হাজার ফুট থেকে—"
Scene 9 [0:24-0:27]: "সে লাফ দিল! ...প্যারাসুট নিয়ে।"
Scene 10[0:27-0:30]: "তারপর? ... কোনো চিহ্ন নেই।"
...
━━━ END EXAMPLE ━━━

KEY THINGS TO NOTICE:
- Pure conversational Bengali, NOT formal/textbook Bengali
- Short, punchy sentences — 5 to 7 words per scene MAX
- Comma pauses (,) for natural breath rhythm
- Ellipsis (...) before shocking reveals
- ALL numbers written as Bengali words: উনিশশো একাত্তর, দুই লাখ, দশ হাজার
- ALL acronyms in Bengali: এফবিআই, সিআইএ, নাসা
- Sentence ends with dramatic punctuation: ! ? — ...
- Phrases like: "হঠাৎ...", "তারপর?", "কিন্তু সেই রাতে...", "পুলিশ আজও জানে না"
"""


class GeminiService:
    MODELS_ORDER = MODELS_ORDER
    MYSTERY_NICHES = MYSTERY_NICHES

    @classmethod
    def get_client(cls, api_key: str) -> genai.Client:
        if not api_key:
            raise ValueError("Gemini API Key is required.")
        return genai.Client(api_key=api_key)

    # ─────────────────────────────────────────────────────────────────────────
    # Trend discovery
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def find_trends(cls, api_key: str) -> List[Dict[str, Any]]:
        fallbacks = [
            {"title": "The Man Who Vanished From A Plane With $200,000", "source": "FBI Records", "category": "True Crime", "views_potential": f"{random.randint(11,24)}.{random.randint(1,9)}M Views", "emoji": "🕵️", "tone": "Storytelling / Suspense"},
            {"title": "The 1968 Submarine That Disappeared Without A Sound", "source": "Naval Archives", "category": "Ocean Mystery", "views_potential": f"{random.randint(9,21)}.{random.randint(1,9)}M Views", "emoji": "🌊", "tone": "Storytelling / Suspense"},
            {"title": "What 9 Hikers Saw Before Dying In Dyatlov Pass", "source": "Inquest Files", "category": "Unexplained Case", "views_potential": f"{random.randint(14,29)}.{random.randint(1,9)}M Views", "emoji": "💀", "tone": "Storytelling / Suspense"},
            {"title": "The Ghost Radio Station UVB-76 That Still Broadcasts", "source": "Signal Monitoring", "category": "Cold War", "views_potential": f"{random.randint(8,19)}.{random.randint(1,9)}M Views", "emoji": "📻", "tone": "Storytelling / Suspense"},
            {"title": "The Ship Found Sailing With No Crew And Warm Meals", "source": "Maritime Board", "category": "Disappearance", "views_potential": f"{random.randint(10,22)}.{random.randint(1,9)}M Views", "emoji": "🚢", "tone": "Storytelling / Suspense"},
            {"title": "The Man From Taured: Traveler From A Non-Existent Country", "source": "Tokyo Police Incident", "category": "Parallel World", "views_potential": f"{random.randint(12,26)}.{random.randint(1,9)}M Views", "emoji": "👁️", "tone": "Storytelling / Suspense"},
        ]
        if not api_key:
            random.shuffle(fallbacks)
            return fallbacks

        client = cls.get_client(api_key)
        niches = random.sample(MYSTERY_NICHES, k=4)
        seed = random.randint(1000, 999999)

        prompt = (
            f"You are the world's top True Crime & Mystery shorts producer. Seed: {seed}. "
            f"Generate 12-15 REAL, spine-chilling unsolved mystery & true crime topics. "
            f"Themes: {', '.join(niches)}. "
            "Return ONLY a valid JSON array. Each item: "
            "title (catchy hook ≤55 chars), source (e.g. FBI Files), category, views_potential (e.g. 12.4M Views), emoji, tone (always Storytelling / Suspense)."
        )

        for model in MODELS_ORDER:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.9, response_mime_type="application/json"),
                )
                raw = resp.text.strip().lstrip("```json").rstrip("```").strip()
                data = json.loads(raw)
                if isinstance(data, list) and data:
                    return data
                if isinstance(data, dict) and data.get("trends"):
                    return data["trends"]
            except Exception as e:
                print(f"find_trends [{model}]: {e}")
        random.shuffle(fallbacks)
        return fallbacks

    # ─────────────────────────────────────────────────────────────────────────
    # Script generation
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def generate_script(
        cls,
        api_key: str,
        topic: str,
        language: str = "Bengali",
        tone: str = "Storytelling / Suspense",
        target_duration_sec: int = 60,
    ) -> Dict[str, Any]:
        client = cls.get_client(api_key)

        if target_duration_sec >= 55:
            scene_count, target_duration_sec = 20, 60
        elif target_duration_sec >= 40:
            scene_count, target_duration_sec = 15, 45
        else:
            scene_count, target_duration_sec = 10, 30

        seed = random.randint(10000, 999999)

        # ── Language-specific narration guidelines ────────────────────────────
        if language == "Bengali":
            lang_rules = f"""
BENGALI NARRATION RULES (বাংলা ভয়েসওভার নিয়মাবলী):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{BENGALI_SCRIPT_EXAMPLES}

MANDATORY:
A) Pure modern spoken Bengali — the kind used on Mystery Xpose, Unsolved Files, Dhaka Mystery YouTube channels.
   NOT stiff textbook/formal Bengali. Write like you're telling a ghost story to a friend.

B) All numbers as Bengali words (never digits):
   ১৯৭১ → "উনিশশো একাত্তর সালে"   |   ২০০,০০০ → "দুই লাখ"
   ১০,০০০ → "দশ হাজার"            |   ৫০% → "পঞ্চাশ শতাংশ"
   ২৪ → "চব্বিশ"                   |   ১ → "এক"

C) All acronyms in Bengali script:
   FBI → "এফবিআই"   |   CIA → "সিআইএ"   |   NASA → "নাসা"
   DNA → "ডিএনএ"    |   CCTV → "সিসিটিভি"

D) Emotional suspense phrases to use freely:
   "হঠাৎ..." | "কিন্তু সেই রাতে..." | "পুলিশ আজও জানে না।"
   "আপনি বিশ্বাস করবেন না..." | "তারপর যা হলো..." | "রহস্যটা আজও অমীমাংসিত।"
   "একটু দাঁড়ান..." | "সবচেয়ে ভয়ঙ্কর ব্যাপার হলো..."

E) Subtitle text in UPPERCASE Banglish romanisation:
   "উনিশশো একাত্তর সালে" → "UNISHSO EKATTOR SHOLE"
"""
        elif language == "Hindi":
            lang_rules = """
HINDI NARRATION RULES:
━━━━━━━━━━━━━━━━━━━━━
A) Pure conversational modern Hindi — NOT formal/literary. Like real Indian mystery YouTubers.
B) All numbers as Hindi words: 1971 → "उन्नीस सौ इकहत्तर में"  |  $200,000 → "दो लाख डॉलर"
C) Acronyms in Hindi: FBI → "एफबीआई"  |  CIA → "सीआईए"
D) Suspense phrases: "अचानक..." | "लेकिन उस रात..." | "पुलिस आज भी नहीं जानती।"
E) Subtitle in UPPERCASE Hinglish: "उन्नीस सौ" → "UNNEES SAU"
"""
        else:
            lang_rules = """
ENGLISH NARRATION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
A) Punchy, eerie, cinematic — like Morbid Mysteries, Mr. Nightmare YouTube channels.
B) Short dramatic sentences. Use "..." for tension. Use "—" for cuts.
C) Subtitle in UPPERCASE.
"""

        system_instruction = f"""You are an elite viral short-form documentary scriptwriter.
Your scripts are crafted specifically so that Sarvam AI's Bulbul v3 neural text-to-speech engine
produces perfectly natural, human-sounding, emotionally gripping narration.

GOLDEN RULES (apply to every single scene — no exceptions):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PACING: Each scene narration = exactly 5 to 7 words.
   — Fewer words = voice has room to breathe naturally.
   — Never write 8+ words in a single scene narration.

2. RHYTHM & PAUSES:
   — Place a comma (,) every 3-4 words for a natural breath pause.
   — Use ellipsis (...) immediately before a shocking reveal or dramatic line.
   — End scenes with strong punctuation: ! ? — ... (not plain full stop when possible)

3. VISUAL TAG MATCH:
   — Each scene's visual_tag must be a concrete English noun phrase that DIRECTLY shows what is being narrated.
   — Example: narration "সে বিমান থেকে লাফ দিল!" → visual_tag "man parachuting from plane night sky"

4. STRICT STRUCTURE: Exactly {scene_count} scenes. Each = 3.0 seconds.

{lang_rules}
"""

        user_prompt = f"""
Write a {target_duration_sec}-second viral mystery short video script on:
TOPIC: "{topic}"
Language: {language}
Tone: {tone}
Scenes: Exactly {scene_count} (each 3.0 seconds, 5-7 words per narration)
Seed: {seed}

CRITICAL SUBTITLE RULE — subtitle_text field:
- MUST always be in pure UPPERCASE ROMAN/LATIN script (Banglish, Hinglish, or English)
- NEVER write Bengali, Hindi, Devanagari, or any Indic Unicode in subtitle_text
- GOOD: "UNISHSO EKATTOR SHOLE EK RAHOSHYO RAATE"
- BAD: "উনিশশো একাত্তর সালের" — WRONG, this is Bengali, not allowed in subtitle_text

Return ONLY a valid JSON object — no markdown, no preamble:
{{
  "title": "Short punchy project title",
  "language": "{language}",
  "tone": "{tone}",
  "estimated_total_duration": {target_duration_sec},
  "seo": {{
    "youtube_title": "Viral click-bait title 😱 #shorts",
    "youtube_description": "2-3 lines with curiosity gap and CTA.",
    "hashtags": ["#shorts", "#mystery", "#truecrime", "#viral"],
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "time_range": "0:00-0:03",
      "visual_tag": "man in dark suit boarding night flight",
      "narration": "উনিশশো একাত্তর সালের, . এক রহস্যময় রাতে,",
      "subtitle_text": "UNISHSO EKATTOR SHOLE EK RAHOSHYO RAATE",
      "keywords": ["man in dark suit boarding night flight", "airport 1970s noir"],
      "suggested_emoji": "✈️",
      "estimated_seconds": 3.0
    }},
    {{
      "scene_id": 2,
      "time_range": "0:03-0:06",
      "visual_tag": "nervous passenger alone on airplane",
      "narration": "একজন অচেনা মানুষ, . বিমানে উঠলেন।",
      "subtitle_text": "EKJON OCHENA MANUSH BIMANAY UTHLHEN",
      "keywords": ["nervous passenger airplane seat", "1970s aircraft interior"],
      "suggested_emoji": "🤫",
      "estimated_seconds": 3.0
    }}
  ]
}}
"""

        last_err = None
        for model in MODELS_ORDER:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.82,
                        response_mime_type="application/json",
                    ),
                )
                raw = resp.text.strip().lstrip("```json").rstrip("```").strip()
                data = json.loads(raw)
                return data
            except Exception as e:
                print(f"generate_script [{model}]: {e}")
                last_err = e

        raise RuntimeError(f"All Gemini models failed: {last_err}")
