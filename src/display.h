#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>

// Christmas tree lamp bits
#define LAMP_AMBER(n) ((uint8_t)(1u << (n)))   // n = 0..4, top to bottom
#define LAMP_GREEN    0x20u
#define LAMP_RED      0x40u

#define MSG_WIDTH     18u   // characters per message line

void display_init(void);
void display_text(uint8_t x, uint8_t y, const char *s);
void display_msg(const char *line1, const char *line2);
void display_class(uint8_t cls);
void display_gauges(uint16_t rpm, uint16_t kmh);
void display_gear(uint8_t gear);
void display_time(uint16_t hundredths);
void display_shift_light(uint8_t on);
void display_lamps(uint8_t mask);
void display_car(uint32_t dist, uint8_t wheelspin, uint8_t frame);
void display_shake(int8_t dy);

// Formats v as decimal, right-aligned in width chars (space padded), into buf.
void fmt_uint(char *buf, uint16_t v, uint8_t width);
// Formats hundredths as "SS.HH" (5 chars + NUL).
void fmt_time(char *buf, uint16_t hundredths);

#endif
