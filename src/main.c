// Pocket Dragster - a drag racer for the original Game Boy.
//
// Flow:     class select (engine off) -> START -> A starts the engine ->
//           countdown -> race.
// Controls: A = gas, UP / DOWN = clutch in + shift up / down (hold = clutch in),
//           START = stage / retry, SELECT = class (when idle).

#include <gb/gb.h>
#include <gb/hardware.h>
#include "physics.h"
#include "display.h"
#include "sound.h"
#include "title.h"

enum { ST_IDLE, ST_STAGE, ST_RACE, ST_FINISH, ST_FOUL, ST_BLOWN,
       ST_IGNITION,   // staged, waiting for A to start the engine
       ST_CRANK };    // starter running

#define AMBER_FRAMES   30u   // 0.5 s per amber lamp
#define MIN_WAIT       40u   // frames before START is accepted after a run
#define SHIFT_KEYS     (J_UP | J_DOWN)

static car_t car;
static uint8_t state, cls, keys, prev, pressed, released, frame;
static uint16_t timer;        // frames since entering the state
static uint16_t race_frames;  // frames since green
static uint16_t race_hund;    // hundredths since green (for the live display)
static uint16_t finish_kmh;   // trap speed, held on the speedometer after the finish
static uint16_t finish_rpm;   // rpm at the line, held on the tach after the finish
static uint16_t hund_frac;    // fractional hundredths, 1/65536 units
static uint16_t stage_delay;  // random wait before first amber
static uint16_t rt_frames;    // reaction time: green -> clutch out
static uint8_t launched;
static uint8_t lamps;
static uint8_t shake;

// Best time per class this session (not saved), hundredths, 0 = none.
// Only used for the "NEW BEST!" message.
static uint16_t best_et[NUM_CLASSES];

static uint16_t frames_to_hundredths(uint16_t f) {
    return (uint16_t)(((uint32_t)f * 6857u) >> 12);   // 100 / 59.7275
}

static void set_lamps(uint8_t mask) {
    if (mask != lamps) { lamps = mask; display_lamps(mask); }
}

// Rev flare when the engine catches, per class.
static const uint16_t catch_rpm[NUM_CLASSES] = { 2200u, 2800u, 3600u, 3600u };

static void enter_idle(void) {
    state = ST_IDLE;
    timer = 0;
    car_reset(&car, cls);
    car.engine_off = 1;     // class selection: car parked, engine off
    set_lamps(0);
    shake = 0;
    display_shake(0);
    display_class(cls);
    display_time(0);
    display_msg("START: STAGE", "SELECT: CLASS");
}

static void enter_ignition(void) {
    state = ST_IGNITION;
    timer = 0;
    car_reset(&car, cls);
    car.engine_off = 1;
    display_time(0);
    display_msg("PRESS A TO START", "THE ENGINE");
}

static void enter_crank(void) {
    state = ST_CRANK;
    timer = 0;
    display_msg("STARTING...", 0);
}

// Engine is running: the countdown begins.
static void enter_stage(void) {
    state = ST_STAGE;
    timer = 0;
    race_frames = 0;
    launched = 0;
    stage_delay = 40u + (DIV_REG & 63u);
    car.engine_off = 0;
    car.rpm = catch_rpm[cls];   // settles to idle on its own
    if (keys & J_UP) car_shift_press(&car);   // UP already held: clutch in, 1st
    display_msg("HOLD UP = 1ST GEAR", "REV A, RELEASE UP");
}

static void enter_foul(void) {
    state = ST_FOUL;
    timer = 0;
    set_lamps(LAMP_RED);
    sound_beep(0);
    display_msg("FOUL! RED LIGHT", "START: RETRY");
}

static void enter_blown(void) {
    state = ST_BLOWN;
    timer = 0;
    shake = 16;
    sound_boom();
    display_msg("ENGINE BLOWN!", "START: RETRY");
}

static void enter_finish(void) {
    char l1[21], l2[21], buf[6];
    uint16_t et = frames_to_hundredths(race_frames);
    uint16_t kmh = KMH(car.speed);
    finish_kmh = kmh;
    finish_rpm = car.rpm;
    uint8_t best = 0;

    state = ST_FINISH;
    timer = 0;
    // Photo finish: freeze the car on the line and switch the engine off.
    car.gas = 0;
    car.clutch_in = 1;
    car.engine_off = 1;
    car.speed = 0;
    car.dist = QUARTER_MILE;

    if (!best_et[cls] || et < best_et[cls]) {
        best_et[cls] = et;
        best = 1;
    }

    // "ET 14.45  159 KM/H"
    fmt_time(buf, et);
    l1[0] = 'E'; l1[1] = 'T'; l1[2] = ' ';
    l1[3] = buf[0]; l1[4] = buf[1]; l1[5] = buf[2]; l1[6] = buf[3]; l1[7] = buf[4];
    l1[8] = ' '; l1[9] = ' ';
    fmt_uint(l1 + 10, kmh, 3);
    l1[13] = ' '; l1[14] = 'K'; l1[15] = 'M'; l1[16] = '/'; l1[17] = 'H'; l1[18] = 0;

    // "RT 0.42  NEW BEST!"
    fmt_time(buf, frames_to_hundredths(rt_frames));
    l2[0] = 'R'; l2[1] = 'T'; l2[2] = ' ';
    l2[3] = buf[1]; l2[4] = buf[2]; l2[5] = buf[3]; l2[6] = buf[4];
    if (best) {
        const char *s = "  NEW BEST!";
        uint8_t i = 7;
        while (*s) l2[i++] = *s++;
        l2[i] = 0;
    } else {
        l2[7] = 0;
    }
    display_msg(l1, l2);
    display_time(et);   // exact value; the live counter is an approximation
    display_class(cls);
}

