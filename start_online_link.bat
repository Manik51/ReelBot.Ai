@echo off
title ReelBot.Ai (Beta) - 1-Click Free Online Launcher
echo =========================================================
echo   💀 ReelBot.Ai (Beta) - 1-Click Free Online Launcher
echo   Starting server & Generating 100%% Free Live HTTPS Link...
echo =========================================================
cd /d "%~dp0"
call venv\Scripts\python.exe run_with_public_link.py
pause
