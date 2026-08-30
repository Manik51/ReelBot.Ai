# 💀 ReelBot.Ai - 1-Click Viral Short Video Creator

An automated, browser-based viral short video creator inspired by MoneyPrinterTurbo. Generate complete 60-second vertical videos (9:16) with **Gemini AI Scripting**, **Pexels & Pixabay HD Stock Footage**, **Hyper-realistic Kokoro/Edge-TTS Voiceovers**, and **Alex Hormozi Animated Word-by-Word Subtitles** — completely free with zero paid servers required.

---

### ⚡ Run Online in 1-Click (Google Colab - Fast Cloud GPU/CPU)

সার্ভার ছাড়া মাত্র ১ ক্লিকে হাই-স্পিড গুগল ক্লাউডে ReelBot চালাতে নিচের বাটনে ক্লিক করুন:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Manik51/ReelBot.Ai/blob/main/ReelBot_Colab.ipynb)

---

## ✨ Features & Architecture

* 🧠 **AI Viral Script Engine (Google Gemini API):**
  * Generates full 55-60s scripts with an instant 3-second hook to maximize viewer retention.
  * Automatically extracts scene-by-scene English visual keywords for stock footage searching.
  * Supports English, Bengali (বাংলা), Hindi (हिंदी), and Spanish.

* 🎥 **HD 9:16 Vertical Stock Footage (Pexels & Pixabay):**
  * Sourced directly from free tier APIs.
  * Automatic dynamic motion gradient fallback with fluid zoom/pan if no footage is returned.

* 🎙️ **Ultra-Realistic Voiceover (Kokoro / Edge-TTS):**
  * Supports English (Christopher, Guy, Sonia, Jenny), Bengali (Pradeep, Tanishaa), Hindi (Madhur, Swara).
  * Exact word boundary timestamp extraction for 100% synchronized word-by-word subtitle highlighting.
  * Custom speech rate control (+10%, +20%) for high-retention fast-paced pacing.

* 🔥 **Alex Hormozi Animated Captions (.ASS Subtitle Engine):**
  * Bold uppercase typography, heavy drop shadows, thick black outlines.
  * Dynamic active word highlight (Yellow, Neon Green, Cyber Cyan, Bold White).
  * Placed in the TikTok/YouTube Shorts safe zone (above bottom UI).

* 🎵 **Smart Audio Ducking & BGM:**
  * Automatically mixes background music under voiceover at ducked volume (10-15%).
  * Includes default energetic & lo-fi beats, plus custom MP3 upload support.

* 🌐 **Modern Glassmorphic Web App:**
  * **Step 1:** Topic input with 1-click viral ideas chips.
  * **Step 2:** Interactive Scene Editor (edit narration, visual tags, emojis).
  * **Step 3:** Studio Customizer (Voice, Subtitle Style, BGM, Speed).
  * **Step 4:** Real-time progress bar with live pipeline stage tracker.
  * **Step 5:** 9:16 In-browser Video Player with 1-click HD MP4 download.

---

## 🚀 How to Run the App

### Option 1: ☁️ Google Colab Cloud Runner (Recommended & Superfast)

