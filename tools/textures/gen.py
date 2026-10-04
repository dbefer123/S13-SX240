"""Procedural texture generation (numpy + PIL, no Blender needed).

Writes PNGs with the BeamNG texture-cooker suffixes (.color.png / .data.png /
.normal.png) into the mod folders referenced by tools/model/materials.py.

    python -m tools.textures.gen [--mod mod] [--only name,...]
"""
from __future__ import annotations

import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from tools.vehicle.s13 import dims as D13

FONT_DIR = "/usr/share/fonts/truetype"
FONTS = {
    "sans": f"{FONT_DIR}/dejavu/DejaVuSans.ttf",
    "sans_bold": f"{FONT_DIR}/dejavu/DejaVuSans-Bold.ttf",
    "cond": f"{FONT_DIR}/dejavu/DejaVuSansCondensed-Bold.ttf",
    "lib": f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf",
    "lib_reg": f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf",
    "free_bold_obl": f"{FONT_DIR}/freefont/FreeSansBoldOblique.ttf",
}


def font(kind, size):
    for k in (kind, "sans_bold", "sans"):
        p = FONTS.get(k)
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


RNG = np.random.default_rng(240)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(img, np.ndarray):
        a = np.clip(img, 0, 1)
        a = (a * 255 + 0.5).astype(np.uint8)
        img = Image.fromarray(a)
    img.save(path, optimize=True)
    return path


