#include "app.h"
#include "devices.h"
#include "storage.h"
#include "platform.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
App app;
static volatile uint32_t heartbeat, beam_change, beam_duration, beam_event;
static volatile bool beam_blocked;
static uint32_t beam_seen, loop_at, control_at, command_at, stopped_at, lid_at, lid_clear_at,
    tilt_at, low_at, obstacle_at, closed_at, line_lost_at, marker_at, marker_clear_at;
static bool tilt_pending, low_pending, obstacle_pending, closed_prev, marker_locked, line_lost,
    marker_pending, marker_clear, boot_submitted, boot_complete;
static uint8_t motor_dir = 255;
static uint32_t direction_at;
static uint16_t ramp_l, ramp_r, servo_start, servo_target, session_user;
static bool convenience_session, beam_ready, transaction_sent;
static uint32_t session_at;
static uint32_t announced_faults, fault_sound_at, warning_at;
static bool warning_pending, warning_sent, full_announced;
static int abs_i(int v) { return v < 0 ? -v : v; }
static bool level(uint16_t pins, unsigned bit, bool high) {
    return (((pins >> bit) & 1) != 0) == high;
}
static bool lid_closed(void) { return level(gpio_b(), 14, LID_CLOSED_HIGH); }
void safety_tick_irq(void) {
    uint32_t now = millis();
    if (app.moving && elapsed(now, heartbeat, 10)) {
        motor_off();
        irq_faults |= F_SCHED;
    }
    if (app.moving && app.mode == MODE_MANUAL && elapsed(now, command_at, 300)) {
        motor_off();
        irq_faults |= F_COMMAND;
    }
    bool b = level(gpio_a(), 12, BEAM_ACTIVE_HIGH);
    if (b != beam_blocked) {
        if (!b) {
            beam_duration = now - beam_change;
            beam_event++;
        }
        beam_change = now;
        beam_blocked = b;
    }
}
void app_message(const char *s) {
    serial_send(0, s);
    serial_send(0, "\r\n");
    display_text(6, s);
}
void app_stop(uint32_t fault) {
    motor_off();
    app.left = app.right = 0;
    ramp_l = ramp_r = 0;
    motor_dir = 255;
    if (app.moving)
        stopped_at = millis();
    app.moving = false;
    app.faults |= fault;
    if (app.mode == MODE_LINE)
        app.mode = MODE_DEPOSIT;
}
static uint32_t conditions(void) {
    uint32_t f = 0;
    uint32_t now = millis();
    uint16_t b = gpio_b();
    if (b & BIT(13))
        f |= F_ESTOP;
    if (b & BIT(12))
        f |= F_COLLISION;
    if (!clock_ok)
        f |= F_CLOCK;
    if (!dev.mcp || elapsed(now, dev.mcp_at, 50))
        f |= F_MCP;
    if (!dev.mpu || elapsed(now, dev.mpu_at, 200))
        f |= F_MPU;
    if (!dev.adc_valid || elapsed(now, dev.adc_at, 300))
        f |= F_ADC;
    if (dev.vbat_mv < 7000)
        f |= F_BATTERY;
    if (abs_i(dev.roll10) > 100 || abs_i(dev.pitch10) > 100)
        f |= F_TILT;
    if (level(b, 8, OBSTACLE_ACTIVE_HIGH))
        f |= F_OBSTACLE;
    if (!lid_closed() || !elapsed(now, closed_at, 100))
        f |= F_LID;
    return f;
}
bool app_clear(void) {
    bool held = app.lid == LID_HELD;
    uint32_t f = conditions();
    if (held)
        f &= ~F_LID;
    if (f || (app.lid != LID_IDLE && !held) || !clear_irq_faults())
        return false;
    app_stop(0);
    app.faults = held ? F_LID : 0;
    return true;
}
bool app_arm(void) {
    if (!clock_ok || !dev.mcp || !dev.adc_valid || dev.vbat_mv < 7000 ||
        (gpio_b() & (BIT(12) | BIT(13))) || irq_faults || app.faults || app.moving || app.left ||
        app.right)
        return false;
    app.armed = true;
    return true;
}
static bool can_move(void) {
    uint32_t current = conditions();
    /* Start/recovery requires <10 degrees and >=7.0 V; moving uses the
       independently timed 18-degree / 6.6 V stop policies in safety_step. */
    if (app.moving)
        current &= F_ESTOP | F_COLLISION | F_CLOCK | F_MCP | F_MPU | F_ADC | F_LID;
    return app.armed && settings.calibrated && boot_complete && !app.faults && !irq_faults &&
           !current && app.lid == LID_IDLE && app.mode != MODE_MAINTENANCE && !dev.full_unknown &&
           store_state == STORE_READY;
}
bool app_motion(int l, int r) {
    if (!can_move() || app.mode != MODE_MANUAL || abs_i(l) > settings.pwm_max ||
        abs_i(r) > settings.pwm_max)
        return false;
    app.left = (int16_t)l;
    app.right = (int16_t)r;
    command_at = millis();
    return true;
}
static void safety_step(uint32_t now) {
    uint16_t b = gpio_b();
    bool closed = lid_closed();
    if (closed && !closed_prev)
        closed_at = now;
    closed_prev = closed;
    app.faults |= irq_faults;
    if (!clock_ok)
        app.faults |= F_CLOCK;
    bool tilt = abs_i(dev.roll10) >= 180 || abs_i(dev.pitch10) >= 180;
    if (tilt && !tilt_pending)
        tilt_at = now;
    tilt_pending = tilt;
    if (tilt && elapsed(now, tilt_at, 200))
        app.faults |= F_TILT;
    bool low = dev.adc_valid && dev.vbat_mv <= 6600;
    if (low && !low_pending)
        low_at = now;
    low_pending = low;
    if (low && (dev.vbat_mv <= 6000 || elapsed(now, low_at, 1000)))
        app.faults |= F_BATTERY;
    bool obstacle = level(b, 8, OBSTACLE_ACTIVE_HIGH);
    if (obstacle && !obstacle_pending)
        obstacle_at = now;
    obstacle_pending = obstacle;
    if (obstacle && elapsed(now, obstacle_at, 20) && app.moving)
        app.faults |= F_OBSTACLE;
    if (app.moving) {
        if (!dev.mcp || elapsed(now, dev.mcp_at, 50))
            app.faults |= F_MCP;
        if (!dev.mpu || elapsed(now, dev.mpu_at, 200))
            app.faults |= F_MPU;
        if (!dev.adc_valid || elapsed(now, dev.adc_at, 300))
            app.faults |= F_ADC;
        if (!closed)
            app.faults |= F_LID;
    }
    if (app.lid != LID_IDLE && app.lid != LID_HELD) {
        if (!dev.mcp || elapsed(now, dev.mcp_at, 50))
            app.faults |= F_MCP;
        if (!dev.adc_valid || elapsed(now, dev.adc_at, 300))
            app.faults |= F_ADC;
    }
    if (app.faults) {
        app_stop(0);
        if (app.lid != LID_IDLE && app.lid != LID_HELD) {
            servo_output(0);
            app.lid = LID_HELD;
            app_message("LID HELD: inspect, use CLOSE");
        }
    }
    if (app.faults && (app.faults != announced_faults || elapsed(now, fault_sound_at, 5000))) {
        announced_faults = app.faults;
        fault_sound_at = now;
        beep(3);
        audio_queue(5, true);
    }
    if (!app.faults)
        announced_faults = 0;
    bool warning = dev.adc_valid && dev.vbat_mv <= 7000;
    if (warning && !warning_pending)
        warning_at = now;
    warning_pending = warning;
    if (!warning)
        warning_sent = false;
    if (warning && !warning_sent && elapsed(now, warning_at, 3000)) {
        warning_sent = true;
        app_message("LOW BATTERY");
        audio_queue(6, false);
    }
    if (dev.full && !full_announced) {
        app_message("BIN FULL");
        audio_queue(4, false);
    }
    full_announced = dev.full;
}
static uint16_t ramp(uint16_t v, uint16_t target) {
    return v < target ? (uint16_t)(v + 1) : v > target ? (uint16_t)(v - 1) : v;
}
static void motion_step(uint32_t now) {
    if (app.mode == MODE_MANUAL && (app.left || app.right) && elapsed(now, command_at, 300)) {
        app_stop(F_COMMAND);
        return;
    }
    if (!app.left && !app.right) {
        if (app.moving)
            app_stop(0);
        return;
    }
    if (!can_move()) {
        app_stop(F_COMMAND);
        return;
    }
    int l = MOTOR_LEFT_INVERT ? -app.left : app.left,
        r = MOTOR_RIGHT_INVERT ? -app.right : app.right;
    uint8_t d = (uint8_t)((l > 0 ? 1 : l < 0 ? 2 : 0) | (r > 0 ? 4 : r < 0 ? 8 : 0));
    if (d != motor_dir) {
        motor_off();
        ramp_l = ramp_r = 0;
        if (!mcp_direction(d)) {
            app_stop(F_MCP);
            return;
        }
        motor_dir = d;
        direction_at = now;
    }
    if (!elapsed(now, direction_at, 100))
        return;
    ramp_l = ramp(ramp_l, (uint16_t)abs_i(l));
    ramp_r = ramp(ramp_r, (uint16_t)abs_i(r));
    if (!motor_output(ramp_l, ramp_r)) {
        app_stop(irq_faults ? irq_faults : F_COMMAND);
        return;
    }
    app.moving = true;
}
static void line_step(uint32_t now) {
    if (app.mode != MODE_LINE)
        return;
    if (!can_move()) {
        app_stop(F_LINE);
        return;
    }
    uint8_t raw = dev.mcp_b & 7;
    uint8_t v = LINE_ACTIVE_HIGH ? raw : (raw ^ 7); /* bit0=L, bit1=C, bit2=R */
    if (v == 0) {
        if (!line_lost)
            line_lost_at = now;
        line_lost = true;
        if (elapsed(now, line_lost_at, 50))
            app_stop(F_LINE);
        return;
    }
    line_lost = false;
    if (v == 5) {
        app_stop(F_LINE);
        return;
    }
    if (v == 7) {
        if (!marker_pending)
            marker_at = now;
        marker_pending = true;
        marker_clear = false;
        if (!marker_locked && elapsed(now, marker_at, 80)) {
            marker_locked = true;
            app.stations++;
            if (app.stations >= app.target) {
                app_stop(0);
                app.mode = MODE_DEPOSIT;
                app_message("ARRIVED");
                return;
            }
        }
    } else {
        marker_pending = false;
        if (v == 2) {
            if (!marker_clear)
                marker_clear_at = now;
            marker_clear = true;
            if (elapsed(now, marker_clear_at, 300))
                marker_locked = false;
        } else
            marker_clear = false;
    }
    int base = settings.pwm_max > 25 ? 25 : settings.pwm_max;
    int slow = base > 10 ? base - 10 : 0;
    app.left = (int16_t)((v == 1 || v == 3) ? slow : base);
    app.right = (int16_t)((v == 4 || v == 6) ? slow : base);
}
static void lid_begin(uint16_t target, uint8_t state) {
    servo_start = app.servo ? app.servo : settings.close_us;
    servo_target = target;
    lid_at = millis();
    app.lid = state;
}
bool app_open(uint16_t id, bool convenience) {
    bool maintenance = app.mode == MODE_MAINTENANCE && app_admin();
    if (!app.armed || !settings.calibrated || !boot_complete || app.moving || app.left ||
        app.right || !elapsed(millis(), stopped_at, 500) || app.faults || irq_faults || !dev.mcp ||
        !dev.adc_valid || dev.vbat_mv < 7000 ||
        (!maintenance && (dev.full || dev.full_unknown || !dev.range_valid ||
                          elapsed(millis(), dev.range_at, 2000))) ||
        store_state != STORE_READY || app.lid != LID_IDLE || !lid_closed())
        return false;
    if (!convenience) {
        User *u = user_id(id);
        if (!u || u->status != USER_ACTIVE || u->points >= POINTS_MAX || u->count == UINT32_MAX ||
            !dev.rfid)
            return false;
    }
    session_user = id;
    convenience_session = convenience;
    transaction_sent = false;
    beam_ready = false;
    beam_seen = beam_event;
    lid_clear_at = millis();
    lid_begin(settings.open_us, LID_OPENING);
    audio_queue(2, false);
    return true;
}
static void lid_step(uint32_t now) {
    switch (app.lid) {
    case LID_IDLE: {
        static uint32_t near_at;
        static bool near_pending;
        bool near = level(dev.mcp_b, 3, NEAR_ACTIVE_HIGH);
        if (near && !near_pending)
            near_at = now;
        near_pending = near;
        if (app.mode == MODE_CONVENIENCE && near && elapsed(now, near_at, 300))
            app_open(0, true);
        break;
    }
    case LID_OPENING:
    case LID_CLOSING: {
        uint32_t dt = now - lid_at;
        if (dt > 1200)
            dt = 1200;
        app.servo = (uint16_t)((int32_t)servo_start +
                               ((int32_t)servo_target - servo_start) * (int32_t)dt / 1200);
        servo_output(app.servo);
        if (app.lid == LID_OPENING && dt == 1200) {
            app.lid = LID_WAIT;
            session_at = now;
            lid_clear_at = now;
            beam_seen = beam_event;
        } else if (app.lid == LID_CLOSING) {
            if (beam_blocked) {
                servo_output(0);
                app.lid = LID_HELD;
                app_message("BEAM BLOCKED / LID HELD");
            } else if (dt == 1200 && lid_closed() && elapsed(now, closed_at, 100)) {
                app.lid = LID_IDLE;
                servo_output(0);
                stopped_at = now;
            } else if (elapsed(now, lid_at, 2200)) {
                app.faults |= F_LID;
                servo_output(0);
                app.lid = LID_HELD;
            }
        }
        break;
    }
    case LID_WAIT:
        if (app.mode == MODE_MAINTENANCE)
            break;
        if (convenience_session) {
            if (level(dev.mcp_b, 3, NEAR_ACTIVE_HIGH) || beam_blocked)
                lid_clear_at = now;
            else if (elapsed(now, lid_clear_at, 2000)) {
                lid_begin(settings.close_us, LID_CLOSING);
            }
            break;
        }
        if (!beam_ready) {
            if (beam_blocked)
                lid_clear_at = now;
            else if (elapsed(now, lid_clear_at, 200)) {
                beam_ready = true;
                beam_seen = beam_event;
            }
        } else if (beam_event != beam_seen) {
            beam_seen = beam_event;
            uint32_t duration = beam_duration;
            if (duration >= 30 && duration <= 2000) {
                app.lid = LID_BLOCK;
                lid_clear_at = now;
            }
        }
        if (beam_blocked && elapsed(now, beam_change, 2000)) {
            app.lid = LID_HELD;
            app_message("BLOCKED: CLEAR THEN CLOSE");
        } else if (elapsed(now, session_at, 10000) && !beam_blocked) {
            app.lid = LID_DELAY;
            lid_at = now;
            app_message("NO DEPOSIT");
        }
        break;
    case LID_BLOCK:
        if (beam_blocked) {
            app.lid = LID_WAIT;
            break;
        }
        if (elapsed(now, lid_clear_at, 100)) {
            Transaction t = {0};
            t.type = TX_DEPOSIT;
            t.id = session_user;
            t.delta = 1;
            if (!transaction_sent && storage_begin(&t)) {
                transaction_sent = true;
                app.lid = LID_COMMIT;
            } else {
                app.lid = LID_HELD;
                app_message("ERR STORAGE / NO CREDIT");
            }
        }
        break;
    case LID_COMMIT:
        break;
    case LID_DELAY:
        if (beam_blocked)
            lid_at = now;
        else if (elapsed(now, lid_at, 2000))
            lid_begin(settings.close_us, LID_CLOSING);
        break;
    case LID_HELD:
        break;
    default:
        break;
    }
}
void app_init(void) {
    memset(&app, 0, sizeof(app));
    app.mode = MODE_DEPOSIT;
    app.servo = 0;
    heartbeat = millis();
    loop_at = millis();
    beam_change = millis();
    beam_blocked = level(gpio_a(), 12, BEAM_ACTIVE_HIGH);
    stopped_at = millis();
    motor_off();
    servo_output(0);
    app_message("BOOT A1 " FW_VERSION " / DISARMED");
    char s[80];
    snprintf(s, sizeof(s), "RESET_FLAGS %08lX CLOCK %s\r\n", (unsigned long)reset_cause,
             clock_ok ? "72MHz" : "FAIL");
    serial_send(0, s);
}
void app_step(void) {
    uint32_t now = millis();
    heartbeat = now;
    uint32_t dt = now - loop_at;
    if (dt * 1000 > app.max_loop_us)
        app.max_loop_us = dt * 1000;
    loop_at = now;
    safety_step(now);
    bool storage_idle = !app.moving && !app.left && !app.right &&
                        (app.lid == LID_IDLE || app.lid == LID_COMMIT || app.lid == LID_HELD);
    storage_step(storage_idle);
    if (store_state == STORE_READY && !boot_submitted) {
        Transaction t = {0};
        t.type = TX_BOOT;
        if (storage_begin(&t))
            boot_submitted = true;
    }
    bool ok;
    if (storage_done(&ok)) {
        if (boot_submitted && !boot_complete) {
            boot_complete = ok;
            if (!ok)
                app_message("ERR BOOT STORAGE");
        } else if (app.lid == LID_COMMIT) {
            if (ok) {
                beep(2);
                audio_queue(3, false);
                app_message("DEPOSIT +1 COMMITTED");
                app.lid = LID_DELAY;
                lid_at = now;
            } else {
                app.lid = LID_HELD;
                app_message("ERR DEPOSIT STORAGE");
            }
        } else
            app_transaction_result(ok);
    }
    if (elapsed(now, control_at, 10)) {
        control_at = now;
        line_step(now);
        motion_step(now);
    }
    devices_step(app.moving, lid_closed(), app.lid == LID_IDLE, app.mode == MODE_MAINTENANCE);
    rfid_step();
    Uid uid;
    if (rfid_event(&uid))
        app_card(&uid);
    lid_step(now);
    app_ui_step();
    char line[128];
    for (unsigned port = 0; port < 2; port++)
        if (serial_line((uint8_t)port, line, sizeof(line)))
            app_command((uint8_t)port, line);
    if (!app.moving || (!irq_faults && elapsed(now, dev.mcp_at, 50) == false &&
                        elapsed(now, dev.mpu_at, 200) == false))
        watchdog_feed();
}
/* Explicit bench-only operations are called by the authenticated console. */
bool app_line_start(unsigned target) {
    if (target < 1 || target > 2 || app.moving || !can_move())
        return false;
    app.mode = MODE_LINE;
    app.stations = 0;
    app.target = (uint8_t)target;
    marker_locked = marker_pending = marker_clear = line_lost = false;
    return true;
}
bool app_close(void) {
    if (app.moving || beam_blocked || !app.armed || !settings.calibrated || irq_faults ||
        !dev.mcp || !dev.adc_valid || dev.vbat_mv < 7000)
        return false;
    if (app.faults & ~F_LID)
        return false;
    app.faults &= ~F_LID;
    lid_begin(settings.close_us, LID_CLOSING);
    return true;
}
bool app_servo_test(unsigned pulse) {
    if (!app.armed || app.moving || app.left || app.right || irq_faults || !dev.mcp ||
        !dev.adc_valid || dev.vbat_mv < 7000 || pulse < 900 || pulse > 2100)
        return false;
    if ((!app.servo && pulse != 1500) || (app.servo && abs_i((int)pulse - app.servo) > 20))
        return false;
    app.servo = (uint16_t)pulse;
    servo_output(app.servo);
    app.lid = LID_HELD;
    return true;
}
