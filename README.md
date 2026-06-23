# test-project

## "Rise Anyway" — 45-second motivational video

A full script-to-MP4 pipeline. See [`script/script.md`](script/script.md) for the
script/narration and [`prompts/flux_prompts.md`](prompts/flux_prompts.md) for the 6
FLUX image prompts.

**Sandbox constraints (read before re-running):** this environment has no GPU and no
hosted image/video API keys, and its network policy blocks Microsoft's Edge-TTS
endpoint (`speech.platform.bing.com` returns 403). So three steps use real,
CPU-only, fully offline substitutes instead of faking output:

| Requested | Used here | Why |
|---|---|---|
| FLUX images | Pillow-generated gradient/silhouette cards (`pipeline/generate_images.py`) | No GPU / model weights / API key available |
| AnimateDiff | ffmpeg `zoompan` Ken Burns pan/zoom (`pipeline/animate_images.py`) | Same — AnimateDiff needs a GPU motion module |
| Edge-TTS | espeak-ng offline TTS (`pipeline/generate_voiceover.py`) | Edge-TTS's endpoint is blocked by this sandbox's egress policy |

The FLUX prompts in `prompts/flux_prompts.md` are real, ready to use on a machine
with FLUX access — swapping in actual renders just means replacing the PNGs in
`assets/images/` before running `animate_images.py`. Likewise the script is
written so any real Edge-TTS/AnimateDiff output could drop in for its substitute.

### Run it

```bash
apt-get install -y ffmpeg espeak-ng
pip install pillow
cd pipeline
python3 main.py
```

Output: `output/motivational_video.mp4` (1280x720, 45.00s, H.264 + AAC, burned-in
subtitles).

### Pipeline stages

1. `generate_voiceover.py` — synthesizes each line, measures real durations, and
   times the pauses so the full track lands on exactly 45s. Writes
   `assets/timing.json`, which every later stage reads for sync.
2. `generate_images.py` — renders the 6 scene visuals.
3. `animate_images.py` — applies per-scene Ken Burns motion sized to the scene's
   timing window.
4. `generate_subtitles.py` — builds `assets/subtitles/captions.srt` from the same
   timing data.
5. `build_video.py` — concatenates the clips, muxes in the voiceover, burns in
   subtitles, and exports the final MP4.
