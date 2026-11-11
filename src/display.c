// Screen layout (20x18 tiles, 1-tile margin all round):
//
//  row 1      class name (class select)  /  big timer, sprites y 4..19 (race)
//             + trophy and best time on the right in both modes
//  rows 3-9   tach gauge (cols 1-7), speedo gauge (cols 9-15)
//             gear digit / km/h readout sit in the gauges' bottom gaps
//  rows 10-11 grandstand, scrolls at half the road speed (parallax)
//  rows 12-15 slanted road with the class car, scrolls with the camera
//  row 16     one message line (cols 1-18)
//  cols 17-19 window layer: the light tree (y 4..115) and the end of the
//             message line. The window ignores the scroll registers, so the
//             tree stays put while the road moves underneath.
//
// Scrolling: an LYC interrupt sets SCX at the grandstand (line 80), at the
// road (line 96) and back to 0 at line 125. All three lines are blank in the
// artwork, so a late register write never shows.
// Needles are sprites: 3 segments each, one of NEEDLE_DIRS pre-drawn angles.

#include <gb/gb.h>
#include <gb/hardware.h>
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
#define KMH_OAM_Y  (GAUGE_Y * 8 + 43 + 16)
// Race timer: sprites at the top left. Columns: digit, digit, '.', digit, digit, 'S'.
#define TIME_PX_X  8
#define TIME_PX_Y  4
#define BEST_X     11   // trophy column; time follows in cols 12-16
#define CROWD_Y    10   // map rows 10-11
#define ROAD_Y     12   // map rows 12-15
#define TREE_X     17   // first window column on screen
#define TREE_Y     0    // lamps start 4 px into this row (half-tile up)
#define MSG_X      1
#define MSG_Y      16

#define CROWD_LY   80   // raster split lines (blank pixel rows in the art)
#define ROAD_LY    96
#define RESET_LY   125

// OAM coordinates for a needle segment centred on the gauge pivot
// (pivot pixel centre minus the segment tile's centre, plus OAM offsets 8/16).
#define TACH_OAM_X    (TACH_X * 8 + 24 + 8)
#define SPEEDO_OAM_X  (SPEEDO_X * 8 + 24 + 8)
#define GAUGE_OAM_Y   (GAUGE_Y * 8 + 24 + 16)

#define SPR_SMOKE     2
#define SPR_TACH      3   // 3,4,5
#define SPR_SPEEDO    6   // 6,7,8
#define SPR_KMH       9   // 9,10,11
#define SPR_BLOWN     12  // 12,13,14: smoke from a blown engine
#define BLOWN_PUFFS   3
#define SPR_TIME      15  // 15..22 digits (top/bottom pairs), 23 '.', 24 'S'
#define TIME_SPRITES  10
#define SPR_CAR       25  // 25..32: class car, 4x2 tile slots (24 or 32 x 12 picture)
#define CAR_TILES     8
#define SPR_START_TREE 33 // 33,34: start tree at the far edge of the road
#define PUFF_LIFE     48  // frames a puff takes to rise and fade
#define CAR_OAM_Y     (107u + 16u)   // car top at y 107: wheels on the near lane


// Last drawn values: tiles are only rewritten when something changes.
static uint16_t last_kmh = 0xFFFFu;
static uint8_t kmh_tick;
static uint8_t last_gear = 0xFFu;
static uint16_t last_time = 0xFFFFu;
static uint8_t lamps_drawn = 0xFFu;   // 0xFF forces a full tree draw

static uint8_t cur_cls;
static uint16_t cur_best;
static uint8_t race_mode;

// Scroll state for the raster splits (written by the main loop, read by the ISR).
static volatile uint8_t scx_crowd, scx_road;
static uint16_t cam;          // world x at the screen's left edge
static uint16_t road_last;    // highest world column streamed into the map
static uint8_t isr_added;


