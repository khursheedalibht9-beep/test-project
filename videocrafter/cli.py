"""Command line interface: one topic in, one finished video out."""

import argparse
import os
import re
import sys
import tempfile

from . import script as script_mod
from . import visuals, voice
from .assemble import build_video

FORMATS = {
    "shorts": (1080, 1920),     # YouTube Shorts / TikTok / Reels
    "landscape": (1920, 1080),  # regular YouTube
    "square": (1080, 1080),     # Instagram feed
}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "video"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="videocrafter",
        description="Generate a complete video from just a topic - script, "
                    "voiceover, visuals, and captions. 100%% free.",
    )
    parser.add_argument("topic", help='what the video is about, e.g. "black holes"')
    parser.add_argument("-f", "--format", choices=FORMATS, default="shorts",
                        help="video format (default: shorts, vertical 9:16)")
    parser.add_argument("-s", "--scenes", type=int, default=6,
                        help="number of scenes including hook and outro (default: 6)")
    parser.add_argument("-v", "--voice", default=voice.DEFAULT_VOICE,
                        help="TTS voice: male, female, uk-male, hindi-female, urdu-male... "
                             "or any edge-tts voice name (default: %(default)s)")
    parser.add_argument("-r", "--rate", default="+5%",
                        help='speaking speed, e.g. "+10%%" or "-5%%" (default: +5%%)')
    parser.add_argument("-o", "--output", default=None,
                        help="output file (default: <topic>.mp4)")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--keep-temp", action="store_true",
                        help="keep intermediate audio/background files")
    args = parser.parse_args(argv)

    size = FORMATS[args.format]
    out_path = args.output or f"{slugify(args.topic)}.mp4"

    print(f"[1/4] Writing script for: {args.topic}")
    data = script_mod.generate_script(args.topic, n_scenes=max(3, args.scenes))
    scenes = data["scenes"]
    for i, s in enumerate(scenes):
        print(f"      {i + 1}. {s['text']}")

    workdir = tempfile.mkdtemp(prefix="videocrafter_")
    print(f"[2/4] Generating voiceover ({args.voice})")
    voice_paths = voice.narrate_scenes(scenes, workdir, voice=args.voice, rate=args.rate)

    print(f"[3/4] Gathering visuals ({args.format} {size[0]}x{size[1]})")
    backgrounds = visuals.gather_backgrounds(scenes, size, workdir)

    print("[4/4] Rendering video")
    build_video(scenes, voice_paths, backgrounds, size, out_path, fps=args.fps)

    if args.keep_temp:
        print(f"      temp files kept in {workdir}")
    else:
        for name in os.listdir(workdir):
            os.remove(os.path.join(workdir, name))
        os.rmdir(workdir)

    print(f"\nDone! -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
