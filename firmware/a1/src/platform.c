#include "platform.h"
#include "stm32f10x.h"
#include <string.h>
volatile uint32_t irq_faults;
bool clock_ok;
uint32_t reset_cause;
uint32_t SystemCoreClock = 8000000;
static volatile uint32_t ticks;
typedef struct {
    volatile uint16_t rh, rt, th, tt;
    volatile bool overflow;
    uint8_t rx[256], tx[1024];
    char line[128];
    uint16_t used;
    bool discard;
} Uart;
static Uart uart[3];
static USART_TypeDef *const ports[] = {USART1, USART2, USART3};
static void pin(GPIO_TypeDef *g, unsigned n, unsigned mode) {
    volatile uint32_t *r = n < 8 ? &g->CRL : &g->CRH;
    unsigned s = (n & 7) * 4;
    *r = (*r & ~(15u << s)) | (mode << s);
}
static bool wait_mask(volatile uint32_t *r, uint32_t mask, bool set) {
    for (unsigned n = 0; n < 1000000; n++)
        if (((*r & mask) != 0) == set)
            return true;
    return false;
}
void SystemInit(void) {
    RCC->CR |= RCC_CR_HSION;
    RCC->CFGR = 0;
    RCC->CR &= ~RCC_CR_PLLON;
    SCB->VTOR = 0x08000000;
    SystemCoreClock = 8000000;
    RCC->CR |= RCC_CR_HSEON;
    if (!wait_mask(&RCC->CR, RCC_CR_HSERDY, true))
        return;
    FLASH->ACR = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY_2;
    RCC->CFGR = RCC_CFGR_PLLSRC | RCC_CFGR_PLLMULL9 | RCC_CFGR_PPRE1_DIV2 | RCC_CFGR_ADCPRE_DIV6;
    RCC->CR |= RCC_CR_PLLON;
    if (!wait_mask(&RCC->CR, RCC_CR_PLLRDY, true))
        return;
    RCC->CFGR |= RCC_CFGR_SW_PLL;
    if (wait_mask(&RCC->CFGR, RCC_CFGR_SWS_1, true)) {
        SystemCoreClock = 72000000;
        RCC->CR |= RCC_CR_CSSON;
    } else
        RCC->CFGR = 0;
    /* clock_ok is assigned in main: C runtime initializes globals after SystemInit. */
}
void SystemCoreClockUpdate(void) {
    SystemCoreClock = (RCC->CFGR & RCC_CFGR_SWS) == RCC_CFGR_SWS_PLL ? 72000000 : 8000000;
}
uint32_t millis(void) { return ticks; }
uint16_t micros16(void) { return (uint16_t)TIM3->CNT; }
void delay_us(uint16_t us) {
    uint16_t t = micros16();
    while ((uint16_t)(micros16() - t) < us) {
    }
}
uint16_t gpio_a(void) { return (uint16_t)GPIOA->IDR; }
uint16_t gpio_b(void) { return (uint16_t)GPIOB->IDR; }
void motor_off(void) {
    TIM1->CCR1 = 0;
    TIM1->CCR4 = 0;
    GPIOB->BRR = BIT(5);
}
bool motor_output(uint16_t l, uint16_t r) {
    uint32_t p = __get_PRIMASK();
    __disable_irq();
    bool ok = clock_ok && !irq_faults && !(GPIOB->IDR & (BIT(12) | BIT(13)));
    if (ok) {
        TIM1->CCR1 = l > 100 ? 3599 : (uint32_t)l * 36;
        TIM1->CCR4 = r > 100 ? 3599 : (uint32_t)r * 36;
        GPIOB->BSRR = BIT(5);
    } else
        motor_off();
    __set_PRIMASK(p);
    return ok;
}
void servo_output(uint16_t pulse) { TIM2->CCR1 = pulse >= 900 && pulse <= 2100 ? pulse : 0; }
void buzzer_output(bool on) {
#if BUZZER_PASSIVE
    TIM4->CCR4 = on ? 250 : 0;
#else
    if (on != BUZZER_ACTIVE_LOW)
        GPIOB->BSRR = BIT(9);
    else
        GPIOB->BRR = BIT(9);
#endif
}
void trigger_output(bool on) {
    if (on)
        GPIOB->BSRR = BIT(15);
    else
        GPIOB->BRR = BIT(15);
}
void dht_drive(bool low) {
    if (low)
        GPIOB->BRR = BIT(11);
    else
        GPIOB->BSRR = BIT(11);
}
void dht_arm(bool on) {
    EXTI->IMR &= ~BIT(11);
    EXTI->PR = BIT(11);
    if (on)
        EXTI->IMR |= BIT(11);
}
static void uart_init(unsigned i, uint32_t bus, uint32_t baud) {
    USART_TypeDef *u = ports[i];
    u->BRR = (bus + baud / 2) / baud;
    u->CR1 = USART_CR1_UE | USART_CR1_TE;
    if (i < 2)
        u->CR1 |= USART_CR1_RE | USART_CR1_RXNEIE;
    NVIC_SetPriority((IRQn_Type)(USART1_IRQn + i), 3);
    NVIC_EnableIRQ((IRQn_Type)(USART1_IRQn + i));
}
void platform_init(void) {
    SystemCoreClockUpdate();
    clock_ok = SystemCoreClock == 72000000;
    reset_cause = RCC->CSR;
    RCC->CSR |= RCC_CSR_RMVF;
    RCC->APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN | RCC_APB2ENR_IOPBEN |
                    RCC_APB2ENR_TIM1EN | RCC_APB2ENR_SPI1EN | RCC_APB2ENR_USART1EN |
                    RCC_APB2ENR_ADC1EN;
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN | RCC_APB1ENR_TIM3EN | RCC_APB1ENR_TIM4EN |
                    RCC_APB1ENR_USART2EN | RCC_APB1ENR_USART3EN;
    AFIO->MAPR = AFIO_MAPR_SWJ_CFG_JTAGDISABLE;
    GPIOA->BSRR = BIT(4) | BIT(15);
    GPIOB->BRR = BIT(5) | BIT(15);
    GPIOB->BSRR = BIT(6) | BIT(7) | BIT(11);
    pin(GPIOA, 4, 3);
    pin(GPIOA, 15, 3);
    pin(GPIOB, 5, 3);
    pin(GPIOB, 15, 3);
    pin(GPIOA, 0, 0xb);
    pin(GPIOA, 8, 0xb);
    pin(GPIOA, 11, 0xb);
    pin(GPIOA, 1, 0);
    pin(GPIOB, 0, LIGHT_DIGITAL ? 4 : 0);
    pin(GPIOA, 5, 0xb);
    pin(GPIOA, 7, 0xb);
    pin(GPIOA, 6, 4);
    pin(GPIOA, 9, 0xb);
    pin(GPIOA, 10, 4);
    pin(GPIOA, 2, 0xb);
    pin(GPIOA, 3, 4);
    pin(GPIOB, 10, 0xb);
    pin(GPIOB, 6, 7);
    pin(GPIOB, 7, 7);
    pin(GPIOB, 11, 7); /* bounded software I2C, open drain */
    pin(GPIOB, 9, BUZZER_PASSIVE ? 0xb : 3);
    buzzer_output(false);
    pin(GPIOA, 12, 8);
    GPIOA->BSRR = BIT(12);
    const uint8_t inputs[] = {1, 3, 4, 8, 12, 13, 14};
    for (unsigned i = 0; i < sizeof(inputs); i++) {
        pin(GPIOB, inputs[i], 8);
        GPIOB->BSRR = BIT(inputs[i]);
    }
    TIM1->PSC = 0;
    TIM1->ARR = clock_ok ? 3599 : 399;
    TIM1->CCMR1 = 0x68;
    TIM1->CCMR2 = 0x6800;
    TIM1->CCER = BIT(0) | BIT(12);
    TIM1->BDTR = TIM_BDTR_MOE;
    TIM1->EGR = 1;
    TIM1->CR1 = 0x81;
    motor_off();
    TIM2->PSC = SystemCoreClock / 1000000 - 1;
    TIM2->ARR = 19999;
    TIM2->CCMR1 = 0x68;
    TIM2->CCER = 1;
    TIM2->EGR = 1;
    TIM2->CR1 = 0x81;
    TIM3->PSC = SystemCoreClock / 1000000 - 1;
    TIM3->ARR = 65535;
    TIM3->EGR = 1;
    TIM3->CR1 = 1;
    TIM4->PSC = SystemCoreClock / 1000000 - 1;
    TIM4->ARR = 499;
    TIM4->CCMR2 = 0x6800;
    TIM4->CCER = BIT(12);
    TIM4->EGR = 1;
    TIM4->CR1 = 0x81;
    SPI1->CR1 = SPI_CR1_MSTR | SPI_CR1_SSM | SPI_CR1_SSI | (5u << 3) | SPI_CR1_SPE;
    uint32_t pclk1 = clock_ok ? 36000000 : 8000000;
    uart_init(0, SystemCoreClock, 115200);
    uart_init(1, pclk1, 9600);
    uart_init(2, pclk1, 9600);
    ADC1->SMPR2 = (7u << 3) | (7u << 24);
    ADC1->CR2 = ADC_CR2_ADON;
    delay_us(10);
    ADC1->CR2 |= ADC_CR2_RSTCAL;
    wait_mask(&ADC1->CR2, ADC_CR2_RSTCAL, false);
    ADC1->CR2 |= ADC_CR2_CAL;
    wait_mask(&ADC1->CR2, ADC_CR2_CAL, false);
    AFIO->EXTICR[0] = (1u << 4);
    AFIO->EXTICR[2] = 1u << 12;
    AFIO->EXTICR[3] = 0x11;
    EXTI->RTSR = BIT(1) | BIT(11) | BIT(12) | BIT(13);
    EXTI->FTSR = BIT(1) | BIT(11);
    EXTI->PR = 0xffff;
    EXTI->IMR = BIT(1) | BIT(12) | BIT(13);
    NVIC_SetPriority(EXTI15_10_IRQn, 0);
    NVIC_EnableIRQ(EXTI15_10_IRQn);
    NVIC_SetPriority(EXTI1_IRQn, 1);
    NVIC_EnableIRQ(EXTI1_IRQn);
    SysTick_Config(SystemCoreClock / 1000);
    NVIC_SetPriority(SysTick_IRQn, 2);
#if ENABLE_WATCHDOG
    IWDG->KR = 0x5555;
    IWDG->PR = 3;
    IWDG->RLR = 625;
    IWDG->KR = 0xaaaa;
    IWDG->KR = 0xcccc;
#endif
}
bool adc_read(uint8_t ch, uint16_t *v) {
    ADC1->SQR1 = 0;
    ADC1->SQR3 = ch;
    ADC1->SR = 0;
    ADC1->CR2 |= ADC_CR2_ADON;
    uint16_t t = micros16();
    while (!(ADC1->SR & ADC_SR_EOC)) {
        if ((uint16_t)(micros16() - t) > 100)
            return false;
    }
    *v = (uint16_t)ADC1->DR;
    return true;
}
/* GPIO I2C avoids F1 receive sequencing/errata. Every clock stretch is bounded. */
static void sda(bool hi) {
    if (hi)
        GPIOB->BSRR = BIT(7);
    else
        GPIOB->BRR = BIT(7);
}
static void scl_lo(void) {
    GPIOB->BRR = BIT(6);
    delay_us(4);
}
static bool scl_hi(void) {
    GPIOB->BSRR = BIT(6);
    uint16_t t = micros16();
    while (!(GPIOB->IDR & BIT(6)))
        if ((uint16_t)(micros16() - t) > 100)
            return false;
    delay_us(4);
    return true;
}
static bool i_start(void) {
    sda(true);
    if (!scl_hi())
        return false;
    if (!(GPIOB->IDR & BIT(7)))
        return false;
    sda(false);
    delay_us(4);
    scl_lo();
    return true;
}
static void i_stop(void) {
    sda(false);
    (void)scl_hi();
    sda(true);
    delay_us(4);
}
static bool i_byte(uint8_t b) {
    for (unsigned i = 0; i < 8; i++) {
        sda((b & 0x80) != 0);
        if (!scl_hi())
            return false;
        scl_lo();
        b <<= 1;
    }
    sda(true);
    if (!scl_hi())
        return false;
    bool ok = !(GPIOB->IDR & BIT(7));
    scl_lo();
    return ok;
}
bool i2c_write(uint8_t a, const uint8_t *p, uint16_t n) {
    bool ok = i_start() && i_byte((uint8_t)(a << 1));
    for (unsigned i = 0; ok && i < n; i++)
        ok = i_byte(p[i]);
    i_stop();
    return ok;
}
bool i2c_read_reg(uint8_t a, uint8_t reg, uint8_t *p, uint16_t n) {
    bool ok = i_start() && i_byte((uint8_t)(a << 1)) && i_byte(reg) && i_start() &&
              i_byte((uint8_t)((a << 1) | 1));
    for (unsigned i = 0; ok && i < n; i++) {
        uint8_t b = 0;
        sda(true);
        for (unsigned j = 0; j < 8; j++) {
            if (!scl_hi()) {
                ok = false;
                break;
            }
            b = (uint8_t)((b << 1) | ((GPIOB->IDR >> 7) & 1));
            scl_lo();
        }
        p[i] = b;
        sda(i + 1 == n);
        if (!scl_hi())
            ok = false;
        scl_lo();
        sda(true);
    }
    i_stop();
    return ok;
}
bool spi_transfer(bool flash, const uint8_t *tx, uint8_t *rx, uint16_t n) {
    GPIOA->BSRR = BIT(4) | BIT(15);
    GPIOA->BRR = flash ? BIT(15) : BIT(4);
    bool ok = true;
    for (unsigned i = 0; i < n; i++) {
        uint16_t t = micros16();
        while (!(SPI1->SR & SPI_SR_TXE)) {
            if ((uint16_t)(micros16() - t) > 100) {
                ok = false;
                break;
            }
        }
        if (!ok)
            break;
        SPI1->DR = tx ? tx[i] : 0xff;
        while (!(SPI1->SR & SPI_SR_RXNE)) {
            if ((uint16_t)(micros16() - t) > 150) {
                ok = false;
                break;
            }
        }
        if (!ok)
            break;
        uint8_t b = (uint8_t)SPI1->DR;
        if (rx)
            rx[i] = b;
    }
    /* RXNE can precede the final trailing clock edge; keep CS asserted
       until the shift engine is idle, with a bounded failure path. */
    uint16_t end_at = micros16();
    while (SPI1->SR & SPI_SR_BSY) {
        if ((uint16_t)(micros16() - end_at) > 100) {
            ok = false;
            break;
        }
    }
    GPIOA->BSRR = BIT(4) | BIT(15);
    return ok;
}
static void uart_irq(unsigned i) {
    Uart *q = &uart[i];
    USART_TypeDef *u = ports[i];
    uint32_t sr = u->SR;
    if (sr & (USART_SR_RXNE | USART_SR_ORE | USART_SR_FE | USART_SR_NE)) {
        uint8_t b = (uint8_t)u->DR;
        uint16_t h = (q->rh + 1) & 255;
        if (sr & (USART_SR_ORE | USART_SR_FE | USART_SR_NE)) {
            q->overflow = true;
            irq_faults |= F_COMMAND;
            motor_off();
        } else if (h == q->rt) {
            q->overflow = true;
            irq_faults |= F_COMMAND;
            motor_off();
        } else {
            q->rx[q->rh] = b;
            q->rh = h;
        }
    }
    if ((sr & USART_SR_TXE) && (u->CR1 & USART_CR1_TXEIE)) {
        if (q->tt != q->th) {
            u->DR = q->tx[q->tt];
            q->tt = (q->tt + 1) & 1023;
        } else
            u->CR1 &= ~USART_CR1_TXEIE;
    }
}
bool serial_line(uint8_t i, char *out, uint16_t cap) {
    Uart *q = &uart[i];
    if (q->overflow) {
        q->discard = true;
        q->used = 0;
        q->overflow = false;
    }
    unsigned budget = 64;
    while (q->rt != q->rh && budget--) {
        char c = (char)q->rx[q->rt];
        q->rt = (q->rt + 1) & 255;
        if (c == '\r')
            continue;
        if (c == '\n') {
            if (q->discard) {
                q->discard = false;
                q->used = 0;
                continue;
            }
            q->line[q->used] = 0;
            if (q->used >= cap) {
                q->used = 0;
                return false;
            }
            memcpy(out, q->line, q->used + 1);
            q->used = 0;
            return true;
        }
        if (c < 32 || c > 126 || q->used >= sizeof(q->line) - 1) {
            q->discard = true;
            q->used = 0;
            irq_faults |= F_COMMAND;
            motor_off();
        } else if (!q->discard)
            q->line[q->used++] = c;
    }
    return false;
}
static bool send_bytes(unsigned i, const uint8_t *p, uint16_t n) {
    Uart *q = &uart[i];
    if (n > 1023 - ((q->th - q->tt) & 1023))
        return false;
    for (unsigned k = 0; k < n; k++) {
        q->tx[q->th] = p[k];
        q->th = (q->th + 1) & 1023;
    }
    ports[i]->CR1 |= USART_CR1_TXEIE;
    return true;
}
bool serial_send(uint8_t i, const char *s) {
    return send_bytes(i, (const uint8_t *)s, (uint16_t)strlen(s));
}
bool audio_send(const uint8_t *p, uint16_t n) { return send_bytes(2, p, n); }
void USART1_IRQHandler(void) { uart_irq(0); }
void USART2_IRQHandler(void) { uart_irq(1); }
void USART3_IRQHandler(void) { uart_irq(2); }
void SysTick_Handler(void) {
    ticks++;
    if (GPIOB->IDR & BIT(13)) {
        motor_off();
        irq_faults |= F_ESTOP;
    }
    if (GPIOB->IDR & BIT(12)) {
        motor_off();
        irq_faults |= F_COLLISION;
    }
    safety_tick_irq();
}
void EXTI1_IRQHandler(void) {
    uint16_t t = micros16();
    EXTI->PR = BIT(1);
    sensor_edge_irq(1, (GPIOB->IDR & BIT(1)) != 0, t);
}
void EXTI15_10_IRQHandler(void) {
    uint16_t t = micros16();
    uint32_t pending = EXTI->PR;
    EXTI->PR = pending & (BIT(11) | BIT(12) | BIT(13));
    if (pending & (BIT(12) | BIT(13))) {
        motor_off();
        if (pending & BIT(12))
            irq_faults |= F_COLLISION;
        if (pending & BIT(13))
            irq_faults |= F_ESTOP;
        sensor_abort_irq();
        return;
    }
    if (pending & BIT(11))
        sensor_edge_irq(11, (GPIOB->IDR & BIT(11)) != 0, t);
}
void watchdog_feed(void) {
#if ENABLE_WATCHDOG
    IWDG->KR = 0xaaaa;
#endif
}
bool clear_irq_faults(void) {
    uint32_t p = __get_PRIMASK();
    __disable_irq();
    bool ok = !(GPIOB->IDR & (BIT(12) | BIT(13)));
    if (ok)
        irq_faults = 0;
    __set_PRIMASK(p);
    return ok;
}
void HardFault_Handler(void) {
    motor_off();
    servo_output(0);
    for (;;) {
    }
}
void NMI_Handler(void) {
    motor_off();
    servo_output(0);
    for (;;) {
    }
}
