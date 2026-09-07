# 🚀 MoneyPrinterTurbo Custom (AI Viral Short Video Generator)

An automated, local-first, browser-based viral short video creator inspired by MoneyPrinterTurbo. 
Generate complete 60-second vertical videos (9:16) with **Gemini AI Scripting**, **Pexels & Pixabay HD Stock Footage**, **Hyper-realistic Kokoro/Edge-TTS Voiceovers**, and **Alex Hormozi Animated Word-by-Word Subtitles** — completely free with zero paid servers required.

---

## ✨ Features & Architecture

- 🧠 **AI Viral Script Engine (Google Gemini API)**:
  - Generates full 55-60s scripts with an instant 3-second hook to maximize viewer retention.
  - Automatically extracts scene-by-scene English visual keywords for stock footage searching.
  - Supports English, Bengali (বাংলা), Hindi (हिंदी), and Spanish.
- 🎥 **HD 9:16 Vertical Stock Footage (Pexels & Pixabay)**:
  - Sourced directly from free tier APIs.
  - Automatic dynamic motion gradient fallback with fluid zoom/pan if no footage is returned.
- 🎙️ **Ultra-Realistic Voiceover (Kokoro / Edge-TTS)**:
  - Supports English (Christopher, Guy, Sonia, Jenny), Bengali (Pradeep, Tanishaa), Hindi (Madhur, Swara).
  - Exact word boundary timestamp extraction for 100% synchronized word-by-word subtitle highlighting.
  - Custom speech rate control (+10%, +20%) for high-retention fast-paced pacing.
- 🔥 **Alex Hormozi Animated Captions (.ASS Subtitle Engine)**:
  - Bold uppercase typography, heavy drop shadows, thick black outlines.
  - Dynamic active word highlight (Yellow, Neon Green, Cyber Cyan, Bold White).
  - Placed in the TikTok/YouTube Shorts safe zone (above bottom UI).
- 🎵 **Smart Audio Ducking & BGM**:
  - Automatically mixes background music under voiceover at ducked volume (10-15%).
  - Includes default energetic & lo-fi beats, plus custom MP3 upload support.
- 🌐 **Modern Glassmorphic Web App**:
  - Step 1: Topic input with 1-click viral ideas chips.
  - Step 2: Interactive Scene Editor (edit narration, visual tags, emojis).
  - Step 3: Studio Customizer (Voice, Subtitle Style, BGM, Speed).
  - Step 4: Real-time progress bar with live pipeline stage tracker.
  - Step 5: 9:16 In-browser Video Player with 1-click HD MP4 download.

---

## 🚀 How to Run the Web App

### Option 1: Double-Click Quick Launcher (Windows)
Double-click `start_app.bat` inside the project folder:
```
C:\Users\MAITRAYEE\.gemini\antigravity\scratch\money-printer-turbo-custom\start_app.bat
```
This will automatically launch the server and open `http://localhost:8000` in your web browser.

### Option 2: Command Line
```powershell
cd C:\Users\MAITRAYEE\.gemini\antigravity\scratch\money-printer-turbo-custom
.\venv\Scripts\python.exe run.py
```

---

## 🔑 Setting Up API Keys (100% Free)

Click **⚙️ API Settings** in the top navigation bar of the web interface:

1. **Google Gemini API Key** (Required for AI scripts):
   - Get your free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. **Pexels API Key** (Recommended for free HD stock videos):
   - Get your free key from [Pexels API](https://www.pexels.com/api/).
3. **Pixabay API Key** (Recommended for free stock footage):
   - Get your free key from [Pixabay API Docs](https://pixabay.com/api/docs/).

*(Note: Even without Pexels/Pixabay keys, the system includes built-in dynamic motion video generator fallbacks to ensure video rendering never fails!)*

---

## 📂 Project Structure

```
money-printer-turbo-custom/
│
├── backend/
│   ├── config.py                 # Application settings, presets & paths
│   ├── app.py                    # FastAPI server, endpoints & background task runner
│   └── services/
│       ├── gemini_service.py     # Gemini AI viral script generator
│       ├── tts_service.py        # Voiceover synthesis & word timestamp tracker
│       ├── media_service.py      # Pexels & Pixabay video search/download engine
│       ├── subtitle_service.py   # Alex Hormozi animated ASS subtitle generator
│       └── video_composer.py     # FFmpeg composition, audio ducking & export
│
├── frontend/
│   ├── index.html                # Single Page Web App structure
│   ├── style.css                 # Dark glassmorphic design & Hormozi animations
│   └── app.js                    # Client-side workflow & real-time progress polling
│
├── storage/
│   ├── bgm/                      # Background music tracks (.mp3)
│   ├── outputs/                  # Rendered final viral short videos (.mp4)
│   └── temp/                     # Workspace for clip chunks and temp files
│
├── run.py                        # Entrypoint script with auto browser launch
├── start_app.bat                 # Windows 1-click batch launcher
└── requirements.txt              # Python dependencies
```

---

## 🎯 Bengali Guide (ব্যবহার নির্দেশিকা)

১. **অ্যাপটি চালু করুন**: `start_app.bat` ফাইলে ডাবল ক্লিক করুন। আপনার ব্রাউজারে `http://localhost:8000` স্বয়ংক্রিয়ভাবে খুলে যাবে।
২. **API Key দিন**: উপরে ডানদিকের **⚙️ API Settings** বাটনে ক্লিক করে আপনার ফ্রি **Gemini API Key** এবং **Pexels API Key** বসিয়ে Save করুন।
৩. **Topic লিখুন**: আপনার পছন্দের ভিডিও টপিক লিখুন (যেমন: *5 Dark Psychology Tricks That Actually Work*) অথবা Quick Ideas চিপসে ক্লিক করুন।
৪. **Generate Script**: `Generate Viral Script` বাটনে ক্লিক করলে Gemini AI সাথে সাথে ৩ সেকেন্ডের হুক সহ দৃশ্যভিত্তিক সম্পূর্ণ চিত্রনাট্য তৈরি করে দেবে।
৫. **Customization**: পছন্দমতো ভয়েস (English / Bengali / Hindi), Alex Hormozi সাবটাইটেল স্টাইল (Yellow / Green / Cyan) এবং ব্যাকগ্রাউন্ড মিউজিক সিলেক্ট করুন।
৬. **Generate Video**: `Generate Complete Video` বাটনে ক্লিক করুন। কয়েক সেকেন্ডের মধ্যে ফুল HD 1080x1920 ভার্টিকাল ভিডিও তৈরি হয়ে যাবে এবং আপনি প্রিভিউ দেখে সাথে সাথে ডাউনলোড করতে পারবেন!
