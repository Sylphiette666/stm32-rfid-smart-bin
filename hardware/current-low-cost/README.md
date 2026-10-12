# 当前制作方案：A1裸PCB手焊

采用STM32F103C8T6核心板、外置MCP23017成品扩展模块与一块100×100mm双层A1 PCB，替代原PWR、IO两块洞洞板。优先复用用户已购的直插电阻、径向电容、SN74AHCT125N和DIP14座、TO-92三极管、端子及模块；本轮选择裸板自行焊接，不改为SMT代焊。AO3400A是已购裸管，仍须焊到转接板再按G/S/D接PCB。

制作先读[A1 PCB说明](pcb-a/README.md)，再核对[逐针接口表](pcb-a/connector-map.csv)、[制造BOM](pcb-a/manufacturing/bom.csv)及[当前接线说明](WIRING.md)。[原理图PDF与KiCad工程](pcb-a/kicad/)用于查电路；[Gerber_RS274X.zip](pcb-a/manufacturing/Gerber_RS274X.zip)用于裸板制造。下单前仍要按A1说明核实实际元件封装、生产参数与制造预览。

完整装配以[同名图解增强版Word](../../docs/manual/STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx)第63章（图45—49）和[330步阅读版](../../docs/manual/ASSEMBLY.md)为准，原步骤编号不重编。PCB铜箔已替代原142条默认内部连线，不再照旧孔位表补线；板外模块及条件电平转换仍按实际型号逐根接线。核心3V3与外设3V3不得并联，动力线不能用细杜邦线。

A1只有JP3—JP10共8组跳帽，没有JP1、JP2。U1第三通道已固定PB9输入、/OE接地，蜂鸣信号通过JP3选择，不能执行旧洞洞板的拆线改接。规则基线为低压普通双层板：间距0.20mm，常规信号线0.30mm、局部0.25mm，过孔外径/孔径0.8/0.4mm，电源主干/分支3/2mm；这些几何规则不替代实际带载温升测试。

[原双洞洞板资料](perfboard/)继续保留，作为历史制作参考；[PCF8574 V2.1 PCB](../archive/pcb-v2.1/)也仅归档，二者都不是A1的接口或制造文件。原洞洞板JCORE、JMCP、JACT、JP9等位号不能直接套到新PCB。资料已做设计检查，不代表已经制作实物并通电通过。

机械图集中在[手册源资料](../../docs/manual/source/)和[裁剪图解](../../docs/manual/cutting-diagrams-20261010/)。当前活动盖用2mm PVC、固定壳体用3mm PVC、五片内胆用1mm PP；原机构和质量目标保留，PCB100×100mm外形须在托板上用纸样试放、留出端子进线及维修空间。
