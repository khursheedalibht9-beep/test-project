"""Free voiceover using Microsoft Edge neural text-to-speech (edge-tts).

No API key, no account, no cost. Dozens of natural voices in many languages.
Try `edge-tts --list-voices` to see them all.
"""

import asyncio
import os

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


def narrate_scenes(scenes, out_dir, voice=DEFAULT_VOICE, rate="+0%"):
    """Generate one MP3 per scene. Returns list of file paths."""
    voice = resolve_voice(voice)
    paths = []

    async def run():
        for i, scene in enumerate(scenes):
            path = os.path.join(out_dir, f"voice_{i:02d}.mp3")
            await _synth(scene["text"], voice, rate, path)
            paths.append(path)
            print(f"  voiced scene {i + 1}/{len(scenes)}")

    asyncio.run(run())
    return paths
