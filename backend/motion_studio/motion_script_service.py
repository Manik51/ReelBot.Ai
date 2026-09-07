"""
ReelBot Motion Studio — Viral Comedy, Fun Facts & Animated GIF Script Generator
Designed for 100% viewer retention using absurdist humor, viral fun facts, rapid-fire punchlines, and meme reactions.
"""
import json
import re
import random
from typing import Dict, Any, List
from google import genai
from google.genai import types

from backend.config import settings

MODELS_ORDER = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
]

VIRAL_CATEGORIES = {
    "unhinged_animals": [
        {"title": "Why Cats Are Scientifically Liquid", "hook": "Feline physics make zero sense!", "emoji": "🐱"},
        {"title": "The Immortal Jellyfish That Refuses To Die", "hook": "Can literally rewind its biological age!", "emoji": "🪼"},
        {"title": "Octopuses Have 3 Hearts & Blue Blood", "hook": "Are octopuses secretly alien creatures?", "emoji": "🐙"},
        {"title": "Crows Never Forget A Human Face", "hook": "They hold generational grudges against enemies!", "emoji": "🦅"},
        {"title": "Tardigrades Can Survive Outer Space", "hook": "Can survive boiling water, ice, and space vacuum!", "emoji": "🔬"},
        {"title": "Why Pandas Are Too Silly To Survive", "hook": "How did this clumsy animal avoid extinction?", "emoji": "🐼"}
    ],
    "dumbest_fails": [
        {"title": "Bank Robber Wrote Demand On His Own Check", "hook": "Handed the teller a check with his full address!", "emoji": "🤦‍♂️"},
        {"title": "Burglar Fell Asleep On Couch Mid-Robbery", "hook": "Woke up to police handcuffs and hot coffee!", "emoji": "😴"},
        {"title": "Thief Stole A Manual Car He Couldn't Drive", "hook": "Stalled 6 times before getting arrested in driveway!", "emoji": "🚗"},
        {"title": "The Man Who Sold The Eiffel Tower Twice", "hook": "Conned scrap metal dealers out of millions!", "emoji": "🗼"},
        {"title": "Criminal Called Police Because Drugs Were Stolen", "hook": "Reported his stolen cocaine to local dispatchers!", "emoji": "🚨"},
        {"title": "Guy Robbed A Bank Then Deposited It In Next Window", "hook": "Thought it was an instant money laundering trick!", "emoji": "🏦"}
    ],
    "mind_body": [
        {"title": "Your Brain Makes You 5x Prettier In Mirrors", "hook": "How psychological bias alters your self-image!", "emoji": "🪞"},
        {"title": "Why Yawning Is Dangerously Contagious", "hook": "Why seeing someone yawn forces you to yawn too!", "emoji": "🥱"},
        {"title": "Phantom Vibration: Feeling A Ghost Phone Buzz", "hook": "Why your brain hallucinates cell phone alerts!", "emoji": "📱"},
        {"title": "Why Your Recorded Voice Sounds So Terrible", "hook": "The bone conduction secret behind your real voice!", "emoji": "🎙️"},
        {"title": "Your Eyes Actually See Everything Upside Down", "hook": "Your brain flips reality right side up 24/7!", "emoji": "👁️"},
        {"title": "You Can't Hum While Holding Your Nose", "hook": "Go ahead, try it right now — it's impossible!", "emoji": "👃"}
    ],
    "everyday_secrets": [
        {"title": "3000-Year-Old Tomb Honey Is Still Edible", "hook": "Archaeologists actually ate ancient Egyptian honey!", "emoji": "🍯"},
        {"title": "Potato Chips Were Born Out Of Pure Petty Revenge", "hook": "A chef made them super thin to spite an angry customer!", "emoji": "🥔"},
        {"title": "Why Water Tastes Sweet After Eating Amla", "hook": "The chemical reaction that tricks your sweet receptors!", "emoji": "🌿"},
        {"title": "Where That Missing Sock Actually Goes In Laundry", "hook": "The dark secret inside washing machine seals!", "emoji": "🧦"},
        {"title": "A Single Cloud Weighs 1.1 Million Pounds", "hook": "That fluffy white cloud is as heavy as 100 elephants!", "emoji": "☁️"},
        {"title": "Bananas Are Technically Radioactive", "hook": "Potassium-40 makes bananas emit real radiation!", "emoji": "🍌"}
    ],
    "coincidences": [
        {"title": "1898 Novel Predicted Titanic Sinking 14 Years Early", "hook": "Called the ship 'Titan' with exact same ice crash!", "emoji": "🚢"},
        {"title": "The Man Who Survived Both Atomic Bombs", "hook": "Tsutomu Yamaguchi survived Hiroshima & Nagasaki!", "emoji": "💥"},
        {"title": "In 1923, A Dead Jockey Won An Entire Horse Race", "hook": "Frank Hayes died mid-race but his horse crossed first!", "emoji": "🏇"},
        {"title": "Mark Twain Born & Died With Halley's Comet", "hook": "Came with the comet in 1835 and left with it in 1910!", "emoji": "☄️"},
        {"title": "Twins Separated At Birth Lived The Exact Same Life", "hook": "Both named their sons James and dogs Toy!", "emoji": "👥"},
        {"title": "The 335-Year War With Exactly Zero Casualties", "hook": "Netherlands and Scilly forgot they were at war!", "emoji": "🕊️"}
    ]
}

