#ifndef APP_H
#define APP_H
#include "config.h"
enum { MODE_DEPOSIT, MODE_QUERY, MODE_MANUAL, MODE_LINE, MODE_CONVENIENCE, MODE_MAINTENANCE };
enum { LID_IDLE, LID_OPENING, LID_WAIT, LID_BLOCK, LID_COMMIT, LID_DELAY, LID_CLOSING, LID_HELD };
typedef struct {
    uint32_t faults;
    uint8_t mode, lid;
    bool armed, moving;
    int16_t left, right;
    uint16_t servo;
    uint16_t selected;
    uint8_t stations, target;
    uint32_t max_loop_us;
} App;
extern App app;
void app_init(void);
void app_step(void);
void app_stop(uint32_t fault);
bool app_clear(void);
bool app_arm(void);
bool app_motion(int left, int right);
bool app_open(uint16_t id, bool convenience);
void app_command(uint8_t port, char *line);
void app_card(const Uid *uid);
void app_message(const char *s);
void app_confirm(void);
void app_back(void);
void app_ui_step(void);
void app_transaction_result(bool ok);
bool app_admin(void);
void app_admin_touch(void);
extern bool local_setup;
#endif
