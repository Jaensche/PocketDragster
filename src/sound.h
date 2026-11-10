#ifndef SOUND_H
#define SOUND_H

#include <stdint.h>

// Channel use: CH2 engine tone, CH4 engine rumble / explosion,
// CH1 tree beeps and tire squeal.

void sound_init(void);
void sound_engine(uint16_t rpm);   // 0 = engine off
void sound_squeal(uint8_t on);
void sound_beep(uint8_t high);     // tree: amber = low, green = high
void sound_boom(void);
// Engine start: call once per frame with t = 0, 1, 2, ... while cranking.
// Returns 1 on the frame the engine catches (plays the catch sound).
uint8_t sound_crank(uint8_t cls, uint8_t t);
uint8_t sound_crank_phase(uint8_t cls, uint8_t t);   // 1 on a compression stroke
void sound_update(void);           // once per frame

#endif
