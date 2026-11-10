// Screen layout (20x18 tiles, 1-tile margin all round):
//
//  row 1      class icon + class name            | tree lamps, cols 17-18, y 4..115
//                                                |   (half a tile above the grid)
//  rows 3-9   tach gauge (cols 1-7)              |   5 ambers, green, red
//             speedo gauge (cols 9-15)           |
//             gear digit / km/h readout sit in the gauges' bottom gaps
//  row 10     "SHIFT" warning under the tach (blank otherwise)
//  rows 11-12 big elapsed time
//  row 13     quarter-mile track (cols 1-15) with the class car sprite
//  rows 15-16 message lines (cols 1-18)
//
// Needles are sprites: 3 segments each, one of NEEDLE_DIRS pre-drawn angles.

#include <gb/gb.h>
#include <string.h>
#include "display.h"
#include "physics.h"
#include "tiles.h"

#define TACH_X     1
#define SPEEDO_X   9
#define GAUGE_Y    3
#define GEAR_X     (TACH_X + 3)        // centre column of the tach
#define GEAR_Y     (GAUGE_Y + 4)
// Speed readout: sprites, centred on the speedo pivot (x = SPEEDO_X*8 + 27.5).
// Glyphs are 5 px wide inside their tile (x 1..5), 6 px apart.
#define KMH_CX2    (SPEEDO_X * 16 + 55)  // pivot x, doubled to keep the .5
#define KMH_OAM_Y  (GAUGE_Y * 8 + 43 + 16)  // glyph top at y 67: 3 px below the old text row
#define LABEL_Y    (GAUGE_Y + 7)
#define TIME_X     6
#define TIME_Y     11
#define TRACK_Y    13
#define TRACK_X0   1
#define START_X    (TRACK_X0 + 2)   // car is 2 tiles long; tree stands in front
#define TRACK_X1   15   // finish tile; col 16 left clear before the tree
#define TREE_X     17
#define TREE_Y     0    // lamps start 4 px into this row (half-tile up)
#define MSG_X      1
#define MSG_Y      15

// OAM coordinates for a needle segment centred on the gauge pivot
// (pivot pixel centre minus the segment tile's centre, plus OAM offsets 8/16).
#define TACH_OAM_X    (TACH_X * 8 + 24 + 8)
#define SPEEDO_OAM_X  (SPEEDO_X * 8 + 24 + 8)
#define GAUGE_OAM_Y   (GAUGE_Y * 8 + 24 + 16)

#define SPR_CAR       0   // 0,1
#define SPR_SMOKE     2
#define SPR_TACH      3   // 3,4,5
#define SPR_SPEEDO    6   // 6,7,8
#define SPR_KMH       9   // 9,10,11


// Last drawn values: tiles are only rewritten when something changes.
static uint16_t last_kmh = 0xFFFFu;
static uint8_t kmh_tick;
static uint8_t last_gear = 0xFFu;
static uint8_t last_shift = 0xFFu;
static uint16_t last_time = 0xFFFFu;


static void put(uint8_t x, uint8_t y, uint8_t t) {
    set_bkg_tile_xy(x, y, t);
}

static void put_seg(uint8_t x, uint8_t y, uint8_t sym) {
    put(x, y, (uint8_t)(T_SEG + sym * 2u));
    put(x, y + 1, (uint8_t)(T_SEG + sym * 2u + 1u));
}

void display_text(uint8_t x, uint8_t y, const char *s) {
    while (*s && x < 20) {
        char c = *s++;
        if (c >= 'a' && c <= 'z') c = (char)(c - 32);
        if (c < ' ' || c > 'Z') c = ' ';
        put(x++, y, (uint8_t)(T_FONT + (uint8_t)(c - ' ')));
    }
}

static void clear_row(uint8_t y, uint8_t x0, uint8_t x1) {
    uint8_t x;
    for (x = x0; x <= x1; x++) put(x, y, T_FONT);  // T_FONT + 0 = space
}

void fmt_uint(char *buf, uint16_t v, uint8_t width) {
    uint8_t i = width;
    buf[width] = 0;
    do {
        buf[--i] = (char)('0' + v % 10u);
        v /= 10u;
    } while (v && i);
    while (i) buf[--i] = ' ';
}

void fmt_time(char *buf, uint16_t h) {
    if (h > 9999u) h = 9999u;
    buf[0] = (char)('0' + h / 1000u);
    buf[1] = (char)('0' + (h / 100u) % 10u);
    buf[2] = '.';
    buf[3] = (char)('0' + (h / 10u) % 10u);
    buf[4] = (char)('0' + h % 10u);
    buf[5] = 0;
    if (buf[0] == '0') buf[0] = ' ';
}

