#!/usr/bin/env python3
"""Render a lesson's scenes and package its web player.

    .venv/bin/python lessonkit/build.py chapter10                 # 1080p30, 4 scenes at a time
    .venv/bin/python lessonkit/build.py linear-motion -q m -j 2   # 720p30, two at a time
    .venv/bin/python lessonkit/build.py chapter10 --only Ch03MaxMin Ch07TangentAngle

A lesson is a folder with lesson.json (its scene list), manim/scenes.py and web/index.html.
The build writes web/media/<nn>-<slug>.mp4 (+ .jpg poster), web/data.js (each part's
duration, caption cues and checkpoint times, as logged by the scenes) and copies the shared
player (lessonkit/player) into web/.

With Gemini narration (see tts.py) every line is synthesized first, one scene at a time,
so the free-tier rate limit is respected and a used-up daily quota stops the build before
any rendering starts.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import tts  # noqa: E402

QUALITY = {"l": ("854,480", 15), "m": ("1280,720", 30), "h": ("1920,1080", 30)}


class Lesson:
    def __init__(self, folder: str):
        self.root = (Path.cwd() / folder).resolve()
        if not (self.root / "lesson.json").exists():
            self.root = (KIT.parent / folder).resolve()
        meta = json.loads((self.root / "lesson.json").read_text())
        self.scenes = [(s["scene"], s["slug"]) for s in meta["scenes"]]
        self.manim = self.root / "manim"
        self.build = self.manim / "build"
        self.web = self.root / "web"


def run_manim(lesson: Lesson, scene: str, args: list[str], log: Path) -> int:
    cmd = [sys.executable, "-m", "manim", "render", *args, "--disable_caching", "scenes.py", scene]
    with open(log, "w") as fh:
        return subprocess.run(cmd, cwd=lesson.manim, stdout=fh, stderr=subprocess.STDOUT).returncode


def prefetch_narration(lesson: Lesson, scenes: list[str]) -> None:
    """Run each scene without rendering frames, which synthesizes and caches all of its narration."""
    for scene in scenes:
        print(f"narration for {scene} …", flush=True)
        log = lesson.build / f"{scene}.narration.log"
        if run_manim(lesson, scene, ["-ql", "--dry_run", "--media_dir", str(lesson.build / "media" / "dry")], log):
            if "QuotaExhausted" in log.read_text():
                sys.exit("Gemini's free daily quota is used up. Clips made so far are cached; run the build "
                         "again tomorrow to continue.")
            sys.exit(f"narration for {scene} failed; see {log}")


def render(lesson: Lesson, scene: str, quality: str) -> Path:
    res, fps = QUALITY[quality]
    media = lesson.build / "media" / quality / scene
    log = lesson.build / f"{scene}.log"
    if run_manim(lesson, scene, ["-r", res, "--fps", str(fps), "--media_dir", str(media)], log):
        raise RuntimeError(f"{scene} failed; see {log}")
    out = max(media.glob(f"videos/scenes/*/{scene}.mp4"), key=lambda p: p.stat().st_mtime)
    for partial in media.glob("videos/scenes/*/partial_movie_files"):
        shutil.rmtree(partial, ignore_errors=True)
    return out


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return round(float(out), 3)


def package(lesson: Lesson, index: int, scene: str, slug: str, src: Path) -> dict:
    media = lesson.web / "media"
    media.mkdir(parents=True, exist_ok=True)
    name = f"{index:02d}-{slug}"
    mp4, jpg = media / f"{name}.mp4", media / f"{name}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-c:v", "libx264", "-preset", "slow", "-crf", "25",
                    "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "128k",
                    "-ar", "48000", "-ac", "1", "-movflags", "+faststart", str(mp4)], check=True)
    log = json.loads((lesson.build / "logs" / f"{scene}.json").read_text())
    duration = probe_duration(mp4)
    cues = log["cues"]
    poster_t = cues[min(2, len(cues) - 1)]["end"] - 0.5 if cues else duration / 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{poster_t:.2f}", "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=480:-1", "-q:v", "4", str(jpg)], check=True)
    return {
        "id": f"part{index}", "scene": scene, "title": log["title"],
        "video": f"media/{mp4.name}", "poster": f"media/{jpg.name}",
        "duration": duration, "cues": cues, "checkpoints": log["checkpoints"],
    }


def read_data(lesson: Lesson) -> dict:
    f = lesson.web / "data.js"
    if not f.exists():
        return {}
    text = f.read_text()
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def copy_player(lesson: Lesson) -> None:
    for f in (KIT / "player").iterdir():
        if f.is_file():
            shutil.copy2(f, lesson.web / f.name)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lesson", help="lesson folder, e.g. chapter10 or linear-motion")
    ap.add_argument("-q", "--quality", choices=QUALITY, default="h")
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--only", nargs="*", help="re-render just these scenes; the rest are reused")
    ap.add_argument("--player-only", action="store_true", help="just copy the shared player into web/")
    args = ap.parse_args()

    lesson = Lesson(args.lesson)
    lesson.web.mkdir(parents=True, exist_ok=True)
    copy_player(lesson)
    if args.player_only:
        print(f"copied the player into {lesson.web}")
        return

    lesson.build.mkdir(parents=True, exist_ok=True)
    todo = [s for s, _ in lesson.scenes if not args.only or s in args.only]
    print(f"narration: {tts.describe()}")
    if tts.ENGINE == "gemini":
        prefetch_narration(lesson, todo)
    with ThreadPoolExecutor(args.jobs) as pool:
        rendered = dict(zip(todo, pool.map(lambda s: render(lesson, s, args.quality), todo)))

    previous = {p["scene"]: p for p in read_data(lesson).get("parts", [])}
    parts = []
    for i, (scene, slug) in enumerate(lesson.scenes, start=1):
        if scene in rendered:
            parts.append(package(lesson, i, scene, slug, rendered[scene]))
        elif scene in previous:
            parts.append(previous[scene])
        else:
            sys.exit(f"{scene} has never been rendered; run without --only first")
    payload = {"voice": tts.describe(), "parts": parts}
    (lesson.web / "data.js").write_text(
        "// Generated by lessonkit/build.py. Do not edit by hand.\nwindow.LESSON_DATA = "
        + json.dumps(payload, indent=1) + ";\n")
    total = sum(p["duration"] for p in parts)
    print(f"wrote {lesson.web / 'data.js'}: {len(parts)} parts, {total / 60:.1f} min")


if __name__ == "__main__":
    main()