def tileable_noise(n, scale, octaves=4, seed=0, persistence=0.5):
    """Tileable value noise in [0,1] (sum of bilinear-upsampled random lattices)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = max(1, int(scale * 2 ** o))
        lat = rng.random((cells, cells))
        # periodic bilinear upsample
        x = np.arange(n) * cells / n
        i0 = np.floor(x).astype(int) % cells
        i1 = (i0 + 1) % cells
        f = x - np.floor(x)
        f = f * f * (3 - 2 * f)
        rows = lat[i0][:, None, :] * (1 - f)[:, None, None] + lat[i1][:, None, :] * f[:, None, None]
        rows = rows[:, 0, :]
        layer = rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :]
        out += amp * layer
        tot += amp
        amp *= persistence
    return out / tot


def normal_from_height(h, strength=2.0, wrap=True):
    """Height map [0,1] -> tangent-space normal map RGB in [0,1] (OpenGL, +Y up)."""
    if wrap:
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(h)
    nx = -dx * strength
    ny = dy * strength          # image rows grow downward; +Y (green) points up
    nz = np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5], -1)


def gray(a):
    return np.stack([a, a, a], -1)


# ---------------------------------------------------------------------------
# S13 instrument cluster
# ---------------------------------------------------------------------------
def _dial(dr, cx, cy, r, vmin, vmax, a0, a1, majors, minors_per, labels, lab_font, color, red_from=None,
          tick_w=(10, 5), label_r=0.70, red_color=(235, 40, 20)):
    """Draw a dial. Angles are degrees CCW from straight up (as seen by the viewer)."""
    def pt(a, rr):
        t = math.radians(a)
        return cx - rr * math.sin(t), cy - rr * math.cos(t)

    def ang(v):
        return a0 + (a1 - a0) * (v - vmin) / (vmax - vmin)
    if red_from is not None:
        rr = r * 0.975
        a_r, a_m = ang(red_from), ang(vmax)
        dr.arc([cx - rr, cy - rr, cx + rr, cy + rr], start=270 - a_r, end=270 - a_m, fill=red_color, width=int(r * 0.07))
    n_major = len(majors)
    for i, v in enumerate(majors):
        a = ang(v)
        col = red_color if (red_from is not None and v >= red_from) else color
        dr.line([pt(a, r * 0.98), pt(a, r * 0.80)], fill=col, width=tick_w[0])
        if labels and labels[i] is not None:
            x, y = pt(a, r * label_r)
            dr.text((x, y), labels[i], font=lab_font, fill=col, anchor="mm")
        if i < n_major - 1 and minors_per:
            for k in range(1, minors_per):
                vv = v + (majors[i + 1] - v) * k / minors_per
                col2 = red_color if (red_from is not None and vv >= red_from) else color
                ln = 0.88 if (minors_per % 2 == 0 and k == minors_per // 2) else 0.91
                dr.line([pt(ang(vv), r * 0.98), pt(ang(vv), r * ln)], fill=col2, width=tick_w[1])


def gauges_s13(out_dir, prefix="s13", style="s13"):
    """Instrument cluster face (+ glow mask).  style "s14": rounder 90s cluster with chrome rings, 150 mph speedo."""
    s14 = style == "s14"
    W_m, H_m = D13.GAUGE_W, D13.GAUGE_H
    PX = 7000                                   # pixels per metre while drawing
    W, H = int(W_m * PX), int(H_m * PX)
    base = Image.new("RGB", (W, H), (8, 8, 9))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    db, dg = ImageDraw.Draw(base), ImageDraw.Draw(glow)
    white = (235, 235, 230)
    lit = (255, 250, 235)

    def u2x(dx_from_col):   # +dx is the driver's left -> image left
        return (W_m / 2 - dx_from_col) * PX

    def v2y(dz):
        return (H_m / 2 - dz) * PX

    for d in (db, dg):
        col = white if d is db else lit
        # subtle face panel separations
        if d is db:
            d.rounded_rectangle([8, 8, W - 8, H - 8], radius=int(0.012 * PX), outline=(30, 30, 32), width=6)
        # --- tach (driver's left of centre) ---
        cx, cy, r = u2x(D13.GAUGE_TACH_DX), v2y(0.0), D13.GAUGE_R_MAIN * PX
        if s14 and d is db:
            for cxx in (cx, u2x(-D13.GAUGE_TACH_DX)):
                d.ellipse([cxx - r * 1.04, cy - r * 1.04, cxx + r * 1.04, cy + r * 1.04], outline=(150, 150, 155),
                          width=int(r * 0.035))
        nfont = font("lib", int(r * 0.24)) if s14 else font("sans_bold", int(r * 0.22))
        _dial(d, cx, cy, r, 0, 8, 120, -120, list(range(0, 9)), 2, [str(i) for i in range(9)], nfont,
              col, red_from=6.5 if s14 else 6.8, tick_w=(int(r * 0.035), int(r * 0.02)), label_r=0.62)
        d.text((cx, cy + r * 0.38), "x1000 RPM" if s14 else "x1000r/min", font=font("sans", int(r * 0.10)), fill=col,
               anchor="mm")
        # --- speedo ---
        cx, cy = u2x(-D13.GAUGE_TACH_DX), v2y(0.0)
        top = 150 if s14 else 140
        majors = list(range(0, top + 1, 10))
        labels = [str(v) if v % 20 == 0 else None for v in majors]
        _dial(d, cx, cy, r, 0, top, 120, -120, majors, 2, labels,
              font("lib", int(r * 0.18)) if s14 else font("sans_bold", int(r * 0.17)), col,
              tick_w=(int(r * 0.03), int(r * 0.018)), label_r=0.66)
        d.text((cx, cy + r * 0.36), "MPH", font=font("sans_bold", int(r * 0.13)), fill=col, anchor="mm")
        # inner km/h ring (small)
        kmh = list(range(0, 241, 20))
        for v in kmh:
            a = 120 - 240 * (v / 1.609) / top
            if (v / 1.609) > top:
                break
            t = math.radians(a)
            x, y = cx - r * 0.42 * math.sin(t), cy - r * 0.42 * math.cos(t)
            if v % 40 == 0:
                d.text((x, y), str(v), font=font("sans", int(r * 0.08)), fill=(170, 170, 170) if d is db else (200, 200, 190),
                       anchor="mm")
        d.text((cx, cy + r * 0.52), "km/h", font=font("sans", int(r * 0.075)), fill=(170, 170, 170), anchor="mm")
        # odometer window
        if d is db:
            ox, oy = cx, cy + r * 0.66
            d.rectangle([ox - r * 0.30, oy - r * 0.07, ox + r * 0.30, oy + r * 0.07], fill=(2, 2, 2), outline=(60, 60, 60), width=3)
            d.text((ox, oy), "0 2 4 0 8 9", font=font("cond", int(r * 0.10)), fill=(225, 225, 225), anchor="mm")
        # --- temp (far left): C .. H over 135 deg ---
        rs = D13.GAUGE_R_SMALL * PX
        cx, cy = u2x(D13.GAUGE_SMALL_DX), v2y(D13.GAUGE_SMALL_DZ)
        _dial(d, cx, cy, rs, 40, 130, 67.5, -67.5, [40, 70, 100, 130], 2, ["C", None, None, "H"],
              font("sans_bold", int(rs * 0.30)), col, red_from=115, tick_w=(int(rs * 0.05), int(rs * 0.03)), label_r=0.62)
        d.text((cx, cy + rs * 0.42), "TEMP", font=font("sans", int(rs * 0.16)), fill=col, anchor="mm")
        # --- fuel (far right): E .. F over 90 deg ---
        cx, cy = u2x(-D13.GAUGE_SMALL_DX), v2y(D13.GAUGE_SMALL_DZ)
        _dial(d, cx, cy, rs, 0, 1, 45, -45, [0, 0.5, 1.0], 2, ["E", None, "F"], font("sans_bold", int(rs * 0.30)), col,
              tick_w=(int(rs * 0.05), int(rs * 0.03)), label_r=0.62, red_from=None)
        d.text((cx, cy + rs * 0.42), "FUEL", font=font("sans", int(rs * 0.16)), fill=col, anchor="mm")
    # warning lamp cut-outs between the dials (dark, unlit)
    for k, (lbl, c) in enumerate((("BRAKE", (170, 20, 20)), ("CHARGE", (170, 20, 20)), ("OIL", (170, 20, 20)),
                                  ("CHECK", (180, 100, 10)))):
        x = W / 2 + (k - 1.5) * 0.012 * PX
        y = v2y(-0.058)
        db.text((x, y), lbl, font=font("sans_bold", int(0.0028 * PX)), fill=tuple(int(v * 0.35) for v in c), anchor="mm")
    if not s14:
        db.text((W / 2, v2y(0.062)), "NISSAN", font=font("sans_bold", int(0.0045 * PX)), fill=(120, 120, 120), anchor="mm")
    base = base.resize((2048, 1024), Image.LANCZOS)
    glow = glow.filter(ImageFilter.GaussianBlur(3)).resize((2048, 1024), Image.LANCZOS)
    save(base, os.path.join(out_dir, f"{prefix}_gauges_b.color.png"))
    save(glow, os.path.join(out_dir, f"{prefix}_gauges_g.color.png"))


def race_tach(out_dir, prefix="s13", n=1024):
    """Round race tachometer face 0-10 x1000 rpm over 270 deg (zero at 135 deg CCW from up)."""
    im = Image.new("RGB", (n, n), (6, 6, 7))
    d = ImageDraw.Draw(im)
    c = n / 2
    d.ellipse([4, 4, n - 4, n - 4], fill=(10, 10, 11), outline=(70, 70, 72), width=6)
    _dial(d, c, c, n * 0.46, 0, 10, 135, -135, list(range(0, 11)), 4, [str(i) for i in range(11)],
          font("sans_bold", int(n * 0.085)), (240, 240, 235), red_from=8.5, tick_w=(int(n * 0.012), int(n * 0.006)),
          label_r=0.72)
    d.text((c, c + n * 0.20), "RPM x1000", font=font("sans_bold", int(n * 0.045)), fill=(200, 200, 200), anchor="mm")
    d.text((c, c + n * 0.28), "RACE", font=font("free_bold_obl", int(n * 0.05)), fill=(220, 30, 20), anchor="mm")
    save(im, os.path.join(out_dir, f"{prefix}_racetach_b.color.png"))


def ivtec_plaque(out_dir, W=1024, H=512):
    im = Image.new("RGB", (W, H), (150, 150, 152))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, W - 6, H - 6], outline=(70, 70, 72), width=10)
    d.rectangle([30, 30, W - 30, H - 30], fill=(190, 190, 192))
    d.text((W / 2 - 130, H / 2), "i-", font=font("free_bold_obl", 230), fill=(170, 10, 15), anchor="mm")
    d.text((W / 2 + 90, H / 2), "VTEC", font=font("free_bold_obl", 230), fill=(170, 10, 15), anchor="mm")
    save(im, os.path.join(out_dir, "s1x_ivtec_b.color.png"))


def brushed_normal(out_dir, n=512):
    rng = np.random.default_rng(51)
    rows = rng.random((n, 1)) * 0.6 + tileable_noise(n, 2, 2, seed=52)[:, :1] * 0.4
    h = np.repeat(rows, n, axis=1) + 0.15 * tileable_noise(n, 80, 2, seed=53)
    save(normal_from_height(h, 1.5), os.path.join(out_dir, "s1x_brushed_nm.normal.png"))


# ---------------------------------------------------------------------------
# damaged glass (shared crack pattern for windows and lamp lenses)
# ---------------------------------------------------------------------------
def glass_dmg(out_dir, prefix="s13", n=1024):
    img = Image.new("L", (n, n), 0)
    dr = ImageDraw.Draw(img)
    rng = np.random.default_rng(13)
    # impact centres with radial + concentric cracks (tileable by wrapping draws)
    for _ in range(6):
        cx, cy = rng.random(2) * n
        n_rad = rng.integers(10, 18)
        for k in range(n_rad):
            a = 2 * math.pi * (k + rng.random() * 0.6) / n_rad
            x, y = cx, cy
            L = rng.uniform(0.15, 0.45) * n
            steps = 18
            for s in range(steps):
                a += rng.normal(0, 0.12)
                nx_, ny_ = x + math.cos(a) * L / steps, y + math.sin(a) * L / steps
                for ox in (-n, 0, n):
                    for oy in (-n, 0, n):
                        dr.line([(x + ox, y + oy), (nx_ + ox, ny_ + oy)], fill=255, width=2)
                x, y = nx_, ny_
        for ring in range(rng.integers(2, 5)):
            rr = rng.uniform(0.03, 0.2) * n
            pts = []
            for k in range(40):
                a = 2 * math.pi * k / 39
                r2 = rr * (1 + rng.normal(0, 0.06))
                pts.append((cx + math.cos(a) * r2, cy + math.sin(a) * r2))
            for ox in (-n, 0, n):
                for oy in (-n, 0, n):
                    dr.line([(p[0] + ox, p[1] + oy) for p in pts], fill=200, width=2)
    crack = np.asarray(img, dtype=np.float32) / 255.0
    soft = np.asarray(img.filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float32) / 255.0
    frost = tileable_noise(n, 24, 4, seed=5)
    # base colour: whitish crack lines over a slightly tinted glass
    col = np.stack([0.05 + 0.85 * crack, 0.06 + 0.85 * crack, 0.065 + 0.85 * crack], -1)
    opacity = np.clip(0.30 + 0.65 * np.maximum(crack, soft * 0.6) + 0.05 * frost, 0, 1)
    h = np.clip(soft * 0.8 + frost * 0.08, 0, 1)
    save(col, os.path.join(out_dir, f"{prefix}_glass_dmg_b.color.png"))
    save(gray(opacity), os.path.join(out_dir, f"{prefix}_glass_dmg_o.data.png"))
    save(normal_from_height(h, 6.0), os.path.join(out_dir, f"{prefix}_glass_dmg_nm.normal.png"))


# ---------------------------------------------------------------------------
# lamp lens patterns (UV0 is box-mapped in metres: 1 tile = 1 m)
# ---------------------------------------------------------------------------
def lens_normals(out_dir, prefix="s13", n=1024):
    x = np.arange(n) / n
    # headlamp: vertical flutes ~8 mm + faint horizontal ribs ~20 mm
    fl = 0.5 + 0.5 * np.cos(2 * math.pi * x * 125)
    rib = 0.5 + 0.5 * np.cos(2 * math.pi * x * 50)
    h = 0.75 * fl[None, :] + 0.25 * rib[:, None]
    save(normal_from_height(h, 3.0), os.path.join(out_dir, f"{prefix}_lens_nm.normal.png"))
    # tail lamp: square prism cells ~10 mm (pyramids)
    fx = np.abs(((x * 100) % 1.0) - 0.5)
    h = 1.0 - 2 * np.maximum(fx[None, :], fx[:, None])
    save(normal_from_height(h, 5.0), os.path.join(out_dir, f"{prefix}_tail_nm.normal.png"))


# ---------------------------------------------------------------------------
# interior textures
# ---------------------------------------------------------------------------
def seat_cloth(out_dir, prefix="s13", n=1024):
    """1 m tile: charcoal cloth with a fine woven fleck and thin pin stripes (S13 SE style)."""
    noise = tileable_noise(n, 180, 3, seed=7)
    fleck = (tileable_noise(n, 400, 1, seed=8) > 0.82).astype(np.float32)
    y = np.arange(n) / n
    stripe = ((y * 50) % 1.0 < 0.08).astype(np.float32)[:, None] * np.ones((1, n))
    base = 0.035 + 0.025 * noise
    r = base + 0.05 * fleck + 0.035 * stripe
    g = base + 0.045 * fleck + 0.035 * stripe
    b = base + 0.06 * fleck + 0.05 * stripe
    save(np.stack([r, g, b], -1) ** (1 / 2.2), os.path.join(out_dir, f"{prefix}_seat_cloth_b.color.png"))


def radio(out_dir, prefix="s13"):
    W, H = 1024, 320
    im = Image.new("RGB", (W, H), (14, 14, 15))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, W - 6, H - 6], radius=16, outline=(45, 45, 48), width=4)
    # cassette door
    d.rounded_rectangle([300, 70, 720, 150], radius=8, fill=(6, 6, 6), outline=(70, 70, 72), width=3)
    d.text((510, 110), "AUTO REVERSE  DOLBY B NR", font=font("sans", 22), fill=(130, 130, 130), anchor="mm")
    # display
    d.rectangle([330, 180, 690, 250], fill=(3, 8, 6), outline=(40, 40, 40), width=2)
    d.text((510, 215), "FM1  98.7", font=font("cond", 40), fill=(70, 200, 150), anchor="mm")
    # knobs
    for cx in (120, 905):
        d.ellipse([cx - 70, H / 2 - 70, cx + 70, H / 2 + 70], fill=(25, 25, 26), outline=(90, 90, 92), width=4)
        d.ellipse([cx - 40, H / 2 - 40, cx + 40, H / 2 + 40], fill=(40, 40, 42))
    # preset buttons
    for k in range(6):
        x = 300 + k * 70
        d.rounded_rectangle([x, 265, x + 58, 300], radius=5, fill=(30, 30, 32), outline=(80, 80, 82), width=2)
        d.text((x + 29, 283), str(k + 1), font=font("sans_bold", 20), fill=(170, 170, 170), anchor="mm")
    d.text((510, 35), "NISSAN", font=font("sans_bold", 30), fill=(140, 140, 140), anchor="mm")
    save(im.resize((1024, 256), Image.LANCZOS), os.path.join(out_dir, f"{prefix}_radio_b.color.png"))


def hvac_s14(out_dir, prefix="s14"):
    """S14 climate panel: fan, temperature and mode dials (the knob meshes sit on the dial centres at
    u = 0.18 / 0.5 / 0.82 of a 0.22 m wide panel), A/C and recirculation buttons between them."""
    W, H = 1024, 320
    im = Image.new("RGB", (W, H), (16, 16, 17))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, W - 6, H - 6], radius=16, outline=(45, 45, 48), width=4)
    px_per_m = W / 0.22
    r_ring = 0.026 * px_per_m
    lab = font("sans_bold", 22)
    for u, kind in ((0.18, "fan"), (0.5, "temp"), (0.82, "mode")):
        cx, cy = u * W, H / 2
        d.ellipse([cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring], outline=(70, 70, 74), width=3)
        a0, a1 = math.radians(225), math.radians(-45)
        if kind == "temp":
            n = 40
            for k in range(n):
                t = k / (n - 1)
                a = a0 + (a1 - a0) * t
                col = (int(60 + 160 * t), int(110 - 60 * t), int(220 - 190 * t))
                x0, y0 = cx + (r_ring + 8) * math.cos(a), cy - (r_ring + 8) * math.sin(a)
                x1, y1 = cx + (r_ring + 22) * math.cos(a), cy - (r_ring + 22) * math.sin(a)
                d.line([x0, y0, x1, y1], fill=col, width=6)
            continue
        labels = ("OFF", "1", "2", "3", "4") if kind == "fan" else ("VENT", "B/L", "FOOT", "F/D", "DEF")
        for k, t in enumerate(labels):
            a = a0 + (a1 - a0) * k / (len(labels) - 1)
            x, y = cx + (r_ring + 34) * math.cos(a), cy - (r_ring + 30) * math.sin(a)
            d.text((x, y), t, font=lab, fill=(165, 165, 165), anchor="mm")
    for u, t, col in ((0.34, "A/C", (80, 170, 95)), (0.66, "REC", (200, 150, 60))):
        cx = u * W
        d.rounded_rectangle([cx - 44, H / 2 - 26, cx + 44, H / 2 + 26], radius=8, fill=(34, 34, 36), outline=(90, 90, 92),
                            width=2)
        d.text((cx, H / 2), t, font=font("sans_bold", 26), fill=(175, 175, 175), anchor="mm")
        d.ellipse([cx - 5, H / 2 - 40, cx + 5, H / 2 - 30], fill=col)
    save(im.resize((1024, 256), Image.LANCZOS), os.path.join(out_dir, f"{prefix}_hvac_b.color.png"))


def hvac(out_dir, prefix="s13"):
    W, H = 1024, 320
    im = Image.new("RGB", (W, H), (16, 16, 17))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, W - 6, H - 6], radius=16, outline=(45, 45, 48), width=4)
    # three sliders + fan knob
    for k, (lbl, ends) in enumerate((("TEMP", ("C", "H")), ("MODE", ("", "")), ("INTAKE", ("REC", "FRE")))):
        x0, x1, y = 90 + k * 0, 0, 0
        cxk = 170 + k * 310
        d.rectangle([cxk - 120, 150, cxk + 120, 162], fill=(5, 5, 5), outline=(70, 70, 70), width=2)
        d.rounded_rectangle([cxk - 20, 132, cxk + 20, 180], radius=5, fill=(60, 60, 62))
        d.text((cxk, 225), lbl, font=font("sans_bold", 28), fill=(170, 170, 170), anchor="mm")
        d.text((cxk - 135, 156), ends[0], font=font("sans_bold", 22), fill=(60, 110, 200) if ends[0] == "C" else (160, 160, 160), anchor="rm")
        d.text((cxk + 135, 156), ends[1], font=font("sans_bold", 22), fill=(200, 60, 40) if ends[1] == "H" else (160, 160, 160), anchor="lm")
    for k, s in enumerate(("OFF", "1", "2", "3", "4")):
        d.text((330 + k * 90, 60), s, font=font("sans_bold", 24), fill=(160, 160, 160), anchor="mm")
    d.text((W / 2, 280), "A/C", font=font("sans_bold", 26), fill=(80, 160, 90), anchor="mm")
    save(im.resize((1024, 256), Image.LANCZOS), os.path.join(out_dir, f"{prefix}_hvac_b.color.png"))


# ---------------------------------------------------------------------------
# shared (s1x) mechanical detail
# ---------------------------------------------------------------------------
def cast_normal(out_dir, n=512):
    h = tileable_noise(n, 30, 5, seed=11, persistence=0.55)
    save(normal_from_height(h, 8.0), os.path.join(out_dir, "s1x_cast_nm.normal.png"))


def crinkle_normal(out_dir, n=512):
    a = tileable_noise(n, 18, 3, seed=21)
    b = tileable_noise(n, 18, 3, seed=22)
    # ridges where two noise fields cross: worm-like wrinkle finish
    h = 1.0 - np.minimum(np.abs(a - 0.5), np.abs(b - 0.5)) * 6
    h = np.clip(h, 0, 1) ** 2
    save(normal_from_height(h, 6.0), os.path.join(out_dir, "s1x_crinkle_nm.normal.png"))


def rotor_normal(out_dir, n=512):
    y = np.arange(n) / n
    lines = tileable_noise(n, 4, 2, seed=31)
    fine = 0.5 + 0.5 * np.sin(2 * math.pi * (y * 160)[:, None] + lines * 6)
    save(normal_from_height(fine * 0.6 + 0.4 * tileable_noise(n, 60, 2, seed=32), 2.0),
         os.path.join(out_dir, "s1x_rotor_nm.normal.png"))


def core(out_dir, n=2048):
    """Radiator / intercooler core, 1 m tile: vertical fins every 2.5 mm, flat tubes every 9 mm."""
    x = np.arange(n) / n
    fins = np.abs(((x * 400) % 1.0) - 0.5) * 2              # 0 at fin
    tubes = (((x * 111) % 1.0) < 0.22).astype(np.float32)   # horizontal tubes (rows)
    h = (1 - tubes[:, None]) * (0.4 + 0.6 * fins[None, :]) * 0.6 + tubes[:, None] * 1.0
    col = 0.10 + 0.55 * tubes[:, None] + 0.25 * (1 - fins[None, :]) * (1 - tubes[:, None])
    col = np.clip(col, 0, 1)
    save(gray(col), os.path.join(out_dir, "s1x_core_b.color.png"))
    save(normal_from_height(h, 4.0), os.path.join(out_dir, "s1x_core_nm.normal.png"))


# ---------------------------------------------------------------------------
# tyres: UV layout (see wheels_mesh.tire_uvs)
#   v 0.00-0.30 inner sidewall (0 = bead), 0.30-0.70 tread, 0.70-1.00 outer sidewall (1 = bead)
#   u: 2 repeats per revolution
# ---------------------------------------------------------------------------
TIRE_TEXT = {
    "street": ("TRACTIVE", "SPORT RADIAL  TUBELESS  STEEL BELTED", (205, 205, 205)),
    "semi": ("TRACTIVE", "R-COMPOUND COMPETITION  DOT", (230, 230, 230)),
    "slick": ("TRACTIVE", "RACING SLICK  NOT FOR HIGHWAY USE", (235, 200, 40)),
}


def tire(out_dir, key, W=2048, H=1024):
    brand, small, tcol = TIRE_TEXT[key]
    h = np.zeros((H, W), np.float32)
    col = np.full((H, W), 0.030, np.float32)
    rows = np.arange(H) / H                       # image row 0 = v 1.0
    v = 1.0 - rows
    tread = (v > 0.30) & (v < 0.70)
    # sidewall: fine radial ribs near the bead + rubber noise
    nz = tileable_noise(512, 64, 3, seed=41)
    nz = np.tile(nz, (H // 512 + 1, W // 512 + 1))[:H, :W]
    h += 0.08 * nz
    xs = np.arange(W) / W
    bead = ((v < 0.05) | (v > 0.95)).astype(np.float32)
    h += 0.15 * bead[:, None] * (0.5 + 0.5 * np.sin(2 * math.pi * xs * 600))[None, :]
    if key == "street":
        # block tread: circumferential grooves come from geometry; add lateral sipes + block edges
        lat = ((xs * 90) % 1.0 < 0.06).astype(np.float32)
        sipes = ((xs * 270) % 1.0 < 0.03).astype(np.float32)
        tv = (v - 0.30) / 0.40
        shoulder = ((tv < 0.22) | (tv > 0.78)).astype(np.float32)
        h_t = 1.0 - np.clip(lat[None, :] + 0.6 * sipes[None, :] * (1 - shoulder[:, None]), 0, 1)
        h = np.where(tread[:, None], h_t * 0.9 + 0.05 * nz, h)
        col = np.where(tread[:, None], 0.028 - 0.012 * (1 - h_t), col)
    elif key == "semi":
        lat = ((xs * 40) % 1.0 < 0.025).astype(np.float32)
        tv = (v - 0.30) / 0.40
        shoulder = ((tv < 0.16) | (tv > 0.84)).astype(np.float32)
        h_t = 1.0 - lat[None, :] * shoulder[:, None]
        h = np.where(tread[:, None], h_t * 0.9 + 0.03 * nz, h)
        col = np.where(tread[:, None], 0.024, col)
    else:
        h = np.where(tread[:, None], 0.5 + 0.02 * nz, h)
        col = np.where(tread[:, None], 0.020 + 0.006 * nz, col)
    # lettering on both sidewalls (raised): drawn upside down because the image grows toward the bead
    letters = Image.new("L", (2 * W, H), 0)       # drawn on a double-width strip, then folded so text wraps at u=0/1
    for side_v, flip in ((0.84, True), (0.16, False)):
        y = (1.0 - side_v) * H
        for rep in range(2):
            cx = W * (0.25 + 0.5 * rep)
            txt = Image.new("L", (W // 2, int(0.12 * H)), 0)
            ImageDraw.Draw(txt).text((W // 4, int(0.06 * H)), brand, font=font("free_bold_obl", int(0.085 * H)), fill=255,
                                     anchor="mm")
            if flip:
                txt = txt.rotate(180)
            letters.paste(txt, (int(cx - W // 4), int(y - 0.06 * H)), txt)
            txt2 = Image.new("L", (W // 2, int(0.05 * H)), 0)
            ImageDraw.Draw(txt2).text((W // 4, int(0.025 * H)), small, font=font("sans_bold", int(0.028 * H)), fill=200,
                                      anchor="mm")
            if flip:
                txt2 = txt2.rotate(180)
            off = -0.085 if flip else 0.085
            cx2 = cx + W * 0.25
            letters.paste(txt2, (int(cx2 - W // 4), int(y + off * H - 0.025 * H)), txt2)
    la = np.asarray(letters, np.float32)
    letters = Image.fromarray(np.clip(la[:, :W] + la[:, W:], 0, 255).astype(np.uint8))
    L = np.asarray(letters, np.float32) / 255.0
    h = np.clip(h + 0.6 * L, 0, 1.5)
    rgb = np.stack([col, col, col], -1)
    tc = np.array(tcol, np.float32) / 255.0
    lt = np.clip(L, 0, 1)[..., None]
    rgb = rgb * (1 - lt * 0.85) + (tc ** 2.2)[None, None, :] * lt * 0.85
    save(rgb ** (1 / 2.2), os.path.join(out_dir, f"s1x_tire_{key}_b.color.png"))
    save(normal_from_height(np.asarray(Image.fromarray((h * 160).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                                       np.float32) / 160.0, 4.0, wrap=False),
         os.path.join(out_dir, f"s1x_tire_{key}_nm.normal.png"))


# ---------------------------------------------------------------------------
GENERATORS = {
    "gauges_s13": lambda m: gauges_s13(os.path.join(m, "vehicles/s13_240sx/textures")),
    "glass_dmg_s13": lambda m: glass_dmg(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "lens_s13": lambda m: lens_normals(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "cloth_s13": lambda m: seat_cloth(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "radio_s13": lambda m: radio(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "hvac_s13": lambda m: hvac(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "racetach_s13": lambda m: race_tach(os.path.join(m, "vehicles/s13_240sx/textures"), "s13"),
    "brushed": lambda m: brushed_normal(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "ivtec": lambda m: ivtec_plaque(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "liveries_s13": lambda m: __import__("tools.textures.liveries", fromlist=["generate"]).generate(
        os.path.join(m, "vehicles/s13_240sx/textures")),
    "gauges_s14": lambda m: gauges_s13(os.path.join(m, "vehicles/s14_240sx/textures"), "s14", style="s14"),
    "glass_dmg_s14": lambda m: glass_dmg(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "lens_s14": lambda m: lens_normals(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "cloth_s14": lambda m: seat_cloth(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "radio_s14": lambda m: radio(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "hvac_s14": lambda m: hvac_s14(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "racetach_s14": lambda m: race_tach(os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "liveries_s14": lambda m: __import__("tools.textures.liveries", fromlist=["generate"]).generate(
        os.path.join(m, "vehicles/s14_240sx/textures"), "s14"),
    "cast": lambda m: cast_normal(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "crinkle": lambda m: crinkle_normal(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "rotor": lambda m: rotor_normal(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "core": lambda m: core(os.path.join(m, "vehicles/common/s1x_240sx/textures")),
    "tire_street": lambda m: tire(os.path.join(m, "vehicles/common/s1x_240sx/textures"), "street"),
    "tire_semi": lambda m: tire(os.path.join(m, "vehicles/common/s1x_240sx/textures"), "semi"),
    "tire_slick": lambda m: tire(os.path.join(m, "vehicles/common/s1x_240sx/textures"), "slick"),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    only = [s for s in a.only.split(",") if s]
    for k, fn in GENERATORS.items():
        if only and k not in only:
            continue
        fn(a.mod)
        print("texture:", k)


if __name__ == "__main__":
    main()
