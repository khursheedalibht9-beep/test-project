"""Stitch voiceover, backgrounds, and word-chunk captions into the final MP4."""

import glob
import os
import re

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    for pattern in ("/usr/share/fonts/**/*Bold*.ttf", "/usr/share/fonts/**/*.ttf"):
        found = sorted(glob.glob(pattern, recursive=True))
        if found:
            return found[0]
    return None  # moviepy/pillow default font


def chunk_text(text, max_words=4):
    """Split narration into short caption chunks, TikTok/Shorts style."""
    words = re.sub(r"\s+", " ", text).strip().split(" ")
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def fit_background(background, size, duration):
    """Load a background and make it exactly `size` for `duration` seconds."""
    width, height = size
    if background["type"] == "video":
        clip = VideoFileClip(background["path"]).without_audio()
        if clip.duration < duration:
            clip = clip.with_effects([vfx.Loop(duration=duration)])
        clip = clip.subclipped(0, duration)
        # cover-crop to the target aspect ratio
        scale = max(width / clip.w, height / clip.h)
        clip = clip.resized(scale)
        clip = clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=width, height=height)
    else:
        clip = ImageClip(background["path"]).with_duration(duration)
        # cover-crop photos of any aspect ratio to fill the frame
        scale = max(width / clip.w, height / clip.h)
        clip = clip.resized(scale)
        clip = clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=width, height=height)
        # gentle Ken Burns zoom so still photos feel alive
        clip = clip.resized(lambda t: 1.0 + 0.04 * (t / max(duration, 0.1)))
        clip = CompositeVideoClip([clip.with_position("center")], size=size).with_duration(duration)
    return clip


def caption_clips(text, duration, size, font):
    """Timed caption chunks, sized to the spoken audio of the scene."""
    width, height = size
    chunks = chunk_text(text)
    total_chars = sum(len(c) for c in chunks) or 1
    clips = []
    cursor = 0.0
    for chunk in chunks:
        chunk_dur = duration * len(chunk) / total_chars
        txt = TextClip(
            font=font,
            text=chunk.upper(),
            font_size=max(34, int(width * 0.055)),
            color="white",
            stroke_color="black",
            stroke_width=max(2, int(width * 0.004)),
            method="caption",
            size=(int(width * 0.85), None),
            text_align="center",
            margin=(0, max(8, int(width * 0.02))),  # keep stroke/descenders from clipping
        )
        txt = (txt.with_start(cursor)
                  .with_duration(chunk_dur)
                  .with_position(("center", int(height * 0.70))))
        clips.append(txt)
        cursor += chunk_dur
    return clips


def build_video(scenes, voice_paths, backgrounds, size, out_path, fps=30):
    font = find_font()
    scene_clips = []
    for i, scene in enumerate(scenes):
        audio = AudioFileClip(voice_paths[i])
        duration = audio.duration + 0.35  # small breath between scenes
        bg = fit_background(backgrounds[i], size, duration)
        captions = caption_clips(scene["text"], audio.duration, size, font)
        composed = CompositeVideoClip([bg, *captions], size=size).with_duration(duration)
        composed = composed.with_audio(audio)
        scene_clips.append(composed)
        print(f"  composed scene {i + 1}/{len(scenes)} ({duration:.1f}s)")

    final = concatenate_videoclips(scene_clips, method="compose")
    final.write_videofile(
        out_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=os.cpu_count() or 2,
        logger=None,
    )
    for clip in scene_clips:
        clip.close()
    return out_path
