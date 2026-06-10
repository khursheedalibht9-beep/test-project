@echo off
title VideoCrafter
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  Python is not installed on this computer.
    echo  1. Go to  https://www.python.org/downloads/
    echo  2. Download and run the installer
    echo  3. IMPORTANT: tick the box "Add Python to PATH"
    echo  4. Then double-click this file again
    echo.
    pause
    exit /b 1
)

echo Installing requirements (first time only, takes a few minutes)...
python -m pip install -r requirements.txt

echo.
echo Starting VideoCrafter... your browser will open automatically.
echo Keep this black window open while you use the app.
echo.
python webapp.py
pause
