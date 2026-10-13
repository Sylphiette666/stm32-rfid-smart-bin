#include "devices.h"
#include "platform.h"
#include "storage.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
Settings settings = {1500, 1700, 65, 85, 25, 2700, 2000, 1000, 0, 0, 0, 0};
static uint32_t now, us;
static bool dht_armed, dht_low, trigger;
static uint8_t mcp[256];
static bool fresh_echo;
static uint16_t range_width = 350;
uint32_t millis(void) { return now; }
uint16_t micros16(void) { return (uint16_t)us; }
void delay_us(uint16_t n) { us += n; }
void motor_off(void) {}
void buzzer_output(bool on) { (void)on; }
void trigger_output(bool on) {
    if (on)
        trigger = true;
}
void dht_drive(bool low) { dht_low = low; }
void dht_arm(bool on) { dht_armed = on; }
bool audio_send(const uint8_t *p, uint16_t n) {
    (void)p;
    (void)n;
    return true;
}
void rfid_init(void) {}
bool nor_init(void) { return true; }
bool adc_read(uint8_t ch, uint16_t *v) {
    *v = ch == 1 ? 2100 : 3000;
    return true;
}
uint16_t gpio_b(void) { return 0; }
bool i2c_write(uint8_t a, const uint8_t *p, uint16_t n) {
    if (a == 0x20 && n == 2)
        mcp[p[0]] = p[1];
    return true;
}
bool i2c_read_reg(uint8_t a, uint8_t r, uint8_t *p, uint16_t n) {
    memset(p, 0, n);
    if (a == 0x20) {
        memcpy(p, mcp + r, n);
        return true;
    }
    if (r == 0x75)
        *p = 0x68;
    else if (r == 0x3b) {
        assert(n == 6);
        p[4] = 0x40;
    }
    return true;
}
static void step(unsigned n, bool maintenance) {
    while (n--) {
        now++;
        us += 1000;
        devices_step(false, true, true, maintenance);
        if (trigger) {
            trigger = false;
            if (fresh_echo) {
                sensor_edge_irq(1, true, (uint16_t)(us + 100));
                sensor_edge_irq(1, false, (uint16_t)(us + 100 + range_width));
            }
        }
    }
}
static void wait_dht(void) {
    for (unsigned i = 0; i < 4000 && !dht_armed; i++)
        step(1, false);
    assert(dht_armed && !dht_low);
}
static void edge(bool high, unsigned width) {
    us += width;
    sensor_edge_irq(11, high, (uint16_t)us);
}
static void frame(bool good) {
    uint8_t b[5] = {55, 0, 24, 0, 79};
    if (!good)
        b[4]++; /* Force a timer wrap during the frame. */
    us = (us & ~65535u) + 65500;
    edge(false, 20);
    edge(true, 80);
    edge(false, 80);
    for (unsigned k = 0; k < 40; k++) {
        edge(true, 50);
        edge(false, (b[k / 8] & (0x80 >> (k % 8))) ? 70 : 26);
    }
    assert(!dht_armed);
    devices_step(false, true, true, false);
}
int main(void) {
    devices_init();
    assert(dev.mcp && dev.mpu && dev.oled);
    assert(mcp[0] == 0x40 && mcp[1] == 0x7f && (mcp[0x14] & 0x10));
    assert(mcp_update(0x20, 0x20));
    assert(mcp_direction(5));
    assert((mcp[0x14] & 0x3f) == 0x35);
    wait_dht();
    frame(true);
    assert(dev.dht_valid && dev.humidity10 == 550 && dev.temp10 == 240);
    wait_dht();
    frame(false);
    assert(!dev.dht_valid);
    wait_dht();
    edge(false, 20);
    edge(true, 10);
    assert(!dht_armed);
    devices_step(false, true, true, false);
    assert(!dev.dht_valid);
    wait_dht();
    sensor_abort_irq();
    assert(!dht_armed && !dht_low);
    devices_step(false, true, true, false);
    assert(dev.full_unknown);
    fresh_echo = true;
    step(1800, false);
    assert(dev.range_valid && !dev.full_unknown && dev.full && dev.range_mm >= 59 &&
           dev.range_mm <= 61);
    range_width = 600;
    step(1800, false);
    assert(dev.full);
    step(800, true);
    assert(!dev.full);
    fresh_echo = false;
    step(1500, false);
    assert(dev.full_unknown && !dev.range_valid);
    mcp[0] = 255;
    step(80, false);
    assert(!dev.mcp);
    puts("PASS sensors: MCP output preservation/reset detection, DHT checksum/edge timing/16-bit "
         "wrap/abort, ultrasonic median/hysteresis/maintenance clear/no-echo unknown");
    return 0;
}
