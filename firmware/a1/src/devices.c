#include "devices.h"
#include "storage.h"
#include "platform.h"
#include <string.h>
#include <math.h>
Devices dev;
static uint8_t shadow, display[1024], oled_page, oled_col;
static uint32_t mcp_due, mcp_check_due, mpu_due, adc_due, range_due, dht_due, light_since, beep_at,
    audio_at, closed_at;
static uint8_t beep_left, audio_q[4], audio_n, audio_state;
static bool beep_on, audio_seen, light_candidate, closed_previous;
static float axf, ayf, azf;
static uint16_t ranges[5];
static uint8_t range_n, range_index, full_hits, clear_hits, range_errors;
static volatile uint8_t echo_state, dht_state, dht_bits, dht_bytes[5];
static volatile uint16_t echo_rise, echo_width, dht_edge;
static uint32_t echo_at, dht_start;
enum {
    D_IDLE,
    D_LOW,
    D_RESP_FALL,
    D_RESP_RISE,
    D_FIRST_FALL,
    D_BIT_RISE,
    D_BIT_FALL,
    D_DONE,
    D_ERROR
};
static bool reg_write(uint8_t addr, uint8_t reg, uint8_t val) {
    uint8_t p[2] = {reg, val};
    return i2c_write(addr, p, 2);
}
bool mcp_update(uint8_t mask, uint8_t val) {
    uint8_t next = (uint8_t)((shadow & ~mask) | (val & mask));
    next &= 0x3f;
    if (!dev.mcp || !reg_write(0x20, 0x14, next)) {
        dev.mcp = false;
        motor_off();
        return false;
    }
    shadow = next;
    return true;
}
bool mcp_direction(uint8_t val) {
    uint8_t r;
    if (!mcp_update(15, val) || !i2c_read_reg(0x20, 0x14, &r, 1) || r != shadow) {
        dev.mcp = false;
        motor_off();
        return false;
    }
    return true;
}
void sensor_abort_irq(void) {
    dht_arm(false);
    dht_drive(false);
    dht_state = D_ERROR;
}
void sensor_edge_irq(uint8_t pin, bool high, uint16_t t) {
    if (pin == 1) {
        if (echo_state == 1 && high) {
            echo_rise = t;
            echo_state = 2;
        } else if (echo_state == 2 && !high) {
            echo_width = (uint16_t)(t - echo_rise);
            echo_state = 3;
        }
        return;
    }
    uint16_t dt = (uint16_t)(t - dht_edge);
    switch (dht_state) {
    case D_RESP_FALL:
        if (!high) {
            dht_edge = t;
            dht_state = D_RESP_RISE;
        }
        break;
    case D_RESP_RISE:
        if (high && dt >= 60 && dt <= 110) {
            dht_edge = t;
            dht_state = D_FIRST_FALL;
        } else
            sensor_abort_irq();
        break;
    case D_FIRST_FALL:
        if (!high && dt >= 60 && dt <= 110) {
            dht_edge = t;
            dht_state = D_BIT_RISE;
        } else
            sensor_abort_irq();
        break;
    case D_BIT_RISE:
        if (high && dt >= 35 && dt <= 75) {
            dht_edge = t;
            dht_state = D_BIT_FALL;
        } else
            sensor_abort_irq();
        break;
    case D_BIT_FALL:
        if (high || !((dt >= 15 && dt <= 40) || (dt >= 55 && dt <= 90))) {
            sensor_abort_irq();
            break;
        }
        dht_bytes[dht_bits / 8] = (uint8_t)((dht_bytes[dht_bits / 8] << 1) | (dt >= 55));
        dht_bits++;
        dht_edge = t;
        if (dht_bits == 40) {
            dht_arm(false);
            dht_state = D_DONE;
        } else
            dht_state = D_BIT_RISE;
        break;
    default:
        break;
    }
}
static void dht_step(uint32_t now, bool moving) {
    if (moving) {
        if (dht_state != D_IDLE)
            sensor_abort_irq();
        dht_state = D_IDLE;
        return;
    }
    if (dht_state == D_IDLE) {
        if (now >= 2000 && elapsed(now, dht_due, 3000)) {
            dht_due = now;
            dht_start = now;
            dht_arm(false);
            dht_drive(true);
            dht_state = D_LOW;
        }
        return;
    }
    if (dht_state == D_LOW) {
        if (elapsed(now, dht_start, 30)) {
            sensor_abort_irq();
            return;
        }
        if (elapsed(now, dht_start, 20)) {
            memset((void *)dht_bytes, 0, 5);
            dht_bits = 0;
            dht_start = now;
            dht_edge = micros16();
            dht_state = D_RESP_FALL;
            dht_arm(true);
            dht_drive(false);
        }
        return;
    }
    if (dht_state == D_DONE) {
        uint8_t sum = (uint8_t)(dht_bytes[0] + dht_bytes[1] + dht_bytes[2] + dht_bytes[3]);
        dev.dht_valid = sum == dht_bytes[4] && dht_bytes[0] <= 100 && (dht_bytes[2] & 127) <= 80;
        if (dev.dht_valid) {
            dev.humidity10 = (uint16_t)(dht_bytes[0] * 10 + dht_bytes[1]);
            dev.temp10 = (int16_t)((dht_bytes[2] & 127) * 10 + (dht_bytes[3] & 127));
            if (dht_bytes[3] & 128)
                dev.temp10 = -dev.temp10;
            dev.dht_at = now;
        }
        dht_state = D_IDLE;
        return;
    }
    if (dht_state == D_ERROR || elapsed(now, dht_start, 6) ||
        (uint16_t)(micros16() - dht_edge) > 150) {
        sensor_abort_irq();
        dev.dht_valid = false;
        dht_state = D_IDLE;
    }
}
static void range_step(uint32_t now, bool allowed, bool maintenance) {
    if (!allowed) {
        echo_state = 0;
        range_n = 0;
        full_hits = clear_hits = 0;
        return;
    }
    if (echo_state == 3) {
        uint16_t w = echo_width;
        echo_state = 0;
        if (w < 110 || w > 24000) {
            range_errors++;
        } else {
            uint16_t mm = (uint16_t)((uint32_t)w * 343 / 2000);
            ranges[range_index++ % 5] = mm;
            if (range_n < 5)
                range_n++;
            range_errors = 0;
            dev.range_at = now;
            dev.range_valid = true;
            if (range_n == 5) {
                uint16_t a[5];
                memcpy(a, ranges, sizeof(a));
                for (unsigned i = 1; i < 5; i++)
                    for (unsigned j = i; j > 0 && a[j] < a[j - 1]; j--) {
                        uint16_t t = a[j];
                        a[j] = a[j - 1];
                        a[j - 1] = t;
                    }
                dev.range_mm = a[2];
                full_hits = a[2] <= settings.full_mm ? (uint8_t)(full_hits + 1) : 0;
                clear_hits = a[2] >= settings.clear_mm ? (uint8_t)(clear_hits + 1) : 0;
                if (full_hits >= 5) {
                    dev.full = true;
                    full_hits = 5;
                }
                if (clear_hits >= 5) {
                    if (maintenance)
                        dev.full = false;
                    clear_hits = 5;
                }
                dev.full_unknown = false;
            }
        }
    }
    if ((echo_state == 1 || echo_state == 2) && elapsed(now, echo_at, 25)) {
        echo_state = 0;
        if (range_errors < 10)
            range_errors++;
    }
    if (range_errors >= 10) {
        dev.full_unknown = true;
        dev.range_valid = false;
    }
    if (!echo_state && elapsed(now, range_due, 100)) {
        range_due = now;
        echo_at = now;
        echo_state = 1;
        trigger_output(true);
        delay_us(10);
        trigger_output(false);
    }
}
static void df_send(uint8_t cmd, uint16_t arg) {
    uint8_t p[10] = {0x7e, 0xff, 6, cmd, 0, (uint8_t)(arg >> 8), (uint8_t)arg, 0, 0, 0xef};
    uint16_t sum = 0;
    for (unsigned i = 1; i < 7; i++)
        sum += p[i];
    sum = (uint16_t)(0 - sum);
    p[7] = (uint8_t)(sum >> 8);
    p[8] = (uint8_t)sum;
    audio_send(p, 10);
}
void audio_queue(uint8_t track, bool priority) {
    if (settings.mute)
        return;
    if (priority) {
        audio_n = 0;
        df_send(0x16, 0);
        audio_state = 0;
    }
    for (unsigned i = 0; i < audio_n; i++)
        if (audio_q[i] == track)
            return;
    if (audio_n < 4)
        audio_q[audio_n++] = track;
}
void beep(uint8_t count) {
    beep_left = count;
    beep_on = false;
    beep_at = millis() - 100;
}
static void sound_step(uint32_t now) {
    if (settings.mute) {
        beep_left = 0;
        buzzer_output(false);
        audio_n = 0;
        if (audio_state) {
            df_send(0x16, 0);
            audio_state = 0;
        }
    }
    if (beep_left && elapsed(now, beep_at, 100)) {
        beep_at = now;
        beep_on = !beep_on;
        buzzer_output(beep_on);
        if (!beep_on)
            beep_left--;
    }
    if (audio_state == 0 && audio_n && now >= 1500) {
        uint8_t t = audio_q[0];
        memmove(audio_q, audio_q + 1, --audio_n);
        df_send(0x12, t);
        audio_at = now;
        audio_state = 1;
        audio_seen = false;
    }
    bool active = (((dev.mcp_a >> 6) & 1) != 0) == AUDIO_BUSY_HIGH;
    if (audio_state) {
        if (active)
            audio_seen = true;
        bool failed =
            elapsed(now, audio_at, 10000) || (!audio_seen && elapsed(now, audio_at, 1500));
        if ((audio_seen && !active) || failed) {
            dev.audio_failed = failed;
            audio_state = 0;
        }
    }
}
/* Original compact 5x7 glyphs. Lowercase maps to uppercase; no external font. */
static const uint8_t letters[26][5] = {{0x7e, 9, 9, 9, 0x7e},
                                       {0x7f, 0x49, 0x49, 0x49, 0x36},
                                       {0x3e, 0x41, 0x41, 0x41, 0x22},
                                       {0x7f, 0x41, 0x41, 0x22, 0x1c},
                                       {0x7f, 0x49, 0x49, 0x49, 0x41},
                                       {0x7f, 9, 9, 9, 1},
                                       {0x3e, 0x41, 0x49, 0x49, 0x7a},
                                       {0x7f, 8, 8, 8, 0x7f},
                                       {0, 0x41, 0x7f, 0x41, 0},
                                       {0x20, 0x40, 0x40, 0x40, 0x3f},
                                       {0x7f, 8, 0x14, 0x22, 0x41},
                                       {0x7f, 0x40, 0x40, 0x40, 0x40},
                                       {0x7f, 2, 4, 2, 0x7f},
                                       {0x7f, 2, 4, 8, 0x7f},
                                       {0x3e, 0x41, 0x41, 0x41, 0x3e},
                                       {0x7f, 9, 9, 9, 6},
                                       {0x3e, 0x41, 0x51, 0x21, 0x5e},
                                       {0x7f, 9, 0x19, 0x29, 0x46},
                                       {0x26, 0x49, 0x49, 0x49, 0x32},
                                       {1, 1, 0x7f, 1, 1},
                                       {0x3f, 0x40, 0x40, 0x40, 0x3f},
                                       {0x1f, 0x20, 0x40, 0x20, 0x1f},
                                       {0x7f, 0x20, 0x18, 0x20, 0x7f},
                                       {0x63, 0x14, 8, 0x14, 0x63},
                                       {3, 4, 0x78, 4, 3},
                                       {0x61, 0x51, 0x49, 0x45, 0x43}};
