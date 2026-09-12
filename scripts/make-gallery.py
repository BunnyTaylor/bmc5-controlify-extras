#!/usr/bin/env python3
"""Render the Modrinth/GitHub gallery images into media/.

Everything is drawn at 2x and downsampled, which is what keeps the wedge edges
and text clean. Run after changing the radial layout so the art stays truthful:

    scripts/make-gallery.py
"""
from __future__ import annotations

import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"
W, H, SS = 1280, 720, 2

BG      = (20, 22, 27)
CARD    = (28, 31, 38)
WEDGE   = (52, 58, 70)
WEDGE_2 = (44, 49, 60)
HI      = (94, 214, 160)
TEXT    = (236, 239, 244)
MUTED   = (138, 147, 163)
RING    = (20, 22, 27)

# RadialMenuScreen places item i at  angle = 2*pi*i/len - pi/2, so each item is
# CENTRED on its direction and i=0 sits at 12 o'clock, running clockwise. The
# wedges below are therefore centred on the angle, not started at it. Keep this
# list in the same order as
# pack/assets/controlify/controllers/default_config/default.json.
SLOTS = [
    "Xaero World Map",
    "Accessories",
    "Open Backpack",
    "Ender Chest",
    "Quest Book",
    "Ping Location",
    "New Waypoint",
    "Waypoint List",
]


def font(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size * SS)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def radial_image() -> Image.Image:
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    d.text((64 * SS, 44 * SS), "BMC5 Controlify Extras", font=font(40, "Bold"), fill=TEXT)
    d.text((64 * SS, 100 * SS),
           "Eight modpack actions on one button — no keyboard, no Steam Input remap.",
           font=font(20), fill=MUTED)

    cx, cy = 640 * SS, 416 * SS
    outer, inner, label_r = 138 * SS, 53 * SS, 198 * SS

    for i in range(8):
        centre = -90 + i * 45
        a0 = centre - 22.5 + 1.4
        a1 = centre + 22.5 - 1.4
        fill = HI if i == 0 else (WEDGE if i % 2 == 0 else WEDGE_2)
        d.pieslice([cx - outer, cy - outer, cx + outer, cy + outer], a0, a1, fill=fill)

    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=RING)
    nub = 17 * SS
    ny = cy - inner * 0.44
    d.ellipse([cx - nub, ny - nub, cx + nub, ny + nub], fill=HI)

    lf = font(21, "SemiBold")
    for i, name in enumerate(SLOTS):
        mid = math.radians(-90 + i * 45)
        x, y = cx + label_r * math.cos(mid), cy + label_r * math.sin(mid)
        c = math.cos(mid)
        anchor = "lm" if c > 0.35 else "rm" if c < -0.35 else "mm"
        d.text((x, y), name, font=lf, fill=TEXT if i == 0 else MUTED, anchor=anchor)

    d.text((640 * SS, 682 * SS),
           "D-Pad Right, then flick the right stick   ·   Minecraft 1.21.1   ·   requires Controlify",
           font=font(18), fill=MUTED, anchor="mm")
    return img.resize((W, H), Image.LANCZOS)


def paddle_image() -> Image.Image:
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    d.text((64 * SS, 44 * SS), "Paddles & back buttons", font=font(40, "Bold"), fill=TEXT)
    d.text((64 * SS, 100 * SS),
           "Holds can't live in a radial menu, so they get a button of their own.",
           font=font(20), fill=MUTED)

    rows = [
        ("L4", "Zoom", "hold  ·  JustZoom"),
        ("L5", "Vein Mining", "hold  ·  shipped unbound, so the mod was inert"),
        ("R4", "Open Backpack", "the pack you're wearing — no hotbar shuffle"),
        ("R5", "Xaero World Map", "instant, and still in the radial"),
    ]
    x, y, rw, rh, gap = 64 * SS, 176 * SS, 1152 * SS, 86 * SS, 16 * SS
    for tag, title, sub in rows:
        d.rounded_rectangle([x, y, x + rw, y + rh], radius=12 * SS, fill=CARD)
        d.rounded_rectangle([x, y, x + 8 * SS, y + rh], radius=4 * SS, fill=HI)
        d.text((x + 40 * SS, y + rh / 2), tag, font=font(26, "Bold"), fill=HI, anchor="lm")
        d.text((x + 130 * SS, y + rh / 2), title, font=font(25, "SemiBold"), fill=TEXT, anchor="lm")
        d.text((x + rw - 34 * SS, y + rh / 2), sub, font=font(19), fill=MUTED, anchor="rm")
        y += rh + gap

    d.text((64 * SS, y + 26 * SS),
           "Steam Deck: Controlify 3.0.1 disables its Deck driver, so the back buttons never reach the game.",
           font=font(19, "SemiBold"), fill=TEXT)
    d.text((64 * SS, y + 58 * SS),
           "The radial menu needs none of them — and the installer sets up a Steam Input fallback if you want them anyway.",
           font=font(19), fill=MUTED)
    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parent.parent / "media"
    out.mkdir(exist_ok=True)
    for name, im in (("radial-menu", radial_image()), ("paddles", paddle_image())):
        p = out / f"{name}.png"
        im.save(p, optimize=True)
        print(f"wrote {p.relative_to(p.parent.parent)}  ({p.stat().st_size // 1024} KB)")
