"""Offline unit tests - no network or API keys needed.

Run with: pytest
"""

import os

from videocrafter.assemble import caption_clips, chunk_text, find_font, fit_background
from videocrafter.cli import slugify
from videocrafter.script import extract_keywords, split_sentences
from videocrafter.visuals import make_gradient_image


def test_chunk_text_short_chunks():
    chunks = chunk_text("one two three four five six seven", max_words=4)
    assert chunks == ["one two three four", "five six seven"]
    assert chunk_text("hello") == ["hello"]


def test_extract_keywords_skips_stopwords():
    kw = extract_keywords("The gravity of a black hole is extreme", "space")
    assert "the" not in kw.split()
    assert "gravity" in kw or "extreme" in kw or "black" in kw


def test_extract_keywords_falls_back_to_topic():
    assert extract_keywords("it is so", "volcanoes") == "volcanoes"


def test_split_sentences_drops_parentheticals_and_short_bits():
    text = "Black holes (also called singularities) bend spacetime around them. Yes. They were predicted by Einstein over a century ago."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert "singularities" not in sentences[0]


def test_slugify():
    assert slugify("Black Holes!") == "black-holes"
    assert slugify("  ???  ") == "video"


def test_gradient_image(tmp_path):
    path = make_gradient_image((120, 200), seed=1, path=str(tmp_path / "g.png"))
    assert os.path.getsize(path) > 0
    from PIL import Image
    assert Image.open(path).size == (120, 200)


def test_fit_background_image(tmp_path):
    bg_path = make_gradient_image((120, 200), seed=2, path=str(tmp_path / "bg.png"))
    clip = fit_background({"type": "image", "path": bg_path}, (120, 200), 3.0)
    assert (clip.w, clip.h) == (120, 200)
    assert abs(clip.duration - 3.0) < 0.01
    clip.close()


def test_caption_clips_cover_full_duration():
    clips = caption_clips("a few words to show on screen here", 4.0, (540, 960), find_font())
    assert clips
    assert abs(sum(c.duration for c in clips) - 4.0) < 0.01
    assert clips[0].start == 0.0
    for clip in clips:
        clip.close()
