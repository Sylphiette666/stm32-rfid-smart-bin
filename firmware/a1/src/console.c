#include "app.h"
#include "devices.h"
#include "storage.h"
#include "platform.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
bool local_setup;
static bool admin_active, register_wait, register_admin, pending_valid, confirm_wait, exporting;
static uint32_t admin_at, setup_at, pending_at, export_at, export_seq, ui_at, button_at, combo_at;
static uint8_t menu, view, export_port, record_page;
static uint16_t export_index, record_scan;
static uint8_t recent[10][64];
static unsigned recent_n;
static Transaction pending;
static Uid last_card;
static uint16_t admin_id;
extern bool app_line_start(unsigned target);
extern bool app_close(void);
extern bool app_servo_test(unsigned pulse);
static const char *const modes[] = {"DEPOSIT", "QUERY",       "MANUAL",
                                    "LINE",    "CONVENIENCE", "MAINTENANCE"};
static const char *const menus[] = {
    "DEPOSIT",        "QUERY",          "MANUAL",    "LINE STATION 1", "LINE STATION 2",
    "CONVENIENCE",    "RECENT RECORDS", "RANKING",   "REGISTER",       "MARK LOST",
    "DELETE USER",    "REDEEM 5",       "REDEEM 10", "MAINTENANCE",    "CARD READ 4",
    "CARD WRITE 4",   "CLEAR FAULT",    "CLOSE LID", "MUTE TOGGLE",    "ARM OUTPUTS",
    "DISARM OUTPUTS", "ENVIRONMENT"};
