from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).resolve().parent;W=R/'working';O=W/'review/four-skills';O.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for src,name in [(R/'analysis','before'),(R/'analysis-after','after')]:
 dest=O/name;dest.mkdir(exist_ok=True)
 for p in src.iterdir():
  if p.is_file() and p.suffix in ('.json','.log','.rpt'):shutil.copy2(p,dest/p.name)
for f in ['plan_stitch.py','stitch_ipc.py','audit_native.py','audit_cli.py','metadata_cli.py','passive_spice.py','run_review.py']:
 shutil.copy2(R/f,O/f)
data=load(W/'circuit.json');parts={p['ref']:p for p in data['parts']}
native=load(W/'review/04-native-final-audit.json');before=load(R/'analysis/native-audit.json');after=load(R/'analysis/native-audit-working.json')
sources={'U1':'https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf','Q1-Q3':'https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf','MCU':'https://www.st.com/resource/en/datasheet/stm32f103c8.pdf','MCP':'https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf','AO3400A':'https://www.aosmd.com/res/data_sheets/AO3400A.pdf'}
deep={'scope':'Manual datasheet cross-reference plus structured native pad/net audit; external purchased modules not physically verified.', 'sources':sources,'board_sha256':sha(W/'kicad/SmartBin_A.kicad_pcb'),'ic_checks':[
 {'ref':'U1','specified_part':'SN74AHCT125N','source':sources['U1'],'pages_1_based':[3,4,5], 'pins':parts['U1']['pins'],'result':'PASS for specified TI PDIP-14','checks':['VCC14=5V_BUS,GND7=GND','OE1/2/3 grounded; OE4=VCC, A4=GND, Y4=NC','3.3V MCU level exceeds 2.0V VIH at 4.5-5.5V supply','R6/R7/R36 establish default levels; R36/R37 mutually exclusive','Outputs drive module logic inputs, not buzzer element or motor load'],'limitations':['C8 VCC distance 5.24mm; DIP opposite-corner ground return; EMC warning retained','Asynchronous power ramp not simulated; no hot-plug claim']},
 {'ref':'Q1,Q2,Q3','specified_part':'2N3904 using onsemi E-B-C reference','source':sources['Q1-Q3'],'pages_1_based':[1,2], 'pins':{r:parts[r]['pins'] for r in ['Q1','Q2','Q3']},'result':'PASS reference pinout; purchased-brand pinout needs physical verification','checks':['Pad1=emitter GND, pad2=base, pad3=collector','Q1 detects NC loop, Q2 clamps STBY, Q3 supplies independent status','At 8.4V and assumed VBE0.7V, R15/R17 nominal dissipate about12.6mW','With EXT3.3V present Q2 base current approx0.55mA and clamp demand <=3.3mA through1k'],'limitations':['EXT power loss cannot guarantee hardware inhibit','Stop circuit not independent safety-rated power disconnect']},
 {'ref':'External modules','result':'CONDITIONAL','checks':['STM32 runs from CORE3.3V; RC522/FLASH/MCP use compatible3.3V interfaces','MCP23017 GPA7/GPB7 not assigned input functions','External buck, BSS138, AO3400A and TB6612 physical pin order remains label-based','CORE/EXT regulator outputs not paralleled; signal-mediated backfeed remains possible'],'limitations':['No complete external module schematics or vendor MPN inventory','No oscillator/regulator/RF antenna layout reviewed; all external']}
 ],'native_reference_and_net_match':native['native_definition_match'],'dnp_native_vs_bom':'9 native schematic DNP flags match circuit.json. kicad-happy statistic dnp_parts=0 is a parser limitation; no source fix needed.','thermal':'Automatic analyzer assessed 0 parts. Divider and base-resistor dissipation bounded separately; no measured motor/buck/board temperature.'}
