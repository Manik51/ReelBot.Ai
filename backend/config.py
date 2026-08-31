import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Settings:
    BASE_DIR = BASE_DIR
    STORAGE_DIR = BASE_DIR / 'storage'
    TEMP_DIR = BASE_DIR / 'storage' / 'temp'
    OUTPUTS_DIR = BASE_DIR / 'storage' / 'outputs'
    MODELS_DIR = BASE_DIR / 'storage' / 'models'
    ASSETS_DIR = BASE_DIR / 'backend' / 'assets'
    FONTS_DIR = ASSETS_DIR / 'fonts'
    BGM_DIR = ASSETS_DIR / 'bgm'
    SFX_DIR = ASSETS_DIR / 'sfx'

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
    PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY', '')

    # Video composition defaults
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    FPS = 30
    DEFAULT_BGM_VOLUME = 0.15

    # Voice Presets with Crystal-Clear Native Pronunciation
    VOICE_PRESETS = [
        # Hindi Native Ultra-Clear Studio Voices (100% Crystal-Clear Native Pronunciation)
        {'id': 'hi-IN-MadhurNeural', 'name': '🇮🇳 Madhur (Hindi Male - Deep Viral Storyteller)', 'gender': 'Male', 'lang': 'Hindi', 'provider': 'edge', 'recommended_for': 'Hindi'},
        {'id': 'hi-IN-SwaraNeural', 'name': '🇮🇳 Swara (Hindi Female - Expressive & Engaging)', 'gender': 'Female', 'lang': 'Hindi', 'provider': 'edge', 'recommended_for': 'Hindi'},

        # Bengali Native Ultra-Clear Studio Voices (100% Crystal-Clear Native Pronunciation)
        {'id': 'bn-IN-TanishaaNeural', 'name': '🇮🇳 Tanishaa (Bengali Female - High-Energy Viral)', 'gender': 'Female', 'lang': 'Bengali', 'provider': 'edge', 'recommended_for': 'Bengali'},
        {'id': 'bn-BD-PradeepNeural', 'name': '🇧🇩 Pradeep (Bengali Male - Deep Storyteller)', 'gender': 'Male', 'lang': 'Bengali', 'provider': 'edge', 'recommended_for': 'Bengali'},
        {'id': 'bn-BD-NabanitaNeural', 'name': '🇧🇩 Nabanita (Bengali Female - Sweet & Clear)', 'gender': 'Female', 'lang': 'Bengali', 'provider': 'edge', 'recommended_for': 'Bengali'},
        {'id': 'bn-IN-BashkarNeural', 'name': '🇮🇳 Bashkar (Bengali Male - Natural & Smooth)', 'gender': 'Male', 'lang': 'Bengali', 'provider': 'edge', 'recommended_for': 'Bengali'},

        # English SOTA Kokoro-82M Open-Source Voices (ElevenLabs Competitor)
        {'id': 'kokoro:am_adam', 'name': '🔥 Kokoro - Adam (Deep Viral Podcast Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:af_bella', 'name': '✨ Kokoro - Bella (Expressive Storyteller Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:am_michael', 'name': '🚀 Kokoro - Michael (Punchy Viral Shorts Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:af_sarah', 'name': '💎 Kokoro - Sarah (Crisp Professional Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:af_nicole', 'name': '🌟 Kokoro - Nicole (Warm Smooth Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:am_george', 'name': '🎙️ Kokoro - George (British Cinematic Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},

        # English Multilingual Broadcast Neural Voices
        {'id': 'en-US-AndrewMultilingualNeural', 'name': '🇺🇸 Andrew (Natural Multilingual Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'edge', 'recommended_for': 'English'},
        {'id': 'en-US-AvaMultilingualNeural', 'name': '🇺🇸 Ava (Natural Multilingual Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'edge', 'recommended_for': 'English'},
        {'id': 'en-US-BrianMultilingualNeural', 'name': '🇺🇸 Brian (Deep Cinematic Storyteller)', 'gender': 'Male', 'lang': 'English', 'provider': 'edge', 'recommended_for': 'English'},
        {'id': 'en-US-EmmaMultilingualNeural', 'name': '🇺🇸 Emma (Emotional Storyteller Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'edge', 'recommended_for': 'English'},
        {'id': 'en-US-ChristopherNeural', 'name': '🇺🇸 Christopher (High-Energy Shorts Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'edge', 'recommended_for': 'English'},
        
        # --- Sarvam AI (Hyper-Realistic Studio Voices) ---
        {"id": "sarvam:meera", "name": "🔥 Sarvam AI - Meera (Bengali/Hindi Female - Ultra Natural)", "language": "Indic"},
        {"id": "sarvam:amol", "name": "🔥 Sarvam AI - Amol (Bengali/Hindi Male - Ultra Natural)", "language": "Indic"},
        {"id": "sarvam:arvind", "name": "🔥 Sarvam AI - Arvind (Deep Storyteller Male)", "language": "Indic"},
    
        # --- F5-TTS (Local Studio Cloning) ---
        {"id": "f5:custom", "name": "🎙️ F5-TTS Studio (Local Voice Clone)", "language": "Multi"},
     ]

    # Alex Hormozi Subtitle Styles
    SUBTITLE_STYLES = [
        {
            'id': 'hormozi_yellow',
            'name': '🔥 Hormozi Viral Yellow',
            'primary_color': '&H00FFFFFF',      # Pure White
            'highlight_color': '&H0000E5FF',    # Vibrant Yellow (&H00BBGGRR)
            'outline_color': '&H00000000',      # Black Outline
            'shadow_color': '&H80000000',       # Dark Shadow
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'hormozi_green',
            'name': '⚡ Neon Green Beast',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H0066FF00',    # Neon Green
            'outline_color': '&H00000000',
            'shadow_color': '&H80000000',
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'cyber_cyan',
            'name': '🌐 Cyber Neon Cyan',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H00FFFF00',    # Cyan
            'outline_color': '&H00000000',
            'shadow_color': '&H80000000',
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'crimson_wine',
            'name': '🍷 Crimson Wine Red',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H003A1EC4',    # Crimson Wine
            'outline_color': '&H00000000',
            'shadow_color': '&H80000000',
            'font_size': 76,
            'font_name': 'Impact',
            'bold': 1,
            'max_words_per_line': 3
        },
        {
            'id': 'bold_white',
            'name': '✨ Clean Bold White',
            'primary_color': '&H00FFFFFF',
            'highlight_color': '&H00FFFFFF',
            'outline_color': '&H00000000',
            'shadow_color': '&H99000000',
            'font_size': 72,
            'font_name': 'Arial Black',
            'bold': 1,
            'max_words_per_line': 4
        }
    ]

settings = Settings()
