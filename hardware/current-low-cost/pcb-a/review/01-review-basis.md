# A 方案独立审查基线

日期：2026-10-12。范围：保留已购直插件、外部 MCP23017/稳压/驱动/核心模块，以两层手焊 PCB 替代洞洞板内部连线。本文是审查要求，不代表新版电路、PCB 或制造文件已通过。

## 约束和审查依据

- 以当前 `hardware/current-low-cost/WIRING.md` 和 `docs/manual/ASSEMBLY.md` 的 MCP23017 方案为原始电气依据，不使用归档 PCF8574 或旧 STM32 底板针序。
- 电气设计由 assembly_electrical 维护；布局和制造输出由主代理维护。审查者只写本 review 目录。
- 遵循 pcb-flow 的本地说明：本地可恢复检查点，不执行公开网盘上传；纯审查不调用会回填板文件的 mash DRC。
- 成品模块通过独立线束按名称接线。自定义板端接口不等于商品模块实际排针次序。
- 针对已有器件保留 DIP14、TO-92、轴向电阻、径向电解和 2.54mm 排针。AO3400A/BSS138 转接模块继续外置时，不把模块画成直接焊裸 SOT-23 的确定封装。

## 冻结电气的逐项判据

| 项目 | 判据 | 尚待实物确认项 |
|---|---|---|
| 3.3V 域 | 3V3_CORE 和 3V3_EXT 不直接并联，共地；核心上拉来自 CORE，外扩上拉来自 EXT | 模块上拉电源、外部稳压型号及去耦 |
| 电源 | 外部降压/电机/舵机主电流保持独立支路；若电源 PCB 承担主干电流，另核铜宽/端子/回流 | 电解脚距与直径、端子额定、堵转电流 |
| MCP23017 | GPA7/GPB7 只配置输出；GPA6 输入；IODIRA=0x40、IODIRB=0x7F；OLAT 先清零；RESET 上拉 EXT，A0–A2 低 | 模块自带 RESET、地址和 I²C 上拉 |
| MCP 上电 | POR 所有 IODIR 默认输入，不把 OLAT=0 误当引脚已输出低；电机使能、MOS 栅极硬件默认低 | 实际 TB6612 模块是否额外上拉 STBY |
| 5V DO | 5V 输出不能直接送 MCP/一般 3.3V 输入；采用已定义条件适配，标明是否反相 | 传感器 DO 电压、源电流、触发极性 |
| PA12 | 兼容核心 USB D+ 上拉的额外约 2.2mA 低态负载；不插核心 USB | 已有核心原理图/实测上拉和模块吸电流 |
| DHT11 | 3.3V 已确认模块可直接开漏；5V 模块通过 BSS138 双向开漏转换，两侧正确上拉 | 模块型号/内置上拉/所用转换板针序 |
| AHCT125 | 5V 供电，14/7 旁去耦；已用通道 /OE 低；未用 A 固定低、/OE 高、Y 悬空；第3通道蜂鸣选配与未用绑线互斥 | SN74AHCT125N DIP14 实物，不替用 HC |
| NPN 脚序 | 每只 2N3904 的符号脚号/封装号对应实际 E/B/C | 厂家/包装/实物脚序不能由 TO-92 名称推断 |
| 急停 | 双 NC 分别控制钳位和反馈；PB5 经 1k，STBY 下拉；接点偏置取总开关后电池 | 约 1–1.6mA 的触点小电流可靠性 |
| 急停边界 | EXT 失电时钳位偏置消失；STBY 低为高阻滑行；不宣称全动力断电/机械制动；软件故障锁保留 | 实测复位/断线/失电行为 |
| 灯 MOS | AO3400A G 经 100Ω，G 对地 100k；S 接地，D 接 LED 负极，LED 串 220Ω | 转接板 G/S/D 追线与 LED 极性 |
| ADC | 电池 33k/10k 与 100nF，8.4V→约1.953V；Echo 12k/20k，5V→3.125V | 实物阻值；单断核心电源须隔离 ADC/IO |
| I²C | 上拉只到 EXT，统计各模块并联等效值；100kHz 起步、短线；不据默认4.7k保证任意总线 | 低态电压、边沿和实际电缆电容 |

## 制造与手焊审查点

100×100mm 只作为目标范围；需根据最终连接器数量、安装孔、接线出线方向、DIP座/电解实体大小判断可实现性。最终检查包括闭合板框、孔边距、封装孔径与脚距、合理焊盘环宽、器件和端子可操作间距、电解极性、插座缺口、关键接口丝印、网络一致性、实际未连接和 DRC 分类、Gerber/Excellon 文件完整性。外部核心与模块无需假定通用整排直插封装。

## 原厂依据（2026-10-12 已核）

- [Microchip MCP23017 DS20001952](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf)：端口 A7/B7 输出限制、POR、I²C 和电压边界。
- [TI SN74AHCT125](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf)：DIP14 引脚、TTL 门限、使能、未用输入处理。
- [onsemi 2N3904](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf)：引脚和饱和规格；只证明对应厂商器件。
- [Nexperia AN10441](https://assets.nexperia.com/documents/application-note/AN10441.pdf)：MOS 双向开漏转换。
- [AOS AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)：G/S/D 和 2.5V 栅压下导通规格。
- [Toshiba TB6612FNG](https://toshiba.semicon-storage.com/info/TB6612FNG_datasheet_en_20141001.pdf?did=10660&prodName=TB6612FNG)：控制门限、下拉及 STBY 行为。
- [ST STM32F103x8/xB](https://www.st.com/resource/en/datasheet/stm32f103c8.pdf)：IO/ADC 工作范围、USB 引脚要求。

既有详细证据和计算见上一级 `circuit-audit.md`。本记录没有实物装配、通电、温升、堵转或制动测试数据。
