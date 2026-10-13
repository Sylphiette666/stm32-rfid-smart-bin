#include "app.h"
#include "devices.h"
#include "platform.h"
#include "storage.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
Devices dev;
volatile uint32_t irq_faults;
bool clock_ok = true;
uint32_t reset_cause;
static uint32_t now;
static uint16_t pa = BIT(12), pb = BIT(8), pwm_l, pwm_r, servo;
static uint8_t flash[0x13000];
static bool mcp_fail, refresh = true;
uint32_t millis(void) { return now; }
uint16_t gpio_a(void) { return pa; }
uint16_t gpio_b(void) { return pb; }
void motor_off(void) { pwm_l = pwm_r = 0; }
bool motor_output(uint16_t l, uint16_t r) {
    if (irq_faults || (pb & (BIT(12) | BIT(13)))) {
        motor_off();
        return false;
    }
    pwm_l = l;
    pwm_r = r;
    return true;
}
void servo_output(uint16_t n) { servo = n; }
bool clear_irq_faults(void) {
    if (pb & (BIT(12) | BIT(13)))
        return false;
    irq_faults = 0;
    return true;
}
bool serial_send(uint8_t p, const char *s) {
    (void)p;
    (void)s;
    return true;
}
bool serial_line(uint8_t p, char *s, uint16_t n) {
    (void)p;
    (void)s;
    (void)n;
    return false;
}
void watchdog_feed(void) {}
void rfid_step(void) {}
bool rfid_event(Uid *u) {
    (void)u;
    return false;
}
bool rfid_card_test(bool w, const uint8_t d[16]) {
    (void)w;
    (void)d;
    return true;
}
void beep(uint8_t n) { (void)n; }
void audio_queue(uint8_t n, bool p) {
    (void)n;
    (void)p;
}
void display_text(uint8_t row, const char *s) {
    (void)row;
    (void)s;
}
bool mcp_direction(uint8_t v) {
    (void)v;
    if (mcp_fail) {
        dev.mcp = false;
        return false;
    }
    return true;
}
void devices_step(bool moving, bool lid, bool idle, bool maintenance) {
    (void)moving;
    (void)lid;
    (void)idle;
    (void)maintenance;
    if (refresh) {
        dev.mcp_at = dev.mpu_at = dev.adc_at = dev.range_at = now;
    }
}
bool nor_read(uint32_t a, void *p, uint16_t n) {
    assert(a + n <= sizeof(flash));
    memcpy(p, flash + a, n);
    return true;
}
bool nor_program(uint32_t a, const void *p, uint16_t n) {
    assert((a & 255) + n <= 256);
    for (unsigned i = 0; i < n; i++)
        flash[a + i] &= ((const uint8_t *)p)[i];
    return true;
}
bool nor_erase(uint32_t a) {
    memset(flash + a, 255, 4096);
    return true;
}
int nor_poll(void) { return 1; }
static void tick(unsigned ms) {
    while (ms--) {
        now++;
        safety_tick_irq();
        app_step();
    }
}
static void command(unsigned port, const char *s) {
    char b[128];
    strcpy(b, s);
    app_command((uint8_t)port, b);
}
static void commit(Transaction *t) {
    assert(storage_begin(t));
    while (store_state == STORE_BUSY)
        storage_step(true);
    bool ok;
    assert(storage_done(&ok) && ok);
}
int main(void) {
    memset(flash, 255, sizeof(flash));
    dev.nor = true;
    storage_init();
    while (store_state == STORE_LOADING)
        storage_step(true);
    assert(storage_format());
    while (store_state == STORE_BUSY)
        storage_step(true);
    Transaction t = {0};
    t.type = TX_REGISTER;
    t.id = 1;
    t.uid.len = 4;
    t.uid.b[0] = 1;
    t.role = ROLE_ADMIN;
    t.status = USER_ACTIVE;
    commit(&t);
    t.id = 2;
    t.uid.b[0] = 2;
    t.role = ROLE_USER;
    commit(&t);
    t = (Transaction){0};
    t.type = TX_CONFIG;
    settings_defaults(&t.settings);
    t.settings.close_us = 1400;
    t.settings.open_us = 1700;
    t.settings.calibrated = 1;
    commit(&t);
    dev.mcp = dev.mpu = dev.adc_valid = dev.range_valid = dev.rfid = true;
    dev.mcp_b = 0x7f;
    dev.vbat_mv = 7400;
    dev.range_mm = 150;
    app_init();
    tick(700);
    assert(!app.armed && !pwm_l && !pwm_r && !servo);
    command(1, "ARM CONFIRM");
    assert(!app.armed);
    command(0, "ARM CONFIRM");
    assert(app.armed);
    command(0, "MODE MANUAL");
    command(1, "MOVE F 25");
    tick(180);
    assert(pwm_l > 0 && pwm_r > 0);
    tick(130);
    assert(!pwm_l && !pwm_r && (app.faults & F_COMMAND));
    tick(500);
    assert(!pwm_l);
    command(0, "CLEAR");
    assert(app.faults == 0);
    command(1, "MOVE F 25junk");
    tick(150);
    assert(!pwm_l && !pwm_r);
    command(1, "MOVE F 25");
    tick(180);
    assert(pwm_l);
    command(1, "STOP");
    assert(!pwm_l && !pwm_r);
    command(0, "CLEAR");
    tick(100);
    assert(!pwm_l);
    pb |= BIT(13);
    command(1, "MOVE F 25");
    tick(20);
    assert(!pwm_l);
    pb &= ~BIT(13);
    command(0, "CLEAR");
    command(1, "MOVE F 25");
    tick(180);
    refresh = false;
    tick(60);
    assert(!pwm_l && (app.faults & F_MCP));
    refresh = true;
    tick(120);
    command(0, "CLEAR");
    assert(!app.faults);
    mcp_fail = true;
    command(1, "MOVE F 25");
    tick(20);
    assert(!pwm_l && (app.faults & F_MCP));
    mcp_fail = false;
    dev.mcp = true;
    tick(120);
    command(0, "CLEAR");
    command(0, "MODE DEPOSIT");
    tick(600);
    Uid uid = users[1].uid;
    app_card(&uid);
    assert(app.lid == LID_OPENING);
    pb |= BIT(14);
    tick(1450);
    assert(app.lid == LID_WAIT);
    pa &= ~BIT(12);
    tick(50);
    pa |= BIT(12);
    tick(150);
    assert(users[1].points == 1 && users[1].count == 1);
    for (unsigned i = 0; i < 3; i++) {
        pa &= ~BIT(12);
        tick(50);
        pa |= BIT(12);
        tick(120);
    }
    assert(users[1].points == 1);
    tick(2200);
    pb &= ~BIT(14);
    tick(1400);
    assert(app.lid == LID_IDLE);
    app_card(&uid);
    pb |= BIT(14);
    tick(1450);
    pa &= ~BIT(12);
    tick(2200);
    assert(app.lid == LID_HELD && users[1].points == 1);
    pa |= BIT(12);
    tick(200);
    command(0, "CLEAR");
    command(0, "CLOSE");
    assert(app.lid == LID_CLOSING);
    pb &= ~BIT(14);
    tick(1400);
    assert(app.lid == LID_IDLE);
    command(0, "MODE QUERY");
    app_card(&users[0].uid);
    assert(app_admin());
    uint32_t seq = last_seq;
    command(1, "DELETE 2");
    command(1, "CONFIRM");
    tick(50);
    assert(last_seq == seq && users[1].status == USER_ACTIVE);
    command(0, "DELETE 2");
    command(0, "CONFIRM");
    command(0, "CONFIRM");
    tick(100);
    assert(users[1].status == USER_DELETED && last_seq == seq + 1);
    printf("PASS app: boot-disarmed, UART permissions, malformed commands, 300ms timeout, STOP "
           "latch, estop interlock, stale MCP, direction failure, one-credit session, obstruction "
           "hold/close, confirmed admin transaction\n");
    return 0;
}
