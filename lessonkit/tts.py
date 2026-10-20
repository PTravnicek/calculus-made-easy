"""Text-to-speech for the narration.

Engines (pick with LESSON_TTS):
  gemini  Google Gemini TTS on the free tier. Needs GEMINI_API_KEY, either in the
          environment or in a .env file at the project root. The default whenever a key is available.
  say     macOS built-in voices. Offline fallback.

Settings (environment variables): LESSON_TTS, LESSON_VOICE, LESSON_STYLE, LESSON_RATE (say only),
LESSON_TTS_RPM (Gemini requests per minute), LESSON_GEMINI_MODEL.

Every clip is cached in lessonkit/cache/audio under a hash of engine, voice, style and text,
so a line is only ever synthesized once. Gemini requests are serialized across
processes and spaced out to stay inside the free-tier rate limit.

    python tts.py "Some line to try"        # synthesize one line and print the file
    python tts.py --samples                 # one line in several Gemini voices -> ../voice-samples
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
AUDIO_DIR = ROOT / "cache" / "audio"


def _load_env() -> None:
    for env in (PROJECT / ".env", Path.cwd() / ".env"):
        if not env.exists():
            continue
        for line in env.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip("'\"")


_load_env()
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
ENGINE = os.environ.get("LESSON_TTS") or ("gemini" if API_KEY else "say")

GEMINI_MODEL = os.environ.get("LESSON_GEMINI_MODEL", "gemini-3.8-flash-tts")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
STYLE = os.environ.get("LESSON_STYLE", "calm, clear and warm, like a teacher explaining a diagram; unhurried")
MIN_INTERVAL = 60 / float(os.environ.get("LESSON_TTS_RPM", "8"))

VOICE = os.environ.get("LESSON_VOICE", "Charon" if ENGINE == "gemini" else "Samantha")
SAY_RATE = int(os.environ.get("LESSON_RATE", "175"))


def describe() -> str:
    """Human-readable credit for the player's footer."""
    if ENGINE == "gemini":
        return f"Google Gemini text-to-speech ({GEMINI_MODEL}, voice {VOICE})"
    return f"macOS text-to-speech (voice {VOICE})"


class QuotaExhausted(RuntimeError):
    pass


