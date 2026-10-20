"""Shared style and narration machinery for every lesson's Manim scenes.

A lesson's scenes.py starts with

    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lessonkit"))
    from narration import *

and each scene mixes in `Narrated`, which
  * speaks each narration line (see tts.py: Gemini TTS, or macOS `say`) and lays it on the soundtrack,
  * stretches the animations so the picture never runs ahead of the voice,
  * logs caption cues and interactive checkpoints to <lesson>/manim/build/logs/<Scene>.json,
    which build.py turns into the data file the web player reads.
"""
from __future__ import annotations

import inspect
import json
import re
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from manim import *

from tts import synthesize

# ── palette (3b1b-style) ────────────────────────────────────────────────
BG = "#0E1014"
CURVE = BLUE_C
CURVE_2 = TEAL_C
POINT = YELLOW
TANGENT = YELLOW
DX_C = GREEN_C
DY_C = RED_C
NOTE = GOLD_C
MUTED = GREY_B
AXIS = GREY_B

config.background_color = BG


# ── speech ──────────────────────────────────────────────────────────────
_SPEECH = [
    (r"\\frac\{dy\}\{dx\}|dy/dx", " d y by d x "),
    (r"\bdx\b", " d x "),
    (r"\bdy\b", " d y "),
    (r"\\tfrac12|\\tfrac\{1\}\{2\}|½", " one half "),
    (r"\\tfrac13|\\tfrac\{1\}\{3\}", " one third "),
    (r"\\tfrac14|\\tfrac\{1\}\{4\}", " one quarter "),
    (r"°", " degrees "),
    (r"−|(?<=\$)-|(?<= )-(?=\d)", " minus "),
    (r"\\,|\\;|\\ ", " "),
    (r"\$", ""),
]


def to_speech(text: str) -> str:
    s = text
    for pat, rep in _SPEECH:
        s = re.sub(pat, rep, s)
    if re.search(r"[\\{}^_]", s):
        raise ValueError(f"needs an explicit say= text: {text!r}")
    return re.sub(r"\s+", " ", s).strip()


class _Voice:
    def __init__(self, scene, start, duration):
        self.scene, self.start, self.duration = scene, start, duration

    def left(self, minimum=0.4, frac=1.0):
        """Seconds of narration still to come (for sizing the next animation)."""
        rest = self.start + self.duration - self.scene.renderer.time
        return max(minimum, rest * frac)


class Narrated:
    chapter_title = ""

    def setup(self):
        super().setup()
        self._cues: list[dict] = []
        self._checkpoints: list[dict] = []

    @contextmanager
    def voice(self, text: str, say: str | None = None, tail: float = 0.35):
        path, dur = synthesize(say or to_speech(text))
        start = self.renderer.time
        self.add_sound(str(path))
        self._cues.append({"start": round(start, 3), "end": round(start + dur, 3), "text": text})
        yield _Voice(self, start, dur)
        rest = start + dur - self.renderer.time
        if rest > 1 / 30:
            self.wait(rest)
        if tail:
            self.wait(tail)

    def narrate(self, text: str, say: str | None = None, tail: float = 0.35):
        with self.voice(text, say, tail):
            pass

    def checkpoint(self, cid: str, hold: float = 1.2):
        """The web player pauses here and opens the interactive question `cid`."""
        self._checkpoints.append({"id": cid, "t": round(self.renderer.time + 0.15, 3)})
        self.wait(hold)

    def tear_down(self):
        super().tear_down()
        log_dir = Path(inspect.getfile(type(self))).resolve().parent / "build" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{type(self).__name__}.json").write_text(json.dumps({
            "title": self.chapter_title,
            "duration": round(self.renderer.time, 3),
            "cues": self._cues,
            "checkpoints": self._checkpoints,
        }, indent=1))

    # ── recurring visual pieces ─────────────────────────────────────────
    def section_card(self, number: int, title: str):
        num = Tex(f"Part {number}", color=MUTED).scale(0.75)
        head = Tex(title).scale(1.25)
        rule = Line(LEFT * 3, RIGHT * 3, stroke_width=2, color=CURVE)
        card = VGroup(num, head, rule).arrange(DOWN, buff=0.35)
        self.play(FadeIn(num, shift=0.2 * UP), Write(head), GrowFromCenter(rule), run_time=1.6)
        self.wait(1.0)
        self.play(FadeOut(card, shift=0.3 * UP), run_time=0.6)

    def ponder_card(self, *lines: str, width: float = 0.0) -> VGroup:
        head = Tex(r"Pause and ponder", color=POINT).scale(0.8)
        body = VGroup(*[Tex(l).scale(0.72) for l in lines]).arrange(DOWN, buff=0.18)
        content = VGroup(head, body).arrange(DOWN, buff=0.3)
        box = RoundedRectangle(
            corner_radius=0.2, width=max(width, content.width + 0.7), height=content.height + 0.6,
            stroke_color=POINT, stroke_width=2, fill_color=BG, fill_opacity=0.92,
        )
        content.move_to(box)
        return VGroup(box, content)


def keep_in_frame(mob, margin=0.25):
    """Shift `mob` so it sits fully inside the visible frame."""
    w, h = config.frame_width / 2 - margin, config.frame_height / 2 - margin
    dx = min(0, w - mob.get_right()[0]) + max(0, -w - mob.get_left()[0])
    dy = min(0, h - mob.get_top()[1]) + max(0, -h - mob.get_bottom()[1])
    return mob.shift(dx * RIGHT + dy * UP)


# ── geometry helpers ────────────────────────────────────────────────────
def tangent_line(ax, f, df, x, length=4.0, color=TANGENT, stroke_width=3):
    p = ax.c2p(x, f(x))
    d = ax.c2p(x + 1, f(x) + df(x)) - ax.c2p(x, f(x))
    d = d / np.linalg.norm(d)
    return Line(p - d * length / 2, p + d * length / 2, color=color, stroke_width=stroke_width)


def direction_line(point, direction, length, color=TANGENT, stroke_width=3):
    d = np.array(direction, dtype=float)
    d = d / np.linalg.norm(d)
    return Line(point - d * length / 2, point + d * length / 2, color=color, stroke_width=stroke_width)


def slope_readout(value_fn, label=r"\frac{dy}{dx}", decimals=2, color=WHITE, scale=1.0):
    """`dy/dx = 0.52`, kept up to date every frame."""
    lhs = MathTex(label, "=").scale(scale)
    num = DecimalNumber(value_fn(), num_decimal_places=decimals, include_sign=True, color=color).scale(scale)
    num.add_updater(lambda m: m.set_value(value_fn()))
    num.add_updater(lambda m: m.next_to(lhs, RIGHT, buff=0.2))
    return VGroup(lhs, num)


def axes_letters(ax, o=True, x="X", y="Y"):
    g = VGroup()
    if o:
        g.add(MathTex("O").scale(0.8).next_to(ax.c2p(0, 0), DL, buff=0.12))
    if x:
        g.add(MathTex(x).scale(0.8).next_to(ax.x_axis.get_end(), DOWN, buff=0.18))
    if y:
        g.add(MathTex(y).scale(0.8).next_to(ax.y_axis.get_end(), LEFT, buff=0.18))
    return g


def plain_axes(x_range, y_range, x_length, y_length, **kw):
    return Axes(
        x_range=x_range, y_range=y_range, x_length=x_length, y_length=y_length,
        tips=True,
        axis_config={"include_ticks": kw.pop("ticks", False), "stroke_color": AXIS,
                     "stroke_width": 2, "tip_width": 0.18, "tip_height": 0.18},
        **kw,
    )
