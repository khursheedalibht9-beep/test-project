"""Concatenate the animated clips, mux the voiceover, burn in subtitles, export MP4."""
import subprocess
from pathlib import Path

from lines import SCENES

ROOT = Path(__file__).resolve().parent.parent
CLIP_DIR = ROOT / "assets" / "clips"
AUDIO_DIR = ROOT / "assets" / "audio"
SUB_PATH = ROOT / "assets" / "subtitles" / "captions.srt"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    concat_list = CLIP_DIR / "concat_list.txt"
    clip_paths = [(CLIP_DIR / f"scene_{s['id']}.mp4").resolve() for s in SCENES]
    concat_list.write_text("\n".join(f"file '{p}'" for p in clip_paths))

    silent_video = CLIP_DIR / "concat_video.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(silent_video)],
        check=True, capture_output=True,
    )

    with_audio = CLIP_DIR / "with_audio.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(silent_video), "-i", str(AUDIO_DIR / "voiceover_full.wav"),
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(with_audio)],
        check=True, capture_output=True,
    )

    final_path = OUT_DIR / "motivational_video.mp4"
    subs_filter = f"subtitles={SUB_PATH}:force_style='FontSize=20,PrimaryColour=&HFFFFFF&,Outline=2,Alignment=2,MarginV=40'"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(with_audio), "-vf", subs_filter,
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
         str(final_path)],
        check=True, capture_output=True,
    )
    print(f"exported {final_path}")


if __name__ == "__main__":
    main()
