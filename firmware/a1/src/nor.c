#include "devices.h"
#include "platform.h"
#include <string.h>
uint32_t nor_capacity;
static uint32_t issued, deadline;
static bool busy;
static uint8_t tx[260], rx[260];
static bool status(uint8_t *s) {
    uint8_t cmd[2] = {5, 255}, r[2];
    if (!spi_transfer(true, cmd, r, 2))
        return false;
    *s = r[1];
    return true;
}
bool nor_init(void) {
    uint8_t cmd[4] = {0x9f, 0xff, 0xff, 0xff}, r[4];
    busy = false;
    nor_capacity = 0;
    if (!spi_transfer(true, cmd, r, 4))
        return false;
    dev.jedec = ((uint32_t)r[1] << 16) | ((uint32_t)r[2] << 8) |
                r[3]; /* Explicit allowlist: Winbond W25Q16/32/64/128, 3.3 V JV/FV family. */
    if (r[1] != 0xef || r[2] != 0x40 || r[3] < 0x15 || r[3] > 0x18)
        return false;
    nor_capacity = 1u << r[3];
    uint8_t s;
    return status(&s) && !(s & 1);
}
bool nor_read(uint32_t a, void *p, uint16_t n) {
    if (n > 256 || !nor_capacity || a > nor_capacity || n > nor_capacity - a)
        return false;
    tx[0] = 3;
    tx[1] = (uint8_t)(a >> 16);
    tx[2] = (uint8_t)(a >> 8);
    tx[3] = (uint8_t)a;
    memset(tx + 4, 255, n);
    if (!spi_transfer(true, tx, rx, n + 4))
        return false;
    memcpy(p, rx + 4, n);
    return true;
}
static bool enable(void) {
    uint8_t c = 6, s;
    if (busy || !status(&s) || (s & 1) || !spi_transfer(true, &c, 0, 1) || !status(&s) || !(s & 2))
        return false;
    return true;
}
bool nor_program(uint32_t a, const void *p, uint16_t n) {
    if (!n || n > 256 || ((a & 255) + n) > 256 || a >= nor_capacity || n > nor_capacity - a ||
        !enable())
        return false;
    tx[0] = 2;
    tx[1] = (uint8_t)(a >> 16);
    tx[2] = (uint8_t)(a >> 8);
    tx[3] = (uint8_t)a;
    memcpy(tx + 4, p, n);
    if (!spi_transfer(true, tx, 0, n + 4))
        return false;
    busy = true;
    issued = millis();
    deadline = 20;
    return true;
}
bool nor_erase(uint32_t a) {
    if ((a & 4095) || a >= nor_capacity || !enable())
        return false;
    uint8_t cmd[4] = {0x20, (uint8_t)(a >> 16), (uint8_t)(a >> 8), (uint8_t)a};
    if (!spi_transfer(true, cmd, 0, 4))
        return false;
    busy = true;
    issued = millis();
    deadline = 3000;
    return true;
}
int nor_poll(void) {
    uint8_t s;
    if (!busy)
        return 1;
    if (!status(&s))
        return -1;
    if (!(s & 1)) {
        busy = false;
        return 1;
    }
    if (elapsed(millis(), issued, deadline)) {
        busy = false;
        return -1;
    }
    return 0;
}
