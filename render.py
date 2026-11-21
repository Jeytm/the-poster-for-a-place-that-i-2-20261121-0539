#!/usr/bin/env python3
"""Render the travel poster for KESSARIN — an invented cliffside town above a
lagoon at dusk, lit by its Lantern Spire. Drawn entirely in code (Pillow).

Deterministic: every random choice comes from random.Random(20261121).
Output: entry.png, 1024x1024.
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1024, 1024
RNG = random.Random(20261121)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, stops):
    """Vertical gradient through (position, color) stops."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                lt = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                px[0, y] = lerp(c0, c1, lt)
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((w, h))


def glow_layer(size):
    """Transparent layer to paint glows on, then blur + composite."""
    return Image.new("RGBA", size, (0, 0, 0, 0))


def add_glow(base, cx, cy, radius, color, alpha):
    """Soft radial glow centred at (cx, cy)."""
    layer = glow_layer(base.size)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    base.alpha_composite(layer)


def spaced_text(draw, cx, y, text, font, fill, tracking=0.16, shadow=None):
    """Draw text centred on cx with letter tracking (fraction of font size)."""
    widths = []
    total = 0
    for ch in text:
        w = draw.textlength(ch, font=font)
        widths.append(w)
        total += w
    total += tracking * font.size * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        if shadow is not None:
            draw.text((x + 3, y + 4), ch, font=font, fill=shadow)
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking * font.size
    return total


