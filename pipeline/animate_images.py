"""Animate each scene image into a short video clip.

AnimateDiff needs a GPU and multi-GB motion-module weights, neither available
here, so this uses ffmpeg's zoompan filter to apply Ken Burns-style slow
zoom/pan motion to each still image instead -- a real, lightweight CPU motion
substitute rather than a faked AnimateDiff output.
"""
import json
import subprocess
from pathlib import Path

from lines import SCENES

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "images"
CLIP_DIR = ROOT / "assets" / "clips"
CLIP_DIR.mkdir(parents=True, exist_ok=True)

FPS = 30
W, H = 1280, 720

# alternate zoom-in and slow pan direction per scene for visual variety
MOTIONS = {
    1: ("zoom_in", None),
    2: ("zoom_in", "left"),
    3: ("zoom_in", None),
    4: ("pan", "right"),
    5: ("zoom_in", None),
    6: ("zoom_out", None),
}


def build_zoompan_expr(kind, pan, frames):
    if kind == "zoom_in":
        z = f"min(zoom+0.0006,1.18)"
    elif kind == "zoom_out":
        z = f"if(eq(on,0),1.18,max(zoom-0.0006,1.0))"
    else:
        z = "1.08"

    if pan == "left":
        x = "iw/2-(iw/zoom/2)+(on*0.6)"
        y = "ih/2-(ih/zoom/2)"
    elif pan == "right":
        x = "iw/2-(iw/zoom/2)-(on*0.6)"
        y = "ih/2-(ih/zoom/2)"
    else:
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"

    return z, x, y


def main():
    timing = json.loads((ROOT / "assets" / "timing.json").read_text())
    scene_starts = [s["start"] for s in timing["scenes"]]
    total = timing["total_duration"]
    # clip boundaries: scene 1's clip covers [0, scene2.start) so it includes
    # the lead-in silence; the last clip covers up to the very end.
    boundaries = [0.0] + scene_starts[1:] + [total]
    clip_durations = {
        scene["id"]: boundaries[i + 1] - boundaries[i]
        for i, scene in enumerate(SCENES)
    }

    for scene in SCENES:
        sid = scene["id"]
        duration = clip_durations[sid]
        frames = max(int(duration * FPS), 1)
        kind, pan = MOTIONS[sid]
        z, x, y = build_zoompan_expr(kind, pan, frames)

        in_path = IMG_DIR / f"scene_{sid}.png"
        out_path = CLIP_DIR / f"scene_{sid}.mp4"
        vf = (
            f"scale={W * 2}:{H * 2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
        )
        subprocess.run(
            ["ffmpeg", "-y", "-loop", "1", "-i", str(in_path),
             "-vf", vf, "-t", f"{duration:.3f}",
             "-pix_fmt", "yuv420p", str(out_path)],
            check=True, capture_output=True,
        )
        print(f"scene {sid}: {duration:.2f}s -> {out_path.name}")


if __name__ == "__main__":
    main()
