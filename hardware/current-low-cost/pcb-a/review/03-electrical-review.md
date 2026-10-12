# A1 电气定义独立复核

日期：2026-10-12。结论：**当前电气 JSON 未发现剩余必须修正的连线或器件值问题，可继续布局和制造检查。此结论不是整板可生产放行，也不是实物验证。**

审查对象为 `circuit.json`（A1-electrical-2026-10-12），SHA-256：
`225c46bab14148b6967e939e0aa3b51cb713c2dd21b1f58574349da68c86e21b`。

更新：J1–J6 的库封装改为 Phoenix MKDS 5.08mm 后再次运行 28 项结构检查，仍全部通过；网络未改变。该库名不要求购入 Phoenix 品牌，已有 KF301 须单独核脚形和本体包络。

复核证据：`audit_circuit.py`、`02-structured-audit.json`。脚本只读取电气定义、当前洞洞板 layout.json 和 connector-map.csv，审查输出仅写本目录。

## 已完成检查

- 94 个位号、72 个网络、293 个已分配电气端点；28 项独立结构检查全部通过。
- 33 组接口的 160 针及 8 组跳线的 21 针，与 connector-map.csv 逐一一致。
- MCU 的 29 个业务 GPIO 全部接到核心线束；PB6/PB7 的 I²C 网络别名正确。PA13/PA14 保留 SWD、PB2 保留 BOOT1；PC13/14/15 未误作业务接口。
- 原两块洞洞板的 44 件电气元件均保留。按旧位号逐件核对值和归一化网络，唯一功能变化是 AHCT 第 3 通道常使能作为 PB9 的 5V 缓冲；没有丢失原先电阻、电容或三管急停连接。新增 5 个偏置位置为 R33–R37，总 37 个电阻位置。
- 33 项功能定义所需的 RFID/SPI FLASH、对射、靠近、超声、三路循迹、蓝牙、MPU、碰撞、急停、按键、编码器、DHT、光敏、照明及语音接口均存在。功能列表代表硬件连接覆盖，不证明固件已实现全部功能。

## 逐组电气结论

| 电路 | 已核对内容与结论 |
|---|---|
| 供电 | J1/J2 只属开关后电池 VBAT_SW；J3 是外置降压 5V 输入，J4/J5/J6 分支。J7 为外部 3.3V 稳压的 5V/GND/3V3_EXT。J8.3 引入核心 3V3_CORE，两 3.3V 电源无直接并联。动力铜箔的实际支路和回流路径还要检查 PCB。 |
| 核心 | J8/J9 是自定义逐线接口，非核心物理排针。SPI、两个电机 PWM、USART1/2、USART3 TX、DHT、反馈及 ADC 映射均符合当前 WIRING。PA11/12 用作业务，正常系统禁止插核心 USB。 |
| MCP23017 | J10 为 EXT/GND/SCL/SDA/RESET；RESET 上拉 EXT，复位短接点不并核心 NRST。J11/J12 只接 A0–A6/B0–B6；A7/B7 不外接且必须配置为输出低。初始化 OLAT 先清零、再 IODIRA=0x40/IODIRB=0x7F；MCP 复位瞬间仍为输入态。A0/A1/A2 地址脚在模块侧接地。 |
| 上拉电源 | R8–R14、R29、R33–R35 属 EXT；R24、R27/R28、R31/R32、R37 属 CORE。编码器和总线的条件装配说明保留，不允许两路稳压各自上拉同一输入。 |
| SPI | J15 的 SDA=CS，PA4/PA5/PA7/PA6 分别 CS/SCK/MOSI/MISO，RST=GPA4。J16 与 RC522 共享三根总线，CS=PA15；WP/HOLD 为可选外露脚且拉 EXT。未知 FLASH 容量和排针次序未被假定。 |
| AHCT | U1 通道 1 为 PA0→舵机，通道 2 为 PB15→TRIG，通道 3 为 PB9→BUZZ_5V，/OE 均接地。通道 4 的 12 脚接地、13 脚接 5V、11 脚 NC。供电 14=5V、7=GND。R6/R7 建立前两路默认低，R36 默认安装给 PB9 下拉；低有效蜂鸣时改为只装 R37。JP3 选 3.3V 直出或 5V 缓冲，不能同时跨两端。 |
| 急停 | Q1/Q3 接两个 NC 的开关后电池偏置，Q2 钳位 STBY；各管 1E/2B/3C 的符号定义正确。PB5 经 R21=1k，R22/R23=10k 下拉，PB13 经 R24 拉 CORE。触点电流约 1.10–1.64mA，须核按钮低负载可靠性。EXT 失电不构成已验证硬件联锁，STBY 低为滑行高阻，软件故障锁和总开关仍需要。 |
| 超声及 ADC | Echo 上臂 R25=12k、下臂 R26=20k，5V→3.125V；按 5.15V 和 1% 不利公差约 3.243V。电池 R1=33k、R2=10k，8.4V→1.953V，C7=100nF；JP9 供明确隔离 ADC，不能误称已隔离全部 GPIO。 |
| DHT | 3.3V 分支 JP7 选 EXT、JP8 闭合；5V 分支 JP7 选 5V、JP8 必须开，经 J23 外接 BSS138。低侧 PB11 开漏，两侧均须有效上拉，R29 按模块实际上拉决定安装。单向 NPN 不替代此双向转换。 |
| IR/语音输入 | J33 六路及 J31 BUSY 都是已适配的 3.3V 输入口。板上没有额外 NPN 转换器，因此所购 5V DO 的条件适配必须留在模块侧，不可直接插接。弱上拉输出、PA12 已有 USB 上拉等负载仍需实测。 |
| 照明/语音 | GPA5 经 R3=100Ω 到外置 MOS G，R4=100k 下拉；MOS S=GND、D=LED_NEG，LED 串 220Ω。DFPlayer RX 经 1k，TX 不接，电源和扬声器从模块侧独立接，扬声器两端不接地。 |
| 模块电源选择 | MPU、HC05、DHT、蜂鸣电源选择口未假定实物额定电压；首次装配前核其 VIN、内部稳压和信号上拉。开路等待确认可接受，不能把这些口视为上电即用。 |

