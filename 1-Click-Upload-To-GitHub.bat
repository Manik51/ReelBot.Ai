@echo off
title ReelBot.Ai - 1-Click GitHub Uploader
color 0C

echo ========================================================
echo       REELBOT.AI - AUTOMATIC 1-CLICK GITHUB UPLOADER
echo ========================================================
echo.

set /p REPO_URL="Enter your GitHub Repository URL (Right-click to Paste): "

if "%REPO_URL%"=="" (
    echo Error: You did not enter a repository URL!
    pause
    exit /b
)

echo.
echo [1/5] Initializing Git repository...
git init

echo.
echo [2/5] Adding project files...
git add .

echo.
echo [3/5] Creating commit...
git commit -m "Deploy ReelBot.Ai with PWA and YouTube SEO"

echo.
echo [4/5] Setting main branch...
git branch -M main

echo.
echo [5/5] Connecting to GitHub...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo Uploading to GitHub... (Please sign in if a browser window opens)
git push -u origin main

echo.
echo ========================================================
echo   UPLOAD COMPLETE! Refresh your GitHub page now.
echo ========================================================
echo.
pause