static bool uid_equal(const Uid *a, const Uid *b) {
    return a->len == b->len && !memcmp(a->b, b->b, a->len);
}
bool app_admin(void) {
    User *u = user_id(admin_id);
    return admin_active && u && u->status == USER_ACTIVE && u->role == ROLE_ADMIN &&
           !elapsed(millis(), admin_at, 60000);
}
void app_admin_touch(void) { admin_at = millis(); }
static bool setup_valid(void) { return local_setup && !elapsed(millis(), setup_at, 60000); }
static void reply(unsigned port, const char *s) {
    serial_send((uint8_t)port, s);
    serial_send((uint8_t)port, "\r\n");
    display_text(6, s);
}
static void show_user(const User *u) {
    char b[100];
    if (!u) {
        app_message("UNKNOWN CARD");
        return;
    }
    snprintf(b, sizeof(b), "USER %u POINTS %lu COUNT %lu STATE %u", u->id, (unsigned long)u->points,
             (unsigned long)u->count, u->status);
    app_message(b);
    app.selected = u->id;
}
void app_card(const Uid *uid) {
    last_card = *uid;
    char s[48];
    unsigned n = 0;
    for (unsigned i = 0; i < uid->len; i++)
        n += (unsigned)snprintf(s + n, sizeof(s) - n, "%02X", uid->b[i]);
    display_text(5, s);
    serial_send(0, "CARD ");
    serial_send(0, s);
    serial_send(0, "\r\n");
    beep(1);
    if (app.moving || app.lid != LID_IDLE) {
        app_message("BUSY CARD IGNORED");
        return;
    }
    User *u = user_uid(uid);
    if (register_wait) {
        if ((register_admin && !setup_valid()) || (!register_admin && !app_admin())) {
            register_wait = false;
            app_message("ERR AUTH EXPIRED");
            return;
        }
        if (u && !register_admin) {
            show_user(u);
            app_message("ALREADY_REGISTERED");
            return;
        }
        memset(&pending, 0, sizeof(pending));
        pending.type = u ? TX_ADMIN_RECOVER : TX_REGISTER;
        pending.id = u ? u->id : storage_next_id();
        pending.uid = *uid;
        pending.role = register_admin ? ROLE_ADMIN : ROLE_USER;
        pending.status = USER_ACTIVE;
        pending_valid = confirm_wait = true;
        pending_at = millis();
        register_wait = false;
        app_message("CONFIRM REGISTER / BACK");
        return;
    }
    if (confirm_wait) {
        pending_valid = confirm_wait = false;
        app_message("PENDING CANCELLED BY CARD");
        return;
    }
    show_user(u);
    if (!u || u->status != USER_ACTIVE)
        return;
    if (u->role == ROLE_ADMIN) {
        admin_active = true;
        admin_id = u->id;
        admin_at = millis();
        app_message("ADMIN AUTH 60 SECONDS");
        return;
    }
    if (app.mode == MODE_DEPOSIT && !app_open(u->id, false))
        app_message("ERR DEPOSIT INTERLOCK");
}
static bool start_pending(Transaction *t) {
    if (app.moving || app.left || app.right ||
        (app.lid != LID_IDLE && !(app.lid == LID_HELD && t->type == TX_CONFIG)) ||
        store_state != STORE_READY || exporting || pending_valid)
        return false;
    if (t->type == TX_CONFIG)
        servo_output(0);
    pending = *t;
    pending_valid = confirm_wait = true;
    pending_at = millis();
    app_message("CONFIRM / BACK CANCEL");
    return true;
}
static bool change_mode(unsigned mode) {
    if (mode > MODE_MAINTENANCE || app.moving || app.left || app.right || app.lid != LID_IDLE ||
        exporting)
        return false;
    if (mode == MODE_MAINTENANCE && !app_admin())
        return false;
    app.mode = (uint8_t)mode;
    app_stop(0);
    view = 0;
    return true;
}
static void prepare_redeem(int cost) {
    User *u = user_id(app.selected);
    if (!u || u->status != USER_ACTIVE || !uid_equal(&u->uid, &last_card)) {
        app_message("SCAN USER CARD IN QUERY");
        return;
    }
    Transaction t = {0};
    t.type = TX_REDEEM;
    t.id = u->id;
    t.delta = -cost;
    if (u->points < (unsigned)cost || !start_pending(&t))
        app_message("ERR BALANCE OR BUSY");
}
void app_confirm(void) {
    if (confirm_wait && pending_valid) {
        bool authorized = false;
        if (pending.type == TX_REGISTER)
            authorized = pending.role == ROLE_ADMIN ? setup_valid() : app_admin();
        else if (pending.type == TX_ADMIN_RECOVER)
            authorized = setup_valid();
        else if (pending.type == TX_STATUS)
            authorized = app_admin();
        else if (pending.type == TX_CONFIG)
            authorized = app_admin() || setup_valid();
        else if (pending.type == TX_REDEEM) {
            User *u = user_id(pending.id);
            authorized = u && uid_equal(&u->uid, &last_card);
        }
        if (elapsed(millis(), pending_at, 30000) || !authorized || exporting || app.moving ||
            (app.lid != LID_IDLE && !(app.lid == LID_HELD && pending.type == TX_CONFIG))) {
            pending_valid = confirm_wait = false;
            app_message("ERR CONFIRM EXPIRED/BUSY");
            return;
        }
        if (storage_begin(&pending)) {
            confirm_wait = false;
            app_message("COMMITTING");
        } else {
            pending_valid = confirm_wait = false;
            app_message("ERR TRANSACTION REJECTED");
        }
        return;
    }
    Transaction t = {0};
    switch (menu) {
    case 0:
    case 1:
    case 2:
        if (!change_mode(menu))
            app_message("ERR MODE BUSY");
        break;
    case 3:
    case 4:
        if (!app_line_start(menu - 2))
            app_message("ERR LINE INTERLOCK");
        break;
    case 5:
        if (!change_mode(MODE_CONVENIENCE))
            app_message("ERR MODE BUSY");
        break;
    case 6:
        app_stop(0);
        view = 1;
        recent_n = 0;
        record_scan = 0;
        record_page = 0;
        break;
    case 7:
        app_stop(0);
        view = 2;
        break;
    case 8:
        if (app_admin()) {
            register_wait = true;
            register_admin = false;
            app_admin_touch();
            app_message("SCAN NEW USER CARD");
        } else
            app_message("ERR ADMIN REQUIRED");
        break;
    case 9:
    case 10:
        if (app_admin()) {
            t.type = TX_STATUS;
            t.id = app.selected;
            t.status = menu == 9 ? USER_LOST : USER_DELETED;
            start_pending(&t);
        } else
            app_message("ERR ADMIN REQUIRED");
        break;
    case 11:
    case 12:
        prepare_redeem(menu == 11 ? 5 : 10);
        break;
    case 13:
        if (!change_mode(MODE_MAINTENANCE) || !app_open(0, true))
            app_message("ERR ADMIN/BUSY");
        break;
    case 14:
    case 15:
        if (app_admin()) {
            uint8_t d[16] = {'S', 'B', 'I', 'N'};
            for (unsigned i = 0; i < 4; i++)
                d[4 + i] = (uint8_t)(last_seq >> (8 * i));
            uint32_t c = crc32(d, 12);
            for (unsigned i = 0; i < 4; i++)
                d[12 + i] = (uint8_t)(c >> (8 * i));
            if (!rfid_card_test(menu == 15, d))
                app_message("ERR CARD BUSY");
        } else
            app_message("ERR ADMIN REQUIRED");
        break;
    case 16:
        if (!app_clear())
            app_message("ERR SOURCE NOT RECOVERED");
        break;
    case 17:
        if (!app_close())
            app_message("ERR CLOSE INTERLOCK");
        break;
    case 18:
        if (app_admin()) {
            t.type = TX_CONFIG;
            t.settings = settings;
            t.settings.mute = !t.settings.mute;
            start_pending(&t);
        } else
            app_message("ERR ADMIN REQUIRED");
        break;
    case 19:
        if (!app_arm())
            app_message("ERR ARM INTERLOCK");
        break;
    case 20:
        app_stop(F_STOP);
        servo_output(0);
        app.armed = false;
        break;
    case 21:
        view = 3;
        break;
    default:
        break;
    }
}
void app_back(void) {
    app_stop(F_STOP);
    pending_valid = confirm_wait = register_wait = exporting = false;
    view = 0;
    app_message("STOP / PENDING CANCELLED");
}
void app_transaction_result(bool ok) {
    if (pending_valid) {
        if (ok && ((pending.type == TX_REGISTER && pending.role == ROLE_ADMIN) ||
                   pending.type == TX_ADMIN_RECOVER)) {
            local_setup = false;
            admin_active = true;
            admin_id = pending.id;
            admin_at = millis();
        }
        pending_valid = false;
    }
    app_message(ok ? "OK COMMITTED" : "ERR STORAGE");
    if (ok)
        beep(2);
}
static bool number(const char *s, long lo, long hi, long *v) {
    if (!s || !*s)
        return false;
    errno = 0;
    char *end;
    long n = strtol(s, &end, 10);
    if (errno || *end || n < lo || n > hi)
        return false;
    *v = n;
    return true;
}
static void status_line(unsigned port) {
    char b[220];
    snprintf(b, sizeof(b),
             "OK STATUS MODE=%s FAULT=%08lX ARM=%u LID=%u VBAT=%u SEQ=%lu STORE=%u MCP=%u MPU=%u "
             "RFID=%u NOR=%06lX FULL=%s RANGE=%u LOOP_MAX_MS=%lu\r\n",
             modes[app.mode], (unsigned long)(app.faults | irq_faults), app.armed, app.lid,
             dev.vbat_mv, (unsigned long)last_seq, store_state, dev.mcp, dev.mpu, dev.rfid,
             (unsigned long)dev.jedec,
             dev.full_unknown ? "UNKNOWN"
             : dev.full       ? "YES"
                              : "NO",
             dev.range_mm, (unsigned long)(app.max_loop_us / 1000));
    serial_send((uint8_t)port, b);
}
void app_command(uint8_t port, char *line) {
    char *v[6];
    unsigned n = 0;
    char *p = line;
    while (*p) {
        while (*p == ' ')
            p++;
        if (!*p)
            break;
        if (n == 6) {
            reply(port, "ERR TOO_MANY_ARGS");
            return;
        }
        v[n++] = p;
        while (*p && *p != ' ')
            p++;
        if (*p)
            *p++ = 0;
    }
    if (!n)
        return;
    long x;
    bool ok = false;
    if (!strcmp(v[0], "STOP")) {
        app_back();
        reply(port, "OK STOP");
        return;
    }
    if (!strcmp(v[0], "STATUS") && n == 1) {
        status_line(port);
        return;
    }
    if (!strcmp(v[0], "RAW") && n == 1) {
        char s[220];
        snprintf(s, sizeof(s),
                 "RAW PA=%04X PB=%04X MCP_A=%02X MCP_B=%02X LIGHT=%u ROLL10=%d PITCH10=%d DHT=%u "
                 "TEMP10=%d RH10=%u AUDIO_FAIL=%u RF_VER=%02X\r\n",
                 gpio_a(), gpio_b(), dev.mcp_a, dev.mcp_b, dev.light_raw, dev.roll10, dev.pitch10,
                 dev.dht_valid, dev.temp10, dev.humidity10, dev.audio_failed, dev.rfid_version);
        serial_send(port, s);
        return;
    }
    if (!strcmp(v[0], "HELP") && n == 1) {
        reply(port, "STATUS RAW STOP CLEAR MODE MOVE LINE QUERY EXPORT CANCEL ARM DISARM REGISTER "
                    "LOST DELETE RESTORE REDEEM SELECT CONFIRM SET SERVO OPEN CLOSE CARD_READ "
                    "CARD_WRITE ADMIN_RECOVER");
        return;
    }
    if (!strcmp(v[0], "CANCEL") && n == 1) {
        pending_valid = confirm_wait = register_wait = exporting = false;
        reply(port, "OK CANCEL");
        return;
    }
    if (!strcmp(v[0], "CLEAR") && n == 1) {
        ok = app_clear();
    } else if (!strcmp(v[0], "DISARM") && n == 1) {
        app_stop(F_STOP);
        servo_output(0);
        app.armed = false;
        ok = true;
    } else if (!strcmp(v[0], "ARM") && n == 2 && !strcmp(v[1], "CONFIRM") && port == 0) {
        ok = app_arm();
        if (ok) {
            app.armed = true;
            app_message("ARMED: bench calibration required");
        }
    } else if (!strcmp(v[0], "MODE") && n == 2) {
        for (unsigned i = 0; i < 6; i++)
            if (!strcmp(v[1], modes[i]))
                ok = change_mode(i);
    } else if (!strcmp(v[0], "MOVE") && n == 3 && number(v[2], 0, 40, &x) && strlen(v[1]) == 1) {
        switch (v[1][0]) {
        case 'F':
            ok = app_motion((int)x, (int)x);
            break;
        case 'B':
            ok = app_motion(-(int)x, -(int)x);
            break;
        case 'L':
            ok = app_motion(-(int)x, (int)x);
            break;
        case 'R':
            ok = app_motion((int)x, -(int)x);
            break;
        default:
            break;
        }
    } else if (!strcmp(v[0], "LINE") && n == 3 && !strcmp(v[1], "START") &&
               number(v[2], 1, 2, &x)) {
        ok = app_line_start((unsigned)x);
    } else if (!strcmp(v[0], "QUERY") && n == 2 && number(v[1], 1, 64, &x)) {
        User *u = user_id((uint16_t)x);
        if (u) {
            char b[90];
            snprintf(b, sizeof(b), "OK USER %u POINTS %lu COUNT %lu STATE %u", u->id,
                     (unsigned long)u->points, (unsigned long)u->count, u->status);
            reply(port, b);
            return;
        }
    } else if (!strcmp(v[0], "EXPORT") && n == 1 && port == 0) {
        ok = !app.moving && !app.left && !app.right && app.lid == LID_IDLE &&
             store_state == STORE_READY && !pending_valid;
        if (ok) {
            exporting = true;
            export_port = port;
            export_index = 0;
            export_seq = last_seq;
            export_at = millis();
            serial_send(
                port,
                "kind,id,uid_or_seq,role_or_type,state_or_delta,points,count,boot,uptime\r\n");
        }
    } else if (port == 0) {
        if (!strcmp(v[0], "CONFIRM") && n == 1) {
            app_confirm();
            return;
        }
        if (!strcmp(v[0], "SELECT") && n == 2 && number(v[1], 1, 64, &x)) {
            ok = user_id((uint16_t)x) != 0;
            if (ok)
                app.selected = (uint16_t)x;
        } else if (!strcmp(v[0], "REGISTER") && n == 1 && app_admin()) {
            register_wait = true;
            register_admin = false;
            app_admin_touch();
            ok = true;
        } else if (!strcmp(v[0], "ADMIN_RECOVER") && n == 1 && setup_valid() &&
                   store_state == STORE_READY) {
            register_wait = true;
            register_admin = true;
            ok = true;
        } else if ((!strcmp(v[0], "LOST") || !strcmp(v[0], "DELETE") || !strcmp(v[0], "RESTORE")) &&
                   n == 2 && number(v[1], 1, 64, &x) && app_admin()) {
            Transaction t = {0};
            t.type = TX_STATUS;
            t.id = (uint16_t)x;
            t.status = !strcmp(v[0], "LOST")     ? USER_LOST
                       : !strcmp(v[0], "DELETE") ? USER_DELETED
                                                 : USER_ACTIVE;
            ok = start_pending(&t);
            app_admin_touch();
        } else if (!strcmp(v[0], "REDEEM") && n == 2 && number(v[1], 5, 10, &x) &&
                   (x == 5 || x == 10)) {
            prepare_redeem((int)x);
            return;
        } else if (!strcmp(v[0], "SERVO") && n == 2 && number(v[1], 900, 2100, &x)) {
            ok = app_servo_test((unsigned)x);
        } else if (!strcmp(v[0], "CLOSE") && n == 1) {
            ok = app_close();
        } else if (!strcmp(v[0], "OPEN") && n == 1 && app.mode == MODE_MAINTENANCE && app_admin()) {
            ok = app_open(0, true);
        } else if (!strcmp(v[0], "SET") && n == 3 && number(v[2], -1800, 4095, &x) &&
                   (app_admin() || setup_valid())) {
            Transaction t = {0};
            t.type = TX_CONFIG;
            t.settings = settings;
            ok = true;
            if (!strcmp(v[1], "CLOSE"))
                t.settings.close_us = (uint16_t)x;
            else if (!strcmp(v[1], "OPEN"))
                t.settings.open_us = (uint16_t)x;
            else if (!strcmp(v[1], "FULL"))
                t.settings.full_mm = (uint16_t)x;
            else if (!strcmp(v[1], "CLEAR"))
                t.settings.clear_mm = (uint16_t)x;
            else if (!strcmp(v[1], "PWM"))
                t.settings.pwm_max = (uint16_t)x;
            else if (!strcmp(v[1], "ADC_SCALE"))
                t.settings.adc_scale = (uint16_t)x;
            else if (!strcmp(v[1], "LIGHT_ON"))
                t.settings.light_on = (uint16_t)x;
            else if (!strcmp(v[1], "LIGHT_OFF"))
                t.settings.light_off = (uint16_t)x;
            else if (!strcmp(v[1], "ROLL_ZERO"))
                t.settings.roll_zero = (int16_t)x;
            else if (!strcmp(v[1], "PITCH_ZERO"))
                t.settings.pitch_zero = (int16_t)x;
            else if (!strcmp(v[1], "CALIBRATED") && (x == 0 || x == 1))
                t.settings.calibrated = (uint8_t)x;
            else if (!strcmp(v[1], "MUTE") && (x == 0 || x == 1))
                t.settings.mute = (uint8_t)x;
            else
                ok = false;
            if (ok && t.settings.calibrated && t.settings.open_us == t.settings.close_us)
                ok = false;
            if (ok)
                ok = settings_valid(&t.settings) && start_pending(&t);
            app_admin_touch();
        } else if ((!strcmp(v[0], "CARD_READ") || !strcmp(v[0], "CARD_WRITE")) && n == 1 &&
                   app_admin() && !app.moving && app.lid == LID_IDLE) {
            menu = !strcmp(v[0], "CARD_READ") ? 14 : 15;
            app_confirm();
            return;
        }
    }
    reply(port, ok ? "OK" : "ERR ARG/AUTH/BUSY/INTERLOCK");
}
static void export_step(void) {
    if (!exporting)
        return;
    if (last_seq != export_seq || store_state != STORE_READY ||
        elapsed(millis(), export_at, 10000)) {
        exporting = false;
        app_message("EXPORT CANCELLED");
        return;
    }
    char s[180];
    bool send = false;
    if (export_index < 64) {
        User *u = &users[export_index];
        if (u->id) {
            char uid[21];
            for (unsigned i = 0; i < u->uid.len; i++)
                snprintf(uid + i * 2, sizeof(uid) - i * 2, "%02X", u->uid.b[i]);
            snprintf(s, sizeof(s), "USER,%u,%s,%u,%u,%lu,%lu,,\r\n", u->id, uid, u->role, u->status,
                     (unsigned long)u->points, (unsigned long)u->count);
            send = true;
        }
    } else if (export_index < 64 + 1008) {
        uint8_t r[64];
        if (storage_log(export_index - 64, r)) {
            if (r[14] == TX_CONFIG) {
                snprintf(s, sizeof(s), "CONFIG,,%lu,%u,,,,,\r\n", (unsigned long)get32(r + 4),
                         r[14]);
            } else
                snprintf(s, sizeof(s), "LOG,%u,%lu,%u,%ld,%lu,%lu,%lu,%lu\r\n", get16(r + 12),
                         (unsigned long)get32(r + 4), r[14], (long)(int32_t)get32(r + 16),
                         (unsigned long)get32(r + 20), (unsigned long)get32(r + 24),
                         (unsigned long)get32(r + 28), (unsigned long)get32(r + 32));
            send = true;
        }
    } else {
        if (serial_send(export_port, "END\r\n"))
            exporting = false;
        return;
    }
    if (!send || serial_send(export_port, s)) {
        export_index++;
        export_at = millis();
    }
}
typedef struct {
    bool raw, stable, long_sent;
    uint32_t changed, pressed;
} Button;
static Button keys[3];
static bool combo_sent;
static uint8_t encoder_prev;
static int encoder_sum;
static void button_step(void) {
    uint32_t now = millis();
    if (!dev.mcp || elapsed(now, dev.mcp_at, 50))
        return;
    bool both = !(dev.mcp_b & BIT(5)) && !(dev.mcp_b & BIT(6));
    if (both) {
        if (!combo_at)
            combo_at = now;
        if (!combo_sent && elapsed(now, combo_at, 3000)) {
            combo_sent = true;
            app_stop(F_STOP);
            local_setup = true;
            setup_at = now;
            if (store_state == STORE_FRESH) {
                if (storage_format()) {
                    register_wait = true;
                    register_admin = true;
                    app_message("INIT: WAIT READY, SCAN ADMIN");
                }
            } else if (store_state == STORE_READY) {
                app_message("LOCAL SETUP: ADMIN_RECOVER");
            } else
                app_message("ERR STORAGE: NO AUTO FORMAT");
        }
    } else {
        combo_at = 0;
        combo_sent = false;
    }
    for (unsigned i = 0; i < 3; i++) {
        Button *k = &keys[i];
        bool raw = !(dev.mcp_b & BIT(4 + i));
        if (raw != k->raw) {
            k->raw = raw;
            k->changed = now;
        }
        if (k->raw != k->stable && elapsed(now, k->changed, 20)) {
            k->stable = k->raw;
            if (k->stable) {
                k->pressed = now;
                k->long_sent = false;
                if (app_admin())
                    app_admin_touch();
                if (i == 2 && !both)
                    app_back();
            } else if (!k->long_sent && !both && i == 1) {
                menu = (menu + 1) % (sizeof(menus) / sizeof(menus[0]));
                view = 0;
            } else if (!k->long_sent && !both && i == 0)
                app_confirm();
        }
        if (k->stable && !k->long_sent && elapsed(now, k->pressed, 800)) {
            k->long_sent = true;
            if (i == 1 && !both)
                app_confirm();
        }
    }
}
static void encoder_step(void) {
    uint8_t v = (uint8_t)((gpio_b() >> 3) & 3);
    static const int8_t table[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
    if ((v ^ encoder_prev) == 3)
        encoder_sum = 0;
    else
        encoder_sum += table[(encoder_prev << 2) | v];
    encoder_prev = v;
    if (encoder_sum >= ENCODER_EDGES || encoder_sum <= -ENCODER_EDGES) {
        int d = encoder_sum > 0 ? 1 : -1;
        encoder_sum = 0;
        if (app_admin())
            app_admin_touch();
        if (view == 1) {
            record_page ^= 1;
            return;
        }
        if (menu == 9 || menu == 10) {
            int id = (int)app.selected + d;
            if (id < 1)
                id = 64;
            if (id > 64)
                id = 1;
            app.selected = (uint16_t)id;
        } else {
            int m = (int)menu + d;
            if (m < 0)
                m = (int)(sizeof(menus) / sizeof(menus[0])) - 1;
            if (m >= (int)(sizeof(menus) / sizeof(menus[0])))
                m = 0;
            menu = (uint8_t)m;
        }
        view = 0;
    }
}
static void records_step(void) {
    if (view != 1 || record_scan >= 1008 || store_state != STORE_READY)
        return;
    uint8_t r[64];
    if (storage_log(record_scan++, r)) {
        unsigned pos = 0;
        while (pos < recent_n && get32(recent[pos] + 4) > get32(r + 4))
            pos++;
        if (pos < 10) {
            unsigned end = recent_n < 10 ? recent_n++ : 9;
            for (unsigned i = end; i > pos; i--)
                memcpy(recent[i], recent[i - 1], 64);
            memcpy(recent[pos], r, 64);
        }
    }
}
static void render(void) {
    char s[80];
    snprintf(s, sizeof(s), "%s %s", app.armed ? "ARM" : "SAFE", modes[app.mode]);
    display_text(0, s);
    snprintf(s, sizeof(s), "FAULT %04lX STORE %u", (unsigned long)(app.faults | irq_faults),
             store_state);
    display_text(1, s);
    snprintf(s, sizeof(s), "BAT %u.%03u LID %u", dev.vbat_mv / 1000, dev.vbat_mv % 1000, app.lid);
    display_text(2, s);
    User *u = user_id(app.selected);
    snprintf(s, sizeof(s), "USER %u POINTS %lu", app.selected, (unsigned long)(u ? u->points : 0));
    display_text(3, s);
    snprintf(s, sizeof(s), "FULL %s DIST %u",
             dev.full_unknown ? "?"
             : dev.full       ? "YES"
                              : "NO",
             dev.range_mm);
    display_text(4, s);
    display_text(7, confirm_wait ? "CONFIRM PENDING" : menus[menu]);
    if (view == 1) {
        for (unsigned i = 0; i < 5; i++) {
            unsigned j = i + record_page * 5;
            if (j < recent_n)
                snprintf(s, sizeof(s), "%lu U%u T%u %ld", (unsigned long)get32(recent[j] + 4),
                         get16(recent[j] + 12), recent[j][14],
                         recent[j][14] == TX_CONFIG ? 0L : (long)(int32_t)get32(recent[j] + 16));
            else
                s[0] = 0;
            display_text((uint8_t)(i + 2), s);
        }
    }
    if (view == 2) {
        uint8_t order[64];
        unsigned count = 0;
        for (unsigned i = 0; i < 64; i++)
            if (users[i].id && users[i].role == ROLE_USER && users[i].status == USER_ACTIVE)
                order[count++] = (uint8_t)i;
        for (unsigned i = 1; i < count; i++)
            for (unsigned j = i; j > 0; j--) {
                User *a = &users[order[j - 1]], *b = &users[order[j]];
                if (a->points > b->points || (a->points == b->points && a->id < b->id))
                    break;
                uint8_t t = order[j];
                order[j] = order[j - 1];
                order[j - 1] = t;
            }
        for (unsigned i = 0; i < 5; i++) {
            if (i < count)
                snprintf(s, sizeof(s), "%u USER %u %lu", i + 1, users[order[i]].id,
                         (unsigned long)users[order[i]].points);
            else
                s[0] = 0;
            display_text((uint8_t)(i + 2), s);
        }
    }
    if (view == 3) {
        if (dev.dht_valid)
            snprintf(s, sizeof(s), "TEMP10 %d RH10 %u", dev.temp10, dev.humidity10);
        else
            snprintf(s, sizeof(s), "DHT UNKNOWN / STALE");
        display_text(3, s);
        snprintf(s, sizeof(s), "LIGHT %u LED %u", dev.light_raw, dev.light);
        display_text(4, s);
        snprintf(s, sizeof(s), "ROLL10 %d PITCH10 %d", dev.roll10, dev.pitch10);
        display_text(5, s);
    }
}
void app_ui_step(void) {
    uint32_t now = millis();
    encoder_step();
    if (elapsed(now, button_at, 10)) {
        button_at = now;
        button_step();
    }
    if (local_setup && !setup_valid())
        local_setup = false;
    if (admin_active && !app_admin()) {
        admin_active = false;
        register_wait = false;
    }
    if (confirm_wait && elapsed(now, pending_at, 30000)) {
        confirm_wait = pending_valid = false;
        app_message("CONFIRM EXPIRED");
    }
    export_step();
    records_step();
    if (elapsed(now, ui_at, 200)) {
        ui_at = now;
        render();
    }
}
