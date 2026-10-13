#ifndef CONFIG_H
#define CONFIG_H
#include <stdint.h>
#include <stdbool.h>
#define FW_VERSION "A1-0.1.0"
/* Commission every physical input before enabling actuators. */
#define HSE_HZ 8000000u
#if HSE_HZ != 8000000u
#error "Recalculate and update platform.c clock configuration for another crystal"
#endif
#define OLED_ADDR 0x3c
#define OLED_SH1106 0
#define MPU_ADDR 0x68
#define BUZZER_ACTIVE_LOW 0
#define BUZZER_PASSIVE 0
#define MOTOR_LEFT_INVERT 0
#define MOTOR_RIGHT_INVERT 0
#define ENCODER_EDGES 4
#define BEAM_ACTIVE_HIGH 0
#define OBSTACLE_ACTIVE_HIGH 0
#define LID_CLOSED_HIGH 0
#define LINE_ACTIVE_HIGH 0
#define NEAR_ACTIVE_HIGH 0
#define AUDIO_BUSY_HIGH 0
#define LIGHT_DARK_HIGH 1
#define LIGHT_DIGITAL 0
#define ENABLE_WATCHDOG 0
#define ENABLE_TEST_COMMANDS 0
#define USERS_MAX 64
#define POINTS_MAX 999999u
#define BIT(n) (1u << (n))
static inline bool elapsed(uint32_t now, uint32_t then, uint32_t period) {
    return (uint32_t)(now - then) >= period;
}
typedef struct {
    uint8_t len, b[10];
} Uid;
typedef struct {
    uint16_t id;
    Uid uid;
    uint8_t role, status;
    uint32_t points, count;
} User;
enum { USER_ACTIVE = 1, USER_LOST = 2, USER_DELETED = 3 };
enum { ROLE_USER = 0, ROLE_ADMIN = 1 };
enum { TX_REGISTER = 1, TX_STATUS, TX_DEPOSIT, TX_REDEEM, TX_CONFIG, TX_BOOT, TX_ADMIN_RECOVER };
typedef struct {
    uint16_t close_us, open_us, full_mm, clear_mm, pwm_max, light_on, light_off;
    uint16_t adc_scale;
    int16_t roll_zero, pitch_zero;
    uint8_t calibrated, mute;
} Settings;
enum {
    F_ESTOP = BIT(0),
    F_COLLISION = BIT(1),
    F_TILT = BIT(2),
    F_BATTERY = BIT(3),
    F_LID = BIT(4),
    F_MCP = BIT(5),
    F_MPU = BIT(6),
    F_OBSTACLE = BIT(7),
    F_LINE = BIT(8),
    F_STOP = BIT(9),
    F_COMMAND = BIT(10),
    F_CLOCK = BIT(11),
    F_SCHED = BIT(12),
    F_ADC = BIT(13)
};
#endif
