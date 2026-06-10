#!/usr/bin/env bash
# VideoCrafter launcher - run with:  bash start_app_mac_linux.sh
cd "$(dirname "$0")"

PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
    echo "Python is not installed. Get it from https://www.python.org/downloads/"
    exit 1
fi

echo "Installing requirements (first time only, takes a few minutes)..."
"$PY" -m pip install -r requirements.txt

echo
echo "Starting VideoCrafter... your browser will open automatically."
echo "Keep this window open while you use the app."
echo
"$PY" webapp.py