## 审查中已关闭的问题

1. 主代理简化 AHCT 通道 3 后，若 R36/R37 同时 DNP，PB9/A3 将在复位时浮空。现改 R36 默认安装、R37 DNP；即使不接蜂鸣器也保留一只偏置。
2. J8 原说明容易被理解为“仅拔核心 5V 线即可插 USB”。现改为正常系统禁止核心 USB；独立 USB 台架须断板电源并拔全部核心线束。
3. 2N3904 来源链接和封装说明已统一到当前 onsemi 2N3904 Rev3，1E/2B/3C。仅同样叫 TO-92 不足以保证另一厂家脚序。

## 布局和交付阶段仍需验证

- 100×100mm 两层板的实体空间：6 组 KF301、DIP14 座、3 只 D12.5 电解、37 只轴向电阻、排针及跳帽操作区，不能只检查焊盘中心距离。
- J3→J4/J5/J6 的正负动力支路必须具有实际低阻路径。计划主干 3mm、支路 2mm；普通 0.8mm 逻辑短支线不因同名电源网就被误认为承担电机电流。反过来也不能用主干标称宽度掩盖端子或热焊盘细颈。
- C1/C4、C2/C5、C3/C6 应分别靠近所对应电源出口；C8 靠近 AHCT 的供电回路。远离本板的驱动/舵机/语音仍需就近去耦。
- 实际购入端子脚形、2N3904 脚序、电解脚距/体积尚未测量；板端明确焊盘号和极性，实物不匹配时采取已说明的短绝缘引线与机械固定，而非强插。
- 原理图与 PCB 一致性、DRC、未连接、板框/钻孔、Gerber 层完整性和 1:1 打印均尚待最终检查。此时不能报告 0 DRC 或“可直接下单”。
- 首次通电按单电源、限流、轮悬空的次序，分别验证两 3.3V、ADC、Echo、PB5/STBY、急停保持/释放、MCU 和 MCP 复位、模块断线、驱动默认状态及真实负载温升。没有预填实物通过结论。

## 原厂证据

- [TI SN74AHCT125 Rev R](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf)：DIP14 引脚、4.5–5.5V 供电、TTL 输入门限和未用输入处理。
- [onsemi 2N3904 Rev3](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf)：第1页给出 1E/2B/3C；第2页为饱和规格，不能外推为任意品牌脚序。
- [Microchip MCP23017 DS20001952](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf)：GPIO7 输出限制、上电寄存器和输入电压范围。
- [Toshiba TB6612FNG](https://toshiba.semicon-storage.com/info/TB6612FNG_datasheet_en_20141001.pdf?did=10660&prodName=TB6612FNG)、[ST STM32F103x8/xB](https://www.st.com/resource/en/datasheet/stm32f103c8.pdf)：控制门限、待机行为、GPIO/ADC 与 USB 边界。
- [Nexperia AN10441](https://assets.nexperia.com/documents/application-note/AN10441.pdf)、[AOS AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)：开漏双向转换与照明 MOS 栅压适用性。

完整前置风险和已有器件取舍见上一级 `circuit-audit.md`。若 JSON 再改，须重跑结构审计并更新本报告哈希；本报告不随源文件自动改变。
