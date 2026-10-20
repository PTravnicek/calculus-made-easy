# Interactive video lessons

Narrated, animated lessons made with [Manim Community](https://www.manim.community/) (the maintained fork of
3Blue1Brown's manim). Each one plays in a web player that stops to ask questions, with exercises and small labs
underneath.

| Lesson | Folder | Source |
|---|---|---|
| Geometrical Meaning of Differentiation | [chapter10/](chapter10/) | *Calculus Made Easy*, Chapter X (Thompson, 1914, public domain) |
| Linear Motion | [linear-motion/](linear-motion/) | topics of the linear-motion chapter in Hewitt's *Conceptual Physics*; all wording, examples and exercises are original |

## Watch

The rendered videos are included, so watching needs nothing but Python 3:

```bash
git clone https://github.com/PTravnicek/calculus-made-easy.git
cd calculus-made-easy
python3 lessonkit/serve.py
```

Then open http://localhost:8710 and pick a lesson. Use this server rather than `python -m http.server`: it answers
range requests, which the videos need in order to seek.

## Build a lesson's video

Needs Python 3.10+, ffmpeg, LaTeX with `dvisvgm`, and macOS if you narrate with the built-in voices.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python lessonkit/build.py linear-motion
```

This renders every scene at 1080p30, four at a time (about 20 minutes per lesson). It writes the videos to
`<lesson>/web/media/` and the captions and question times to `<lesson>/web/data.js`, and copies the shared player
into `<lesson>/web/`.

- Re-render some parts only: `lessonkit/build.py chapter10 --only Ch03MaxMin`
- Preview one scene quickly: `cd linear-motion/manim && ../../.venv/bin/manim -ql scenes.py LM06HowFast`
- After editing `lessonkit/player/*`: `lessonkit/build.py <lesson> --player-only`

## Narration voice

`lessonkit/tts.py` picks the voice:

- **Gemini TTS** (Google's `gemini-3.8-flash-tts`, free tier). It's used automatically when a key is available.
  Create one at https://aistudio.google.com/apikey and save it in a file called `.env` at the top of this
  project, with this one line:

  ```
  GEMINI_API_KEY=your-key
  ```

  Then rebuild each lesson. Requests are spaced about 8 seconds apart, and every clip is cached in
  `lessonkit/cache/audio`. If the free daily quota runs out, the build stops and keeps what it has made;
  run it again the next day to finish. `python lessonkit/tts.py --samples` writes a few voices to
  `voice-samples/` so you can compare them; choose one with `LESSON_VOICE=Sadaltager`.
- **macOS voices**, used when there is no key. Choose one with `LESSON_VOICE=Daniel` (and `LESSON_RATE=165`).

## How a lesson is put together

```
lessonkit/            shared by every lesson
  narration.py        Narrated mixin: speaks each line, keeps animations in step, logs captions and question times
  tts.py              Gemini or macOS voices, cached
  build.py            renders scenes, encodes video, writes data.js, copies the player
  serve.py            local server with range requests and a lesson index
  player/             player.js + player.css: video, timeline, captions, questions, exercises, plotting kit
<lesson>/
  lesson.json         title and scene list
  manim/scenes.py     one Scene per part; `with self.voice("…"):` narrates, `self.checkpoint("id")` asks a question
  web/index.html      the lesson's text, question definitions, exercises and labs; calls Lesson.start({...})
```

A new lesson needs a `lesson.json`, a `manim/scenes.py` starting with the two lessonkit import lines, and a
`web/index.html` modelled on an existing one.
