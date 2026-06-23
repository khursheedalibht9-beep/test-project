"""Render 6 stand-in scene visuals.

FLUX can't run in this sandbox (no GPU, no model weights, no hosted API key),
so these are programmatically generated gradient/silhouette cards that follow
the same scene composition described in prompts/flux_prompts.md. They're a
placeholder for the real FLUX renders, not a replacement for them.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from lines import SCENES

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vertical_gradient(top, bottom):
    img = Image.new("RGB", (W, H), top)
    top_rgb, bottom_rgb = hex2rgb(top), hex2rgb(bottom)
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def figure_silhouette(draw, cx, base_y, scale=1.0, arms_up=False, lean=0):
    color = (8, 8, 12)
    head_r = 14 * scale
    body_h = 90 * scale
    draw.ellipse([cx - head_r + lean, base_y - body_h - head_r * 2,
                  cx + head_r + lean, base_y - body_h], fill=color)
    if arms_up:
        draw.line([cx + lean, base_y - body_h, cx - 35 * scale, base_y - body_h - 60 * scale],
                   fill=color, width=int(8 * scale))
        draw.line([cx + lean, base_y - body_h, cx + 35 * scale, base_y - body_h - 60 * scale],
                   fill=color, width=int(8 * scale))
    draw.polygon([
        (cx - 18 * scale + lean, base_y),
        (cx + 18 * scale + lean, base_y),
        (cx + 10 * scale, base_y - body_h),
        (cx - 10 * scale, base_y - body_h),
    ], fill=color)


def scene_1(img):
    d = ImageDraw.Draw(img)
    random.seed(1)
    for _ in range(80):
        x, y = random.randint(0, W), random.randint(0, H // 2)
        b = random.randint(120, 220)
        d.ellipse([x, y, x + 1, y + 1], fill=(b, b, b))
    d.line([(0, H * 0.72), (W, H * 0.7)], fill=(60, 80, 130), width=3)
    figure_silhouette(d, W // 2, int(H * 0.85), scale=1.6)
    return img


def scene_2(img):
    d = ImageDraw.Draw(img)
    random.seed(2)
    for _ in range(60):
        x = random.randint(0, W)
        y = random.randint(0, H // 2)
        d.line([(x, y), (x - 25, y + 90)], fill=(150, 160, 180), width=1)
    bolt = [(W * 0.65, 0), (W * 0.6, H * 0.25), (W * 0.68, H * 0.25), (W * 0.55, H * 0.55)]
    d.line(bolt, fill=(230, 230, 255), width=4)
    figure_silhouette(d, W // 2, int(H * 0.9), scale=1.3, lean=-6)
    return img


def scene_3(img):
    d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.55, -H * 0.2, W * 1.2, H * 0.5], fill=(255, 210, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, glow, 0.55)
    d = ImageDraw.Draw(img)
    figure_silhouette(d, W // 2, int(H * 0.88), scale=1.5)
    return img


def scene_4(img):
    d = ImageDraw.Draw(img)
    random.seed(4)
    for i in range(6):
        y = int(H * 0.55 + i * 18)
        d.line([(0, y), (W, y - 60)], fill=(70, 45, 20), width=10)
    path_x = int(W * 0.5)
    figure_silhouette(d, path_x, int(H * 0.82), scale=1.4, lean=8)
    for _ in range(40):
        x, y = random.randint(int(W * 0.3), int(W * 0.7)), random.randint(int(H * 0.6), H)
        d.ellipse([x, y, x + 2, y + 2], fill=(180, 140, 90))
    return img


def scene_5(img):
    cx, cy = int(W * 0.5), int(H * 0.32)
    d = ImageDraw.Draw(img)
    for i in range(24):
        ang = i * (2 * math.pi / 24)
        x2 = cx + math.cos(ang) * W
        y2 = cy + math.sin(ang) * W
        d.line([(cx, cy), (x2, y2)], fill=(255, 230, 180), width=2)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 220, cy - 220, cx + 220, cy + 220], fill=(255, 200, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img = Image.blend(img, glow, 0.6)
    d = ImageDraw.Draw(img)
    figure_silhouette(d, int(W * 0.5), int(H * 0.85), scale=1.5)
    return img


def scene_6(img):
    d = ImageDraw.Draw(img)
    sun_cx, sun_cy = int(W * 0.5), int(H * 0.62)
    d.ellipse([sun_cx - 90, sun_cy - 90, sun_cx + 90, sun_cy + 90], fill=(255, 250, 210))
    for i in range(16):
        ang = i * (2 * math.pi / 16)
        x2 = sun_cx + math.cos(ang) * 420
        y2 = sun_cy + math.sin(ang) * 420
        d.line([(sun_cx, sun_cy), (x2, y2)], fill=(255, 240, 190), width=3)
    d.polygon([(0, H * 0.78), (W * 0.45, H * 0.55), (W * 0.6, H * 0.78)], fill=(20, 12, 8))
    figure_silhouette(d, int(W * 0.45), int(H * 0.62), scale=1.5, arms_up=True)
    return img


RENDERERS = {1: scene_1, 2: scene_2, 3: scene_3, 4: scene_4, 5: scene_5, 6: scene_6}


def main():
    for scene in SCENES:
        top, bottom = scene["palette"]
        img = vertical_gradient(top, bottom)
        img = RENDERERS[scene["id"]](img)
        img = img.filter(ImageFilter.GaussianBlur(0.6))
        out_path = IMG_DIR / f"scene_{scene['id']}.png"
        img.save(out_path)
        print(f"saved {out_path}")


if __name__ == "__main__":
    main()