(O/'deep_review.json').write_text(json.dumps(deep,ensure_ascii=False,indent=2),encoding='utf-8')
rows='\n'.join(f"| {n} | {before['native_gnd_coverage'][n]['coverage_pct']}% | {after['native_gnd_coverage'][n]['coverage_pct']}% |" for n in ['PA5','PA6','PA7','I2C_SCL','I2C_SDA'])
report=f'''# SmartBin A1 四套技能联合设计审查

2026-10-12。结论：本次完成 A1 的接地加强改版，裸板制造检查通过；保留已购模块、全部接口、BOM 和原有手焊方式。**这是供单台课设验证的原型版本，EMC 布局审查仍有残留风险，不能将 DRC 零错误理解为整机抗干扰、温升或功能已通过。**

## 实际使用的四套技能

| 技能来源 | 本次实际工作与证据 |
|---|---|
| [HubertHQH/KiCad-skills](https://github.com/HubertHQH/KiCad-skills) | kicad-connect 连接真实 KiCad 10.0.6；按 kicad-pcb 的 IPC 事务方法加入 55 个 GND 过孔，铺铜并保存。证据 before/hubert-ipc-edit.json。制造导出采用经验证的 KiCad CLI，未假称全部 IPC 导出接口可用。 |
| [mash/kicad-skills](https://github.com/mash/kicad-skills) | kicad-tool/workflow 及本地结构化扩展检查 ERC、原理图与 PCB 一致性、原生几何和 DNP；未用文本替换修改 CAD。 |
| [aklofas/kicad-happy](https://github.com/aklofas/kicad-happy) | 执行原理图、PCB、交叉、Gerber、EMC、热、生命周期和 SPICE 探测；另核对原厂手册，并通过 ngspice-46 DLL 完成两处分压共六组直流仿真。原始输出保留在 before/after。 |
| [Toaster496/PCB-design](https://github.com/Toaster496/PCB-design) | 按 pcb-flow、布线/设计规则/布局及 pitfalls 阶段清单复核，逐项记录适用范围和未满足项目，见 phase-checklist.md。 |

四套流程依本机整合说明协作；同一 PCB 只由一个后端写入。IPC 保存并关闭本次实例后才转 CLI。没有更改用户既有 Word 会话，没有下单或购买元件。

## 改了什么

新增 55 个 0.8mm 焊盘、0.4mm 钻孔的 GND 过孔，使双面地铜在更多位置互连。原有 62 个信号过孔保留，总计 117 个；411 个金属化孔加 4 个非金属化安装孔与钻孔文件逐一匹配。过孔由板厂完成，无新增手焊动作、元件或模块采购。

未改动 1117 段原有走线、94 个位号、293 个有网络连接的电气引脚及 1 个明确 NC 引脚。原计划 33 段电源/地粗线全部保留，宽度和路径没有缩小。100×100mm 板框、90×90mm 安装孔中心距、181 个接口针脚定义与原方案相同。

## 数字检查和测量结果

| 检查 | 结果 | 范围 |
|---|---|---|
| KiCad ERC | 0 违规 | 层次原理图；工程自带规则 |
| KiCad PCB DRC | 0 违规、0 未连接、0 原理图差异 | 最终重新铺铜后的 PCB |
| 原生定义核对 | 94 个位号逐针一致；33/33 粗电源线段保留 | circuit.json 与原生 PCB 对照 |
| Gerber / Excellon | 9 个制造文件；411 PTH + 4 NPTH 一一匹配 | 坐标、孔径、镀孔分类、层识别和独立 CAM 图 |
| SPICE 分压 | 电池满电标称1.953V，1%最坏高值1.984V；Echo标称3.125V，5.15V输入及1%误差下3.243V | 不带 MCU 钳位/寄生/模块模型的直流网络；不是全机仿真 |
| 热分析自动工具 | 执行但0个器件可评估 | 缺少完整模块功耗、MPN与热模型，不能记作热验证通过 |
| 生命周期工具 | 执行但0个物料完成查询 | 未编造已购物料型号或库存 |

独立 GND 覆盖抽样采用 KiCad 已填充多边形，对信号另一面每约2mm取样，检查中心与0.5mm邻域。它用于比较改版，**不是阻抗或 EMC 合格率**：

| 网络 | 改版前 | 改版后 |
|---|---|---|
{rows}

PA6 下方仍无该指标定义的连续地铜，PA7 覆盖也偏低；局部地回流需要绕行。55 个过孔改善了整体接地，但没有彻底重排双面信号走线。自动 EMC 输出由114项变135项，其中45 error、44 warning、46 info；增加的返回路径检查在有地过孔后才启用。风险评分79→70只是工具启发式结果，**不能宣称警告清零或达到认证标准**。

## 告警逐类处置

| 项目 | 处理结论 |
|---|---|
| 无专门 GND 过孔 | 已改进：新增55个，并确认0未连。原本59个GND通孔焊盘已提供直流层间连接；新增孔用于缩短局部回流。 |
| GP-001 地铜覆盖、RP-001 换层回流 | 真实布局限制保留。PA5/PA7与I²C部分改善，PA6等仍需实物看波形；不能直接提升到高速、长排线环境。 |
| DC-001 U1/C8距离 | C8正脚距U1.14约5.24mm，地脚到U1.7直线约25.02mm；DIP14两电源脚分布在相对角。保留为布局警告，验证U1处5V波形；现有去耦不能被描述为最优。 |
| J11/J12无独立GND脚 | 两排属于同一个MCP模块线束，GND在J10.2。必须将J10/J11/J12一起短线连接；不允许只接信号排针运行。 |
| SS-001 缺少MPN | 字段缺失属实，自动PCBA采购门槛不适用于本次仅订裸PCB、手焊已购件。仍需按bom.csv实测已购端子、TO-92脚序和电容尺寸；当前BOM不可当作已配齐料号的SMT订单。 |
| PS-002 5V平面分裂 | 误判：本板两个灌铜区均为GND，5V为显式走线。KiCad原生核对、全部粗线段覆盖与0未连支持其连通，不照此提示向信号区盲目加5V铺铜。 |
| DNP统计0 | 分析器遗漏：结构化读取原理图确认R8/R9/R13/R14/R27/R28/R29/R33/R37共9个原生DNP标记，与BOM匹配。没有修改原理图来迁就错误统计。 |
| 无专用TP封装 | 已有通孔接口可作探测位置；用绝缘细探头按下面表格测量，避免短接邻脚。 |
| 缺少锡膏层/钢网/CPL | 本版全手焊裸板，不适用。制造包不需要这些文件。 |
| CAM解析提示 | KiCad G90头位置和RoundRect尾参数提示没有造成孔/焊盘偏移；逐孔及实际图层核对通过。 |

## 上电与信号验证条件

先按图解增强版第63章逐段供电验收。电机和舵机主电流走 J1–J6 及端子导线，不能通过杜邦线或核心板稳压器。所有模块按实物丝印逐根接；两路3.3V稳压输出不并联；核心板USB单独调试时拆开整个核心板接口线束，以免信号路径反灌电。

首次 RC522 测试使用短线（建议每段不超过10cm），SCK与地线并行靠近，线束避开电机线。STM32 SPI1 若PCLK2=72MHz，可先设分频256，即281.25kHz；I²C先100kHz。降低时钟频率不会消除快边沿或修复地平面裂隙，只用于减少初次调试变量。通过后再按实测波形和错误率决定提速，不能把工具评分作为依据。

| 探测点 | 首次验收参考 |
|---|---|
| J1.1 对 J1.2 | 受保险丝/总开关保护的2S电池电压，满电不超过8.4V |
| J3.1 对 J3.2 | 降压空载先调5.00V，接负载后按手册验证跌落；本方案Echo计算上限5.15V |
| U1.14 对 U1.7 | 正常约5V；观察电机/舵机启动时是否跌落或出现毛刺 |
| J8.3 对 J8.2 | CORE约3.3V；先确认接口表和丝印再落探头 |
| J7.3 对 J7.2 | EXT约3.3V；不能短接到CORE稳压输出 |
| JP9.1 对GND | 电池8.4V时分压约1.95V；闭合JP9前确认 |
| J21.4、PB1 对GND | Echo原始高电平约5V，分压后约3.125V；用示波器/逻辑工具观察，万用表不适合量短脉冲峰值 |
| STBY_OUT 对GND | 急停按下后应为低，软件锁存后不能自行恢复行驶；先悬空车轮验证 |

U1须是AHCT125的PDIP14型号；普通HC125不能直接沿用本方案3.3→5V阈值结论。[TI手册]({sources['U1']})。Q1–Q3按1=E、2=B、3=C参考封装，所购品牌仍须核对。[onsemi手册]({sources['Q1-Q3']})。MCU电源/IO约束与MCP限制分别参见[ST手册]({sources['MCU']})和[Microchip手册]({sources['MCP']})。

急停现有电路属于驱动禁止加软件锁存，不切除全部能源，EXT3.3V失电时硬件钳位不保证成立。保留外部总开关及保险丝。尚未验证实际焊接、元件包络、堵转电流、温升、动态电源、机壳布线和整机固件。

## 最终文件身份

- PCB SHA-256：`{sha(W/'kicad/SmartBin_A.kicad_pcb')}`
- Gerber ZIP SHA-256：`{sha(W/'manufacturing/Gerber_RS274X.zip')}`
- BOM及接口表与上一版逐字节一致。更新后的图46取自当前制造源；下载打板时以本目录最终ZIP为准。

`before/`保留初始报告，`after/`保留最终分析。自动严重等级保持原样，没有删除告警伪造全通过。审查范围不含外置成品模块内部电路、射频天线、固件完备性或实验室EMC认证。
'''
# Verify every listed test header against electrical definition before writing.
assert parts['J8']['pins']['3']=='3V3_CORE' and parts['J8']['pins']['2']=='GND'
(O/'四套技能联合审查报告.md').write_text(report,encoding='utf-8')
print(json.dumps({'report':str(O/'四套技能联合审查报告.md'),'board':sha(W/'kicad/SmartBin_A.kicad_pcb')},ensure_ascii=False))
