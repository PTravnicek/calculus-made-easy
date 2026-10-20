/* lessonkit player: interactive video, pause-and-ponder questions, exercise sheet and a small plotting kit.
   Copied into each lesson's web/ folder by lessonkit/build.py; edit the original in lessonkit/player/.

   A lesson page loads data.js (generated) and this file, then calls

     Lesson.start({
       id: "ch10",                       // prefix for what the browser remembers
       questions: { "<checkpoint id>": { kind: "choice" | "number" | <custom>, prompt, ... } },
       widgets: { custom(q, body, api) { ... return { check, reveal, redraw, dispose } } },
       partMeta: { SceneName: "Fig. 7" },  // small label under each part
       exercises: [ { n, text, fields: [{ label, answer, angle?, alt?, group?, ph? }], widget?, proof?, hint, solution } ],
       exWidgets: { name(box, exercise) { ... } },
       endCard: { title, text, button, target },
     });

   Lesson.util holds the helpers (el, Plot, dragX, parseNumber, typeset …) for the page's own labs. */
(function () {
"use strict";
if (!window.MathJax) {
  window.MathJax = {
    tex: { inlineMath: [["$", "$"]], displayMath: [] },
    svg: { fontCache: "global" },
    options: { enableMenu: false },
    startup: { typeset: false },
  };
  const s = document.createElement("script");
  s.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js";
  s.defer = true;
  document.head.append(s);
}

/* ═════════════ small helpers ═════════════ */
const $ = (s, el = document) => el.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "html") n.innerHTML = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids) if (k != null) n.append(k);
  return n;
};
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const fmtTime = (s) => { s = Math.max(0, s || 0); return Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0"); };
let STORE_PREFIX = "lesson";
const store = {
  get(k, d) { try { const v = localStorage.getItem(STORE_PREFIX + "." + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(STORE_PREFIX + "." + k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
};
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

let mjChain = Promise.resolve();
function typeset(...nodes) {
  if (!window.MathJax || !MathJax.typesetPromise || !MathJax.startup || !MathJax.startup.promise) {
    // MathJax may still be loading (it is deferred); try again shortly.
    return new Promise((r) => setTimeout(() => typeset(...nodes).then(r), 150));
  }
  mjChain = mjChain.then(() => MathJax.startup.promise).then(() => MathJax.typesetPromise(nodes)).catch((e) => console.warn(e));
  return mjChain;
}

/* ═════════════ reading answers safely ═════════════ */
const FUNCS = { sqrt: Math.sqrt, sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, ln: Math.log, log: Math.log, abs: Math.abs, atan: Math.atan, asin: Math.asin, acos: Math.acos };
const CONSTS = { pi: Math.PI, e: Math.E };
function compile(src) {
  const s = String(src).toLowerCase()
    .replace(/[−–]/g, "-").replace(/[×·]/g, "*").replace(/÷/g, "/")
    .replace(/²/g, "^2").replace(/³/g, "^3").replace(/π/g, "pi").replace(/√/g, "sqrt")
    .replace(/½/g, "(1/2)").replace(/⅓/g, "(1/3)").replace(/¼/g, "(1/4)").replace(/¾/g, "(3/4)").replace(/⅔/g, "(2/3)");
  const raw = [];
  let i = 0, m;
  while (i < s.length) {
    const rest = s.slice(i);
    if (/^\s/.test(rest)) { i++; continue; }
    if ((m = /^(\d+\.?\d*|\.\d+)/.exec(rest))) { raw.push({ t: "num", v: parseFloat(m[0]) }); i += m[0].length; continue; }
    if ((m = /^[a-z]+/.exec(rest))) {
      let w = m[0];
      // split runs like "xsqrt" or "pix" into known names
      while (w) {
        const name = ["sqrt", "atan", "asin", "acos", "sin", "cos", "tan", "exp", "abs", "log", "ln", "pi", "x", "e"].find((n) => w.startsWith(n));
        if (!name) throw new Error(`I don't know “${m[0]}”`);
        raw.push({ t: "id", v: name }); w = w.slice(name.length);
      }
      i += m[0].length; continue;
    }
    if ("+-*/^()".includes(rest[0])) { raw.push({ t: rest[0] }); i++; continue; }
    throw new Error(`Unexpected “${rest[0]}”`);
  }
  const toks = [];
  for (const tk of raw) {
    const p = toks[toks.length - 1];
    const pEnds = p && (p.t === "num" || p.t === ")" || (p.t === "id" && !FUNCS[p.v]));
    const tStarts = tk.t === "num" || tk.t === "id" || tk.t === "(";
    if (pEnds && tStarts) toks.push({ t: "*" });
    toks.push(tk);
  }
  let k = 0;
  const peek = () => toks[k], eat = (t) => { if (toks[k] && toks[k].t === t) return toks[k++]; return null; };
  const need = (t) => { if (!eat(t)) throw new Error(`Expected “${t}”`); };
  function expr() {
    let a = term();
    for (;;) {
      if (eat("+")) { const l = a, r = term(); a = (x) => l(x) + r(x); }
      else if (eat("-")) { const l = a, r = term(); a = (x) => l(x) - r(x); }
      else return a;
    }
  }
  function term() {
    let a = unary();
    for (;;) {
      if (eat("*")) { const l = a, r = unary(); a = (x) => l(x) * r(x); }
      else if (eat("/")) { const l = a, r = unary(); a = (x) => l(x) / r(x); }
      else return a;
    }
  }
  function unary() {
    if (eat("-")) { const u = unary(); return (x) => -u(x); }
    if (eat("+")) return unary();
    return power();
  }
  function power() {
    const b = atom();
    if (eat("^")) { const e = unary(); return (x) => Math.pow(b(x), e(x)); }
    return b;
  }
  function atom() {
    const tk = peek();
    if (!tk) throw new Error("Something is missing at the end");
    if (eat("num")) return () => tk.v;
    if (eat("(")) { const e = expr(); need(")"); return e; }
    if (eat("id")) {
      if (FUNCS[tk.v]) {
        const f = FUNCS[tk.v];
        if (peek() && peek().t === "(") { need("("); const e = expr(); need(")"); return (x) => f(e(x)); }
        const e = power(); return (x) => f(e(x));
      }
      if (tk.v === "x") return (x) => { if (x === undefined) throw new Error("Give a number, not an expression in x"); return x; };
      return () => CONSTS[tk.v];
    }
    throw new Error(`Unexpected “${tk.t}”`);
  }
  if (!toks.length) throw new Error("Empty");
  const f = expr();
  if (k < toks.length) throw new Error(`Unexpected “${toks[k].t === "num" ? toks[k].v : toks[k].t}”`);
  return f;
}
function parseNumber(s) {
  const v = compile(s)();
  if (!Number.isFinite(v)) throw new Error("That doesn't come out to a number");
  return v;
}
function parseAngle(s) {
  const m = /^\s*([+-−]?\d+(?:\.\d+)?)\s*(?:°|deg|d)\s*(?:(\d+(?:\.\d+)?)\s*(?:'|′|min|m)?)?\s*$/i.exec(s);
  if (m) {
    const d = parseFloat(m[1].replace("−", "-")), mins = m[2] ? parseFloat(m[2]) : 0;
    return d < 0 ? d - mins / 60 : d + mins / 60;
  }
  return parseNumber(s);
}
const near = (v, a) => Math.abs(v - a) <= Math.max(0.011, Math.abs(a) * 0.01);
const nearAngle = (v, a) => Math.abs(v - a) <= 0.12;
const dms = (deg) => { const s = deg < 0 ? "−" : ""; deg = Math.abs(deg); let d = Math.floor(deg), m = Math.round((deg - d) * 60); if (m === 60) { d++; m = 0; } return `${s}${d}°${String(m).padStart(2, "0")}′`; };
const fmtNum = (v, n = 2) => (v < 0 ? "−" : "+") + Math.abs(v).toFixed(n);

/* ═════════════ a little plotting kit ═════════════ */
class Plot {
  constructor(canvas, opts) {
    this.c = canvas; this.ctx = canvas.getContext("2d");
    this.o = Object.assign({ x: [-1, 5], y: [-2, 5], aspect: 0.6, inset: { l: 30, r: 16, t: 14, b: 26 }, screen: false }, opts);
    this.resize();
  }
  setRange(x, y) { this.o.x = x; this.o.y = y; this.layout(); }
  resize() {
    const w = Math.max(240, this.c.clientWidth || this.c.parentElement.clientWidth || 400);
    const h = Math.round(w * this.o.aspect);
    const dpr = window.devicePixelRatio || 1;
    this.c.width = Math.round(w * dpr); this.c.height = Math.round(h * dpr); this.c.style.height = h + "px";
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = w; this.h = h; this.layout();
  }
  layout() {
    const { l, r, t, b } = typeof this.o.inset === "function" ? this.o.inset(this.w) : this.o.inset;
    const [x0, x1] = this.o.x, [y0, y1] = this.o.y;
    this.box = { l, r: this.w - r, t, b: this.h - b };
    this.sx = (this.box.r - this.box.l) / (x1 - x0);
    this.sy = (this.box.b - this.box.t) / (y1 - y0);
  }
  X(x) { return this.box.l + (x - this.o.x[0]) * this.sx; }
  Y(y) { return this.box.b - (y - this.o.y[0]) * this.sy; }
  ix(px) { return this.o.x[0] + (px - this.box.l) / this.sx; }
  col(name) { return css(this.o.screen ? { ink: "--screen-ink", muted: "--screen-muted", rule: "--screen-rule", curve: "--s-curve", mark: "--s-gold", dx: "--s-dx", dy: "--s-dy", teal: "--s-teal", bg: "--screen" }[name] : { ink: "--ink", muted: "--muted", rule: "--rule", curve: "--accent", mark: "--mark", dx: "--dx", dy: "--dy", teal: "--good", bg: "--bg" }[name]); }
  clear() { const g = this.ctx; g.clearRect(0, 0, this.w, this.h); g.fillStyle = this.col("bg"); g.fillRect(0, 0, this.w, this.h); }
  clip(fn) { const g = this.ctx; g.save(); g.beginPath(); g.rect(this.box.l - 1, this.box.t - 1, this.box.r - this.box.l + 2, this.box.b - this.box.t + 2); g.clip(); fn(g); g.restore(); }
  axes({ ticks = 1, xl = "x", yl = "y", numbers = true } = {}) {
    const g = this.ctx, [x0, x1] = this.o.x, [y0, y1] = this.o.y;
    // grid and number spacing: a "nice" step (1, 2, 5 × 10ⁿ) that leaves room between labels
    const nice = (span, px, minPx) => {
      const raw = span * minPx / Math.max(px, 1), p = Math.pow(10, Math.floor(Math.log10(raw)));
      return [1, 2, 5, 10].map((m) => m * p).find((v) => v >= raw);
    };
    const gx = Math.max(ticks, nice(x1 - x0, this.box.r - this.box.l, 30));
    const gy = Math.max(ticks, nice(y1 - y0, this.box.b - this.box.t, 20));
    const fmt = (v, step) => (step < 1 ? v.toFixed(Math.ceil(-Math.log10(step))) : String(Math.round(v))).replace("-", "−");
    g.lineWidth = 1; g.strokeStyle = this.col("rule"); g.fillStyle = this.col("muted");
    g.font = `11px ${css("--mono") || "monospace"}`;
    // faint grid
    g.globalAlpha = 0.45; g.beginPath();
    for (let x = Math.ceil(x0 / gx) * gx; x <= x1 + 1e-9; x += gx) { g.moveTo(this.X(x), this.box.t); g.lineTo(this.X(x), this.box.b); }
    for (let y = Math.ceil(y0 / gy) * gy; y <= y1 + 1e-9; y += gy) { g.moveTo(this.box.l, this.Y(y)); g.lineTo(this.box.r, this.Y(y)); }
    g.stroke(); g.globalAlpha = 1;
    // axes through the origin when visible, else along the edges
    const ax = clamp(0, y0, y1), ay = clamp(0, x0, x1);
    g.strokeStyle = this.col("muted"); g.lineWidth = 1.2; g.beginPath();
    g.moveTo(this.box.l, this.Y(ax)); g.lineTo(this.box.r, this.Y(ax));
    g.moveTo(this.X(ay), this.box.t); g.lineTo(this.X(ay), this.box.b); g.stroke();
    if (numbers) {
      g.textAlign = "center"; g.textBaseline = "top";
      for (let x = Math.ceil(x0 / gx) * gx; x <= x1 + 1e-9; x += gx) if (Math.abs(x) > gx / 2) g.fillText(fmt(x, gx), this.X(x), this.Y(ax) + 4);
      g.textAlign = "right"; g.textBaseline = "middle";
      for (let y = Math.ceil(y0 / gy) * gy; y <= y1 + 1e-9; y += gy) if (Math.abs(y) > gy / 2) g.fillText(fmt(y, gy), this.X(ay) - 5, this.Y(y));
    }
    g.font = `italic 14px ${css("--display") || "serif"}`; g.fillStyle = this.col("ink");
    g.textAlign = "right"; g.textBaseline = "bottom"; g.fillText(xl, this.box.r, this.Y(ax) - 3);
    g.textAlign = "left"; g.textBaseline = "top"; g.fillText(yl, this.X(ay) + 5, this.box.t);
  }
  curve(f, color, width = 2.4, range) {
    const [a, b] = range || this.o.x;
    this.clip((g) => {
      g.strokeStyle = color; g.lineWidth = width; g.lineJoin = "round"; g.beginPath();
      const n = Math.max(200, Math.round((this.X(b) - this.X(a)) * 1.5));
      let pen = false, prev = null;
      for (let i = 0; i <= n; i++) {
        const x = a + (b - a) * i / n; let y;
        try { y = f(x); } catch { y = NaN; }
        const py = this.Y(y);
        const ok = Number.isFinite(y) && Math.abs(py) < 1e5;
        if (ok && pen && prev !== null && Math.abs(py - prev) > this.h * 1.5) pen = false;
        if (ok) { pen ? g.lineTo(this.X(x), py) : g.moveTo(this.X(x), py); pen = true; prev = py; } else { pen = false; prev = null; }
      }
      g.stroke();
    });
  }
  param(fx, fy, t0, t1, color, width = 2.4) {
    this.clip((g) => { g.strokeStyle = color; g.lineWidth = width; g.beginPath(); for (let i = 0; i <= 300; i++) { const t = t0 + (t1 - t0) * i / 300; const X = this.X(fx(t)), Y = this.Y(fy(t)); i ? g.lineTo(X, Y) : g.moveTo(X, Y); } g.stroke(); });
  }
  seg(x0, y0, x1, y1, color, width = 2, dash) {
    this.clip((g) => { g.strokeStyle = color; g.lineWidth = width; g.setLineDash(dash || []); g.beginPath(); g.moveTo(this.X(x0), this.Y(y0)); g.lineTo(this.X(x1), this.Y(y1)); g.stroke(); });
  }
  lineThrough(x, y, slope, color, width = 2, lenPx) {
    let dx = this.sx, dy = -this.sy * slope; const n = Math.hypot(dx, dy); dx /= n; dy /= n;
    const L = lenPx || 4 * Math.hypot(this.w, this.h), X = this.X(x), Y = this.Y(y);
    this.clip((g) => { g.strokeStyle = color; g.lineWidth = width; g.beginPath(); g.moveTo(X - dx * L / 2, Y - dy * L / 2); g.lineTo(X + dx * L / 2, Y + dy * L / 2); g.stroke(); });
  }
  dot(x, y, color, r = 4.5) { const g = this.ctx; g.fillStyle = color; g.beginPath(); g.arc(this.X(x), this.Y(y), r, 0, 7); g.fill(); }
  text(s, x, y, color, { align = "left", base = "bottom", dx = 0, dy = 0, font } = {}) {
    const g = this.ctx; g.fillStyle = color; g.textAlign = align; g.textBaseline = base;
    g.font = font || `500 12px ${css("--mono") || "monospace"}`; g.fillText(s, this.X(x) + dx, this.Y(y) + dy);
  }
}
/* make a canvas draggable along x; calls onX(newX) */
function dragX(canvas, plot, onX, step = 0.05, getX) {
  let down = false;
  const at = (e) => { const r = canvas.getBoundingClientRect(); onX(plot.ix(e.clientX - r.left)); };
  canvas.addEventListener("pointerdown", (e) => { down = true; canvas.setPointerCapture(e.pointerId); at(e); });
  canvas.addEventListener("pointermove", (e) => { if (down) at(e); });
  canvas.addEventListener("pointerup", () => { down = false; });
  canvas.addEventListener("pointercancel", () => { down = false; });
  canvas.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); onX(getX() + (e.key === "ArrowRight" ? step : -step) * (e.shiftKey ? 5 : 1)); }
  });
}
const redrawers = new Set();
const redrawAll = () => redrawers.forEach((f) => f());
window.addEventListener("resize", () => { clearTimeout(redrawAll.t); redrawAll.t = setTimeout(redrawAll, 120); });
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redrawAll);
new MutationObserver(redrawAll).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });


