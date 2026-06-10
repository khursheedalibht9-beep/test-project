"""Free voiceover using Microsoft Edge neural text-to-speech (edge-tts).

No API key, no account, no cost. Dozens of natural voices in many languages.
Try `edge-tts --list-voices` to see them all.
"""

import asyncio
import os
import re
import shutil
import subprocess

import edge_tts

DEFAULT_VOICE = "en-US-ChristopherNeural"

POPULAR_VOICES = {
    "male": "en-US-ChristopherNeural",
    "female": "en-US-AriaNeural",
    "uk-male": "en-GB-RyanNeural",
    "uk-female": "en-GB-SoniaNeural",
    "hindi-male": "hi-IN-MadhurNeural",
    "hindi-female": "hi-IN-SwaraNeural",
    "urdu-male": "ur-PK-AsadNeural",
    "urdu-female": "ur-PK-UzmaNeural",
}


def resolve_voice(name):
    return POPULAR_VOICES.get(name.lower(), name)


async def _synth(text, voice, rate, path):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(path)


def narrate_scenes_espeak(scenes, out_dir, rate="+0%"):
    """Offline fallback voice using espeak-ng (apt install espeak-ng).

    Robotic but free and needs no internet at all.
    """
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        return None
    percent = int(re.sub(r"[^0-9-]", "", rate) or 0)
    wpm = max(80, int(165 * (1 + percent / 100)))
    paths = []
    for i, scene in enumerate(scenes):
        path = os.path.join(out_dir, f"voice_{i:02d}.wav")
        subprocess.run(
            [espeak, "-v", "en-us", "-s", str(wpm), "-w", path, scene["text"]],
            check=True, capture_output=True,
        )
        paths.append(path)
        print(f"  voiced scene {i + 1}/{len(scenes)} (offline espeak voice)")
    return paths


def narrate_scenes(scenes, out_dir, voice=DEFAULT_VOICE, rate="+0%"):
    """Generate one audio file per scene. Returns list of file paths.

    Uses Edge neural TTS (free, natural voices); if that service is not
    reachable, falls back to offline espeak-ng when installed.
    """
    voice = resolve_voice(voice)
    paths = []

    async def run():
        for i, scene in enumerate(scenes):
            path = os.path.join(out_dir, f"voice_{i:02d}.mp3")
            await _synth(scene["text"], voice, rate, path)
            paths.append(path)
            print(f"  voiced scene {i + 1}/{len(scenes)}")

    try:
        asyncio.run(run())
        return paths
    except Exception as err:
        print(f"  Edge TTS not reachable ({type(err).__name__}); trying offline fallback...")
        fallback = narrate_scenes_espeak(scenes, out_dir, rate)
        if fallback:
            return fallback
        raise RuntimeError(
            "No TTS available: Edge TTS is unreachable on this network and "
            "espeak-ng is not installed (sudo apt install espeak-ng for an "
            "offline voice)."
        ) from err
