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
