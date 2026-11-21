import json
import pathlib
import subprocess
import sys

def main() -> int:
    mf_path = pathlib.Path("docs/manifest.json")
    if not mf_path.exists():
        print("Missing docs/manifest.json", file=sys.stderr)
        return 1
    data = json.loads(mf_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        print("manifest scenes must be a list", file=sys.stderr)
        return 1

    max_bytes = 100 * 1024 * 1024
    for scene in scenes:
        vid_rel = scene.get("video", "")
        vid_path = pathlib.Path("docs") / vid_rel
        if not vid_rel or not vid_path.is_file():
            print(f"Missing video file: {vid_path}", file=sys.stderr)
            return 1
        size = vid_path.stat().st_size
        if size >= max_bytes:
            print(f"Asset exceeds 100MB ({size} bytes): {vid_path}", file=sys.stderr)
            return 1
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
                str(vid_path),
            ],
            text=True,
        ).strip()
        w_str, h_str = out.split("x")
        w, h = int(w_str), int(h_str)
        if w != 2 * h:
            print(f"Not 2:1 equirectangular ({w}x{h}): {vid_path}", file=sys.stderr)
            return 1

    print(f"Validated {len(scenes)} scene(s) successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
