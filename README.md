# VideoCrafter 🎬

Generate a complete video **A to Z from just a topic** — like InVideo AI, but
**100% free**. No subscription, no watermark, no credit card.

Give it a topic, it does everything:

1. **Script** — writes a hook, story scenes, and an outro
2. **Voiceover** — natural AI voice (Microsoft Edge neural TTS, free, no key)
3. **Visuals** — real stock footage (free Pexels key) or generated backgrounds (no key)
4. **Captions** — bold animated word-chunk captions, Shorts/TikTok style
5. **Render** — final MP4 ready to upload

## Quick start

```bash
pip install -r requirements.txt

python -m videocrafter "black holes"
```

That's it. You get `black-holes.mp4` — a vertical Short with voiceover and
captions. Works with **zero API keys** out of the box (script comes from
Wikipedia, backgrounds are generated).

## Make it even better (still free)

All of these are optional and have free tiers that cost nothing:

| What | Where to get the free key | How to use |
|------|---------------------------|------------|
| Real stock video footage | [pexels.com/api](https://www.pexels.com/api/) | `export PEXELS_API_KEY=...` |
| Smarter AI scripts | [console.groq.com](https://console.groq.com) | `export GROQ_API_KEY=...` |
| Smarter AI scripts (alt) | [aistudio.google.com](https://aistudio.google.com) | `export GEMINI_API_KEY=...` |

With keys set, VideoCrafter automatically uses them — no config files needed.

## Options

```bash
python -m videocrafter "ancient Egypt" \
  --format landscape \
  --scenes 8 \
  --voice female \
  --rate "+10%" \
  --output my_video.mp4
```

- `--format`: `shorts` (default, vertical 9:16), `landscape`, or `square`
- `--scenes`: number of scenes including the hook and outro
- `--voice`: shortcuts like `male`, `female`, `uk-female`, `hindi-male`,
  `urdu-female`, or any voice name from `edge-tts --list-voices`
  (hundreds of voices, dozens of languages — all free)
- `--rate`: speaking speed, e.g. `"+10%"` or `"-5%"`

## How it stays free

- **Script**: Wikipedia (no key) or Groq / Gemini free tiers
- **Voice**: `edge-tts` — Microsoft Edge's neural voices, free and keyless
- **Footage**: Pexels free API, or locally generated gradient backgrounds
- **Editing/render**: MoviePy + FFmpeg, open source, runs on your machine

## Requirements

- Python 3.9+
- FFmpeg (installed automatically via `imageio-ffmpeg`)
- Internet connection (for script, voice, and footage)
