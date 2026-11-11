#!/usr/bin/env python3
"""Generate Game Boy 2bpp tile data for the game.

Writes res/tiles.c and res/tiles.h. Optional: --preview out.png renders every
tile for visual checking (needs Pillow).

Colors: 0 = white, 1 = light gray, 2 = dark gray, 3 = black (BGP 0xE4).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- font 5x7
FONT = {
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '.': [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '@': [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    '>': ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
    '<': ["....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    '=': [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    ',': [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
}
FONT_FIRST, FONT_LAST = 32, 96  # ' ' .. '`'; tile index = ord(c) - 32

# Icons drawn in place of '#' '[' '\\' ']' '^' '_' '`' (see ICON_* in src/display.h).
ICONS = {
    '#': ["..3333..", ".333333.", "33...333", "33.33.33",
          "33...333", "33.33.33", ".3...33.", "..3333.."],   # round B button
    '[': ["...3....", "..33....", ".333333.", "3333333.",
          ".333333.", "..33....", "...3....", "........"],   # D-pad left
    ']': ["....3...", "....33..", ".333333.", ".3333333",
          ".333333.", "....33..", "....3...", "........"],   # D-pad right
    '\\': ["..3333..", ".333333.", "333..333", "33.33.33",
           "33....33", "33.33.33", ".3.33.3.", "..3333.."],   # round A button
    '^': ["...3....", "..333...", ".33333..", "3333333.",
          "..333...", "..333...", "..333...", "........"],   # D-pad up
    '_': ["..333...", "..333...", "..333...", "3333333.",
          ".33333..", "..333...", "...3....", "........"],   # D-pad down
    '`': [".3333333", ".3.333.3", ".3.333.3", "..33333.",
          "...333..", "....3...", "...333..", "..33333."],   # trophy
}


def blank():
    return [[0] * 8 for _ in range(8)]


def font_tile(ch):
    t = blank()
    g = FONT.get(ch)
    if g:
        for y, row in enumerate(g):
            for x, px in enumerate(row):
                if px == '#':
                    t[y][x + 1] = 3
    return t


# ------------------------------------------------- 7-segment digits 8x16
SEGS = {  # which segments are lit per symbol
    '0': "abcdef", '1': "bc", '2': "abged", '3': "abgcd", '4': "fgbc",
    '5': "afgcd", '6': "afgedc", '7': "abc", '8': "abcdefg", '9': "abcdfg",
    ' ': "", '-': "g",
}
SEG_ORDER = "0123456789 -"


def seg_pixels():
    """Return dict segment -> list of (x, y) on an 8x16 canvas."""
    p = {s: [] for s in "abcdefg"}
    for x in range(2, 6):
        p['a'] += [(x, 0), (x, 1)]
        p['g'] += [(x, 7), (x, 8)]
        p['d'] += [(x, 14), (x, 15)]
    for y in range(2, 7):
        p['f'] += [(0, y), (1, y)]
        p['b'] += [(6, y), (7, y)]
    for y in range(9, 14):
        p['e'] += [(0, y), (1, y)]
        p['c'] += [(6, y), (7, y)]
    # bevel corners so segments read as separate bars
    for s, pts in (('f', [(1, 1), (1, 7)]), ('b', [(6, 1), (6, 7)]),
                   ('e', [(1, 8), (1, 14)]), ('c', [(6, 8), (6, 14)])):
        p[s] += pts
    return p


def seg_tiles(sym):
    canvas = [[0] * 8 for _ in range(16)]
    lit = SEGS[sym]
    for s, pts in seg_pixels().items():
        for (x, y) in pts:
            if s in lit:
                canvas[y][x] = 3
    return canvas[:8], canvas[8:]


# ------------------------------------------------------- lamps 16x16
LAMP_STYLES = ("amber", "green", "red")


def lamp_fill(style, on, x, y):
    """Interior pixel colour. Each lamp type has its own pattern so they read
    apart on a 4-shade screen; 'on' is always dark, 'off' always light."""
    if style == "amber":
        if on:
            return 0 if (x - 5) ** 2 + (y - 5) ** 2 <= 3 else 3
        return 1
    if style == "green":   # horizontal stripes
        stripe = (y % 3) == 0
        if on:
            return 2 if stripe else 3
        return 1 if stripe else 0
    # red: diagonal stripes
    stripe = ((x + y) % 4) == 0
    if on:
        return 2 if stripe else 3
    return 1 if stripe else 0


def lamp_canvas(style, on):
    c = [[0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            d2 = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d2 <= 7.5 ** 2:
                c[y][x] = 3 if d2 >= 6.0 ** 2 else lamp_fill(style, on, x, y)
    return c


# The tree is 7 lamps of 16 px stacked, drawn TREE_SHIFT px above the tile
# grid. So a tile row can hold the bottom of one lamp and the top of the next;
# every row gets 4 variants: index = (state of upper lamp << 1) | lower lamp.
TREE_LAMPS = ["amber"] * 5 + ["green", "red"]
TREE_SHIFT = 4
TREE_ROWS = (len(TREE_LAMPS) * 16 + TREE_SHIFT + 7) // 8


def tree_row_lamps(r):
    """(upper, lower) lamp index touching tile row r, -1 = none."""
    def lamp_at(y):
        k = y // 16
        return k if 0 <= y and k < len(TREE_LAMPS) else -1
    return lamp_at(r * 8 - TREE_SHIFT), lamp_at(r * 8 + 7 - TREE_SHIFT)


def tree_row_tiles(r, s_up, s_lo):
    up, lo = tree_row_lamps(r)
    strip = []
    for py in range(8):
        y = r * 8 + py - TREE_SHIFT
        k = y // 16 if y >= 0 else -1
        if 0 <= k < len(TREE_LAMPS):
            on = s_up if k == up else s_lo
            strip.append(lamp_canvas(TREE_LAMPS[k], on)[y % 16])
        else:
            strip.append([0] * 16)
    return [[row[0:8] for row in strip], [row[8:16] for row in strip]]


# ------------------------------------------------------- round gauges
# 7x7 tiles (56 px). The pivot sits at the centre of the middle tile so the
# needle sprites and single-tile readouts centre on it.
GAUGE_TILES = 7
GAUGE_PX = GAUGE_TILES * 8
GC = 27.5            # pivot, pixel centre of tile 3
ANG_START = 225.0    # degrees, value 0 (lower left)
ANG_SWEEP = 270.0    # clockwise to lower right

TINY = {  # 3x5 digits for dial labels
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#.", "##.", ".#.", ".#.", "###"],
    '2': ["###", "..#", "###", "#..", "###"], '3': ["###", "..#", ".##", "..#", "###"],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "###", "..#", "###"],
    '6': ["###", "#..", "###", "#.#", "###"], '7': ["###", "..#", "..#", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "###"],
}


def ang_for(v, vmax):
    import math
    return math.radians(ANG_START - ANG_SWEEP * v / vmax)


def gauge_face(vmax, major, minor, labels, red_from=None):
    import math
    c = [[0] * GAUGE_PX for _ in range(GAUGE_PX)]

    def plot(x, y, col):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < GAUGE_PX and 0 <= yi < GAUGE_PX:
            c[yi][xi] = col

    # bezel: full circle
    for y in range(GAUGE_PX):
        for x in range(GAUGE_PX):
            d = math.hypot(x - GC, y - GC)
            if 26.0 <= d <= 27.6:
                c[y][x] = 3
    # red zone band (hatched)
    if red_from is not None:
        for y in range(GAUGE_PX):
            for x in range(GAUGE_PX):
                d = math.hypot(x - GC, y - GC)
                if 21.5 <= d <= 25.5:
                    a = math.degrees(math.atan2(-(y - GC), x - GC))
                    v = (ANG_START - a) % 360.0 / ANG_SWEEP * vmax
                    if red_from <= v <= vmax:
                        c[y][x] = 3 if (x + y) % 2 == 0 else 2
    # ticks
    v = 0
    while v <= vmax:
        a = ang_for(v, vmax)
        r0 = 20.5 if v % major == 0 else 23.0
        r = r0
        while r <= 25.5:
            plot(GC + r * math.cos(a), GC - r * math.sin(a), 3)
            r += 0.25
        v += minor
    # labels
    for lv, text in labels:
        a = ang_for(lv, vmax)
        cx, cy = GC + 14.0 * math.cos(a), GC - 14.0 * math.sin(a)
        w = len(text) * 4 - 1
        x0, y0 = int(round(cx - w / 2 + 0.5)), int(round(cy - 2.5 + 0.5))
        for i, ch in enumerate(text):
            for gy, row in enumerate(TINY[ch]):
                for gx, px in enumerate(row):
                    if px == '#':
                        plot(x0 + i * 4 + gx, y0 + gy, 3)
    # pivot cap
    for y in range(GAUGE_PX):
        for x in range(GAUGE_PX):
            if math.hypot(x - GC, y - GC) <= 2.6:
                c[y][x] = 3
    return c


def split_canvas(c, tw, th):
    tiles = []
    for ty in range(th):
        for tx in range(tw):
            tiles.append([row[tx * 8:tx * 8 + 8] for row in c[ty * 8:ty * 8 + 8]])
    return tiles


TACH_MAX, SPEEDO_MAX = 10000, 400
TACH_LABELS = [(v, str(v // 1000)) for v in range(0, 10001, 2000)]
SPEEDO_LABELS = [(v, str(v)) for v in range(0, 401, 100)]
# Red-zone variants: index used per class in display.c
TACH_RED = [7000, 9000, 9700]



# ------------------------------------------------------- scrolling strip
# The quarter mile is a pre-rendered world strip that the game streams into
# the background map one tile column at a time. World x in px = START_WX +
# feet * 3/4. The road band is 4 tile rows (screen y 96..127), the grandstand
# above it 2 rows (y 80..95) and repeats every CROWD_PERIOD px (parallax).
WORLD_START_WX = 40                       # car nose position at the start
START_LINE_WX = WORLD_START_WX + 12       # start line at the far edge; it slants back
                                          # 11 px by the near edge, staying ahead of the nose
WORLD_FIN_WX = WORLD_START_WX + 1320 * 3 // 4
CAM_NOSE_X = 72                           # where the camera holds the car's nose
CAM_FIN_X = 120                           # finish line screen x when the camera stops
CAM_MAX = WORLD_FIN_WX - CAM_FIN_X
ROAD_COLS = CAM_MAX // 8 + 33             # columns ever streamed (view + 32 lookahead)
ROAD_ROWS = 4
CROWD_PERIOD = 32                         # px; divides the 256 px map width
# road band local rows: 0-1 blank (raster split), 2 far edge, 3..24 asphalt,
# 25 near edge, 26..28 shoulder, 29..31 blank (raster split)
R_FAR, R_NEAR, R_DASH = 2, 25, 14


def road_pixel(wx, y):
    if y < R_FAR or y > R_NEAR + 3:
        return 0
    if y == R_FAR or y == R_NEAR:
        return 3
    if y > R_NEAR:                                      # shoulder
        return 2 if (wx + y) % 4 == 0 else 0
    c = 1                                               # asphalt
    if y in (R_DASH, R_DASH + 1) and wx % 16 < 8:
        c = 0                                           # lane dashes
    # slanted concrete joints every 32 px
    if (wx + (y - R_FAR) // 2) % 32 == 0:
        c = 2
    # slanted start line (white) and finish line (checkered)
    sx = wx + (y - R_FAR) // 2
    if START_LINE_WX - 2 <= sx < START_LINE_WX:
        c = 0
    if WORLD_FIN_WX <= sx < WORLD_FIN_WX + 6:
        c = 3 if ((sx - WORLD_FIN_WX) // 3 + (y - R_FAR) // 3) % 2 else 0
    return c


def crowd_pixel(wx, y):
    """Grandstand, 32 px period: two staggered rows of spectators (round head,
    shoulders) in varied shades, over a wall with posts. Rows 0-1 stay blank
    for the raster split."""
    if y < 2:
        return 0
    if y == 12:
        return 3                                         # wall top
    if y > 12:
        return 2 if wx % 8 in (0, 1) else 1              # wall with posts
    # back row (y 2..6) people every 4 px, front row (y 7..11) offset by 2 px
    row = 0 if y < 7 else 1
    ly = y - (2 if row == 0 else 7)
    px = (wx + (2 if row else 0)) % 4
    person = ((wx + (2 if row else 0)) // 4 + row * 3) % 8
    if person == (5 if row == 0 else 2):
        return 0                                         # an empty seat
    shade = 2 if person % 3 == 0 else (3 if person % 3 == 1 else 1)
    if ly <= 1:                                          # head: 2 px wide
        return 2 if px in (1, 2) else 0
    if ly == 2:                                          # neck/shoulders
        return shade if px in (0, 1, 2) else 0
    return shade if px != 3 else 0                       # body


def strip_tiles(fn, cols, rows):
    """Column-major tiles of a world strip: [col][row]."""
    out = []
    for tc in range(cols):
        for tr in range(rows):
            out.append([[fn(tc * 8 + x, tr * 8 + y) for x in range(8)] for y in range(8)])
    return out

# ------------------------------------------------------- misc bg tiles
def from_rows(rows):
    m = {'.': 0, '1': 1, '2': 2, '3': 3}
    return [[m[ch] for ch in r] for r in rows]


TRACK = from_rows(["........", "........", "........", "........",
                   "........", "........", "33333333", "11111111"])
# Mini light tree marking the start line: top tile sits above the track row,
# bottom tile is a track tile with the post standing on the line.
MINI_TREE = [
    from_rows(["........", "........", ".333....", ".313....",
               ".333....", ".313....", ".333....", ".313...."]),
    from_rows([".333....", ".323....", ".333....", "..3.....",
               "..3.....", "..3.....", "33333333", "11111111"]),
]
FINISH = from_rows(["33..33..", "33..33..", "..33..33", "..33..33",
                    "33..33..", "33..33..", "33333333", "11111111"])

# ------------------------------------------------------- sprites
# ------------------------------------------------------- class cars (24x12)
# Drawn with simple shape primitives so the wheels come out round. Each car
# sits at the top of a 16 px tall box = 2 rows of sprite tiles (the bottom 4
# rows are empty, which keeps the car's sprites off the race timer's scanlines).
CAR_H = 12


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[0] * w for _ in range(h)]

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(self.h):
            for x in range(self.w):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.3:
                    self.p[y][x] = c

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def poly(self, pts, c):
        """Filled polygon with a black outline."""
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                    self.px(x, y, c)
        for i in range(len(pts)):
            self.line(*pts[i], *pts[(i + 1) % len(pts)], 3)

    def wheel(self, cx, cy, r, hub=1, arch=False):
        if arch:
            self.disc(cx, cy, r + 1.0, 3)      # wheel well cut into the body
        self.disc(cx, cy, r, 3)                # tyre
        if r >= 3.0:
            self.disc(cx, cy, r * 0.62, 2)     # sidewall / rim
            self.disc(cx, cy, r * 0.30, 1)     # hub
        elif r >= 2.0:
            self.disc(cx, cy, r * 0.45, 2)
            self.px(cx, cy, 1)
        elif hub:
            self.px(cx, cy, 1)


def car_stock(w, h):
    c, k = Canvas(w, h), w / 24.0
    bt, bb = round(h * 0.42), round(h * 0.78)
    c.poly([(0, bt + 1), (1, bt), (w - 2, bt), (w - 1, bt + 1), (w - 1, bb), (0, bb)], 2)
    c.poly([(5 * k, bt), (7.5 * k, 1), (15 * k, 1), (18.5 * k, bt)], 1)   # greenhouse
    c.line(11.5 * k, 1, 11.5 * k, bt, 3)                                  # B pillar
    c.rect(round(1 * k), bt + 2, w - 2, bt + 2, 1)                        # side highlight
    c.px(w - 1, bt + 1, 1)                                                # headlight
    r = 2.6 * k
    c.wheel(5 * k, h - 1 - r, r, arch=True)
    c.wheel(w - 1 - 5 * k, h - 1 - r, r, arch=True)
    return c


def car_promod(w, h):
    c, k = Canvas(w, h), w / 24.0
    bt, bb = round(h * 0.45), round(h * 0.78)
    c.poly([(0, bt), (w - 3, bt + 1), (w - 1, bt + 2), (w - 1, bb), (0, bb)], 2)
    c.poly([(6 * k, bt), (8 * k, 2), (14.5 * k, 2), (17 * k, bt + 0.5)], 1)
    c.line(11 * k, 2, 11 * k, bt, 3)
    c.rect(round(17.5 * k), bt - 1, round(20 * k), bt, 3)                 # hood scoop
    c.rect(0, 0, round(4 * k), 1, 3)                                      # wing
    c.line(round(2 * k), 1, round(2 * k), bt, 3)
    c.rect(round(1 * k), bt + 2, w - 3, bt + 2, 1)
    rr, rf = 3.2 * k, 2.4 * k
    c.wheel(5 * k, h - 1 - rr, rr, arch=True)
    c.wheel(w - 1 - 4.5 * k, h - 1 - rf, rf, arch=True)
    return c


def car_funny(w, h):
    """Raked one-piece body: tall at the back, long sloping hood, big slicks."""
    c, k = Canvas(w, h), w / 24.0
    rr, rf = 0.36 * h, 0.19 * h
    rcx, fcx = rr + 0.8 * k, w - 1 - 3.5 * k
    c.wheel(rcx, h - 1 - rr, rr)
    c.wheel(fcx, h - 1 - rf, rf)
    c.poly([(0, 0.28 * h), (3 * k, 0.20 * h), (8 * k, 0.24 * h), (13 * k, 0.42 * h),
            (w - 1, 0.58 * h), (w - 1, 0.68 * h), (rcx + rr + 1, 0.60 * h),
            (rcx + rr * 0.3, 0.52 * h), (0, 0.52 * h)], 2)
    c.poly([(7.5 * k, 0.24 * h), (9.5 * k, 0.04 * h), (12.5 * k, 0.36 * h)], 1)  # canopy
    c.line(2 * k, 0.42 * h, w - 2, 0.62 * h, 1)                                 # flank stripe
    c.rect(0, round(0.14 * h), round(1.5 * k), round(0.22 * h), 3)             # rear spoiler
    return c


def car_topfuel(w, h):
    """Rear-engine rail, 32 px long and sitting low: slick + wing at the back,
    engine and driver just ahead of it, long thin nose close to the ground."""
    c = Canvas(w, h)
    rr = 4.6                                   # rear slick radius
    rcx, rcy = rr, h - 1 - rr
    c.rect(0, 0, 9, 1, 3)                      # rear wing
    c.rect(1, 1, 8, 1, 1)
    c.line(4, 2, 4, rcy - rr, 3)               # wing strut
    c.wheel(rcx, rcy, rr)
    e0 = 2 * rr - 0.5                          # engine starts at the slick's front edge
    # low body / rail: from the engine to the nose, tapering towards the ground
    c.poly([(e0, 6.5), (e0 + 9, 7.0), (w - 1, 8.5), (w - 1, 9.5), (e0, 9.5)], 2)
    c.line(e0 + 3, 8.2, w - 3, 9.0, 1)         # highlight along the body
    # engine block, blower, injector scoop
    c.poly([(e0, 4.0), (e0 + 4, 4.0), (e0 + 4, 7.5), (e0, 7.5)], 2)
    c.rect(round(e0 + 0.5), 2, round(e0 + 3.5), 3, 3)
    c.rect(round(e0 + 1.5), 0, round(e0 + 2.5), 1, 3)
    # driver: roll cage + helmet in front of the engine
    c.line(e0 + 4.5, 6.5, e0 + 5.5, 3.5, 3)
    c.line(e0 + 5.5, 3.5, e0 + 8.0, 6.8, 3)
    c.disc(e0 + 6.2, 5.0, 1.3, 3)
    # tiny front wheel near the nose, front wing on the tip
    c.wheel(w - 5, h - 2.4, 1.4, hub=0)
    c.rect(w - 4, 8, w - 1, 8, 3)
    return c


def car_tiles(fn, w):
    """w x 12 picture at the top of a w x 16 box, as (w/8) x 2 tiles, row-major."""
    car = fn(w, CAR_H)
    box = [row[:] for row in car.p] + [[0] * w for _ in range(16 - CAR_H)]
    tw = w // 8
    return [[row[tx * 8:tx * 8 + 8] for row in box[ty * 8:ty * 8 + 8]]
            for ty in range(2) for tx in range(tw)]


# (drawing function, width in px) in class order; every car is 12 px tall.
CARS = [(car_stock, 24), (car_promod, 24), (car_funny, 24), (car_topfuel, 32)]


SMOKE = from_rows([
    "........", "...11...", ".11221..", "1222221.",
    "12222211", ".122221.", "..1111..", "........",
])
SMOKE2 = from_rows([
    "........", "........", "..1.1...", ".12121..",
    "1211121.", ".1.121..", "...1....", "........",
])
# Blown-engine smoke: a fresh, small dark puff (then SMOKE, then SMOKE2 as it thins).
PUFF = from_rows([
    "........", "........", "...22...", "..2332..",
    "..2332..", "...22...", "........", "........",
])
NEEDLE_DIRS = 8   # line orientations over 180 degrees


def needle_tile(k):
    """8x8 needle segment through the tile centre at angle k*22.5 deg."""
    import math
    t = blank()
    a = math.radians(k * 180.0 / NEEDLE_DIRS)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx   # perpendicular
    s = -4.6
    while s <= 4.6:
        for off in (-0.45, 0.45):
            x = int(math.floor(3.5 + s * dx + off * px + 0.5))
            y = int(math.floor(3.5 + s * dy + off * py + 0.5))
            if 0 <= x < 8 and 0 <= y < 8:
                t[y][x] = 3
        s += 0.2
    return t


# ------------------------------------------------------- encoding
def encode(tile):
    out = []
    for row in tile:
        lo = hi = 0
        for x, px in enumerate(row):
            bit = 7 - x
            lo |= (px & 1) << bit
            hi |= ((px >> 1) & 1) << bit
        out += [lo, hi]
    return out


def build():
    bg, defs, maps = [], [], []
    index = {}

    def add(name, tiles):
        """Fixed block: tiles stored in order (indices are meaningful)."""
        defs.append((name, len(bg)))
        for t in tiles:
            index.setdefault(tuple(encode(t)), len(bg))
            bg.append(t)

    def add_map(name, tiles):
        """Deduplicated: returns a tile map, reusing identical tiles."""
        m = []
        for t in tiles:
            key = tuple(encode(t))
            if key not in index:
                index[key] = len(bg)
                bg.append(t)
            m.append(index[key])
        maps.append((name, m))

    add("T_FONT", [from_rows(ICONS[chr(c)]) if chr(c) in ICONS else font_tile(chr(c))
                   for c in range(FONT_FIRST, FONT_LAST + 1)])
    seg = []
    for sym in SEG_ORDER:
        top, bot = seg_tiles(sym)
        seg += [top, bot]
    add("T_SEG", seg)

    for i, red in enumerate(TACH_RED):
        add_map(f"map_tach{i}", split_canvas(
            gauge_face(TACH_MAX, 2000, 1000, TACH_LABELS, red), GAUGE_TILES, GAUGE_TILES))
    tree = []
    for r in range(TREE_ROWS):
        for idx in range(4):
            tree += tree_row_tiles(r, bool(idx & 2), bool(idx & 1))
    add_map("tree_map", tree)   # [row][idx][left, right]

    add_map("crowd_map", strip_tiles(crowd_pixel, CROWD_PERIOD // 8, 2))   # [col][row]
    add_map("road_map", strip_tiles(road_pixel, ROAD_COLS, ROAD_ROWS))      # [col][row]

    add_map("map_speedo", split_canvas(
        gauge_face(SPEEDO_MAX, 100, 50, SPEEDO_LABELS), GAUGE_TILES, GAUGE_TILES))

    spr, sdefs = [], []

    def sadd(name, tiles):
        sdefs.append((name, len(spr)))
        spr.extend(tiles)

    # Each class gets 8 tile slots (4x2); 24 px cars leave their 4th column empty.
    cars = []
    for fn, w in CARS:
        t = car_tiles(fn, w)
        tw = w // 8
        for ty in range(2):
            row = t[ty * tw:(ty + 1) * tw]
            cars += row + [blank()] * (4 - tw)
    sadd("S_CARS", cars)
    sadd("S_SMOKE", [SMOKE, SMOKE2])
    sadd("S_PUFF", [PUFF])
    # Start tree beside the road (sprites, so it scrolls with the road)
    sadd("S_MINI_TREE", [MINI_TREE[0], MINI_TREE[1][:6] + [[0] * 8, [0] * 8]])
    sadd("S_NEEDLE", [needle_tile(k) for k in range(NEEDLE_DIRS)])
    sadd("S_DIGITS", [font_tile(str(d)) for d in range(10)])   # speed readout
    # Race timer as sprites: 7-seg symbols (top, bottom per symbol), '.' and 'S'
    sseg = []
    for sym in SEG_ORDER:
        top, bot = seg_tiles(sym)
        sseg += [top, bot]
    sadd("S_SEG", sseg)
    sadd("S_TIME_DOT", [font_tile('.')])
    sadd("S_TIME_S", [font_tile('S')])
    return bg, defs, maps, spr, sdefs


def sine_table():
    import math
    return [int(round(127 * math.sin(2 * math.pi * i / 256))) for i in range(256)]


ENGINE_PERIODS = 161   # rpm 0..10240 in 64 rpm steps
NEEDLE_R = (6, 13, 20)  # segment centre radii, px
ANG_START_B, ANG_SWEEP_B = 160, 192   # binary degrees (256 = 360)


def needle_table():
    """Per sweep step 0..ANG_SWEEP_B: tile direction, then (dx, dy) per segment.
    dy is screen-down positive."""
    import math
    out = []
    for sw in range(ANG_SWEEP_B + 1):
        a = (ANG_START_B - sw) % 256
        rad = 2 * math.pi * a / 256
        out.append(((a + 8) >> 4) & (NEEDLE_DIRS - 1))
        for r in NEEDLE_R:
            out.append(int(round(r * math.cos(rad))))
            out.append(int(round(-r * math.sin(rad))))
    return out


def engine_periods():
    out = []
    for i in range(ENGINE_PERIODS):
        rpm = max(i * 64, 1000)
        out.append(int(round(2048 - 131072 / (rpm / 15.0))))
    return out


def write_c(bg, defs, maps, spr, sdefs):
    def hexrows(data, fmt="0x{:02X}"):
        lines = []
        for i in range(0, len(data), 16):
            lines.append("    " + ", ".join(fmt.format(b) for b in data[i:i + 16]) + ",")
        return "\n".join(lines)

    def arr(name, tiles):
        data = []
        for t in tiles:
            data += encode(t)
        return f"const uint8_t {name}[] = {{\n" + hexrows(data) + "\n};\n"

    hdr = "// Generated by tools/gen_tiles.py - do not edit.\n"
    with open(os.path.join(ROOT, "res", "tiles.c"), "w") as f:
        f.write(hdr + '#include "tiles.h"\n\n')
        f.write(arr("bg_tiles", bg) + "\n" + arr("spr_tiles", spr) + "\n")
        for name, m in maps:
            f.write(f"const uint8_t {name}[] = {{\n" + hexrows(m) + "\n};\n\n")
        f.write("// Needle: per sweep step, [dir, dx0, dy0, dx1, dy1, dx2, dy2] (dy screen-down).\n")
        f.write("const int8_t needle_table[(ANG_SWEEP + 1) * 7] = {\n" +
                hexrows(needle_table(), "{:d}") + "\n};\n\n")
        rows = [tree_row_lamps(r) for r in range(TREE_ROWS)]
        f.write("// Light tree: upper / lower lamp touching each tile row (-1 = none).\n")
        f.write("const int8_t tree_row_up[TREE_ROWS] = { " + ", ".join(str(u) for u, _ in rows) + " };\n")
        f.write("const int8_t tree_row_lo[TREE_ROWS] = { " + ", ".join(str(l) for _, l in rows) + " };\n\n")
        f.write("// CH2 period for engine tone, index rpm >> 6. V8 firing freq = rpm / 15 Hz.\n")
        f.write("const uint16_t engine_period[ENGINE_PERIODS] = {\n" +
                hexrows(engine_periods(), "{:d}") + "\n};\n")
    with open(os.path.join(ROOT, "res", "tiles.h"), "w") as f:
        f.write(hdr + "#ifndef TILES_H\n#define TILES_H\n\n#include <stdint.h>\n\n")
        for n, i in defs:
            f.write(f"#define {n:<14} {i}u\n")
        f.write(f"#define {'BG_TILE_COUNT':<14} {len(bg)}u\n\n")
        for n, i in sdefs:
            f.write(f"#define {n:<14} {i}u\n")
        f.write(f"#define {'SPR_TILE_COUNT':<14} {len(spr)}u\n")
        f.write(f"#define {'NEEDLE_DIRS':<14} {NEEDLE_DIRS}u\n\n")
        f.write(f"#define GAUGE_TILES    {GAUGE_TILES}u\n")
        f.write(f"#define TACH_MAX       {TACH_MAX}u\n#define SPEEDO_MAX     {SPEEDO_MAX}u\n")
        f.write("// Needle angle in binary degrees (256 = 360), screen maths convention.\n")
        assert int(ANG_START * 256 / 360) == ANG_START_B and int(ANG_SWEEP * 256 / 360) == ANG_SWEEP_B
        f.write(f"#define ANG_START      {ANG_START_B}\n")
        f.write(f"#define ANG_SWEEP      {ANG_SWEEP_B}\n\n")
        f.write("// Font: tile = T_FONT + (ch - ' ') for ' '..'Z'.\n")
        f.write("// 7-seg: symbol order \"0123456789 -\", 2 tiles each (top, bottom).\n")
        f.write("#define SEG_BLANK 10u\n#define SEG_DASH  11u\n\n")
        f.write("extern const uint8_t bg_tiles[];\nextern const uint8_t spr_tiles[];\n")
        for name, _ in maps:
            f.write(f"extern const uint8_t {name}[];\n")
        f.write("extern const int8_t needle_table[(ANG_SWEEP + 1) * 7];\n")
        f.write(f"#define TREE_ROWS      {TREE_ROWS}u\n")
        for n, v in (("WORLD_START_WX", WORLD_START_WX), ("START_LINE_WX", START_LINE_WX),
                     ("WORLD_FIN_WX", WORLD_FIN_WX),
                     ("CAM_NOSE_X", CAM_NOSE_X), ("CAM_MAX", CAM_MAX), ("ROAD_COLS", ROAD_COLS),
                     ("ROAD_ROWS", ROAD_ROWS), ("CROWD_COLS", CROWD_PERIOD // 8)):
            f.write(f"#define {n:<14} {v}u\n")
        f.write("extern const int8_t tree_row_up[TREE_ROWS];\nextern const int8_t tree_row_lo[TREE_ROWS];\n")
        f.write(f"#define ENGINE_PERIODS {ENGINE_PERIODS}u\n")
        f.write("extern const uint16_t engine_period[ENGINE_PERIODS];\n\n#endif\n")


def preview(bg, spr, path, maps=None):
    from PIL import Image
    shades = [(224, 248, 208), (136, 192, 112), (52, 104, 86), (8, 24, 32)]
    tiles = bg + spr
    cols = 16
    rows = (len(tiles) + cols - 1) // cols
    sheet_h = rows * 9
    gauges_h = 0
    if maps:
        gauges_h = GAUGE_PX + 8
    img = Image.new("RGB", (max(cols * 9, len(maps or []) * (GAUGE_PX + 8)), sheet_h + gauges_h),
                    (255, 0, 255))
    for i, t in enumerate(tiles):
        ox, oy = (i % cols) * 9, (i // cols) * 9
        for y in range(8):
            for x in range(8):
                img.putpixel((ox + x, oy + y), shades[t[y][x]])
    for gi, (_, m) in enumerate(maps or []):
        for ti, idx in enumerate(m):
            ox = gi * (GAUGE_PX + 8) + (ti % GAUGE_TILES) * 8
            oy = sheet_h + 4 + (ti // GAUGE_TILES) * 8
            for y in range(8):
                for x in range(8):
                    img.putpixel((ox + x, oy + y), shades[bg[idx][y][x]])
    img = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
    img.save(path)


if __name__ == "__main__":
    bg, defs, maps, spr, sdefs = build()
    assert len(bg) <= 256, f"too many bg tiles: {len(bg)}"
    assert len(spr) <= 128, len(spr)
    write_c(bg, defs, maps, spr, sdefs)
    if "--preview" in sys.argv:
        preview(bg, spr, sys.argv[sys.argv.index("--preview") + 1], maps)
    print(f"bg tiles: {len(bg)}, sprite tiles: {len(spr)}")
