# A1 固件：编译已验证，待实物调试

适用：2026-10-12 A1 PCB、STM32F103C8T6、外置 MCP23017。代码版本 `A1-0.1.0`。

这份工程已实现账户、积分持久化、刷卡投放、盖板、运动、菜单、串口和传感器流程，提供可编译工程及烧录文件。编译和主机测试不等于实物33项验收通过。传感器极性、模块型号、供电、机构脉宽及速度必须按实物确认。

## 开发工具已确定使用 Keil

本项目使用 **Keil µVision + Arm Compiler 6** 完成编辑、编译、下载和源码调试。STM32CubeMX、STM32CubeIDE、STM32CubeProgrammer 都不是当前工程的必装软件；早期手册中的 ST 工具路线不再作为本固件的操作入口。继续使用现有下载器，首次按实际型号选择 ST-LINK 或 J-Link 并安装相应驱动。

| 工具 | 本项目用途 |
|---|---|
| Keil µVision、Arm Compiler 6、STM32F1xx_DFP | 必需的软件开发环境，已有可用安装可直接复用 |
| 下载器驱动、USB串口驱动及串口终端 | 连接实物、执行 STATUS/RAW 和保存测量记录 |
| VS Code | 可选，用于编辑源码；也可在终端调用下方已有构建脚本，无需另建一套工程 |
| CubeMX / CubeIDE / CubeProgrammer | 当前流程不依赖，无需为本项目安装 |

