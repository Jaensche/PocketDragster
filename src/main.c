// Hello world / hardware smoke test.
// Checks on real hardware: text output, joypad input, sound channel 1.

#include <gb/gb.h>
#include <gb/hardware.h>
#include <stdio.h>
#include <gbdk/console.h>

static void sound_init(void) {
    NR52_REG = 0x80;  // sound on
    NR50_REG = 0x77;  // max volume both sides
    NR51_REG = 0xFF;  // all channels to both outputs
}

static void beep(uint16_t freq) {
    NR10_REG = 0x00;              // no sweep
    NR11_REG = 0x80;              // 50% duty
    NR12_REG = 0xF3;              // volume 15, decay
    NR13_REG = (uint8_t)freq;
    NR14_REG = 0x80 | (uint8_t)(freq >> 8);  // trigger
}

static void show_button(uint8_t x, uint8_t y, const char *name, uint8_t down) {
    gotoxy(x, y);
    printf(down ? "[%s]" : " %s ", name);
}

void main(void) {
    uint8_t keys, prev = 0;

    sound_init();
    DISPLAY_ON;

    gotoxy(3, 2);  printf("QUARTER  MILE");
    gotoxy(4, 4);  printf("hello, world!");
    gotoxy(1, 7);  printf("press buttons:");

    while (1) {
        keys = joypad();

        show_button(1, 9,  "A",  keys & J_A);
        show_button(6, 9,  "B",  keys & J_B);
        show_button(1, 11, "START",  keys & J_START);
        show_button(9, 11, "SELECT", keys & J_SELECT);
        show_button(1, 13, "U", keys & J_UP);
        show_button(5, 13, "D", keys & J_DOWN);
        show_button(9, 13, "L", keys & J_LEFT);
        show_button(13, 13, "R", keys & J_RIGHT);

        // beep on new A/B presses
        if ((keys & J_A) && !(prev & J_A)) beep(1750);   // ~ 1 kHz
        if ((keys & J_B) && !(prev & J_B)) beep(1546);   // ~ 500 Hz

        prev = keys;
        vsync();
    }
}