১. **ফ্রি Ngrok Auth Token সংগ্রহ করুন:**
   * [Ngrok Sign Up পেজে যান](https://dashboard.ngrok.com/signup) এবং ফ্রিতে অ্যাকাউন্ট তৈরি করুন।
   * লগইন করে [Ngrok Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) পেজ থেকে আপনার টোকেনটি কপি করুন।

২. **Colab-এ চালু করার ধাপ:**
   * উপরের **[Open In Colab](https://colab.research.google.com/github/Manik51/ReelBot.Ai/blob/main/ReelBot_Colab.ipynb)** ব্যাজে ক্লিক করুন।
   * নোটবুকের ফর্মে আপনার `NGROK_AUTH_TOKEN`, `GEMINI_API_KEY`, এবং `PEXELS_API_KEY` বসিয়ে দিন।
   * বামপাশের **Play (▶)** বাটনে ক্লিক করুন।
   * ১ মিনিটের মধ্যে কোলাব আউটপুটে একটি লাইভ লিঙ্ক (`https://xxxx.ngrok-free.app`) পেয়ে যাবেন। সেই লিঙ্কে ক্লিক করলেই সম্পূর্ণ ওয়েব ইন্টারফেস লাইভ চালু হয়ে যাবে।

---

### Option 2: 💻 Local Machine Setup (Windows)

* **Quick Batch Launcher:**
  `start_app.bat` ফাইলে ডাবল-ক্লিক করুন। এটি স্বয়ংক্রিয়ভাবে সার্ভার চালু করে আপনার ব্রাউজারে `http://localhost:8000` ওপেন করবে।

* **Manual Command Line:**
  ```bash
  # ভার্চুয়াল এনভায়রনমেন্ট চালু ও স্ক্রিপ্ট রান
  python -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
  python run.py
🔑 Setting Up API Keys (100% Free)
​অ্যাপের নেভিগেশন বারের ⚙️ API Settings অপশনে গিয়ে কি-গুলো সেট করুন:
​Google Gemini API Key: Google AI Studio থেকে ফ্রি কী সংগ্রহ করুন।
​Pexels API Key: Pexels API থেকে ফ্রি কী নিন।
​Pixabay API Key: Pixabay API Docs থেকে ফ্রি কী সংগ্রহ করুন।
​(নোট: Pexels বা Pixabay কি না থাকলেও সিস্টেমের বিল্ট-ইন ডায়নামিক মোশন জেনারেটরের মাধ্যমে ভিডিও রেন্ডারিং সফলভাবে সম্পন্ন হবে)
​📂 Project Structure

ReelBot.Ai/
├── backend/
│   ├── config.py              # Application settings, presets & paths
│   ├── app.py                 # FastAPI server, endpoints & background tasks
│   └── services/
│       ├── gemini_service.py   # Gemini AI viral script generator
│       ├── tts_service.py      # Voiceover synthesis & word timestamp tracker
│       ├── media_service.py    # Pexels & Pixabay video search/download engine
│       ├── subtitle_service.py # Alex Hormozi animated ASS subtitle generator
│       └── video_composer.py  # FFmpeg composition, audio ducking & export
├── frontend/
│   ├── index.html             # Single Page Web App structure
│   ├── style.css              # Dark glassmorphic design & Hormozi animations
│   ├── app.js                 # Client-side workflow & real-time progress polling
│   └── assets/                # Logos & icons
├── storage/
│   ├── bgm/                   # Background music tracks (.mp3)
│   ├── outputs/               # Rendered final viral short videos (.mp4)
│   └── temp/                  # Workspace for clip chunks and temp files
├── ReelBot_Colab.ipynb        # 1-Click Google Colab Cloud Notebook
├── run.py                     # Entrypoint script with auto browser launch
├── start_app.bat              # Windows 1-click batch launcher
└── requirements.txt           # Python dependencies

🎯 Bengali Guide (ব্যবহার নির্দেশিকা)
​অ্যাপ চালু করুন: Google Colab-এর লিঙ্ক অথবা উইন্ডোজে start_app.bat ফাইলে ক্লিক করে অ্যাপ ওপেন করুন।
​API Key সেটআপ: উপরে ডানদিকের ⚙️ API Settings বাটনে ক্লিক করে ফ্রি Gemini ও Pexels API Key দিয়ে Save করুন।
​Topic নির্বাচন: ভিডিওর টপিক লিখুন (যেমন: 5 Dark Psychology Tricks That Actually Work) অথবা ভাইরাল আইডিয়া চিপসে ক্লিক করুন।
​Generate Script: Generate Viral Script বাটনে ক্লিক করলে Gemini AI দৃশ্যভিত্তিক চিত্রনাট্য ও ভিজ্যুয়াল কিওয়ার্ড তৈরি করে দেবে।
​Customization: নিজের পছন্দমতো ভয়েস (English / Bengali / Hindi), Alex Hormozi স্টাইল সাবটাইটেল এবং ব্যাকগ্রাউন্ড মিউজিক সিলেক্ট করুন।
​Generate Video: Generate Complete Video বাটনে ক্লিক করুন। কয়েক সেকেন্ডের মধ্যে ফুল HD 1080x1920 ভার্টিকাল রিল তৈরি হয়ে যাবে এবং ব্রাউজার থেকেই প্রিভিউ দেখে ডাউনলোড করতে পারবেন।
