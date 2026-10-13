#include "devices.h"
#include "platform.h"
#include <string.h>
#include <stdio.h>
static uint8_t state, rx[32], rx_len, rx_bits, cascade, block[5], frame[32];
static uint32_t started, next_poll, last_seen;
static Uid scanning, present, event_uid;
static bool event_ready, present_lock, request_test, test_write;
static uint8_t test_data[16], original[16];
enum {
    R_IDLE,
    R_WAKE,
    R_ANTICOLL,
    R_SELECT,
    R_AUTH,
    R_READ,
    R_WRITE_CMD,
    R_WRITE_DATA,
    R_VERIFY,
    R_HALT
};
static bool wr(uint8_t r, uint8_t v) {
    uint8_t p[2] = {(uint8_t)((r << 1) & 0x7e), v};
    return spi_transfer(false, p, 0, 2);
}
static bool rd(uint8_t reg, uint8_t *v) {
    uint8_t p[2] = {(uint8_t)(0x80 | ((reg << 1) & 0x7e)), 0}, r[2];
    if (!spi_transfer(false, p, r, 2))
        return false;
    *v = r[1];
    return true;
}
static uint16_t crc_a(const uint8_t *p, unsigned n) {
    uint16_t c = 0x6363;
    while (n--) {
        uint8_t d = (uint8_t)(*p++ ^ c);
        d ^= (uint8_t)(d << 4);
        c = (uint16_t)((c >> 8) ^ ((uint16_t)d << 8) ^ ((uint16_t)d << 3) ^ (d >> 4));
    }
    return c;
}
static void append_crc(uint8_t *p, unsigned n) {
    uint16_t c = crc_a(p, n);
    p[n] = (uint8_t)c;
    p[n + 1] = (uint8_t)(c >> 8);
}
static bool valid_crc(const uint8_t *p, unsigned n) {
    return n >= 2 && crc_a(p, n - 2) == ((uint16_t)p[n - 2] | ((uint16_t)p[n - 1] << 8));
}
static bool start(const uint8_t *p, uint8_t n, uint8_t bits, bool auth) {
    if (!wr(1, 0) || !wr(4, 0x7f) || !wr(10, 0x80) || !wr(13, bits))
        return false;
    for (unsigned i = 0; i < n; i++)
        if (!wr(9, p[i]))
            return false;
    if (!wr(1, auth ? 0x0e : 0x0c))
        return false;
    if (!auth && !wr(13, (uint8_t)(bits | 0x80)))
        return false;
    started = millis();
    return true;
}
static int poll(bool auth) {
    uint8_t irq, err;
    if (!rd(4, &irq) || !rd(6, &err))
        return -1;
    if (err & 0x1b)
        return -1;
    if (irq & (auth ? 0x10 : 0x30)) {
        if (auth) {
            uint8_t s;
            if (!rd(8, &s) || !(s & 8))
                return -1;
            return 1;
        }
        uint8_t ctrl;
        if (!rd(10, &rx_len) || !rd(12, &ctrl) || rx_len > sizeof(rx))
            return -1;
        rx_bits = ctrl & 7;
        for (unsigned i = 0; i < rx_len; i++)
            if (!rd(9, &rx[i]))
                return -1;
        return 1;
    }
    if ((irq & 1) || elapsed(millis(), started, 30))
        return -1;
    return 0;
}
static void finish(void) {
    wr(1, 0);
    wr(8, 0);
    state = R_IDLE;
    next_poll = millis();
}
static void halt_card(void) {
    uint8_t h[4] = {0x50, 0};
    append_crc(h, 2);
    if (start(h, 4, 0, false))
        state = R_HALT;
    else
        finish();
}
static bool report_block(const char *label, const uint8_t *p) {
    char s[90];
    int n = snprintf(s, sizeof(s), "%s ", label);
    for (unsigned i = 0; i < 16; i++)
        n += snprintf(s + n, sizeof(s) - (unsigned)n, "%02X", p[i]);
    snprintf(s + n, sizeof(s) - (unsigned)n, "\r\n");
    return serial_send(0, s);
}
void rfid_init(void) {
    state = R_IDLE;
    next_poll = millis();
    event_ready = present_lock = request_test = false;
    dev.rfid = false;
    if (!dev.mcp)
        return;
    if (!wr(1, 0x0f))
        return; /* Soft reset completion is checked on first service. */
}
static bool configure(void) {
    uint8_t v, c;
    if (!rd(1, &c) || (c & 0x10) || !rd(0x37, &v) || v == 0 || v == 255)
        return false;
    dev.rfid_version = v;
    return wr(0x2a, 0x8d) && wr(0x2b, 0x3e) && wr(0x2c, 0) && wr(0x2d, 30) && wr(0x15, 0x40) &&
           wr(0x11, 0x3d) && wr(0x26, 0x70) && wr(0x14, 3);
}
bool rfid_event(Uid *uid) {
    if (!event_ready)
        return false;
    *uid = event_uid;
    event_ready = false;
    return true;
}
bool rfid_card_test(bool write, const uint8_t data[16]) {
    if (!dev.rfid || request_test)
        return false;
    request_test = true;
    test_write = write;
    if (write)
        memcpy(test_data, data, 16);
    serial_send(0, "CARD_TEST: present dedicated Classic 1K card, block 4 only\r\n");
    return true;
}
void rfid_step(void) {
    uint32_t now = millis();
    if (!dev.mcp)
        return;
    if (!dev.rfid) {
        if (elapsed(now, next_poll, 50)) {
            dev.rfid = configure();
            next_poll = now;
        }
        return;
    }
    if (present_lock && elapsed(now, last_seen, 500))
        present_lock = false;
    if (state == R_IDLE) {
        if (!elapsed(now, next_poll, 60))
            return;
        scanning.len = 0;
        cascade = 0;
        uint8_t w = 0x52;
        wr(8, 0);
        if (start(&w, 1, 7, false))
            state = R_WAKE;
        else
            finish();
        return;
    }
    if (state == R_HALT) {
        if (elapsed(now, started, 5))
            finish();
        return;
    }
    int done = poll(state == R_AUTH);
    if (!done)
        return;
    if (done < 0) {
        if (state >= R_AUTH) {
            serial_send(0, "ERR CARD_TEST FAILED/UNKNOWN\r\n");
            request_test = false;
        }
        finish();
        return;
    }
    switch (state) {
    case R_WAKE:
        if (rx_len != 2 || rx_bits) {
            finish();
            break;
        }
        frame[0] = 0x93;
        frame[1] = 0x20;
        if (start(frame, 2, 0, false))
            state = R_ANTICOLL;
        else
            finish();
        break;
    case R_ANTICOLL:
        if (rx_len != 5 || rx_bits || (rx[0] ^ rx[1] ^ rx[2] ^ rx[3]) != rx[4]) {
            finish();
            break;
        }
        memcpy(block, rx, 5);
        frame[0] = (uint8_t)(0x93 + cascade * 2);
        frame[1] = 0x70;
        memcpy(frame + 2, block, 5);
        append_crc(frame, 7);
        if (start(frame, 9, 0, false))
            state = R_SELECT;
        else
            finish();
        break;
    case R_SELECT:
        if (rx_len != 3 || rx_bits || !valid_crc(rx, 3)) {
            finish();
            break;
        }
        if (block[0] == 0x88) {
            if (cascade >= 2 || !(rx[0] & 4)) {
                finish();
                break;
            }
            memcpy(scanning.b + scanning.len, block + 1, 3);
            scanning.len += 3;
        } else {
            if (rx[0] & 4) {
                finish();
                break;
            }
            memcpy(scanning.b + scanning.len, block, 4);
            scanning.len += 4;
        }
        if (rx[0] & 4) {
            cascade++;
            frame[0] = (uint8_t)(0x93 + cascade * 2);
            frame[1] = 0x20;
            if (start(frame, 2, 0, false))
                state = R_ANTICOLL;
            else
                finish();
            break;
        }
        last_seen = now;
        if (!present_lock) {
            present = scanning;
            if (!request_test) {
                event_uid = scanning;
                event_ready = true;
            }
            present_lock = true;
        } else if (present.len != scanning.len ||
                   memcmp(present.b, scanning.b,
                          scanning.len)) { /* require a real absence before another identity */
        }
        if (request_test) {
            if ((rx[0] & 0x7f) != 8) {
                serial_send(0, "ERR CLASSIC_1K_REQUIRED\r\n");
                request_test = false;
                halt_card();
                break;
            }
            frame[0] = 0x60;
            frame[1] = 4;
            memset(frame + 2, 255, 6);
            memcpy(frame + 8, scanning.b + scanning.len - 4, 4);
            if (start(frame, 12, 0, true))
                state = R_AUTH;
            else
                finish();
        } else
            halt_card();
        break;
    case R_AUTH:
        frame[0] = 0x30;
        frame[1] = 4;
        append_crc(frame, 2);
        if (start(frame, 4, 0, false))
            state = R_READ;
        else
            finish();
        break;
    case R_READ:
        if (rx_len != 18 || rx_bits || !valid_crc(rx, 18)) {
            request_test = false;
            serial_send(0, "ERR CARD_READ\r\n");
            halt_card();
            break;
        }
        memcpy(original, rx, 16);
        if (!report_block("CARD_ORIGINAL", original)) {
            request_test = false;
            halt_card();
            break;
        }
        if (!test_write) {
            request_test = false;
            halt_card();
            break;
        }
        frame[0] = 0xa0;
        frame[1] = 4;
        append_crc(frame, 2);
        if (start(frame, 4, 0, false))
            state = R_WRITE_CMD;
        else
            finish();
        break;
    case R_WRITE_CMD:
        if (rx_len != 1 || rx_bits != 4 || (rx[0] & 15) != 10) {
            request_test = false;
            serial_send(0, "ERR CARD_ACK\r\n");
            halt_card();
            break;
        }
        memcpy(frame, test_data, 16);
        append_crc(frame, 16);
        if (start(frame, 18, 0, false))
            state = R_WRITE_DATA;
        else
            finish();
        break;
    case R_WRITE_DATA:
        if (rx_len != 1 || rx_bits != 4 || (rx[0] & 15) != 10) {
            request_test = false;
            serial_send(0, "ERR CARD_WRITE_UNKNOWN\r\n");
            halt_card();
            break;
        }
        frame[0] = 0x30;
        frame[1] = 4;
        append_crc(frame, 2);
        if (start(frame, 4, 0, false))
            state = R_VERIFY;
        else
            finish();
        break;
    case R_VERIFY:
        serial_send(0, rx_len == 18 && !rx_bits && valid_crc(rx, 18) && !memcmp(rx, test_data, 16)
                           ? "OK CARD_WRITE_VERIFY\r\n"
                           : "ERR CARD_VERIFY\r\n");
        if (rx_len >= 16)
            report_block("CARD_READBACK", rx);
        request_test = false;
        halt_card();
        break;
    default:
        finish();
        break;
    }
}
