"""Background visuals for each scene.

Free sources, tried in order for every scene:
1. Pexels stock VIDEO footage - needs a free key (https://www.pexels.com/api/)
2. Wikimedia Commons photos   - free, no key, matched to the scene keywords
3. Openverse photos           - free, no key, matched to the scene keywords
4. Generated gradient         - always works, even fully offline
"""

import io
import os
import random

import numpy as np
import requests
from PIL import Image

USER_AGENT = {"User-Agent": "VideoCrafter/0.1 (open source video generator)"}

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


def _save_image_from_url(url, path):
    """Download an image, validate it, normalize to RGB jpeg. Returns path or None."""
    resp = requests.get(url, headers=USER_AGENT, timeout=60)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    if img.width < 400 or img.height < 300:
        return None
    img.save(path, "JPEG", quality=90)
    return path


def fetch_commons_image(keywords, out_dir, idx, used):
    """Topic-matched photo from Wikimedia Commons. Free, no key."""
    resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "generator": "search",
        "gsrsearch": f"filetype:bitmap {keywords}", "gsrlimit": 8, "gsrnamespace": 6,
        "prop": "imageinfo", "iiprop": "url|size", "iiurlwidth": 1280, "format": "json",
    }, headers=USER_AGENT, timeout=30)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})
    for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url or url in used or info.get("width", 0) < 600:
            continue
        path = _save_image_from_url(url, os.path.join(out_dir, f"bg_{idx:02d}.jpg"))
        if path:
            used.add(url)
            return path
    return None


def fetch_openverse_image(keywords, out_dir, idx, used):
    """Topic-matched openly-licensed photo from Openverse. Free, no key."""
    resp = requests.get("https://api.openverse.org/v1/images/", params={
        "q": keywords, "page_size": 8,
    }, headers=USER_AGENT, timeout=30)
    resp.raise_for_status()
    for result in resp.json().get("results", []):
        url = result.get("url")
        if not url or url in used:
            continue
        try:
            path = _save_image_from_url(url, os.path.join(out_dir, f"bg_{idx:02d}.jpg"))
        except Exception:
            continue
        if path:
            used.add(url)
            return path
    return None


def gather_backgrounds(scenes, size, out_dir):
    """Return a list of {'type': 'video'|'image', 'path': str}, one per scene."""
    backgrounds = []
    used = set()
    have_pexels = bool(os.environ.get("PEXELS_API_KEY"))
    if not have_pexels:
        print("  tip: a free pexels.com/api key upgrades photos to stock video footage")
    for i, scene in enumerate(scenes):
        video = fetch_pexels_video(scene["keywords"], size, out_dir, i, used) if have_pexels else None
        if video:
            backgrounds.append({"type": "video", "path": video})
            print(f"  scene {i + 1}: stock footage ({scene['keywords']})")
            continue
        photo = None
        for source, fetch in (("Wikimedia Commons", fetch_commons_image),
                              ("Openverse", fetch_openverse_image)):
            try:
                photo = fetch(scene["keywords"], out_dir, i, used)
            except Exception as err:
                print(f"  {source} not reachable ({type(err).__name__})")
            if photo:
                print(f"  scene {i + 1}: photo from {source} ({scene['keywords']})")
                break
        if not photo:
            photo = make_gradient_image(size, seed=i, path=os.path.join(out_dir, f"bg_{i:02d}.png"))
            print(f"  scene {i + 1}: generated background")
        backgrounds.append({"type": "image", "path": photo})
    return backgrounds