void display_msg(const char *line1, const char *line2) {
    clear_row(MSG_Y, MSG_X, MSG_X + MSG_WIDTH - 1u);
    clear_row(MSG_Y + 1, MSG_X, MSG_X + MSG_WIDTH - 1u);
    if (line1) display_text((uint8_t)(MSG_X + (MSG_WIDTH - strlen(line1)) / 2u), MSG_Y, line1);
    if (line2) display_text((uint8_t)(MSG_X + (MSG_WIDTH - strlen(line2)) / 2u), MSG_Y + 1, line2);
}

void display_class(uint8_t cls) {
    uint16_t red = car_classes[cls].redline;
    const uint8_t *map = red < 8000u ? map_tach0 : (red < 9500u ? map_tach1 : map_tach2);

    set_bkg_tiles(TACH_X, GAUGE_Y, GAUGE_TILES, GAUGE_TILES, map);
    last_gear = 0xFFu;

    // Class icon (2 tiles) + name; the track car uses the same picture.
    clear_row(1, 1, 16);
    put(1, 1, (uint8_t)(T_CARS + cls * 2u));
    put(2, 1, (uint8_t)(T_CARS + cls * 2u + 1u));
    display_text(4, 1, car_classes[cls].name);
    set_sprite_tile(SPR_CAR, (uint8_t)(S_CARS + cls * 2u));
    set_sprite_tile(SPR_CAR + 1, (uint8_t)(S_CARS + cls * 2u + 1u));
}

// sweep: needle deflection in binary degrees (0..ANG_SWEEP). Offsets come
// precomputed from tools/gen_tiles.py (multiplies are slow on the SM83).
static void place_needle(uint8_t spr, uint8_t ox, uint8_t sweep) {
    const int8_t *n = &needle_table[(uint16_t)sweep * 7u];
    uint8_t tile = (uint8_t)(S_NEEDLE + (uint8_t)n[0]);
    uint8_t i;
    for (i = 0; i < 3; i++) {
        set_sprite_tile(spr + i, tile);
        move_sprite(spr + i, (uint8_t)(ox + n[1]), (uint8_t)(GAUGE_OAM_Y + n[2]));
        n += 2;
    }
}

void display_gauges(uint16_t rpm, uint16_t kmh) {
    uint16_t sw;
    if (rpm > TACH_MAX) rpm = TACH_MAX;
    if (kmh > SPEEDO_MAX) kmh = SPEEDO_MAX;
    // Divisions are slow on the SM83, so the sweep uses 16-bit multiply + shift:
    // rpm * 192 / 10000 ~= (rpm >> 4) * 79 >> 8,  kmh * 192 / 400 ~= kmh * 123 >> 8
    sw = (uint16_t)(((rpm >> 4) * 79u) >> 8);
    place_needle(SPR_TACH, TACH_OAM_X, sw > ANG_SWEEP ? ANG_SWEEP : (uint8_t)sw);
    sw = (uint16_t)((kmh * 123u) >> 8);
    place_needle(SPR_SPEEDO, SPEEDO_OAM_X, sw > ANG_SWEEP ? ANG_SWEEP : (uint8_t)sw);
    // Refresh the number at 15 Hz: steadier to read than every frame.
    if (kmh != last_kmh && (++kmh_tick & 3u) == 0) {
        uint8_t d[3], n, i, x;
        last_kmh = kmh;
        // digits by subtraction (no division)
        d[0] = 0; while (kmh >= 100u) { kmh -= 100u; d[0]++; }
        d[1] = 0; while (kmh >= 10u)  { kmh -= 10u;  d[1]++; }
        d[2] = (uint8_t)kmh;
        n = d[0] ? 3u : (d[1] ? 2u : 1u);
        // left edge of the glyphs: pivot - width/2, width = 6n - 1
        x = (uint8_t)((KMH_CX2 + 1u - (6u * n - 1u)) / 2u);
        for (i = 0; i < 3; i++) {
            if (i < n) {
                set_sprite_tile(SPR_KMH + i, (uint8_t)(S_DIGITS + d[3u - n + i]));
                // tile x = glyph x - 1; OAM adds 8
                move_sprite(SPR_KMH + i, (uint8_t)(x + 6u * i + 7u), KMH_OAM_Y);
            } else {
                hide_sprite(SPR_KMH + i);
            }
        }
    }
}

void display_gear(uint8_t gear) {
    if (gear == last_gear) return;
    last_gear = gear;
    put_seg(GEAR_X, GEAR_Y, gear);
}

// Elapsed time "SS.HH". Runs every frame during a race, so digits are
// counted up incrementally (no division) and only changed digits are drawn.
static uint8_t time_digit[4];       // tens, ones, tenths, hundredths
static uint8_t time_drawn[4] = { 0xFFu, 0xFFu, 0xFFu, 0xFFu };

