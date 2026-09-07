#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "      🚀 ReelBot.Ai — Google Cloud Shell Starter"
echo "=========================================================="

# 1. Ensure system packages (FFmpeg)
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 Installing FFmpeg on Cloud Shell..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg -qq
fi

# 2. Setup Python Virtual Environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# 3. Install/Update Dependencies
echo "📦 Checking and installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Check for .env Configuration
if [ ! -f ".env" ]; then
    echo "⚙️ Creating default .env file..."
    cat << 'EOF' > .env
# ReelBot API Keys (Add your keys here if needed)
GEMINI_API_KEY=
SERPER_API_KEY=
PEXELS_API_KEY=
PIXABAY_API_KEY=
EOF
    echo "⚠️ Note: You can edit .env anytime to add your GEMINI_API_KEY and SERPER_API_KEY."
fi

# 5. Launch FastAPI Backend on Port 8080 (Cloud Shell Web Preview Default)
echo ""
echo "=========================================================="
echo " ✅ ReelBot Studio is starting on Port 8080!"
echo " 👉 In Google Cloud Shell, look at the top-right toolbar:"
echo "    Click on the 'Web Preview' icon (eye/window icon)"
echo "    Select 'Preview on port 8080'"
echo " 👉 A new tab will open with your full ReelBot Studio!"
echo "=========================================================="
echo ""

exec python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
