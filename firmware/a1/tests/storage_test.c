#include "storage.h"
#include "devices.h"
#include "platform.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
Devices dev;
static uint8_t flash[0x13000], backup[0x13000];
static uint32_t now;
static int cut_after = -1, write_count, partial = -1;
static bool power_lost;
uint32_t millis(void) { return now; }
bool nor_read(uint32_t a, void *p, uint16_t n) {
    assert(a + n <= sizeof(flash));
    if (power_lost)
        return false;
    memcpy(p, flash + a, n);
    return true;
}
bool nor_program(uint32_t a, const void *p, uint16_t n) {
    assert(a + n <= sizeof(flash));
    assert((a & 255) + n <= 256);
    if (power_lost)
        return false;
    unsigned bytes = n;
    if (cut_after == write_count && partial >= 0 && partial < (int)n)
        bytes = (unsigned)partial;
    for (unsigned i = 0; i < bytes; i++) {
        uint8_t v = ((const uint8_t *)p)[i];
        assert((flash[a + i] & v) == v);
        flash[a + i] &= v;
    }
    if (cut_after == write_count++) {
        power_lost = true;
        return false;
    }
    return true;
}
bool nor_erase(uint32_t a) {
    assert(!(a & 4095) && a + 4096 <= sizeof(flash));
    if (power_lost)
        return false;
    unsigned n = 4096;
    if (cut_after == write_count && partial >= 0 && partial < 4096)
        n = (unsigned)partial;
    memset(flash + a, 255, n);
    if (cut_after == write_count++) {
        power_lost = true;
        return false;
    }
    return true;
}
int nor_poll(void) { return power_lost ? -1 : 1; }
static void recover(void) {
    power_lost = false;
    cut_after = -1;
    partial = -1;
    dev.nor = true;
    storage_init();
    for (unsigned i = 0; i < 3000 && store_state == STORE_LOADING; i++) {
        now++;
        storage_step(true);
    }
    assert(store_state != STORE_LOADING);
}
static void settle(void) {
    for (unsigned i = 0; i < 3000 && store_state == STORE_BUSY; i++) {
        now++;
        storage_step(true);
    }
    assert(store_state != STORE_BUSY);
}
static bool transaction(Transaction *t) {
    if (!storage_begin(t))
        return false;
    settle();
    bool ok = false;
    assert(storage_done(&ok));
    return ok;
}
static Transaction registration(unsigned id, unsigned role, unsigned len) {
    Transaction t = {0};
    t.type = TX_REGISTER;
    t.id = (uint16_t)id;
    t.uid.len = (uint8_t)len;
    for (unsigned i = 0; i < len; i++)
        t.uid.b[i] = (uint8_t)(id + i * 3);
    t.role = (uint8_t)role;
    t.status = USER_ACTIVE;
    return t;
}
static void fresh(void) {
    memset(flash, 255, sizeof(flash));
    recover();
    assert(store_state == STORE_FRESH);
    assert(storage_format());
    settle();
    assert(store_state == STORE_READY);
}
int main(void) {
    assert(crc32("123456789", 9) == 0xcbf43926);
    fresh();
    Transaction t = registration(1, ROLE_ADMIN, 4);
    assert(transaction(&t));
    t = registration(2, ROLE_USER, 7);
    assert(transaction(&t));
    t = registration(3, ROLE_USER, 10);
    assert(transaction(&t));
    t = (Transaction){0};
    t.type = TX_STATUS;
    t.id = 1;
    t.status = USER_DELETED;
    assert(!storage_begin(&t));
    t = (Transaction){0};
    t.type = TX_DEPOSIT;
    t.id = 2;
    t.delta = 1;
    assert(transaction(&t));
    assert(users[1].points == 1);
    recover();
    assert(store_state == STORE_READY && users[1].points == 1 && users[1].uid.len == 7);
    memcpy(backup, flash, sizeof(flash));
    unsigned cuts = 0;
    for (int cut = 0; cut < 3; cut++)
        for (int bytes = 0; bytes <= 64; bytes++) {
            memcpy(flash, backup, sizeof(flash));
            recover();
            write_count = 0;
            cut_after = cut;
            partial = bytes;
            assert(storage_begin(&t));
            settle();
            recover();
            assert(store_state == STORE_READY);
            assert(users[1].points == 1 || users[1].points == 2);
            assert(users[1].count == users[1].points);
            cuts++;
        }
    memcpy(flash, backup, sizeof(flash));
    recover();
    for (unsigned i = 0; i < 1200; i++)
        assert(transaction(&t));
    assert(users[1].points == 1201);
    recover();
    assert(store_state == STORE_READY && users[1].points == 1201 && users[1].count == 1201);
    t.type = TX_REDEEM;
    t.delta = -5;
    assert(transaction(&t));
    assert(users[1].points == 1196);
    recover();
    assert(users[1].points == 1196);
    while (last_seq % 256) {
        t.type = TX_DEPOSIT;
        t.delta = 1;
        assert(transaction(&t));
    }
    uint32_t baseline = users[1].points;
    memcpy(backup, flash, sizeof(flash));
    /* Cut every erase/program stage, including partial snapshot, commit and log writes. */
    for (int cut = 0; cut < 15; cut++)
        for (int bytes = 0; bytes <= 256; bytes += 17) {
            memcpy(flash, backup, sizeof(flash));
            recover();
            write_count = 0;
            cut_after = cut;
            partial = bytes;
            assert(storage_begin(&t));
            settle();
            recover();
            assert(store_state == STORE_READY);
            assert(users[1].points == baseline || users[1].points == baseline + 1);
            cuts++;
        }
    memcpy(flash, backup, sizeof(flash));
    recover();
    /* Reclaim an old sector after a full ring, with cuts during erase/header. */
    while (last_seq % 63)
        assert(transaction(&t));
    baseline = users[1].points;
    memcpy(backup, flash, sizeof(flash));
    for (int cut = 0; cut < 6; cut++) {
        const int tears[] = {0, 1, 4, 32, 60, 63, 64, 127, 256, 2048, 4096};
        for (unsigned j = 0; j < sizeof(tears) / sizeof(tears[0]); j++) {
            memcpy(flash, backup, sizeof(flash));
            recover();
            write_count = 0;
            cut_after = cut;
            partial = tears[j];
            assert(storage_begin(&t));
            settle();
            recover();
            assert(store_state == STORE_READY);
            assert(users[1].points == baseline || users[1].points == baseline + 1);
            cuts++;
        }
    }
    memcpy(flash, backup, sizeof(flash));
    recover();
    t = (Transaction){0};
    t.type = TX_CONFIG;
    t.settings = settings;
    t.settings.close_us = 1400;
    t.settings.open_us = 1700;
    t.settings.calibrated = 1;
    assert(transaction(&t));
    recover();
    assert(settings.close_us == 1400 && settings.open_us == 1700 && settings.calibrated);
    for (unsigned id = 4; id <= 64; id++) {
        t = registration(id, ROLE_USER, id % 3 == 0 ? 10 : id % 3 == 1 ? 4 : 7);
        assert(transaction(&t));
    }
    assert(storage_next_id() == 0);
    t = registration(65, ROLE_USER, 4);
    assert(!storage_begin(&t));
    recover();
    assert(users[63].id == 64);
    t = (Transaction){0};
    t.type = TX_STATUS;
    t.id = 2;
    t.status = USER_LOST;
    assert(transaction(&t));
    t.type = TX_DEPOSIT;
    t.delta = 1;
    assert(!storage_begin(&t));
    uint32_t saved_balance = users[1].points;
    t = (Transaction){0};
    t.type = TX_ADMIN_RECOVER;
    t.id = 2;
    assert(transaction(&t));
    recover();
    assert(users[1].points == saved_balance && users[1].role == ROLE_ADMIN &&
           users[1].status == USER_ACTIVE);
    /* Unknown nonblank media must never be silently treated as a fresh ledger. */
    memset(flash, 255, sizeof(flash));
    flash[0x8000] = 0;
    recover();
    assert(store_state == STORE_CORRUPT);
    assert(!storage_format());
    printf("PASS storage: CRC, 4/7/10-byte UID, last-admin guard, %u power cuts, >1008 "
           "transactions, rollover, config, capacity, lost-card, corrupt-media\n",
           cuts);
    return 0;
}