def soft_blob(draw, box, color, blur=18):
    """Draw a filled ellipse on a temp layer, blur it, return the layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=color)
    return layer.filter(ImageFilter.GaussianBlur(blur))


def render():
    img = Image.new("RGBA", (W, H))

    # ---- sky: deep indigo -> violet -> rose -> warm amber at horizon ----
    sky = vgrad((W, 580), [
        (0.00, (24, 20, 58)),
        (0.35, (58, 38, 96)),
        (0.62, (128, 62, 108)),
        (0.85, (206, 110, 96)),
        (1.00, (238, 158, 96)),
    ])
    img.paste(sky, (0, 0))

    # ---- stars (denser and brighter near the top) ----
    d = ImageDraw.Draw(img)
    for _ in range(260):
        x = RNG.uniform(0, W)
        y = RNG.uniform(0, 430) ** 1.15 / (430 ** 0.15)
        y = min(y, 430)
        r = RNG.choice([1, 1, 1, 2, 2, 3])
        a = int(RNG.uniform(90, 235) * (1 - y / 620))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 220, max(a, 40)))
    # a few bright stars with a sparkle cross
    for _ in range(12):
        x = RNG.uniform(40, W - 40)
        y = RNG.uniform(20, 300)
        d.line([x - 7, y, x + 7, y], fill=(255, 250, 235, 220), width=1)
        d.line([x, y - 7, x, y + 7], fill=(255, 250, 235, 220), width=1)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 250, 235, 255))

    # ---- moon + halo, upper right ----
    add_glow(img, 828, 268, 150, (250, 226, 178), 110)
    add_glow(img, 828, 268, 70, (255, 244, 214), 150)
    d = ImageDraw.Draw(img)
    d.ellipse([776, 216, 880, 320], fill=(252, 242, 214, 255))
    d.ellipse([800, 240, 830, 268], fill=(238, 224, 192, 255))
    d.ellipse([842, 272, 862, 290], fill=(240, 228, 196, 255))
    d.ellipse([788, 282, 806, 298], fill=(242, 230, 200, 255))

    # ---- clouds: soft rose / lavender bands ----
    for (cy, cw, ch, col, al) in [
        (150, 420, 26, (214, 150, 158), 90),
        (205, 520, 30, (196, 128, 158), 80),
        (300, 380, 24, (226, 168, 150), 70),
        (380, 460, 28, (206, 140, 150), 75),
        (455, 300, 22, (232, 176, 140), 65),
    ]:
        cx = RNG.uniform(120, W - 120)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        for k in range(5):
            ox = cx - cw / 2 + k * cw / 5 + RNG.uniform(-14, 14)
            oy = cy + RNG.uniform(-8, 8)
            rw = cw / 3.4 + RNG.uniform(-12, 12)
            dd.ellipse([ox - rw, oy - ch / 2, ox + rw, oy + ch / 2],
                       fill=col + (al,))
        layer = layer.filter(ImageFilter.GaussianBlur(16))
        img.alpha_composite(layer)

    # ---- distant headland silhouette on the horizon, right side ----
    d = ImageDraw.Draw(img)
    d.polygon([(700, 560), (760, 512), (830, 528), (900, 505),
               (965, 540), (1024, 522), (1024, 560)],
              fill=(52, 34, 72, 255))

    # ---- sea: teal at horizon -> deep blue at the bottom ----
    sea = vgrad((W, H - 560), [
        (0.00, (30, 98, 112)),
        (0.30, (22, 76, 98)),
        (0.65, (14, 52, 78)),
        (1.00, (8, 30, 56)),
    ])
    img.paste(sea, (0, 560))

    # ---- moon reflection column on the water ----
    for _ in range(170):
        x = 828 + RNG.gauss(0, 52)
        y = RNG.uniform(566, 1010)
        ln = RNG.uniform(8, 46) * (1 - (y - 560) / 900) + 4
        a = int(RNG.uniform(40, 150) * (1 - (y - 560) / 1100))
        d = ImageDraw.Draw(img)
        d.line([x - ln / 2, y, x + ln / 2, y],
               fill=(252, 226, 170, max(a, 18)), width=2)
    # scattered sparkle across the sea
    for _ in range(120):
        x = RNG.uniform(0, W)
        y = RNG.uniform(575, 1000)
        d = ImageDraw.Draw(img)
        d.point((x, y), fill=(190, 220, 220, RNG.randint(40, 120)))

    # ---- cliff headland (left), dark plum with a warm lit rim ----
    d = ImageDraw.Draw(img)
    cliff = [(0, 560), (0, 430), (60, 400), (130, 372), (205, 348),
             (280, 322), (350, 300), (420, 288), (470, 300), (520, 330),
             (560, 380), (580, 440), (585, 560)]
    d.polygon(cliff, fill=(46, 30, 62, 255))
    # warm rim light along the cliff top edge
    for i in range(len(cliff) - 2):
        x0, y0 = cliff[i + 1]
        x1, y1 = cliff[i + 2]
        d.line([x0, y0, x1, y1], fill=(238, 164, 104, 200), width=3)
    # cliff facets / texture strokes (short, contour-hugging, subtle)
    for _ in range(22):
        x = RNG.uniform(10, 560)
        y = RNG.uniform(330, 555)
        ln = RNG.uniform(8, 26)
        d.line([x, y, x + ln, y + RNG.uniform(-3, 6)],
               fill=(70, 48, 88, 90), width=2)
    for _ in range(18):
        x = RNG.uniform(10, 540)
        y = RNG.uniform(340, 545)
        d.line([x, y, x + RNG.uniform(10, 30), y + RNG.uniform(-3, 3)],
               fill=(96, 70, 110, 70), width=2)

    # ---- the town: whitewashed houses stacked on the cliff ----
    houses = []
    rows = [
        # back terrace: smaller houses higher on the cliff, drawn first
        (90, 92, 30, 34), (150, 100, 28, 32), (215, 88, 32, 36),
        (285, 96, 30, 34), (350, 104, 28, 32), (410, 90, 30, 34),
        (120, 118, 26, 30), (260, 122, 28, 30), (330, 118, 26, 30),
        # front row
        (330, 12, 46, 62), (368, 10, 40, 54), (402, 9, 44, 58),
        (300, 14, 52, 70), (255, 16, 44, 60), (210, 18, 48, 66),
        (160, 20, 42, 56), (115, 22, 46, 62), (70, 24, 44, 58),
        (350, 26, 40, 52), (305, 28, 46, 60), (255, 30, 42, 54),
        (200, 32, 48, 62), (145, 34, 44, 58), (95, 36, 40, 52),
        (45, 38, 44, 60), (385, 40, 36, 48), (330, 42, 40, 54),
        (270, 44, 44, 58), (205, 46, 40, 52), (140, 48, 44, 58),
        (80, 50, 38, 50), (30, 52, 40, 54), (430, 44, 42, 56),
        (470, 52, 38, 50), (500, 66, 40, 54),
    ]
    wall_tones = [(244, 226, 200), (238, 210, 182), (250, 234, 214),
                  (232, 200, 176), (246, 220, 190)]
    roof_tones = [(146, 74, 52), (128, 62, 48), (164, 88, 58),
                  (112, 56, 52)]
    for (hx, hy, hw, hh) in rows:
        tone = RNG.choice(wall_tones)
        roof = RNG.choice(roof_tones)
        top = 470 - hy - hh
        d.rectangle([hx, top, hx + hw, 470 - hy], fill=tone + (255,))
        # pitched roof
        d.polygon([(hx - 3, top), (hx + hw / 2, top - 14),
                   (hx + hw + 3, top)], fill=roof + (255,))
        # chimney
        if RNG.random() < 0.6:
            cx = hx + hw - 10
            d.rectangle([cx, top - 20, cx + 7, top - 8], fill=(120, 92, 84, 255))
        houses.append((hx, top, hw, hh))
    # windows: warm lit rectangles with a soft glow
    win_glow = glow_layer(img.size)
    wd = ImageDraw.Draw(win_glow)
    for (hx, top, hw, hh) in houses:
        cols = max(1, hw // 16)
        rws = max(1, hh // 24)
        for c in range(cols):
            for r in range(rws):
                if RNG.random() < 0.72:
                    wx = hx + 5 + c * 15 + RNG.uniform(-1, 1)
                    wy = top + 6 + r * 20 + RNG.uniform(-1, 1)
                    lit = RNG.random() < 0.86
                    col = (255, 196, 110, 255) if lit else (52, 44, 66, 255)
                    d.rectangle([wx, wy, wx + 7, wy + 10], fill=col)
                    if lit:
                        wd.ellipse([wx - 4, wy - 4, wx + 11, wy + 14],
                                   fill=(255, 180, 90, 70))
    win_glow = win_glow.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(win_glow)
    # chimney smoke wisps
    for (hx, top, hw, hh) in houses[:8]:
        if RNG.random() < 0.7:
            sx = hx + hw - 7
            sy = top - 22
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(layer)
            for k in range(4):
                dd.ellipse([sx - 8 + k * 5, sy - 26 - k * 14,
                            sx + 8 + k * 5, sy - 12 - k * 14],
                           fill=(220, 210, 205, 46))
            layer = layer.filter(ImageFilter.GaussianBlur(7))
            img.alpha_composite(layer)

    # ---- cypress silhouettes among the houses ----
    d = ImageDraw.Draw(img)
    for (tx, ty, th) in [(120, 380, 46), (250, 330, 54), (395, 300, 48),
                         (500, 360, 40), (60, 420, 38)]:
        d.ellipse([tx - 7, ty - th, tx + 7, ty], fill=(26, 40, 34, 255))
        d.polygon([(tx - 7, ty - th + 12), (tx, ty - th - 8),
                   (tx + 7, ty - th + 12)], fill=(26, 40, 34, 255))

    # ---- THE LANTERN SPIRE — the landmark, on the cliff edge ----
    # Beacon sits below the name band so its rays never cross the title.
    sx0, sx1 = 448, 478
    stop, sbot = 268, 470
    d = ImageDraw.Draw(img)
    # tower body, warm stone in the dusk light
    d.polygon([(sx0, sbot), (sx0 + 4, stop + 34), (sx1 - 4, stop + 34),
               (sx1, sbot)], fill=(236, 214, 182, 255))
    # stone banding
    for yy in range(stop + 60, sbot - 10, 34):
        d.line([sx0 + 2, yy, sx1 - 2, yy], fill=(196, 164, 138, 255), width=2)
    # small arched windows up the tower, lit
    for yy in range(stop + 52, sbot - 30, 44):
        d.ellipse([sx0 + 11, yy, sx1 - 11, yy + 18], fill=(255, 196, 110, 255))
    # beacon housing + dome
    d.rectangle([sx0 - 4, stop + 8, sx1 + 4, stop + 34], fill=(72, 44, 40, 255))
    d.ellipse([sx0 - 2, stop - 12, sx1 + 2, stop + 12], fill=(146, 74, 52, 255))
    # the beacon flame + strong glow + short rays (kept below the title)
    add_glow(img, 463, stop - 2, 90, (255, 190, 90), 170)
    add_glow(img, 463, stop - 2, 38, (255, 220, 140), 220)
    d = ImageDraw.Draw(img)
    d.ellipse([453, stop - 14, 473, stop + 8], fill=(255, 232, 160, 255))
    d.ellipse([458, stop - 8, 468, stop + 2], fill=(255, 250, 220, 255))
    for ang in (-58, -32, -12, 12, 32, 58):
        import math
        rad = math.radians(ang - 90)
        x2 = 463 + math.cos(rad) * 78
        y2 = stop - 2 + math.sin(rad) * 78
        d.line([463, stop - 2, x2, y2], fill=(255, 214, 130, 70), width=3)
    # beacon reflection on the water below the cliff
    for _ in range(70):
        x = 463 + RNG.gauss(0, 26)
        y = RNG.uniform(570, 900)
        ln = RNG.uniform(6, 30)
        a = int(RNG.uniform(40, 130) * (1 - (y - 560) / 900))
        d.line([x - ln / 2, y, x + ln / 2, y],
               fill=(255, 196, 110, max(a, 16)), width=2)

    # ---- foreground rocks, bottom left, with foam ----
    d = ImageDraw.Draw(img)
    rocks = [(0, 1024), (0, 940), (70, 912), (140, 936), (210, 918),
             (268, 950), (320, 980), (330, 1024)]
    d.polygon(rocks, fill=(30, 22, 44, 255))
    d.polygon([(0, 1024), (0, 962), (90, 940), (180, 962), (260, 946),
               (300, 972), (330, 1000), (330, 1024)], fill=(44, 32, 58, 255))
    for _ in range(26):
        x = RNG.uniform(0, 330)
        y = RNG.uniform(920, 1000)
        d.arc([x - 5, y - 3, x + 5, y + 3], 180, 360,
              fill=(220, 235, 235, RNG.randint(50, 110)), width=2)
    for _ in range(20):
        x = RNG.uniform(0, 320)
        y = RNG.uniform(930, 990)
        d.point((x, y), fill=(230, 240, 240, RNG.randint(50, 110)))

    # ---- a small lantern boat on the lagoon ----
    bx, by = 690, 800
    d = ImageDraw.Draw(img)
    d.polygon([(bx - 34, by), (bx + 34, by), (bx + 22, by + 14),
               (bx - 22, by + 14)], fill=(52, 30, 34, 255))
    d.polygon([(bx - 2, by - 52), (bx - 2, by), (bx + 26, by)],
              fill=(250, 238, 210, 255))
    d.line([bx, by - 56, bx, by], fill=(60, 40, 36, 255), width=3)
    add_glow(img, bx - 8, by - 6, 26, (255, 190, 100), 160)
    d = ImageDraw.Draw(img)
    d.ellipse([bx - 13, by - 11, bx - 3, by - 1], fill=(255, 214, 130, 255))
    # boat reflection
    for _ in range(26):
        x = bx + RNG.gauss(0, 20)
        y = by + 18 + RNG.uniform(0, 60)
        d.line([x - 8, y, x + 8, y], fill=(250, 220, 170, RNG.randint(30, 90)),
               width=2)

    # ---- birds ----
    d = ImageDraw.Draw(img)
    for _ in range(7):
        x = RNG.uniform(120, 900)
        y = RNG.uniform(180, 420)
        s = RNG.uniform(6, 12)
        d.arc([x - s, y - s * 0.6, x, y + s * 0.6], 200, 340,
              fill=(30, 24, 48, 220), width=2)
        d.arc([x, y - s * 0.6, x + s, y + s * 0.6], 200, 340,
              fill=(30, 24, 48, 220), width=2)

    # ---- fine grain over the whole poster (richness + file size) ----
    noise = Image.effect_noise((W, H), 10).convert("RGBA")
    noise.putalpha(5)
    img.alpha_composite(noise)

    # ---- poster frame + name ----
    d = ImageDraw.Draw(img)
    d.rectangle([26, 26, W - 26, H - 26], outline=(250, 240, 210, 170), width=3)
    d.rectangle([34, 34, W - 34, H - 34], outline=(250, 240, 210, 90), width=1)

    name_font = ImageFont.truetype(SERIF_BOLD, 96)
    spaced_text(d, W // 2, 62, "KESSARIN", name_font,
                fill=(252, 244, 222, 255), tracking=0.22,
                shadow=(18, 12, 44, 200))
    # thin rule + diamond under the name
    d.line([W // 2 - 150, 178, W // 2 - 16, 178], fill=(252, 244, 222, 220), width=2)
    d.line([W // 2 + 16, 178, W // 2 + 150, 178], fill=(252, 244, 222, 220), width=2)
    d.polygon([(W // 2, 170), (W // 2 + 8, 178), (W // 2, 186), (W // 2 - 8, 178)],
              fill=(252, 244, 222, 255))

    return img.convert("RGB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = render()
    img.save(out, "PNG")
    print(out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
