#include "storage.h"
#include "devices.h"
#include "platform.h"
#include <string.h>
#include <limits.h>
#define SNAP_SIZE 2304u
#define SNAP_MAGIC 0x31414253u
#define LOG_MAGIC 0x31474c53u
#define TX_MAGIC 0x31585453u
User users[USERS_MAX];
Settings settings;
uint8_t store_state;
uint32_t last_seq, boot_id;
static uint8_t image[SNAP_SIZE], record[64], verify[256];
static uint32_t generation, snap_seq, sector_seq[16], sector_last[16];
static uint16_t offset, slot, scan_slot;
static uint8_t active_snap, sector, scan_sector, phase, next_phase;
static uint32_t address, scan_addr, replay_seq;
static uint16_t seen_sectors;
static bool have_snap, all_blank, result_pending, result_ok, pending_tx, formatting;
static Transaction txn;
enum {
    P_SNAP_READ = 1,
    P_BLANK_SCAN,
    P_HEADERS,
    P_PICK_SECTOR,
    P_REPLAY,
    P_IDLE,
    P_SECTOR_ERASE,
    P_SECTOR_HEADER,
    P_TX_BODY,
    P_TX_VERIFY,
    P_TX_COMMIT,
    P_TX_APPLY,
    P_SNAP_ERASE,
    P_SNAP_BODY,
    P_SNAP_VERIFY,
    P_SNAP_COMMIT,
    P_SNAP_FINISH,
    P_WAIT
};
uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void put16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}
static void put32(uint8_t *p, uint32_t v) {
    for (unsigned i = 0; i < 4; i++)
        p[i] = (uint8_t)(v >> (8 * i));
}
uint32_t crc32(const void *data, uint32_t n) {
    const uint8_t *p = data;
    uint32_t c = 0xffffffff;
    while (n--) {
        c ^= *p++;
        for (unsigned k = 0; k < 8; k++)
            c = (c >> 1) ^ (0xedb88320u & ((uint32_t)-(int32_t)(c & 1)));
    }
    return c ^ 0xffffffff;
}
static bool blank(const uint8_t *p, unsigned n) {
    while (n--)
        if (*p++ != 255)
            return false;
    return true;
}
static bool uid_valid(const Uid *u) { return u->len == 4 || u->len == 7 || u->len == 10; }
static bool uid_equal(const Uid *a, const Uid *b) {
    return a->len == b->len && memcmp(a->b, b->b, a->len) == 0;
}
User *user_id(uint16_t id) {
    return id && id <= USERS_MAX && users[id - 1].id == id ? &users[id - 1] : 0;
}
User *user_uid(const Uid *uid) {
    if (!uid_valid(uid))
        return 0;
    for (unsigned i = 0; i < USERS_MAX; i++)
        if (users[i].id && uid_equal(&users[i].uid, uid))
            return &users[i];
    return 0;
}
uint16_t storage_next_id(void) {
    for (unsigned i = 0; i < USERS_MAX; i++)
        if (!users[i].id)
            return (uint16_t)(i + 1);
    return 0;
}
void settings_defaults(Settings *s) {
    memset(s, 0, sizeof(*s));
    s->close_us = 1500;
    s->open_us = 1500;
    s->full_mm = 65;
    s->clear_mm = 85;
    s->pwm_max = 25;
    s->light_on = LIGHT_DARK_HIGH ? 2700 : 2000;
    s->light_off = LIGHT_DARK_HIGH ? 2000 : 2700;
    s->adc_scale = 1000;
}
bool settings_valid(const Settings *s) {
    return s->close_us >= 900 && s->close_us <= 2100 && s->open_us >= 900 && s->open_us <= 2100 &&
           s->full_mm >= 20 && s->full_mm < s->clear_mm && s->clear_mm <= 1000 && s->pwm_max >= 1 &&
           s->pwm_max <= 40 && s->adc_scale >= 800 && s->adc_scale <= 1200 && s->light_on <= 4095 &&
           s->light_off <= 4095 && s->light_on != s->light_off && s->calibrated <= 1 &&
           s->mute <= 1 && s->roll_zero >= -1800 && s->roll_zero <= 1800 && s->pitch_zero >= -900 &&
           s->pitch_zero <= 900;
}
static void config_put(uint8_t *p, const Settings *s) {
    put16(p, s->close_us);
    put16(p + 2, s->open_us);
    put16(p + 4, s->full_mm);
    put16(p + 6, s->clear_mm);
    put16(p + 8, s->pwm_max);
    put16(p + 10, s->light_on);
    put16(p + 12, s->light_off);
    put16(p + 14, s->adc_scale);
    put16(p + 16, (uint16_t)s->roll_zero);
    put16(p + 18, (uint16_t)s->pitch_zero);
    p[20] = s->calibrated;
    p[21] = s->mute;
}
static void config_get(Settings *s, const uint8_t *p) {
    s->close_us = get16(p);
    s->open_us = get16(p + 2);
    s->full_mm = get16(p + 4);
    s->clear_mm = get16(p + 6);
    s->pwm_max = get16(p + 8);
    s->light_on = get16(p + 10);
    s->light_off = get16(p + 12);
    s->adc_scale = get16(p + 14);
    s->roll_zero = (int16_t)get16(p + 16);
    s->pitch_zero = (int16_t)get16(p + 18);
    s->calibrated = p[20];
    s->mute = p[21];
}
static void user_put(uint8_t *p, const User *u) {
    memset(p, 0, 32);
    put16(p, u->id);
    p[2] = u->uid.len;
    p[3] = u->role;
    p[4] = u->status;
    memcpy(p + 5, u->uid.b, 10);
    put32(p + 16, u->points);
    put32(p + 20, u->count);
}
static bool user_get(User *u, const uint8_t *p, unsigned index) {
    memset(u, 0, sizeof(*u));
    u->id = get16(p);
    u->uid.len = p[2];
    u->role = p[3];
    u->status = p[4];
    memcpy(u->uid.b, p + 5, 10);
    u->points = get32(p + 16);
    u->count = get32(p + 20);
    return !u->id || (u->id == index + 1 && uid_valid(&u->uid) && u->role <= 1 && u->status >= 1 &&
                      u->status <= 3 && u->points <= POINTS_MAX);
}
static void fail(void) {
    store_state = STORE_CORRUPT;
    phase = P_IDLE;
    if (pending_tx) {
        result_pending = true;
        result_ok = false;
        pending_tx = false;
    }
}
static void wait_for(uint8_t next) {
    next_phase = next;
    phase = P_WAIT;
}
static bool snapshot_valid(void) {
    return get32(image) == SNAP_MAGIC && get32(image + 4) == 1 && get32(image + 8) == SNAP_SIZE &&
           get32(image + 2300) == COMMIT_WORD && crc32(image, 2296) == get32(image + 2296);
}
static bool snapshot_load(void) {
    Settings s;
    config_get(&s, image + 32);
    if (!settings_valid(&s))
        return false;
    for (unsigned i = 0; i < USERS_MAX; i++) {
        User u;
        if (!user_get(&u, image + 64 + 32 * i, i))
            return false;
    }
    for (unsigned i = 0; i < USERS_MAX; i++)
        user_get(&users[i], image + 64 + 32 * i, i);
    settings = s;
    last_seq = get32(image + 16);
    boot_id = get32(image + 20);
    generation = get32(image + 12);
    snap_seq = last_seq;
    return true;
}
static void snapshot_prepare(void) {
    memset(image, 0xff, sizeof(image));
    put32(image, SNAP_MAGIC);
    put32(image + 4, 1);
    put32(image + 8, SNAP_SIZE);
    put32(image + 12, generation + 1);
    put32(image + 16, last_seq);
    put32(image + 20, boot_id);
    config_put(image + 32, &settings);
    for (unsigned i = 0; i < USERS_MAX; i++)
        user_put(image + 64 + 32 * i, &users[i]);
    put32(image + 2296, crc32(image, 2296));
    address = (uint32_t)(1 - active_snap) * 4096;
    phase = P_SNAP_ERASE;
    store_state = STORE_BUSY;
}
static bool apply(const uint8_t *r) {
    uint32_t seq = get32(r + 4);
    if (seq != last_seq + 1 || get32(r + 8) != seq)
        return false;
    uint8_t type = r[14];
    uint16_t id = get16(r + 12);
    User *u = user_id(id);
    if (type == TX_REGISTER) {
        Uid uid = {0};
        uid.len = r[40];
        memcpy(uid.b, r + 41, 10);
        if (!uid_valid(&uid) || !id || id > USERS_MAX || u || user_uid(&uid) || r[51] > 1 ||
            r[52] != USER_ACTIVE || get32(r + 20) || get32(r + 24))
            return false;
        u = &users[id - 1];
        memset(u, 0, sizeof(*u));
        u->id = id;
        u->uid = uid;
        u->role = r[51];
        u->status = r[52];
    } else if (type == TX_STATUS) {
        if (!u || r[52] < 1 || r[52] > 3 || get32(r + 20) != u->points || get32(r + 24) != u->count)
            return false;
        u->status = r[52];
    } else if (type == TX_DEPOSIT || type == TX_REDEEM) {
        int32_t delta = (int32_t)get32(r + 16);
        if (!u || u->status != USER_ACTIVE)
            return false;
        if (type == TX_DEPOSIT && (delta != 1 || u->count == UINT32_MAX))
            return false;
        if (type == TX_REDEEM && (delta != -5 && delta != -10))
            return false;
        int64_t next = (int64_t)u->points + delta;
        if (next < 0 || next > POINTS_MAX || get32(r + 20) != (uint32_t)next ||
            get32(r + 24) != u->count + (type == TX_DEPOSIT))
            return false;
        u->points = (uint32_t)next;
        u->count = get32(r + 24);
    } else if (type == TX_CONFIG) {
        Settings s;
        config_get(&s, r + 16);
        if (!settings_valid(&s))
            return false;
        settings = s;
    } else if (type == TX_BOOT) {
        if (get32(r + 28) != boot_id + 1)
            return false;
        boot_id = get32(r + 28);
    } else if (type == TX_ADMIN_RECOVER) {
        if (!u || get32(r + 20) != u->points || get32(r + 24) != u->count)
            return false;
        u->role = ROLE_ADMIN;
        u->status = USER_ACTIVE;
    } else
        return false;
    last_seq = seq;
    return true;
}
static void encode_tx(void) {
    memset(record, 0, 64);
    put32(record, TX_MAGIC);
    put32(record + 4, last_seq + 1);
    put32(record + 8, last_seq + 1);
    put16(record + 12, txn.id);
    record[14] = txn.type;
    User *u = user_id(txn.id);
    put32(record + 16, (uint32_t)txn.delta);
    put32(record + 20, u ? (uint32_t)((int64_t)u->points + txn.delta) : 0);
    put32(record + 24, u ? u->count + (txn.type == TX_DEPOSIT) : 0);
    put32(record + 28, boot_id + (txn.type == TX_BOOT));
    put32(record + 32, millis());
    record[40] = txn.uid.len;
    memcpy(record + 41, txn.uid.b, 10);
    record[51] = txn.role;
    record[52] = txn.status;
    if (txn.type == TX_CONFIG)
        config_put(record + 16, &txn.settings);
    put32(record + 56, crc32(record, 56));
    put32(record + 60, COMMIT_WORD);
}
void storage_init(void) {
    memset(users, 0, sizeof(users));
    settings_defaults(&settings);
    memset(sector_seq, 0, sizeof(sector_seq));
    memset(sector_last, 0, sizeof(sector_last));
    last_seq = boot_id = generation = snap_seq = 0;
    offset = 0;
    active_snap = 0;
    scan_sector = 0;
    scan_slot = 0;
    seen_sectors = 0;
    have_snap = false;
    all_blank = true;
    pending_tx = result_pending = formatting = false;
    store_state = dev.nor ? STORE_LOADING : STORE_OFFLINE;
    phase = P_SNAP_READ;
}
bool storage_format(void) {
    if (store_state != STORE_FRESH)
        return false;
    formatting = true;
    active_snap = 1;
    snapshot_prepare();
    return true;
}
bool storage_begin(const Transaction *t) {
    if (store_state != STORE_READY || pending_tx || result_pending || last_seq >= 0xffffff00u)
        return false;
    User *u = user_id(t->id);
    if (t->type == TX_REGISTER) {
        if (t->id != storage_next_id() || !t->id || !uid_valid(&t->uid) || user_uid(&t->uid) ||
            t->role > 1 || t->status != USER_ACTIVE)
            return false;
    } else if (t->type == TX_STATUS) {
        if (!u || t->status < 1 || t->status > 3)
            return false;
        if (u->role == ROLE_ADMIN && u->status == USER_ACTIVE && t->status != USER_ACTIVE) {
            unsigned n = 0;
            for (unsigned i = 0; i < USERS_MAX; i++)
                if (users[i].id && users[i].role == ROLE_ADMIN && users[i].status == USER_ACTIVE)
                    n++;
            if (n <= 1)
                return false;
        }
    } else if (t->type == TX_DEPOSIT || t->type == TX_REDEEM) {
        if (!u || u->status != USER_ACTIVE)
            return false;
        if ((t->type == TX_DEPOSIT && (t->delta != 1 || u->count == UINT32_MAX)) ||
            (t->type == TX_REDEEM && t->delta != -5 && t->delta != -10))
            return false;
        int64_t p = (int64_t)u->points + t->delta;
        if (p < 0 || p > POINTS_MAX)
            return false;
    } else if (t->type == TX_CONFIG) {
        if (!settings_valid(&t->settings))
            return false;
    } else if (t->type == TX_BOOT) {
        if (boot_id >= 0xffffff00u)
            return false;
    } else if (t->type == TX_ADMIN_RECOVER) {
        if (!u)
            return false;
    } else
        return false;
    txn = *t;
    pending_tx = true;
    store_state = STORE_BUSY;
    phase = P_IDLE;
    return true;
}
bool storage_done(bool *ok) {
    if (!result_pending)
        return false;
    *ok = result_ok;
    result_pending = false;
    return true;
}
bool storage_log(uint16_t index, uint8_t out[64]) {
    if (index >= 16 * 63 || store_state != STORE_READY)
        return false;
    uint32_t a = LOG_BASE + (index / 63) * 4096 + 64 + (index % 63) * 64;
    if (!nor_read(a, out, 64))
        return false;
    return get32(out) == TX_MAGIC && get32(out + 60) == COMMIT_WORD &&
           crc32(out, 56) == get32(out + 56);
}
void storage_step(bool idle) {
    if (store_state == STORE_OFFLINE || store_state == STORE_CORRUPT || store_state == STORE_FRESH)
        return;
    if (phase == P_WAIT) {
        int p = nor_poll();
        if (p < 0)
            fail();
        else if (p > 0)
            phase = next_phase;
        return;
    }
    switch (phase) {
    case P_SNAP_READ:
        if (!nor_read((uint32_t)scan_sector * 4096 + offset, image + offset, 256)) {
            fail();
            break;
        }
        offset += 256;
        if (offset < SNAP_SIZE)
            break;
        if (snapshot_valid() && (!have_snap || get32(image + 12) > generation)) {
            if (!snapshot_load()) {
                fail();
                break;
            }
            have_snap = true;
            active_snap = scan_sector;
        }
        offset = 0;
        if (++scan_sector < 2)
            break;
        scan_sector = 0;
        if (!have_snap) {
            scan_addr = 0;
            phase = P_BLANK_SCAN;
        } else
            phase = P_HEADERS;
        break;
    case P_BLANK_SCAN:
        if (!nor_read(scan_addr, verify, 256)) {
            fail();
            break;
        }
        if (!blank(verify, 256)) {
            fail();
            break;
        }
        scan_addr += 256;
        if (scan_addr >= 0x12000)
            store_state = STORE_FRESH;
        break;
    case P_HEADERS:
        if (!nor_read(LOG_BASE + scan_sector * 4096, verify, 64)) {
            fail();
            break;
        }
        if (get32(verify) == LOG_MAGIC && get32(verify + 60) == COMMIT_WORD &&
            get32(verify + 8) == crc32(verify, 8))
            sector_seq[scan_sector] = get32(verify + 4);
        if (++scan_sector == 16) {
            phase = P_PICK_SECTOR;
            seen_sectors = 0;
            sector = 15;
            slot = 63;
            replay_seq = snap_seq;
        }
        break;
    case P_PICK_SECTOR: {
        uint32_t min = UINT32_MAX;
        int pick = -1;
        for (unsigned i = 0; i < 16; i++)
            if (!(seen_sectors & BIT(i)) && sector_seq[i] && sector_seq[i] < min) {
                min = sector_seq[i];
                pick = (int)i;
            }
        if (pick < 0) {
            phase = P_IDLE;
            store_state = STORE_READY;
            break;
        }
        scan_sector = (uint8_t)pick;
        seen_sectors |= (uint16_t)BIT(pick);
        scan_slot = 0;
        sector = scan_sector;
        slot = 0;
        phase = P_REPLAY;
        break;
    }
    case P_REPLAY:
        if (!nor_read(LOG_BASE + scan_sector * 4096 + 64 + scan_slot * 64, record, 64)) {
            fail();
            break;
        }
        if (!blank(record, 64))
            slot = scan_slot + 1;
        if (get32(record + 60) == COMMIT_WORD) {
            if (get32(record) != TX_MAGIC || crc32(record, 56) != get32(record + 56)) {
                fail();
                break;
            }
            uint32_t seq = get32(record + 4);
            if (seq < sector_seq[scan_sector] || seq <= sector_last[scan_sector]) {
                fail();
                break;
            }
            sector_last[scan_sector] = seq;
            if (seq > snap_seq) {
                if (seq != replay_seq + 1 || !apply(record)) {
                    fail();
                    break;
                }
                replay_seq = seq;
            }
        }
        if (++scan_slot >= 63)
            phase = P_PICK_SECTOR;
        break;
    case P_IDLE:
        if (pending_tx) {
            if (last_seq - snap_seq >= 256 ||
                (slot >= 63 && sector_last[(sector + 1) % 16] > snap_seq)) {
                if (!idle)
                    return;
                snapshot_prepare();
                break;
            }
            encode_tx();
            if (slot >= 63) {
                sector = (sector + 1) % 16;
                slot = 0;
                phase = P_SECTOR_ERASE;
            } else {
                address = LOG_BASE + sector * 4096 + 64 + slot * 64;
                phase = P_TX_BODY;
            }
        }
        break;
    case P_SECTOR_ERASE:
        if (!idle)
            return;
        if (!nor_erase(LOG_BASE + sector * 4096)) {
            fail();
            break;
        }
        wait_for(P_SECTOR_HEADER);
        break;
    case P_SECTOR_HEADER:
        memset(verify, 0xff, 64);
        put32(verify, LOG_MAGIC);
        put32(verify + 4, last_seq + 1);
        put32(verify + 8, crc32(verify, 8));
        put32(verify + 60, COMMIT_WORD);
        if (!nor_program(LOG_BASE + sector * 4096, verify, 64)) {
            fail();
            break;
        }
        sector_seq[sector] = last_seq + 1;
        sector_last[sector] = 0;
        address = LOG_BASE + sector * 4096 + 64;
        wait_for(P_TX_BODY);
        break;
    case P_TX_BODY:
        if (!nor_read(LOG_BASE + sector * 4096, verify, 64) || get32(verify) != LOG_MAGIC ||
            get32(verify + 8) != crc32(verify, 8) || get32(verify + 60) != COMMIT_WORD) {
            fail();
            break;
        }
        if (!nor_program(address, record, 60)) {
            fail();
            break;
        }
        wait_for(P_TX_VERIFY);
        break;
    case P_TX_VERIFY:
        if (!nor_read(address, verify, 64) || memcmp(verify, record, 60) ||
            get32(verify + 60) != 0xffffffff) {
            fail();
            break;
        }
        phase = P_TX_COMMIT;
        break;
    case P_TX_COMMIT:
        if (!nor_program(address + 60, record + 60, 4)) {
            fail();
            break;
        }
        wait_for(P_TX_APPLY);
        break;
    case P_TX_APPLY:
        if (!nor_read(address, verify, 64) || memcmp(record, verify, 64) || !apply(record)) {
            fail();
            break;
        }
        sector_last[sector] = last_seq;
        slot++;
        pending_tx = false;
        result_pending = true;
        result_ok = true;
        store_state = STORE_READY;
        phase = P_IDLE;
        break;
    case P_SNAP_ERASE:
        if (!nor_erase(address)) {
            fail();
            break;
        }
        offset = 0;
        wait_for(P_SNAP_BODY);
        break;
    case P_SNAP_BODY: {
        uint16_t n = (uint16_t)(2300 - offset);
        if (n > 256)
            n = 256;
        if (!nor_program(address + offset, image + offset, n)) {
            fail();
            break;
        }
        offset += n;
        wait_for(offset == 2300 ? P_SNAP_VERIFY : P_SNAP_BODY);
        if (offset == 2300)
            offset = 0;
        break;
    }
    case P_SNAP_VERIFY: {
        uint16_t n = (uint16_t)(2300 - offset);
        if (n > 256)
            n = 256;
        if (!nor_read(address + offset, verify, n) || memcmp(verify, image + offset, n)) {
            fail();
            break;
        }
        offset += n;
        if (offset == 2300)
            phase = P_SNAP_COMMIT;
        break;
    }
    case P_SNAP_COMMIT:
        put32(verify, COMMIT_WORD);
        if (!nor_program(address + 2300, verify, 4)) {
            fail();
            break;
        }
        wait_for(P_SNAP_FINISH);
        break;
    case P_SNAP_FINISH:
        if (!nor_read(address + 2300, verify, 4) || get32(verify) != COMMIT_WORD) {
            fail();
            break;
        }
        active_snap = 1 - active_snap;
        generation++;
        snap_seq = last_seq;
        have_snap = true;
        if (formatting) {
            formatting = false;
            sector = 15;
            slot = 63;
        }
        store_state = pending_tx ? STORE_BUSY : STORE_READY;
        phase = P_IDLE;
        break;
    default:
        fail();
        break;
    }
}
