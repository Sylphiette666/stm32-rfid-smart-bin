# STM32与RFID积分式智能移动垃圾桶

嵌入式与RFID双课设的设计和实施资料。当前制作路线为**单台低成本、复用已有模块**，主控STM32F103C8T6，使用MCP23017扩展与洞洞板连接。

## 从这里开始

1. [下载图解增强版Word手册](docs/manual/STM32%E4%B8%8ERFID%E6%99%BA%E8%83%BD%E7%A7%BB%E5%8A%A8%E5%9E%83%E5%9C%BE%E6%A1%B6_%E9%80%90%E6%AD%A5%E7%BB%84%E8%A3%85%E4%B8%8E%E8%B0%83%E8%AF%95%E5%AE%9E%E6%96%BD%E6%89%8B%E5%86%8C_%E5%9B%BE%E8%A7%A3%E5%A2%9E%E5%BC%BA%E7%89%88.docx)：168页，保留330个步骤、33项功能；本轮加入5幅SG90图和4幅洞洞板图，现有39幅操作图解、1幅外观概念图及原7幅图，共47幅。[原125页版本](docs/manual/STM32%E4%B8%8ERFID%E6%99%BA%E8%83%BD%E7%A7%BB%E5%8A%A8%E5%9E%83%E5%9C%BE%E6%A1%B6_%E9%80%90%E6%AD%A5%E7%BB%84%E8%A3%85%E4%B8%8E%E8%B0%83%E8%AF%95%E5%AE%9E%E6%96%BD%E6%89%8B%E5%86%8C.docx)保留。
2. [在线阅读全部步骤](docs/manual/ASSEMBLY.md)：按顺序检查、装配和调试，原330步不重编；图解以同名Word最新版为准。
3. [查看当前接线表](hardware/current-low-cost/WIRING.md)和[33项功能验收清单](docs/ACCEPTANCE.md)。
4. [查看SG90等新增图解与说明](docs/manual/illustrated-additions-20261010/)及[洞洞板正反面图、孔位与逐根焊线表](hardware/current-low-cost/perfboard/)。
5. [查看固件开发状态](firmware/README.md)，再开始编写和烧录程序。

## 目录

[查看成品外观概念图](docs/appearance/README.md)（合盖与开盖两种状态，非实物照片）。

| 目录 | 内容 |
| --- | --- |
| `docs/manual/` | 原版及最新同名图解增强版Word、330步阅读版、内容源与图解生成源 |
| `docs/manual/illustrated-additions-20261010/` | 本轮SG90等新增图解及整合说明 |
| `docs/planning/` | 功能成本选型、33项功能机械设计及功能数据 |
| `docs/appearance/` | 成品外观概念图及生成说明 |
| `hardware/current-low-cost/` | 当前MCP23017成品模块方案说明与接线资料 |
| `hardware/current-low-cost/perfboard/` | PWR与IO两块洞洞板的正反面图、孔位表、逐根焊线表及外接说明 |
| `hardware/archive/pcb-v2.1/` | 旧PCF8574方案的嘉立创工程、KiCad、Gerber、BOM和贴片坐标 |
| `firmware/legacy/` | 已有CMSIS基础文件，应用程序待实现 |
| `archive/` | 较早手册、采购表及折叠内胆参考图 |

## 当前状态与版本边界

- 已整理设计、采购、装配、接线、软件实施步骤和验收方法；文档步骤不代表已完成实物验证。
- 当前仓库**没有实现全部33项功能的完整可编译固件**，不能把CMSIS目录当作成品程序烧录。
- 当前方案和旧V2.1 PCB使用不同的扩展器与接线；按各自说明使用，不能混用。
- 2026年10月10日逐步手册为当前装配基线；先前文档中的尺寸、价格和部件选择仅供历史参考。
- 仓库内没有上传账户凭据、订单截图、渲染缓存、临时锁文件或工具依赖目录。

## 更新方式

后续每次增加图解，都加入同名图解增强版Word，更新目录并渲染检查排版，再替换本地与仓库中的同名版本；同步相关接线说明、图片和校验清单后，提交并推送到本仓库。原330个步骤保持编号。实测记录请写日期、硬件版本、固件提交号、测试条件和结果；未完成检查或实测的项目不能写成已完成。

初始归档日期：2026-10-10。文件校验值见[MANIFEST.sha256](MANIFEST.sha256)。第三方资料说明见[THIRD_PARTY.md](THIRD_PARTY.md)。
