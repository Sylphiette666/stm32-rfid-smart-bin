#include "devices.h"
#include "platform.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
Devices dev;
static uint32_t now;
static uint8_t regfile[64], out[64], in[64], out_n, in_n, in_pos, uid[10], uid_len;
static uint8_t card_block[16];
static bool card_present, expect_write;
static unsigned halts, writes;
static char serial_log[4096];
uint32_t millis(void) { return now; }
bool serial_send(uint8_t p, const char *s) {
    (void)p;
    if (strlen(serial_log) + strlen(s) >= sizeof(serial_log))
        return false;
    strcat(serial_log, s);
    return true;
}
static uint16_t crc(const uint8_t *p, unsigned n) {
    uint16_t c = 0x6363;
    while (n--) {
        uint8_t d = (uint8_t)(*p++ ^ c);
        d ^= (uint8_t)(d << 4);
        c = (uint16_t)((c >> 8) ^ ((uint16_t)d << 8) ^ ((uint16_t)d << 3) ^ (d >> 4));
    }
    return c;
}
static void crc_append(unsigned n) {
    uint16_t c = crc(in, n);
    in[n] = (uint8_t)c;
    in[n + 1] = (uint8_t)(c >> 8);
    in_n = (uint8_t)(n + 2);
}
static void transceive(void) {
    in_pos = 0;
    in_n = 0;
    regfile[6] = 0;
    regfile[12] = 0;
    regfile[4] = 0x30;
    if (!card_present) {
        regfile[4] = 1;
        return;
    }
    if (expect_write) {
        assert(out_n == 18);
        memcpy(card_block, out, 16);
        expect_write = false;
        in[0] = 10;
        in_n = 1;
        regfile[12] = 4;
        writes++;
        return;
    }
    if (out[0] == 0x52) {
        assert(out_n == 1 && (regfile[13] & 7) == 7);
        in[0] = 4;
        in[1] = 0;
        in_n = 2;
    } else if (out[0] == 0x93 || out[0] == 0x95 || out[0] == 0x97) {
        unsigned cascade = (out[0] - 0x93) / 2;
        unsigned offset = cascade * 3;
        bool more = uid_len - offset > 4;
        if (out[1] == 0x20) {
            if (more) {
                in[0] = 0x88;
                memcpy(in + 1, uid + offset, 3);
            } else
                memcpy(in, uid + offset, 4);
            in[4] = in[0] ^ in[1] ^ in[2] ^ in[3];
            in_n = 5;
        } else {
            assert(out[1] == 0x70 && out_n == 9);
            in[0] = more ? 4 : 8;
            crc_append(1);
        }
    } else if (out[0] == 0x50) {
        assert(out[1] == 0);
        halts++;
        regfile[4] = 1;
    } else if (out[0] == 0x30) {
        assert(out[1] == 4);
        memcpy(in, card_block, 16);
        crc_append(16);
    } else if (out[0] == 0xa0) {
        assert(out[1] == 4);
        expect_write = true;
        in[0] = 10;
        in_n = 1;
        regfile[12] = 4;
    } else
        assert(!"unexpected RFID command");
}
bool spi_transfer(bool flash, const uint8_t *tx, uint8_t *rx, uint16_t n) {
    assert(!flash && n == 2);
    unsigned r = (tx[0] & 0x7e) >> 1;
    if (tx[0] & 0x80) {
        uint8_t v;
        if (r == 9) {
            assert(in_pos < in_n);
            v = in[in_pos++];
        } else if (r == 10)
            v = in_n;
        else
            v = regfile[r];
        if (rx) {
            rx[0] = 0;
            rx[1] = v;
        }
    } else {
        uint8_t v = tx[1];
        if (r == 4)
            regfile[r] &= (uint8_t)~v;
        else if (r == 10 && (v & 0x80)) {
            out_n = 0;
            in_n = 0;
            in_pos = 0;
        } else if (r == 9) {
            assert(out_n < 64);
            out[out_n++] = v;
        } else {
            regfile[r] = v;
            if (r == 1 && v == 0x0f)
                regfile[1] = 0;
            if (r == 1 && v == 0x0e) {
                assert(out_n == 12 && out[0] == 0x60 && out[1] == 4);
                assert(!memcmp(out + 8, uid + uid_len - 4, 4));
                regfile[8] |= 8;
                regfile[4] = 0x10;
            }
            if (r == 13 && (v & 0x80))
                transceive();
        }
    }
    return true;
}
static unsigned run(unsigned ms, Uid *last) {
    unsigned events = 0;
    while (ms--) {
        now++;
        rfid_step();
        Uid u;
        if (rfid_event(&u)) {
            events++;
            if (last)
                *last = u;
        }
    }
    return events;
}
int main(void) {
    dev.mcp = true;
    regfile[0x37] = 0x92;
    for (unsigned len = 4; len <= 10; len += 3) {
        uid_len = (uint8_t)len;
        for (unsigned i = 0; i < len; i++)
            uid[i] = (uint8_t)(0x10 + i);
        card_present = true;
        rfid_init();
        Uid last;
        assert(run(1000, &last) == 1);
        assert(last.len == len && !memcmp(last.b, uid, len));
        assert(run(10000, 0) == 0);
        assert(halts > 0);
        card_present = false;
        assert(run(700, 0) == 0);
        card_present = true;
        assert(run(500, 0) == 1);
    }
    uint8_t data[16];
    for (unsigned i = 0; i < 16; i++)
        data[i] = (uint8_t)i;
    assert(rfid_card_test(true, data));
    assert(run(1000, 0) == 0);
    assert(writes == 1 && !memcmp(data, card_block, 16));
    assert(strstr(serial_log, "CARD_ORIGINAL") && strstr(serial_log, "OK CARD_WRITE_VERIFY"));
    assert(rfid_card_test(false, 0));
    run(1000, 0);
    assert(writes == 1);
    puts("PASS RFID: 4/7/10-byte cascade, CRC, 10-second presence dedup, WUPA/HALT, block-4 "
         "authentication/write/readback, no business event during card test");
    return 0;
}
