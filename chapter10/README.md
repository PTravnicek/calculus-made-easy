# Chapter X: Geometrical Meaning of Differentiation

An interactive, narrated video of Chapter X of *Calculus Made Easy* (Silvanus P. Thompson, 1914, public domain;
original text at <https://calculusmadeeasy.org/10.html>). The animations are made with
[Manim Community](https://www.manim.community/), the maintained fork of 3Blue1Brown's manim.

## Watch it

From the project folder:

```bash
python3 lessonkit/serve.py
```

Then open <http://localhost:8710> and choose this lesson. Building, voices and the shared player are described
in the [project README](../README.md).

The player has:

- nine parts (about 12 minutes) on one timeline, with captions and a clickable transcript;
- seven "pause and ponder" stops where the video waits for an answer: multiple choice, a number,
  dragging a point to where the tangent is level, and swinging a line until it touches a parabola;
- Thompson's Exercises VIII, with answer checking (numbers, fractions, `sqrt(2)`, angles like `26°34'`),
  hints and worked answers;
- a slope lab where you drag Q, shrink dx, and watch the chord QT turn into the tangent.

Answers and progress are kept in the browser's local storage. "Start over" under the parts list clears them.

## Parts

| Part | Scene | Covers |
|---|---|---|
| 1 | `Ch01Tangent` | dy/dx as the slope of the tangent (Fig. 7) |
| 2 | `Ch02ReadingSlopes` | 45°, steeper, gentler, level, downward; lines vs. curves (Figs. 8–14) |
| 3 | `Ch03MaxMin` | maxima and minima, dy/dx = 0 (Figs. 15, 16, 28) |
| 4 | `Ch04Oddities` | least-steep point, vertical "nose", cusp (Figs. 17, 18, 25) |
| 5 | `Ch05Lines` | y = x + b and y = ax + b (Examples 1–2) |
| 6 | `Ch06Parabola` | y = ¼x² + 3, the table, and the slope graph (Example 3) |
| 7 | `Ch07TangentAngle` | tangent to y = 1/(2x) + 3 and its angles with y = 2x² + 2 (Example 4) |
| 8 | `Ch08TangentFromPoint` | tangents from (2, −1) to y = x² − 5x + 6 (Example 5) |
| 9 | `Ch09Recap` | summary |

## Rebuild the video

```bash
.venv/bin/python lessonkit/build.py chapter10
```

Narration lines and question stops are written in `manim/scenes.py` (`with self.voice("…"):` and
`self.checkpoint("id")`); the questions themselves are defined in `QUESTIONS` in `web/index.html`.
