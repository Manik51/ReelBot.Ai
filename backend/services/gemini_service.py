import json
import re
import time
import random
from typing import Dict, Any, List
from google import genai
from google.genai import types

class GeminiService:
        MODELS_ORDER = [
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-flash-latest"
    ]

    TREND_NICHES = [
        "Dark Psychology and Body Language Manipulation Secrets",
        "Bizarre Unexplained Ocean Abyss and Underwater Anomalies",
        "How Top 1% Billionaires Exploit Money and Tax Loopholes",
        "Terrifying Deep Space, Black Holes and Universe Paradoxes",
        "Ancient Stoic Discipline and Psychological Dominance Rules",
        "Untold Historical Secrets and Classified CIA Experiments",
        "Mind-Bending Neuroscience and Brain Chemistry Hacks",
        "Shocking Future AI and Cybernetic Revelations"
    ]

    @classmethod
    def get_client(cls, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is required")
        return genai.Client(api_key=api_key)

    @classmethod
    def find_trends(cls, api_key: str) -> List[Dict[str, Any]]:
        client = cls.get_client(api_key)
        
        # Pick 3-4 random niches each time for infinite diversity
        selected_niches = random.sample(cls.TREND_NICHES, k=4)
        current_time_seed = time.time()
        random_seed = random.randint(1000, 999999)

        prompt = (
            f"You are a cutting-edge YouTube Shorts and Instagram Reels algorithm analyst. "
            f"Current timestamp seed: {current_time_seed} (Random ID: {random_seed}). "
            f"Generate a COMPLETELY FRESH, UNIQUE, and UNREPEATABLE batch of 12-15 viral trending topics. "
            f"Focus on these dynamic niches for this batch: {', '.join(selected_niches)}. "
            f"Every single topic must be an irresistible, high-retention curiosity hook with high dopamine potential. "
            f"Never output boring or generic titles. Each title should make viewers stop scrolling instantly. "
            f"Respond ONLY with a valid JSON array of objects with keys: "
            f"'title' (string, ultra-catchy viral hook under 55 chars), "
            f"'category' (string), "
            f"'views_potential' (e.g. '9.4M Views', '14.1M Views', '18.7M Views'), "
            f"'emoji' (e.g. '💀', '💰', '🌊', '👁️', '⚡', '🌌', '⚔️', '🧠'), "
            f"'tone' (one of: 'High Energy / Viral', 'Storytelling / Suspense', 'Motivational / Powerful', 'Informative / Documentary'). "
            f"DO NOT include markdown code blocks or any other text outside the JSON array."
        )

        for model_name in cls.MODELS_ORDER:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.95,
                        response_mime_type="application/json"
                    )
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
                    raw_text = re.sub(r"\n```$", "", raw_text)
                data = json.loads(raw_text)
                if isinstance(data, list) and len(data) > 0:
                    return data
                elif isinstance(data, dict) and "trends" in data and len(data["trends"]) > 0:
                    return data["trends"]
            except Exception as e:
                print(f"find_trends fallback from {model_name}: {e}")
                continue

        # Dynamic fallback generator if API temporarily limits
        curated_fallbacks = [
            {"title": "The Silence Trick That Controls Any Conversation", "category": "Psychology", "views_potential": f"{random.randint(7, 19)}.{random.randint(1, 9)}M Views", "emoji": "💀", "tone": "Storytelling / Suspense"},
            {"title": "Why The Wealthiest 1% Never Keep Cash in Banks", "category": "Wealth", "views_potential": f"{random.randint(8, 22)}.{random.randint(1, 9)}M Views", "emoji": "💰", "tone": "High Energy / Viral"},
            {"title": "The Sound Recorded 35,000 Feet Under the Ocean", "category": "Ocean", "views_potential": f"{random.randint(6, 15)}.{random.randint(1, 9)}M Views", "emoji": "🌊", "tone": "Storytelling / Suspense"},
            {"title": "3 Signs Someone Is Secretly Jealous of You", "category": "Psychology", "views_potential": f"{random.randint(9, 18)}.{random.randint(1, 9)}M Views", "emoji": "👁️", "tone": "Storytelling / Suspense"},
            {"title": "The Quantum Physicist Warning About Parallel Realities", "category": "Space", "views_potential": f"{random.randint(7, 16)}.{random.randint(1, 9)}M Views", "emoji": "🌌", "tone": "Informative / Documentary"},
            {"title": "3 Ancient Spartan Habits to Build Ruthless Focus", "category": "Stoic", "views_potential": f"{random.randint(5, 14)}.{random.randint(1, 9)}M Views", "emoji": "⚔️", "tone": "Motivational / Powerful"},
            {"title": "What 10 Minutes of Overthinking Does to Your Arteries", "category": "Brain", "views_potential": f"{random.randint(8, 17)}.{random.randint(1, 9)}M Views", "emoji": "🧠", "tone": "Informative / Documentary"},
            {"title": "The Classified Cold War Submarine Incident in 1968", "category": "Mystery", "views_potential": f"{random.randint(6, 13)}.{random.randint(1, 9)}M Views", "emoji": "⏳", "tone": "Storytelling / Suspense"},
            {"title": "How Ultra-Rich Monopolize Prime Real Estate Free", "category": "Wealth", "views_potential": f"{random.randint(10, 25)}.{random.randint(1, 9)}M Views", "emoji": "💎", "tone": "High Energy / Viral"},
            {"title": "The Black Hole That Is Moving Towards Earth Faster", "category": "Space", "views_potential": f"{random.randint(12, 28)}.{random.randint(1, 9)}M Views", "emoji": "🚀", "tone": "Storytelling / Suspense"},
            {"title": "How Criminal Interrogators Break Anyone in 3 Steps", "category": "Psychology", "views_potential": f"{random.randint(9, 21)}.{random.randint(1, 9)}M Views", "emoji": "🔥", "tone": "Storytelling / Suspense"},
            {"title": "The 5-Second Stoic Rule When Disrespected in Public", "category": "Stoic", "views_potential": f"{random.randint(7, 18)}.{random.randint(1, 9)}M Views", "emoji": "👑", "tone": "Motivational / Powerful"}
        ]
        random.shuffle(curated_fallbacks)
        return curated_fallbacks

    @classmethod
    def generate_script(
        cls,
        api_key: str,
        topic: str,
        language: str = "English",
        tone: str = "High Energy / Viral",
        target_duration_sec: int = 60
    ) -> Dict[str, Any]:
        client = cls.get_client(api_key)
        scene_count = max(int(target_duration_sec / 3.2), 9)
        creative_seed = random.randint(10000, 999999)

        system_instruction = (
            "You are a world-class viral short-form video creator and scriptwriter (specialized in YouTube Shorts, Instagram Reels, and TikTok). "
            "Your videos achieve 90%+ audience retention by following these strict principles:\n"
            "1. Ultra-Rapid Pacing: 1 dynamic visual cut every 2.5 to 3.5 seconds (around 18-20 scenes for a 60s video).\n"
            "2. Viral 3-Second Hook: Scene 1 must immediately grab attention and stop the scroll with an explosive curiosity gap.\n"
            "3. High Dopamine & Dynamic Storytelling: Write a fresh, unique, engaging narrative every single time. Never produce predictable or repetitive lines.\n"
            "4. Multi-Language & Transliteration Rules:\n"
            "   - If language is 'Hindi': narration MUST be natural spoken Hindi in native Devanagari script for TTS engines (e.g. 'आंखों की पुतलियां सच बताती हैं।'), and subtitle_text MUST be UPPERCASE Hinglish in English alphabet (e.g. 'AANKHON KI PUTLIYAN SACH BATATI HAIN').\n"
            "   - If language is 'Bengali' or 'Bangla': narration MUST be natural spoken Bengali in native Bangla script for TTS engines (e.g. 'এই ৩টি নিয়ম তোমাকে অপরাজেয় করে তুলবে।'), and subtitle_text MUST be UPPERCASE Banglish in English alphabet (e.g. 'EI 3TI NIYOM TOMAKE OPARAJEYO KORE TULBE').\n"
            "   - If language is 'English': narration is punchy spoken English and subtitle_text is standard punchy English in UPPERCASE.\n"
            "5. EXACT LITERAL STOCK FOOTAGE KEYWORDS (STRICT RULE):\n"
            "   - Stock video search engines (Pexels / Pixabay) search for physical, visible objects.\n"
            "   - DO NOT provide abstract words like 'psychology', 'mindset', 'future', 'success'.\n"
            "   - ALWAYS provide 2-3 literal physical nouns in English that describe exactly what is seen in the clip.\n"
            "     * If voice speaks about eye dilation: keywords: ['macro eye pupil dilation zoom', 'dramatic iris lighting effect']\n"
            "     * If voice speaks about deep ocean: keywords: ['dark ocean abyss underwater', 'scuba diver flashlight deep sea']\n"
            "     * If voice speaks about money/wealth: keywords: ['counting stack of cash slow motion', 'luxury gold bullion vault']\n"
            "     * If voice speaks about brain/thought: keywords: ['glowing human brain neural network', 'person thinking in shadow']\n"
            "6. VIRAL YOUTUBE SEO METADATA:\n"
            "   - Generate click-worthy YouTube Shorts Title (with emoji), high-retention Description, and trending #Shorts Hashtags."
        )

        user_prompt = f"""
Create an original, highly engaging {target_duration_sec}-second viral short video script on the topic: "{topic}".
Random Creative Variation ID: {creative_seed}
Target Language: {language}
Tone & Style: {tone}
Number of Scenes: Exactly {scene_count} rapid scenes (each 2.5 - 3.5 seconds).

Return a JSON object with this exact schema:
{{
  "title": "Short punchy project title",
  "language": "{language}",
  "tone": "{tone}",
  "estimated_total_duration": {target_duration_sec},
  "seo": {{
    "youtube_title": "Viral Click-Worthy Title (under 60 chars) 😱 #shorts",
    "youtube_description": "2-3 sentence engaging description with keywords and call-to-action.",
    "hashtags": ["#shorts", "#viral", "#psychology", "#trending", "#reels"],
    "tags": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "Exact spoken words for voiceover (Bengali/Hindi/English native script)",
      "subtitle_text": "LATIN UPPERCASE SUBTITLE (Banglish/Hinglish/English)",
      "keywords": ["concrete physical english noun 1", "concrete physical noun 2"],
      "suggested_emoji": "🔥",
      "estimated_seconds": 3.0
    }}
  ]
}}
"""

        last_err = None
        for model_name in cls.MODELS_ORDER:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.85,
                        response_mime_type="application/json"
                    )
                )

                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
                    raw_text = re.sub(r"\n```$", "", raw_text)

                data = json.loads(raw_text)
                return data
            except Exception as e:
                print(f"generate_script fallback from {model_name}: {e}")
                last_err = e
                continue

        raise RuntimeError(f"All Gemini models failed: {last_err}")
