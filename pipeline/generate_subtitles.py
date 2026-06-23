"""Build an SRT subtitle file synced to the per-scene narration timing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    timing = json.loads((ROOT / "assets" / "timing.json").read_text())
    lines = []
    for i, scene in enumerate(timing["scenes"], start=1):
        lines.append(str(i))
        lines.append(f"{fmt_ts(scene['start'])} --> {fmt_ts(scene['end'])}")
        lines.append(scene["line"])
        lines.append("")

    out_path = ROOT / "assets" / "subtitles" / "captions.srt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