static void update_tree(void) {
    uint16_t t = timer;
    uint8_t mask = 0, n;
    if (t < stage_delay) return;
    t -= stage_delay;
    n = (uint8_t)(t / AMBER_FRAMES) + 1u;      // ambers lit so far
    if (n > 5u) {
        // Green!
        set_lamps(LAMP_GREEN);
        sound_beep(1);
        display_msg("GO!", "UP/DOWN = SHIFT");
        state = ST_RACE;
        race_frames = 0;
        race_hund = 0;
        hund_frac = 0;
        return;
    }
    while (n--) mask |= LAMP_AMBER(n);
    if (mask != lamps) sound_beep(0);
    set_lamps(mask);
}

static void handle_drive_input(void) {
    car.gas = (keys & J_A) ? 1u : 0u;

    if (pressed & J_UP) {
        // While staged only neutral -> 1st is allowed (clutch held until green).
        if (!(state == ST_STAGE && car.gear)) car_shift_press(&car);
    } else if (pressed & J_DOWN) {
        car_downshift_press(&car);
    }
    // Clutch comes out when no shift key is held any more.
    if ((released & SHIFT_KEYS) && !(keys & SHIFT_KEYS) && car.clutch_in) {
        if (state == ST_STAGE && car.gear) {
            enter_foul();                                    // jumped the start
            return;
        }
        car_shift_release(&car);
        if (!launched && car.gear) {
            launched = 1;
            rt_frames = race_frames;
        }
    }
}

static void render(void) {
    const car_class_t *c = &car_classes[cls];
    // Photo finish: both gauges freeze on their values at the line.
    if (state == ST_FINISH) display_gauges(finish_rpm, finish_kmh);
    else display_gauges(car.rpm, KMH(car.speed));
    display_gear(car.gear);
    display_shift_light(!car.blown &&
        (state == ST_FINISH ? finish_rpm : car.rpm) >= c->redline - (c->redline >> 4));
    display_car(car.dist, car.wheelspin, frame);
    if (state == ST_RACE) display_time(race_hund);
    if (shake) {
        display_shake((frame & 2u) ? (int8_t)(shake >> 2) : -(int8_t)(shake >> 2));
        if (frame & 1u) shake--;
        if (!shake) display_shake(0);
    }
    if (state == ST_FINISH) set_lamps((frame & 16u) ? LAMP_GREEN : 0);
}

void main(void) {
    title_run();
    display_init();
    sound_init();
    for (cls = 0; cls < NUM_CLASSES; cls++) { best_et[cls] = 0; }
    cls = 0;
    enter_idle();

    while (1) {
        vsync();
        render();

        prev = keys;
        keys = joypad();
        pressed = keys & (uint8_t)~prev;
        released = prev & (uint8_t)~keys;
        frame++;
        timer++;

        switch (state) {
        case ST_IDLE:
            if (pressed & J_SELECT) {
                cls = (uint8_t)((cls + 1u) & 3u);
                enter_idle();
            } else if (pressed & J_START) {
                enter_ignition();
            }
            break;
        case ST_IGNITION:
            if (pressed & J_A) enter_crank();
            else if (pressed & J_START) enter_idle();
            break;
        case ST_CRANK:
            if (sound_crank(cls, (uint8_t)(timer - 1u))) enter_stage();
            break;
        case ST_STAGE:
            handle_drive_input();
            if (state == ST_STAGE) update_tree();
            break;
        case ST_RACE:
            race_frames++;
            // +1.674271 hundredths per frame (100 / 59.7275), without multiplying
            race_hund++;
            hund_frac += 44189u;
            if (hund_frac < 44189u) race_hund++;
            handle_drive_input();
            if (pressed & J_START) enter_idle();
            break;
        default:   // FINISH, FOUL, BLOWN
            if (state == ST_FOUL) car.gas = (keys & J_A) ? 1u : 0u;
            if ((pressed & J_START) && timer > MIN_WAIT) enter_idle();
            break;
        }

        car_update(&car);
        // Starter turning the engine over: tach twitches with each stroke.
        if (state == ST_CRANK) car.rpm = sound_crank_phase(cls, (uint8_t)(timer - 1u)) ? 350u : 150u;

        if (car.blown && state != ST_BLOWN) enter_blown();
        if (state == ST_RACE && car.dist >= QUARTER_MILE) enter_finish();

        sound_engine((car.blown || car.engine_off) ? 0u : car.rpm);
        sound_squeal(state == ST_RACE && car.wheelspin);
        sound_update();
    }
}
