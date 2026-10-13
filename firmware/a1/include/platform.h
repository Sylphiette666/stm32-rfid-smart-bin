#ifndef PLATFORM_H
#define PLATFORM_H
#include "config.h"
extern volatile uint32_t irq_faults;
extern bool clock_ok;
extern uint32_t reset_cause;
void platform_init(void);
uint32_t millis(void);
uint16_t micros16(void);
void delay_us(uint16_t us);
uint16_t gpio_a(void);
uint16_t gpio_b(void);
void motor_off(void);
bool motor_output(uint16_t left, uint16_t right);
void servo_output(uint16_t pulse);
void buzzer_output(bool on);
void trigger_output(bool on);
void dht_drive(bool low);
void dht_arm(bool on);
bool adc_read(uint8_t channel, uint16_t *value);
bool i2c_write(uint8_t addr, const uint8_t *buf, uint16_t len);
bool i2c_read_reg(uint8_t addr, uint8_t reg, uint8_t *buf, uint16_t len);
bool spi_transfer(bool flash, const uint8_t *tx, uint8_t *rx, uint16_t len);
bool serial_line(uint8_t port, char *line, uint16_t cap);
bool serial_send(uint8_t port, const char *s);
bool audio_send(const uint8_t *p, uint16_t len);
void watchdog_feed(void);
bool clear_irq_faults(void);
void safety_tick_irq(void);
void sensor_edge_irq(uint8_t pin, bool high, uint16_t at);
void sensor_abort_irq(void);
#endif
