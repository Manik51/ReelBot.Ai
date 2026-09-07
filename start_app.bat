@echo off
title ReelBot.Ai - Launcher
color 0C

echo =========================================================
echo   💀 ReelBot.Ai (Beta) - AI Viral Shorts Creator
echo   Starting server at http://localhost:8000 ...
echo =========================================================
echo.

cd /d "C:\Users\MAITRAYEE\.gemini\antigravity\scratch\money-printer-turbo-custom"

:: Open Browser automatically
start "" "http://localhost:8000"

:: Start Uvicorn Python Server
venv\Scripts\python.exe run.py

pause
