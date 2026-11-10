// Drag-race physics. Plain C with explicit integer widths so the same code
// runs on the Game Boy (SDCC, 16-bit int) and on the host (gcc) for tuning.
#ifndef PHYSICS_H
#define PHYSICS_H

#include <stdint.h>

#define NUM_CLASSES   4
#define NUM_GEARS     4
#define IDLE_RPM      1000u
#define TACH_MAX_RPM  10000u

// Distance unit: 1/65536 ft. Quarter mile = 1320 ft.
#define QUARTER_MILE  ((uint32_t)1320u << 16)

// Speed unit: 1/256 mph (uint16 -> max ~255 mph).
#define MPH(v)        ((uint16_t)((v) >> 8))
#define KMH(v)        ((uint16_t)((((v) >> 7) * 103u) >> 7))   // v/256 * 1.609 = (v>>7) * 0.805, 16-bit only

typedef struct {
    const char *name;
    uint16_t redline;        // engine blows above this
    uint16_t inv_redline;    // 64 * 65536 / redline (avoids a division per frame)
    uint8_t  gear_k[NUM_GEARS + 1]; // rpm = speed * k >> 8 (index 0 = neutral, unused)
    uint16_t power;          // force scale
    uint8_t  drag_shift;     // aero drag = mph^2 >> drag_shift
    uint16_t traction;       // max accel per frame (1/256 mph); above -> wheelspin
    uint8_t  free_up;        // rpm/frame gained when declutched with gas
    uint8_t  free_down;      // rpm/frame lost when declutched without gas
    uint8_t  slip;           // rpm/frame the clutch pulls the engine toward wheel rpm
} car_class_t;

typedef struct {
    uint8_t  cls;
    uint8_t  gear;           // 0 = neutral, 1..4
    uint8_t  clutch_in;      // 1 = clutch pedal down (shift key held), drivetrain open
    uint8_t  gas;            // 1 = throttle
    uint8_t  wheelspin;      // set by car_update when traction-limited
    uint8_t  blown;          // engine exploded
    uint8_t  engine_off;     // ignition off: engine stopped (rpm 0)
    uint16_t rpm;
    uint16_t speed;          // 1/256 mph
    uint32_t dist;           // 1/65536 ft
} car_t;

extern const car_class_t car_classes[NUM_CLASSES];

void car_reset(car_t *car, uint8_t cls);
void car_update(car_t *car);     // advance one frame (1/59.73 s)
void car_shift_press(car_t *car);     // clutch in, next gear up
void car_downshift_press(car_t *car); // clutch in, next gear down (1 -> neutral)
void car_shift_release(car_t *car);   // clutch out

#endif
