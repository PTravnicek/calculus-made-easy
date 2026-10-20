"""Linear Motion: speed, velocity, acceleration and free fall.

One Scene per part of the interactive video. Render one with
    ../../.venv/bin/manim -ql scenes.py LM04Acceleration
or all of them, for the web player, with lessonkit/build.py linear-motion.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lessonkit"))
from narration import *  # noqa: E402
import narration  # noqa: E402

# Units read aloud properly when a line has no explicit say= text.
narration._SPEECH[:0] = [
    (r"m/s²", " metres per second squared "),
    (r"km/h", " kilometres per hour "),
    (r"m/s", " metres per second "),
]

VEL = YELLOW          # velocity: the slope of the distance graph, so the same colour as a tangent
ACC = "#FF8C42"       # acceleration
BODY = TEAL_C         # moving things
GROUND = GREY_C


# ── little props ────────────────────────────────────────────────────────
def make_cart(color=BODY, w=1.0):
    body = RoundedRectangle(corner_radius=0.08 * w, width=w, height=0.34 * w, stroke_width=0,
                            fill_color=color, fill_opacity=1)
    cabin = RoundedRectangle(corner_radius=0.08 * w, width=0.52 * w, height=0.26 * w, stroke_width=0,
                             fill_color=color, fill_opacity=0.55)
    cabin.next_to(body, UP, buff=0).shift(0.08 * w * LEFT)
    wheels = VGroup(*[Circle(radius=0.12 * w, stroke_color=GREY_A, stroke_width=2, fill_color=BG, fill_opacity=1)
                      .move_to(body.get_bottom() + dx * w * RIGHT) for dx in (-0.27, 0.27)])
    return VGroup(cabin, body, wheels)


def make_ball(color=BLUE_C, r=0.17):
    return VGroup(Circle(radius=r, stroke_width=0, fill_color=color, fill_opacity=1),
                  Circle(radius=r * 0.33, stroke_width=0, fill_color=WHITE, fill_opacity=0.35).shift(r * 0.33 * UL))


def arrow(start, vec, color=VEL, sw=6):
    vec = np.array(vec, dtype=float)
    if np.linalg.norm(vec) < 0.05:
        # keep it an Arrow (always_redraw swaps mobjects in place), just invisible
        return Arrow(start, start + 0.06 * RIGHT, buff=0, color=color, stroke_width=sw).set_opacity(0)
    return Arrow(start, start + vec, buff=0, color=color, stroke_width=sw,
                 max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10)


def gauge(value_fn, vmax, major, minor, unit, radius=1.15, decimals=0):
    """A speedometer: 240° dial, needle and digital readout, following value_fn()."""
    a0, sweep = 210 * DEGREES, -240 * DEGREES
    ang = lambda v: a0 + sweep * min(max(v / vmax, 0), 1)
    hub = Dot(ORIGIN, radius=0.07, color=GREY_A)
    dial = VGroup(Arc(radius=radius, start_angle=a0, angle=sweep, color=GREY_B, stroke_width=3))
    v = 0.0
    while v <= vmax + 1e-9:
        d = np.array([np.cos(ang(v)), np.sin(ang(v)), 0])
        big = abs(v / major - round(v / major)) < 1e-6
        dial.add(Line(d * radius * (0.8 if big else 0.9), d * radius, color=GREY_B, stroke_width=2.2 if big else 1.2))
        if big:
            dial.add(MathTex(str(int(round(v)))).scale(0.42).move_to(d * radius * 0.6))
        v += minor
    needle = always_redraw(lambda: Line(
        hub.get_center(),
        hub.get_center() + radius * 0.86 * np.array([np.cos(ang(value_fn())), np.sin(ang(value_fn())), 0]),
        color=VEL, stroke_width=4))
    num = DecimalNumber(value_fn(), num_decimal_places=decimals).scale(0.62).next_to(hub, DOWN, buff=0.42)
    num.add_updater(lambda m: m.set_value(value_fn()).next_to(hub, DOWN, buff=0.42))
    unit_t = Tex(unit, color=MUTED).scale(0.5).next_to(num, DOWN, buff=0.08)
    unit_t.add_updater(lambda m: m.next_to(num, DOWN, buff=0.08))
    return VGroup(dial, needle, hub, num, unit_t)


def clock_readout(t_fn, label="t", unit="s", decimals=1, scale=0.8):
    lhs = MathTex(label, "=").scale(scale)
    num = DecimalNumber(t_fn(), num_decimal_places=decimals).scale(scale)
    u = MathTex(r"\text{" + unit + "}").scale(scale)
    num.next_to(lhs, RIGHT, buff=0.15)
    u.next_to(num, RIGHT, buff=0.12)
    num.add_updater(lambda m: m.set_value(t_fn()).next_to(lhs, RIGHT, buff=0.15))
    u.add_updater(lambda m: m.next_to(num, RIGHT, buff=0.12))
    return VGroup(lhs, num, u)


def fade_all(scene, run_time=0.8):
    scene.play(*[FadeOut(o) for o in scene.mobjects], run_time=run_time)


# ════════════════════════════════════════════════════════════════════════
class LM01Speed(Narrated, Scene):
    chapter_title = "Speed"

    def construct(self):
        self.opening()

        formula = MathTex(r"\text{speed}", "=", r"\frac{\text{distance}}{\text{time}}").scale(1.1).to_edge(UP, buff=0.7)
        with self.voice(
            "Calling something fast or slow is vague. Galileo made it precise: measure the distance covered, "
            "measure the time it takes, and divide one by the other."
        ) as v:
            self.wait(v.left(frac=0.5))
            self.play(Write(formula), run_time=v.left(minimum=1.0))

        # a cyclist covers 30 m in 5 s
        track = NumberLine(x_range=[0, 40, 5], length=11, include_numbers=True, font_size=26,
                           color=GROUND).shift(1.6 * DOWN)
        m_lab = Tex("metres", color=MUTED).scale(0.55).next_to(track, RIGHT, buff=0.25)
        s = ValueTracker(0)
        bike = make_cart(BODY, 0.8)
        bike.add_updater(lambda m: m.next_to(track.n2p(s.get_value()), UP, buff=0.05))
        t_read = clock_readout(lambda: s.get_value() / 6).move_to([3.8, 0.9, 0])
        with self.voice("Take a cyclist who rides thirty metres in five seconds.") as v:
            self.play(Create(track), FadeIn(m_lab), FadeIn(bike), FadeIn(t_read), run_time=1.2)
            self.play(s.animate.set_value(30), run_time=5.0, rate_func=linear)
        brace = BraceBetweenPoints(track.n2p(0) + 0.9 * UP, track.n2p(30) + 0.9 * UP, UP)
        b_lab = MathTex(r"30\ \text{m in } 5\ \text{s}").scale(0.8).next_to(brace, UP, buff=0.1)
        calc = MathTex(r"\frac{30\ \text{m}}{5\ \text{s}} = 6\ \text{m/s}").scale(1.0).move_to([-3.6, 0.9, 0])
        with self.voice("Thirty metres divided by five seconds is six metres per second.",
                        say="Thirty metres, divided by five seconds, is six metres per second.") as v:
            self.play(GrowFromCenter(brace), FadeIn(b_lab), run_time=0.8)
            self.play(Write(calc), run_time=v.left(minimum=1.0))

        conv = VGroup(
            MathTex(r"1\ \text{m/s} = \frac{3600\ \text{m}}{1\ \text{h}} = 3.6\ \text{km/h}").scale(0.85),
            MathTex(r"6\ \text{m/s} \approx 22\ \text{km/h}").scale(0.85),
        ).arrange(DOWN, buff=0.35).move_to([0, 0.6, 0])
        with self.voice(
            "Any distance over any time will do. For cars we use kilometres per hour. One metre every second is "
            "three thousand six hundred metres an hour, or 3.6 kilometres per hour, so our cyclist is doing about 22.",
            say="Any distance over any time will do. For cars we use kilometres per hour. One metre every second is "
                "three thousand six hundred metres an hour, or three point six kilometres per hour. So our cyclist "
                "is doing about twenty two.",
        ) as v:
            self.play(FadeOut(calc), FadeOut(t_read), FadeOut(brace), FadeOut(b_lab), run_time=0.5)
            self.play(Write(conv[0]), run_time=2.0)
            self.wait(v.left(frac=0.5))
            self.play(Write(conv[1]), run_time=v.left(minimum=1.0))
        bike.clear_updaters()
        fade_all(self)

        self.trip()

    def trip(self):
        # speed profile of a 30-minute drive (km/h against minutes)
        pts = [(0, 0), (2, 60), (8, 60), (9, 0), (11, 0), (13, 90), (28, 90), (30, 0)]
        def speed(tm):
            for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
                if tm <= t1:
                    return v0 + (v1 - v0) * (tm - t0) / (t1 - t0)
            return 0.0
        ts = np.linspace(0, 30, 3001)
        dist = np.concatenate([[0], np.cumsum((np.array([speed(t) for t in ts[1:]]) +
                                               np.array([speed(t) for t in ts[:-1]])) / 2 * (ts[1] - ts[0]) / 60)])
        km = lambda tm: float(np.interp(tm, ts, dist))
        total = km(30)  # 33 km

        tm = ValueTracker(0)
        road = Line([-6.3, 1.2, 0], [6.3, 1.2, 0], color=GROUND, stroke_width=3)
        marks = VGroup(*[Line([x, 1.12, 0], [x, 1.28, 0], color=GROUND, stroke_width=2) for x in np.linspace(-6.3, 6.3, 12)])
        start_l = Tex("start", color=MUTED).scale(0.5).next_to(road.get_start(), DOWN, buff=0.15)
        end_l = Tex("33 km", color=MUTED).scale(0.5).next_to(road.get_end(), DOWN, buff=0.15)
        car = make_cart(BLUE_C, 0.7)
        car.add_updater(lambda m: m.next_to(road.get_start() + (12.6 * km(tm.get_value()) / total) * RIGHT, UP, buff=0.02))
        dial = gauge(lambda: speed(tm.get_value()), 120, 20, 10, "km/h").move_to([-3.2, -1.7, 0])
        dial_l = Tex("instantaneous speed", color=MUTED).scale(0.6).next_to(dial, UP, buff=0.25)
        odo = VGroup(Tex("distance", color=MUTED).scale(0.6), DecimalNumber(0, num_decimal_places=1).scale(0.9),
                     Tex("km").scale(0.6))
        clock = VGroup(Tex("time", color=MUTED).scale(0.6), DecimalNumber(0, num_decimal_places=0).scale(0.9),
                       Tex("min").scale(0.6))
        panel = VGroup(odo, clock)
        for row in panel:
            row.arrange(RIGHT, buff=0.2, aligned_edge=DOWN)
        panel.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([2.6, -1.4, 0])
        odo[1].add_updater(lambda m: m.set_value(km(tm.get_value())))
        clock[1].add_updater(lambda m: m.set_value(tm.get_value()))
        odo[2].add_updater(lambda m: m.next_to(odo[1], RIGHT, buff=0.15, aligned_edge=DOWN))
        clock[2].add_updater(lambda m: m.next_to(clock[1], RIGHT, buff=0.15, aligned_edge=DOWN))

        with self.voice(
            "On a real trip the speed keeps changing. The speedometer shows the speed at each instant, "
            "the instantaneous speed: up to sixty, down to zero at a red light, then ninety on the open road."
        ) as v:
            self.play(Create(road), FadeIn(marks), FadeIn(start_l), FadeIn(end_l), FadeIn(car), run_time=1.0)
            self.play(FadeIn(dial), FadeIn(dial_l), FadeIn(panel), run_time=0.8)
            self.play(tm.animate.set_value(30), run_time=v.left(minimum=6.0), rate_func=linear)
        avg = MathTex(r"\text{average speed} = \frac{\text{total distance}}{\text{total time}}",
                      r"= \frac{33\ \text{km}}{0.5\ \text{h}} = 66\ \text{km/h}").scale(0.8)
        avg.arrange(DOWN, buff=0.3).move_to([0, 3.0, 0])
        with self.voice(
            "For the whole trip, the car covered 33 kilometres in half an hour. Its average speed is total distance "
            "over total time: 66 kilometres per hour, a number the speedometer showed only in passing.",
            say="For the whole trip, the car covered thirty three kilometres in half an hour. Its average speed is "
                "total distance over total time: sixty six kilometres per hour, a number the speedometer showed "
                "only in passing.",
        ) as v:
            self.play(Write(avg[0]), run_time=2.0)
            self.wait(v.left(frac=0.4))
            self.play(Write(avg[1]), run_time=v.left(minimum=1.0))

        rearr = MathTex(r"\text{distance} = \text{average speed} \times \text{time}", color=NOTE).scale(0.8).move_to([0, -3.3, 0])
        with self.voice("Turn it round, and distance is average speed multiplied by time.") as v:
            self.play(Write(rearr), run_time=v.left(minimum=1.0))

        card = self.ponder_card(r"A coach averages $75$ km/h on a journey",
                                r"lasting 2 hours 24 minutes. How far does it go?").move_to([3.2, -1.6, 0])
        keep_in_frame(card)
        with self.voice("Pause and try one: a coach averages 75 kilometres per hour on a journey of 2 hours and 24 minutes. "
                        "How far does it go?",
                        say="Pause and try one. A coach averages seventy five kilometres per hour, on a journey of "
                            "two hours and twenty four minutes. How far does it go?") as v:
            self.play(FadeOut(panel), FadeOut(rearr), FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("lm1-coach")
        ans = MathTex(r"2\,\text{h}\ 24\,\text{min} = 2.4\ \text{h}", r"\quad 75 \times 2.4 = 180\ \text{km}").scale(0.8)
        ans.arrange(DOWN, buff=0.25).move_to([3.2, -1.6, 0])
        with self.voice("Twenty-four minutes is 0.4 of an hour, so the journey lasts 2.4 hours, and 75 times 2.4 is 180 kilometres.",
                        say="Twenty four minutes is zero point four of an hour, so the journey lasts two point four hours. "
                            "Seventy five times two point four is one hundred and eighty kilometres.") as v:
            self.play(FadeOut(card), run_time=0.4)
            self.play(Write(ans[0]), run_time=1.4)
            self.play(Write(ans[1]), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        car.clear_updaters()
        fade_all(self)

    def opening(self):
        kicker = Tex("Mechanics", color=MUTED).scale(0.8)
        title = Tex("Linear Motion").scale(1.9)
        sub = Tex(r"speed $\cdot$ velocity $\cdot$ acceleration $\cdot$ free fall", color=POINT).scale(0.75)
        g = VGroup(kicker, title, sub).arrange(DOWN, buff=0.4)
        ball = make_ball(BLUE_C, 0.14).move_to([-5.5, 2.8, 0])
        with self.voice(
            "This lesson is about the simplest motion there is: motion along a straight line. On the way we'll meet "
            "speed, velocity, acceleration, and the way things fall."
        ) as v:
            self.play(FadeIn(kicker, shift=0.2 * DOWN), Write(title), run_time=2.0)
            self.play(FadeIn(sub), run_time=0.8)
            self.add(ball)
            self.play(ball.animate.move_to([5.5, 2.8, 0]), run_time=v.left(minimum=1.0), rate_func=linear)
        self.play(FadeOut(g, shift=0.3 * UP), FadeOut(ball), run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class LM02Relative(Narrated, Scene):
    chapter_title = "Motion is relative"

    def construct(self):
        self.section_card(2, "Motion is relative")

        sun = Circle(radius=0.45, stroke_width=0, fill_color=GOLD_C, fill_opacity=1).move_to([-3.2, 0.3, 0])
        orbit = Circle(radius=2.2, color=GREY_D, stroke_width=1.5).move_to(sun)
        th = ValueTracker(0.6)
        earth = always_redraw(lambda: Dot(sun.get_center() + 2.2 * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0]),
                                          radius=0.16, color=BLUE_C))
        e_v = always_redraw(lambda: arrow(earth.get_center(), 1.2 * np.array([-np.sin(th.get_value()), np.cos(th.get_value()), 0])))
        lab = VGroup(Tex(r"sitting still: $0$ m/s relative to the floor").scale(0.7),
                     Tex(r"about $30$ km/s relative to the Sun", color=VEL).scale(0.7)).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        lab.move_to([3.4, 0.3, 0])
        with self.voice(
            "Every speed is measured relative to something. Sitting in your chair, you're at rest relative to the floor. "
            "Yet the Earth is carrying you round the Sun at about thirty kilometres every second."
        ) as v:
            self.play(FadeIn(sun), Create(orbit), FadeIn(earth), run_time=1.2)
            self.play(Write(lab[0]), run_time=1.4)
            self.play(Create(e_v), Write(lab[1]), th.animate.set_value(1.6), run_time=v.left(minimum=1.5), rate_func=linear)
        fade_all(self, 0.6)

        # the moving walkway
        belt = RoundedRectangle(corner_radius=0.12, width=11, height=0.5, stroke_color=GREY_B, stroke_width=2,
                                fill_color="#1A1F26", fill_opacity=1).move_to([0, -1.0, 0])
        floor = Line([-7, -1.32, 0], [7, -1.32, 0], color=GROUND, stroke_width=2)
        shift = ValueTracker(0)
        def stripes():
            g = VGroup()
            x0 = belt.get_left()[0] + 0.2
            for k in range(-1, 24):
                x = x0 + ((k * 0.5 + shift.get_value()) % 11.0)
                if belt.get_left()[0] + 0.1 < x < belt.get_right()[0] - 0.1:
                    g.add(Line([x, -1.18, 0], [x - 0.12, -0.82, 0], color=GREY_C, stroke_width=2))
            return g
        st = always_redraw(stripes)
        belt_v = 1.5
        k = 0.9   # screen units per metre, for the arrows
        km = 0.32 # screen units per metre, for the motion itself
        walker_x = ValueTracker(-4.8)
        walker = always_redraw(lambda: VGroup(
            Circle(radius=0.2, stroke_width=0, fill_color=BODY, fill_opacity=1).move_to([walker_x.get_value(), -0.15, 0]),
            Line([walker_x.get_value(), -0.35, 0], [walker_x.get_value(), -0.75, 0], color=BODY, stroke_width=6)))
        belt_lab = Tex(r"walkway: $1.5$ m/s", color=GREEN_C).scale(0.65).next_to(belt, DOWN, buff=0.35).to_edge(LEFT, buff=0.8)
        with self.voice(
            "Now an airport's moving walkway. Its belt slides along at one and a half metres per second."
        ) as v:
            self.play(FadeIn(belt), Create(floor), FadeIn(st), run_time=1.0)
            self.play(shift.animate.set_value(belt_v * km * v.left(minimum=2.0)), FadeIn(belt_lab),
                      run_time=v.left(minimum=2.0), rate_func=linear)

        def arrows_row(rel):
            p = np.array([-1.8, 2.3, 0])
            a_belt = arrow(p, [belt_v * k * 1.3, 0, 0], GREEN_C)
            a_walk = arrow(p + [belt_v * k * 1.3, 0.0, 0] + 0.35 * UP, [rel * k * 1.3, 0, 0], VEL)
            a_sum = arrow(p + 0.9 * DOWN, [(belt_v + rel) * k * 1.3, 0, 0], WHITE)
            return a_belt, a_walk, a_sum
        a_belt, a_walk, a_sum = arrows_row(1.0)
        l_belt = Tex("1.5", color=GREEN_C).scale(0.6).next_to(a_belt, DOWN, buff=0.08)
        l_walk = Tex(r"$1.0$ relative to the belt", color=VEL).scale(0.6).next_to(a_walk, UP, buff=0.1)
        l_sum = Tex(r"$2.5$ m/s relative to the floor").scale(0.65).next_to(a_sum, DOWN, buff=0.12)
        with self.voice(
            "Walk along it at one metre per second, measured against the belt, and someone standing on the floor sees "
            "you go past at two and a half. The two velocities add."
        ) as v:
            self.add(walker)
            self.play(GrowArrow(a_belt), FadeIn(l_belt), run_time=0.8)
            self.play(GrowArrow(a_walk), FadeIn(l_walk), run_time=0.8)
            self.play(GrowArrow(a_sum), FadeIn(l_sum),
                      walker_x.animate.set_value(-4.8 + 2.5 * km * 2.2), shift.animate.increment_value(belt_v * km * 2.2),
                      run_time=2.2, rate_func=linear)
            rest = v.left(minimum=1.0)
            self.play(walker_x.animate.increment_value(2.5 * km * rest),
                      shift.animate.increment_value(belt_v * km * rest), run_time=rest, rate_func=linear)

        b_walk, b_sum = arrows_row(-1.0)[1:]
        m_walk = Tex(r"$1.0$ backwards", color=VEL).scale(0.6).next_to(b_walk, UP, buff=0.1)
        m_sum = Tex(r"$0.5$ m/s relative to the floor").scale(0.65).next_to(b_sum, DOWN, buff=0.12)
        with self.voice(
            "Turn round and walk the other way at the same pace, and relative to the floor you only creep forward, "
            "at half a metre per second."
        ) as v:
            self.play(Transform(a_walk, b_walk), Transform(l_walk, m_walk), Transform(a_sum, b_sum), Transform(l_sum, m_sum),
                      run_time=1.2)
            rest = v.left(minimum=1.5)
            self.play(walker_x.animate.increment_value(0.5 * km * rest),
                      shift.animate.increment_value(belt_v * km * rest), run_time=rest, rate_func=linear)

        card = self.ponder_card(r"A ferry heads upstream at $6$ m/s relative to the water.",
                                r"The river flows at $2$ m/s. How fast does the ferry",
                                r"pass the riverbank?").move_to([0, 2.0, 0])
        with self.voice(
            "Pause and ponder. A ferry heads upstream at six metres per second, relative to the water, against a current "
            "of two metres per second. How fast does it pass the riverbank?"
        ) as v:
            self.play(*[FadeOut(o) for o in (a_belt, l_belt, a_walk, l_walk, a_sum, l_sum, belt, floor, st, walker, belt_lab)],
                      run_time=0.5)
            self.play(FadeIn(card, shift=0.2 * DOWN), run_time=0.8)
        self.checkpoint("lm2-ferry")
        p = np.array([2.2, 2.5, 0])
        f_boat = arrow(p, [-6 * 0.6, 0, 0], VEL)
        f_river = arrow(p + [-6 * 0.6, 0, 0] + 0.4 * DOWN, [2 * 0.6, 0, 0], BLUE_C)
        f_sum = arrow(p + 1.1 * DOWN, [-4 * 0.6, 0, 0], WHITE)
        f_labs = VGroup(Tex(r"$6$ upstream", color=VEL).scale(0.6).next_to(f_boat, UP, buff=0.1),
                        Tex(r"$2$ current", color=BLUE_C).scale(0.6).next_to(f_river, RIGHT, buff=0.15),
                        Tex(r"$4$ m/s past the bank").scale(0.65).next_to(f_sum, DOWN, buff=0.12))
        with self.voice(
            "The current pushes back against it, so the velocities subtract: six minus two is four metres per second. "
            "From now on, unless we say otherwise, speeds are measured relative to the ground."
        ) as v:
            self.play(FadeOut(card), run_time=0.4)
            self.play(GrowArrow(f_boat), FadeIn(f_labs[0]), run_time=0.8)
            self.play(GrowArrow(f_river), FadeIn(f_labs[1]), run_time=0.8)
            self.play(GrowArrow(f_sum), FadeIn(f_labs[2]), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM03Velocity(Narrated, Scene):
    chapter_title = "Velocity"

    def construct(self):
        self.section_card(3, "Velocity")

        sp = VGroup(Tex(r"\textbf{speed}", color=WHITE).scale(0.8), Tex(r"$25$ m/s").scale(0.8),
                    Tex(r"how fast", color=MUTED).scale(0.6)).arrange(DOWN, buff=0.2)
        ve = VGroup(Tex(r"\textbf{velocity}", color=VEL).scale(0.8), Tex(r"$25$ m/s, heading east").scale(0.8),
                    Tex(r"how fast, and which way", color=MUTED).scale(0.6)).arrange(DOWN, buff=0.2)
        pair = VGroup(sp, ve).arrange(RIGHT, buff=2.2).move_to([0, 2.2, 0])
        kinds = VGroup(Tex(r"a scalar: just a size", color=MUTED).scale(0.55).next_to(sp, DOWN, buff=0.3),
                       Tex(r"a vector: size and direction", color=MUTED).scale(0.55).next_to(ve, DOWN, buff=0.3))
        with self.voice(
            "Speed tells you how fast. Velocity tells you how fast and in which direction. Speed is a plain number, "
            "a scalar; velocity is a vector, best drawn as an arrow."
        ) as v:
            self.play(FadeIn(sp, shift=0.2 * UP), run_time=0.8)
            self.play(FadeIn(ve, shift=0.2 * UP), run_time=0.8)
            self.wait(v.left(frac=0.5))
            self.play(FadeIn(kinds), run_time=v.left(minimum=0.8))

        road = NumberLine(x_range=[-6, 6, 1], length=12, include_tip=True, color=GROUND).shift(1.4 * DOWN)
        plus = Tex(r"$+$ direction", color=MUTED).scale(0.55).next_to(road.get_end(), UP, buff=0.15).shift(0.4 * LEFT)
        c1, c2 = make_cart(BLUE_C, 0.8), make_cart(MAROON_B, 0.8).flip()
        x1, x2 = ValueTracker(-4.5), ValueTracker(4.5)
        c1.add_updater(lambda m: m.next_to(road.n2p(x1.get_value()), UP, buff=0.05))
        c2.add_updater(lambda m: m.next_to(road.n2p(x2.get_value()), UP, buff=0.05))
        a1 = always_redraw(lambda: arrow(c1.get_top() + 0.25 * UP, [1.6, 0, 0], VEL))
        a2 = always_redraw(lambda: arrow(c2.get_top() + 0.25 * UP, [-1.6, 0, 0], VEL))
        l1 = Tex(r"$+25$ m/s", color=VEL).scale(0.6).add_updater(lambda m: m.next_to(a1, UP, buff=0.1))
        l2 = Tex(r"$-25$ m/s", color=VEL).scale(0.6).add_updater(lambda m: m.next_to(a2, UP, buff=0.1))
        with self.voice(
            "Two cars pass each other at 25 metres per second, one heading east, one west. Same speed, opposite velocities. "
            "On a straight road we let the sign carry the direction: plus 25 one way, minus 25 the other."
        ) as v:
            self.play(Create(road), FadeIn(plus), FadeIn(c1), FadeIn(c2), run_time=1.0)
            self.add(a1, a2, l1, l2)
            self.play(x1.animate.set_value(4.0), x2.animate.set_value(-4.0), run_time=v.left(minimum=3.0), rate_func=linear)
        for m in (c1, c2, l1, l2):
            m.clear_updaters()
        fade_all(self, 0.6)

        # constant velocity: equal steps in equal times
        road = NumberLine(x_range=[0, 12, 1], length=12, color=GROUND).shift(0.4 * DOWN)
        x = ValueTracker(0.5)
        cart = make_cart(BODY, 0.8)
        cart.add_updater(lambda m: m.next_to(road.n2p(x.get_value()), UP, buff=0.05))
        va = always_redraw(lambda: arrow(cart.get_top() + 0.3 * UP, [1.4, 0, 0], VEL))
        ghosts = VGroup()
        with self.voice(
            "Constant velocity means a steady speed in an unchanging direction: a straight line, covered at an even pace. "
            "Snapshots taken every second come out evenly spaced."
        ) as v:
            self.play(Create(road), FadeIn(cart), run_time=0.8)
            self.add(va)
            step = v.left(minimum=3.0) / 4
            for k in range(4):
                g = make_cart(BODY, 0.8).set_opacity(0.3).next_to(road.n2p(x.get_value()), UP, buff=0.05)
                ghosts.add(g)
                self.add(g)
                self.play(x.animate.increment_value(2.5), run_time=step, rate_func=linear)
            self.add(make_cart(BODY, 0.8).set_opacity(0.3).next_to(road.n2p(x.get_value()), UP, buff=0.05))
        cart.clear_updaters()
        fade_all(self, 0.6)

        # round a circular track: speed constant, velocity turning
        centre = np.array([-2.6, -0.3, 0])
        R = 2.3
        track = Circle(radius=R, color=GROUND, stroke_width=3).move_to(centre)
        th = ValueTracker(-PI / 2)
        P = lambda: centre + R * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0])
        car = always_redraw(lambda: Dot(P(), radius=0.16, color=BODY))
        vel = always_redraw(lambda: arrow(P(), 1.5 * np.array([-np.sin(th.get_value()), np.cos(th.get_value()), 0])))
        info = VGroup(Tex(r"speed: $20$ m/s, the whole way round").scale(0.7),
                      Tex(r"velocity: always turning", color=VEL).scale(0.7)).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        info.move_to([3.6, 0.6, 0])
        with self.voice(
            "Now drive round a circular track at a steady 20 metres per second. The speed never changes, but the "
            "velocity changes every instant, because the direction does."
        ) as v:
            self.play(Create(track), FadeIn(car), run_time=1.0)
            self.add(vel)
            self.play(Write(info[0]), run_time=1.2)
            self.play(Write(info[1]), th.animate.set_value(PI), run_time=v.left(minimum=2.0), rate_func=linear)

        card = self.ponder_card(r"A cyclist rides round a roundabout", r"at a steady $20$ km/h.",
                                r"Which of these stays constant?").move_to([3.6, -1.9, 0])
        keep_in_frame(card)
        with self.voice(
            "Pause and ponder. A cyclist rides round a roundabout at a steady twenty kilometres per hour. "
            "Is the speed constant? The velocity? Both, or neither?"
        ) as v:
            self.play(FadeIn(card, shift=0.2 * UP), th.animate.set_value(PI + 1.2), run_time=v.left(minimum=1.0), rate_func=linear)
        self.checkpoint("lm3-roundabout")
        with self.voice(
            "Only the speed. The direction keeps changing, so the velocity does too, and as we'll see next, "
            "a changing velocity means the cyclist is accelerating."
        ) as v:
            self.play(FadeOut(card), th.animate.set_value(3 * PI), run_time=v.left(minimum=2.0), rate_func=linear)
        self.wait(0.4)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM04Acceleration(Narrated, Scene):
    chapter_title = "Acceleration"

    def construct(self):
        self.section_card(4, "Acceleration")

        formula = MathTex(r"\text{acceleration}", "=", r"\frac{\text{change in velocity}}{\text{time it takes}}",
                          r"\qquad a = \frac{\Delta v}{\Delta t}").scale(0.9).to_edge(UP, buff=0.6)
        formula[3].set_color(ACC)
        with self.voice(
            "Acceleration measures how quickly velocity changes: the change in velocity, divided by the time it takes "
            "to happen."
        ) as v:
            self.play(Write(formula[:3]), run_time=2.0)
            self.play(Write(formula[3]), run_time=v.left(minimum=1.0))

        k = 0.66  # screen units per metre
        road = NumberLine(x_range=[0, 18, 2], length=18 * k, include_numbers=True, font_size=22, color=GROUND)
        road.move_to([0, -0.9, 0])
        m_lab = Tex("m", color=MUTED).scale(0.55).next_to(road, RIGHT, buff=0.2)
        t = ValueTracker(0)
        scooter = make_cart(BODY, 0.7)
        scooter.add_updater(lambda m: m.next_to(road.n2p(t.get_value() ** 2), UP, buff=0.05))
        v_arrow = always_redraw(lambda: arrow(scooter.get_top() + 0.25 * UP, [0.22 * 2 * t.get_value(), 0, 0]))
        table = MathTable([["0", "1", "2", "3", "4"], ["0", "2", "4", "6", "8"]],
                          row_labels=[MathTex(r"t\ (\text{s})"), MathTex(r"v\ (\text{m/s})", color=VEL)],
                          include_outer_lines=False, h_buff=0.7, v_buff=0.35,
                          line_config={"stroke_width": 1, "color": MUTED}).scale(0.62).move_to([0, 1.2, 0])
        for c in range(2, 7):
            for r in (1, 2):
                table.get_entries((r, c)).set_opacity(0)
        with self.voice(
            "An electric scooter pulls away from rest. Every second it gains another two metres per second: "
            "zero, two, four, six, eight."
        ) as v:
            self.play(Create(road), FadeIn(m_lab), FadeIn(scooter), run_time=1.0)
            self.add(v_arrow)
            self.play(Create(table.get_horizontal_lines()), Create(table.get_vertical_lines()), FadeIn(table.get_row_labels()),
                      table.get_entries((1, 2)).animate.set_opacity(1), table.get_entries((2, 2)).animate.set_opacity(1), run_time=0.8)
            step = v.left(minimum=4.0) / 4
            for sec in range(1, 5):
                ghost = make_cart(BODY, 0.7).set_opacity(0.25).next_to(road.n2p((sec - 1) ** 2), UP, buff=0.05)
                self.add(ghost)
                self.play(t.animate.set_value(sec), table.get_entries((1, sec + 2)).animate.set_opacity(1),
                          table.get_entries((2, sec + 2)).animate.set_opacity(1), run_time=step, rate_func=linear)
        unit = MathTex(r"a = 2\ \frac{\text{m/s}}{\text{s}} = 2\ \text{m/s}^2", color=ACC).scale(0.9).move_to([3.6, 2.6, 0])
        with self.voice(
            "That steady gain is its acceleration: two metres per second, every second. The second appears twice, once "
            "inside the velocity and once for the time, so we write it as metres per second squared.",
            say="That steady gain is its acceleration: two metres per second, every second. The second appears twice, "
                "once inside the velocity, and once for the time, so we write it as metres per second squared.",
        ) as v:
            self.play(FadeOut(formula), run_time=0.4)
            self.play(Write(unit), run_time=v.left(minimum=1.0))
        scooter.clear_updaters()
        fade_all(self, 0.6)

        # the velocity graph: its slope is the acceleration
        ax = plain_axes([0, 4.6, 1], [0, 10, 2], 6.4, 4.6, ticks=True).move_to([-2.4, -0.3, 0])
        ax_l = VGroup(MathTex(r"t\ (\text{s})").scale(0.6).next_to(ax.x_axis.get_end(), DOWN, buff=0.15),
                      MathTex(r"v\ (\text{m/s})", color=VEL).scale(0.6).next_to(ax.y_axis.get_end(), LEFT, buff=0.15))
        nums = VGroup(*[MathTex(str(k)).scale(0.45).next_to(ax.c2p(k, 0), DOWN, buff=0.12) for k in range(1, 5)],
                      *[MathTex(str(k)).scale(0.45).next_to(ax.c2p(0, k), LEFT, buff=0.12) for k in (2, 4, 6, 8)])
        dots = VGroup(*[Dot(ax.c2p(k, 2 * k), color=VEL, radius=0.06) for k in range(5)])
        line = ax.plot(lambda x: 2 * x, x_range=[0, 4.5], color=VEL, stroke_width=4)
        run = Line(ax.c2p(2, 4), ax.c2p(3, 4), color=GREEN_C, stroke_width=4)
        rise = Line(ax.c2p(3, 4), ax.c2p(3, 6), color=ACC, stroke_width=4)
        rl = VGroup(MathTex(r"1\ \text{s}", color=GREEN_C).scale(0.55).next_to(run, DOWN, buff=0.1),
                    MathTex(r"2\ \text{m/s}", color=ACC).scale(0.55).next_to(rise, RIGHT, buff=0.1))
        note = VGroup(Tex(r"slope of the velocity graph", color=MUTED).scale(0.62),
                      MathTex(r"= \frac{dv}{dt} = a", color=ACC).scale(0.9)).arrange(DOWN, buff=0.25).move_to([3.8, 0.6, 0])
        with self.voice(
            "Plot the velocity against time, and the points fall on a straight line. Each second it climbs two, so its "
            "slope is the acceleration. It's the same idea as d y by d x in the last lesson: acceleration is d v by d t.",
            say="Plot the velocity against time, and the points fall on a straight line. Each second it climbs two, so "
                "its slope is the acceleration. It's the same idea as d y by d x in the last lesson: acceleration is "
                "d v by d t.",
        ) as v:
            self.play(Create(ax), FadeIn(ax_l), FadeIn(nums), run_time=1.0)
            self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.25), run_time=1.4)
            self.play(Create(line), run_time=1.0)
            self.play(Create(run), Create(rise), FadeIn(rl), run_time=1.0)
            self.play(Write(note), run_time=v.left(minimum=1.0))
        fade_all(self, 0.6)

        rows = VGroup(
            Tex(r"airliner: $250 \to 260$ m/s in $10$ s", r"\quad $a = 1$ m/s$^2$").scale(0.72),
            Tex(r"scooter: $0 \to 8$ m/s in $4$ s", r"\quad $a = 2$ m/s$^2$").scale(0.72),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to([0, 1.8, 0])
        for r in rows:
            r[1].set_color(ACC)
        with self.voice(
            "Compare an airliner gaining ten metres per second in ten seconds with our scooter. The airliner is enormously "
            "faster, but the scooter has twice the acceleration. Velocity and acceleration are different things.",
        ) as v:
            self.play(FadeIn(rows[0], shift=0.2 * RIGHT), run_time=1.0)
            self.play(FadeIn(rows[1], shift=0.2 * RIGHT), run_time=1.0)
            self.wait(v.left(frac=0.4))
            self.play(Indicate(rows[1][1], color=ACC), run_time=v.left(minimum=0.8))

        # braking: the acceleration points backwards
        k = 0.26
        road = Line([-6, -1.6, 0], [6, -1.6, 0], color=GROUND, stroke_width=3)
        tb = ValueTracker(0)
        pos = lambda: -5.4 + k * (20 * tb.get_value() - 2.5 * tb.get_value() ** 2)
        car = make_cart(BLUE_C, 0.8)
        car.add_updater(lambda m: m.next_to([pos(), -1.6, 0], UP, buff=0.02))
        va = always_redraw(lambda: arrow(car.get_top() + 0.3 * UP, [0.09 * (20 - 5 * tb.get_value()), 0, 0]))
        aa = always_redraw(lambda: arrow(car.get_bottom() + 0.45 * DOWN + 0.4 * RIGHT,
                                         [-0.9 if tb.get_value() < 3.99 else 0, 0, 0], ACC))
        legend = VGroup(Tex("velocity", color=VEL).scale(0.6), Tex("acceleration", color=ACC).scale(0.6)).arrange(RIGHT, buff=0.6)
        legend.move_to([3.6, -0.3, 0])
        brake = MathTex(r"20 \to 0\ \text{m/s in } 4\ \text{s}:\quad a = -5\ \text{m/s}^2").scale(0.75).move_to([0, -3.0, 0])
        with self.voice(
            "Slowing down is acceleration too. A car braking from twenty metres per second to rest in four seconds "
            "has an acceleration of minus five metres per second squared: the arrow points backwards, against the motion.",
            say="Slowing down is acceleration too. A car braking from twenty metres per second to rest in four seconds "
                "has an acceleration of minus five metres per second squared. Its arrow points backwards, against the motion.",
        ) as v:
            self.play(Create(road), FadeIn(car), FadeIn(legend), run_time=0.8)
            self.add(va, aa)
            self.play(tb.animate.set_value(4), run_time=4.0, rate_func=linear)
            self.play(Write(brake), run_time=v.left(minimum=1.0))
        extra = VGroup(Tex(r"Turning a corner at a steady speed is acceleration too.").scale(0.66),
                       Tex(r"Cruising straight at a steady $30$ m/s: $a = 0$, however fast.").scale(0.66)
                       ).arrange(DOWN, buff=0.3).move_to([0, 2.6, 0])
        with self.voice(
            "Anything that changes the velocity is an acceleration, including turning a corner at a steady speed. "
            "And zero acceleration doesn't mean standing still: a car cruising straight at thirty metres per second "
            "has no acceleration at all."
        ) as v:
            self.play(FadeOut(rows), run_time=0.4)
            self.play(FadeIn(extra[0]), run_time=1.0)
            self.wait(v.left(frac=0.45))
            self.play(FadeIn(extra[1]), run_time=v.left(minimum=0.8))
        car.clear_updaters()
        fade_all(self, 0.6)

        card = self.ponder_card(r"A tram speeds up from $8$ m/s to $14$ m/s in $3$ s.",
                                r"What is its acceleration?").move_to([0, 0.5, 0])
        with self.voice("Pause and try it. A tram speeds up from eight to fourteen metres per second in three seconds. "
                        "What is its acceleration?") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("lm4-tram")
        ans = MathTex(r"a = \frac{14 - 8}{3} = \frac{6\ \text{m/s}}{3\ \text{s}} = 2\ \text{m/s}^2").scale(0.95).move_to([0, -1.6, 0])
        with self.voice("It gains six metres per second in three seconds: two metres per second squared.") as v:
            self.play(Write(ans), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM05Inclines(Narrated, Scene):
    chapter_title = "Galileo's ramps"

    def construct(self):
        self.section_card(5, "Galileo's ramps")

        B = np.array([5.2, -2.6, 0])      # bottom of the ramp
        L = 10.0
        th = ValueTracker(14 * DEGREES)
        up_dir = lambda: np.array([-np.cos(th.get_value()), np.sin(th.get_value()), 0])
        top = lambda: B + min(L, 6.2 / max(np.sin(th.get_value()), 1e-3)) * up_dir()
        ramp = always_redraw(lambda: VGroup(
            Polygon(B, top(), [top()[0], B[1], 0], stroke_width=0, fill_color="#1B222B", fill_opacity=1),
            Line(top(), B, color=GREY_B, stroke_width=3)))
        floor = Line([-7, B[1], 0], [7, B[1], 0], color=GROUND, stroke_width=2)
        u = 1.12      # screen units per "unit" of distance down the ramp
        s = ValueTracker(0)
        r = 0.17
        normal = lambda: np.array([np.sin(th.get_value()), np.cos(th.get_value()), 0])
        ball_at = lambda d: top() - d * u * up_dir() + r * normal()
        ball = always_redraw(lambda: make_ball(BLUE_C, r).move_to(ball_at(0.5 * s.get_value() ** 2)))
        with self.voice(
            "Galileo wanted to study falling, but a dropped stone lands in a moment, and he had no stopwatch. "
            "So he slowed the fall down, by letting balls roll down gentle ramps."
        ) as v:
            self.play(Create(floor), FadeIn(ramp), run_time=1.2)
            self.play(FadeIn(ball), run_time=v.left(minimum=0.6))

        ghosts = VGroup()
        speeds = VGroup()
        with self.voice(
            "Mark where the ball is at the end of each second. It picks up the same amount of speed every second: "
            "its acceleration is constant."
        ) as v:
            step = v.left(minimum=4.0) / 4
            for sec in range(1, 5):
                self.play(s.animate.set_value(sec), run_time=step, rate_func=linear)
                g = make_ball(BLUE_C, r).set_opacity(0.35).move_to(ball_at(0.5 * sec ** 2))
                lab = MathTex(rf"v = {sec}", color=VEL).scale(0.5).next_to(g, UR, buff=0.08)
                ghosts.add(g)
                speeds.add(lab)
                self.add(g, lab)
        # distances from the start: 1, 4, 9, 16 (in units of the first second's distance)
        dist_labs = VGroup()
        for sec in range(1, 5):
            p = ball_at(0.5 * sec ** 2) - 2.6 * r * normal()
            dist_labs.add(MathTex(str(sec * sec), color=WHITE).scale(0.6).move_to(p))
        gap_labs = VGroup()
        for sec in range(1, 5):
            mid = ball_at(0.5 * ((sec - 1) ** 2 + sec ** 2) / 2) + 3.2 * r * normal()
            gap_labs.add(MathTex(str(2 * sec - 1), color=GREEN_C).scale(0.6).move_to(mid))
        key = VGroup(Tex(r"distance from the start: $1, 4, 9, 16$", color=WHITE).scale(0.62),
                     Tex(r"covered in each second: $1, 3, 5, 7$", color=GREEN_C).scale(0.62)).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        key.move_to([-3.3, 2.7, 0])
        with self.voice(
            "And the distances tell a story. Measured from the start they go one, four, nine, sixteen: the squares of "
            "the time. The stretch covered in each second grows like the odd numbers: one, three, five, seven."
        ) as v:
            self.play(FadeOut(speeds), run_time=0.4)
            self.play(FadeIn(key[0]), LaggedStart(*[FadeIn(d) for d in dist_labs], lag_ratio=0.3), run_time=2.0)
            self.wait(v.left(frac=0.4))
            self.play(FadeIn(key[1]), LaggedStart(*[FadeIn(d) for d in gap_labs], lag_ratio=0.3), run_time=v.left(minimum=1.5))
        self.play(FadeOut(ghosts), FadeOut(dist_labs), FadeOut(gap_labs), FadeOut(key), run_time=0.6)
        s.set_value(0)

        a_read = VGroup(MathTex(r"a =", color=ACC), DecimalNumber(0, num_decimal_places=1, color=ACC),
                        MathTex(r"\text{m/s}^2", color=ACC)).scale(0.9)
        a_read[1].set_value(9.8 * np.sin(th.get_value()))
        a_read.arrange(RIGHT, buff=0.15).move_to([-3.6, 2.6, 0])
        a_read[1].add_updater(lambda m: m.set_value(9.8 * np.sin(th.get_value())))
        ang_read = always_redraw(lambda: MathTex(rf"{np.degrees(th.get_value()):.0f}^\circ", color=MUTED).scale(0.6)
                                 .move_to(B + 1.1 * np.array([-np.cos(th.get_value() / 2), np.sin(th.get_value() / 2), 0])))
        with self.voice(
            "Tip the ramp up more steeply, and the acceleration grows. Stand it upright, and the ball simply falls, "
            "with the largest acceleration of all: g, about 9.8 metres per second squared.",
            say="Tip the ramp up more steeply, and the acceleration grows. Stand it upright, and the ball simply falls, "
                "with the largest acceleration of all: g, about nine point eight metres per second squared.",
        ) as v:
            self.play(FadeIn(a_read), FadeIn(ang_read), run_time=0.6)
            self.play(th.animate.set_value(45 * DEGREES), run_time=2.0)
            self.wait(0.6)
            self.play(th.animate.set_value(90 * DEGREES), run_time=v.left(minimum=2.0))
        same = Tex(r"the same $g$ for a heavy ball and a light one,\\as long as air resistance is negligible", color=MUTED).scale(0.62)
        same.move_to([-3.4, 1.4, 0])
        with self.voice(
            "Galileo's great discovery was that, when air resistance is small enough to ignore, it's the same g for "
            "everything: heavy or light, big or small."
        ) as v:
            self.play(FadeIn(same), run_time=v.left(minimum=1.0))
        fade_all(self, 0.6)

        card = self.ponder_card(r"A ball rolls from rest and covers $1$ unit in the first second.",
                                r"How far from the start is it after $3$ seconds?").move_to([0, 0.6, 0])
        with self.voice("Pause and ponder. A ball rolling from rest covers one unit in the first second. "
                        "How far from the start is it after three seconds?") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("lm5-ramp")
        ans = Tex(r"distance $\propto t^2$: \quad $3^2 = 9$ units \quad (and $5$ of them in the third second alone)").scale(0.7)
        ans.move_to([0, -1.6, 0])
        with self.voice("Distance grows as the square of the time: three squared is nine units. "
                        "Five of those come in the third second alone.") as v:
            self.play(Write(ans), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM06HowFast(Narrated, Scene):
    chapter_title = "Free fall: how fast"

    def construct(self):
        self.section_card(6, "Free fall: how fast")

        intro = VGroup(Tex(r"\textbf{free fall}: gravity is the only thing acting").scale(0.8),
                       MathTex(r"g \approx 9.8\ \text{m/s}^2 \approx 10\ \text{m/s}^2", color=ACC).scale(0.9)
                       ).arrange(DOWN, buff=0.35).move_to([0, 2.6, 0])
        with self.voice(
            "When gravity is the only thing acting on a body, with no air resistance worth mentioning, it is in free fall. "
            "Near the Earth it accelerates at g, about 9.8 metres per second squared. We'll round that to ten, "
            "to keep the arithmetic easy.",
            say="When gravity is the only thing acting on a body, with no air resistance worth mentioning, it is in free "
                "fall. Near the Earth it accelerates at g, about nine point eight metres per second squared. "
                "We'll round that to ten, to keep the arithmetic easy.",
        ) as v:
            self.play(Write(intro[0]), run_time=1.6)
            self.wait(v.left(frac=0.45))
            self.play(Write(intro[1]), run_time=v.left(minimum=1.0))
        self.play(intro.animate.scale(0.75).to_corner(UL, buff=0.4), run_time=0.6)

        # dropped from rest: snapshots every second
        top_y, k = 2.2, 0.068          # 80 m of fall in about 5.4 screen units
        x0 = -4.0
        t = ValueTracker(0)
        Y = lambda tt: top_y - k * 5 * tt ** 2
        ball = always_redraw(lambda: make_ball(BLUE_C, 0.15).move_to([x0, Y(t.get_value()), 0]))
        varr = always_redraw(lambda: arrow(np.array([x0 + 0.35, Y(t.get_value()), 0]), [0, -0.02 * 10 * t.get_value(), 0]))
        ruler = Line([x0 - 0.6, top_y, 0], [x0 - 0.6, Y(4), 0], color=GROUND, stroke_width=2)
        rticks = VGroup(*[Line([x0 - 0.7, Y(s), 0], [x0 - 0.5, Y(s), 0], color=GROUND, stroke_width=2) for s in range(5)])
        table = MathTable([["0", "1", "2", "3", "4"], ["0", "10", "20", "30", "40"]],
                          row_labels=[MathTex(r"t\ (\text{s})"), MathTex(r"v\ (\text{m/s})", color=VEL)],
                          include_outer_lines=False, h_buff=0.65, v_buff=0.35,
                          line_config={"stroke_width": 1, "color": MUTED}).scale(0.62).move_to([2.6, 1.0, 0])
        for c in range(2, 7):
            for r in (1, 2):
                table.get_entries((r, c)).set_opacity(0)
        with self.voice(
            "Drop a ball from rest. After one second it is falling at ten metres per second, after two seconds twenty, "
            "after three, thirty. It gains ten metres per second, every second."
        ) as v:
            self.play(FadeIn(ball), Create(ruler), FadeIn(rticks), run_time=0.8)
            self.add(varr)
            self.play(Create(table.get_horizontal_lines()), Create(table.get_vertical_lines()), FadeIn(table.get_row_labels()),
                      table.get_entries((1, 2)).animate.set_opacity(1), table.get_entries((2, 2)).animate.set_opacity(1), run_time=0.8)
            step = v.left(minimum=4.0) / 4
            for sec in range(1, 5):
                g_ = make_ball(BLUE_C, 0.15).set_opacity(0.3).move_to([x0, Y(sec - 1), 0])
                self.add(g_)
                self.play(t.animate.set_value(sec), table.get_entries((1, sec + 2)).animate.set_opacity(1),
                          table.get_entries((2, sec + 2)).animate.set_opacity(1), run_time=step, rate_func=lambda a: a)
        vgt = MathTex(r"v = g\,t", color=VEL).scale(1.2).next_to(table, DOWN, buff=0.6)
        with self.voice("Velocity acquired is acceleration times time: v equals g t.",
                        say="The velocity it has gained is acceleration multiplied by time. v equals g t.") as v:
            self.play(Write(vgt), run_time=v.left(minimum=1.0))
        fade_all(self, 0.6)

        # thrown straight up at 30 m/s
        base_y, kk = -2.9, 0.117
        T = ValueTracker(0)
        Yu = lambda tt: base_y + kk * (30 * tt - 5 * tt ** 2)
        Vu = lambda tt: 30 - 10 * tt
        xb = -4.3
        hand = Line([xb - 0.45, base_y - 0.22, 0], [xb + 0.45, base_y - 0.22, 0], color=GREY_B, stroke_width=6)
        ball = always_redraw(lambda: make_ball(BLUE_C, 0.15).move_to([xb, Yu(T.get_value()), 0]))
        varr = always_redraw(lambda: arrow(np.array([xb + 0.4, Yu(T.get_value()), 0]), [0, 0.025 * Vu(T.get_value()), 0]))
        aarr = always_redraw(lambda: arrow(np.array([xb - 0.45, Yu(T.get_value()) + 0.3, 0]), [0, -0.6, 0], ACC))
        legend = VGroup(Tex("velocity", color=VEL).scale(0.55), Tex(r"acceleration, $g$ downward", color=ACC).scale(0.55)
                        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT).move_to([-1.6, -3.3, 0])
        ax = plain_axes([0, 6.5, 1], [-35, 35, 10], 5.4, 4.6, ticks=True).move_to([2.6, -0.4, 0])
        ax_l = VGroup(MathTex(r"t\ (\text{s})").scale(0.55).next_to(ax.x_axis.get_end(), DOWN, buff=0.12),
                      MathTex(r"v\ (\text{m/s})", color=VEL).scale(0.55).next_to(ax.y_axis.get_end(), LEFT, buff=0.12))
        nums = VGroup(*[MathTex(str(k)).scale(0.42).next_to(ax.c2p(k, 0), DOWN, buff=0.1) for k in (1, 2, 3, 4, 5, 6)],
                      *[MathTex(str(k)).scale(0.42).next_to(ax.c2p(0, k), LEFT, buff=0.1) for k in (-30, -20, -10, 10, 20, 30)])
        trace = always_redraw(lambda: ax.plot(lambda x: 30 - 10 * x, x_range=[0, max(T.get_value(), 0.01)], color=VEL, stroke_width=4))
        vdot = always_redraw(lambda: Dot(ax.c2p(T.get_value(), Vu(T.get_value())), color=VEL, radius=0.06))
        rd = clock_readout(lambda: Vu(T.get_value()), label="v", unit="m/s", decimals=0, scale=0.7).move_to([2.6, 2.9, 0])
        tr = clock_readout(lambda: T.get_value(), scale=0.7).next_to(rd, LEFT, buff=0.8)
        with self.voice(
            "Now throw a ball straight up at thirty metres per second. Call up positive. On the way up, gravity takes "
            "away ten metres per second each second: thirty, twenty, ten..."
        ) as v:
            self.play(Create(hand), FadeIn(ball), FadeIn(legend), Create(ax), FadeIn(ax_l), FadeIn(nums), run_time=1.2)
            self.add(varr, aarr, trace, vdot, rd, tr)
            self.play(T.animate.set_value(2.6), run_time=v.left(minimum=2.5), rate_func=linear)
        with self.voice("...and at the very top, after three seconds, it stops for an instant.") as v:
            self.play(T.animate.set_value(3.0), run_time=v.left(minimum=1.0), rate_func=linear)

        card = self.ponder_card(r"At the very top of its flight, what are", r"the ball's velocity and acceleration?")
        card.move_to([3.4, -1.75, 0])
        keep_in_frame(card)
        with self.voice("Pause and ponder: at that very top point, what are the ball's velocity, and its acceleration?") as v:
            self.play(FadeIn(card, shift=0.2 * DOWN), run_time=0.8)
        self.checkpoint("lm6-top")
        with self.voice(
            "The velocity is zero for an instant, but it is still changing at ten metres per second every second. "
            "If the acceleration were zero up there too, the ball would just hang in the air."
        ) as v:
            self.play(FadeOut(card), run_time=0.4)
            self.play(Indicate(aarr, color=ACC, scale_factor=1.3), run_time=v.left(minimum=1.0))
        with self.voice(
            "Then it falls, gaining ten metres per second each second, and it's back in your hand after six seconds, "
            "moving at thirty metres per second, downwards. The velocity graph is one straight line, with slope minus ten "
            "the whole way."
        ) as v:
            self.play(T.animate.set_value(6.0), run_time=3.0, rate_func=linear)
            self.wait(v.left(minimum=0.5))
        self.wait(0.5)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM07HowFar(Narrated, Scene):
    chapter_title = "Free fall: how far"

    def construct(self):
        self.section_card(7, "Free fall: how far")

        ax = plain_axes([0, 4.4, 1], [0, 44, 10], 6.2, 4.8, ticks=True).move_to([-2.9, -0.5, 0])
        ax_l = VGroup(MathTex(r"t\ (\text{s})").scale(0.55).next_to(ax.x_axis.get_end(), DOWN, buff=0.12),
                      MathTex(r"v\ (\text{m/s})", color=VEL).scale(0.55).next_to(ax.y_axis.get_end(), LEFT, buff=0.12))
        nums = VGroup(*[MathTex(str(k)).scale(0.42).next_to(ax.c2p(k, 0), DOWN, buff=0.1) for k in (1, 2, 3, 4)],
                      *[MathTex(str(k)).scale(0.42).next_to(ax.c2p(0, k), LEFT, buff=0.1) for k in (10, 20, 30, 40)])
        vline = ax.plot(lambda x: 10 * x, x_range=[0, 4.2], color=VEL, stroke_width=4)
        q = VGroup(Tex(r"after $1$ s: \ moving at $10$ m/s").scale(0.7),
                   Tex(r"\ldots but fallen only $5$ m").scale(0.7)).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([3.6, 2.4, 0])
        with self.voice(
            "How far a falling body goes is a different question from how fast. After one second, a dropped ball is "
            "moving at ten metres per second, yet it has fallen only five metres. Why five, and not ten?"
        ) as v:
            self.play(Create(ax), FadeIn(ax_l), FadeIn(nums), Create(vline), run_time=1.4)
            self.play(FadeIn(q[0]), run_time=0.8)
            self.wait(v.left(frac=0.45))
            self.play(FadeIn(q[1]), run_time=v.left(minimum=0.8))

        avg = DashedLine(ax.c2p(0, 5), ax.c2p(1, 5), color=WHITE, stroke_width=2)
        avg_l = MathTex(r"\bar v = 5", color=WHITE).scale(0.55).next_to(avg, UP, buff=0.08).shift(0.2 * RIGHT)
        first = ax.get_area(ax.plot(lambda x: 10 * x, x_range=[0, 1]), x_range=[0, 1], color=BLUE_C, opacity=0.45)
        why = Tex(r"It started from rest, so its average speed\\over that second was only $\frac{0 + 10}{2} = 5$ m/s.").scale(0.65)
        why.move_to([3.6, 0.9, 0])
        with self.voice(
            "Because it wasn't doing ten for the whole second. It started from rest, so its average speed over that "
            "second was halfway between zero and ten: five metres per second, and five for one second is five metres."
        ) as v:
            self.play(Create(avg), FadeIn(avg_l), run_time=1.0)
            self.play(Write(why), run_time=2.0)
            self.play(FadeIn(first), run_time=v.left(minimum=1.0))

        steps = VGroup(
            MathTex(r"d = \bar v\, t"),
            MathTex(r"= \frac{0 + g t}{2}\, t"),
            MathTex(r"= \tfrac12 g t^2", color=BLUE_C),
        ).scale(0.85).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([3.6, -1.4, 0])
        with self.voice(
            "The same argument works for any time t. The average speed is half of g t, so the distance is half g t, "
            "times t: one half g t squared.",
            say="The same argument works for any time t. The average speed is half of g t, so the distance is half g t, "
                "times t. One half, g, t squared.",
        ) as v:
            for m in steps:
                self.play(Write(m), run_time=v.left(minimum=0.8) / 3 if m is not steps[-1] else v.left(minimum=0.8))
        self.play(FadeOut(q), FadeOut(why), FadeOut(avg), FadeOut(avg_l), FadeOut(first), run_time=0.5)

        T = ValueTracker(1)
        area = always_redraw(lambda: ax.get_area(ax.plot(lambda x: 10 * x, x_range=[0, T.get_value()]),
                                                 x_range=[0, T.get_value()], color=BLUE_C, opacity=0.45))
        d_read = clock_readout(lambda: 5 * T.get_value() ** 2, label="d", unit="m", decimals=0, scale=0.8).move_to([3.6, 2.6, 0])
        t_read = clock_readout(lambda: T.get_value(), scale=0.8).next_to(d_read, UP, buff=0.3)
        with self.voice(
            "Look at the graph again. The distance is the area of the triangle under the velocity line: half the base, "
            "t, times the height, g t. Let the time run on: five metres, twenty, forty-five, eighty.",
            say="Look at the graph again. The distance is the area of the triangle under the velocity line: half the base, "
                "t, times the height, g t. Let the time run on: five metres, twenty, forty five, eighty.",
        ) as v:
            self.play(steps.animate.shift(0.6 * DOWN), FadeIn(area), FadeIn(d_read), FadeIn(t_read), run_time=1.0)
            self.wait(v.left(frac=0.45))
            self.play(T.animate.set_value(4), run_time=v.left(minimum=2.5), rate_func=linear)
        note = Tex(r"how fast: $v \propto t$ \qquad how far: $d \propto t^2$", color=MUTED).scale(0.65).move_to([3.6, 1.6, 0])
        with self.voice("Speed grows in proportion to the time; distance grows with the square of the time.") as v:
            self.play(FadeIn(note), run_time=v.left(minimum=0.8))
        fade_all(self, 0.6)

        # the distance graph, and its slope
        ax2 = plain_axes([0, 4.4, 1], [0, 90, 20], 6.2, 5.0, ticks=True).move_to([-2.6, -0.4, 0])
        ax2_l = VGroup(MathTex(r"t\ (\text{s})").scale(0.55).next_to(ax2.x_axis.get_end(), DOWN, buff=0.12),
                       MathTex(r"d\ (\text{m})", color=BLUE_C).scale(0.55).next_to(ax2.y_axis.get_end(), LEFT, buff=0.12))
        nums2 = VGroup(*[MathTex(str(k)).scale(0.42).next_to(ax2.c2p(k, 0), DOWN, buff=0.1) for k in (1, 2, 3, 4)],
                       *[MathTex(str(k)).scale(0.42).next_to(ax2.c2p(0, k), LEFT, buff=0.1) for k in (20, 40, 60, 80)])
        f = lambda x: 5 * x * x
        df = lambda x: 10 * x
        par = ax2.plot(f, x_range=[0, 4.15], color=BLUE_C, stroke_width=4)
        tt = ValueTracker(0.6)
        tan = always_redraw(lambda: tangent_line(ax2, f, df, tt.get_value(), 2.4, color=VEL))
        dot = always_redraw(lambda: Dot(ax2.c2p(tt.get_value(), f(tt.get_value())), color=VEL, radius=0.07))
        sl = slope_readout(lambda: df(tt.get_value()), label=r"\text{slope} = \frac{dd}{dt}", decimals=0, scale=0.8)
        sl.move_to([3.5, 1.4, 0])
        sp = clock_readout(lambda: 10 * tt.get_value(), label="v = g t", unit="m/s", decimals=0, scale=0.8)
        sp.next_to(sl, DOWN, buff=0.5)
        with self.voice(
            "Plot the distance itself and you get a parabola. Run a tangent along it: its slope at each moment is "
            "exactly the speed, g t. The geometrical meaning of the derivative, once again.",
            say="Plot the distance itself, and you get a parabola. Run a tangent along it. Its slope at each moment is "
                "exactly the speed, g t. The geometrical meaning of the derivative, once again.",
        ) as v:
            self.play(Create(ax2), FadeIn(ax2_l), FadeIn(nums2), Create(par), run_time=1.6)
            self.add(tan, dot)
            self.play(FadeIn(sl), FadeIn(sp), run_time=0.6)
            self.play(tt.animate.set_value(3.8), run_time=v.left(minimum=2.5), rate_func=smooth)
        fade_all(self, 0.6)

        # air resistance: feather and hammer, on Earth and on the Moon
        def column(cx, title, g, drag):
            ground = Line([cx - 1.6, -2.8, 0], [cx + 1.6, -2.8, 0], color=GROUND, stroke_width=3)
            head = Tex(title).scale(0.7).move_to([cx, 3.2, 0])
            return ground, head
        g1, h1 = column(-3.3, "Earth, in air", 9.8, True)
        g2, h2 = column(3.3, "Moon, no air", 1.6, False)
        tm = ValueTracker(0)
        H = 5.4    # screen drop, standing for about 1.6 m
        def fall(tt, g):
            return min(H, 0.5 * g * tt * tt * H / 1.6)
        def hammer(cx, g):
            y = 2.5 - fall(tm.get_value(), g)
            return VGroup(Rectangle(width=0.5, height=0.16, stroke_width=0, fill_color=GREY_B, fill_opacity=1).move_to([cx - 0.5, y + 0.2, 0]),
                          Rectangle(width=0.08, height=0.55, stroke_width=0, fill_color="#8B6A4A", fill_opacity=1).move_to([cx - 0.5, y - 0.15, 0]))
        def feather(cx, y):
            return VGroup(Ellipse(width=0.22, height=0.62, stroke_width=0, fill_color=GREY_A, fill_opacity=0.9).move_to([cx + 0.5, y, 0]),
                          Line([cx + 0.5, y - 0.36, 0], [cx + 0.5, y + 0.3, 0], color=GREY_D, stroke_width=1.5))
        e_ham = always_redraw(lambda: hammer(-3.3, 9.8))
        e_fea = always_redraw(lambda: feather(-3.3, 2.5 - min(H - 0.05, 0.55 * tm.get_value() * H / 1.6)
                                              + 0.08 * np.sin(6 * tm.get_value())))
        m_ham = always_redraw(lambda: hammer(3.3, 1.6))
        m_fea = always_redraw(lambda: feather(3.3, 2.5 - fall(tm.get_value(), 1.6)))
        with self.voice(
            "Air spoils the picture for light, broad things. On Earth a feather drifts down long after a hammer has landed. "
            "But in 1971, on the airless Moon, Apollo 15 astronaut David Scott dropped a hammer and a falcon feather "
            "together, and they reached the ground at the same moment."
        ) as v:
            self.play(Create(g1), Create(g2), FadeIn(h1), FadeIn(h2), FadeIn(e_ham), FadeIn(e_fea), FadeIn(m_ham), FadeIn(m_fea), run_time=1.0)
            self.wait(v.left(frac=0.25))
            self.play(tm.animate.set_value(1.45), run_time=v.left(minimum=3.0), rate_func=linear)
        fade_all(self, 0.6)

        card = self.ponder_card(r"A stone dropped into a well hits the water $3$ s later.",
                                r"How deep is the well? \ (Use $g = 10$ m/s$^2$.)").move_to([0, 0.6, 0])
        with self.voice("Pause and try one. A stone dropped into a well hits the water three seconds later. "
                        "How deep is the well? Use g equals ten.") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("lm7-well")
        ans = MathTex(r"d = \tfrac12 \cdot 10 \cdot 3^2 = 45\ \text{m}", r"\qquad v = 10 \cdot 3 = 30\ \text{m/s}").scale(0.9).move_to([0, -1.6, 0])
        ans[1].set_color(MUTED)
        with self.voice("One half times ten times three squared: forty-five metres. It hits the water at thirty metres per second.",
                        say="One half, times ten, times three squared: forty five metres. And it hits the water at "
                            "thirty metres per second.") as v:
            self.play(Write(ans), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM08Reaction(Narrated, Scene):
    chapter_title = "Catch the ruler"

    def construct(self):
        self.section_card(8, "Catch the ruler")

        cm = 0.15                       # screen units per centimetre
        y_f = -0.6                      # height of the catching fingers
        drop = ValueTracker(0)          # centimetres fallen
        def ruler():
            y0 = y_f - drop.get_value() * cm          # the ruler's 0 cm end starts between the fingers
            body = Rectangle(width=0.75, height=31 * cm, stroke_color=GREY_B, stroke_width=1.5,
                             fill_color="#E9D9A6", fill_opacity=1).move_to([-3.0, y0 + 15 * cm, 0])
            ticks = VGroup()
            for c in range(0, 31):
                y = y0 + c * cm
                w = 0.28 if c % 5 == 0 else 0.15
                ticks.add(Line([-3.375, y, 0], [-3.375 + w, y, 0], color="#3A2E12", stroke_width=1.5))
                if c % 5 == 0:
                    ticks.add(MathTex(str(c), color="#3A2E12").scale(0.36).move_to([-2.95, y, 0]))
            return VGroup(body, ticks)
        r = always_redraw(ruler)
        pinch = ValueTracker(0.0)
        fingers = always_redraw(lambda: VGroup(
            RoundedRectangle(corner_radius=0.12, width=0.9, height=0.3, stroke_width=0, fill_color="#C99A7C", fill_opacity=1)
            .move_to([-3.0 - 0.95 + 0.42 * pinch.get_value(), y_f, 0]),
            RoundedRectangle(corner_radius=0.12, width=0.9, height=0.3, stroke_width=0, fill_color="#C99A7C", fill_opacity=1)
            .move_to([-3.0 + 0.95 - 0.42 * pinch.get_value(), y_f, 0])))
        with self.voice(
            "Here's a use for the free-fall formula you can try with a friend. They hold a ruler with its zero mark "
            "between your open fingers, and let go without warning. You catch it as fast as you can."
        ) as v:
            self.play(FadeIn(r), FadeIn(fingers), run_time=1.0)
            self.wait(v.left(minimum=0.5))
        with self.voice("The ruler falls freely until your hand reacts. Say it drops twenty centimetres before you catch it.") as v:
            self.play(drop.animate.set_value(20), run_time=1.2, rate_func=lambda a: a * a)
            self.play(pinch.animate.set_value(1), run_time=0.25)
            mark = VGroup(Line([-2.4, y_f, 0], [-1.8, y_f, 0], color=VEL, stroke_width=3),
                          Tex(r"$20$ cm", color=VEL).scale(0.65).move_to([-1.3, y_f, 0]))
            self.play(FadeIn(mark), run_time=v.left(minimum=0.6))

        work = VGroup(
            MathTex(r"d = \tfrac12 g t^2"),
            MathTex(r"t = \sqrt{\frac{2d}{g}}", color=VEL),
            MathTex(r"= \sqrt{\frac{2 \times 0.20\ \text{m}}{9.8\ \text{m/s}^2}} \approx 0.20\ \text{s}"),
        ).scale(0.85).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([2.6, 1.2, 0])
        with self.voice(
            "Turn d equals one half g t squared around to get the time: t is the square root of two d over g. "
            "For twenty centimetres that's about two tenths of a second: your reaction time.",
            say="Turn, d equals one half g t squared, around, to get the time. t is the square root of two d over g. "
                "For twenty centimetres, that's about two tenths of a second: your reaction time.",
        ) as v:
            for m in work:
                self.play(Write(m), run_time=v.left(minimum=0.8) / 3 if m is not work[-1] else v.left(minimum=0.8))

        scale_marks = VGroup()
        for tt in (0.10, 0.15, 0.20, 0.24):
            d_cm = 0.5 * 9.8 * tt * tt * 100
            y = y_f + (d_cm - 20) * cm               # where that mark sits on the caught ruler
            scale_marks.add(VGroup(Line([-2.62, y, 0], [-2.35, y, 0], color=ACC, stroke_width=3),
                                   MathTex(rf"{tt:.2f}\,\text{{s}}", color=ACC).scale(0.45).next_to([-2.35, y, 0], RIGHT, buff=0.08)))
        cal = Tex(r"print reaction times on the ruler:\\the marks spread out further along", color=MUTED).scale(0.6).move_to([2.6, -2.4, 0])
        with self.voice(
            "You could even print reaction times straight onto the ruler. Because distance grows with the square of the "
            "time, the marks spread further apart the further along the ruler they go."
        ) as v:
            self.play(FadeOut(mark), run_time=0.3)
            self.play(LaggedStart(*[FadeIn(m) for m in scale_marks], lag_ratio=0.3), FadeIn(cal), run_time=v.left(minimum=1.5))
        fade_all(self, 0.6)

        card = self.ponder_card(r"Someone catches a falling metre stick after it", r"has dropped $45$ cm. What was their reaction time?",
                                r"(Use $g = 10$ m/s$^2$.)").move_to([0, 0.6, 0])
        with self.voice("Pause and try it. Someone catches a falling metre stick after it has dropped forty-five centimetres. "
                        "What was their reaction time? Use g equals ten.",
                        say="Pause and try it. Someone catches a falling metre stick after it has dropped forty five "
                            "centimetres. What was their reaction time? Use g equals ten.") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("lm8-ruler")
        ans = MathTex(r"t = \sqrt{\frac{2 \times 0.45}{10}} = \sqrt{0.09} = 0.3\ \text{s}").scale(0.95).move_to([0, -1.7, 0])
        tryit = Tex(r"Try it yourself below the video: there's a ruler to catch.", color=VEL).scale(0.7).move_to([0, -3.0, 0])
        with self.voice("The square root of two times 0.45 over ten is the square root of 0.09: three tenths of a second, "
                        "a little slow. Try it yourself below the video: there's a ruler you can catch.",
                        say="The square root of, two times zero point four five, over ten, is the square root of zero point "
                            "zero nine: three tenths of a second. A little slow. Try it yourself below the video: "
                            "there's a ruler you can catch.") as v:
            self.play(Write(ans), run_time=2.0)
            self.wait(v.left(frac=0.4))
            self.play(FadeIn(tryit), run_time=v.left(minimum=0.8))
        self.wait(0.6)
        fade_all(self)


# ════════════════════════════════════════════════════════════════════════
class LM09Recap(Narrated, Scene):
    chapter_title = "Recap"

    def construct(self):
        self.section_card(9, "Recap")
        items = [
            (r"Speed $=$ distance $\div$ time. Average speed is for the whole trip.",
             "Speed is distance divided by time; average speed describes the whole trip."),
            (r"Every speed is measured relative to something.",
             "Every speed is measured relative to something."),
            (r"Velocity is speed with a direction.",
             "Velocity is speed with a direction."),
            (r"Acceleration $=$ change in velocity $\div$ time, in m/s$^2$.",
             "Acceleration is the change in velocity divided by the time, in metres per second squared."),
            (r"Free fall: $a = g \approx 10$ m/s$^2$, \ $v = gt$, \ $d = \tfrac12 g t^2$.",
             "In free fall the acceleration is g, about ten; v equals g t, and d equals one half g t squared."),
            (r"Slope of the distance graph is $v$; slope of the velocity graph is $a$;\\area under the velocity graph is the distance.",
             "The slope of the distance graph is the velocity, the slope of the velocity graph is the acceleration, "
             "and the area under the velocity graph is the distance."),
        ]
        rows = VGroup(*[Tex(t).scale(0.62) for t, _ in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        rows.to_edge(LEFT, buff=0.8).shift(0.15 * DOWN)
        bullets = VGroup(*[Dot(radius=0.05, color=POINT).next_to(r[0][0], LEFT, buff=0.22) for r in rows])
        for (tex, spoken), row, bul in zip(items, rows, bullets):
            with self.voice(tex.replace(r"\\", " "), say=spoken) as v:
                self.play(FadeIn(bul), FadeIn(row, shift=0.15 * RIGHT), run_time=v.left(minimum=1.0))
        nxt = Tex(r"Now try the exercises, the motion lab and the ruler below the video.", color=POINT).scale(0.72).to_edge(DOWN, buff=0.4)
        with self.voice("That's linear motion. Below the video you'll find exercises, a motion lab, and a ruler to catch.") as v:
            self.play(Write(nxt), run_time=v.left(minimum=1.0))
        self.wait(1.5)
        fade_all(self, 1.0)
