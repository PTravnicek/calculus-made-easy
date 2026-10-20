"""Calculus Made Easy, Chapter X: Geometrical Meaning of Differentiation.

One Scene per part of the interactive video. Render one with
    ../../.venv/bin/manim -ql scenes.py Ch01Tangent
or all of them, for the web player, with lessonkit/build.py chapter10.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lessonkit"))
from narration import *  # noqa: E402


# ════════════════════════════════════════════════════════════════════════
class Ch01Tangent(Narrated, MovingCameraScene):
    chapter_title = "The slope at a point"

    def construct(self):
        self.opening()

        f = lambda x: 0.25 + 0.13 * x**2
        df = lambda x: 0.26 * x
        ax = plain_axes([0, 7], [0, 5.5], 8.4, 6.0).to_edge(LEFT, buff=0.6).shift(0.2 * DOWN)
        letters = axes_letters(ax)
        curve = ax.plot(f, x_range=[0.6, 6.1], color=CURVE, stroke_width=4)
        P = MathTex("P").scale(0.85).next_to(ax.c2p(1.0, f(1.0)), UL, buff=0.1)
        R = MathTex("R").scale(0.85).next_to(ax.c2p(5.8, f(5.8)), LEFT, buff=0.2)

        xq = ValueTracker(2.6)   # abscissa of Q
        h = ValueTracker(2.2)    # dx
        ext = ValueTracker(1.0)  # how far the line QT is produced beyond Q and T
        dot_r = ValueTracker(0.08)
        sw = ValueTracker(1.0)   # stroke-width multiplier, so lines stay thin while zoomed in

        X = lambda: xq.get_value()
        Qp = lambda: ax.c2p(X(), f(X()))
        Tp = lambda: ax.c2p(X() + h.get_value(), f(X() + h.get_value()))
        corner = lambda: ax.c2p(X() + h.get_value(), f(X()))

        dot_q = always_redraw(lambda: Dot(Qp(), radius=dot_r.get_value(), color=POINT))
        dot_t = always_redraw(lambda: Dot(Tp(), radius=dot_r.get_value(), color=POINT))
        lab_q = MathTex("Q").scale(0.85).add_updater(lambda m: m.next_to(Qp(), UL, buff=0.08))
        lab_t = MathTex("T").scale(0.85).add_updater(lambda m: m.next_to(Tp(), UL, buff=0.08))

        def chord():
            p, q = Qp(), Tp()
            if h.get_value() < 1e-3:
                d = ax.c2p(X() + 1, f(X()) + df(X())) - p
            else:
                d = q - p
            d = d / np.linalg.norm(d)
            return Line(p - d * ext.get_value(), q + d * ext.get_value(), color=TANGENT,
                        stroke_width=3 * sw.get_value())

        dx_line = always_redraw(lambda: Line(Qp(), corner(), color=DX_C, stroke_width=4 * sw.get_value()))
        dy_line = always_redraw(lambda: Line(corner(), Tp(), color=DY_C, stroke_width=4 * sw.get_value()))
        dx_lab = MathTex("dx", color=DX_C).scale(0.8).add_updater(lambda m: m.next_to(dx_line, DOWN, buff=0.12))
        dy_lab = MathTex("dy", color=DY_C).scale(0.8).add_updater(lambda m: m.next_to(dy_line, RIGHT, buff=0.12))

        # ── the curve PQR ──
        with self.voice(
            "Any function of $x$, such as $x^2$, or $\\sqrt{x}$, or $ax+b$, can be plotted as a curve. "
            "Here is a piece of one, $PQR$, drawn on the axes $OX$ and $OY$.",
            say="Any function of x, such as x squared, or the square root of x, or a x plus b, can be plotted "
                "as a curve. Here is a piece of one, P Q R, drawn on the axes O X, and O Y.",
        ) as v:
            self.play(Create(ax), FadeIn(letters), run_time=1.5)
            self.play(Create(curve), run_time=v.left(frac=0.6))
            self.play(FadeIn(P), FadeIn(R), run_time=0.6)

        foot = ax.c2p(2.6, 0)
        v_dash = DashedLine(foot, Qp(), color=MUTED, stroke_width=2)
        h_dash = DashedLine(ax.c2p(0, f(2.6)), Qp(), color=MUTED, stroke_width=2)
        x_brace = BraceBetweenPoints(ax.c2p(0, 0), foot, DOWN, buff=0.05)
        x_txt = MathTex("x").scale(0.85).next_to(x_brace, DOWN, buff=0.08)
        y_brace = BraceBetweenPoints(foot, Qp(), RIGHT, buff=0.05)
        y_txt = MathTex("y").scale(0.85).next_to(y_brace, RIGHT, buff=0.08)
        with self.voice("Take any point $Q$ on the curve. Its abscissa is $x$, and its ordinate is $y$.") as v:
            self.play(GrowFromCenter(dot_q), FadeIn(lab_q), run_time=0.8)
            self.play(Create(v_dash), Create(h_dash), run_time=0.8)
            self.play(GrowFromCenter(x_brace), FadeIn(x_txt), GrowFromCenter(y_brace), FadeIn(y_txt),
                      run_time=v.left(frac=0.7))

        # ── dx and dy ──
        with self.voice(
            "Now let $x$ grow by a small step $dx$ to the right. On this ascending curve, $y$ grows too, "
            "by a small step $dy$, and we arrive at a neighbouring point $T$."
        ) as v:
            self.play(FadeOut(x_brace, x_txt, y_brace, y_txt, h_dash, v_dash), run_time=0.5)
            self.play(Create(dx_line), FadeIn(dx_lab), run_time=1.4)
            self.wait(0.6)
            self.play(Create(dy_line), FadeIn(dy_lab), run_time=1.4)
            self.play(GrowFromCenter(dot_t), FadeIn(lab_t), run_time=v.left(frac=0.5))

        ratio = MathTex(r"\text{slope of } QT", "=", r"\frac{dy}{dx}").scale(0.95)
        ratio.move_to([4.6, 2.4, 0])
        ratio[2][0][0:2].set_color(DY_C)
        ratio[2][0][3:5].set_color(DX_C)
        with self.voice("The ratio of $dy$ to $dx$ measures how steeply the curve climbs between $Q$ and $T$.") as v:
            line_qt = chord()
            self.play(Create(line_qt), run_time=1.2)
            self.play(Write(ratio), run_time=v.left(frac=0.8))
        self.remove(line_qt)
        secant = always_redraw(chord)
        self.add(secant)

        arc = ax.plot(f, x_range=[2.6, 4.8], color=WHITE, stroke_width=7)
        ticks = VGroup(*[tangent_line(ax, f, df, x, 1.1, color=PURPLE_B, stroke_width=4) for x in (2.95, 3.7, 4.45)])
        with self.voice(
            "But look closely. Between $Q$ and $T$ the curve keeps bending, so it has many different slopes. "
            "We can't really speak of the slope between $Q$ and $T$."
        ) as v:
            self.play(Create(arc), run_time=1.0)
            self.play(LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.5), run_time=2.4)
            self.wait(v.left(frac=0.6))
            self.play(FadeOut(arc), FadeOut(ticks), run_time=0.6)

        # ── shrink dx ──
        with self.voice(
            "So bring $T$ closer. Make $dx$ smaller, and smaller. As $T$ slides toward $Q$, "
            "the little piece of curve $QT$ becomes practically straight."
        ) as v:
            self.play(h.animate.set_value(1.0), run_time=2.0)
            self.play(FadeOut(dx_lab), FadeOut(dy_lab), FadeOut(lab_t), run_time=0.4)
            self.play(h.animate.set_value(0.25), run_time=v.left(frac=0.8))

        frame = self.camera.frame
        with self.voice(
            "Zoom in on $Q$ and you see it plainly: magnified enough, a smooth curve looks like a straight line, "
            "and the line through $Q$ and $T$ hugs it."
        ) as v:
            self.play(FadeOut(lab_q), FadeOut(ratio), run_time=0.4)
            frame.save_state()
            self.play(frame.animate.scale(0.11).move_to(ax.c2p(2.72, f(2.72))),
                      dot_r.animate.set_value(0.008), sw.animate.set_value(0.11),
                      curve.animate.set_stroke(width=4 * 0.11), run_time=3.0)
            self.play(h.animate.set_value(0.05), run_time=v.left(frac=0.7))
            self.wait(0.4)

        with self.voice(
            "In the limit, the straight line touches the curve at practically one point only. "
            "It is the tangent to the curve at $Q$."
        ) as v:
            self.play(Restore(frame), dot_r.animate.set_value(0.08), sw.animate.set_value(1.0),
                      curve.animate.set_stroke(width=4), run_time=2.5)
            self.remove(dx_line, dy_line, dot_t)
            h.set_value(0)
            self.play(ext.animate.set_value(2.6), FadeIn(lab_q), run_time=v.left(frac=0.8))

        meaning = VGroup(
            MathTex(r"\frac{dy}{dx}").scale(1.3),
            Tex(r"is the slope of the\\tangent to the curve\\at the point $Q$.").scale(0.85),
        ).arrange(DOWN, buff=0.3).move_to([4.6, 1.6, 0])
        meaning[0][0][0:2].set_color(DY_C)
        meaning[0][0][3:5].set_color(DX_C)
        box = SurroundingRectangle(meaning, color=TANGENT, buff=0.3, corner_radius=0.15)
        with self.voice(
            "And that is the geometrical meaning we were after: $\\frac{dy}{dx}$ is the slope of the tangent "
            "to the curve at the point $Q$."
        ) as v:
            self.play(Write(meaning), run_time=2.0)
            self.play(Create(box), run_time=v.left(frac=0.6))

        readout = slope_readout(lambda: df(X()), scale=0.95).move_to([4.6, -1.6, 0])
        with self.voice(
            "The slope of a curve, on its own, means little, since every small portion of a curve has a different slope. "
            "But the slope at a point is perfectly defined. Move $Q$, and $\\frac{dy}{dx}$ moves with it."
        ) as v:
            self.play(FadeIn(readout), run_time=0.6)
            self.wait(v.left(frac=0.45))
            self.play(xq.animate.set_value(1.1), run_time=2.2)
            self.play(xq.animate.set_value(5.4), run_time=3.5)
            self.play(xq.animate.set_value(2.6), run_time=v.left(minimum=1.5))

        with self.voice(
            "One last thing. In diagrams, $dx$ and $dy$ must be drawn big enough to see. "
            "In thought, they are as short as you please: indefinitely short."
        ) as v:
            h.set_value(1.2)
            ext.set_value(1.0)
            self.play(FadeIn(dx_line), FadeIn(dy_line), FadeIn(dot_t), FadeIn(dx_lab), FadeIn(dy_lab), run_time=1.0)
            self.wait(v.left(frac=0.45))
            self.play(FadeOut(dx_lab), FadeOut(dy_lab), run_time=0.4)
            self.play(h.animate.set_value(0.02), run_time=v.left(minimum=1.5))
        self.wait(0.5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

    def opening(self):
        book = Tex(r"\textit{Calculus Made Easy}", color=MUTED).scale(0.85)
        chap = Tex(r"Chapter X", color=POINT).scale(0.95)
        title = Tex(r"Geometrical Meaning\\of Differentiation").scale(1.6)
        after = Tex(r"after Silvanus P.\ Thompson, 1914", color=MUTED).scale(0.6)
        g = VGroup(book, chap, title, after).arrange(DOWN, buff=0.4)
        with self.voice(
            "Chapter ten of Calculus Made Easy asks a simple question: what does the differential coefficient, "
            "$\\frac{dy}{dx}$, actually look like?"
        ) as v:
            self.play(FadeIn(book, shift=0.2 * DOWN), FadeIn(chap), run_time=1.2)
            self.play(Write(title), run_time=2.2)
            self.play(FadeIn(after), run_time=0.8)
            self.wait(v.left(minimum=0.2))
        self.play(FadeOut(g, shift=0.3 * UP), run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch02ReadingSlopes(Narrated, Scene):
    chapter_title = "Reading the slope"

    def construct(self):
        self.section_card(2, "Reading the slope")

        plane = NumberPlane(
            x_range=[-8, 8, 1], y_range=[-5, 5, 1],
            background_line_style={"stroke_color": BLUE_E, "stroke_opacity": 0.45, "stroke_width": 1},
            axis_config={"stroke_opacity": 0},
        )
        pivot = np.array([-4.0, -1.0, 0])
        L = 2.0
        th = ValueTracker(np.arctan(0.5))
        m = lambda: np.tan(th.get_value())

        def the_line():
            u = np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0])
            run = L / np.cos(th.get_value())
            return Line(pivot - 1.6 * u, pivot + (run + 1.4) * u, color=CURVE, stroke_width=5)

        def dy_line():
            a, b = pivot + L * RIGHT, pivot + L * RIGHT + L * m() * UP
            if abs(L * m()) < 1e-3:
                return VMobject()
            return Line(a, b, color=DY_C, stroke_width=5)

        line = always_redraw(the_line)
        dx = Line(pivot, pivot + L * RIGHT, color=DX_C, stroke_width=5)
        dy = always_redraw(dy_line)
        dx_lab = MathTex("dx", color=DX_C).scale(0.85).add_updater(
            lambda o: o.next_to(dx, UP if th.get_value() < -0.01 else DOWN, buff=0.12))
        dy_lab = MathTex("dy", color=DY_C).scale(0.85).add_updater(
            lambda o: o.next_to(pivot + L * RIGHT + 0.5 * L * m() * UP, RIGHT, buff=0.15).set_opacity(
                min(1.0, abs(L * m()) / 0.4)))
        dot = Dot(pivot, color=POINT, radius=0.07)
        angle = always_redraw(lambda: Arc(
            radius=0.75, start_angle=0, angle=th.get_value(), arc_center=pivot, color=WHITE, stroke_width=2)
            if abs(th.get_value()) > 0.01 else VMobject())
        deg = DecimalNumber(np.degrees(th.get_value()), num_decimal_places=0, unit=r"^\circ").scale(0.65)
        deg.add_updater(lambda o: o.set_value(np.degrees(th.get_value())))
        deg.add_updater(lambda o: o.move_to(pivot + 1.15 * np.array(
            [np.cos(th.get_value() / 2), np.sin(th.get_value() / 2), 0]) + 0.25 * RIGHT).set_opacity(
                min(1.0, abs(th.get_value()) / 0.15)))

        readout = slope_readout(m, scale=1.15).move_to([3.6, 1.6, 0])
        verdict = Tex("").move_to([3.6, 0.2, 0])

        def set_verdict(tex, color=WHITE):
            new = Tex(tex, color=color).scale(0.9).move_to([3.6, 0.3, 0])
            return Transform(verdict, new)

        def blank_verdict():
            return verdict.animate.set_opacity(0)

        with self.voice(
            "From here on, read $\\frac{dy}{dx}$ as steepness. Take $dx$ as a short step to the right; "
            "$dy$ is how far you must climb to stay on the line."
        ) as v:
            self.play(FadeIn(plane), run_time=0.8)
            self.play(Create(line), FadeIn(dot), run_time=1.2)
            self.play(Create(dx), FadeIn(dx_lab), run_time=1.0)
            self.play(Create(dy), FadeIn(dy_lab), Create(angle), FadeIn(deg), run_time=1.0)
            self.play(FadeIn(readout), run_time=v.left(frac=0.5))
        self.add(verdict)

        steps = [
            (np.pi / 4, "If the line rises at $45°$, $dy$ and $dx$ are equal, so $\\frac{dy}{dx} = 1$.",
             r"rising at $45^\circ$:\quad $\frac{dy}{dx} = 1$", WHITE),
            (np.arctan(1.8), "Make it steeper than $45°$ and $dy$ outgrows $dx$: $\\frac{dy}{dx}$ is greater than $1$.",
             r"steeper than $45^\circ$:\quad $\frac{dy}{dx} > 1$", WHITE),
            (np.arctan(0.3), "Let it rise only gently, and $dy$ is the smaller step: $\\frac{dy}{dx}$ is a fraction, less than $1$.",
             r"gentle:\quad $0 < \frac{dy}{dx} < 1$", WHITE),
            (0.0, "Where the line is horizontal, $dy$ is zero, so $\\frac{dy}{dx}$ is zero too.",
             r"level:\quad $\frac{dy}{dx} = 0$", WHITE),
        ]
        for angle_to, text, tex, col in steps:
            with self.voice(text) as v:
                self.play(th.animate.set_value(angle_to), blank_verdict(), run_time=2.0)
                self.play(set_verdict(tex, col), run_time=v.left(minimum=0.6, frac=0.4))

        card = self.ponder_card(r"The line now slopes \emph{downward} at $45^\circ$.",
                                r"What is $\dfrac{dy}{dx}$?").to_edge(UP, buff=0.4).shift(3.3 * RIGHT)
        with self.voice(
            "Pause and ponder. Suppose the line slopes downward, at forty-five degrees. What is $\\frac{dy}{dx}$ now?"
        ) as v:
            self.play(FadeOut(readout), FadeOut(verdict), FadeIn(card, shift=0.2 * DOWN), run_time=1.0)
        self.checkpoint("ch2-down45")

        with self.voice(
            "Going downhill, $dy$ is a step down, so it counts as negative. At $45°$ down, $dy = -dx$, "
            "and $\\frac{dy}{dx} = -1$.",
            say="Going downhill, d y is a step down, so it counts as negative. At 45 degrees down, "
                "d y equals minus d x, and d y by d x equals minus 1.",
        ) as v:
            self.play(FadeOut(card), FadeIn(readout), run_time=0.6)
            self.play(th.animate.set_value(-np.pi / 4), run_time=2.4)
            self.play(set_verdict(r"falling:\quad $\frac{dy}{dx} < 0$"), run_time=v.left(frac=0.5))
        self.wait(0.6)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)

        # ── three shapes: Figures 12, 13, 14 ──
        shapes = [
            ("a straight line", lambda x: 0.6 + 0.55 * x, lambda x: 0.55 * 1),
            ("turning upward", lambda x: 0.2 + 0.17 * x**2, lambda x: 0.34 * x),
            ("getting flatter", lambda x: 2.9 * (1 - np.exp(-x / 1.1)), lambda x: 2.9 / 1.1 * np.exp(-x / 1.1)),
        ]
        panels, trackers, groups = [], [], []
        for i, (name, f, df) in enumerate(shapes):
            ax = plain_axes([0, 4.2], [0, 3.4], 3.6, 2.9)
            g = ax.plot(f, x_range=[0.05, 4.0], color=CURVE, stroke_width=4)
            t = ValueTracker(0.35)
            dot = always_redraw(lambda ax=ax, f=f, t=t: Dot(ax.c2p(t.get_value(), f(t.get_value())), color=POINT, radius=0.06))
            tan = always_redraw(lambda ax=ax, f=f, df=df, t=t: tangent_line(ax, f, df, t.get_value(), 1.6))
            head = Tex(name).scale(0.75).next_to(ax, UP, buff=0.3)
            rd = slope_readout(lambda df=df, t=t: df(t.get_value()), scale=0.8).next_to(ax, DOWN, buff=0.45)
            grp = VGroup(head, ax, g, rd)
            panels.append((ax, g, dot, tan, head, rd))
            trackers.append(t)
            groups.append(grp)
        row = VGroup(*groups).arrange(RIGHT, buff=0.9)
        # re-anchor the readouts after arranging
        for (ax, g, dot, tan, head, rd) in panels:
            rd[0].next_to(ax, DOWN, buff=0.45).shift(0.5 * LEFT)

        texts = [
            "If the curve is a straight line, its slope is the same at every point. Slide along it: the reading never changes.",
            "If the curve turns more and more upward as it goes to the right, $\\frac{dy}{dx}$ grows with the increasing steepness.",
            "And if it gets flatter and flatter, $\\frac{dy}{dx}$ grows smaller and smaller as the flatter part is reached.",
        ]
        for i, text in enumerate(texts):
            ax, g, dot, tan, head, rd = panels[i]
            with self.voice(text) as v:
                self.play(FadeIn(head), Create(ax), run_time=0.7)
                self.play(Create(g), FadeIn(dot), FadeIn(tan), FadeIn(rd), run_time=1.0)
                self.play(trackers[i].animate.set_value(3.8), run_time=v.left(minimum=2.0, frac=0.9), rate_func=linear)
        self.wait(0.8)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch03MaxMin(Narrated, Scene):
    chapter_title = "Summits and troughs"

    def construct(self):
        self.section_card(3, "Summits and troughs")

        f = lambda x: x**3 / 3 - 2 * x**2 + 3 * x + 1
        df = lambda x: x**2 - 4 * x + 3
        ax = plain_axes([-1, 5, 1], [-2, 5, 1], 7.6, 5.8, ticks=True).to_edge(LEFT, buff=0.6).shift(0.25 * DOWN)
        nums = VGroup(*[MathTex(str(k)).scale(0.55).next_to(ax.c2p(k, 0), DOWN, buff=0.15) for k in (1, 2, 3, 4)],
                      *[MathTex(str(k)).scale(0.55).next_to(ax.c2p(0, k), LEFT, buff=0.15) for k in (1, 2, 3, 4)])
        curve = ax.plot(f, x_range=[-0.62, 4.62], color=CURVE, stroke_width=4)
        x = ValueTracker(-0.45)
        X = lambda: x.get_value()
        dot = always_redraw(lambda: Dot(ax.c2p(X(), f(X())), color=POINT, radius=0.08))
        tan = always_redraw(lambda: tangent_line(ax, f, df, X(), 2.4))
        readout = slope_readout(lambda: df(X()), scale=1.0).move_to([4.7, 2.6, 0])

        def mood():
            s = df(X())
            if abs(s) < 0.04:
                return Tex(r"level", color=POINT)
            return Tex(r"rising", color=GREEN_C) if s > 0 else Tex(r"falling", color=RED_C)
        mood_lab = always_redraw(lambda: mood().scale(0.8).next_to(readout, DOWN, buff=0.35))

        # sign strip under the graph
        strip_y = ax.c2p(0, -2)[1] - 0.45
        reach = [X()]
        def strip():
            reach[0] = max(reach[0], X())
            g = VGroup()
            for a, b, c in ((-0.62, 1, GREEN_C), (1, 3, RED_C), (3, 4.62, GREEN_C)):
                hi = min(b, reach[0])
                if hi > a + 1e-3:
                    g.add(Line([ax.c2p(a, 0)[0], strip_y, 0], [ax.c2p(hi, 0)[0], strip_y, 0], color=c, stroke_width=8))
            return g
        sign_strip = always_redraw(strip)
        strip_lab = Tex(r"sign of $\frac{dy}{dx}$", color=MUTED).scale(0.6).next_to([ax.c2p(4.62, 0)[0], strip_y, 0], RIGHT, buff=0.3)

        with self.voice(
            "Here is a curve that climbs, falls back, and climbs again. Let's ride along it and watch $\\frac{dy}{dx}$."
        ) as v:
            self.play(Create(ax), FadeIn(nums), run_time=1.2)
            self.play(Create(curve), run_time=1.6)
            self.play(FadeIn(dot), Create(tan), FadeIn(readout), FadeIn(mood_lab), run_time=v.left(frac=0.6))

        card = keep_in_frame(self.ponder_card(r"Where on this curve is $\dfrac{dy}{dx} = 0$?").move_to([4.3, -0.6, 0]))
        with self.voice("Before we set off: at which points do you expect $\\frac{dy}{dx}$ to be exactly zero?") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("ch3-flat")
        self.play(FadeOut(card), run_time=0.5)
        self.add(sign_strip, strip_lab)

        mx = VGroup(DashedLine(ax.c2p(0.3, 7 / 3), ax.c2p(1.7, 7 / 3), color=POINT, stroke_width=2),
                    Tex(r"maximum", color=POINT).scale(0.65).next_to(ax.c2p(1, 7 / 3), UP, buff=0.25))
        mn = VGroup(DashedLine(ax.c2p(2.3, 1), ax.c2p(3.7, 1), color=POINT, stroke_width=2),
                    Tex(r"minimum", color=POINT).scale(0.65).next_to(ax.c2p(3, 1), DOWN, buff=0.3))

        with self.voice(
            "Climbing, $\\frac{dy}{dx}$ is positive, but it shrinks as the curve levels off. At the summit it is exactly zero."
        ) as v:
            self.play(FadeIn(strip_lab), run_time=0.4)
            self.play(x.animate.set_value(1.0), run_time=v.left(frac=0.85), rate_func=smooth)
            self.play(Create(mx[0]), FadeIn(mx[1]), run_time=0.6)
        with self.voice(
            "Past the summit, $dy$ is a step down, so $\\frac{dy}{dx}$ is negative, until the bottom of the trough, "
            "where once again it is zero."
        ) as v:
            self.play(x.animate.set_value(3.0), run_time=v.left(frac=0.85), rate_func=smooth)
            self.play(Create(mn[0]), FadeIn(mn[1]), run_time=0.6)
        with self.voice(
            "From there it is positive, and keeps on growing. At the trough, $y$ is said to pass by a minimum; "
            "over the summit, by a maximum."
        ) as v:
            self.play(x.animate.set_value(4.5), run_time=3.0, rate_func=smooth)
            self.play(Indicate(mn[1]), Indicate(mx[1]), run_time=v.left(minimum=1.0))

        note = VGroup(
            Tex(r"At a maximum or a minimum,", color=NOTE).scale(0.72),
            MathTex(r"\frac{dy}{dx} = 0").scale(1.1),
        ).arrange(DOWN, buff=0.25)
        note_box = SurroundingRectangle(note, color=NOTE, buff=0.3, corner_radius=0.15)
        note_g = keep_in_frame(VGroup(note_box, note).move_to([4.3, -0.7, 0]))
        with self.voice(
            "Note this well: for the value of $x$ that makes $y$ a maximum or a minimum, $\\frac{dy}{dx} = 0$. "
            "Later chapters turn this into a way of finding them."
        ) as v:
            self.play(FadeOut(mood_lab), x.animate.set_value(1.0), run_time=1.6)
            self.play(Write(note), Create(note_box), run_time=v.left(frac=0.6))

        low = ax.plot(f, x_range=[-0.62, 0], color=RED_C, stroke_width=7)
        high = ax.plot(f, x_range=[4.0, 4.62], color=RED_C, stroke_width=7)
        lvl1 = DashedLine(ax.c2p(-1, 1), ax.c2p(5, 1), color=MUTED, stroke_width=1.5)
        lvl2 = DashedLine(ax.c2p(-1, 7 / 3), ax.c2p(5, 7 / 3), color=MUTED, stroke_width=1.5)
        with self.voice(
            "But a minimum is not necessarily the smallest value of $y$. Here the minimum is $y = 1$, "
            "yet further left the curve dips well below $1$."
        ) as v:
            self.play(FadeOut(readout), FadeOut(note_g), FadeOut(tan), FadeOut(dot), run_time=0.6)
            self.play(Create(lvl1), run_time=1.0)
            self.play(Create(low), run_time=v.left(frac=0.6))
        arrows = VGroup(
            Arrow(ax.c2p(2.55, 1.15), ax.c2p(2.05, 1.65), buff=0, color=GREEN_C, stroke_width=4, max_tip_length_to_length_ratio=0.3),
            Arrow(ax.c2p(3.45, 1.15), ax.c2p(3.95, 1.65), buff=0, color=GREEN_C, stroke_width=4, max_tip_length_to_length_ratio=0.3),
        )
        with self.voice(
            "Likewise the maximum, two and a third, is easily beaten on the right. What makes a minimum is that "
            "$y$ increases on either side of it.",
        ) as v:
            self.play(Create(lvl2), run_time=1.0)
            self.play(Create(high), run_time=1.2)
            self.wait(v.left(frac=0.35))
            self.play(GrowArrow(arrows[0]), GrowArrow(arrows[1]), run_time=v.left(minimum=1.0))
        self.wait(0.8)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch04Oddities(Narrated, Scene):
    chapter_title = "Curious curves"

    def construct(self):
        self.section_card(4, "Curious curves")

        # ── Figure 17: always rising, with one lazy stretch ──
        f = lambda x: 0.25 * (x - 2) ** 3 + 0.4 * x + 1.0
        df = lambda x: 0.75 * (x - 2) ** 2 + 0.4
        ax = plain_axes([0, 4.5], [-1.5, 5.5], 6.5, 6.0).to_edge(LEFT, buff=1.0).shift(0.2 * DOWN)
        curve = ax.plot(f, x_range=[0.1, 4.25], color=CURVE, stroke_width=4)
        x = ValueTracker(0.25)
        dot = always_redraw(lambda: Dot(ax.c2p(x.get_value(), f(x.get_value())), color=POINT, radius=0.08))
        tan = always_redraw(lambda: tangent_line(ax, f, df, x.get_value(), 2.4))
        readout = slope_readout(lambda: df(x.get_value())).move_to([4.2, 2.2, 0])
        with self.voice(
            "Some curves never stop rising, yet have one lazy stretch. Here $\\frac{dy}{dx}$ is positive everywhere."
        ) as v:
            self.play(Create(ax), Create(curve), run_time=1.6)
            self.play(FadeIn(dot), Create(tan), FadeIn(readout), run_time=0.8)
            self.play(x.animate.set_value(2.0), run_time=v.left(minimum=1.5))
        lazy = VGroup(
            Tex(r"least steep here:", color=POINT).scale(0.7),
            Tex(r"$\frac{dy}{dx}$ is a \emph{minimum}", color=POINT).scale(0.7),
        ).arrange(DOWN, buff=0.12).next_to(ax.c2p(2, f(2)), RIGHT, buff=1.0).shift(0.9 * DOWN)
        with self.voice(
            "But at one place the climb is least steep. There, $\\frac{dy}{dx}$ itself is a minimum: "
            "smaller than at any other part of the curve."
        ) as v:
            self.play(Flash(ax.c2p(2, f(2)), color=POINT), FadeIn(lazy, shift=0.2 * LEFT), run_time=1.2)
            self.wait(v.left(frac=0.3))
            self.play(x.animate.set_value(4.1), run_time=v.left(minimum=1.2))
        self.wait(0.5)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.7)

        # ── Figure 18: a curve with a nose ──
        ax = plain_axes([0, 4], [-0.5, 4.5], 5.6, 5.6).to_edge(LEFT, buff=1.2).shift(0.2 * DOWN)
        cx = lambda t: 3 - 0.5 * t**2
        cy = lambda t: 2 + t
        nose = ax.plot_parametric_curve(lambda t: np.array([cx(t), cy(t), 0]), t_range=[-2.2, 2.2], color=CURVE, stroke_width=4)
        t = ValueTracker(1.9)
        T = lambda: t.get_value()
        P = lambda: ax.c2p(cx(T()), cy(T()))
        dot = always_redraw(lambda: Dot(P(), color=POINT, radius=0.08))
        tan = always_redraw(lambda: direction_line(P(), ax.c2p(-T(), 1) - ax.c2p(0, 0), 2.4))
        lhs = MathTex(r"\frac{dy}{dx}", "=").move_to([3.2, 2.2, 0])
        num = DecimalNumber(0, num_decimal_places=2, include_sign=True)
        inf = MathTex(r"\pm\infty", color=POINT)
        def upd_num(m):
            s = -1 / T() if abs(T()) > 1e-6 else 1e9
            m.set_value(s)
            m.next_to(lhs, RIGHT, buff=0.2)
            m.set_opacity(0 if abs(s) > 40 else 1)
        def upd_inf(m):
            m.next_to(lhs, RIGHT, buff=0.2)
            m.set_opacity(1 if abs(T()) < 1 / 40 else 0)
        num.add_updater(upd_num)
        inf.add_updater(upd_inf)
        with self.voice(
            "This curve bends right back on itself. On the upper part, $\\frac{dy}{dx}$ is negative; "
            "as it rounds the nose, the slope gets steeper and steeper."
        ) as v:
            self.play(Create(ax), Create(nose), run_time=1.6)
            self.play(FadeIn(dot), Create(tan), FadeIn(lhs), FadeIn(num), run_time=0.8)
            self.add(inf)
            self.play(t.animate.set_value(0.35), run_time=v.left(minimum=1.5))
        card = self.ponder_card(r"At the nose the tangent stands straight up.",
                                r"What happens to $\dfrac{dy}{dx}$ there?").move_to([3.8, -1.6, 0])
        keep_in_frame(card)
        with self.voice("Pause and ponder: at the nose, the tangent is vertical. What becomes of $\\frac{dy}{dx}$?") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("ch4-nose")
        with self.voice(
            "Near the nose, $dx$ shrinks to nothing while $dy$ does not, so $\\frac{dy}{dx}$ becomes infinitely great. "
            "Then, on the lower part, it is positive."
        ) as v:
            self.play(FadeOut(card), run_time=0.5)
            self.play(t.animate.set_value(0.0), run_time=2.0, rate_func=smooth)
            self.wait(1.2)
            self.play(t.animate.set_value(-1.9), run_time=v.left(minimum=1.5))
        self.wait(0.5)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.7)

        # ── Figure 25: a cusp ──
        g = lambda x: 3.2 - 0.9 * abs(x - 2) - 0.12 * (x - 2) ** 2
        dg = lambda x: (-0.9 if x > 2 else 0.9) - 0.24 * (x - 2)
        ax = plain_axes([0, 4.2], [0, 4], 6.0, 4.8).to_edge(LEFT, buff=1.0)
        cusp = VGroup(ax.plot(g, x_range=[0.1, 1.9999, 0.01], color=CURVE, stroke_width=4),
                      ax.plot(g, x_range=[2.0001, 3.9, 0.01], color=CURVE, stroke_width=4))
        x = ValueTracker(0.4)
        dot = always_redraw(lambda: Dot(ax.c2p(x.get_value(), g(x.get_value())), color=POINT, radius=0.08))
        tan = always_redraw(lambda: tangent_line(ax, g, dg, x.get_value(), 2.4))
        readout = slope_readout(lambda: dg(x.get_value())).move_to([4.2, 1.8, 0])
        with self.voice(
            "And if a curve comes to a sudden point, a cusp, the slope changes from upward to downward all at once: "
            "$\\frac{dy}{dx}$ jumps abruptly from a positive value to a negative one."
        ) as v:
            self.play(Create(ax), Create(cusp), run_time=1.6)
            self.play(FadeIn(dot), Create(tan), FadeIn(readout), run_time=0.8)
            self.play(x.animate.set_value(1.97), run_time=2.5, rate_func=linear)
            self.wait(0.5)
            self.play(x.animate.set_value(2.03), run_time=0.15, rate_func=linear)
            self.wait(0.5)
            self.play(x.animate.set_value(3.7), run_time=v.left(minimum=1.5), rate_func=linear)
        self.wait(0.6)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.7)


# ════════════════════════════════════════════════════════════════════════
class Ch05Lines(Narrated, Scene):
    chapter_title = "Straight lines"

    def construct(self):
        self.section_card(5, "Straight lines")

        u = 0.82  # equal scales on both axes
        ax = plain_axes([-1, 7, 1], [-1, 6.5, 1], 8 * u, 7.5 * u, ticks=True).to_edge(LEFT, buff=0.7).shift(0.1 * DOWN)
        letters = axes_letters(ax, o=False, x="x", y="y")
        b = 1.0
        eq = MathTex("y", "=", "x", "+", "b").scale(1.2).move_to([4.2, 2.6, 0])

        with self.voice(
            "Now let's connect the picture with the rules for differentiating. The simplest case: $y = x + b$, "
            "plotted with equal scales on both axes.",
            say="Now let's connect the picture with the rules for differentiating. The simplest case: y equals x plus b, "
                "plotted with equal scales on both axes.",
        ) as v:
            self.play(Create(ax), FadeIn(letters), run_time=1.4)
            self.play(Write(eq), run_time=v.left(frac=0.6))

        start = Dot(ax.c2p(0, b), color=POINT)
        bb = BraceBetweenPoints(ax.c2p(0, 0), ax.c2p(0, b), LEFT, buff=0.08)
        bl = MathTex("b").scale(0.85).next_to(bb, LEFT, buff=0.1)
        with self.voice("Put $x = 0$ and you get $y = b$: the line crosses the $y$ axis at a height $b$.") as v:
            self.play(GrowFromCenter(start), run_time=0.6)
            self.play(GrowFromCenter(bb), FadeIn(bl), run_time=v.left(frac=0.6))

        line = ax.plot(lambda x: x + b, x_range=[-0.25, 5.3], color=CURVE, stroke_width=4)
        stairs = VGroup()
        for k in range(4):
            p = ax.c2p(k, k + b)
            stairs.add(Line(p, ax.c2p(k + 1, k + b), color=DX_C, stroke_width=4),
                       Line(ax.c2p(k + 1, k + b), ax.c2p(k + 1, k + 1 + b), color=DY_C, stroke_width=4))
        with self.voice(
            "From there it climbs at $45°$: every step to the right is matched by an equal step up. "
            "A gradient of one in one."
        ) as v:
            self.play(Create(line), run_time=1.4)
            self.play(LaggedStart(*[Create(s) for s in stairs], lag_ratio=0.4), run_time=v.left(frac=0.8))

        d1 = MathTex(r"\frac{dy}{dx}", "=", "1").scale(1.2).next_to(eq, DOWN, buff=0.7)
        with self.voice(
            "Differentiate $y = x + b$ and you get $\\frac{dy}{dx} = 1$. The algebra and the picture agree: "
            "the slope is one, and it is the same everywhere.",
            say="Differentiate y equals x plus b, and you get d y by d x equals 1. The algebra and the picture agree: "
                "the slope is one, and it is the same everywhere.",
        ) as v:
            self.play(TransformFromCopy(eq, d1), run_time=1.4)
            self.play(Indicate(stairs, color=WHITE), run_time=v.left(frac=0.6))

        # ── y = ax + b ──
        a = ValueTracker(1.0)
        line2 = always_redraw(lambda: ax.plot(lambda x: a.get_value() * x + b, x_range=self._clip(a.get_value(), b),
                                              color=CURVE, stroke_width=4))
        eq2 = MathTex("y", "=", "a", "x", "+", "b").scale(1.2).move_to(eq)
        d2 = MathTex(r"\frac{dy}{dx}", "=", "a").scale(1.2).move_to(d1)
        with self.voice(
            "Next, $y = ax + b$. It starts from the same height $b$, and differentiating gives $\\frac{dy}{dx} = a$: "
            "a constant slope, decided by $a$.",
            say="Next, y equals a x, plus b. It starts from the same height b, and differentiating gives d y by d x "
                "equals a: a constant slope, decided by a.",
        ) as v:
            self.play(FadeOut(stairs), run_time=0.5)
            self.remove(line)
            self.add(line2)
            self.play(TransformMatchingTex(eq, eq2), TransformMatchingTex(d1, d2), run_time=1.5)
            self.wait(v.left(minimum=0.2))

        tri = VGroup(
            Line(ax.c2p(0, b), ax.c2p(3, b), color=DX_C, stroke_width=4),
            Line(ax.c2p(3, b), ax.c2p(3, b + 1), color=DY_C, stroke_width=4),
        )
        b3 = MathTex("3", color=DX_C).scale(0.8).next_to(tri[0], DOWN, buff=0.12)
        b1 = MathTex("1", color=DY_C).scale(0.8).next_to(tri[1], RIGHT, buff=0.12)
        a_val = MathTex(r"a = \tfrac13").scale(1.0).next_to(d2, DOWN, buff=0.6)
        with self.voice(
            "Say $a = \\tfrac13$. Then the line rises one in three: $dx$ is three times as long as $dy$.",
            say="Say a equals one third. Then the line rises one in three: d x is three times as long as d y.",
        ) as v:
            self.play(a.animate.set_value(1 / 3), FadeIn(a_val), run_time=1.6)
            self.play(Create(tri[0]), FadeIn(b3), run_time=0.8)
            self.play(Create(tri[1]), FadeIn(b1), run_time=v.left(frac=0.7))

        a_read = VGroup(MathTex(r"a = \frac{dy}{dx} ="), DecimalNumber(1 / 3, num_decimal_places=2, include_sign=True))
        a_read[1].add_updater(lambda m: m.set_value(a.get_value()))
        a_read[1].add_updater(lambda m: m.next_to(a_read[0], RIGHT, buff=0.2))
        a_read.move_to(a_val).shift(0.2 * LEFT)
        with self.voice(
            "Change $a$, and the line swings about the point where it meets the $y$ axis. "
            "The constant $b$ fixes where the line starts; only $a$ decides its steepness.",
            say="Change a, and the line swings about the point where it meets the y axis. "
                "The constant b fixes where the line starts; only a decides its steepness.",
        ) as v:
            self.play(FadeOut(tri), FadeOut(b3), FadeOut(b1), FadeOut(a_val), run_time=0.5)
            self.play(FadeIn(a_read), run_time=0.5)
            self.play(a.animate.set_value(1.6), run_time=1.6)
            self.play(a.animate.set_value(-0.6), run_time=2.0)
            self.play(a.animate.set_value(1 / 3), run_time=v.left(minimum=1.2))

        card = self.ponder_card(r"A straight line passes through", r"$(0,\,1)$ and $(6,\,3)$.",
                                r"What is its $\dfrac{dy}{dx}$?").move_to([4.0, -2.0, 0])
        with self.voice(
            "Your turn. A straight line passes through the points $(0, 1)$ and $(6, 3)$. What is its $\\frac{dy}{dx}$?",
            say="Your turn. A straight line passes through the points zero, 1, and 6, 3. What is its d y by d x?",
        ) as v:
            self.play(FadeOut(a_read), FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("ch5-line")
        pts = VGroup(Dot(ax.c2p(0, 1), color=POINT), Dot(ax.c2p(6, 3), color=POINT))
        run = Line(ax.c2p(0, 1), ax.c2p(6, 1), color=DX_C, stroke_width=4)
        rise = Line(ax.c2p(6, 1), ax.c2p(6, 3), color=DY_C, stroke_width=4)
        ans = MathTex(r"\frac{dy}{dx} = \frac{2}{6} = \frac13").move_to([4.0, -2.0, 0])
        with self.voice(
            "It rises $2$ while running $6$, so $\\frac{dy}{dx} = \\tfrac26$, which is one third. That's the very line on the screen.",
            say="It rises 2 while running 6, so d y by d x is 2 sixths, which is one third. That's the very line on the screen.",
        ) as v:
            self.play(FadeOut(card), FadeIn(pts), run_time=0.6)
            self.play(Create(run), Create(rise), run_time=1.2)
            self.play(Write(ans), run_time=v.left(frac=0.7))
        self.wait(0.6)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)

    @staticmethod
    def _clip(a, b, x0=-0.25, x1=6.6, y0=-1.0, y1=6.5):
        lo, hi = x0, x1
        if abs(a) > 1e-6:
            xs = sorted(((y0 - b) / a, (y1 - b) / a))
            lo, hi = max(lo, xs[0]), min(hi, xs[1])
        return [lo, hi]


# ════════════════════════════════════════════════════════════════════════
class Ch06Parabola(Narrated, Scene):
    chapter_title = "A slope that changes"

    def construct(self):
        self.section_card(6, "A slope that changes")

        f = lambda x: 0.25 * x**2 + 3
        df = lambda x: 0.5 * x
        ax = plain_axes([-5.5, 5.5, 1], [0, 10.5, 1], 7.4, 6.2).to_edge(LEFT, buff=0.6).shift(0.2 * DOWN)
        letters = axes_letters(ax, o=False, x="x", y="y")
        curve = ax.plot(f, x_range=[-5.2, 5.2], color=CURVE, stroke_width=4)
        P = Dot(ax.c2p(0, 3), color=POINT)
        P_lab = MathTex("P").scale(0.8).next_to(P, UR, buff=0.08)
        bb = BraceBetweenPoints(ax.c2p(0, 0), ax.c2p(0, 3), LEFT, buff=0.08)
        bl = MathTex("b").scale(0.85).next_to(bb, LEFT, buff=0.1)
        eq = MathTex("y", "=", "a", "x^2", "+", "b").scale(1.15).move_to([4.4, 2.7, 0])

        with self.voice(
            "Now a harder case: $y = ax^2 + b$. Again the curve starts on the $y$ axis, at a height $b$.",
            say="Now for a slightly harder case: y equals a x squared, plus b. Again the curve starts on the y axis, at a height b.",
        ) as v:
            self.play(Create(ax), FadeIn(letters), Write(eq), run_time=1.6)
            self.play(Create(curve), run_time=1.6)
            self.play(FadeIn(P), FadeIn(P_lab), GrowFromCenter(bb), FadeIn(bl), run_time=v.left(frac=0.6))

        d = MathTex(r"\frac{dy}{dx}", "=", "2", "a", "x").scale(1.15).next_to(eq, DOWN, buff=0.6)
        with self.voice(
            "Differentiate. If you've forgotten how, don't turn back: think it out. You get $\\frac{dy}{dx} = 2ax$.",
            say="Now differentiate. If you've forgotten how, don't turn back: think it out. You get d y by d x equals 2 a x.",
        ) as v:
            self.wait(v.left(frac=0.55))
            self.play(TransformFromCopy(eq, d), run_time=v.left(minimum=1.0))

        x = ValueTracker(0.0)
        dot = always_redraw(lambda: Dot(ax.c2p(x.get_value(), f(x.get_value())), color=POINT, radius=0.08))
        tan = always_redraw(lambda: tangent_line(ax, f, df, x.get_value(), 2.6))
        readout = slope_readout(lambda: df(x.get_value()), scale=0.9).move_to([4.4, -0.6, 0])
        with self.voice(
            "So the steepness isn't constant; it grows as $x$ grows. At the starting point $P$, where $x = 0$, "
            "the curve has no steepness at all: it is level."
        ) as v:
            self.play(FadeIn(dot), Create(tan), FadeIn(readout), FadeOut(bb), FadeOut(bl), run_time=1.0)
            self.wait(v.left(frac=0.5))
            self.play(x.animate.set_value(4.4), run_time=v.left(minimum=1.5))
        with self.voice(
            "To the left of the origin, $x$ is negative, so $\\frac{dy}{dx}$ is negative too: there the curve descends "
            "from left to right."
        ) as v:
            self.play(x.animate.set_value(-4.4), run_time=v.left(frac=0.7))
            self.play(x.animate.set_value(0), run_time=v.left(minimum=1.0))

        eq_n = MathTex(r"y = \tfrac14 x^2 + 3").scale(1.15).move_to(eq)
        d_n = MathTex(r"\frac{dy}{dx} = \tfrac12 x").scale(1.15).move_to(d)
        with self.voice(
            "Let's put in numbers: $y = \\tfrac14 x^2 + 3$. Differentiating, $\\frac{dy}{dx} = \\tfrac12 x$.",
            say="Let's put in numbers: y equals one quarter x squared, plus 3. Differentiating, d y by d x equals one half x.",
        ) as v:
            self.play(ReplacementTransform(eq, eq_n), run_time=1.2)
            self.play(ReplacementTransform(d, d_n), run_time=v.left(minimum=1.0))

        card = self.ponder_card(r"What is the slope of", r"$y = \tfrac14 x^2 + 3$ at $x = 4$?", width=5.2).move_to([4.4, -1.9, 0])
        with self.voice("Pause and try it: what is the slope of this curve where $x = 4$?") as v:
            self.play(FadeOut(readout), FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("ch6-slope4")
        self.play(FadeOut(card), run_time=0.4)

        # ── the table ──
        xs = [0, 1, 2, 3, 4, 5]
        ys = [r"3", r"3\tfrac14", r"4", r"5\tfrac14", r"7", r"9\tfrac14"]
        ds = [r"0", r"\tfrac12", r"1", r"1\tfrac12", r"2", r"2\tfrac12"]
        table = MathTable(
            [[str(v) for v in xs], ys, ds],
            row_labels=[MathTex("x"), MathTex("y"), MathTex(r"\frac{dy}{dx}")],
            include_outer_lines=False, h_buff=0.75, v_buff=0.45,
            line_config={"stroke_width": 1, "color": MUTED},
        ).scale(0.8).move_to([0, 0.1, 0])
        with self.voice(
            "Now tabulate, from $x = 0$ to $5$: $y$ from the first equation, $\\frac{dy}{dx}$ from the second."
        ) as v:
            self.play(*[FadeOut(o) for o in (ax, letters, curve, P, P_lab, dot, tan)], run_time=0.6)
            self.play(VGroup(eq_n, d_n).animate.arrange(RIGHT, buff=1.2).to_edge(UP, buff=0.5), run_time=0.8)
            self.play(Create(table.get_horizontal_lines()), Create(table.get_vertical_lines()),
                      FadeIn(table.get_row_labels()), run_time=0.8)
            cols = [VGroup(*[table.get_entries((r, c)) for r in (1, 2, 3)]) for c in range(2, 8)]
            self.play(LaggedStart(*[FadeIn(c, shift=0.15 * DOWN) for c in cols], lag_ratio=0.35), run_time=v.left(minimum=2.0))
        col4 = SurroundingRectangle(cols[4], color=POINT, buff=0.12)
        with self.voice("At $x = 4$ the slope is $2$: the curve climbs two units for every one across.") as v:
            self.play(Create(col4), run_time=v.left(frac=0.5))

        # ── two graphs, one above the other ──
        top = plain_axes([0, 5.5, 1], [0, 10.5, 1], 6.6, 3.3, ticks=True).move_to([-2.6, 1.55, 0])
        bot = plain_axes([0, 5.5, 1], [0, 3.2, 1], 6.6, 2.1, ticks=True).move_to([-2.6, -2.35, 0])
        top_l = VGroup(MathTex("y").scale(0.7).next_to(top.y_axis.get_end(), LEFT, buff=0.15),
                       MathTex("x").scale(0.7).next_to(top.x_axis.get_end(), DOWN, buff=0.15))
        bot_l = VGroup(MathTex(r"\frac{dy}{dx}").scale(0.6).next_to(bot.y_axis.get_end(), LEFT, buff=0.15),
                       MathTex("x").scale(0.7).next_to(bot.x_axis.get_end(), DOWN, buff=0.15))
        xn = VGroup(*[MathTex(str(k)).scale(0.45).next_to(bot.c2p(k, 0), DOWN, buff=0.12) for k in range(1, 6)])
        yd = [f(k) for k in xs]
        dd = [df(k) for k in xs]
        top_dots = VGroup(*[Dot(top.c2p(k, yv), radius=0.06, color=CURVE) for k, yv in zip(xs, yd)])
        bot_dots = VGroup(*[Dot(bot.c2p(k, dv), radius=0.06, color=DY_C) for k, dv in zip(xs, dd)])
        top_curve = top.plot(f, x_range=[0, 5.3], color=CURVE, stroke_width=4)
        bot_curve = bot.plot(df, x_range=[0, 5.3], color=DY_C, stroke_width=4)
        with self.voice(
            "Then plot them out: $y$ against $x$ in one figure, and $\\frac{dy}{dx}$ against $x$ in another, just beneath it."
        ) as v:
            self.play(FadeOut(col4), table.animate.scale(0.62).move_to([4.6, 0.2, 0]),
                      VGroup(eq_n, d_n).animate.scale(0.8).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([4.6, 2.6, 0]),
                      run_time=1.0)
            self.play(Create(top), Create(bot), FadeIn(top_l), FadeIn(bot_l), FadeIn(xn), run_time=1.0)
            self.play(LaggedStart(*[TransformFromCopy(table.get_entries((2, c + 2)), top_dots[c]) for c in range(6)], lag_ratio=0.15),
                      LaggedStart(*[TransformFromCopy(table.get_entries((3, c + 2)), bot_dots[c]) for c in range(6)], lag_ratio=0.15),
                      run_time=2.0)
            self.play(Create(top_curve), Create(bot_curve), run_time=v.left(minimum=1.2))

        xv = ValueTracker(0.0)
        Xv = lambda: xv.get_value()
        tdot = always_redraw(lambda: Dot(top.c2p(Xv(), f(Xv())), color=POINT, radius=0.07))
        ttan = always_redraw(lambda: tangent_line(top, f, df, Xv(), 2.2))
        trun = always_redraw(lambda: Line(top.c2p(Xv(), f(Xv())), top.c2p(Xv() + 1, f(Xv())), color=DX_C, stroke_width=4))
        trise = always_redraw(lambda: Line(top.c2p(Xv() + 1, f(Xv())), top.c2p(Xv() + 1, f(Xv()) + df(Xv())), color=DY_C, stroke_width=4)
                              if Xv() > 0.02 else VMobject())
        bbar = always_redraw(lambda: Line(bot.c2p(Xv(), 0), bot.c2p(Xv(), df(Xv())), color=DY_C, stroke_width=5)
                             if Xv() > 0.02 else VMobject())
        bdot = always_redraw(lambda: Dot(bot.c2p(Xv(), df(Xv())), color=POINT, radius=0.07))
        link = always_redraw(lambda: DashedLine(top.c2p(Xv(), 0), bot.c2p(Xv(), df(Xv())), color=MUTED, stroke_width=1.5))
        one = MathTex("1", color=DX_C).scale(0.55).add_updater(lambda m: m.next_to(trun, DOWN, buff=0.06))
        with self.voice(
            "Now run along the upper curve. For each $x$, take one step across: the rise you need is the slope. "
            "Below, that same rise is drawn as a height."
        ) as v:
            self.play(FadeIn(tdot), Create(ttan), FadeIn(bdot), FadeIn(link), run_time=1.0)
            self.add(trun, trise, bbar, one)
            self.play(xv.animate.set_value(2.0), run_time=2.0)
            self.play(TransformFromCopy(trise, bbar.copy().clear_updaters()), run_time=1.4)
            self.play(xv.animate.set_value(4.2), run_time=v.left(minimum=1.5))
        with self.voice(
            "So, for any value of $x$, the height of the lower graph is proportional to the slope of the upper one. "
            "Level at zero, and steeper and steeper as $x$ grows."
        ) as v:
            self.play(xv.animate.set_value(0.0), run_time=v.left(frac=0.5))
            self.play(xv.animate.set_value(3.0), run_time=v.left(minimum=1.0))
        self.wait(0.6)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch07TangentAngle(Narrated, MovingCameraScene):
    chapter_title = "Example: a tangent and an angle"

    def construct(self):
        self.section_card(7, "Worked example: a tangent and an angle")

        u = 1.12  # equal scales, so angles on screen are true angles
        ax = plain_axes([-4, 1.5, 1], [-0.5, 5, 1], 5.5 * u, 5.5 * u, ticks=True).to_edge(LEFT, buff=0.5).shift(0.35 * DOWN)
        letters = axes_letters(ax, o=False, x="x", y="y")
        nums = VGroup(*[MathTex(str(k)).scale(0.5).next_to(ax.c2p(k, 0), DOWN, buff=0.12) for k in (-3, -2, -1, 1)],
                      *[MathTex(str(k)).scale(0.5).next_to(ax.c2p(0, k), RIGHT, buff=0.12) for k in (1, 3, 4)])
        h = lambda x: 1 / (2 * x) + 3
        hyp = VGroup(ax.plot(h, x_range=[-4, -0.172], color=CURVE, stroke_width=4),
                     ax.plot(h, x_range=[0.25, 1.5], color=CURVE, stroke_width=4))
        hyp_lab = MathTex(r"y = \frac{1}{2x} + 3", color=CURVE).scale(0.75).next_to(ax.c2p(-3.0, h(-3.0)), DOWN, buff=0.3)
        pt = Dot(ax.c2p(-1, 2.5), color=POINT)

        RX = 3.9  # centre of the working column on the right
        prob = Tex(r"Find the slope of the tangent to\\$y = \dfrac{1}{2x} + 3$ where $x = -1$.").scale(0.7).move_to([RX, 3.2, 0])
        with self.voice(
            "An example. Find the slope of the tangent to $y = \\frac{1}{2x} + 3$ at the point where $x = -1$.",
            say="Here is an example. Find the slope of the tangent to the curve y equals 1 over 2 x, plus 3, "
                "at the point where x equals minus 1.",
        ) as v:
            self.play(Create(ax), FadeIn(letters), FadeIn(nums), FadeIn(prob), run_time=1.6)
            self.play(Create(hyp), FadeIn(hyp_lab), run_time=1.6)
            self.play(GrowFromCenter(pt), run_time=v.left(minimum=0.5))

        card = self.ponder_card(r"Differentiate, then put $x = -1$.", width=4.6).move_to([RX, 0.6, 0])
        with self.voice("Try it before I do: differentiate, then put in $x = -1$.",
                        say="Try it before I do: differentiate, then put in x equals minus 1.") as v:
            self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoint("ch7-slope")

        s1 = MathTex(r"\frac{dy}{dx} = -\frac{1}{2x^2}").scale(0.8)
        s2 = MathTex(r"x=-1:\quad \frac{dy}{dx} = -\tfrac12").scale(0.8)
        work = VGroup(s1, s2).arrange(DOWN, buff=0.3).move_to([RX, 1.5, 0])
        tan = ax.plot(lambda x: -0.5 * x + 2, x_range=[-4, 1.5], color=TANGENT, stroke_width=3)
        with self.voice(
            "Differentiating gives $\\frac{dy}{dx} = -\\frac{1}{2x^2}$. At $x = -1$ that's $-\\tfrac12$: the slope of "
            "the curve, and of its tangent, at that point.",
            say="Differentiating gives d y by d x equals minus 1 over 2 x squared. At x equals minus 1, that's minus one half: "
                "the slope of the curve, and of its tangent, at that point.",
        ) as v:
            self.play(FadeOut(card), Write(s1), run_time=1.4)
            self.wait(v.left(frac=0.45))
            self.play(Write(s2), run_time=1.2)
            self.play(Create(tan), run_time=v.left(minimum=1.0))

        s3 = MathTex(r"y = -\tfrac12 x + b").scale(0.8)
        s4 = MathTex(r"2\tfrac12 = -\tfrac12(-1) + b").scale(0.8)
        s5 = MathTex(r"b = 2").scale(0.8)
        work2 = VGroup(s3, s4, s5).arrange(DOWN, buff=0.3).next_to(work, DOWN, buff=0.4)
        with self.voice(
            "The tangent is a straight line, $y = ax + b$, with $a = -\\tfrac12$. It passes through the point "
            "$x = -1$, $y = 2\\tfrac12$, so $2\\tfrac12 = \\tfrac12 + b$, and $b = 2$.",
            say="The tangent is a straight line, y equals a x plus b, with a equal to minus one half. It passes through "
                "the point x equals minus 1, y equals 2 and a half. So 2 and a half equals one half plus b, and b equals 2.",
        ) as v:
            self.play(Write(s3), run_time=1.2)
            self.wait(v.left(frac=0.35))
            self.play(Write(s4), run_time=1.4)
            self.play(Write(s5), run_time=v.left(minimum=0.8))
        tan_eq = MathTex(r"y = -\tfrac12 x + 2", color=TANGENT).scale(0.9).move_to([RX, 1.6, 0])
        with self.voice("So the tangent is $y = -\\tfrac12 x + 2$.",
                        say="So the tangent is: y equals minus one half x, plus 2.") as v:
            self.play(FadeOut(prob), FadeOut(work), FadeOut(work2[:2]), ReplacementTransform(s5, tan_eq), run_time=1.2)
            self.play(Circumscribe(tan_eq, color=TANGENT), run_time=v.left(minimum=0.8))

        # ── part two: the angle with y = 2x^2 + 2 ──
        par = ax.plot(lambda x: 2 * x**2 + 2, x_range=[-1.22, 1.22], color=CURVE_2, stroke_width=4)
        par_lab = MathTex(r"y = 2x^2 + 2", color=CURVE_2).scale(0.75).next_to(ax.c2p(-1.15, 4.6), LEFT, buff=0.15)
        prob2 = Tex(r"At what angle does this tangent\\cut the curve $y = 2x^2 + 2$?").scale(0.7).move_to([RX, 3.2, 0])
        with self.voice(
            "Second part: at what angle does this tangent cut the curve $y = 2x^2 + 2$? "
            "Where two curves meet, the point satisfies both equations at once.",
            say="Second part: at what angle does this tangent cut the curve y equals 2 x squared, plus 2? "
                "Where two curves meet, the point satisfies both equations at once.",
        ) as v:
            self.play(FadeOut(hyp_lab), hyp.animate.set_stroke(opacity=0.35), FadeOut(pt), FadeIn(prob2), run_time=1.0)
            self.play(Create(par), FadeIn(par_lab), run_time=v.left(minimum=1.0))
        e1 = MathTex(r"2x^2 + 2 = -\tfrac12 x + 2").scale(0.8)
        e2 = MathTex(r"x\,(2x + \tfrac12) = 0").scale(0.8)
        e3 = MathTex(r"x = 0 \quad\text{or}\quad x = -\tfrac14").scale(0.8)
        eqs = VGroup(e1, e2, e3).arrange(DOWN, buff=0.3).move_to([RX, 0.0, 0])
        A0, A1 = ax.c2p(0, 2), ax.c2p(-0.25, 2.125)
        d0, d1 = Dot(A0, color=POINT, radius=0.05), Dot(A1, color=POINT, radius=0.05)
        with self.voice(
            "Setting $2x^2 + 2 = -\\tfrac12 x + 2$ gives $x(2x + \\tfrac12) = 0$: so $x = 0$, or $x = -\\tfrac14$.",
            say="Setting 2 x squared plus 2 equal to minus one half x plus 2 gives: x, times 2 x plus one half, equals zero. "
                "So x equals zero, or x equals minus one quarter.",
        ) as v:
            self.play(Write(e1), run_time=1.4)
            self.play(Write(e2), run_time=1.4)
            self.play(Write(e3), FadeIn(d0), FadeIn(d1), run_time=v.left(minimum=1.0))

        # zoom in on the two crossings
        frame = self.camera.frame
        frame.save_state()
        z = 0.085
        centre = ax.c2p(-0.11, 2.05)
        thin = [hyp, tan, par]
        with self.voice("The two crossings are very close together, so let's zoom in.") as v:
            self.play(frame.animate.scale(z).move_to(centre),
                      *[m.animate.set_stroke(width=m.get_stroke_width() * z) for m in thin],
                      ax.animate.set_stroke(width=2 * z, opacity=0.35),
                      d0.animate.scale(z), d1.animate.scale(z),
                      run_time=v.left(minimum=2.0))

        r = 0.11
        horiz = DashedLine(ax.c2p(-0.35, 2), ax.c2p(0.42, 2), color=CURVE_2, stroke_width=2 * z, dash_length=0.02)
        arc0 = Arc(radius=r, start_angle=-np.arctan(0.5), angle=np.arctan(0.5), arc_center=A0, color=WHITE, stroke_width=2.5 * z)
        lab0 = MathTex(r"26^\circ 34'").scale(0.7 * z).next_to(A0 + r * np.array([np.cos(-0.23), np.sin(-0.23), 0]), RIGHT, buff=0.03)
        ptan = Line(ax.c2p(-0.25 - 0.17, 2.125 + 0.17), ax.c2p(-0.25 + 0.17, 2.125 - 0.17), color=CURVE_2, stroke_width=2.5 * z)
        arc1 = Arc(radius=r, start_angle=-np.pi / 4, angle=np.pi / 4 - np.arctan(0.5), arc_center=A1, color=WHITE, stroke_width=2.5 * z)
        mid1 = -(np.pi / 4 + np.arctan(0.5)) / 2
        lab1 = MathTex(r"18^\circ 26'").scale(0.7 * z).move_to(A1 + np.array([-0.03, -0.16, 0]))
        lead1 = Line(lab1.get_top() + 0.01 * UP, A1 + (r - 0.01) * np.array([np.cos(mid1), np.sin(mid1), 0]),
                     color=MUTED, stroke_width=1.5 * z)
        info0 = MathTex(r"\text{parabola: } \frac{dy}{dx} = 4x = 0").scale(0.6 * z).move_to(centre + np.array([0.36, 0.26, 0]))
        with self.voice(
            "The parabola's slope is $4x$. At $x = 0$ that's zero: the parabola runs horizontally there. "
            "The line falls with slope $-\\tfrac12$, at an angle whose tangent is $\\tfrac12$. That's $26°34'$.",
            say="The parabola's slope is 4 x. At x equals zero that's zero: the parabola runs horizontally there. "
                "The line falls with slope minus one half, at an angle whose tangent is one half. That's 26 degrees, 34 minutes.",
        ) as v:
            self.play(FadeIn(info0), run_time=0.8)
            self.play(Create(horiz), run_time=1.0)
            self.wait(v.left(frac=0.4))
            self.play(Create(arc0), FadeIn(lab0), run_time=v.left(minimum=1.0))
        info1 = MathTex(r"\text{parabola at } x = -\tfrac14:\ \frac{dy}{dx} = -1").scale(0.6 * z).move_to(info0)
        with self.voice(
            "At $x = -\\tfrac14$, the parabola's slope is $-1$: it falls at $45°$. The line falls at $26°34'$, "
            "so the two cross at $45° - 26°34'$, which is $18°26'$.",
            say="At x equals minus one quarter, the parabola's slope is minus 1: it falls at 45 degrees. "
                "The line falls at 26 degrees 34, so the two cross at 45 degrees, minus 26 degrees 34. That's 18 degrees, 26 minutes.",
        ) as v:
            self.play(ReplacementTransform(info0, info1), run_time=0.8)
            self.play(Create(ptan), run_time=1.0)
            self.wait(v.left(frac=0.45))
            self.play(Create(arc1), FadeIn(lab1), Create(lead1), run_time=v.left(minimum=1.0))
        self.wait(0.6)

        summary = VGroup(
            Tex(r"The tangent cuts $y = 2x^2+2$", color=WHITE).scale(0.7),
            MathTex(r"\text{at } x = 0: \; 26^\circ 34'").scale(0.75),
            MathTex(r"\text{at } x = -\tfrac14: \; 18^\circ 26'").scale(0.75),
        ).arrange(DOWN, buff=0.25).move_to([RX, -2.6, 0])
        with self.voice("Zoom back out, and that's the answer: the tangent cuts the parabola at $26°34'$ and at $18°26'$.",
                        say="Zoom back out, and that's the answer: the tangent cuts the parabola at 26 degrees 34 minutes, "
                            "and at 18 degrees 26 minutes.") as v:
            self.play(*[FadeOut(o) for o in (info1, lab0, lab1, lead1, arc0, arc1, horiz, ptan)], run_time=0.4)
            self.play(Restore(frame), *[m.animate.set_stroke(width=m.get_stroke_width() / z) for m in thin],
                      ax.animate.set_stroke(width=2, opacity=1),
                      d0.animate.scale(1 / z), d1.animate.scale(1 / z), run_time=2.2)
            self.play(Write(summary), run_time=v.left(minimum=1.0))
        self.wait(0.8)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch08TangentFromPoint(Narrated, Scene):
    chapter_title = "Example: a tangent from a point"

    def construct(self):
        self.section_card(8, "Worked example: a tangent from a point")

        f = lambda x: x**2 - 5 * x + 6
        ax = plain_axes([-0.5, 5.5, 1], [-2, 7.5, 1], 6.2, 6.6, ticks=True).to_edge(LEFT, buff=0.7).shift(0.1 * DOWN)
        letters = axes_letters(ax, o=False, x="x", y="y")
        nums = VGroup(*[MathTex(str(k)).scale(0.5).next_to(ax.c2p(k, 0), DOWN, buff=0.12) for k in range(1, 6)],
                      *[MathTex(str(k)).scale(0.5).next_to(ax.c2p(0, k), LEFT, buff=0.12) for k in (-1, 2, 4, 6)])
        curve = ax.plot(f, x_range=[-0.2, 5.2], color=CURVE, stroke_width=4)
        c_lab = MathTex(r"y = x^2 - 5x + 6", color=CURVE).scale(0.75).next_to(ax.c2p(4.6, f(4.6)), RIGHT, buff=0.15)
        A = Dot(ax.c2p(2, -1), color=POINT)
        A_lab = MathTex(r"(2,\,-1)").scale(0.65).next_to(A, RIGHT, buff=0.15)
        RX = 3.9
        prob = Tex(r"A straight line through $(2, -1)$ touches\\$y = x^2 - 5x + 6$. Where does it touch?").scale(0.68).move_to([RX, 3.3, 0])
        with self.voice(
            "Last example. A straight line is drawn through the point $(2, -1)$, as a tangent to the curve "
            "$y = x^2 - 5x + 6$. Where is the point of contact?",
            say="Last example. A straight line is drawn through the point 2, minus 1, as a tangent to the curve "
                "y equals x squared, minus 5 x, plus 6. Where is the point of contact?",
        ) as v:
            self.play(Create(ax), FadeIn(letters), FadeIn(nums), FadeIn(prob), run_time=1.6)
            self.play(Create(curve), FadeIn(c_lab), run_time=1.4)
            self.play(GrowFromCenter(A), FadeIn(A_lab), run_time=v.left(minimum=0.5))

        m = ValueTracker(-6.0)

        def clipped(slope):
            lo, hi = -0.5, 5.5
            for yb in (-2.0, 7.5):
                xb = 2 + (yb + 1) / slope if abs(slope) > 1e-6 else None
                if xb is None:
                    continue
                if slope > 0:
                    lo, hi = (max(lo, xb), hi) if yb < 0 else (lo, min(hi, xb))
                else:
                    lo, hi = (lo, min(hi, xb)) if yb < 0 else (max(lo, xb), hi)
            return [lo, hi]
        line = always_redraw(lambda: ax.plot(lambda x: m.get_value() * (x - 2) - 1, x_range=clipped(m.get_value()),
                                             color=TANGENT, stroke_width=3))

        def crossings():
            s = m.get_value()
            disc = (5 + s) ** 2 - 4 * (7 + 2 * s)
            g = VGroup()
            if disc >= 0:
                for sgn in (-1, 1):
                    xx = ((5 + s) + sgn * np.sqrt(disc)) / 2
                    g.add(Dot(ax.c2p(xx, f(xx)), color=RED_C, radius=0.07))
            return g
        hits = always_redraw(crossings)
        with self.voice(
            "Swing a line about that point. Most positions cut the curve twice, or miss it entirely. "
            "Only at two special angles does the line just touch."
        ) as v:
            self.play(Create(line), run_time=0.8)
            self.add(hits)
            self.play(m.animate.set_value(3.0), run_time=v.left(minimum=3.0), rate_func=smooth)
        card = self.ponder_card(r"Swing the line yourself", r"until it just grazes the curve.").move_to([RX, -1.4, 0])
        with self.voice("Your turn: swing the line until it just grazes the curve.") as v:
            self.play(m.animate.set_value(-0.8), FadeIn(card, shift=0.2 * UP), run_time=v.left(minimum=1.0))
        self.checkpoint("ch8-touch")
        self.play(FadeOut(card), FadeOut(hits), FadeOut(line), run_time=0.5)

        eqs = VGroup(
            MathTex(r"y = x^2 - 5x + 6", r"\quad(i)"),
            MathTex(r"y = ax + b", r"\quad(ii)"),
            MathTex(r"-1 = 2a + b", r"\quad(iii)"),
            MathTex(r"a = 2x - 5", r"\quad(iv)"),
        ).scale(0.72)
        for e in eqs:
            e[1].set_color(MUTED)
        eqs.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([RX, 1.0, 0])
        with self.voice(
            "Now the algebra. Write the line as $y = ax + b$. It passes through $(2, -1)$, and at the point of contact "
            "its slope $a$ must equal the curve's slope, $2x - 5$. Four equations in $a$, $b$, $x$ and $y$.",
            say="Now the algebra. Write the line as y equals a x plus b. It passes through 2, minus 1, and at the point "
                "of contact its slope, a, must equal the curve's slope, 2 x minus 5. Four equations, in a, b, x and y.",
        ) as v:
            self.play(FadeOut(prob), run_time=0.4)
            self.play(LaggedStart(*[Write(e) for e in eqs], lag_ratio=0.6), run_time=v.left(minimum=2.0))
        k1 = MathTex(r"x^2 - 5x + 6 = ax + b").scale(0.72)
        k2 = MathTex(r"x^2 - 5x + 6 = (2x-5)x - 1 - 2(2x-5)").scale(0.62)
        k3 = MathTex(r"x^2 - 4x + 3 = 0").scale(0.8)
        k4 = MathTex(r"(x-1)(x-3) = 0").scale(0.8)
        ks = VGroup(k1, k2, k3, k4).arrange(DOWN, buff=0.25).next_to(eqs, DOWN, buff=0.45)
        with self.voice(
            "Equations one and two give $x^2 - 5x + 6 = ax + b$. Replace $a$ by $2x - 5$, and $b$ by $-1 - 2a$.",
            say="Equations one and two give x squared minus 5 x plus 6 equals a x plus b. Replace a by 2 x minus 5, "
                "and b by minus 1, minus 2 a.",
        ) as v:
            self.play(Write(k1), run_time=1.4)
            self.wait(v.left(frac=0.4))
            self.play(Write(k2), run_time=v.left(minimum=1.0))
        with self.voice("It all simplifies to $x^2 - 4x + 3 = 0$, so $x = 1$, or $x = 3$.",
                        say="It all simplifies to x squared minus 4 x plus 3 equals zero. So x equals 1, or x equals 3.") as v:
            self.play(Write(k3), run_time=1.4)
            self.play(Write(k4), run_time=v.left(minimum=1.0))

        t1 = ax.plot(lambda x: -3 * (x - 2) - 1, x_range=clipped(-3), color=TANGENT, stroke_width=3)
        t2 = ax.plot(lambda x: 1 * (x - 2) - 1, x_range=clipped(1), color=TANGENT, stroke_width=3)
        c1, c2 = Dot(ax.c2p(1, 2), color=RED_C), Dot(ax.c2p(3, 0), color=RED_C)
        l1 = MathTex(r"(1,\,2)").scale(0.65).next_to(c1, UR, buff=0.06)
        l2 = MathTex(r"(3,\,0)").scale(0.65).next_to(c2, DR, buff=0.08)
        with self.voice(
            "Put these into the curve's equation and you get $y = 2$ and $y = 0$. Two tangents, touching at "
            "$(1, 2)$ and at $(3, 0)$.",
            say="Put these into the curve's equation and you get y equals 2, and y equals zero. Two tangents, "
                "touching at the points 1, 2, and 3, zero.",
        ) as v:
            self.play(Create(t1), Create(t2), run_time=1.6)
            self.play(GrowFromCenter(c1), GrowFromCenter(c2), FadeIn(l1), FadeIn(l2), run_time=v.left(minimum=1.0))
        with self.voice(
            "That's Thompson's advice for every exercise about curves: check your deductions by actually plotting the curves. "
            "Here the picture and the algebra agree."
        ) as v:
            self.play(Indicate(c1, scale_factor=1.6), Indicate(c2, scale_factor=1.6), run_time=v.left(minimum=1.0))
        self.wait(0.8)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=0.8)


# ════════════════════════════════════════════════════════════════════════
class Ch09Recap(Narrated, Scene):
    chapter_title = "Recap"

    def construct(self):
        self.section_card(9, "Recap")
        f = lambda x: x**3 / 3 - 2 * x**2 + 3 * x + 1
        df = lambda x: x**2 - 4 * x + 3
        ax = plain_axes([-0.7, 4.7], [-1.2, 4.6], 4.8, 3.4).to_edge(RIGHT, buff=0.6).shift(0.4 * DOWN)
        curve = ax.plot(f, x_range=[-0.6, 4.6], color=CURVE, stroke_width=4)
        x = ValueTracker(-0.5)
        dot = always_redraw(lambda: Dot(ax.c2p(x.get_value(), f(x.get_value())), color=POINT, radius=0.07))
        tan = always_redraw(lambda: tangent_line(ax, f, df, x.get_value(), 1.8))

        items = [
            (r"$\dfrac{dy}{dx}$ is the slope of the tangent at a point.",
             "d y by d x is the slope of the tangent to the curve, at a point."),
            (r"Rising: $\dfrac{dy}{dx} > 0$.\quad Falling: $\dfrac{dy}{dx} < 0$.",
             "Where the curve rises, it is positive; where it falls, negative."),
            (r"At a maximum or minimum, $\dfrac{dy}{dx} = 0$.",
             "At a maximum or a minimum, it is zero; though a maximum need not be the greatest value, nor a minimum the least."),
            (r"Straight line $y = ax+b$: constant slope $a$.",
             "A straight line, y equals a x plus b, has the constant slope a."),
            (r"Plot $\dfrac{dy}{dx}$ against $x$ to see how the steepness changes.",
             "And plotting d y by d x against x gives a picture of how the steepness changes."),
        ]
        rows = VGroup(*[Tex(t).scale(0.68) for t, _ in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        rows.to_edge(LEFT, buff=0.7).shift(0.2 * DOWN)
        bullets = VGroup(*[Dot(radius=0.05, color=POINT).next_to(r, LEFT, buff=0.22) for r in rows])
        self.play(Create(ax), Create(curve), FadeIn(dot), Create(tan), run_time=1.4)
        stops = [0.3, 2.0, 3.0, 3.8, 4.5]
        for (tex, spoken), row, bul, stop in zip(items, rows, bullets, stops):
            with self.voice(tex.replace(r"\dfrac", r"\frac").replace(r"\quad", " "), say=spoken) as v:
                self.play(FadeIn(bul), FadeIn(row, shift=0.15 * RIGHT), x.animate.set_value(stop), run_time=v.left(minimum=1.0))
        nxt = Tex(r"Now try \textbf{Exercises VIII} below the video.", color=POINT).scale(0.8).to_edge(DOWN, buff=0.45)
        with self.voice("That's the chapter. Now try your hand at Exercises Eight, just below the video.") as v:
            self.play(Write(nxt), run_time=v.left(minimum=1.0))
        self.wait(1.5)
        self.play(*[FadeOut(o) for o in self.mobjects], run_time=1.0)