static const uint8_t digits[10][5] = {
    {0x3e, 0x51, 0x49, 0x45, 0x3e}, {0, 0x42, 0x7f, 0x40, 0},
    {0x62, 0x51, 0x49, 0x49, 0x46}, {0x22, 0x41, 0x49, 0x49, 0x36},
    {0x18, 0x14, 0x12, 0x7f, 0x10}, {0x27, 0x45, 0x45, 0x45, 0x39},
    {0x3e, 0x49, 0x49, 0x49, 0x32}, {1, 0x71, 9, 5, 3},
    {0x36, 0x49, 0x49, 0x49, 0x36}, {0x26, 0x49, 0x49, 0x49, 0x3e}};
void display_text(uint8_t row, const char *s) {
    if (row >= 8)
        return;
    uint8_t *d = display + row * 128;
    memset(d, 0, 128);
    for (unsigned i = 0; i < 21 && s[i]; i++) {
        char c = s[i];
        if (c >= 'a' && c <= 'z')
            c = (char)(c - 'a' + 'A');
        if (c >= 'A' && c <= 'Z')
            memcpy(d + i * 6, letters[c - 'A'], 5);
        else if (c >= '0' && c <= '9')
            memcpy(d + i * 6, digits[c - '0'], 5);
        else if (c == '-')
            memset(d + i * 6, 8, 5);
        else if (c == ':') {
            d[i * 6 + 2] = 0x24;
        } else if (c == '.')
            d[i * 6 + 2] = 0x40;
        else if (c == '/') {
            for (unsigned j = 0; j < 5; j++)
                d[i * 6 + j] = (uint8_t)(0x20 >> j);
        } else if (c == '?') {
            d[i * 6] = 2;
            d[i * 6 + 1] = 1;
            d[i * 6 + 2] = 0x59;
            d[i * 6 + 3] = 9;
            d[i * 6 + 4] = 6;
        }
    }
}
void display_step(void) {
    if (!dev.oled)
        return;
    static bool address_phase;
    uint8_t p[17];
    if (!address_phase) {
        unsigned col = oled_col + (OLED_SH1106 ? 2 : 0);
        uint8_t cmd[4] = {0, (uint8_t)(0xb0 + oled_page), (uint8_t)(col & 15),
                          (uint8_t)(0x10 | (col >> 4))};
        if (!i2c_write(OLED_ADDR, cmd, 4))
            dev.oled = false;
        address_phase = true;
    } else {
        p[0] = 0x40;
        memcpy(p + 1, display + oled_page * 128 + oled_col, 16);
        if (!i2c_write(OLED_ADDR, p, 17))
            dev.oled = false;
        oled_col += 16;
        if (oled_col == 128) {
            oled_col = 0;
            oled_page = (oled_page + 1) & 7;
        }
        address_phase = false;
    }
}
void devices_init(void) {
    memset(&dev, 0, sizeof(dev));
    dev.full_unknown = true;
    uint8_t p[2], dirs[2];
    dev.mcp = reg_write(0x20, 5, 0) && reg_write(0x20, 0x0a, 0) && reg_write(0x20, 0x14, 0) &&
              reg_write(0x20, 0x15, 0) && reg_write(0x20, 0, 0x40) && reg_write(0x20, 1, 0x7f) &&
              reg_write(0x20, 0x0c, 0x40) && reg_write(0x20, 0x0d, 0x7f) &&
              i2c_read_reg(0x20, 0, dirs, 2) && dirs[0] == 0x40 && dirs[1] == 0x7f;
    shadow = 0;
    if (dev.mcp)
        mcp_update(0x10, 0x10);
#if OLED_SH1106
    const uint8_t oled_init[] = {0,    0xae, 0xd5, 0x80, 0xa8, 0x3f, 0xd3, 0,
                                 0x40, 0xad, 0x8b, 0xa1, 0xc8, 0xda, 0x12, 0x81,
                                 0x7f, 0xd9, 0x22, 0xdb, 0x35, 0xa4, 0xa6, 0xaf};
#else
    const uint8_t oled_init[] = {0,    0xae, 0xd5, 0x80, 0xa8, 0x3f, 0xd3, 0,    0x40,
                                 0x8d, 0x14, 0x20, 2,    0xa1, 0xc8, 0xda, 0x12, 0x81,
                                 0x7f, 0xd9, 0xf1, 0xdb, 0x40, 0xa4, 0xa6, 0xaf};
#endif
    dev.oled = i2c_write(OLED_ADDR, oled_init, sizeof(oled_init));
    dev.mpu = i2c_read_reg(MPU_ADDR, 0x75, p, 1) && p[0] == 0x68 && reg_write(MPU_ADDR, 0x6b, 1) &&
              reg_write(MPU_ADDR, 0x1c, 0) && reg_write(MPU_ADDR, 0x1a, 3);
    dev.nor = nor_init();
    rfid_init();
    df_send(6, 5);
    dht_state = D_IDLE;
}
void devices_step(bool moving, bool lid_closed, bool idle, bool maintenance) {
    uint32_t now = millis();
    if (elapsed(now, dev.dht_at, 6000))
        dev.dht_valid = false;
    sound_step(now);
    dht_step(now, moving);
    if (lid_closed && !closed_previous)
        closed_at = now;
    closed_previous = lid_closed;
    range_step(now, !moving && lid_closed && elapsed(now, closed_at, 500), maintenance);
    if (dev.mcp && elapsed(now, mcp_due, 10)) {
        mcp_due = now;
        uint8_t b[2];
        if (i2c_read_reg(0x20, 0x12, b, 2)) {
            dev.mcp_a = b[0];
            dev.mcp_b = b[1];
            dev.mcp_at = now;
        } else {
            dev.mcp = false;
            motor_off();
        }
        return;
    }
    if (dev.mcp && elapsed(now, mcp_check_due, 40)) {
        mcp_check_due = now;
        uint8_t b[2];
        if (!i2c_read_reg(0x20, 0, b, 2) || b[0] != 0x40 || b[1] != 0x7f) {
            dev.mcp = false;
            motor_off();
        }
        return;
    }
    if (dev.mpu && elapsed(now, mpu_due, 20)) {
        mpu_due = now;
        uint8_t b[6];
        if (i2c_read_reg(MPU_ADDR, 0x3b, b, 6)) {
            float a[3];
            for (unsigned i = 0; i < 3; i++)
                a[i] = (float)(int16_t)((uint16_t)b[i * 2] << 8 | b[i * 2 + 1]);
            float norm = a[0] * a[0] + a[1] * a[1] + a[2] * a[2];
            if (norm > 40000000.0f && norm < 900000000.0f) {
                axf += 0.2f * (a[0] - axf);
                ayf += 0.2f * (a[1] - ayf);
                azf += 0.2f * (a[2] - azf);
                dev.roll10 = (int16_t)(atan2f(ayf, azf) * 572.9578f) - settings.roll_zero;
                dev.pitch10 = (int16_t)(atan2f(-axf, sqrtf(ayf * ayf + azf * azf)) * 572.9578f) -
                              settings.pitch_zero;
                dev.mpu_at = now;
            }
        }
        return;
    }
    if (elapsed(now, adc_due, 100)) {
        adc_due = now;
        uint16_t b, l;
        dev.adc_valid = adc_read(1, &b);
        if (dev.adc_valid) {
            dev.vbat_mv =
                (uint16_t)((uint64_t)b * 3300 * 43 * settings.adc_scale / (4095u * 10u * 1000u));
            dev.adc_at = now;
        }
#if LIGHT_DIGITAL
        l = (gpio_b() & 1) ? 4095 : 0;
#else
        if (!adc_read(8, &l))
            return;
#endif
        dev.light_raw = l;
        bool dark = LIGHT_DARK_HIGH ? l >= settings.light_on : l <= settings.light_on;
        bool bright = LIGHT_DARK_HIGH ? l <= settings.light_off : l >= settings.light_off;
        bool candidate = dev.light ? (!bright) : dark;
        if (candidate != light_candidate) {
            light_candidate = candidate;
            light_since = now;
        }
        if (candidate != dev.light && elapsed(now, light_since, 2000) && dev.mcp) {
            if (mcp_update(0x20, candidate ? 0x20 : 0))
                dev.light = candidate;
        }
        return;
    }
    if (idle || !moving)
        display_step();
}
