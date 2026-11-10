#include "physics.h"

// Tuned with tools/sim.c (make sim). Red lines follow the 1980 class layout.
const car_class_t car_classes[NUM_CLASSES] = {
    //  name         redline inv   gear_k (N,1,2,3,4)      pow drag trac  up  dn slip
    { "STOCK",       6999u, 599u, { 0, 170, 115, 84, 64 },   88, 11,   55, 110,  90,  60 },
    { "MODIFIED",    8999u, 466u, { 0, 165, 115, 86, 66 },  140, 12,   85, 140, 100,  80 },
    { "FUNNY CAR",   9999u, 419u, { 0, 110,  78, 56, 42 },  600, 13,  235, 220, 120, 120 },
    { "TOP FUEL",    8999u, 466u, { 0,  95,  66, 48, 35 },  900, 13,  285, 240, 130, 130 },
};

// Normalized torque (0..255) vs rpm/redline, 17 points at 1/16 steps.
static const uint8_t torque_curve[17] = {
    150, 160, 172, 185, 198, 210, 222, 232, 241, 248, 253, 255, 253, 248, 240, 228, 212
};

static uint8_t torque_at(uint16_t rpm, uint16_t inv_redline) {
    // 0..64 = 0..redline; 16-bit only: (rpm/128) * (64*65536/redline) / 512
    uint16_t frac = (uint16_t)(((rpm >> 7) * inv_redline) >> 9);
    uint8_t i, f;
    if (frac >= 64u) return torque_curve[16];
    i = (uint8_t)(frac >> 2);
    f = (uint8_t)(frac & 3u);
    return (uint8_t)(torque_curve[i] +
           (((int16_t)torque_curve[i + 1] - (int16_t)torque_curve[i]) * f) / 4);
}

void car_reset(car_t *car, uint8_t cls) {
    car->cls = cls;
    car->gear = 0;
    car->clutch_in = 0;
    car->gas = 0;
    car->wheelspin = 0;
    car->blown = 0;
    car->engine_off = 0;
    car->rpm = IDLE_RPM;
    car->speed = 0;
    car->dist = 0;
}

void car_shift_press(car_t *car) {
    if (car->blown) return;
    if (car->gear < NUM_GEARS) car->gear++;
    car->clutch_in = 1;
}

void car_downshift_press(car_t *car) {
    if (car->blown) return;
    if (car->gear > 0) car->gear--;
    car->clutch_in = 1;
}

void car_shift_release(car_t *car) {
    car->clutch_in = 0;
}

static uint16_t sub_floor(uint16_t v, uint16_t d, uint16_t floor) {
    return (v > floor + d) ? (uint16_t)(v - d) : floor;
}

void car_update(car_t *car) {
    const car_class_t *c = &car_classes[car->cls];
    uint16_t mph = MPH(car->speed);
    int16_t accel;
    int16_t drag = (int16_t)(((uint16_t)mph * mph) >> c->drag_shift);
    if (car->speed) drag += 1;  // rolling resistance

    car->wheelspin = 0;

    if (car->blown) {
        car->rpm = sub_floor(car->rpm, 150, 0);
        accel = -drag - 8;
    } else if (car->engine_off) {
        car->rpm = 0;                             // ignition off: engine stopped
        accel = -drag;
    } else if (car->gear == 0 || car->clutch_in) {
        // Drivetrain open: engine revs freely, car coasts.
        if (car->gas) car->rpm += c->free_up;
        else          car->rpm = sub_floor(car->rpm, c->free_down, IDLE_RPM);
        accel = -drag;
    } else {
        uint8_t k = c->gear_k[car->gear];
        uint16_t wheel = (uint16_t)(((uint32_t)car->speed * k) >> 8);
        uint16_t floor = wheel > IDLE_RPM ? wheel : IDLE_RPM;
        int16_t force;

        // Clutch slip: the engine is pulled down toward wheel speed.
        if (car->rpm > floor) {
            car->rpm = sub_floor(car->rpm, car->gas ? c->slip : (uint16_t)c->slip * 2u, floor);
        } else {
            car->rpm = floor;  // engine dragged up by the wheels (or idling with slip)
        }

        if (car->gas) {
            force = (int16_t)(((uint32_t)torque_at(car->rpm, c->inv_redline) * k * c->power) >> 16);
            if (force > (int16_t)c->traction) {
                force = (int16_t)c->traction;
                car->wheelspin = 1;
            }
        } else {
            force = -(int16_t)(k >> 4);  // engine braking
        }
        accel = force - drag;
    }

    if (accel < 0 && (uint16_t)(-accel) > car->speed) car->speed = 0;
    else if (accel > 0 && car->speed > (uint16_t)(65000u - (uint16_t)accel)) car->speed = 65000u;
    else car->speed = (uint16_t)(car->speed + accel);

    // ft/frame = mph * 1.46667 / 59.7275; in our units: speed * 1609 >> 8
    car->dist += ((uint32_t)car->speed * 1609u) >> 8;

    if (car->rpm > c->redline) car->blown = 1;
}