// Background writes left of the tree go to the BG map, from col 17 on to the
// window map (which stays fixed while the BG scrolls).
static void put(uint8_t x, uint8_t y, uint8_t t) {
    if (x >= TREE_X) set_win_tile_xy((uint8_t)(x - TREE_X), y, t);
    else set_bkg_tile_xy(x, y, t);
}

static void put_seg(uint8_t x, uint8_t y, uint8_t sym) {
    put(x, y, (uint8_t)(T_SEG + sym * 2u));
    put(x, y + 1, (uint8_t)(T_SEG + sym * 2u + 1u));
}

void display_text(uint8_t x, uint8_t y, const char *s) {
    while (*s && x < 20) {
        char c = *s++;
        if (c >= 'a' && c <= 'z') c = (char)(c - 32);
        if (c < ' ' || c > '`') c = ' ';   // '#' '[' '\\' ']' '^' '_' '`' are icons
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

void display_msg(const char *line) {
    clear_row(MSG_Y, MSG_X, MSG_X + MSG_WIDTH - 1u);
    if (line) display_text((uint8_t)(MSG_X + (MSG_WIDTH - strlen(line)) / 2u), MSG_Y, line);
}

// ------------------------------------------------------------------ top line
static void draw_top_line(void) {
    char buf[6];
    clear_row(1, 1, 16);
    if (!race_mode) display_text(1, 1, car_classes[cur_cls].name);
    if (cur_best) {
        fmt_time(buf, cur_best);
        display_text(BEST_X, 1, ICON_TROPHY);
        display_text(BEST_X + 1u, 1, buf);
    }
}

static void place_timer(uint8_t show) {
    uint8_t i, y = show ? TIME_PX_Y + 16u : 0u;   // y 0 = hidden
    for (i = 0; i < 4u; i++) {
        uint8_t px = (uint8_t)(TIME_PX_X + (i + (i >= 2u)) * 8u + 8u);   // skip the '.' column
        move_sprite(SPR_TIME + i * 2u,      px, y);
        move_sprite(SPR_TIME + i * 2u + 1u, px, show ? y + 8u : 0u);
    }
    move_sprite(SPR_TIME + 8u, TIME_PX_X + 2u * 8u + 8u, show ? y + 8u : 0u);
    move_sprite(SPR_TIME + 9u, TIME_PX_X + 5u * 8u + 8u, show ? y + 8u : 0u);
}

void display_race_mode(uint8_t on) {
    race_mode = on;
    draw_top_line();
    place_timer(on);
}

static uint8_t place_car(void);

void display_class(uint8_t cls, uint16_t best_et) {
    uint8_t i;
    uint16_t red = car_classes[cls].redline;
    const uint8_t *map = red < 8000u ? map_tach0 : (red < 9500u ? map_tach1 : map_tach2);
    cur_cls = cls;
    cur_best = best_et;

    set_bkg_tiles(TACH_X, GAUGE_Y, GAUGE_TILES, GAUGE_TILES, map);
    last_gear = 0xFFu;
    draw_top_line();
    // The track car shows the class picture; move it in the same frame, so
    // the new picture and its new width appear together.
    for (i = 0; i < CAR_TILES; i++)
        set_sprite_tile(SPR_CAR + i, (uint8_t)(S_CARS + cls * CAR_TILES + i));
    place_car();
}

// ------------------------------------------------------------------ gauges
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
            set_sprite_tile(SPR_TIME + i * 2u,      (uint8_t)(S_SEG + sym * 2u));
            set_sprite_tile(SPR_TIME + i * 2u + 1u, (uint8_t)(S_SEG + sym * 2u + 1u));
        }
    }
}

