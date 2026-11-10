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
FONT_FIRST, FONT_LAST = 32, 90  # ' ' .. 'Z'; tile index = ord(c) - 32


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
# One 16x8 side view per class (facing right), in class order.
CARS = [
    from_rows([   # STOCK: sedan
        "................",
        ".....333333.....",
        "....31131113....",
        ".33333333333333.",
        "3333333333333333",
        "3333333333333333",
        ".33133....33133.",
        "..333......333..",
    ]),
    from_rows([   # MODIFIED: rear wing, hood scoop, fat rear tyre
        "333.............",
        ".3....33333.....",
        ".3...3113113.3..",
        "33333333333333..",
        "3333333333333333",
        "3333333333333333",
        "33133.....3133..",
        ".333.......33...",
    ]),
    from_rows([   # FUNNY CAR: raked one-piece body, big slicks
        "................",
        ".3333...........",
        "31111333333.....",
        "3333333333333...",
        "3333333333333333",
        "33333333333333..",
        "31113.......313.",
        ".333.........3..",
    ]),
    from_rows([   # TOP FUEL: long rail, tall slick, rear wing
        "3333............",
        ".33.............",
        "3333.33.........",
        "33333333........",
        "3113333333333333",
        "3113...........3",
        "3113.........333",
        ".33...........3.",
    ]),
]
SMOKE = from_rows([
    "........", "...11...", ".11221..", "1222221.",
    "12222211", ".122221.", "..1111..", "........",
])
SMOKE2 = from_rows([
    "........", "........", "..1.1...", ".12121..",
    "1211121.", ".1.121..", "...1....", "........",
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


def split16(c):
    return [[r[0:8] for r in c], [r[8:16] for r in c]]


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

    add("T_FONT", [font_tile(chr(c)) for c in range(FONT_FIRST, FONT_LAST + 1)])
    seg = []
    for sym in SEG_ORDER:
        top, bot = seg_tiles(sym)
        seg += [top, bot]
    add("T_SEG", seg)
    add("T_CARS", [t for car in CARS for t in split16(car)])   # 2 tiles per class
    add("T_TRACK", [TRACK])
    add("T_MINI_TREE", MINI_TREE)   # top, bottom
    add("T_FINISH", [FINISH])

    for i, red in enumerate(TACH_RED):
        add_map(f"map_tach{i}", split_canvas(
            gauge_face(TACH_MAX, 2000, 1000, TACH_LABELS, red), GAUGE_TILES, GAUGE_TILES))
    tree = []
    for r in range(TREE_ROWS):
        for idx in range(4):
            tree += tree_row_tiles(r, bool(idx & 2), bool(idx & 1))
    add_map("tree_map", tree)   # [row][idx][left, right]

    add_map("map_speedo", split_canvas(
        gauge_face(SPEEDO_MAX, 100, 50, SPEEDO_LABELS), GAUGE_TILES, GAUGE_TILES))

    spr, sdefs = [], []

    def sadd(name, tiles):
        sdefs.append((name, len(spr)))
        spr.extend(tiles)

    sadd("S_CARS", [t for car in CARS for t in split16(car)])  # 2 tiles per class
    sadd("S_SMOKE", [SMOKE, SMOKE2])
    sadd("S_NEEDLE", [needle_tile(k) for k in range(NEEDLE_DIRS)])
    sadd("S_DIGITS", [font_tile(str(d)) for d in range(10)])   # speed readout
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
