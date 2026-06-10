"""Turn a topic into a narrated video script.

Free sources, in order of preference:
1. Groq free tier  (set GROQ_API_KEY)   - best quality scripts
2. Gemini free tier (set GEMINI_API_KEY) - great quality scripts
3. Wikipedia (no key, always free)       - factual fallback, works out of the box
"""

import json
import os
import re

import requests

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "is", "are", "was", "were", "be", "been", "it", "its", "this",
    "that", "these", "those", "as", "by", "from", "has", "have", "had", "he",
    "she", "they", "we", "you", "i", "his", "her", "their", "our", "your",
    "not", "no", "can", "will", "would", "could", "should", "may", "might",
    "also", "which", "who", "whom", "what", "when", "where", "how", "than",
    "then", "there", "here", "such", "into", "over", "under", "about", "most",
    "more", "some", "any", "all", "one", "two", "other", "many", "much",
}

LLM_PROMPT = """Write a short, engaging narration script for a video about: {topic}

Rules:
- Exactly {n} scenes.
- Scene 1 must be a strong hook (a question or surprising fact).
- The last scene must be a short outro inviting the viewer to like and subscribe.
- Each scene is 1-2 spoken sentences, conversational tone, no emojis, no hashtags.
- For each scene give 2-3 visual search keywords for stock footage.

Respond ONLY with JSON in this exact shape:
{{"title": "...", "scenes": [{{"text": "...", "keywords": "word word"}}]}}"""


def extract_keywords(text, topic, count=3):
    """Pick search keywords for stock footage from a sentence."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    # Prefer longer, rarer-looking words; keep order stable for determinism
    words = sorted(set(words), key=lambda w: (-len(w), w))[:count]
    if not words:
        words = [topic]
    return " ".join(words[:count])


def split_sentences(text):
    text = re.sub(r"\([^)]*\)", "", text)          # drop parentheticals
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _parse_llm_json(raw):
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no JSON found in LLM response")
    data = json.loads(match.group(0))
    if not data.get("scenes"):
        raise ValueError("LLM response has no scenes")
    return data


def script_from_groq(topic, n_scenes):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [{"role": "user", "content": LLM_PROMPT.format(topic=topic, n=n_scenes)}],
            "temperature": 0.8,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return _parse_llm_json(resp.json()["choices"][0]["message"]["content"])


def script_from_gemini(topic, n_scenes):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": key},
        json={"contents": [{"parts": [{"text": LLM_PROMPT.format(topic=topic, n=n_scenes)}]}]},
        timeout=60,
    )
    resp.raise_for_status()
    return _parse_llm_json(resp.json()["candidates"][0]["content"]["parts"][0]["text"])


def script_from_wikipedia(topic, n_scenes):
    """Keyless fallback: build a script from the Wikipedia intro of the topic."""
    api = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "VideoCrafter/0.1 (open source video generator)"}

    def get_json(params):
        resp = requests.get(api, params=params, headers=headers, timeout=30)
        try:
            resp.raise_for_status()
            return resp.json()
        except (requests.HTTPError, ValueError):
            raise RuntimeError(
                f"Wikipedia is not reachable from this network (HTTP {resp.status_code}). "
                "Check your connection/firewall, or set GROQ_API_KEY / GEMINI_API_KEY "
                "to use a free LLM for the script instead."
            )

    search = get_json({
        "action": "query", "list": "search", "srsearch": topic,
        "srlimit": 1, "format": "json",
    })
    hits = search.get("query", {}).get("search", [])
    if not hits:
        raise RuntimeError(f"Wikipedia has no article matching '{topic}'. "
                           "Try a broader topic, or set GROQ_API_KEY / GEMINI_API_KEY.")
    title = hits[0]["title"]

    page = get_json({
        "action": "query", "prop": "extracts", "explaintext": 1,
        "titles": title, "format": "json", "exintro": 0,
    })
    pages = page.get("query", {}).get("pages", {})
    extract = next(iter(pages.values())).get("extract", "")
    sentences = split_sentences(extract)
    if not sentences:
        raise RuntimeError(f"Could not read the Wikipedia article for '{topic}'.")

    body_count = max(1, n_scenes - 2)
    scenes = [{
        "text": f"Did you know this about {title}? Stick around, because what's coming might surprise you.",
        "keywords": title,
    }]
    for sentence in sentences[:body_count]:
        scenes.append({"text": sentence, "keywords": extract_keywords(sentence, title)})
    scenes.append({
        "text": f"And that's the story of {title}. If you learned something new, hit like and subscribe for more!",
        "keywords": f"{title} cinematic",
    })
    return {"title": title, "scenes": scenes}


def generate_script(topic, n_scenes=6):
    """Return {"title": str, "scenes": [{"text": str, "keywords": str}]}."""
    for source, fn in (("Groq", script_from_groq), ("Gemini", script_from_gemini)):
        try:
            data = fn(topic, n_scenes)
            if data:
                print(f"  script written by {source} (free tier)")
                return data
        except Exception as err:  # fall through to the next free source
            print(f"  {source} unavailable ({err}); trying next free source...")
    data = script_from_wikipedia(topic, n_scenes)
    print("  script built from Wikipedia (free, no key)")
    return data
