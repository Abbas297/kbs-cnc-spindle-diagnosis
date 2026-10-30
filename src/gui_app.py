"""
CNC Spindle & Process Fault Diagnosis — Desktop GUI
Knowledge-Based Systems (CT-359) — Complex Computing Problem (CCP)
NED University of Engineering & Technology

Visual Design: Industrial Control-Room Dashboard (ui-ux-pro-max + frontend-design)
Zero external dependencies: Python standard library + Tkinter only.
"""

import csv
import json
import math
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── DPI awareness for Windows 10/11 sharpness ────────────────────────────────
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inference_engine import (
    KnowledgeBase,
    diagnose,
    diagnose_telemetry,
    get_default_kb_path,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS  (every colour & font constant lives here)
# ═══════════════════════════════════════════════════════════════════════════════

BG            = "#0F172A"     # base background
CARD          = "#1E293B"     # card / panel surface
CARD_HOVER    = "#253349"     # subtle card hover lift
BORDER        = "#334155"     # structural borders
BORDER_LIGHT  = "#475569"     # lighter borders for internal dividers

TEXT          = "#E2E8F0"     # primary text
TEXT_MUTED    = "#94A3B8"     # secondary / labels
TEXT_DIM      = "#64748B"     # tertiary / footnotes
TEXT_DARK     = "#0F172A"     # text on bright backgrounds

GREEN         = "#22C55E"     # nominal / safe
GREEN_DIM     = "#166534"     # green background tint
AMBER         = "#F59E0B"     # warning
AMBER_DIM     = "#78350F"     # amber background tint
RED           = "#EF4444"     # fault / critical
RED_DIM       = "#7F1D1D"     # red background tint
CYAN          = "#38BDF8"     # info / rule IDs / telemetry
ORANGE        = "#F97316"     # primary CTA button
ORANGE_HOVER  = "#EA580C"     # button hover

GAUGE_TRACK   = "#1E293B"     # gauge empty arc
GAUGE_SIZE    = 140           # gauge canvas dimension

FONT          = "Segoe UI"
MONO          = "Consolas"

# Type scale
H1_SIZE       = 16
H2_SIZE       = 12
BODY          = 10
SMALL         = 9
TINY          = 8
VALUE_SIZE    = 14            # large numeric readouts

# Spacing
PAD           = 16
PAD_SM        = 8
PAD_XS        = 4
RADIUS        = 8             # card corner radius


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITY: rounded-rectangle on Canvas
# ═══════════════════════════════════════════════════════════════════════════════

def rounded_rect(canvas, x1, y1, x2, y2, r=RADIUS, **kw):
    """Draw a rounded rectangle on a Canvas. Returns the item id."""
    pts = [
        x1+r, y1,  x2-r, y1,  x2, y1,  x2, y1+r,
        x2, y2-r,  x2, y2,  x2-r, y2,  x1+r, y2,
        x1, y2,  x1, y2-r,  x1, y1+r,  x1, y1,  x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ═══════════════════════════════════════════════════════════════════════════════
#  WIDGET: Animated Precision Gauge
# ═══════════════════════════════════════════════════════════════════════════════

class AnimatedGauge(tk.Canvas):
    """Arc gauge with smooth animation, threshold markers, and colour transitions."""

    ARC_START  = 135
    ARC_EXTENT = 270  # degrees of sweep

    def __init__(self, parent, title="", unit="", min_v=0, max_v=100,
                 safe_label="", crit_lo=None, crit_hi=None, warn_hi=None,
                 limit_marker=None, **kw):
        super().__init__(parent, width=GAUGE_SIZE, height=GAUGE_SIZE + 42,
                         bg=CARD, highlightthickness=0, **kw)
        self.title = title
        self.unit = unit
        self.min_v = float(min_v)
        self.max_v = float(max_v)
        self.safe_label = safe_label
        self.crit_lo = crit_lo
        self.crit_hi = crit_hi
        self.warn_hi = warn_hi
        self.limit_marker = limit_marker   # value at which to draw a tick
        self._display_val = self.min_v
        self._target_val  = self.min_v
        self._animating = False
        self._draw()

    def set_value(self, val):
        self._target_val = float(val)
        if not self._animating:
            self._animating = True
            self._animate_step()

    def _animate_step(self):
        diff = self._target_val - self._display_val
        if abs(diff) < 0.5:
            self._display_val = self._target_val
            self._animating = False
            self._draw()
            return
        self._display_val += diff * 0.25
        self._draw()
        self.after(16, self._animate_step)

    def _color(self, val):
        if self.crit_lo is not None and val < self.crit_lo:
            return RED
        if self.crit_hi is not None and val > self.crit_hi:
            return RED
        if self.warn_hi is not None and val >= self.warn_hi:
            return AMBER
        return GREEN

    def _draw(self):
        self.delete("all")
        cx = GAUGE_SIZE // 2
        cy = GAUGE_SIZE // 2
        r = 52
        arc_w = 10
        pad = cx - r

        # Background track
        self.create_arc(pad, cy - r, pad + 2*r, cy + r,
                        start=self.ARC_START, extent=self.ARC_EXTENT,
                        style="arc", outline=BORDER, width=arc_w)

        # Value arc
        val = self._display_val
        clamped = max(self.min_v, min(self.max_v, val))
        span = max(0.001, self.max_v - self.min_v)
        frac = (clamped - self.min_v) / span
        ext = frac * self.ARC_EXTENT
        color = self._color(val)

        if ext > 1:
            self.create_arc(pad, cy - r, pad + 2*r, cy + r,
                            start=self.ARC_START, extent=ext,
                            style="arc", outline=color, width=arc_w)

        # Limit marker tick
        if self.limit_marker is not None:
            lm_frac = (self.limit_marker - self.min_v) / span
            lm_angle = math.radians(self.ARC_START + lm_frac * self.ARC_EXTENT)
            mx1 = cx - (r - arc_w//2) * math.cos(lm_angle)
            my1 = cy - (r - arc_w//2) * math.sin(lm_angle)
            mx2 = cx - (r + arc_w//2 + 4) * math.cos(lm_angle)
            my2 = cy - (r + arc_w//2 + 4) * math.sin(lm_angle)
            self.create_line(mx1, my1, mx2, my2, fill=RED, width=2)

        # Value text (large)
        if abs(val) >= 10000:
            vs = f"{val/1000:.1f}k"
        elif abs(val) >= 1000:
            vs = f"{val:,.0f}"
        else:
            vs = f"{val:.1f}" if isinstance(val, float) and val != int(val) else f"{int(val)}"
        self.create_text(cx, cy - 2, text=vs, fill=color,
                         font=(MONO, VALUE_SIZE, "bold"))

        # Unit
        self.create_text(cx, cy + 20, text=self.unit, fill=TEXT_MUTED,
                         font=(FONT, TINY))

        # Title below
        self.create_text(cx, GAUGE_SIZE + 8, text=self.title, fill=TEXT,
                         font=(FONT, SMALL, "bold"))
        self.create_text(cx, GAUGE_SIZE + 26, text=self.safe_label, fill=TEXT_DIM,
                         font=(FONT, TINY))


# ═══════════════════════════════════════════════════════════════════════════════
#  WIDGET: Custom Canvas Slider
# ═══════════════════════════════════════════════════════════════════════════════

class CanvasSlider(tk.Frame):
    """Custom drawn slider: thin track, round handle, value readout on the right.
       Track turns red when the value crosses a rule limit."""

    def __init__(self, parent, label="", min_v=0, max_v=100, init_v=0, step=0.1,
                 crit_lo=None, crit_hi=None, warn_hi=None,
                 on_change=None, fmt=".1f", **kw):
        super().__init__(parent, bg=CARD, **kw)
        self.min_v = float(min_v)
        self.max_v = float(max_v)
        self._val = float(init_v)
        self.step = step
        self.crit_lo = crit_lo
        self.crit_hi = crit_hi
        self.warn_hi = warn_hi
        self.on_change = on_change
        self.fmt = fmt
        self._dragging = False

        # Label row
        top = tk.Frame(self, bg=CARD)
        top.pack(fill=tk.X)
        tk.Label(top, text=label, bg=CARD, fg=TEXT_MUTED,
                 font=(FONT, TINY, "bold")).pack(side=tk.LEFT)
        self._val_label = tk.Label(top, text=self._format(self._val), bg=CARD,
                                    fg=CYAN, font=(MONO, SMALL, "bold"))
        self._val_label.pack(side=tk.RIGHT)

        # Canvas track
        self._track_h = 24
        self._canvas = tk.Canvas(self, height=self._track_h, bg=CARD,
                                  highlightthickness=0, cursor="hand2")
        self._canvas.pack(fill=tk.X, pady=(2, 0))
        self._canvas.bind("<Configure>", self._on_resize)
        self._canvas.bind("<Button-1>", self._on_click)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

    def _format(self, v):
        return f"{v:{self.fmt}}"

    def get(self):
        return self._val

    def set(self, v):
        self._val = max(self.min_v, min(self.max_v, float(v)))
        self._val_label.config(text=self._format(self._val))
        self._redraw()

    def _track_color(self):
        v = self._val
        if self.crit_lo is not None and v < self.crit_lo:
            return RED
        if self.crit_hi is not None and v > self.crit_hi:
            return RED
        if self.warn_hi is not None and v >= self.warn_hi:
            return AMBER
        return CYAN

    def _redraw(self):
        c = self._canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 10:
            return
        margin = 10
        track_y = self._track_h // 2
        track_left = margin
        track_right = w - margin

        # Full track (thin)
        c.create_line(track_left, track_y, track_right, track_y,
                      fill=BORDER, width=3, capstyle="round")

        # Filled portion
        span = max(0.001, self.max_v - self.min_v)
        frac = (self._val - self.min_v) / span
        fill_x = track_left + frac * (track_right - track_left)

        tc = self._track_color()
        c.create_line(track_left, track_y, fill_x, track_y,
                      fill=tc, width=3, capstyle="round")

        # Handle (circle)
        hr = 7
        c.create_oval(fill_x - hr, track_y - hr, fill_x + hr, track_y + hr,
                      fill=tc, outline="", tags="handle")

    def _on_resize(self, e):
        self._redraw()

    def _x_to_val(self, x):
        w = self._canvas.winfo_width()
        margin = 10
        frac = (x - margin) / max(1, w - 2*margin)
        frac = max(0, min(1, frac))
        return self.min_v + frac * (self.max_v - self.min_v)

    def _on_click(self, e):
        self._dragging = True
        self._update_from_x(e.x)

    def _on_drag(self, e):
        if self._dragging:
            self._update_from_x(e.x)

    def _on_release(self, e):
        self._dragging = False

    def _update_from_x(self, x):
        v = self._x_to_val(x)
        # Snap to step
        v = round(v / self.step) * self.step
        self._val = max(self.min_v, min(self.max_v, v))
        self._val_label.config(text=self._format(self._val))
        self._redraw()
        if self.on_change:
            self.on_change()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CNC Fault Diagnosis — KBS (CT-359)")
        self.root.geometry("1280x820")
        self.root.minsize(1280, 720)
        self.root.configure(bg=BG)

        self.rules_path = get_default_kb_path()
        self.kb = KnowledgeBase(self.rules_path)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.csv_path = os.path.join(base, "knowledge_base", "ai4i2020.csv")

        self.symptom_vars = {}
        self._active_tab = 0
        self._rule_detail_widgets = []

        self._build_header()
        self._build_tab_bar()
        self._build_tab_frames()
        self._show_tab(0)

        # Load row 1 on startup
        self._load_csv_row(1)

    # ──────────────────────────────────────────────────────────────────────────
    #  HEADER: title + status banner
    # ──────────────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG, padx=PAD, pady=PAD_SM)
        hdr.pack(fill=tk.X)

        # Title
        tk.Label(hdr, text="CNC Spindle & Process Fault Diagnosis",
                 bg=BG, fg=TEXT, font=(FONT, H1_SIZE, "bold")).pack(side=tk.LEFT)

        # Status badge (right side)
        self.status_frame = tk.Frame(hdr, bg=GREEN_DIM, padx=PAD, pady=PAD_XS)
        self.status_frame.pack(side=tk.RIGHT)
        self.status_label = tk.Label(self.status_frame, text="NOMINAL",
                                      bg=GREEN_DIM, fg=GREEN,
                                      font=(MONO, H2_SIZE, "bold"))
        self.status_label.pack()

    # ──────────────────────────────────────────────────────────────────────────
    #  CUSTOM SEGMENTED TAB BAR (replaces ttk.Notebook)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_tab_bar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill=tk.X, padx=PAD)

        self.tab_names = [
            "Sensor Telemetry",
            "Operator Symptoms",
            "Knowledge Base",
            "Dataset Benchmark",
        ]
        self.tab_btns = []
        self.tab_underlines = []

        for i, name in enumerate(self.tab_names):
            col = tk.Frame(bar, bg=BG)
            col.pack(side=tk.LEFT, padx=(0, PAD))

            btn = tk.Label(col, text=name, bg=BG, fg=TEXT_MUTED,
                           font=(FONT, BODY, "bold"), cursor="hand2",
                           padx=PAD_XS, pady=PAD_SM)
            btn.pack()
            btn.bind("<Button-1>", lambda e, idx=i: self._show_tab(idx))
            self.tab_btns.append(btn)

            underline = tk.Frame(col, bg=BG, height=3)
            underline.pack(fill=tk.X)
            self.tab_underlines.append(underline)

        # Thin border below tab bar
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

    def _show_tab(self, idx):
        self._active_tab = idx
        for i, (btn, ul) in enumerate(zip(self.tab_btns, self.tab_underlines)):
            if i == idx:
                btn.config(fg=TEXT)
                ul.config(bg=CYAN)
            else:
                btn.config(fg=TEXT_MUTED)
                ul.config(bg=BG)
        for i, f in enumerate(self.tab_frames):
            if i == idx:
                f.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=(PAD_SM, PAD))
            else:
                f.pack_forget()

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB FRAMES
    # ──────────────────────────────────────────────────────────────────────────
    def _build_tab_frames(self):
        self.tab_frames = [tk.Frame(self.root, bg=BG) for _ in range(4)]
        self._build_telemetry_tab(self.tab_frames[0])
        self._build_symptoms_tab(self.tab_frames[1])
        self._build_rules_tab(self.tab_frames[2])
        self._build_bench_tab(self.tab_frames[3])

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 0 — SENSOR TELEMETRY
    # ══════════════════════════════════════════════════════════════════════════
    def _build_telemetry_tab(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        # ── Left sidebar (370 px) ──
        left = tk.Frame(wrap, bg=CARD, width=370,
                        highlightbackground=BORDER, highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, PAD_SM))
        left.pack_propagate(False)

        # Row navigator
        self._card_heading(left, "Dataset row")
        rf = tk.Frame(left, bg=CARD)
        rf.pack(fill=tk.X, padx=PAD, pady=(0, PAD_XS))

        self.var_row = tk.StringVar(value="1")
        ent = tk.Entry(rf, textvariable=self.var_row, width=7, justify="center",
                       bg=BG, fg=GREEN, insertbackground=GREEN,
                       font=(MONO, BODY, "bold"), bd=0, relief="flat")
        ent.pack(side=tk.LEFT)
        ent.bind("<Return>", lambda e: self._load_csv_row(int(self.var_row.get())))

        for txt, delta in [("◀", -1), ("▶", 1)]:
            b = tk.Label(rf, text=txt, bg=BORDER, fg=TEXT, font=(FONT, BODY, "bold"),
                         padx=8, pady=2, cursor="hand2")
            b.pack(side=tk.LEFT, padx=2)
            b.bind("<Button-1>", lambda e, d=delta: self._step_row(d))

        self._make_button(rf, "Load", GREEN_DIM, GREEN,
                          lambda: self._load_csv_row(int(self.var_row.get())),
                          side=tk.LEFT, padx=(6, 0))

        self.lbl_row_info = tk.Label(left, text="", bg=CARD, fg=TEXT_MUTED,
                                      font=(FONT, TINY, "italic"))
        self.lbl_row_info.pack(anchor=tk.W, padx=PAD, pady=(0, PAD_SM))

        self._divider(left)

        # Presets
        self._card_heading(left, "Benchmark scenarios")
        pg = tk.Frame(left, bg=CARD)
        pg.pack(fill=tk.X, padx=PAD, pady=(0, PAD_SM))
        presets = [
            ("Nominal", "normal"), ("HDF", "hdf"), ("PWF↑", "pwf_high"),
            ("PWF↓", "pwf_low"), ("OSF", "osf"), ("TWF", "twf"),
        ]
        for i, (lbl, key) in enumerate(presets):
            r, c = i // 3, i % 3
            b = tk.Label(pg, text=lbl, bg=BG, fg=TEXT_MUTED, font=(FONT, TINY, "bold"),
                         padx=10, pady=4, cursor="hand2")
            b.grid(row=r, column=c, padx=2, pady=2, sticky="ew")
            b.bind("<Button-1>", lambda e, k=key: self._load_preset(k))
            b.bind("<Enter>", lambda e, w=b: w.config(bg=BORDER))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=BG))
        for c in range(3):
            pg.columnconfigure(c, weight=1)

        self._divider(left)

        # Sliders
        self._card_heading(left, "Sensor readings")

        self.sl_air = CanvasSlider(left, "Air temperature [K]", 290, 310, 298.1, 0.1,
                                    on_change=self._on_slider, fmt=".1f")
        self.sl_air.pack(fill=tk.X, padx=PAD, pady=2)

        self.sl_proc = CanvasSlider(left, "Process temperature [K]", 300, 320, 308.6, 0.1,
                                     on_change=self._on_slider, fmt=".1f")
        self.sl_proc.pack(fill=tk.X, padx=PAD, pady=2)

        self.sl_speed = CanvasSlider(left, "Rotational speed [rpm]", 1100, 2900, 1551, 1,
                                      on_change=self._on_slider, fmt=".0f")
        self.sl_speed.pack(fill=tk.X, padx=PAD, pady=2)

        self.sl_torque = CanvasSlider(left, "Spindle torque [Nm]", 3, 80, 42.8, 0.1,
                                       on_change=self._on_slider, fmt=".1f")
        self.sl_torque.pack(fill=tk.X, padx=PAD, pady=2)

        self.sl_tw = CanvasSlider(left, "Tool wear [min]", 0, 260, 0, 1,
                                   warn_hi=200, on_change=self._on_slider, fmt=".0f")
        self.sl_tw.pack(fill=tk.X, padx=PAD, pady=2)

        # Product type
        tf = tk.Frame(left, bg=CARD)
        tf.pack(fill=tk.X, padx=PAD, pady=4)
        tk.Label(tf, text="Product type", bg=CARD, fg=TEXT_MUTED,
                 font=(FONT, TINY, "bold")).pack(side=tk.LEFT)
        self.var_type = tk.StringVar(value="M")
        for t in ["L", "M", "H"]:
            b = tk.Radiobutton(tf, text=t, variable=self.var_type, value=t,
                               bg=CARD, fg=TEXT, selectcolor=BG, activebackground=CARD,
                               font=(FONT, SMALL, "bold"), indicatoron=0, padx=10, pady=2,
                               relief="flat", bd=0, command=self._on_slider)
            b.pack(side=tk.RIGHT, padx=2)

        # Spacer
        tk.Frame(left, bg=CARD).pack(fill=tk.Y, expand=True)

        # Buttons
        self._make_button(left, "Run diagnosis", ORANGE, "#fff",
                          self._run_telemetry, fill_x=True, padx=PAD, pady=(PAD_XS, PAD_XS),
                          font_size=BODY)
        self._make_button(left, "Reset inputs", BG, TEXT_MUTED,
                          lambda: self._load_preset("normal"),
                          fill_x=True, padx=PAD, pady=(0, PAD))

        # ── Right main area ──
        right = tk.Frame(wrap, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Gauge strip
        self._build_gauges(right)

        # Result cards
        self.tel_results_frame = tk.Frame(right, bg=BG)
        self.tel_results_frame.pack(fill=tk.BOTH, expand=True)
        self._build_empty_state(self.tel_results_frame,
                                "Adjust sensors or load a dataset row, then press Run diagnosis.")

    def _build_gauges(self, parent):
        strip = tk.Frame(parent, bg=CARD,
                         highlightbackground=BORDER, highlightthickness=1)
        strip.pack(fill=tk.X, pady=(0, PAD_SM))

        self.gauge_dt = AnimatedGauge(strip, "Thermal ΔT", "K",
                                       0, 20, "Safe ≥ 8.6 K", crit_lo=8.6, limit_marker=8.6)
        self.gauge_dt.pack(side=tk.LEFT, padx=PAD_SM, pady=PAD_SM)

        self.gauge_pw = AnimatedGauge(strip, "Drive Power", "W",
                                       0, 12000, "3.5k – 9.0k W",
                                       crit_lo=3500, crit_hi=9000,
                                       limit_marker=9000)
        self.gauge_pw.pack(side=tk.LEFT, padx=PAD_SM, pady=PAD_SM)

        self.gauge_os = AnimatedGauge(strip, "Overstrain", "min·Nm",
                                       0, 16000, "Limit varies by type",
                                       crit_hi=12000, limit_marker=12000)
        self.gauge_os.pack(side=tk.LEFT, padx=PAD_SM, pady=PAD_SM)

        self.gauge_tw = AnimatedGauge(strip, "Tool Wear", "min",
                                       0, 260, "Safe < 200 min",
                                       warn_hi=200, limit_marker=200)
        self.gauge_tw.pack(side=tk.LEFT, padx=PAD_SM, pady=PAD_SM)

        # Machine state summary
        sf = tk.Frame(strip, bg=CARD, padx=PAD)
        sf.pack(side=tk.RIGHT, fill=tk.Y, pady=PAD)
        tk.Label(sf, text="MACHINE STATE", bg=CARD, fg=TEXT_DIM,
                 font=(FONT, TINY, "bold")).pack(anchor=tk.E)
        self.lbl_state = tk.Label(sf, text="NOMINAL", bg=CARD, fg=GREEN,
                                   font=(MONO, H1_SIZE, "bold"))
        self.lbl_state.pack(anchor=tk.E, pady=(2, 0))
        self.lbl_state_sub = tk.Label(sf, text="All readings nominal", bg=CARD, fg=TEXT_MUTED,
                                       font=(FONT, TINY))
        self.lbl_state_sub.pack(anchor=tk.E)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — OPERATOR SYMPTOMS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_symptoms_tab(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Top: 2x3 symptom chip grid
        chip_frame = tk.Frame(wrap, bg=BG)
        chip_frame.pack(fill=tk.X, pady=(0, PAD_SM))

        symptoms = [
            ("unusual_noise",               "Unusual noise / chatter"),
            ("high_vibration",              "High vibration levels"),
            ("spindle_overheating",         "Bearing overheating"),
            ("poor_surface_finish",         "Poor surface finish"),
            ("increased_power_consumption", "Increased power draw"),
            ("metal_particles_in_oil",      "Metal particles in oil"),
        ]
        self._symptom_chips = {}
        for i, (sid, label) in enumerate(symptoms):
            var = tk.BooleanVar(value=False)
            self.symptom_vars[sid] = var
            r, c = i // 3, i % 3
            chip = tk.Frame(chip_frame, bg=CARD, padx=PAD, pady=PAD,
                            highlightbackground=BORDER, highlightthickness=1,
                            cursor="hand2")
            chip.grid(row=r, column=c, padx=PAD_XS, pady=PAD_XS, sticky="nsew")

            lbl = tk.Label(chip, text=label, bg=CARD, fg=TEXT_MUTED,
                           font=(FONT, BODY, "bold"), wraplength=200, justify=tk.LEFT)
            lbl.pack(anchor=tk.W)

            self._symptom_chips[sid] = (chip, lbl, var)

            for w in (chip, lbl):
                w.bind("<Button-1>", lambda e, s=sid: self._toggle_symptom(s))

        for c in range(3):
            chip_frame.columnconfigure(c, weight=1)
        for r in range(2):
            chip_frame.rowconfigure(r, weight=0)

        # Buttons
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, PAD_SM))
        self._make_button(btn_row, "Run diagnosis", ORANGE, "#fff",
                          self._run_symptoms, side=tk.LEFT, font_size=BODY)
        self._make_button(btn_row, "Clear all", BG, TEXT_MUTED,
                          self._clear_symptoms, side=tk.LEFT, padx=(PAD_SM, 0))

        # Results area
        self.sym_results_frame = tk.Frame(wrap, bg=BG)
        self.sym_results_frame.pack(fill=tk.BOTH, expand=True)
        self._build_empty_state(self.sym_results_frame,
                                "Select symptoms from the chips above, then press Run diagnosis.")

    def _toggle_symptom(self, sid):
        chip, lbl, var = self._symptom_chips[sid]
        new_val = not var.get()
        var.set(new_val)
        if new_val:
            chip.config(highlightbackground=CYAN, highlightthickness=2, bg=BG)
            lbl.config(bg=BG, fg=TEXT)
        else:
            chip.config(highlightbackground=BORDER, highlightthickness=1, bg=CARD)
            lbl.config(bg=CARD, fg=TEXT_MUTED)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — KNOWLEDGE BASE (RULE VIEWER)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_rules_tab(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Top controls
        ctrl = tk.Frame(wrap, bg=CARD, padx=PAD, pady=PAD_SM,
                        highlightbackground=BORDER, highlightthickness=1)
        ctrl.pack(fill=tk.X, pady=(0, PAD_SM))

        # Filter chips
        self.rule_filter = tk.StringVar(value="All")
        for mode in ["All", "Telemetry", "Bearings"]:
            b = tk.Radiobutton(ctrl, text=mode, variable=self.rule_filter, value=mode,
                               bg=CARD, fg=TEXT, selectcolor=BG, activebackground=CARD,
                               font=(FONT, SMALL), indicatoron=0, padx=12, pady=4,
                               relief="flat", bd=0, command=self._populate_rules)
            b.pack(side=tk.LEFT, padx=2)

        # Search
        tk.Label(ctrl, text="Search:", bg=CARD, fg=TEXT_MUTED,
                 font=(FONT, SMALL)).pack(side=tk.LEFT, padx=(PAD, PAD_XS))
        self.rule_search_var = tk.StringVar()
        se = tk.Entry(ctrl, textvariable=self.rule_search_var, width=24,
                      bg=BG, fg=GREEN, insertbackground=GREEN,
                      font=(MONO, SMALL), bd=0)
        se.pack(side=tk.LEFT)
        se.bind("<KeyRelease>", lambda e: self._populate_rules())

        # Paned: tree on left, detail on right
        paned = tk.PanedWindow(wrap, orient=tk.HORIZONTAL, bg=BORDER,
                               sashwidth=3, sashrelief="flat")
        paned.pack(fill=tk.BOTH, expand=True)

        # Treeview
        tree_frame = tk.Frame(paned, bg=CARD)

        style = ttk.Style()
        style.configure("Rules.Treeview", background=CARD, foreground=TEXT,
                        fieldbackground=CARD, font=(FONT, SMALL), rowheight=28,
                        borderwidth=0)
        style.configure("Rules.Treeview.Heading", background=BG, foreground=CYAN,
                        font=(FONT, SMALL, "bold"), relief="flat")
        style.map("Rules.Treeview", background=[("selected", BORDER_LIGHT)])

        cols = ("id", "module", "type", "conditions", "conclusion", "cf")
        self.rule_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                       selectmode="browse", style="Rules.Treeview")
        self.rule_tree.heading("id", text="Rule")
        self.rule_tree.heading("module", text="Module")
        self.rule_tree.heading("type", text="Type")
        self.rule_tree.heading("conditions", text="IF (Antecedent)")
        self.rule_tree.heading("conclusion", text="THEN (Consequent)")
        self.rule_tree.heading("cf", text="CF")

        self.rule_tree.column("id", width=50, minwidth=50, anchor=tk.CENTER)
        self.rule_tree.column("module", width=100, minwidth=80)
        self.rule_tree.column("type", width=60, minwidth=50, anchor=tk.CENTER)
        self.rule_tree.column("conditions", width=280, minwidth=180)
        self.rule_tree.column("conclusion", width=200, minwidth=120)
        self.rule_tree.column("cf", width=50, minwidth=40, anchor=tk.CENTER)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rule_tree.yview)
        self.rule_tree.configure(yscrollcommand=sb.set)
        self.rule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.rule_tree.bind("<<TreeviewSelect>>", self._on_rule_select)
        self.rule_tree.tag_configure("stripe", background=BG)

        paned.add(tree_frame, minsize=500)

        # Detail panel
        self.rule_detail_frame = tk.Frame(paned, bg=CARD, padx=PAD, pady=PAD)
        paned.add(self.rule_detail_frame, minsize=300)

        self._build_empty_state(self.rule_detail_frame,
                                "Select a rule from the table to view its full detail.")

        self._populate_rules()

    def _populate_rules(self):
        self.rule_tree.delete(*self.rule_tree.get_children())
        filt = self.rule_filter.get()
        kw = self.rule_search_var.get().lower().strip()

        for i, r in enumerate(self.kb.rules):
            rid = r.get("id", "")
            r_num = int(rid.replace("R", ""))

            if r_num >= 14:
                mod = "Telemetry"
            else:
                mod = "Bearings"

            if filt == "Telemetry" and mod != "Telemetry":
                continue
            if filt == "Bearings" and mod != "Bearings":
                continue

            # Determine rule type and build THEN text
            if "then_fault" in r:
                rtype = "Fault"
                then_text = f"fault: {r['then_fault']}"
            elif "then_action" in r:
                rtype = "Action"
                aid = r["then_action"]
                ainfo = self.kb.actions.get(aid, {})
                then_text = f"action: [{aid}] {ainfo.get('name', aid)}"
            elif "then_safety" in r:
                rtype = "Safety"
                then_text = f"safety: {r['then_safety'][:60]}..."
            else:
                rtype = "?"
                then_text = "?"

            cond_text = " AND ".join(r.get("if", []))
            cf = r.get("cf", 1.0)

            combined = f"{rid} {mod} {cond_text} {then_text} {r.get('why','')}".lower()
            if kw and kw not in combined:
                continue

            tag = "stripe" if i % 2 == 0 else ""
            self.rule_tree.insert("", tk.END, iid=rid,
                                   values=(rid, mod, rtype, cond_text, then_text, f"{cf:.2f}"),
                                   tags=(tag,))

    def _on_rule_select(self, event):
        sel = self.rule_tree.selection()
        if not sel:
            return
        rid = sel[0]
        rule = None
        for r in self.kb.rules:
            if r.get("id") == rid:
                rule = r
                break
        if not rule:
            return

        # Clear detail
        for w in self.rule_detail_frame.winfo_children():
            w.destroy()

        # Build detail card
        tk.Label(self.rule_detail_frame, text=f"Rule {rid}",
                 bg=CARD, fg=CYAN, font=(FONT, H2_SIZE, "bold")).pack(anchor=tk.W)

        self._divider(self.rule_detail_frame)

        # IF
        tk.Label(self.rule_detail_frame, text="IF (Antecedent Conditions):",
                 bg=CARD, fg=TEXT_MUTED, font=(FONT, SMALL, "bold")).pack(anchor=tk.W, pady=(PAD_SM, 2))
        for cond in rule.get("if", []):
            tk.Label(self.rule_detail_frame, text=f"  • {cond}",
                     bg=CARD, fg=TEXT, font=(FONT, BODY)).pack(anchor=tk.W)

        # THEN
        tk.Label(self.rule_detail_frame, text="THEN (Consequent):",
                 bg=CARD, fg=TEXT_MUTED, font=(FONT, SMALL, "bold")).pack(anchor=tk.W, pady=(PAD_SM, 2))
        if "then_fault" in rule:
            tk.Label(self.rule_detail_frame, text=f"  Conclude fault: {rule['then_fault']}",
                     bg=CARD, fg=AMBER, font=(FONT, BODY, "bold")).pack(anchor=tk.W)
        elif "then_action" in rule:
            aid = rule["then_action"]
            ainfo = self.kb.actions.get(aid, {})
            tk.Label(self.rule_detail_frame,
                     text=f"  Recommend action [{aid}]: {ainfo.get('name', aid)}",
                     bg=CARD, fg=GREEN, font=(FONT, BODY, "bold")).pack(anchor=tk.W)
        elif "then_safety" in rule:
            tk.Label(self.rule_detail_frame, text=f"  {rule['then_safety']}",
                     bg=CARD, fg=RED, font=(FONT, BODY, "bold"), wraplength=350,
                     justify=tk.LEFT).pack(anchor=tk.W)

        # CF
        tk.Label(self.rule_detail_frame, text=f"Certainty Factor: {rule.get('cf', 1.0):.2f}",
                 bg=CARD, fg=CYAN, font=(MONO, BODY, "bold")).pack(anchor=tk.W, pady=(PAD_SM, 0))

        # Rationale
        tk.Label(self.rule_detail_frame, text="Engineering Rationale:",
                 bg=CARD, fg=TEXT_MUTED, font=(FONT, SMALL, "bold")).pack(anchor=tk.W, pady=(PAD_SM, 2))
        tk.Label(self.rule_detail_frame, text=rule.get("why", ""),
                 bg=CARD, fg=TEXT, font=(FONT, BODY), wraplength=350,
                 justify=tk.LEFT).pack(anchor=tk.W)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — DATASET BENCHMARK
    # ══════════════════════════════════════════════════════════════════════════
    def _build_bench_tab(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Top card
        top = tk.Frame(wrap, bg=CARD, padx=PAD, pady=PAD,
                       highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill=tk.X, pady=(0, PAD_SM))

        tk.Label(top, text="AI4I 2020 Dataset Validation Suite",
                 bg=CARD, fg=TEXT, font=(FONT, H2_SIZE, "bold")).pack(anchor=tk.W)
        tk.Label(top, text="Evaluates 10,000 CNC milling cycles against the forward-chaining rule engine.",
                 bg=CARD, fg=TEXT_MUTED, font=(FONT, SMALL)).pack(anchor=tk.W, pady=(2, PAD_SM))

        btn_row = tk.Frame(top, bg=CARD)
        btn_row.pack(anchor=tk.W)
        self._make_button(btn_row, "Run 10,000-row validation", ORANGE, "#fff",
                          self._run_batch, side=tk.LEFT, font_size=BODY)

        self.bench_progress_var = tk.DoubleVar(value=0)
        self.bench_progress = ttk.Progressbar(top, variable=self.bench_progress_var,
                                               maximum=100, length=300)
        self.bench_progress.pack(anchor=tk.W, pady=(PAD_SM, 0))

        # Result tiles frame
        self.bench_tiles_frame = tk.Frame(wrap, bg=BG)
        self.bench_tiles_frame.pack(fill=tk.X, pady=(0, PAD_SM))

        # Collapsible raw log
        self.bench_log_visible = tk.BooleanVar(value=False)
        log_toggle = tk.Label(wrap, text="▶ Show raw output log", bg=BG, fg=CYAN,
                               font=(FONT, SMALL, "bold"), cursor="hand2")
        log_toggle.pack(anchor=tk.W)
        log_toggle.bind("<Button-1>", lambda e: self._toggle_bench_log(log_toggle))

        self.bench_log_frame = tk.Frame(wrap, bg=BG)
        # Initially hidden
        self.bench_log_text = scrolledtext.ScrolledText(
            self.bench_log_frame, font=(MONO, SMALL), bg=BG, fg=TEXT_MUTED,
            bd=0, height=12, insertbackground=TEXT
        )
        self.bench_log_text.pack(fill=tk.BOTH, expand=True)

    def _toggle_bench_log(self, toggle_label):
        if self.bench_log_visible.get():
            self.bench_log_frame.pack_forget()
            toggle_label.config(text="▶ Show raw output log")
            self.bench_log_visible.set(False)
        else:
            self.bench_log_frame.pack(fill=tk.BOTH, expand=True, pady=(PAD_XS, 0))
            toggle_label.config(text="▼ Hide raw output log")
            self.bench_log_visible.set(True)

    # ──────────────────────────────────────────────────────────────────────────
    #  UI HELPER WIDGETS
    # ──────────────────────────────────────────────────────────────────────────
    def _card_heading(self, parent, text):
        f = tk.Frame(parent, bg=CARD)
        f.pack(fill=tk.X, padx=PAD, pady=(PAD_SM, PAD_XS))
        tk.Frame(f, bg=ORANGE, width=3, height=12).pack(side=tk.LEFT, padx=(0, PAD_SM))
        tk.Label(f, text=text, bg=CARD, fg=TEXT_MUTED,
                 font=(FONT, TINY, "bold")).pack(side=tk.LEFT)

    def _divider(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=PAD, pady=PAD_XS)

    def _make_button(self, parent, text, bg_color, fg_color, cmd,
                     side=None, fill_x=False, padx=0, pady=0, font_size=SMALL):
        b = tk.Label(parent, text=text, bg=bg_color, fg=fg_color,
                     font=(FONT, font_size, "bold"), padx=PAD, pady=PAD_XS,
                     cursor="hand2")
        if fill_x:
            b.pack(fill=tk.X, padx=padx, pady=pady)
        elif side:
            b.pack(side=side, padx=padx, pady=pady)
        else:
            b.pack(padx=padx, pady=pady)
        b.bind("<Button-1>", lambda e: cmd())
        hover_bg = ORANGE_HOVER if bg_color == ORANGE else BORDER
        b.bind("<Enter>", lambda e: b.config(bg=hover_bg))
        b.bind("<Leave>", lambda e: b.config(bg=bg_color))
        return b

    def _build_empty_state(self, parent, text):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill=tk.BOTH, expand=True)
        tk.Label(f, text="—", bg=BG, fg=TEXT_DIM, font=(FONT, 24)).pack(pady=(40, 4))
        tk.Label(f, text=text, bg=BG, fg=TEXT_DIM, font=(FONT, BODY)).pack()
        return f

    # ──────────────────────────────────────────────────────────────────────────
    #  RESULT RENDERING
    # ──────────────────────────────────────────────────────────────────────────
    def _render_results(self, res, target_frame):
        for w in target_frame.winfo_children():
            w.destroy()

        faults = res.get("faults", {})
        safety = res.get("safety", [])
        actions = res.get("actions", [])
        explanations = res.get("explanations", [])
        fired = res.get("fired_rules", [])

        # Scrollable canvas for results
        canvas = tk.Canvas(target_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(target_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Mouse wheel binding
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Safety alerts (only if present)
        if safety:
            for msg in safety:
                sf = tk.Frame(inner, bg=RED_DIM, padx=PAD, pady=PAD_SM,
                              highlightbackground=RED, highlightthickness=1)
                sf.pack(fill=tk.X, pady=(0, PAD_XS))
                tk.Label(sf, text="⚠  SAFETY ALERT", bg=RED_DIM, fg=RED,
                         font=(FONT, SMALL, "bold")).pack(anchor=tk.W)
                tk.Label(sf, text=msg, bg=RED_DIM, fg=TEXT, font=(FONT, BODY),
                         wraplength=700, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 0))

        # Faults
        if faults:
            tk.Label(inner, text="Diagnosed faults", bg=BG, fg=TEXT,
                     font=(FONT, H2_SIZE, "bold")).pack(anchor=tk.W, pady=(PAD_SM, PAD_XS))
            for name, cf in sorted(faults.items(), key=lambda x: -x[1]):
                color = RED if cf >= 0.9 else (AMBER if cf >= 0.7 else TEXT_MUTED)
                fc = tk.Frame(inner, bg=CARD, padx=0, pady=0,
                              highlightbackground=BORDER, highlightthickness=1)
                fc.pack(fill=tk.X, pady=2)

                # Coloured left edge
                tk.Frame(fc, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)

                body = tk.Frame(fc, bg=CARD, padx=PAD, pady=PAD_SM)
                body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                top = tk.Frame(body, bg=CARD)
                top.pack(fill=tk.X)
                display = name.replace("_", " ").title()
                tk.Label(top, text=display, bg=CARD, fg=TEXT,
                         font=(FONT, BODY, "bold")).pack(side=tk.LEFT)

                # Find which rules concluded this fault
                rule_ids = [r_obj["id"] for r_obj in self.kb.rules
                            if r_obj.get("then_fault") == name and r_obj["id"] in fired]
                if rule_ids:
                    tk.Label(top, text="  ".join(rule_ids), bg=CARD, fg=CYAN,
                             font=(MONO, TINY)).pack(side=tk.RIGHT)

                # Confidence bar
                bar_frame = tk.Frame(body, bg=CARD)
                bar_frame.pack(fill=tk.X, pady=(PAD_XS, 0))

                bar_bg = tk.Frame(bar_frame, bg=BORDER, height=8)
                bar_bg.pack(fill=tk.X)
                bar_bg.update_idletasks()

                bar_fill = tk.Frame(bar_bg, bg=color, height=8)
                # Use place for proportional width
                bar_fill.place(relwidth=min(1.0, cf), relheight=1.0)

                tk.Label(bar_frame, text=f"CF {cf:.2f}", bg=CARD, fg=color,
                         font=(MONO, TINY, "bold")).pack(anchor=tk.E)
        else:
            nf = tk.Frame(inner, bg=GREEN_DIM, padx=PAD, pady=PAD_SM,
                          highlightbackground=GREEN, highlightthickness=1)
            nf.pack(fill=tk.X, pady=(PAD_SM, PAD_XS))
            tk.Label(nf, text="All parameters within safe operating envelope.",
                     bg=GREEN_DIM, fg=GREEN, font=(FONT, BODY, "bold")).pack(anchor=tk.W)

        # Recommended actions
        if actions:
            tk.Label(inner, text="Recommended actions", bg=BG, fg=TEXT,
                     font=(FONT, H2_SIZE, "bold")).pack(anchor=tk.W, pady=(PAD_SM, PAD_XS))
            for idx, a in enumerate(actions, 1):
                ac = tk.Frame(inner, bg=CARD, padx=PAD, pady=PAD_SM,
                              highlightbackground=BORDER, highlightthickness=1)
                ac.pack(fill=tk.X, pady=2)

                top_row = tk.Frame(ac, bg=CARD)
                top_row.pack(fill=tk.X)

                # Priority badge
                p = a.get("priority", 3)
                p_color = RED if p == 1 else (AMBER if p == 2 else CYAN)
                p_bg = RED_DIM if p == 1 else (AMBER_DIM if p == 2 else BG)
                badge = tk.Label(top_row, text=f" P{p} ", bg=p_bg, fg=p_color,
                                 font=(MONO, TINY, "bold"), padx=4)
                badge.pack(side=tk.LEFT, padx=(0, PAD_SM))

                tk.Label(top_row, text=f"{idx}. [{a['id']}] {a['name']}",
                         bg=CARD, fg=TEXT, font=(FONT, BODY, "bold")).pack(side=tk.LEFT)

                tk.Label(top_row, text=f"CF {a['cf']:.2f}", bg=CARD, fg=CYAN,
                         font=(MONO, TINY, "bold")).pack(side=tk.RIGHT)

                detail = tk.Frame(ac, bg=CARD)
                detail.pack(fill=tk.X, pady=(PAD_XS, 0))
                for label, val in [("Cost", a["cost"]), ("Downtime", a["downtime"]),
                                   ("Personnel", a["who"])]:
                    tk.Label(detail, text=f"{label}: {val}", bg=CARD, fg=TEXT_MUTED,
                             font=(FONT, TINY)).pack(side=tk.LEFT, padx=(0, PAD))

        # Explanation (collapsible)
        if explanations:
            exp_header = tk.Label(inner, text="▶ Why? (inference audit trail)", bg=BG, fg=CYAN,
                                   font=(FONT, SMALL, "bold"), cursor="hand2")
            exp_header.pack(anchor=tk.W, pady=(PAD_SM, PAD_XS))

            exp_frame = tk.Frame(inner, bg=BG)
            exp_visible = [False]

            def toggle_exp(e=None):
                if exp_visible[0]:
                    exp_frame.pack_forget()
                    exp_header.config(text="▶ Why? (inference audit trail)")
                    exp_visible[0] = False
                else:
                    exp_frame.pack(fill=tk.X, after=exp_header)
                    exp_header.config(text="▼ Why? (inference audit trail)")
                    exp_visible[0] = True

            exp_header.bind("<Button-1>", toggle_exp)

            for line in explanations:
                # Colour rule IDs in cyan
                ef = tk.Frame(exp_frame, bg=CARD, padx=PAD_SM, pady=2)
                ef.pack(fill=tk.X, pady=1)
                tk.Label(ef, text=f"• {line}", bg=CARD, fg=TEXT_MUTED,
                         font=(FONT, TINY), wraplength=700, justify=tk.LEFT,
                         anchor=tk.W).pack(anchor=tk.W)

    # ──────────────────────────────────────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────────────────────────────────────
    def _load_csv_row(self, target):
        if not (1 <= target <= 10000):
            return
        if not os.path.exists(self.csv_path):
            messagebox.showerror("File missing", f"Dataset not found:\n{self.csv_path}")
            return

        with open(self.csv_path, "r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if int(row["UDI"]) == target:
                    air = float(row["Air temperature [K]"])
                    proc = float(row["Process temperature [K]"])
                    spd = float(row["Rotational speed [rpm]"])
                    trq = float(row["Torque [Nm]"])
                    tw = float(row["Tool wear [min]"])
                    ptype = row.get("Type", "M")

                    self.sl_air.set(air)
                    self.sl_proc.set(proc)
                    self.sl_speed.set(spd)
                    self.sl_torque.set(trq)
                    self.sl_tw.set(tw)
                    self.var_type.set(ptype)
                    self.var_row.set(str(target))

                    mf = row.get("Machine failure", "0")
                    pid = row.get("Product ID", "")
                    tag = "FAILURE" if mf == "1" else "Nominal"
                    color = RED if mf == "1" else GREEN
                    self.lbl_row_info.config(
                        text=f"Row {target} ({pid}) — Ground truth: {tag}",
                        fg=color)

                    self._run_telemetry()
                    return

    def _step_row(self, delta):
        try:
            cur = int(self.var_row.get())
        except ValueError:
            cur = 1
        nv = max(1, min(10000, cur + delta))
        self.var_row.set(str(nv))
        self._load_csv_row(nv)

    def _load_preset(self, key):
        presets = {
            "normal":   (298.1, 308.6, 1551, 42.8,   0, "M"),
            "hdf":      (298.9, 306.0, 1350, 45.0,  30, "M"),
            "pwf_high": (298.0, 308.0, 2800, 65.0,  25, "L"),
            "pwf_low":  (298.5, 309.0, 1200, 20.0,  15, "H"),
            "osf":      (298.3, 308.5, 1450, 58.0, 215, "L"),
            "twf":      (298.4, 308.7, 1520, 38.0, 225, "M"),
        }
        if key in presets:
            a, p, s, t, w, ty = presets[key]
            self.sl_air.set(a)
            self.sl_proc.set(p)
            self.sl_speed.set(s)
            self.sl_torque.set(t)
            self.sl_tw.set(w)
            self.var_type.set(ty)
            self.lbl_row_info.config(text=f"Preset: {key.upper()}", fg=CYAN)
            self._run_telemetry()

    # ──────────────────────────────────────────────────────────────────────────
    #  DIAGNOSIS EXECUTION
    # ──────────────────────────────────────────────────────────────────────────
    def _on_slider(self):
        self._run_telemetry()

    def _run_telemetry(self):
        air = self.sl_air.get()
        proc = self.sl_proc.get()
        spd = self.sl_speed.get()
        trq = self.sl_torque.get()
        tw = self.sl_tw.get()
        ty = self.var_type.get()

        res = diagnose_telemetry(air, proc, spd, trq, tw, ty, rules_path=self.rules_path)
        m = res.get("telemetry_metrics", {})

        # Update gauges
        dt = m.get("delta_T_K", proc - air)
        pw = m.get("power_watts", trq * spd * 2 * math.pi / 60)
        os_val = m.get("overstrain_min_Nm", tw * trq)
        os_lim = m.get("overstrain_limit", 12000)

        self.gauge_dt.set_value(dt)
        self.gauge_pw.set_value(pw)
        self.gauge_os.max_v = max(os_lim * 1.3, 16000)
        self.gauge_os.crit_hi = os_lim
        self.gauge_os.limit_marker = os_lim
        self.gauge_os.safe_label = f"Limit: {os_lim:,.0f}"
        self.gauge_os.set_value(os_val)
        self.gauge_tw.set_value(tw)

        # Update slider track colours
        self.sl_air.crit_lo = None  # air temp alone has no threshold
        dt_val = proc - air
        if dt_val < 8.6 and spd < 1380:
            self.sl_proc.crit_lo = proc + 1  # force red (value is below crit_lo)
        else:
            self.sl_proc.crit_lo = None
        self.sl_proc._redraw()

        pw_actual = trq * spd * 2 * math.pi / 60
        if pw_actual < 3500 or pw_actual > 9000:
            self.sl_speed.crit_lo = self.sl_speed.max_v + 1  # force red
        else:
            self.sl_speed.crit_lo = None
        self.sl_speed._redraw()

        # Machine state header
        faults = res.get("faults", {})
        if faults:
            self.lbl_state.config(text="FAULT", fg=RED)
            self.lbl_state_sub.config(
                text=list(faults.keys())[0].replace("_", " ").title(), fg=RED)
            self.status_frame.config(bg=RED_DIM)
            self.status_label.config(text="FAULT DETECTED", bg=RED_DIM, fg=RED)
        elif tw >= 200:
            self.lbl_state.config(text="WARNING", fg=AMBER)
            self.lbl_state_sub.config(text="Tool wear critical zone", fg=AMBER)
            self.status_frame.config(bg=AMBER_DIM)
            self.status_label.config(text="WARNING", bg=AMBER_DIM, fg=AMBER)
        else:
            self.lbl_state.config(text="NOMINAL", fg=GREEN)
            self.lbl_state_sub.config(text="All readings nominal", fg=TEXT_MUTED)
            self.status_frame.config(bg=GREEN_DIM)
            self.status_label.config(text="NOMINAL", bg=GREEN_DIM, fg=GREEN)

        self._render_results(res, self.tel_results_frame)

    def _run_symptoms(self):
        selected = [s for s, v in self.symptom_vars.items() if v.get()]
        if not selected:
            messagebox.showinfo("No symptoms", "Select at least one symptom.")
            return
        res = diagnose(selected, rules_path=self.rules_path)

        faults = res.get("faults", {})
        if faults:
            self.status_frame.config(bg=RED_DIM)
            self.status_label.config(text="FAULT DETECTED", bg=RED_DIM, fg=RED)
        else:
            self.status_frame.config(bg=GREEN_DIM)
            self.status_label.config(text="NOMINAL", bg=GREEN_DIM, fg=GREEN)

        self._render_results(res, self.sym_results_frame)

    def _clear_symptoms(self):
        for sid, (chip, lbl, var) in self._symptom_chips.items():
            var.set(False)
            chip.config(highlightbackground=BORDER, highlightthickness=1, bg=CARD)
            lbl.config(bg=CARD, fg=TEXT_MUTED)

        for w in self.sym_results_frame.winfo_children():
            w.destroy()
        self._build_empty_state(self.sym_results_frame,
                                "Select symptoms from the chips above, then press Run diagnosis.")
        self.status_frame.config(bg=GREEN_DIM)
        self.status_label.config(text="NOMINAL", bg=GREEN_DIM, fg=GREEN)

    # ──────────────────────────────────────────────────────────────────────────
    #  BATCH BENCHMARK
    # ──────────────────────────────────────────────────────────────────────────
    def _run_batch(self):
        if not os.path.exists(self.csv_path):
            messagebox.showerror("Missing", f"Dataset not found:\n{self.csv_path}")
            return

        # Clear previous tiles
        for w in self.bench_tiles_frame.winfo_children():
            w.destroy()
        self.bench_log_text.delete("1.0", tk.END)
        self.bench_progress_var.set(0)
        self.root.update_idletasks()

        t0 = time.time()
        counters = {k: {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
                     for k in ("HDF", "PWF", "OSF", "Overall")}
        total = 0

        with open(self.csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                amf = int(row["Machine failure"])
                ahdf = int(row["HDF"])
                apwf = int(row["PWF"])
                aosf = int(row["OSF"])

                res = diagnose_telemetry(
                    float(row["Air temperature [K]"]),
                    float(row["Process temperature [K]"]),
                    float(row["Rotational speed [rpm]"]),
                    float(row["Torque [Nm]"]),
                    float(row["Tool wear [min]"]),
                    row.get("Type", "M"),
                    rules_path=self.rules_path
                )
                faults = res.get("faults", {})
                phdf = 1 if "heat_dissipation_failure" in faults else 0
                ppwf = 1 if "power_failure" in faults else 0
                posf = 1 if "overstrain_failure" in faults else 0
                pmf = 1 if (phdf or ppwf or posf) else 0

                for pred, act, key in [(phdf, ahdf, "HDF"), (ppwf, apwf, "PWF"),
                                        (posf, aosf, "OSF"), (pmf, amf, "Overall")]:
                    c = counters[key]
                    if pred and act:     c["tp"] += 1
                    elif pred and not act: c["fp"] += 1
                    elif not pred and act: c["fn"] += 1
                    else:                  c["tn"] += 1

                if total % 500 == 0:
                    self.bench_progress_var.set(total / 100)
                    self.root.update_idletasks()

        elapsed = time.time() - t0
        self.bench_progress_var.set(100)

        # Build result tiles
        for key in ("HDF", "PWF", "OSF", "Overall"):
            c = counters[key]
            tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
            prec = tp / max(1, tp + fp) * 100
            rec = tp / max(1, tp + fn) * 100
            f1 = 2 * prec * rec / max(0.01, prec + rec)
            acc = (tp + tn) / total * 100

            tile = tk.Frame(self.bench_tiles_frame, bg=CARD, padx=PAD, pady=PAD_SM,
                            highlightbackground=BORDER, highlightthickness=1)
            tile.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=PAD_XS)

            title_color = GREEN if fp == 0 and fn == 0 else (AMBER if fp == 0 else RED)
            tk.Label(tile, text=key, bg=CARD, fg=title_color,
                     font=(FONT, H2_SIZE, "bold")).pack(anchor=tk.W)

            for label, val in [("TP", tp), ("FP", fp), ("FN", fn), ("TN", tn)]:
                rf = tk.Frame(tile, bg=CARD)
                rf.pack(fill=tk.X)
                tk.Label(rf, text=label, bg=CARD, fg=TEXT_MUTED,
                         font=(FONT, TINY)).pack(side=tk.LEFT)
                v_color = RED if (label in ("FP", "FN") and val > 0) else TEXT
                tk.Label(rf, text=str(val), bg=CARD, fg=v_color,
                         font=(MONO, SMALL, "bold")).pack(side=tk.RIGHT)

            self._divider(tile)

            for label, val in [("Precision", prec), ("Recall", rec), ("F1", f1/100)]:
                rf = tk.Frame(tile, bg=CARD)
                rf.pack(fill=tk.X)
                tk.Label(rf, text=label, bg=CARD, fg=TEXT_MUTED,
                         font=(FONT, TINY)).pack(side=tk.LEFT)
                fmt_val = f"{val:.2f}%" if "F1" not in label else f"{val:.4f}"
                tk.Label(rf, text=fmt_val, bg=CARD, fg=GREEN if val >= 99 else TEXT,
                         font=(MONO, SMALL, "bold")).pack(side=tk.RIGHT)

            # Accuracy bar
            bar_bg = tk.Frame(tile, bg=BORDER, height=6)
            bar_bg.pack(fill=tk.X, pady=(PAD_XS, 0))
            bar_fill = tk.Frame(bar_bg, bg=GREEN, height=6)
            bar_fill.place(relwidth=min(1.0, acc / 100), relheight=1.0)

            tk.Label(tile, text=f"Acc {acc:.2f}%", bg=CARD, fg=TEXT_DIM,
                     font=(MONO, TINY)).pack(anchor=tk.E)

        # Raw log
        log_lines = [
            f"Processed {total:,} rows in {elapsed:.2f}s ({total/max(0.01,elapsed):,.0f} rows/sec)",
            "",
        ]
        for key in ("HDF", "PWF", "OSF", "Overall"):
            c = counters[key]
            tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
            prec = tp / max(1, tp + fp) * 100
            rec = tp / max(1, tp + fn) * 100
            f1 = 2 * prec * rec / max(0.01, prec + rec)
            log_lines.append(f"--- {key} ---")
            log_lines.append(f"  TP={tp} FP={fp} FN={fn} TN={tn}")
            log_lines.append(f"  Precision={prec:.2f}% Recall={rec:.2f}% F1={f1/100:.4f}")
            log_lines.append("")

        self.bench_log_text.insert(tk.END, "\n".join(log_lines))


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