// ------------------------------------------------------------------ tree
void display_lamps(uint8_t mask) {
    // Tree is drawn 4 px above the tile grid (see tools/gen_tiles.py), so a
    // tile row may show two lamps; tree_map holds 4 variants per row.
    uint8_t changed = (lamps_drawn == 0xFFu) ? 0x7Fu : (uint8_t)(mask ^ lamps_drawn);
    uint8_t r, idx, touch;
    int8_t up, lo;
    const uint8_t *t;
    lamps_drawn = mask;
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

// ------------------------------------------------------------------ road
static void lcd_isr(void) {
    if (LYC_REG == CROWD_LY) {
        SCX_REG = scx_crowd;
        LYC_REG = ROAD_LY;
    } else if (LYC_REG == ROAD_LY) {
        SCX_REG = scx_road;
        LYC_REG = RESET_LY;
    } else {
        SCX_REG = 0;
        LYC_REG = CROWD_LY;
    }
}

static void stream_column(uint16_t col) {
    set_bkg_tiles((uint8_t)(col & 31u), ROAD_Y, 1, ROAD_ROWS, &road_map[col * ROAD_ROWS]);
}

// Fills the map with world columns 0..31 (camera at the start line).
static void road_reset(void) {
    uint8_t c;
    for (c = 0; c < 32u; c++) stream_column(c);
    road_last = 31u;
    cam = 0;
    scx_road = scx_crowd = 0;
}

// ------------------------------------------------------------------ car
// Car picture width per class; Top Fuel is the long one.
static const uint8_t car_w[NUM_CLASSES] = { 24, 24, 24, 32 };
// Engine position inside each class's car picture (px from the left).
static const uint8_t engine_x[NUM_CLASSES] = { 19, 19, 17, 11 };
static uint8_t smoke_t;      // blown-smoke animation clock, 0..PUFF_LIFE-1
static uint8_t smoke_shown;
static uint16_t car_ft;      // last drawn distance (ft)

static void blown_smoke(uint8_t car_x, uint8_t car_y) {
    uint8_t i, age, tile;
    if (++smoke_t >= PUFF_LIFE) smoke_t = 0;
    for (i = 0; i < BLOWN_PUFFS; i++) {
        // three puffs, evenly staggered over the life cycle
        age = (uint8_t)(smoke_t + i * (PUFF_LIFE / BLOWN_PUFFS));
        if (age >= PUFF_LIFE) age -= PUFF_LIFE;
        tile = age < 10u ? S_PUFF : (age < 28u ? S_SMOKE : S_SMOKE + 1u);
        set_sprite_tile(SPR_BLOWN + i, tile);
        // rises 24 px and drifts back 8 px over its life
        move_sprite(SPR_BLOWN + i,
                    (uint8_t)(car_x + engine_x[cur_cls] - 4u - age / 6u),
                    (uint8_t)(car_y - 6u - age / 2u));
    }
    smoke_shown = 1;
}

// Moves the camera with the car, streams new road columns, positions the car
// sprites and returns the car's OAM x. The camera holds still at the start
// line, then keeps the car's nose at CAM_NOSE_X, and stops with the finish
// line in view so the car drives up to it.
static uint8_t place_car(void) {
    uint16_t nose = (uint16_t)(WORLD_START_WX + ((car_ft * 3u) >> 2));   // 3/4 px per ft
    uint16_t c = nose > CAM_NOSE_X ? nose - CAM_NOSE_X : 0u;
    uint8_t x, i;
    if (c > CAM_MAX) c = CAM_MAX;
    if (c < cam) road_reset();                       // new run: back to the start
    cam = c;
    while (road_last < (cam >> 3) + 31u && road_last < ROAD_COLS - 1u)
        stream_column(++road_last);                  // at most ~1 column per frame
    scx_road = (uint8_t)cam;
    scx_crowd = (uint8_t)(cam >> 1);

    // Start tree: post at the start line's far end, standing on the far edge
    // (tree art: post at x 2 of the tile, last visible row 13 -> y 97).
    if (cam < START_LINE_WX + 6u) {
        x = (uint8_t)(START_LINE_WX - 3u - cam + 8u);
        move_sprite(SPR_START_TREE,      x, 84u + 16u);
        move_sprite(SPR_START_TREE + 1u, x, 92u + 16u);
    } else {
        hide_sprite(SPR_START_TREE);
        hide_sprite(SPR_START_TREE + 1u);
    }

    x = (uint8_t)(nose - cam - car_w[cur_cls] + 8u);
    for (i = 0; i < CAR_TILES; i++)
        move_sprite(SPR_CAR + i, (uint8_t)(x + (i & 3u) * 8u), (uint8_t)(CAR_OAM_Y + (i >> 2) * 8u));
    return x;
}

void display_car(uint32_t dist, uint8_t wheelspin, uint8_t blown, uint8_t frame) {
    uint16_t ft = (uint16_t)(dist >> 16);
    uint8_t x, y = CAR_OAM_Y, i;
    car_ft = ft > 1320u ? 1320u : ft;
    x = place_car();
    if (wheelspin) {
        set_sprite_tile(SPR_SMOKE, (uint8_t)(S_SMOKE + ((frame >> 2) & 1u)));
        move_sprite(SPR_SMOKE, x - 7u, y + 4u);   // at tyre height
    } else {
        hide_sprite(SPR_SMOKE);
    }
    if (blown) {
        blown_smoke(x, y);
    } else if (smoke_shown) {
        for (i = 0; i < BLOWN_PUFFS; i++) hide_sprite(SPR_BLOWN + i);
        smoke_shown = 0;
        smoke_t = 0;
    }
}

void display_shake(int8_t dy) {
    SCY_REG = (uint8_t)dy;
}

// ------------------------------------------------------------------ init
void display_init(void) {
    uint8_t x;

    DISPLAY_OFF;
    BGP_REG = 0xE4;
    OBP0_REG = 0xE4;
    // Forget what was drawn: we may come back from the title screen.
    last_kmh = 0xFFFFu;
    last_gear = lamps_drawn = 0xFFu;
    last_time = 0xFFFFu;
    for (x = 0; x < 4u; x++) time_drawn[x] = 0xFFu;
    set_bkg_data(0, BG_TILE_COUNT, bg_tiles);
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    fill_bkg_rect(0, 0, 32, 32, T_FONT);  // spaces

    // Window: own map (0x9C00), parked over cols 17-19 for the whole height.
    LCDC_REG |= LCDCF_WIN9C00;
    fill_win_rect(0, 0, 3, 18, T_FONT);
    WX_REG = TREE_X * 8u + 7u;
    WY_REG = 0;

    set_bkg_tiles(SPEEDO_X, GAUGE_Y, GAUGE_TILES, GAUGE_TILES, map_speedo);
    for (x = 0; x < 32u; x++)              // grandstand repeats every CROWD_COLS
        set_bkg_tiles(x, CROWD_Y, 1, 2, &crowd_map[(x % CROWD_COLS) * 2u]);
    road_reset();

    set_sprite_tile(SPR_SMOKE, S_SMOKE);
    set_sprite_tile(SPR_START_TREE, S_MINI_TREE);
    set_sprite_tile(SPR_START_TREE + 1u, S_MINI_TREE + 1u);
    set_sprite_tile(SPR_TIME + 8u, S_TIME_DOT);
    set_sprite_tile(SPR_TIME + 9u, S_TIME_S);
    display_lamps(0);
    display_time(0);
    display_race_mode(0);

    // Raster splits for the parallax grandstand and the road.
    CRITICAL {
        STAT_REG = STATF_LYC;
        LYC_REG = CROWD_LY;
        if (!isr_added) { add_LCD(lcd_isr); isr_added = 1; }
    }
    set_interrupts(VBL_IFLAG | LCD_IFLAG);

    SHOW_BKG;
    SHOW_WIN;
    SHOW_SPRITES;
    DISPLAY_ON;
}
