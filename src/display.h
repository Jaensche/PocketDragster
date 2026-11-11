#ifndef DISPLAY_H
#define DISPLAY_H

#include <stdint.h>

// Christmas tree lamp bits
#define LAMP_AMBER(n) ((uint8_t)(1u << (n)))   // n = 0..4, top to bottom
#define LAMP_GREEN    0x20u
#define LAMP_RED      0x40u

#define MSG_WIDTH     18u   // characters in the (single) message line

// Button icons usable inside display_text / display_msg strings.
#define ICON_LEFT     "["
#define ICON_RIGHT    "]"
#define ICON_A        "\\"
#define ICON_B        "#"
#define ICON_UP       "^"
#define ICON_DOWN     "_"
#define ICON_TROPHY   "`"

void display_init(void);   // loads the game tile set and redraws everything
void display_text(uint8_t x, uint8_t y, const char *s);
void display_msg(const char *line);   // one line at the bottom, 0 = clear
void display_class(uint8_t cls, uint16_t best_et);   // best_et 0 = none
void display_race_mode(uint8_t on);   // top line: class name (0) or race timer (1)
void display_gauges(uint16_t rpm, uint16_t kmh);
void display_gear(uint8_t gear);
void display_time(uint16_t hundredths);
void display_lamps(uint8_t mask);
void display_car(uint32_t dist, uint8_t wheelspin, uint8_t blown, uint8_t frame);
void display_shake(int8_t dy);

// Formats v as decimal, right-aligned in width chars (space padded), into buf.
void fmt_uint(char *buf, uint16_t v, uint8_t width);
// Formats hundredths as "SS.HH" (5 chars + NUL).
void fmt_time(char *buf, uint16_t hundredths);

#endif
