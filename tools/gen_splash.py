#!/usr/bin/env python3
"""Generate the splash screen: big title, Top Fuel dragster, waving flag.

Writes res/splash.c and res/splash.h. --preview out.png renders all flag
frames composited onto the screen (needs Pillow).

VRAM layout while the splash is shown (its own tile set):
  0 ..               static tiles (blank, small font subset, title, dragster, pole)
  SPLASH_FLAG_A ..   flag frame buffer A (FLAG_W * FLAG_H tiles)
  SPLASH_FLAG_B ..   flag frame buffer B
The next frame is uploaded into the hidden buffer, then the map is switched.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_tiles import FONT, encode, font_tile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCREEN_W, SCREEN_H = 20, 18
FLAG_X, FLAG_Y, FLAG_W, FLAG_H = 1, 6, 9, 9      # tiles
FLAG_FRAMES = 8
DRAGSTER_X, DRAGSTER_Y = 11, 7                   # 8x3 tiles
CREDIT = (12, 11, "BY J.E.")
PRESS = (4, 16, "PRESS A OR B")
TITLE = [(4, 1, "POCKET"), (2, 3, "DRAGSTER")]   # 2x2-tile letters


def canvas(w, h):
    return [[0] * w for _ in range(h)]


def tiles_of(c, tw, th):
    return [[row[tx * 8:tx * 8 + 8] for row in c[ty * 8:ty * 8 + 8]]
            for ty in range(th) for tx in range(tw)]


# ------------------------------------------------------------ big title font
COL_X = [0, 3, 5, 7, 9]   # 5 source columns -> 12 px: bold outer strokes
COL_W = [3, 2, 2, 2, 3]


def big_letter(ch):
    c = canvas(16, 16)
    g = FONT[ch]
    for layer, (ox, oy, col) in enumerate(((2, 2, 2), (1, 1, 3))):  # shadow, then glyph
        for gy, row in enumerate(g):
            for gx, px in enumerate(row):
                if px != '#':
                    continue
                for y in range(oy + gy * 2, oy + gy * 2 + 2):
                    for x in range(ox + COL_X[gx], ox + COL_X[gx] + COL_W[gx]):
                        if x < 16 and y < 16:
                            c[y][x] = col
    return c


# ------------------------------------------------------------ dragster 64x24
def dragster():
    c = canvas(64, 24)

    def rect(x0, y0, x1, y1, col):
        for y in range(max(0, y0), min(24, y1 + 1)):
            for x in range(max(0, x0), min(64, x1 + 1)):
                c[y][x] = col

    def disc(cx, cy, r, col):
        for y in range(24):
            for x in range(64):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    c[y][x] = col

    def line(x0, y0, x1, y1, col):
        n = max(abs(x1 - x0), abs(y1 - y0)) * 2 + 1
        for i in range(n + 1):
            t = i / n
            x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
            if 0 <= x < 64 and 0 <= y < 24:
                c[y][x] = col

    # long tapered body + chassis rail, nose on the right
    for x in range(28, 63):
        top = 12 + (x - 28) * 3 // 35
        rect(x, top, x, 15, 3)
    rect(38, 13, 58, 13, 1)           # body stripe
    rect(18, 16, 57, 16, 3)           # lower rail
    rect(58, 11, 63, 12, 3)           # front wing
    line(52, 16, 56, 19, 3)           # front strut
    disc(56, 20, 3.3, 3)              # front wheel
    disc(56, 20, 1.0, 1)
    # roll cage + driver
    line(30, 12, 31, 6, 3)
    line(31, 6, 37, 6, 3)
    line(37, 6, 40, 12, 3)
    disc(34.5, 9.5, 2.6, 3)           # helmet
    rect(35, 8, 36, 9, 1)             # visor
    # engine behind the driver: block, blower, injector scoop, headers
    rect(17, 7, 29, 14, 3)
    rect(18, 9, 28, 12, 2)
    rect(19, 4, 27, 6, 2)
    rect(19, 4, 27, 4, 3)
    rect(21, 0, 25, 3, 3)
    rect(22, 1, 24, 2, 1)
    for x in (19, 22, 25, 28):
        rect(x, 13, x + 1, 13, 1)
    # rear wing on struts
    rect(0, 0, 14, 2, 3)
    rect(1, 1, 13, 1, 1)
    rect(4, 3, 5, 6, 3)
    rect(10, 3, 11, 6, 3)
    # huge rear slick
    disc(10.5, 14.5, 9.4, 3)
    disc(10.5, 14.5, 5.5, 2)
    disc(10.5, 14.5, 2.2, 1)
    return c


# ------------------------------------------------------------ waving flag
FLAG_PX_W, FLAG_PX_H = FLAG_W * 8, FLAG_H * 8
POLE_X = 2           # pole occupies x 2..4
CLOTH_X0, CLOTH_W, CLOTH_Y0, CLOTH_H, CHECK = 6, 64, 10, 48, 8


def pole(c, y0, y1):
    for y in range(y0, y1):
        c[y][POLE_X] = 3
        c[y][POLE_X + 1] = 1
        c[y][POLE_X + 2] = 3


def flag_frame(k):
    c = canvas(FLAG_PX_W, FLAG_PX_H)
    pole(c, 4, FLAG_PX_H)
    for y in range(0, 7):                       # finial
        for x in range(0, 7):
            if (x - 3) ** 2 + (y - 2.5) ** 2 <= 2.6 ** 2:
                c[y][x] = 3
    ph = 2 * math.pi * k / FLAG_FRAMES
    for u in range(CLOTH_W):
        amp = 1.0 + 5.0 * u / (CLOTH_W - 1)     # pinned at the pole, free at the end
        a = 2 * math.pi * u / 36.0 - ph
        dy = amp * math.sin(a)
        slope = amp * math.cos(a) * 2 * math.pi / 36.0
        shade = 1 if slope < -0.3 else (-1 if slope > 0.3 else 0)
        x = CLOTH_X0 + u
        for y in range(FLAG_PX_H):
            v = y - CLOTH_Y0 - dy
            if not (0 <= v < CLOTH_H):
                continue
            edge = v < 1 or v >= CLOTH_H - 1 or u == CLOTH_W - 1
            black = ((u // CHECK) + (int(v) // CHECK)) % 2 == 1
            if edge:
                col = 3
            elif black:
                col = 2 if shade < 0 else 3     # highlight lifts black to dark gray
            else:
                col = 1 if shade > 0 else 0     # shadow drops white to light gray
            c[y][x] = col
    return c


# ------------------------------------------------------------ assembly
def build():
    static = [canvas(8, 8)]            # tile 0 = blank
    index = {tuple(encode(static[0])): 0}
    smap = [0] * (SCREEN_W * SCREEN_H)

    def tile_id(t):
        key = tuple(encode(t))
        if key not in index:
            index[key] = len(static)
            static.append(t)
        return index[key]

    def place(tx, ty, tw, th, c):
        for i, t in enumerate(tiles_of(c, tw, th)):
            smap[(ty + i // tw) * SCREEN_W + tx + i % tw] = tile_id(t)

    def text(tx, ty, s):
        ids = []
        for i, ch in enumerate(s):
            ids.append(tile_id(font_tile(ch)))
            smap[ty * SCREEN_W + tx + i] = ids[-1]
        return ids

    for tx, ty, word in TITLE:
        for i, ch in enumerate(word):
            place(tx + i * 2, ty, 2, 2, big_letter(ch))
    place(DRAGSTER_X, DRAGSTER_Y, 8, 3, dragster())
    text(*CREDIT)
    press_ids = text(*PRESS)
    # pole below the animated area
    below = canvas(8, 8)
    pole(below, 0, 8)
    for ty in range(FLAG_Y + FLAG_H, PRESS[1] + 1):
        smap[ty * SCREEN_W + FLAG_X] = tile_id(below)

    flag_a = len(static)
    flag_b = flag_a + FLAG_W * FLAG_H
    assert flag_b + FLAG_W * FLAG_H <= 256, "splash tiles exceed 256"
    for i in range(FLAG_W * FLAG_H):
        smap[(FLAG_Y + i // FLAG_W) * SCREEN_W + FLAG_X + i % FLAG_W] = flag_a + i
    frames = [tiles_of(flag_frame(k), FLAG_W, FLAG_H) for k in range(FLAG_FRAMES)]
    return static, smap, press_ids, flag_a, flag_b, frames


def write(static, smap, press_ids, flag_a, flag_b, frames):
    def hexrows(data):
        return "\n".join("    " + ", ".join(f"0x{b:02X}" for b in data[i:i + 16]) + ","
                         for i in range(0, len(data), 16))

    def enc(tiles):
        out = []
        for t in tiles:
            out += encode(t)
        return out

    hdr = "// Generated by tools/gen_splash.py - do not edit.\n"
    with open(os.path.join(ROOT, "res", "splash.c"), "w") as f:
        f.write(hdr + '#include "splash.h"\n\n')
        f.write("const uint8_t splash_tiles[] = {\n" + hexrows(enc(static)) + "\n};\n\n")
        f.write("const uint8_t splash_map[] = {\n" + hexrows(smap) + "\n};\n\n")
        f.write("const uint8_t splash_press[] = { " + ", ".join(map(str, press_ids)) + " };\n\n")
        f.write(f"const uint8_t splash_flag[{FLAG_FRAMES}][{FLAG_W * FLAG_H * 16}] = {{\n")
        for fr in frames:
            f.write("  {\n" + hexrows(enc(fr)) + "\n  },\n")
        f.write("};\n")
    with open(os.path.join(ROOT, "res", "splash.h"), "w") as f:
        f.write(hdr + "#ifndef SPLASH_DATA_H\n#define SPLASH_DATA_H\n\n#include <stdint.h>\n\n")
        for name, val in (("SPLASH_STATIC_COUNT", len(static)), ("SPLASH_FLAG_A", flag_a),
                          ("SPLASH_FLAG_B", flag_b), ("SPLASH_FLAG_X", FLAG_X),
                          ("SPLASH_FLAG_Y", FLAG_Y), ("SPLASH_FLAG_W", FLAG_W),
                          ("SPLASH_FLAG_H", FLAG_H), ("SPLASH_FLAG_FRAMES", FLAG_FRAMES),
                          ("SPLASH_PRESS_X", PRESS[0]), ("SPLASH_PRESS_Y", PRESS[1]),
                          ("SPLASH_PRESS_LEN", len(PRESS[2]))):
            f.write(f"#define {name:<20} {val}u\n")
        f.write("\nextern const uint8_t splash_tiles[];\nextern const uint8_t splash_map[];\n")
        f.write("extern const uint8_t splash_press[];\n")
        f.write(f"extern const uint8_t splash_flag[{FLAG_FRAMES}][{FLAG_W * FLAG_H * 16}];\n\n#endif\n")


def preview(static, smap, flag_a, frames, path):
    from PIL import Image
    shades = [(224, 248, 208), (136, 192, 112), (52, 104, 86), (8, 24, 32)]
    sheet = Image.new("RGB", (4 * 168, 2 * 152), "white")
    for k, fr in enumerate(frames):
        img = Image.new("RGB", (160, 144))
        for i, tid in enumerate(smap):
            tx, ty = i % SCREEN_W, i // SCREEN_W
            t = fr[tid - flag_a] if tid >= flag_a else static[tid]
            for y in range(8):
                for x in range(8):
                    img.putpixel((tx * 8 + x, ty * 8 + y), shades[t[y][x]])
        sheet.paste(img, ((k % 4) * 168, (k // 4) * 152))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(path)


if __name__ == "__main__":
    data = build()
    write(*data)
    if "--preview" in sys.argv:
        static, smap, _, flag_a, _, frames = data
        preview(static, smap, flag_a, frames, sys.argv[sys.argv.index("--preview") + 1])
    print(f"splash static tiles: {len(data[0])}, flag buffers at {data[3]}/{data[4]}")
