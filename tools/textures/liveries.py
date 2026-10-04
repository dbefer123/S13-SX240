"""Colour-palette liveries (fully colourable skins) drawn in vehicle coordinates.

The body panels' UV1 is the livery atlas written by tools/model/build_meshes.livery_uv:
    left side  : u = (y + 2.6) s,        v = 0.74 + z s
    right side : u = (2.6 - y) s,        v = 0.48 + z s
    plan (top) : u = (y + 2.6) s,        v = 0.146 + (x + 0.9) s
    front      : u = (x + 0.9) s,        v = z s   (clamped)
    rear       : u = 0.5 + (0.9 - x) s,  v = z s   (clamped)
with s = 1 / 5.2.  Each livery is a function f(region, x, y, z) -> (r, g, b) weights for
paint slots 1/2/3 (red channel = paint 1, green = paint 2, blue = paint 3).
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = 1.0 / 5.2
N = 2048
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _coords():
    """Per-pixel (region, x, y, z) arrays for the atlas."""
    u = (np.arange(N) + 0.5) / N
    v = 1.0 - (np.arange(N) + 0.5) / N                 # image row 0 = v 1
    U, V = np.meshgrid(u, v)
    region = np.full(U.shape, "", dtype=object)
    X = np.zeros_like(U); Y = np.zeros_like(U); Z = np.zeros_like(U)
    m = V >= 0.74
    region[m] = "L"; Y[m] = U[m] / S - 2.6; Z[m] = (V[m] - 0.74) / S; X[m] = 0.85
    m = (V >= 0.48) & (V < 0.74)
    region[m] = "R"; Y[m] = 2.6 - U[m] / S; Z[m] = (V[m] - 0.48) / S; X[m] = -0.85
    m = (V >= 0.146) & (V < 0.48)
    region[m] = "T"; Y[m] = U[m] / S - 2.6; X[m] = (V[m] - 0.146) / S - 0.9; Z[m] = 1.0
    m = (V < 0.146) & (U < 0.5)
    region[m] = "F"; X[m] = U[m] / S - 0.9; Z[m] = V[m] / S; Y[m] = -2.3
    m = (V < 0.146) & (U >= 0.5)
    region[m] = "B"; X[m] = 0.9 - (U[m] - 0.5) / S; Z[m] = V[m] / S; Y[m] = 2.3
    return region, X, Y, Z


def _smooth(a, w=0.006):
    return np.clip(a / w + 0.5, 0, 1)


def livery_two_tone(region, X, Y, Z):
    """Factory two-tone: paint 2 below the side rub strip, paint 1 above."""
    side = (region == "L") | (region == "R")
    lower = side & (Z < 0.343)
    fr = (region == "F") | (region == "B")
    lower |= fr & (Z < 0.343)
    w2 = lower.astype(float)
    return 1 - w2, w2, np.zeros_like(w2)


def livery_stripes(region, X, Y, Z):
    """Twin racing stripes over hood, roof and hatch + matching bumper stripes (paint 2)."""
    top = region == "T"
    st = top & (((np.abs(X) > 0.07) & (np.abs(X) < 0.20)))
    fr = ((region == "F") | (region == "B")) & (np.abs(X) > 0.07) & (np.abs(X) < 0.20) & (Z > 0.26)
    w2 = (st | fr).astype(float)
    return 1 - w2, w2, np.zeros_like(w2)


def _roundel(img_rgb, centers, radius_px, number, fill_ch, text_ch):
    """Draw number roundels (circle in fill channel, digits in text channel) on the RGB weight image."""
    pil = Image.fromarray((img_rgb * 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    font = ImageFont.truetype(FONT, int(radius_px * 1.15))
    for cx, cy, flip in centers:
        col = [0, 0, 0]
        col[fill_ch] = 255
        d.ellipse([cx - radius_px, cy - radius_px, cx + radius_px, cy + radius_px], fill=tuple(col))
        tcol = [0, 0, 0]
        tcol[text_ch] = 255
        timg = Image.new("RGB", (int(radius_px * 2), int(radius_px * 2)), (0, 0, 0))
        ImageDraw.Draw(timg).text((radius_px, radius_px), number, font=font, fill=(255, 255, 255), anchor="mm")
        mask = timg.convert("L")
        if flip:
            mask = mask.transpose(Image.FLIP_LEFT_RIGHT)
        pil.paste(Image.new("RGB", mask.size, tuple(tcol)), (int(cx - radius_px), int(cy - radius_px)), mask)
    return np.asarray(pil, np.float32) / 255.0


def _uv_px(region, y, z):
    if region == "L":
        u, v = (y + 2.6) * S, 0.74 + z * S
    else:
        u, v = (2.6 - y) * S, 0.48 + z * S
    return u * N, (1 - v) * N


def livery_imsa(region, X, Y, Z):
    """GTO tribute: white top (paint 1), red swoosh rising toward the rear (paint 2), blue lower body (paint 3)."""
    side = (region == "L") | (region == "R")
    yy = np.where(region == "R", Y, Y)
    band_lo = 0.36 + 0.05 * (yy + 2.3) / 4.6
    band_hi = band_lo + 0.11 + 0.10 * np.clip((yy + 0.6) / 2.8, 0, 1)
    blue = side & (Z < band_lo)
    red = side & (Z >= band_lo) & (Z < band_hi)
    fr = (region == "F") | (region == "B")
    blue |= fr & (Z < 0.33)
    red |= fr & (Z >= 0.33) & (Z < 0.40)
    top = region == "T"
    red |= top & (np.abs(X) < 0.16) & (Y < -0.85)                  # hood centre stripe
    blue |= top & (np.abs(X) < 0.06) & (Y < -0.85)
    b = blue.astype(float)
    g = red.astype(float) * (1 - b)
    r = 1 - g - b
    return r, g, b


def livery_track(region, X, Y, Z):
    """Track livery: paint 1 base, paint 2 diagonal splash from the front wheel, paint 3 sills and number board."""
    side = (region == "L") | (region == "R")
    diag = side & ((Z - 0.20) < 0.75 * (-0.4 - Y) + 0.55) & ((Z - 0.20) > 0.75 * (-0.4 - Y) + 0.15)
    sill = side & (Z < 0.30)
    top = region == "T"
    hood = top & (Y < -1.4) & (np.abs(X) < 0.55)
    g = (diag | hood).astype(float)
    b = sill.astype(float) * (1 - g)
    r = 1 - g - b
    return r, g, b


def livery_drift(region, X, Y, Z):
    """Drift two-tone: paint 2 front half, paint 3 hood/roof stripe; hard diagonal split on the doors."""
    side = (region == "L") | (region == "R")
    split = side & (Y < 0.2 - 0.6 * (Z - 0.2))
    fr = region == "F"
    top = (region == "T") & (np.abs(X) < 0.30)
    g = (split | fr).astype(float)
    b = top.astype(float) * (1 - g)
    r = 1 - g - b
    return r, g, b


LIVERIES = {
    "twotone": ("Factory Two-Tone", livery_two_tone, None),
    "stripes": ("Twin Racing Stripes", livery_stripes, None),
    "imsa": ("IMSA GTO Tribute Livery", livery_imsa, ("13", 2, 2)),      # roundel in paint 1 (R) with number in paint 3
    "track": ("Tractive Racing Track Livery", livery_track, ("27", 0, 2)),
    "drift": ("Drift Two-Tone Livery", livery_drift, None),
}


def generate(out_dir, prefix="s13"):
    os.makedirs(out_dir, exist_ok=True)
    region, X, Y, Z = _coords()
    paths = {}
    for key, (title, fn, number) in LIVERIES.items():
        r, g, b = fn(region, X, Y, Z)
        rgb = np.stack([r, g, b], -1).astype(np.float32)
        empty = region == ""
        rgb[empty] = (1, 0, 0)
        if number:
            num, _, text_ch = number
            centers = []
            for reg, flip in (("L", False), ("R", False)):
                cx, cy = _uv_px(reg, 0.0 if reg == "L" else 0.0, 0.62)
                centers.append((cx, cy, flip))
            rgb = _roundel(rgb, centers, int(0.16 * S * N), num, 0, text_ch)
            # hood roundel (plan view)
            cx, cy = ((-1.45 + 2.6) * S) * N, (1 - (0.146 + 0.9 * S)) * N
            rgb = _roundel(rgb, [(cx, cy, False)], int(0.15 * S * N), num, 0, text_ch)
        img = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
        p = os.path.join(out_dir, f"{prefix}_livery_{key}.color.png")
        img.save(p, optimize=True)
        paths[key] = p
    return paths


if __name__ == "__main__":
    import sys
    print(generate(sys.argv[1] if len(sys.argv) > 1 else "mod/vehicles/s13_240sx/textures"))