VS Code 本身不包含 STM32 编译器和下载调试器。Arm 也提供 [Keil Studio for VS Code](https://mdk-packs.github.io/vscode-cmsis-solution-docs/installation.html)，但它采用 CMSIS solution 工程工作流；本次交付的是 µVision `.uvprojx` 工程，未配置 VS Code 原生断点调试。为了直接复用已经验证的工程，本项目的下载和调试入口统一使用 Keil。

## 打开与编译

1. 用已有 Keil 打开 `MDK/SmartBin_A1.uvprojx`。
2. 选择 **SmartBin_A1**，执行 **Rebuild**。实测环境：MDK 5.43、Arm Compiler 6.24、STM32F1xx_DFP 2.4.1。
3. HEX 位于 `build/keil/SmartBin_A1.hex`；AXF 可用于源码调试。
4. `release/` 提供命令行优化构建的 HEX、BIN、AXF、校验值和验证记录。HEX 已包含地址；BIN 起始地址为 `0x08000000`。
5. 调试器按实物选择 ST-LINK 或 J-Link、SWD；不要把核心 USB 接入已连接的整机。

保留整个固件目录结构，不要只复制 `.uvprojx`：工程仍引用 `firmware/legacy/SmartBin_F103/CMSIS/Device/` 中的设备头文件。若编译器或器件包未找到，在 Options for Target / Pack Installer 中选择已安装的兼容版本，再重新编译。

Keil的C/C++ Misc Controls已显式设置`-Oz`体积优化。当前重新编译为0错误、0警告，Code+RO+RW为29320字节，低于32KB；许可仍以本机正常激活的编译器为准。优化可能使部分局部变量不可观察、单步顺序与源代码不同；需要细查某个模块时可调整优化后重编译，并重新检查程序大小。

## Keil 下载与源码调试

本工程不附带与个人下载器绑定的 `.uvoptx`，首次连接按以下顺序设置。编译通过不代表已经连接或烧录实物。

1. 先按 [实验室清单](LAB_CHECKLIST.md) 完成供电检查。接线时断电，电机和舵机功率支路断开；SWDIO 接 PA13、SWCLK 接 PA14、GND 共地，有 NRST 则接 NRST。目标板按 A1 方案供电，下载器的参考电压与供电输出按实际型号区分。
2. 打开 **Options for Target → Debug**，选择实际的 **ST-Link Debugger** 或 **J-LINK / J-TRACE Cortex**；进入 Settings，选 **SWD**，初始时钟选择约 400 kHz 或更低的可用档位。
3. 在 **Utilities** 中选 **Use Debug Driver**。在 **Flash Download** 中确认适用于 STM32F103C8 的中容量算法 `STM32F10x Med-density Flash`（文件 `STM32F10x_128.FLM`）；实际工程链接范围仍为 `0x08000000` 起的 64KB。算法文件名中的128不代表可把C8工程按128KB使用。保留 Program 和 Verify。
4. 执行 **Rebuild**，确认无错误，再选 **Flash → Download**。使用当前工程生成的映像；由工程地址配置决定下载位置，无需另开 CubeProgrammer。
5. 先保持 DISARMED，用串口终端 115200、8N1 发送 `STATUS` 和 `RAW`，核对启动状态和输入。单独核心板未接齐外设时可能报告模块故障，不应通过使能执行器绕过。
6. 选 **Debug → Start/Stop Debug Session**，在 `main` 或目标模块设置断点，使用 Run、Step、Watch 观察。**设置断点前保持 DISARM 并断开动力支路**：CPU暂停时定时器可能继续输出，不能把暂停当作执行器停止。执行器联调以运行中的串口记录为主。
7. 下载后退出调试，重新上电检查程序能独立运行，再继续管理员初始化和各模块标定。连接失败先查供电、共地、SWD接线和驱动；必要时连接NRST并尝试 under reset，不先修改 Option Bytes。

该流程对应 [Arm 官方 ST-LINK 与 µVision 使用说明](https://www.keil.com/appnotes/files/apnt_286_v1.7.pdf)。本机已验证编译；实物连接、烧录和断点仍待用户持有硬件时验证。

## 可选命令行构建

也可以用 Python 3 执行：

```powershell
python tools/build.py --compiler D:\Keil5\ARM\ARMCLANG\bin
python tools/build_keil.py --keil D:\Keil5\UV4\UV4.exe
python tools/test.py
```

最后一条需要 Windows MSVC C 编译工具；本机路径写在脚本中，可按实际安装调整。脚本不下载或烧录任何设备。

**与旧手册的软件路线区别：**本次直接复用现有 ST 设备头文件和启动文件，使用 CMSIS 寄存器方式及 Keil 工程，没有生成 CubeMX `.ioc`，没有混用 HAL 和标准外设库。I²C 使用 PB6/PB7 开漏软件时序、每次时钟拉伸限时100 µs，常规事务拆成小块；不是硬件 I²C1 HAL 实现。应用层与硬件层分开，后续可移植，但不要把本工程当作 CubeMX 自动生成工程覆盖。

## 实验室首次调试

详细顺序见 [LAB_CHECKLIST.md](LAB_CHECKLIST.md)。两次实验室安排仍适用：第一次集中做断电检查、电源调节、逻辑模块电平核对；第二次做执行器标定和整机带载。硬件变更后复查对应部分。

上电始终 **DISARMED**：电机PWM=0、PB5低、舵机无脉冲。串口诊断可以使用，业务动作还需初始化账本、标定、解除故障并明确使能。

电脑串口：115200、8N1、无流控，命令大写，以换行结束。HC-05默认9600；持续运动时每100 ms发送完整 `MOVE` 命令，300 ms未收到有效运动命令会锁停。

```text
STATUS
RAW
HELP
```

`STATUS` 含故障位、供电、模块状态、存储状态、积分序号、桶满状态和主循环最大间隔。`RAW` 用于记录每个传感器触发/不触发时的原始电平。没有取得有效数据时，不应将显示的初值当实测。

## 首次管理员与权限

全新且全空白的外部FLASH显示 `STORE=1`。停车、同时按 MODE+BACK 三秒，初始化空账本；等待 `STORE=2`，刷管理员卡，再长按MODE或发送 `CONFIRM`。初始化采用事务写入；并非每次开机清空。

已有账本：在查询模式刷管理员卡，授权60秒；按键操作及管理请求续期。注册新卡需 `REGISTER` → 刷新卡 → `CONFIRM`。挂失、注销、恢复也需管理员和确认。

丢失管理员卡：本机 MODE+BACK 三秒后，在60秒内发送 `ADMIN_RECOVER` → 刷恢复卡 → `CONFIRM`。可恢复已有账户为管理员，也可在有空槽时创建新管理员；不清空普通用户积分。此为课设本机恢复入口，不是抗物理攻击的身份系统。UID识别也不提供防复制保证。

最后一位有效管理员不能被挂失或注销。64个历史账户槽位不回收，以保留用户ID与历史一致性；满容量时拒绝新增。

## 常用命令

| 命令 | 条件/含义 |
|---|---|
| `STOP` / `DISARM` | 停车锁存；DISARM另撤销执行器使能并关闭舵机脉冲 |
| `CLEAR` | 原因恢复后人工清锁；不会自动重新运动 |
| `ARM CONFIRM` | 仅电脑串口；电气检查完成后允许执行器测试；也可在本机菜单 ARM OUTPUTS 长按确认 |
| `MODE DEPOSIT` / `MODE QUERY` | 刷卡投放或只查询 |
| `MODE MANUAL` | 遥控模式，进入时不自动运动 |
| `MOVE F 25` / `MOVE B 25` / `MOVE L 20` / `MOVE R 20` | 前、后、左转、右转；不超过标定PWM上限，必须持续发送 |
| `LINE START 1` / `LINE START 2` | 从人工确认起点开始循迹，计到指定标记停车 |
| `MODE CONVENIENCE` | 独立靠近传感器开盖，不计积分 |
| `MODE MAINTENANCE` → `OPEN` | 管理员清桶模式，允许满桶时开盖；实际拆装前仍需断电 |
| `CLOSE` | 光束畅通、停止输入恢复后显式关盖；开盖/卡阻故障先检查，再CLEAR |
| `QUERY 2` | 查询用户2，不开盖、不改积分 |
| `REGISTER` → 刷卡 → `CONFIRM` | 管理员注册普通用户 |
| `SELECT 2` → `LOST 2` / `DELETE 2` / `RESTORE 2` → `CONFIRM` | 管理员管理账户；串口操作直接使用ID，SELECT用于菜单选择 |
| `REDEEM 5` / `REDEEM 10` → `CONFIRM` | 先在查询模式刷对应用户卡；余额足够才提交；重复确认不会重复扣分 |
| `EXPORT` | 仅电脑串口，导出账户和已提交日志；保存串口文本为CSV；日志为物理槽顺序，可按seq排序 |
| `CANCEL` / `STOP` | 取消待确认操作或导出；STOP同时停车 |
| `SERVO 1500`，之后每次增减不超过20 | 仅电脑串口、已ARM、拆连杆后的舵机标定；上电首次仅接受1500 µs |
| `SET CLOSE 1400` → `CONFIRM` | 管理员/本机设置窗口保存闭盖脉宽；数字只是格式例子 |
| `SET OPEN 1700` → `CONFIRM` | 保存实测开盖脉宽；不要直接套用示例值 |
| `SET FULL 65` / `SET CLEAR 85` → `CONFIRM` | 实测判满/清满距离，单位mm；默认值仅初始候选 |
| `SET PWM 25` → `CONFIRM` | 实测限速后的最大占空比；代码限制1～40%，不是速度闭环 |
| `SET ADC_SCALE 1000` → `CONFIRM` | 电池电压比例系数，千分比，800～1200；据万用表读数计算 |
| `SET ROLL_ZERO 0` / `SET PITCH_ZERO 0` → `CONFIRM` | 安装姿态偏置，单位0.1度；以平放读数标定 |
| `SET LIGHT_ON 2700` / `SET LIGHT_OFF 2000` → `CONFIRM` | 明暗阈值，按实际ADC极性设置 |
| `SET CALIBRATED 1` → `CONFIRM` | 确认电气输入、舵机、倾角、速度、桶满等已实测；该标志不是自动校准 |
| `SET MUTE 1` / `SET MUTE 0` → `CONFIRM` | 持久化静音/解除静音 |
| `CARD_READ` / `CARD_WRITE` | 管理员，专用MIFARE Classic 1K测试卡、默认Key A为六个FF；只访问块4 |

CARD_WRITE会把块4原数据输出为 `CARD_ORIGINAL`，写入SBIN测试数据并回读；先保存串口日志。块0及尾块7无写入入口。卡片实验与本地积分账本独立。

蓝牙可STATUS、RAW、STOP、CLEAR、切换普通模式及运动；不可ARM、导出或管理账户。错误命令不刷新运动时限。两路RX溢出或线路错误锁停。

## 本机菜单

MODE短按切换菜单，MODE长按800 ms确认；旋钮转动选择、按下确认；BACK立即停并取消待确认操作。选择挂失/注销菜单时，旋钮选择用户ID。最近记录旋钮切换两页各5条；排行榜显示有效普通用户前5名，同分按ID升序。

提供投放、查询、遥控、1/2站循迹、便捷开盖、记录、排行、账户管理、兑换、维护、卡片实验、清锁、关盖、静音、ARM、DISARM和环境页。ARM每次重启后需重新确认，不持久保存。

## 需要根据实物修改的编译配置

编辑 `include/config.h` 后重新编译：

- 核心晶振要求8 MHz，系统72 MHz；更换晶振必须修改 `platform.c` 时钟配置，不能只改显示值。HSE失败锁住运动；时钟失效NMI撤输出。
- OLED默认SSD1306、地址0x3C；SH1106需设 `OLED_SH1106=1`，包含两列偏移及对应电荷泵初始化。尺寸为128×64。
- MPU6050默认0x68；AD0高时改为0x69，WHO_AM_I仍按0x68检查。
- 对射、障碍、闭盖、循迹、靠近、DFPlayer BUSY的有效电平；经NPN适配会反相。急停PB13、碰撞PB12固定高为故障，不能为绕开故障随意改成反向。
- 电机左右反向、有源/无源蜂鸣器及有效电平、编码器每格边沿数、光敏AO/DO模式。
- 外部FLASH仅允许Winbond JEDEC `EF4015/16/17/18`（W25Q16/32/64/128、3.3V系列）。未知ID只读身份，不擦写。实物不在此列表时应按型号适配驱动，不能硬改为“已识别”。
- 独立看门狗入口已实现，`ENABLE_WATCHDOG=0` 是首轮台架默认；完成停止与任务时序测试后置1，再验证复位行为。禁止在中断中无条件喂狗。

## 存储格式与恢复

FLASH 0x000000、0x001000为双4KB快照；0x002000～0x011FFF为16扇区环形日志；0x012000保留TEST区域，本版业务不使用它。

每条事务64B，CRC-32/ISO-HDLC，提交字最后写。快照有效负载2304B，含64个32B账户槽、参数、序号、CRC和提交字。日志每扇区64B头＋63条事务。每256笔或回收需要时保存另一份快照，再允许擦掉被其覆盖的日志；任何NOR等待都分步返回主循环。

REGISTER、STATUS、DEPOSIT、REDEEM、BOOT沿用手册的字段顺序。CONFIG（type=5）将字节16～37作为22B参数载荷，不将这些字节误当余额或日期；CSV以CONFIG行标记。新增ADMIN_RECOVER（type=7）只改角色及状态、保持积分和次数。格式版本为1，不兼容其他程序私有账本。boot_id/uptime仅表示启动编号与运行时长，不是日期时间。

恢复检查双快照、CRC、提交标记、连续序号、完整UID及余额一致性。两个快照均无效且区域非全FF时进入CORRUPT，不自动格式化。序号接近32位上限拒绝新事务，需先导出维护。断电模拟已测试；真实供电坍塌、SPI干扰和芯片行为仍须实验验证。

## 功能与文件对应

| 功能 | 实现位置 |
|---|---|
| A1～A9：完整UID、账户/权限、积分、查询、掉电保存、卡块实验、记录排行、兑换 | `rfid.c`、`storage.c`、`console.c`、`app.c` |
| B1～B5/B8：开盖、经过检测、去重超时、便捷、满桶、维护 | `app.c`、`devices.c` |
| C1/C2/C3/C4/C6/C8/C9：移动、障碍、循迹、站点、遥控、倾角、碰撞 | `app.c`、`platform.c`、`devices.c` |
| D1～D8：界面、蜂鸣、按键旋钮、停止、自检、电压、导出 | `console.c`、`devices.c`、`platform.c` |
| E1/E2/E4：温湿度、光控、语音 | `devices.c` |

已有功能清单仍称“33项”，原验收表保留原编号；本表按其列出的全部编号建立实现对应，不重新删改编号。

## 验证范围

实际运行了四组原生C测试，直接链接交付源码：账本掉电/日志回收、业务互锁/单次积分、RFID协议状态机、DHT及超声/MCP。模拟外设不验证真实电压、波形、机械动作或未提供型号的兼容模块。

实际运行了Arm Compiler命令行编译和Keil Rebuild；内存严格按64KB Flash、20KB SRAM链接，保留4KB栈，不使用动态分配。具体大小、散列和测试结果见 `release/validation.json`。命令行的旧汇编器会给出弃用提示；Keil重编译结果另记录，不能混为同一次构建。

未连接或烧录用户硬件，未把任何实物验收项标成通过。最终仍需按仓库 `docs/ACCEPTANCE.md` 逐项验收。

## 协议依据与第三方文件

- [ST RM0008](https://www.st.com/resource/en/reference_manual/cd00171190-stm32f101-103-105-107-stm32f100-series-armbased-32bit-mcus-stmicroelectronics.pdf)：寄存器、定时器和中断配置。
- [NXP MFRC522](https://www.nxp.com/docs/en/data-sheet/MFRC522.pdf)：读卡器寄存器、收发、认证。
- [Winbond W25Q32JV资料入口](https://www.winbond.com/hq/support/documentation/?__locale=en&category=%2F.categories%2Fresources%2Fdatasheet%2F&family=%2Fproduct%2Fcode-storage-flash-memory%2Fserial-nor-flash%2Findex.html&line=%2Fproduct%2Fcode-storage-flash-memory%2Findex.html&pno=W25Q32JV)：NOR命令与参数。
- [DFRobot DFPlayer说明](https://wiki.dfrobot.com.cn/_SKU_DFR0299_DFPlayer_Mini%E6%A8%A1%E5%9D%97)：串口帧和MP3目录编号。
- 设备头文件来自已有 `firmware/legacy/SmartBin_F103/CMSIS/Device`，版权保留。`src/startup.s`仅调整栈到4KB、堆到0。
- `vendor/CMSIS5_Core` 为本机已有CMSIS5头文件的所需子集，保留Arm Apache-2.0许可；原归档CMSIS6头文件不完整，不直接混用。应用和字模为本轮实现。