function playerMarkup(cfg) {
  const ec = cfg.endCard;
  return `
  <div class="screen" id="screen">
    <div class="stage" id="stage">
      <video id="video" playsinline preload="metadata"></video>
      <div class="caption" id="caption" hidden></div>
      <button class="bigplay" id="bigplay" aria-label="Play">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l12.5-7.5z" fill="currentColor"/></svg>
      </button>
      <div class="endcard" id="endcard" hidden>
        <div>
          <h2>${ec.title}</h2>
          <p>${ec.text}</p>
          <div class="row">
            <button class="sbtn primary" id="toExercises">${ec.button}</button>
            <button class="sbtn" id="rewatch">Watch again</button>
          </div>
        </div>
      </div>
    </div>
    <div class="overlay" id="question" hidden role="dialog" aria-modal="false" aria-labelledby="qPrompt">
      <div class="qcard">
        <div class="qhead"><span class="qkicker">Pause and ponder</span><span class="qpart" id="qPart"></span></div>
        <p class="qprompt" id="qPrompt"></p>
        <div class="qbody" id="qBody"></div>
        <p class="qfeedback" id="qFeedback" aria-live="polite"></p>
        <div class="qactions">
          <div class="left">
            <button class="sbtn" id="qCheck">Check</button>
            <button class="sbtn" id="qReveal">Show me</button>
          </div>
          <button class="sbtn primary" id="qContinue">Skip</button>
        </div>
      </div>
    </div>
    <div class="scrub" id="scrub" role="slider" tabindex="0" aria-label="Seek through the whole lesson" aria-valuemin="0">
      <div class="tip" id="tip" hidden></div>
    </div>
    <div class="controls">
      <button class="cbtn" id="play" aria-label="Play">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path id="playIcon" d="M7 4.5v15l12.5-7.5z" fill="currentColor"/></svg>
      </button>
      <button class="cbtn" id="back" aria-label="Back 10 seconds">
        <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4h4"/></svg>
      </button>
      <span class="time" id="time">0:00 / 0:00</span>
      <span class="nowtitle" id="nowtitle"></span>
      <button class="cbtn switch" id="qToggle" aria-pressed="true" title="Stop the video for questions">
        <span class="track" aria-hidden="true"></span><span>Questions</span>
      </button>
      <button class="cbtn" id="cc" aria-pressed="true" aria-label="Captions"><span class="pill">CC</span></button>
      <button class="cbtn" id="rate" aria-label="Playback speed">1×</button>
      <button class="cbtn" id="mute" aria-pressed="false" aria-label="Mute">
        <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor" stroke="none"/><path id="muteWaves" d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11" stroke-linecap="round"/></svg>
      </button>
      <button class="cbtn" id="full" aria-label="Full screen">
        <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>
      </button>
    </div>
  </div>
  <aside class="rail" aria-label="Parts and transcript">
    <div class="rail-inner">
      <div class="tabs" role="tablist">
        <button class="tab" role="tab" id="tabParts" aria-selected="true" aria-controls="panelParts">Parts</button>
        <button class="tab" role="tab" id="tabText" aria-selected="false" aria-controls="panelText">Transcript</button>
      </div>
      <div class="panel" id="panelParts" role="tabpanel" aria-labelledby="tabParts"><ol class="parts" id="parts"></ol></div>
      <div class="panel" id="panelText" role="tabpanel" aria-labelledby="tabText" hidden><div class="transcript" id="transcript"></div></div>
      <div class="hint-keys"><span><kbd>Space</kbd> play · <kbd>←</kbd><kbd>→</kbd> 5 s · <kbd>C</kbd> captions · <kbd>F</kbd> full screen</span><button class="reset" id="reset">Start over</button></div>
    </div>
  </aside>`;
}

