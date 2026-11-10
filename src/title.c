#include <gb/gb.h>
#include "title.h"
#include "splash.h"

#define FLAG_TILES  (SPLASH_FLAG_W * SPLASH_FLAG_H)
#define FRAME_TIME  6u    // frames per flag animation step (10 fps)
#define BLINK_MASK  32u   // PRESS START blink period: 32 frames on, 32 off

static uint8_t flag_map[2][FLAG_TILES];
static const uint8_t blank_row[SPLASH_PRESS_LEN];   // zeros = blank tile

void title_run(void) {
    uint8_t i, k = 0, buf = 0, t = 0, step = 0;
    uint8_t keys, prev = 0xFFu;   // a START held at power-on doesn't skip the splash

    DISPLAY_OFF;
    HIDE_SPRITES;
    SCX_REG = 0;
    SCY_REG = 0;
    BGP_REG = 0xE4;
    set_bkg_data(0, SPLASH_STATIC_COUNT, splash_tiles);
    set_bkg_data(SPLASH_FLAG_A, FLAG_TILES, splash_flag[0]);
    set_bkg_tiles(0, 0, 20, 18, splash_map);
    for (i = 0; i < FLAG_TILES; i++) {
        flag_map[0][i] = (uint8_t)(SPLASH_FLAG_A + i);
        flag_map[1][i] = (uint8_t)(SPLASH_FLAG_B + i);
    }
    SHOW_BKG;
    DISPLAY_ON;

    while (1) {
        vsync();
        keys = joypad();
        if ((keys & J_START) && !(prev & J_START)) break;
        prev = keys;
        t++;

        if ((t & (BLINK_MASK - 1u)) == 0)
            set_bkg_tiles(SPLASH_PRESS_X, SPLASH_PRESS_Y, SPLASH_PRESS_LEN, 1,
                          (t & BLINK_MASK) ? blank_row : splash_press);

        // Waving flag: upload the next frame into the hidden buffer (takes
        // about a frame with the LCD on), then point the map at it.
        if (++step == FRAME_TIME) {
            step = 0;
            k = (uint8_t)((k + 1u) % SPLASH_FLAG_FRAMES);
            buf ^= 1u;
            set_bkg_data(buf ? SPLASH_FLAG_B : SPLASH_FLAG_A, FLAG_TILES, splash_flag[k]);
            vsync();
            set_bkg_tiles(SPLASH_FLAG_X, SPLASH_FLAG_Y, SPLASH_FLAG_W, SPLASH_FLAG_H, flag_map[buf]);
        }
    }
    // Wait for START to be released so the game doesn't see it as a press.
    while (joypad() & J_START) vsync();
}
