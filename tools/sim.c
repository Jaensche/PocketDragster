// Host-side tuning harness for src/physics.c.
// Build & run: make sim
// For each class, grid-searches launch rpm and shift rpm with a simple
// driver (lift + tap clutch for SHIFT_FRAMES) and reports the best ET/trap.

#include <stdio.h>
#include "../src/physics.h"

#define FPS 59.7275
#define MAX_FRAMES (60 * 40)

typedef struct { int ok; double et, mph; int frames60, spin_frames; } result_t;

static result_t run(uint8_t cls, uint16_t launch_rpm, uint16_t shift_rpm,
                    int shift_frames, int verbose) {
    car_t car;
    result_t r = {0};
    int f, shifting = 0;
    car_reset(&car, cls);

    // Staged: clutch in, 1st gear, rev to launch rpm (feathering).
    car_shift_press(&car);
    for (f = 0; f < 120; f++) {
        car.gas = car.rpm < launch_rpm;
        car_update(&car);
        if (car.blown) return r;
    }
    car.gas = 1;
    car_shift_release(&car);

    for (f = 0; f < MAX_FRAMES; f++) {
        if (shifting) {
            if (--shifting == 0) { car_shift_release(&car); car.gas = 1; }
        } else if (car.gear < NUM_GEARS && car.rpm >= shift_rpm) {
            car.gas = 0;
            car_shift_press(&car);
            shifting = shift_frames;
        }
        car_update(&car);
        if (car.wheelspin) r.spin_frames++;
        if (verbose && f % 30 == 0)
            printf("  t=%5.2f g=%d rpm=%5u mph=%3u ft=%4lu%s\n", f / FPS, car.gear, car.rpm,
                   MPH(car.speed), (unsigned long)(car.dist >> 16), car.wheelspin ? " SPIN" : "");
        if (car.blown) return r;
        if (MPH(car.speed) >= 60 && !r.frames60) r.frames60 = f;
        if (car.dist >= QUARTER_MILE) {
            r.ok = 1;
            r.et = (f + 1) / FPS;
            r.mph = car.speed / 256.0;
            return r;
        }
    }
    return r;
}

int main(void) {
    uint8_t cls;
    for (cls = 0; cls < NUM_CLASSES; cls++) {
        const car_class_t *c = &car_classes[cls];
        result_t best = {0};
        uint16_t bl = 0, bs = 0, l, s;
        for (l = 1500; l <= c->redline; l += 250)
            for (s = 3000; s <= c->redline; s += 100) {
                result_t r = run(cls, l, s, 4, 0);
                if (r.ok && (!best.ok || r.et < best.et)) { best = r; bl = l; bs = s; }
            }
        printf("%-10s redline %5u | best ET %6.2f s @ %5.1f mph | launch %5u shift %5u | 0-60 %.2f s | spin %d fr\n",
               c->name, c->redline, best.et, best.mph, bl, bs, best.frames60 / FPS, best.spin_frames);
        {   // sensitivity: sloppy driving
            result_t a = run(cls, 2000, bs, 4, 0);
            result_t b = run(cls, bl, (uint16_t)(c->redline * 3 / 4), 4, 0);
            result_t d = run(cls, bl, bs, 12, 0);
            printf("%10s low launch %6.2f | early shift %6.2f | slow shifts %s%6.2f\n", "",
                   a.ok ? a.et : 0, b.ok ? b.et : 0, d.ok ? "" : "BLOWN ", d.ok ? d.et : 0);
        }
    }
    return 0;
}