void display_time(uint16_t h) {
    uint8_t i, sym;
    if (h > 9999u) h = 9999u;
    if (h == last_time) return;
    if (last_time != 0xFFFFu && h > last_time && h - last_time < 10u) {
        uint8_t n = (uint8_t)(h - last_time);
        while (n--) {
            i = 3;
            while (++time_digit[i] == 10u) {
                time_digit[i] = 0;
                if (i == 0) break;
                i--;
            }
        }
    } else {
        time_digit[0] = (uint8_t)(h / 1000u);
        time_digit[1] = (uint8_t)((h / 100u) % 10u);
        time_digit[2] = (uint8_t)((h / 10u) % 10u);
        time_digit[3] = (uint8_t)(h % 10u);
    }
    last_time = h;
    for (i = 0; i < 4; i++) {
        sym = (i == 0 && time_digit[0] == 0) ? SEG_BLANK : time_digit[i];
        if (time_drawn[i] != sym) {
            time_drawn[i] = sym;
            put_seg((uint8_t)(TIME_X + i + (i >= 2u)), TIME_Y, sym);   // skip the '.' column
        }
    }
}

void display_shift_light(uint8_t on) {
    if (on == last_shift) return;
    last_shift = on;
    display_text(TACH_X + 1, LABEL_Y, on ? "SHIFT" : "     ");
}

void display_lamps(uint8_t mask) {
    // Tree is drawn 4 px above the tile grid (see tools/gen_tiles.py), so a
    // tile row may show two lamps; tree_map holds 4 variants per row.
    static uint8_t drawn = 0xFFu;   // 0xFF forces a full draw the first time
    uint8_t changed = (drawn == 0xFFu) ? 0x7Fu : (uint8_t)(mask ^ drawn);
    uint8_t r, idx, touch;
    int8_t up, lo;
    const uint8_t *t;
    drawn = mask;
    for (r = 0; r < TREE_ROWS; r++) {
        up = tree_row_up[r];
        lo = tree_row_lo[r];
        touch = (uint8_t)((up >= 0 ? (1u << up) : 0u) | (lo >= 0 ? (1u << lo) : 0u));
        if (!(changed & touch)) continue;
        idx = 0;
        if (up >= 0 && (mask & (1u << up))) idx |= 2u;
        if (lo >= 0 && (mask & (1u << lo))) idx |= 1u;
        t = &tree_map[(uint8_t)(r * 4u + idx) * 2u];
        put(TREE_X,     (uint8_t)(TREE_Y + r), t[0]);
        put(TREE_X + 1, (uint8_t)(TREE_Y + r), t[1]);
    }
}

void display_car(uint32_t dist, uint8_t wheelspin, uint8_t frame) {
    // Car (16 px) runs from the start line until its nose reaches the finish tile.
    uint16_t ft = (uint16_t)(dist >> 16);
    uint8_t x, y = TRACK_Y * 8u + 16u;
    if (ft > 1320u) ft = 1320u;
    // ft * 96 / 1320 ~= (ft / 4) * 149 / 512, kept in 16 bits (96 = run length in px)
    x = (uint8_t)((((ft >> 2) * 149u) >> 9) + TRACK_X0 * 8u + 8u);
    move_sprite(SPR_CAR, x, y);
    move_sprite(SPR_CAR + 1, x + 8u, y);
    if (wheelspin) {
        set_sprite_tile(SPR_SMOKE, (uint8_t)(S_SMOKE + ((frame >> 2) & 1u)));
        move_sprite(SPR_SMOKE, x - 7u, y);
    } else {
        hide_sprite(SPR_SMOKE);
    }
}

void display_shake(int8_t dy) {
    SCY_REG = (uint8_t)dy;
}

void display_init(void) {
    uint8_t x;

    DISPLAY_OFF;
    BGP_REG = 0xE4;
    OBP0_REG = 0xE4;
    set_bkg_data(0, BG_TILE_COUNT, bg_tiles);
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    fill_bkg_rect(0, 0, 32, 32, T_FONT);  // spaces

    set_bkg_tiles(SPEEDO_X, GAUGE_Y, GAUGE_TILES, GAUGE_TILES, map_speedo);
    display_text(TIME_X + 5, TIME_Y + 1, "S");

    for (x = TRACK_X0; x < TRACK_X1; x++) put(x, TRACK_Y, T_TRACK);
    put(TRACK_X1, TRACK_Y, T_FINISH);
    // Start line: mini light tree just ahead of the staged car's nose.
    put(START_X, TRACK_Y - 1, T_MINI_TREE);
    put(START_X, TRACK_Y,     T_MINI_TREE + 1);

    set_sprite_tile(SPR_SMOKE, S_SMOKE);

    put(TIME_X + 2, TIME_Y + 1, (uint8_t)(T_FONT + ('.' - ' ')));
    display_lamps(0);
    display_shift_light(0);
    display_time(0);

    SHOW_BKG;
    SHOW_SPRITES;
    DISPLAY_ON;
}
