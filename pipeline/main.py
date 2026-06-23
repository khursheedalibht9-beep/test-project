"""Run the full pipeline end to end: voiceover -> images -> animation -> subtitles -> export."""
import generate_voiceover
import generate_images
import animate_images
import generate_subtitles
import build_video


def main():
    print("== 1/5 voiceover ==")
    generate_voiceover.main()
    print("== 2/5 images ==")
    generate_images.main()
    print("== 3/5 animation ==")
    animate_images.main()
    print("== 4/5 subtitles ==")
    generate_subtitles.main()
    print("== 5/5 export ==")
    build_video.main()


if __name__ == "__main__":
    main()
