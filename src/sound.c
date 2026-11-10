#include <gb/gb.h>
#include <gb/hardware.h>
#include "sound.h"
#include "tiles.h"

static uint8_t engine_on;
static uint8_t squeal_on;
static uint8_t beep_timer;     // CH1 busy with a beep
static uint8_t boom_timer;     // CH4 busy with the explosion
static uint8_t wobble;
static uint8_t rumble_on;

void sound_init(void) {
    NR52_REG = 0x80;
    NR50_REG = 0x77;
    NR51_REG = 0xFF;
    engine_on = squeal_on = beep_timer = boom_timer = rumble_on = 0;
}

// V8 firing frequency = rpm / 15 Hz; periods precomputed by tools/gen_tiles.py.
static uint16_t rpm_to_period(uint16_t rpm) {
    uint8_t i = (uint8_t)(rpm >> 6);
    if (i >= ENGINE_PERIODS) i = ENGINE_PERIODS - 1u;
    return engine_period[i];
}

void sound_engine(uint16_t rpm) {
    uint16_t x;
    if (!rpm) {
        if (engine_on) {
            NR22_REG = 0x00;       // DAC off silences the channel
            if (!boom_timer) NR42_REG = 0x00;
            engine_on = 0;
            rumble_on = 0;
        }
        return;
    }
    x = rpm_to_period(rpm);
    if (!engine_on) {
        NR21_REG = 0x00;           // 12.5% duty: buzzy
        NR22_REG = 0x90;           // volume 9, no envelope
        NR23_REG = (uint8_t)x;
        NR24_REG = 0x80 | (uint8_t)(x >> 8);
        engine_on = 1;
    } else {
        NR23_REG = (uint8_t)x;
        NR24_REG = (uint8_t)(x >> 8);   // no retrigger -> no click
    }
    if (!boom_timer) {
        // Low rumble on the noise channel; clock shift drops as rpm rises.
        uint8_t shift = (uint8_t)(7u - (rpm >> 11));   // 1000->7 .. 9999->3
        uint8_t nr43 = (uint8_t)((shift << 4) | 0x08 | 0x03); // 7-bit LFSR, divisor 3
        if (!rumble_on) {
            rumble_on = 1;
            NR41_REG = 0x00;
            NR42_REG = 0x30;       // volume 3, no envelope
            NR43_REG = nr43;
            NR44_REG = 0x80;
        } else {
            NR43_REG = nr43;
        }
    }
}

void sound_squeal(uint8_t on) {
    if (on == squeal_on) return;
    squeal_on = on;
    if (beep_timer) return;
    if (on) {
        NR10_REG = 0x00;
        NR11_REG = 0x40;           // 25% duty
        NR12_REG = 0x70;
        NR13_REG = (uint8_t)1990u;
        NR14_REG = 0x80 | (uint8_t)(1990u >> 8);
    } else {
        NR12_REG = 0x00;
    }
}

void sound_beep(uint8_t high) {
    uint16_t x = high ? 1899u : 1750u;   // 880 Hz / 440 Hz
    NR10_REG = 0x00;
    NR11_REG = 0x80;
    NR12_REG = 0xF2;
    NR13_REG = (uint8_t)x;
    NR14_REG = 0x80 | (uint8_t)(x >> 8);
    beep_timer = high ? 30u : 10u;
}

void sound_boom(void) {
    sound_squeal(0);
    NR22_REG = 0x00;
    engine_on = 0;
    rumble_on = 0;
    NR41_REG = 0x00;
    NR42_REG = 0xF7;               // full volume, slow decay
    NR43_REG = 0x71;               // low, rough noise
    NR44_REG = 0x80;
    boom_timer = 120;
}

// Starter per class: crank length, compression period (frames), CH2 period
// register of the starter tone, and how loud the engine fires on catch.
typedef struct {
    uint8_t  frames;
    uint8_t  period;
    uint16_t tone;      // 2048 - 131072 / Hz
    uint8_t  catch_env; // NR42 for the catch burst
    uint8_t  catch_nr43;
} crank_t;

static const crank_t cranks[4] = {
    { 54, 8,  737u, 0xA2, 0x62 },   // STOCK: slow starter, ~100 Hz, soft catch
    { 42, 6,  956u, 0xC2, 0x52 },   // MODIFIED: quicker, ~120 Hz
    { 33, 4, 1393u, 0xF3, 0x41 },   // FUNNY CAR: external starter whine, nitro bang
    { 33, 4, 1452u, 0xF4, 0x40 },   // TOP FUEL: even bigger bang
};

uint8_t sound_crank_phase(uint8_t cls, uint8_t t) {
    const crank_t *c = &cranks[cls & 3u];
    return (uint8_t)((t % c->period) < (c->period >> 1));
}

uint8_t sound_crank(uint8_t cls, uint8_t t) {
    const crank_t *c = &cranks[cls & 3u];
    uint16_t x;
    if (t >= c->frames) {
        // Catch: silence the starter, fire a noise burst. The engine tone is
        // re-triggered by sound_engine(); the burst holds CH4 for a moment.
        NR22_REG = 0x00;
        engine_on = 0;
        rumble_on = 0;
        NR41_REG = 0x00;
        NR42_REG = c->catch_env;
        NR43_REG = c->catch_nr43;
        NR44_REG = 0x80;
        boom_timer = 20;
        return 1;
    }
    // Starter motor tone, pitch sagging on each compression stroke.
    x = sound_crank_phase(cls, t) ? c->tone : (uint16_t)(c->tone - 120u);
    if (t == 0) {
        NR21_REG = 0x80;           // 50% duty
        NR22_REG = 0x70;           // volume 7, no envelope
        NR23_REG = (uint8_t)x;
        NR24_REG = 0x80 | (uint8_t)(x >> 8);
    } else {
        NR23_REG = (uint8_t)x;
        NR24_REG = (uint8_t)(x >> 8);
    }
    // A chug on the noise channel at every compression stroke.
    if ((t % c->period) == 0u) {
        NR41_REG = 0x00;
        NR42_REG = 0x61;           // volume 6, quick decay
        NR43_REG = 0x57;
        NR44_REG = 0x80;
    }
    return 0;
}

void sound_update(void) {
    if (beep_timer && --beep_timer == 0) {
        NR12_REG = 0x00;
        if (squeal_on) { squeal_on = 0; sound_squeal(1); }
    }
    if (boom_timer && --boom_timer == 0) {
        NR42_REG = 0x00;
    }
    if (squeal_on && !beep_timer) {
        uint16_t x = (uint16_t)(1984u + (wobble & 7u));
        wobble += 3;
        NR13_REG = (uint8_t)x;
        NR14_REG = (uint8_t)(x >> 8);
    }
}