ALL_CURATED_HOOKS = [
    item for cat_list in VIRAL_CATEGORIES.values() for item in cat_list
]

class MotionScriptService:
    @classmethod
    def get_client(cls) -> genai.Client:
        key = settings.GEMINI_API_KEY.strip()
        if not key:
            raise ValueError("Gemini API Key is required. Please set it in Configure.")
        return genai.Client(api_key=key)

    @classmethod
    def get_random_viral_hook(cls, category: str = "all") -> Dict[str, str]:
        """Returns an instant viral topic idea."""
        if category in VIRAL_CATEGORIES:
            pool = VIRAL_CATEGORIES[category]
        else:
            pool = ALL_CURATED_HOOKS
        item = random.choice(pool)
        return {"topic": item["title"], "category": category}

    @classmethod
    def find_motion_trends(cls, category: str = "all") -> List[Dict[str, Any]]:
        """Generates 6 dynamic, trending, funny, and mindblowing topics."""
        client = cls.get_client()
        seed = random.randint(1000, 999999)

        cat_names = {
            "unhinged_animals": "Unhinged Animals & Wild Superpowers",
            "dumbest_fails": "Dumbest Criminals & Real Life Fails",
            "mind_body": "Mind-Blowing Human Body & Psychology Illusions",
            "everyday_secrets": "Everyday Food & Household Dark Secrets",
            "coincidences": "Crazy Coincidences & Glitch In The Matrix",
            "all": "Absurd Viral Facts, Animals, Fails & Mysteries"
        }
        cat_desc = cat_names.get(category, "Viral Entertainment & Absurd Fun Facts")

        prompt = (
            f"You are the world's top YouTube Shorts and TikTok viral entertainment creator. Random Seed: {seed}. "
            f"Topic Category: '{cat_desc}'. "
            "Generate EXACTLY 6 hilarious, jaw-dropping, curiosity-inducing viral topics that make viewers instantly click and watch till the end! "
            "Return ONLY a valid JSON array of exactly 6 objects. Each object must have: "
            "title (witty, punchy, <= 45 chars), hook_desc (1 punchy sentence teaser), views_potential (e.g. 18.4M Views), emoji (single relevant emoji), category (category name)."
        )

        for model in MODELS_ORDER:
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.95, response_mime_type="application/json"),
                )
                raw = resp.text.strip().lstrip("```json").rstrip("```").strip()
                data = json.loads(raw)
                if isinstance(data, list) and len(data) >= 6:
                    return data[:6]
                elif isinstance(data, list) and data:
                    return data
            except Exception as e:
                print(f"find_motion_trends [{model}]: {e}")

        # Fallback to curated 6 items
        if category in VIRAL_CATEGORIES:
            sampled = VIRAL_CATEGORIES[category][:6]
        else:
            sampled = random.sample(ALL_CURATED_HOOKS, k=6)

        fallbacks = []
        for idx, item in enumerate(sampled):
            fallbacks.append({
                "title": item["title"],
                "hook_desc": item.get("hook", "Mind-blowing viral fact that will shock you!"),
                "category": cat_desc,
                "views_potential": f"{random.randint(14, 38)}.{random.randint(1, 9)}M Views",
                "emoji": item.get("emoji", "🔥")
            })
        return fallbacks

    @classmethod
    def generate_motion_script(
        cls,
        topic: str,
        language: str = "Bengali",
        tone: str = "Funny / Entertainment",
        target_duration_sec: int = 30
    ) -> Dict[str, Any]:
        """
        Generates rapid-fire funny short scripts with hilarious punchlines and
        concrete story-action visual search tags.
        """
        client = cls.get_client()

        if target_duration_sec >= 55:
            scene_count, target_duration_sec = 20, 60
        elif target_duration_sec >= 40:
            scene_count, target_duration_sec = 15, 45
        else:
            scene_count, target_duration_sec = 10, 30

        seed = random.randint(10000, 999999)

        system_instruction = f"""You are a master comedy scriptwriter and visual director for viral animated video shorts.

CRITICAL RULES:
1. SCRIPT PACING: Exactly 5 to 7 words per scene narration. Fast, conversational, hilarious, punchy.
2. COMEDY HOOK & STORYTELLING:
   - Scene 1 MUST be an absurd, mind-bending hook that shocks or makes the viewer laugh out loud.
   - Middle scenes build the absurdity with escalating jokes, crazy real facts, or ridiculous twists.
   - Last scene has an unexpected, funny twist or punchline ending!
3. NATURAL PAUSES:
   - Use period (.) with spaces around it like ' . ' for full dramatic stops.
   - Use comma (,) for natural breath breaks.
4. LANGUAGE & NUMBERS:
   - Bengali: Conversational, friendly Kolkata/Dhaka young YouTube style (e.g. ভাই, বিশ্বাস করবেন না, একদম সত্যি).
   - Write numbers as Bengali words (উনিশশো তেইশ, দশ লাখ, পাঁচ হাজার).
   - Acronyms in Bengali (নাসা, সিআইএ).
5. SUBTITLE_TEXT FIELD:
   - MUST BE 100% UPPERCASE LATIN/ROMAN SCRIPT (Banglish, Hinglish, or English).
   - NO Indic script allowed in subtitle_text!
   - Example: "BHAI BISSHAS KORBEN NA ETA SHOTTI"
6. VISUAL_TAG & KEYWORDS (CONCRETE STORY ACTION — NEVER GENERIC MEME FACES):
   - Every scene MUST represent the SPECIFIC PHYSICAL ACTION or OBJECT happening in that exact sentence!
   - NEVER use generic reaction face memes (e.g. NEVER use 'shocked face', 'confused woman', 'man looking at camera' for story scenes).
   - In 'keywords', provide EXACTLY 3 distinct search terms in order of priority:
     1. Primary: Specific physical action/object (e.g. "cat liquid glass bowl")
     2. Alternative: Related concrete action (e.g. "cat squeezing into vase")
     3. Fallback: Broader subject (e.g. "funny cat flexible")
   - ONLY on the final scene (the punchline/twist ending), you may use a funny explosive reaction (e.g. "mind blown galaxy explosion meme").
7. SCENE_SFX FIELD:
   - Assign a specific contextual sound effect tag matching the scene mood:
     Options: "whoosh", "pop", "bonk", "record_scratch", "ding", "boom", "bell", "cheer"
"""

        user_prompt = f"""
Write a {target_duration_sec}-second hilarious, unhinged, viral entertainment short script on:
TOPIC: "{topic}"
Language: {language}
Tone: {tone}
Scenes: Exactly {scene_count} (each 3.0 seconds, 5-7 words per narration)
Seed: {seed}

Return ONLY valid JSON (no markdown formatting):
{{
  "title": "Short catchy funny title",
  "language": "{language}",
  "tone": "{tone}",
  "estimated_total_duration": {target_duration_sec},
  "seo": {{
    "youtube_title": "Craziest Thing You Never Knew! 😂 #shorts #reelbot.ai",
    "youtube_description": "Wait for the ending! 😂 #shorts #funny #funfacts #viral #reelbot.ai",
    "hashtags": ["#shorts", "#funny", "#funfacts", "#viral", "#comedy", "#reelbot.ai"],
    "tags": ["funny", "comedy", "facts", "viral", "shorts"]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "time_range": "0:00-0:03",
      "visual_tag": "cat liquid squeezing into round glass bowl",
      "narration": "বিজ্ঞানীরা বলছেন . বিড়াল আসলে পুরোপুরি তরল পদার্থ!",
      "subtitle_text": "BIGGANI-RA BOLCHHEN BIRAL ASHOLE PURAPURI TOROL",
      "keywords": ["cat liquid bowl", "cat squeezing vase", "funny cat flexible"],
      "scene_sfx": "whoosh",
      "suggested_emoji": "🐱",
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
                        temperature=0.92,
                        response_mime_type="application/json"
                    )
                )
                raw = resp.text.strip().lstrip("```json").rstrip("```").strip()
                data = json.loads(raw)
                return data
            except Exception as e:
                print(f"generate_motion_script [{model}]: {e}")
                last_err = e

        raise RuntimeError(f"All Gemini models failed: {last_err}")
