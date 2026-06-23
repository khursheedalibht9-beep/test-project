"""Generate per-scene voiceover with espeak-ng and time the gaps to hit ~45s total.

Edge-TTS was the requested engine, but this sandbox's network policy blocks
speech.platform.bing.com (confirmed: explicit 403, not a transient failure), so
espeak-ng is used as the offline substitute -- it needs no network access at all.
"""
import json
import subprocess
from pathlib import Path

from lines import SCENES

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "assets" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

VOICE = "en-us+m3"
RATE_WPM = 130
TARGET_TOTAL_SECONDS = 45.0
LEAD_IN = 1.0
TAIL_OUT = 0.8


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def synthesize_line(scene_id: int, text: str) -> Path:
    out_path = AUDIO_DIR / f"scene_{scene_id}.wav"
    subprocess.run(
        ["espeak-ng", "-v", VOICE, "-s", str(RATE_WPM), "-w", str(out_path), text],
        check=True,
    )
    return out_path


def make_silence(path: Path, seconds: float):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
         "-t", f"{max(seconds, 0.05):.3f}", str(path)],
        check=True, capture_output=True,
    )


def main():
    durations = {}
    for scene in SCENES:
        wav = synthesize_line(scene["id"], scene["line"])
        durations[scene["id"]] = probe_duration(wav)

    speech_total = sum(durations.values())
    fixed_total = LEAD_IN + TAIL_OUT
    remaining = TARGET_TOTAL_SECONDS - speech_total - fixed_total
    gap = max(remaining / (len(SCENES) - 1), 0.3)

    timeline = []
    cursor = LEAD_IN
    make_silence(AUDIO_DIR / "lead_in.wav", LEAD_IN)
    concat_list = [AUDIO_DIR / "lead_in.wav"]

    for i, scene in enumerate(SCENES):
        start = cursor
        dur = durations[scene["id"]]
        end = start + dur
        timeline.append({"id": scene["id"], "title": scene["title"],
                          "line": scene["line"], "start": start, "end": end})
        concat_list.append(AUDIO_DIR / f"scene_{scene['id']}.wav")
        cursor = end
        if i < len(SCENES) - 1:
            silence_path = AUDIO_DIR / f"gap_{scene['id']}.wav"
            make_silence(silence_path, gap)
            concat_list.append(silence_path)
            cursor += gap

    make_silence(AUDIO_DIR / "tail_out.wav", TAIL_OUT)
    concat_list.append(AUDIO_DIR / "tail_out.wav")
    cursor += TAIL_OUT

    list_file = AUDIO_DIR / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in concat_list))

    full_path = AUDIO_DIR / "voiceover_full.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         str(full_path)],
        check=True, capture_output=True,
    )

    total_duration = probe_duration(full_path)

    timing = {
        "lead_in": LEAD_IN, "gap": gap, "tail_out": TAIL_OUT,
        "total_duration": total_duration, "scenes": timeline,
    }
    (ROOT / "assets" / "timing.json").write_text(json.dumps(timing, indent=2))

    print(f"Speech total: {speech_total:.2f}s | gap: {gap:.2f}s | "
          f"final track: {total_duration:.2f}s")
    for t in timeline:
        print(f"  scene {t['id']}: {t['start']:.2f}s -> {t['end']:.2f}s  "
              f"\"{t['line']}\"")


if __name__ == "__main__":
    main()
