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
    SARVAM_API_KEY = os.getenv('SARVAM_API_KEY', '')
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
    PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY', '')

    # Video composition defaults
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    FPS = 30
    DEFAULT_BGM_VOLUME = 0.15

    # Pure Studio Quality Voice Presets (Sarvam AI + F5-TTS + Kokoro)
    VOICE_PRESETS = [
        # --- Sarvam AI (Hyper-Realistic Studio Voice - Bengali & Hindi) ---
        {'id': 'sarvam:meera', 'name': '🔥 Sarvam AI - Meera (Bengali/Hindi Female - Ultra Natural)', 'gender': 'Female', 'lang': 'Bengali', 'provider': 'sarvam', 'recommended_for': 'Bengali'},
        {'id': 'sarvam:amol', 'name': '🔥 Sarvam AI - Amol (Bengali/Hindi Male - Ultra Natural)', 'gender': 'Male', 'lang': 'Bengali', 'provider': 'sarvam', 'recommended_for': 'Bengali'},
        {'id': 'sarvam:arvind', 'name': '🔥 Sarvam AI - Arvind (Hindi/Bengali Deep Storyteller Male)', 'gender': 'Male', 'lang': 'Hindi', 'provider': 'sarvam', 'recommended_for': 'Hindi'},
        {'id': 'sarvam:pavithra', 'name': '✨ Sarvam AI - Pavithra (Expressive Female)', 'gender': 'Female', 'lang': 'Hindi', 'provider': 'sarvam', 'recommended_for': 'Hindi'},

        # --- F5-TTS (Local Studio Voice Cloning) ---
        {'id': 'f5:custom', 'name': '🎙️ F5-TTS Studio (Local Voice Clone)', 'gender': 'Custom', 'lang': 'Bengali', 'provider': 'f5', 'recommended_for': 'Bengali'},

        # --- Kokoro-82M SOTA (English Viral Voices) ---
        {'id': 'kokoro:am_adam', 'name': '🔥 Kokoro - Adam (Deep Viral Podcast Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:af_bella', 'name': '✨ Kokoro - Bella (Expressive Storyteller Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:am_michael', 'name': '🚀 Kokoro - Michael (Punchy Viral Shorts Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:af_sarah', 'name': '💎 Kokoro - Sarah (Crisp Professional Female)', 'gender': 'Female', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'},
        {'id': 'kokoro:am_george', 'name': '🎙️ Kokoro - George (British Cinematic Male)', 'gender': 'Male', 'lang': 'English', 'provider': 'kokoro', 'recommended_for': 'English'}
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