# ── public entry point ──────────────────────────────────────────────────
def synthesize(spoken: str) -> tuple[Path, float]:
    """Return (wav path, duration in seconds) for one narration line."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    if ENGINE == "gemini":
        key = hashlib.sha1(f"gemini|{GEMINI_MODEL}|{VOICE}|{STYLE}|{spoken}".encode()).hexdigest()[:16]
    else:
        key = hashlib.sha1(f"{VOICE}|{SAY_RATE}|{spoken}".encode()).hexdigest()[:16]  # matches the old cache
    path = AUDIO_DIR / f"{key}.wav"
    if not path.exists():
        if ENGINE == "gemini":
            _gemini_to(path, spoken)
        elif ENGINE == "say":
            subprocess.run(["say", "-v", VOICE, "-r", str(SAY_RATE), "--file-format=WAVE",
                            "--data-format=LEI16@44100", "-o", str(path), spoken], check=True)
        else:
            raise ValueError(f"unknown LESSON_TTS engine {ENGINE!r}")
    return path, wav_duration(path)


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


# ── Gemini ──────────────────────────────────────────────────────────────
def _gemini_to(path: Path, text: str) -> None:
    if not API_KEY:
        raise RuntimeError("LESSON_TTS=gemini needs GEMINI_API_KEY (in the environment or in the project's .env)")
    words = len(text.split())
    tmp = path.with_suffix(".raw.wav")
    for take in range(2):
        tmp.write_bytes(_gemini_request(text))
        _tidy(tmp, path)
        tmp.unlink(missing_ok=True)
        rate = words / max(wav_duration(path), 0.01)
        # Far outside normal speaking speed usually means a truncated or rambling take: try once more,
        # and keep the second take whatever it sounds like.
        if 1.3 <= rate <= 4.2 or words < 4 or take == 1:
            return
        print(f"[tts] odd pacing ({rate:.1f} words/s) for: {text[:60]!r}; retrying", file=sys.stderr)


def _gemini_request(text: str) -> bytes:
    body = {
        "model": GEMINI_MODEL,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{"type": "speech_metadata", "style": STYLE}] if STYLE else [],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": VOICE}]},
    }
    lock_path = AUDIO_DIR / ".gemini.lock"
    stamp_path = AUDIO_DIR / ".gemini.last"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # one request at a time, even across parallel renders
        for attempt in range(8):
            last = float(stamp_path.read_text()) if stamp_path.exists() else 0.0
            wait = last + MIN_INTERVAL - time.time()
            if wait > 0:
                time.sleep(wait)
            stamp_path.write_text(str(time.time()))
            req = urllib.request.Request(
                GEMINI_URL, data=json.dumps(body).encode(), method="POST",
                headers={"x-goog-api-key": API_KEY, "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=240) as r:
                    return _audio_from(json.load(r))
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")
                if e.code == 429:
                    if re.search(r"per.?day|PerDay|daily", detail, re.I):
                        raise QuotaExhausted(
                            "Gemini's free daily quota is used up. Clips made so far are cached in lessonkit/cache/audio; "
                            "run build.py again tomorrow to continue.") from None
                    delay = _retry_delay(detail) or 30.0
                    print(f"[tts] rate limited; waiting {delay:.0f}s", file=sys.stderr)
                    time.sleep(delay)
                    continue
                if e.code >= 500:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"Gemini TTS error {e.code}: {_short(detail)}") from None
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"[tts] network problem ({e}); retrying", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        raise RuntimeError("Gemini TTS kept failing; giving up on this line")


def _audio_from(resp: dict) -> bytes:
    """Find the base64 audio in an Interactions API response, return WAV bytes."""
    found: list[tuple[str, str]] = []

    def walk(o):
        if isinstance(o, dict):
            d = o.get("data")
            if isinstance(d, str) and len(d) > 256:
                found.append((o.get("mime_type") or o.get("mimeType") or "", d))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(resp)
    if not found:
        raise RuntimeError(f"no audio in Gemini response: {_short(json.dumps(resp))}")
    mime, data = found[-1]
    audio = base64.b64decode(data)
    if audio[:4] == b"RIFF":
        return audio
    rate = int(m.group(1)) if (m := re.search(r"rate=(\d+)", mime)) else 24000
    return _pcm_to_wav(audio, rate)


def _pcm_to_wav(pcm: bytes, rate: int) -> bytes:
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _tidy(src: Path, dst: Path) -> None:
    """Trim leading/trailing silence and convert to 44.1 kHz mono 16-bit WAV."""
    trim = "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-48dB"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-af", f"{trim},areverse,{trim},areverse,apad=pad_dur=0.05",
         "-ar", "44100", "-ac", "1", "-sample_fmt", "s16", str(dst)],
        check=True,
    )


def _retry_delay(detail: str) -> float | None:
    m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', detail)
    return float(m.group(1)) + 1 if m else None


def _short(s: str, n: int = 400) -> str:
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= n else s[:n] + "…"


# ── command line ────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--samples"]:
        line = ("Zoom in on Q and you see it plainly: magnified enough, a smooth curve looks like a straight line. "
                "And that is the geometrical meaning of d y by d x: it is the slope of the tangent at Q.")
        out = PROJECT / "voice-samples"
        out.mkdir(exist_ok=True)
        for v in (args[1:] or ["Charon", "Sadaltager", "Iapetus", "Erinome", "Sulafat"]):
            VOICE = v
            p, d = synthesize(line)
            target = out / f"{v}.wav"
            target.write_bytes(p.read_bytes())
            print(f"{target}  {d:.1f}s")
    elif args:
        p, d = synthesize(" ".join(args))
        print(f"{p}  {d:.2f}s  [{describe()}]")
    else:
        print(__doc__)
