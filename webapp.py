"""VideoCrafter web app - type a topic in your browser, get a video.

Run:  python webapp.py
Then open the link it prints (http://127.0.0.1:7860).
"""

import argparse
import os
import tempfile

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

try:
    import gradio as gr
except ImportError:
    raise SystemExit("Gradio is not installed. Run:  pip install gradio")

from videocrafter import script as script_mod
from videocrafter import visuals, voice
from videocrafter.assemble import build_video
from videocrafter.cli import FORMATS, slugify

VOICE_CHOICES = list(voice.POPULAR_VOICES.keys())


def create_video(topic, video_format, voice_name, scenes, fast_preview,
                 pexels_key, progress=gr.Progress()):
    topic = (topic or "").strip()
    if not topic:
        raise gr.Error("Please type a topic first.")
    if pexels_key and pexels_key.strip():
        os.environ["PEXELS_API_KEY"] = pexels_key.strip()

    size = FORMATS[video_format]
    fps = 30
    if fast_preview:
        size = (size[0] // 2, size[1] // 2)
        fps = 24

    workdir = tempfile.mkdtemp(prefix="videocrafter_")
    progress(0.05, desc="Writing script...")
    data = script_mod.generate_script(topic, n_scenes=int(scenes))
    scene_list = data["scenes"]

    progress(0.25, desc="Generating voiceover...")
    voice_paths = voice.narrate_scenes(scene_list, workdir, voice=voice_name)

    progress(0.45, desc="Finding visuals...")
    backgrounds = visuals.gather_backgrounds(scene_list, size, workdir)

    progress(0.65, desc="Rendering video (this is the slow part)...")
    out_path = os.path.join(workdir, f"{slugify(topic)}.mp4")
    build_video(scene_list, voice_paths, backgrounds, size, out_path, fps=fps)

    script_text = "\n".join(f"{i + 1}. {s['text']}" for i, s in enumerate(scene_list))
    return out_path, script_text


with gr.Blocks(title="VideoCrafter - free topic to video") as app:
    gr.Markdown("# 🎬 VideoCrafter\nType a topic and get a complete video - "
                "script, voiceover, visuals, and captions. 100% free.")
    with gr.Row():
        with gr.Column():
            topic = gr.Textbox(label="Topic", placeholder='e.g. "black holes" or "ancient Egypt"')
            video_format = gr.Radio(list(FORMATS), value="shorts", label="Format")
            voice_name = gr.Dropdown(VOICE_CHOICES, value="male", label="Voice")
            scenes = gr.Slider(3, 10, value=6, step=1, label="Number of scenes")
            fast_preview = gr.Checkbox(value=True, label="Fast preview (half resolution, much quicker)")
            pexels_key = gr.Textbox(
                label="Pexels API key (optional - upgrades photos to stock video footage, "
                      "free key at pexels.com/api)", type="password")
            go = gr.Button("🎬 Create Video", variant="primary")
        with gr.Column():
            video_out = gr.Video(label="Your video")
            script_out = gr.Textbox(label="Script used", lines=8)
    go.click(create_video,
             inputs=[topic, video_format, voice_name, scenes, fast_preview, pexels_key],
             outputs=[video_out, script_out])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true",
                        help="also create a temporary public link you can open from any device")
    args = parser.parse_args()
    app.launch(server_port=args.port, share=args.share, inbrowser=True)
