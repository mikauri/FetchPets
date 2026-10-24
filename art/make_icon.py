"""Draws the FetchPets icon as 64x64 pixel art, then scales it to 512x512.

A tamed wolf (red collar) and Steve leaning over a glowing compass whose needle
points at the wolf, on a grassy hill at sunset.
Run:  python art/make_icon.py   ->  art/icon.png (512) and art/icon-64.png (1:1 sprite)
"""
import math
import random
from pathlib import Path
from PIL import Image

N = 64
OUT = Path(__file__).parent
random.seed(5)

img = Image.new("RGB", (N, N))
px = img.load()


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def put(x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < N and 0 <= y < N:
        px[x, y] = c


def get(x, y):
    return px[min(max(int(x), 0), N - 1), min(max(int(y), 0), N - 1)]


def blend(c1, c2, a):
    a = min(max(a, 0.0), 1.0)
    return tuple(round(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(bands, t, x, y):
    t = min(max(t, 0.0), 1.0) * (len(bands) - 1)
    i = min(int(t), len(bands) - 2)
    return bands[i + 1] if (t - i) * 16 > BAYER[y % 4][x % 4] + 0.5 else bands[i]


# ---------------- sunset sky ----------------
SKY = [hexc(h) for h in ("#25265e", "#3d2f78", "#6a3a86", "#a8487a", "#e0695a", "#f59a4a", "#ffc864")]
SUN = (31.0, 29.0)
for y in range(N):
    for x in range(N):
        # warmer toward the sun, cooler toward the top corners
        t = y / 40 + max(0, 1 - math.hypot(x - SUN[0], y - SUN[1]) / 34) * 0.35
        px[x, y] = dither(SKY, t, x, y)

# sun + glow
for y in range(N):
    for x in range(N):
        d = math.hypot(x - SUN[0], y - SUN[1])
        if d < 4.2:
            put(x, y, hexc("#fff6c8"))
        elif d < 9:
            put(x, y, blend(get(x, y), hexc("#ffe08a"), (9 - d) / 9 * 0.8))

# blocky clouds
CLOUD, CLOUD_HI = hexc("#e98a7c"), hexc("#ffb58a")
for cx, cy, w in ((6, 8, 9), (20, 4, 7), (40, 9, 10), (52, 3, 7), (13, 17, 6), (47, 18, 8)):
    for x in range(cx, cx + w):
        put(x, cy, CLOUD_HI)
        put(x, cy + 1, CLOUD)
    for x in range(cx + 2, cx + w - 1):
        put(x, cy - 1, CLOUD_HI)

# ---------------- tree line (silhouettes) ----------------
FAR, NEAR, TRUNK = hexc("#3b2c4e"), hexc("#1b2420"), hexc("#151a17")
for x in range(N):
    h = 34 + int(3 * math.sin(x * 0.5) + 2 * math.sin(x * 1.3 + 1))
    for y in range(h, 46):
        put(x, y, FAR)
# big blocky trees at the edges, framing the scene like the reference
LEAF = [hexc(h) for h in ("#141c18", "#1b2620", "#24332a", "#2f4234")]
for left, top, w, h in ((-5, 4, 15, 19),):
    tx = left + w // 2 - 1
    for y in range(top + h - 2, 50):
        for k in range(3):
            put(tx + k, y, TRUNK if k else hexc("#2a201a"))
    for y in range(top, top + h):
        for x in range(left, left + w):
            # ragged, leafy edge instead of a hard box
            edge = min(x - left, left + w - 1 - x, y - top, top + h - 1 - y)
            if edge == 0 and random.random() < 0.45:
                continue
            c = random.choice(LEAF[:3]) if random.random() < 0.7 else LEAF[3]
            # sunset rim light on the side facing the sun
            facing = (x - left) / w if left < SUN[0] else 1 - (x - left) / w
            if facing > 0.8 and random.random() < 0.5:
                c = blend(c, hexc("#c86a3c"), 0.45)
            put(x, y, c)

# ---------------- grass ----------------
GRASS = [hexc(h) for h in ("#1c3a14", "#2b5419", "#3f7322", "#5b922c")]
for y in range(46, N):
    for x in range(N):
        light = max(0, 1 - math.hypot(x - 42, (y - 50) * 1.6) / 30)   # warm pool under the compass
        t = 0.25 + light * 0.75 - (y - 46) / 60
        c = dither(GRASS, t + random.uniform(-0.12, 0.12), x, y)
        put(x, y, blend(c, hexc("#c9a63c"), light * 0.25))
# grass tufts on the horizon edge and in the foreground corners
for x in range(0, N, 2):
    if random.random() < 0.6:
        put(x, 45, GRASS[2])
for bx, by in ((2, 58), (6, 61), (55, 59), (60, 56), (58, 62)):
    for k in range(4):
        put(bx, by - k, GRASS[3] if k < 2 else GRASS[2])
        put(bx + 1, by - k + 1, GRASS[2])

# ---------------- sprite helper ----------------
OUTLINE = hexc("#120d10")


def sprite(rows, colours, ox, oy, cell, rim_side, rim_keys, noise_keys):
    """Draw an ASCII pixel map: outline first, then cells, with a warm rim light
    on the edge facing the sun (rim_side = +1 right edge, -1 left edge)."""
    cells = {(c, r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."}
    for c, r in cells:
        for yy in range(oy + r * cell - 1, oy + r * cell + cell + 1):
            for xx in range(ox + c * cell - 1, ox + c * cell + cell + 1):
                put(xx, yy, OUTLINE)
    for c, r in cells:
        ch = rows[r][c]
        for yy in range(cell):
            for xx in range(cell):
                col = colours[ch]
                if ch in noise_keys and random.random() < 0.15:
                    col = blend(col, hexc("#000000"), 0.12)
                edge_x = cell - 1 if rim_side > 0 else 0
                if ch in rim_keys and xx == edge_x and (c + rim_side, r) not in cells:
                    col = blend(col, hexc("#ffcf7a"), 0.55)
                put(ox + c * cell + xx, oy + r * cell + yy, col)


# ---------------- Steve, leaning in from the right ----------------
STEVE = [
    ".....HHHHHHHH",
    ".....HHHHHHHH",
    ".....HSSSSSSH",
    ".....SSSSSSSS",
    ".....SEBSSBES",
    ".....SSSNNSSS",
    ".....SSMMMMSS",
    ".....SSSSSSSS",
    ".....cCCCCCCC",
    ".AAAAcCCCCCCC",
    ".AAAAcCCCCCCC",
    ".aAAAcCCCCCCC",
    ".aAAAcCCCCCCC",
    ".kkkkcCCCCCCC",
    ".kkkkcCCCCCCC",
    ".kkkkcCCCCCCC",
    ".sKKKpPPPPPPP",
    ".sKKKpPPPPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
    ".....pPPpPPPP",
]
STEVE_COL = {
    "H": hexc("#3b2814"), "S": hexc("#c4906d"), "E": hexc("#ffffff"), "B": hexc("#4b3fa0"),
    "N": hexc("#8a5a40"), "M": hexc("#5c3a22"), "C": hexc("#14a3a8"), "c": hexc("#0d7f86"),
    "A": hexc("#14a3a8"), "a": hexc("#0d7f86"), "k": hexc("#c4906d"), "K": hexc("#b07e5e"),
    "s": hexc("#9a6a4c"), "P": hexc("#3c3c9c"), "p": hexc("#2c2c78"),
}
sprite(STEVE, STEVE_COL, 35, 12, 2, -1, "HSCAkKP", "HSCAkP")

# ---------------- glowing compass ----------------
CC = (37.0, 52.0)
R = 9.5
GOLD = hexc("#ffd23f")
# glow halo (also washes gold over Steve's arm and the grass)
for y in range(N):
    for x in range(N):
        d = math.hypot(x - CC[0], y - CC[1])
        if R < d < R + 6:
            put(x, y, blend(get(x, y), GOLD, ((R + 6 - d) / 6) ** 1.6 * 0.85))
# rim + face
for y in range(N):
    for x in range(N):
        d = math.hypot(x + 0.5 - CC[0], y + 0.5 - CC[1])
        if d <= R + 1:
            put(x, y, hexc("#16120c"))                       # outline
        if d <= R:
            lit = ((CC[0] - x) + (CC[1] - y)) / (2 * R)      # light from top-left
            put(x, y, blend(hexc("#7d7d82"), hexc("#e2e2e6"), 0.5 + lit))
        if d <= R - 2.2:
            put(x, y, hexc("#26262b") if (x + y) % 7 else hexc("#303036"))
for ang in (0, 90, 180, 270):
    a = math.radians(ang)
    put(CC[0] + math.cos(a) * (R - 1.1), CC[1] + math.sin(a) * (R - 1.1), hexc("#3a3a40"))

# needle: red end points up-left, toward the wolf
NEEDLE_ANG = math.radians(-150)
dxn, dyn = math.cos(NEEDLE_ANG), math.sin(NEEDLE_ANG)
pxn, pyn = -dyn, dxn


def needle(length, colour, shade, sign):
    for s in range(int(length * 4)):
        f = s / (length * 4)
        half = (1 - f) * 2.4
        for w in range(-6, 7):
            o = w / 6 * half
            x = CC[0] + sign * dxn * f * length + pxn * o
            y = CC[1] + sign * dyn * f * length + pyn * o
            put(x, y, colour if o < 0 else shade)


needle(7.8, hexc("#ff4a2e"), hexc("#c0201a"), 1)
needle(6.0, hexc("#f2f2f2"), hexc("#a9a9b0"), -1)
put(CC[0], CC[1], hexc("#5a5a60"))

# gold sparkles around the compass
for _ in range(18):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(R + 2, R + 9)
    put(CC[0] + math.cos(a) * r, CC[1] + math.sin(a) * r, GOLD if random.random() < 0.6 else hexc("#fff3b0"))

# ---------------- the wolf (side view, facing the compass) ----------------
WOLF = [
    "........DD.DD...",
    ".......GGGGGG...",
    ".......GWWWKW...",
    ".......GWWWWWMMK",
    "T......GRWWWWMMM",
    "TT.GGGGWRWWWWmm.",
    ".TGGWWWWRGGGG...",
    "..GWWWWWRWWWWW..",
    "..GWWWWWWWWWWW..",
    "..GWWWWWWWWWWG..",
    "..WW.WW...WW.WW.",
    "..WW.WW...WW.WW.",
    "..DD.DD...DD.DD.",
]
WOLF_COL = {
    "G": hexc("#bfb6ab"), "W": hexc("#ece6dc"), "M": hexc("#f8f4ee"),
    "D": hexc("#7f766c"), "K": hexc("#141014"), "m": hexc("#d3c9bd"),
    "R": hexc("#d72f2a"), "T": hexc("#cfc6ba"),
}
WX, WY = -3, 35
sprite(WOLF, WOLF_COL, WX, WY, 2, +1, "GWMT", "GWT")
put(WX + 11 * 2 + 1, WY + 2 * 2, hexc("#ffffff"))   # eye shine

img.save(OUT / "icon-64.png")
img.resize((512, 512), Image.NEAREST).save(OUT / "icon.png")
print("wrote", OUT / "icon.png")
