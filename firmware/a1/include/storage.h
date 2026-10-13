#ifndef STORAGE_H
#define STORAGE_H
#include "config.h"
#define LOG_BASE 0x2000u
#define LOG_SECTORS 16u
#define LOG_SLOTS 63u
#define COMMIT_WORD 0xa55a5aa5u
enum { STORE_LOADING, STORE_FRESH, STORE_READY, STORE_BUSY, STORE_CORRUPT, STORE_OFFLINE };
typedef struct {
    uint8_t type, status, role;
    uint16_t id;
    Uid uid;
    int32_t delta;
    Settings settings;
} Transaction;
extern User users[USERS_MAX];
extern Settings settings;
extern uint8_t store_state;
extern uint32_t last_seq, boot_id;
void storage_init(void);
void storage_step(bool idle);
bool storage_format(void); /* caller requires local three-second gesture */
bool storage_begin(const Transaction *t);
bool storage_done(bool *success);
User *user_uid(const Uid *uid);
User *user_id(uint16_t id);
uint16_t storage_next_id(void);
uint32_t crc32(const void *p, uint32_t len);
void settings_defaults(Settings *s);
bool settings_valid(const Settings *s);
bool storage_log(uint16_t physical, uint8_t out[64]);
uint32_t get32(const uint8_t *p);
uint16_t get16(const uint8_t *p);
#endif
