#ifndef DEVICES_H
#define DEVICES_H
#include "config.h"
typedef struct {
    bool mcp, mpu, oled, rfid, nor, adc_valid, dht_valid, range_valid, full, full_unknown, light;
    bool audio_failed;
    uint8_t mcp_a, mcp_b;
    uint16_t vbat_mv, light_raw, range_mm;
    int16_t roll10, pitch10, temp10;
    uint16_t humidity10;
    uint32_t mcp_at, mpu_at, adc_at, dht_at, range_at;
    uint32_t jedec;
    uint8_t rfid_version;
} Devices;
extern Devices dev;
void devices_init(void);
void devices_step(bool moving, bool lid_closed, bool idle, bool maintenance);
bool mcp_update(uint8_t mask, uint8_t value);
bool mcp_direction(uint8_t value);
void display_text(uint8_t row, const char *text);
void display_step(void);
void beep(uint8_t count);
void audio_queue(uint8_t track, bool priority);
void rfid_init(void);
void rfid_step(void);
bool rfid_event(Uid *uid);
bool rfid_card_test(bool write, const uint8_t data[16]);
bool nor_init(void);
bool nor_read(uint32_t addr, void *data, uint16_t len);
bool nor_program(uint32_t addr, const void *data, uint16_t len);
bool nor_erase(uint32_t addr);
int nor_poll(void); /* 0 busy, 1 done, -1 error */
extern uint32_t nor_capacity;
#endif
