#!/usr/bin/env python3
"""Game-style board drawing primitives (palette and cat sprite from the level-155 screenshot)."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

PAL = {
    "purple": (137, 121, 218), "yellow": (251, 217, 131), "pink": (248, 155, 229),
    "brown": (168, 109, 74), "orange": (250, 157, 92), "green": (139, 213, 125),
    "dgreen": (42, 140, 83), "blue": (56, 169, 192), "rose": (211, 111, 143),
    "gold": (205, 164, 0), "gray": (226, 219, 214),
}
PAGE = (247, 242, 239)
INK = (140, 92, 92)        # the game's mauve text colour
RED = (225, 70, 70)
S = 3                      # oversampling
CAT = Image.open(os.path.join(HERE, "cat.png")).convert("RGBA")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15 * S)
FONT_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15 * S)


def board(rows, cols, colors=None, xs=(), cats=(), rings=(), outlines=(), dots=(),
          cell=64, gap=7, pad=12, labels=None):
    """Draw one board panel (white rounded card) at oversampled scale."""
    colors = colors or {}
    cs, gs, ps = cell * S, gap * S, pad * S
    W = ps * 2 + cols * cs + (cols - 1) * gs
    H = ps * 2 + rows * cs + (rows - 1) * gs
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)

    def xy(r, c):
        return ps + c * (cs + gs), ps + r * (cs + gs)

    for r in range(rows):
        for c in range(cols):
            x, y = xy(r, c)
            col = colors.get((r, c), "gray")
            col = PAL[col] if isinstance(col, str) else col
            d.rounded_rectangle([x, y, x + cs, y + cs], radius=10 * S, fill=col)
    for (r, c) in xs:
        x, y = xy(r, c)
        cx, cy = x + cs / 2, y + cs / 2
        a = cs * 0.30
        w = int(cs * 0.115)
        for (dx1, dy1, dx2, dy2) in ((-a, -a, a, a), (-a, a, a, -a)):
            d.line([cx + dx1, cy + dy1, cx + dx2, cy + dy2], fill="white", width=w)
            for (dx, dy) in ((dx1, dy1), (dx2, dy2)):
                d.ellipse([cx + dx - w / 2, cy + dy - w / 2, cx + dx + w / 2, cy + dy + w / 2], fill="white")
    for (r, c) in dots:
        x, y = xy(r, c)
        cx, cy = x + cs / 2, y + cs / 2
        d.ellipse([cx - cs * 0.11, cy - cs * 0.11, cx + cs * 0.11, cy + cs * 0.11],
                  fill=(255, 255, 255, 230))
    for (r, c) in rings:
        x, y = xy(r, c)
        d.rounded_rectangle([x - 2 * S, y - 2 * S, x + cs + 2 * S, y + cs + 2 * S],
                            radius=12 * S, outline=(255, 205, 60), width=4 * S)
    for (r, c) in cats:
        x, y = xy(r, c)
        sz = int(cs * 0.80)
        cat = CAT.resize((sz, int(sz * CAT.height / CAT.width)), Image.LANCZOS)
        im.alpha_composite(cat, (int(x + (cs - cat.width) / 2), int(y + (cs - cat.height) / 2)))
    if labels:
        lf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(cs * 0.42))
        for (r, c), text in labels.items():
            x, y = xy(r, c)
            tw = d.textlength(str(text), font=lf)
            d.text((x + (cs - tw) / 2, y + cs * 0.22), str(text), fill=(70, 45, 45), font=lf)
    for (r0, c0, r1, c1, colour) in outlines:
        x0, y0 = xy(r0, c0)
        x1, y1 = xy(r1, c1)
        d.rounded_rectangle([x0 - gs * 0.5, y0 - gs * 0.5, x1 + cs + gs * 0.5, y1 + cs + gs * 0.5],
                            radius=13 * S, outline=colour, width=3 * S)
    return im


def figure(name, panels, captions=None, arrows=False, gapx=26):
    """Lay panels out side by side on the page background with captions."""
    captions = captions or [""] * len(panels)
    gx = gapx * S
    arrow_w = 40 * S if arrows else 0
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

    def wrap(text, width):
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if dummy.textlength(trial, font=FONT) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines
    wrapped = [wrap(c, p.width + gx * 0.8) if c else [] for c, p in zip(captions, panels)]
    nlines = max((len(w) for w in wrapped), default=0)
    text_h = (10 + 20 * nlines) * S if nlines else 0
    W = gx * 2 + sum(p.width for p in panels) + (len(panels) - 1) * (gx + arrow_w)
    H = gx * 2 + max(p.height for p in panels) + text_h
    im = Image.new("RGBA", (W, H), PAGE + (255,))
    d = ImageDraw.Draw(im)
    x = gx
    for i, p in enumerate(panels):
        y = gx
        # soft shadow + rounded card
        card = Image.new("RGBA", p.size, (0, 0, 0, 0))
        mask = Image.new("L", p.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, p.width - 1, p.height - 1], radius=16 * S, fill=255)
        card.paste(p, (0, 0), mask)
        im.alpha_composite(card, (x, y))
        for k, line in enumerate(wrapped[i]):
            tw = d.textlength(line, font=FONT)
            d.text((x + (p.width - tw) / 2, y + p.height + (8 + 20 * k) * S), line, fill=INK, font=FONT)
        x += p.width
        if arrows and i < len(panels) - 1:
            cy = y + p.height / 2
            ax0, ax1 = x + gx * 0.4, x + gx + arrow_w - gx * 0.4
            d.line([ax0, cy, ax1, cy], fill=INK, width=4 * S)
            d.polygon([(ax1, cy), (ax1 - 12 * S, cy - 9 * S), (ax1 - 12 * S, cy + 9 * S)], fill=INK)
            x += arrow_w
        x += gx
    out = im.resize((W // S, H // S), Image.LANCZOS).convert("RGB")
    out.save(os.path.join(IMG, name))
    print("wrote", name)


def rect(r0, c0, r1, c1):
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def row_cells(r, cols, exclude=()):
    return [(r, c) for c in range(cols) if (r, c) not in exclude]


def col_cells(c, rows, exclude=()):
    return [(r, c) for r in range(rows) if (r, c) not in exclude]


def attacked(cell, rows, cols):
    r, c = cell
    return [(i, j) for i in range(rows) for j in range(cols)
            if (i, j) != cell and (i == r or j == c or (abs(i - r) <= 1 and abs(j - c) <= 1))]


