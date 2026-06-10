"""Background visuals for each scene.

- With a free Pexels API key (https://www.pexels.com/api/ - free forever,
  generous limits): real stock video footage matched to each scene.
- Without any key: pretty generated gradient backgrounds, so the pipeline
  still works completely offline-from-APIs and at zero cost.
"""

import os
import random

import numpy as np
import requests
from PIL import Image

PALETTES = [
    ((24, 26, 56), (94, 53, 177)),    # midnight purple
    ((10, 36, 64), (0, 121, 145)),    # deep ocean
    ((40, 12, 38), (199, 64, 92)),    # plum to rose
    ((12, 40, 28), (26, 148, 109)),   # forest emerald
    ((38, 24, 8), (191, 110, 33)),    # amber dusk
    ((16, 18, 30), (66, 99, 235)),    # electric night
]


def make_gradient_image(size, seed, path):
    """Generate a smooth diagonal gradient PNG as a fallback background."""
    width, height = size
    rng = random.Random(seed)
    top, bottom = rng.choice(PALETTES)

    y = np.linspace(0.0, 1.0, height)[:, None]
    x = np.linspace(0.0, 0.35, width)[None, :]
    t = np.clip(y + x * rng.choice([-1, 1]), 0.0, 1.0)[..., None]
    pixels = (np.array(top) * (1 - t) + np.array(bottom) * t).astype(np.uint8)
    # subtle vignette so captions pop
    yy = (np.linspace(-1, 1, height) ** 2)[:, None]
    xx = (np.linspace(-1, 1, width) ** 2)[None, :]
    vignette = (1 - 0.35 * np.clip(xx + yy, 0, 1))[..., None]
    pixels = (pixels * vignette).astype(np.uint8)

    Image.fromarray(pixels).save(path)
    return path


def fetch_pexels_video(keywords, size, out_dir, idx, used_ids):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    width, height = size
    orientation = "portrait" if height > width else "landscape"
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": keywords, "per_page": 10, "orientation": orientation},
            timeout=30,
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        for video in videos:
            if video["id"] in used_ids:
                continue
            files = [f for f in video.get("video_files", []) if f.get("height")]
            if not files:
                continue
            # smallest file that still covers the output height = fast + sharp
            files.sort(key=lambda f: (f["height"] < height, abs(f["height"] - height)))
            url = files[0]["link"]
            path = os.path.join(out_dir, f"bg_{idx:02d}.mp4")
            with requests.get(url, stream=True, timeout=120) as dl:
                dl.raise_for_status()
                with open(path, "wb") as fh:
                    for chunk in dl.iter_content(1 << 16):
                        fh.write(chunk)
            used_ids.add(video["id"])
            return path
    except Exception as err:
        print(f"  Pexels fetch failed for '{keywords}' ({err}); using gradient")
    return None


def gather_backgrounds(scenes, size, out_dir):
    """Return a list of {'type': 'video'|'image', 'path': str}, one per scene."""
    backgrounds = []
    used_ids = set()
    have_pexels = bool(os.environ.get("PEXELS_API_KEY"))
    if not have_pexels:
        print("  no PEXELS_API_KEY set - using generated gradient backgrounds "
              "(get a free key at pexels.com/api for real stock footage)")
    for i, scene in enumerate(scenes):
        video = fetch_pexels_video(scene["keywords"], size, out_dir, i, used_ids) if have_pexels else None
        if video:
            backgrounds.append({"type": "video", "path": video})
            print(f"  stock footage found for scene {i + 1} ({scene['keywords']})")
        else:
            path = make_gradient_image(size, seed=i, path=os.path.join(out_dir, f"bg_{i:02d}.png"))
            backgrounds.append({"type": "image", "path": path})
    return backgrounds
