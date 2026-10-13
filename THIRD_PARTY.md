# 第三方资料

- `firmware/legacy/SmartBin_F103/CMSIS/`保留原有ARM/ST等版权和许可声明；使用或分发时遵守文件内许可。
- `firmware/a1/vendor/CMSIS5_Core/`是本机已有CMSIS5（Core版本5.6）所需头文件子集，保留Apache-2.0许可和文件版权；没有把不完整的CMSIS6归档与其混编。
- `firmware/a1/src/startup.s`派生自原ST启动文件，仅把栈改为4096字节、堆改为0，保留原版权声明。A1应用代码不引入第三方RFID驱动或字体库。
- 历史KiCad工程所含库封装保留原样，其许可遵循原始库及文件声明。
- 当前A1工程使用的KiCad本地库说明及许可入口见[KiCad库许可记录](hardware/current-low-cost/pcb-a/kicad/KICAD_LIBRARY_LICENSE.md)；本条不改变各库原有的许可与例外条款。
- 文档中的芯片、模块资料链接指向各自权利人的资料。

当前图解增强版Word为198页，保留330个步骤，含57幅图、64张表（49幅操作图解、1幅外观概念图及原7幅图）。各图源目录中168页、175页等数量指对应历史增量，不代表当前版本。第63章采用A1裸PCB替代双洞洞板，第61章仅作历史参照；新图45—49见[A1图解目录](hardware/current-low-cost/pcb-a/diagrams/)，本轮手册更新源见[pcb-a-update-20261012](docs/manual/pcb-a-update-20261012/)。

本次归档未为所有内容统一添加开源许可证。公开或重新分发前需按相应文件的权利与许可处理。