function start(cfg) {
  cfg = Object.assign({ id: "lesson", endCard: { title: "That's the lesson.", text: "Now try the exercises.", button: "Go to the exercises", target: "#exercises" } }, cfg);
  STORE_PREFIX = cfg.id;
  const host = $("#player");
  host.classList.add("player");
  host.innerHTML = playerMarkup(cfg);

  /* ═════════════ the player ═════════════ */
  const DATA = window.LESSON_DATA && window.LESSON_DATA.parts ? window.LESSON_DATA.parts : [];
  const QUESTIONS = cfg.questions || {};
  const META = cfg.partMeta || {};
  const video = $("#video"), screenEl = $("#screen");
  const offsets = []; let total = 0;
  DATA.forEach((p) => { offsets.push(total); total += p.duration; });
  const answered = store.get("answers", {});
  const watched = store.get("watched", {});
  const prefs = Object.assign({ cc: true, questions: true, rate: 1, muted: false }, store.get("prefs", {}));
  const savePrefs = () => store.set("prefs", prefs);
  let cur = 0, lastT = 0, asking = null, seekingNow = false, started = false;

  function buildFacts() {
    const qn = DATA.reduce((n, p) => n + p.checkpoints.length, 0);
    const facts = [["Parts", DATA.length || "–"], ["Running time", total ? Math.round(total / 60) + " min" : "–"], ["Questions in the video", qn || "–"]];
    if (cfg.exercises && cfg.exercises.length) facts.push(["Exercises", String(cfg.exercises.length)]);
    if (!$("#facts")) return;
    $("#facts").replaceChildren(...facts.map(([k, v]) => el("div", {}, el("dt", { text: k }), el("dd", { text: String(v) }))));
  }

  function buildScrub() {
    const scrub = $("#scrub");
    scrub.setAttribute("aria-valuemax", Math.round(total));
    DATA.forEach((p, i) => {
      const seg = el("div", { class: "seg", "data-i": i, style: `flex:${p.duration} 1 0` }, el("div", { class: "fill" }));
      for (const cp of p.checkpoints) seg.append(el("i", { class: "cp", "data-id": cp.id, style: `left:${(100 * cp.t / p.duration).toFixed(2)}%` }));
      scrub.append(seg);
    });
    const locate = (clientX) => {
      const segs = [...scrub.querySelectorAll(".seg")];
      for (let i = 0; i < segs.length; i++) {
        const r = segs[i].getBoundingClientRect();
        if (clientX <= r.right + 1.5 || i === segs.length - 1) return { i, t: clamp((clientX - r.left) / r.width, 0, 0.999) * DATA[i].duration };
      }
      return { i: 0, t: 0 };
    };
    let dragging = false;
    const tip = $("#tip");
    scrub.addEventListener("pointerdown", (e) => { if (asking) return; dragging = true; scrub.setPointerCapture(e.pointerId); const { i, t } = locate(e.clientX); seek(i, t); });
    scrub.addEventListener("pointermove", (e) => {
      const { i, t } = locate(e.clientX);
      const r = scrub.getBoundingClientRect();
      tip.hidden = false; tip.style.left = clamp(e.clientX - r.left, 70, r.width - 70) + "px";
      tip.textContent = `${i + 1} · ${DATA[i].title} · ${fmtTime(offsets[i] + t)}`;
      if (dragging) seek(i, t);
    });
    scrub.addEventListener("pointerleave", () => { tip.hidden = true; });
    scrub.addEventListener("pointerup", () => { dragging = false; });
    scrub.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); nudge(e.key === "ArrowRight" ? 5 : -5); }
    });
  }

  function buildParts() {
    const list = $("#parts");
    DATA.forEach((p, i) => {
      const qs = p.checkpoints.map((c) => el("span", { class: "q" + (answered[c.id] ? " done" : ""), "data-id": c.id, title: answered[c.id] ? "Question answered" : "Has a question" }, el("i"), "question"));
      const btn = el("button", { class: "part", "data-i": i, onclick: () => { seek(i, 0); play(); } },
        el("span", { class: "thumb" }, el("img", { src: p.poster, alt: "", loading: "lazy" }), el("span", { class: "bar" })),
        el("span", {},
          el("span", { class: "num", text: `Part ${i + 1}` }),
          el("span", { class: "ttl", text: p.title }),
          el("span", { class: "meta" }, el("span", { text: META[p.scene] || "" }), el("span", { text: fmtTime(p.duration) }), ...qs)));
      list.append(el("li", {}, btn));
    });
  }

  function buildTranscript() {
    const box = $("#transcript");
    DATA.forEach((p, i) => {
      box.append(el("p", { class: "tpart", text: `Part ${i + 1} · ${p.title}` }));
      p.cues.forEach((c, j) => {
        box.append(el("button", { class: "cue", "data-i": i, "data-j": j, onclick: () => { seek(i, c.start); play(); } },
          el("span", { class: "t", text: fmtTime(offsets[i] + c.start) }), el("span", { class: "x", text: c.text })));
      });
    });
  }

  function loadPart(i, t, autoplay) {
    cur = i;
    const p = DATA[i];
    const src = new URL(p.video, location.href).href;
    if (video.src !== src) {
      video.src = p.video;
      video.poster = p.poster;
      video.defaultPlaybackRate = prefs.rate;
      video.addEventListener("loadedmetadata", () => {
        video.playbackRate = prefs.rate;
        if (t > 0) video.currentTime = t;
        lastT = t;
        if (autoplay) play();
      }, { once: true });
    } else {
      video.currentTime = t; lastT = t;
      if (autoplay) play();
    }
    lastT = t;
    $("#endcard").hidden = true;
    document.querySelectorAll(".part").forEach((b) => b.setAttribute("aria-current", String(+b.dataset.i === i)));
    $("#nowtitle").innerHTML = "";
    $("#nowtitle").append(el("b", { text: `Part ${i + 1}` }), " · " + p.title);
  }
  function seek(i, t) {
    if (asking) return;
    if (i !== cur) loadPart(i, t, !video.paused);
    else { video.currentTime = t; lastT = t; }
  }
  function nudge(d) {
    let g = offsets[cur] + video.currentTime + d;
    g = clamp(g, 0, total - 0.1);
    let i = DATA.length - 1; while (i > 0 && offsets[i] > g) i--;
    seek(i, g - offsets[i]);
  }
  function play() { if (asking) return; $("#endcard").hidden = true; const pr = video.play(); if (pr) pr.catch(() => {}); }
  function togglePlay() { if (asking) return; video.paused ? play() : video.pause(); }

  function syncButtons() {
    const paused = video.paused;
    $("#playIcon").setAttribute("d", paused ? "M7 4.5v15l12.5-7.5z" : "M6.5 4.5h4v15h-4zM13.5 4.5h4v15h-4z");
    $("#play").setAttribute("aria-label", paused ? "Play" : "Pause");
    $("#bigplay").hidden = !paused || !!asking || !$("#endcard").hidden;
  }
  video.addEventListener("play", () => { started = true; syncButtons(); });
  video.addEventListener("pause", syncButtons);
  video.addEventListener("seeking", () => { seekingNow = true; });
  video.addEventListener("seeked", () => { seekingNow = false; lastT = video.currentTime; });
  video.addEventListener("ended", () => {
    if (cur < DATA.length - 1) loadPart(cur + 1, 0, true);
    else { $("#endcard").hidden = false; syncButtons(); }
  });

  let activeCue = null;
  function frame() {
    if (DATA.length) {
      const p = DATA[cur], t = video.currentTime || 0;
      // stop for questions
      if (!video.paused && !seekingNow && prefs.questions && !asking) {
        for (const cp of p.checkpoints) {
          if (lastT < cp.t && t >= cp.t && !answered[cp.id]) { video.pause(); video.currentTime = cp.t; openQuestion(cp.id); break; }
        }
      }
      if (!seekingNow) lastT = t;
      // timeline
      document.querySelectorAll("#scrub .seg").forEach((s, i) => {
        s.classList.toggle("current", i === cur);
        s.firstChild.style.width = (i < cur ? 100 : i > cur ? 0 : 100 * t / DATA[i].duration) + "%";
      });
      $("#scrub").setAttribute("aria-valuenow", Math.round(offsets[cur] + t));
      $("#scrub").setAttribute("aria-valuetext", `${fmtTime(offsets[cur] + t)} of ${fmtTime(total)}`);
      $("#time").textContent = `${fmtTime(offsets[cur] + t)} / ${fmtTime(total)}`;
      // how far each part has been watched
      const w = Math.max(watched[cur] || 0, t / p.duration);
      if (w - (watched[cur] || 0) > 0.01) { watched[cur] = w; store.set("watched", watched); }
      document.querySelectorAll(".part .bar").forEach((b, i) => { b.style.width = (100 * (watched[i] || 0)) + "%"; });
      // captions + transcript
      const j = p.cues.findIndex((c) => t >= c.start - 0.05 && t < c.end + 0.6);
      const key = j < 0 ? null : cur + ":" + j;
      if (key !== activeCue) {
        activeCue = key;
        document.querySelectorAll(".cue.active").forEach((c) => c.classList.remove("active"));
        const cap = $("#caption");
        if (key) {
          const item = document.querySelector(`.cue[data-i="${cur}"][data-j="${j}"]`);
          item.classList.add("active");
          cap.innerHTML = item.querySelector(".x").innerHTML;
          const panel = $("#panelText");
          if (!panel.hidden && !panel.matches(":hover")) panel.scrollTo({ top: item.offsetTop - panel.clientHeight / 3, behavior: "smooth" });
        }
      }
      $("#caption").hidden = !prefs.cc || !activeCue || !!asking || !started;
    }
    requestAnimationFrame(frame);
  }

  /* ── question overlay ── */
  const qEl = $("#question");
  let qWidget = null;
  function openQuestion(id) {
    const q = QUESTIONS[id]; if (!q) return;
    asking = { id, solved: false };
    qEl.hidden = false; syncButtons();
    $("#qPart").textContent = `Part ${cur + 1}`;
    $("#qPrompt").innerHTML = q.prompt;
    $("#qFeedback").className = "qfeedback"; $("#qFeedback").textContent = "";
    $("#qContinue").textContent = "Skip";
    const body = $("#qBody"); body.replaceChildren();
    qWidget = WIDGETS[q.kind](q, body, API);
    $("#qCheck").hidden = !qWidget.check;
    typeset(qEl).then(() => { qWidget.redraw && qWidget.redraw(); });
    (qEl.querySelector("input, .choice, canvas") || $("#qContinue")).focus({ preventScroll: true });
  }
  function settle(ok, html) {
    const fb = $("#qFeedback");
    fb.className = "qfeedback " + (ok ? "ok" : "no");
    fb.innerHTML = html;
    typeset(fb);
    if (ok && asking) {
      asking.solved = true;
      answered[asking.id] = "correct"; store.set("answers", answered);
      $("#qContinue").textContent = "Continue";
      markAnswered(asking.id);
    }
  }
  function markAnswered(id) {
    document.querySelectorAll(`[data-id="${id}"]`).forEach((n) => { n.classList.add("done"); });
  }
  function closeQuestion() {
    if (!asking) return;
    if (!answered[asking.id]) { answered[asking.id] = "skipped"; store.set("answers", answered); markAnswered(asking.id); }
    if (qWidget && qWidget.dispose) qWidget.dispose();
    redrawers.delete(qWidget && qWidget.redraw);
    asking = null; qWidget = null; qEl.hidden = true;
    play();
  }
  $("#qContinue").addEventListener("click", closeQuestion);
  $("#qCheck").addEventListener("click", () => qWidget && qWidget.check && qWidget.check());
  $("#qReveal").addEventListener("click", () => {
    const q = QUESTIONS[asking.id];
    qWidget && qWidget.reveal && qWidget.reveal();
    const fb = $("#qFeedback"); fb.className = "qfeedback"; fb.innerHTML = q.explain; typeset(fb);
    $("#qContinue").textContent = "Continue";
  });

  const WIDGETS = {
    choice(q, body) {
      const row = el("div", { class: "choices", role: "group", "aria-label": "Answers" });
      q.options.forEach((o, i) => row.append(el("button", { class: "choice", html: o, onclick: (e) => {
        const ok = i === q.answer;
        e.currentTarget.classList.add(ok ? "right" : "wrong");
        settle(ok, ok ? "Right. " + q.explain : "Not quite. Try another one.");
      } })));
      body.append(row);
      return { reveal: () => row.children[q.answer].classList.add("right") };
    },
    number(q, body) {
      const id = "qnum";
      const inp = el("input", { type: "text", id, inputmode: "decimal", autocomplete: "off", placeholder: "e.g. 0.5 or 1/2" });
      body.append(el("div", { class: "numrow" }, el("label", { for: id, html: q.label }), inp, q.unit ? el("span", { class: "readout", html: q.unit }) : null));
      const check = () => {
        let v; try { v = parseNumber(inp.value); } catch (e) { return settle(false, "I couldn't read that. Use a number like <code>0.5</code> or a fraction like <code>1/2</code>."); }
        near(v, q.answer) ? settle(true, "Right. " + q.explain) : settle(false, "Not quite. Have another go, or press Show me.");
      };
      inp.addEventListener("keydown", (e) => { if (e.key === "Enter") check(); e.stopPropagation(); });
      return { check, reveal: () => { inp.value = String(+q.answer.toFixed(4)); } };
    },
  };
  Object.assign(WIDGETS, cfg.widgets || {});
  const API = { settle, typeset, redrawers };

  /* ── controls ── */
  function setPressed(btn, v) { btn.setAttribute("aria-pressed", String(v)); }
  $("#play").addEventListener("click", togglePlay);
  $("#bigplay").addEventListener("click", play);
  video.addEventListener("click", togglePlay);
  $("#back").addEventListener("click", () => nudge(-10));
  $("#cc").addEventListener("click", () => { prefs.cc = !prefs.cc; setPressed($("#cc"), prefs.cc); savePrefs(); });
  $("#qToggle").addEventListener("click", () => { prefs.questions = !prefs.questions; setPressed($("#qToggle"), prefs.questions); savePrefs(); });
  const RATES = [1, 1.25, 1.5, 0.75];
  const showRate = () => { $("#rate").textContent = prefs.rate + "×"; };
  $("#rate").addEventListener("click", () => {
    prefs.rate = RATES[(RATES.indexOf(prefs.rate) + 1) % RATES.length];
    video.playbackRate = video.defaultPlaybackRate = prefs.rate; showRate(); savePrefs();
  });
  const showMute = () => { setPressed($("#mute"), video.muted); $("#muteWaves").style.opacity = video.muted ? 0.15 : 1; $("#mute").setAttribute("aria-label", video.muted ? "Unmute" : "Mute"); };
  $("#mute").addEventListener("click", () => { video.muted = !video.muted; prefs.muted = video.muted; showMute(); savePrefs(); });
  $("#full").addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else if (screenEl.requestFullscreen) screenEl.requestFullscreen().catch(() => {});
  });
  document.addEventListener("fullscreenchange", () => setTimeout(redrawAll, 60));
  $("#toExercises").addEventListener("click", () => { const t = $(cfg.endCard.target || "#exercises"); if (t) t.scrollIntoView({ behavior: "smooth" }); });
  $("#rewatch").addEventListener("click", () => { seek(0, 0); play(); });
  $("#reset").addEventListener("click", (e) => {
    const b = e.currentTarget;
    if (b.dataset.armed !== "1") { b.dataset.armed = "1"; b.textContent = "Clear all answers and progress?"; setTimeout(() => { b.dataset.armed = ""; b.textContent = "Start over"; }, 4000); return; }
    for (const k of ["answers", "watched", "exercises"]) store.set(k, {});
    location.reload();
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, select, textarea") || e.metaKey || e.ctrlKey || e.altKey || asking) return;
    if (e.target.closest(".lab, .ex")) return;
    const k = e.key.toLowerCase();
    if (k === " " || k === "k") { if (e.target.closest("button")) return; e.preventDefault(); togglePlay(); }
    else if (k === "arrowright" || k === "l") { e.preventDefault(); nudge(5); }
    else if (k === "arrowleft" || k === "j") { e.preventDefault(); nudge(-5); }
    else if (k === "c") $("#cc").click();
    else if (k === "f") $("#full").click();
    else if (k === "m") $("#mute").click();
  });
  for (const [tab, panel, other, otherPanel] of [["#tabParts", "#panelParts", "#tabText", "#panelText"], ["#tabText", "#panelText", "#tabParts", "#panelParts"]]) {
    $(tab).addEventListener("click", () => {
      $(tab).setAttribute("aria-selected", "true"); $(other).setAttribute("aria-selected", "false");
      $(panel).hidden = false; $(otherPanel).hidden = true;
      if (panel === "#panelText") { const a = $(".cue.active"); if (a) $(panel).scrollTop = a.offsetTop - $(panel).clientHeight / 3; }
    });
  }


  /* ── exercises ── */
  const EXERCISES = cfg.exercises || [];
  const EXWIDGETS = cfg.exWidgets || {};
  const exState = store.get("exercises", {});
  function exStatus(n, s) {
    if (s && exState[n] !== "solved") { exState[n] = s; store.set("exercises", exState); }
    const st = exState[n];
    const chip = document.querySelector(`#ex${n} .status`);
    chip.className = "status " + (st || "");
    chip.textContent = st === "solved" ? "Solved" : st === "revealed" ? "Answer shown" : "To do";
    const dot = document.querySelector(`#exDots a[href="#ex${n}"]`);
    dot.className = st || "";
    const solved = EXERCISES.filter((e) => exState[e.n] === "solved").length;
    $("#exCount").textContent = `${solved} of ${EXERCISES.length} solved`;
  }
  function buildExercises() {
    const sheet = $("#sheet"), dots = $("#exDots");
    for (const ex of EXERCISES) {
      dots.append(el("a", { href: `#ex${ex.n}`, text: String(ex.n), "aria-label": `Exercise ${ex.n}` }));
      const card = el("article", { class: "ex", id: `ex${ex.n}` });
      card.append(el("div", { class: "ex-head" }, el("span", { class: "ex-no", text: `${ex.n}.` }), el("p", { class: "ex-text", text: ex.text }), el("span", { class: "status" })));
      if (ex.widget) { const w = el("div", { class: "widget" }); card.append(w); EXWIDGETS[ex.widget](w, ex); }
      const marks = [], inputs = [];
      if (ex.fields) {
        const fs = el("div", { class: "fields" });
        ex.fields.forEach((f, i) => {
          const id = `ex${ex.n}f${i}`;
          const inp = el("input", { type: "text", id, autocomplete: "off", spellcheck: "false", inputmode: f.angle ? "text" : "decimal", placeholder: f.ph || "" });
          const mk = el("span", { class: "mark", "aria-live": "polite" });
          inp.addEventListener("keydown", (e) => { if (e.key === "Enter") check(); });
          inputs.push(inp); marks.push(mk);
          fs.append(el("div", { class: "field" }, el("label", { for: id, text: f.label }), el("span", { class: "inp" }, inp, mk)));
        });
        card.append(fs);
      }
      const fb = el("div", { class: "feedback", "aria-live": "polite" });
      const hint = el("p", { class: "note", hidden: true }, el("b", { text: "Hint. " }), ex.hint);
      const sol = el("p", { class: "note", hidden: true }, el("b", { text: "Answer. " }), ex.solution);
      function check() {
        let bad = null;
        const vals = inputs.map((inp, i) => {
          if (!inp.value.trim()) return null;
          try { return ex.fields[i].angle ? parseAngle(inp.value) : parseNumber(inp.value); }
          catch (e) { bad = e.message; return NaN; }
        });
        const ok = ex.fields.map(() => false);
        const used = new Set();
        ex.fields.forEach((f, i) => {
          const v = vals[i]; if (v == null || Number.isNaN(v)) return;
          const match = (ans) => (f.angle ? nearAngle : near)(v, ans);
          if (f.group) {
            const j = ex.fields.findIndex((g, k) => g.group === f.group && !used.has(k) && match(g.answer));
            if (j >= 0) { used.add(j); ok[i] = true; }
          } else ok[i] = match(f.answer) || (f.alt || []).some(match);
        });
        marks.forEach((mk, i) => {
          const empty = vals[i] == null;
          mk.textContent = empty ? "" : ok[i] ? "✓" : "✗";
          mk.className = "mark " + (empty ? "" : ok[i] ? "ok" : "no");
          mk.setAttribute("aria-label", empty ? "" : ok[i] ? "correct" : "not right yet");
        });
        if (bad) { fb.className = "feedback no"; fb.textContent = `I couldn't read one of those (${bad}). Try a number, 1/3, sqrt(2) or 26°34'.`; return; }
        if (ok.every(Boolean)) { fb.className = "feedback ok"; fb.textContent = "All correct."; exStatus(ex.n, "solved"); }
        else if (vals.some((v) => v == null)) { fb.className = "feedback"; fb.textContent = "Fill in every box, then check again."; }
        else { fb.className = "feedback no"; fb.textContent = "Not all there yet. The crosses show which to look at again."; }
      }
      const actions = el("div", { class: "ex-actions" });
      if (ex.fields) actions.append(el("button", { class: "btn primary", text: "Check", onclick: check }));
      if (ex.proof) actions.append(el("button", { class: "btn primary", text: "I've shown it", onclick: () => { exStatus(ex.n, "solved"); fb.className = "feedback ok"; fb.textContent = "Marked as done. Compare with the worked answer if you like."; } }));
      actions.append(
        el("button", { class: "btn quiet", text: "Hint", onclick: () => { hint.hidden = !hint.hidden; } }),
        el("button", { class: "btn quiet", text: "Show answer", onclick: () => { sol.hidden = false; exStatus(ex.n, "revealed"); } }),
        fb);
      card.append(actions, hint, sol);
      sheet.append(card);
      exStatus(ex.n);
    }
  }


  /* ── start ── */
  if (window.LESSON_DATA && window.LESSON_DATA.voice && $("#voiceCredit")) $("#voiceCredit").textContent = `Narration voiced with ${window.LESSON_DATA.voice}.`;
  buildFacts();
  if ($("#sheet")) buildExercises();
  if (DATA.length) {
    buildScrub(); buildParts(); buildTranscript();
    setPressed($("#cc"), prefs.cc); setPressed($("#qToggle"), prefs.questions); showRate();
    video.muted = prefs.muted; showMute();
    Object.keys(answered).forEach(markAnswered);
    loadPart(0, 0, false);
    syncButtons();
    requestAnimationFrame(frame);
  } else {
    $("#stage").append(el("p", { class: "caption", text: "The video hasn't been built yet. Run lessonkit/build.py for this lesson, then reload." }));
    $("#bigplay").hidden = true;
  }
  typeset(document.querySelector(".wrap") || document.body).then(redrawAll);
}

window.Lesson = {
  start,
  util: { $, el, clamp, fmtTime, store, css, typeset, compile, parseNumber, parseAngle, near, nearAngle, dms, fmtNum, Plot, dragX, redrawers, redrawAll },
};
})();
