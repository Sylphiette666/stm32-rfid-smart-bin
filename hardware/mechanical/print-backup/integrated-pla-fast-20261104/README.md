# PLA树形支撑加速候选

**24小时目标尚未达到。** 三件合计约47小时42分，上半件单件约33小时。此次提供可检查的候选，不称为24H成品方案。

|打印件|预计时间|PLA含支撑|
|---|---:|---:|
|[下半主体](projects/P2S_LOWER_H41_B1_PLA_FAST_CANDIDATE.3mf)|13小时41分|373.9 g|
|[上半主体](projects/P2S_UPPER_INTEGRATED_PLA_FAST_CANDIDATE.3mf)|32小时58分|803.0 g|
|[面板盖](projects/P2S_PANEL_COVER_PLA_FAST_CANDIDATE.3mf)|1小时1分|25.3 g|

仍为P2S、0.4 mm喷嘴、纹理PEI、256×256 mm、PLA。两个主体0.28 mm层高，面板盖0.20 mm；三墙、主体10%螺旋体，顶底不低于0.8 mm。外墙120、内墙230 mm/s；实际受官方Generic PLA的12 mm³/s体积流量和悬垂限速约束。未假定未知PLA能支持更高流量。

树形为自动细树形，枝径3、分支间距5、分支角40°、阈值35°、一道支撑壁；支撑与模型同步层高，上下Z间隙0.28、XY间隙0.35 mm，接触上下各两层、间距0.5 mm，主体6 mm裙边。面板盖平放无需支撑。

![下半件实际支撑](preview/LOWER_H41_B1_supports.png)
![上半件实际支撑](preview/UPPER_INTEGRATED_supports.png)

棕色图形抽取实际刀路每3层中的1层显示。支撑已真实生成并检查完整床面范围。作为工程打开projects/内3MF，保持100%比例和已保存方向后重新切片；文件包含模型和参数，不含机器G-code，也没有启动打印。

原CAD模型与安装孔槽未改变，仅刚性旋转、平移上半件。STEP仍使用[上一版模型](../integrated-pla-20261104/README.md)。本版降低层精细度和墙数，不能声称与0.08 mm版本表面质量或强度相同；实打、载荷和拆支撑尚未验证。当前最快候选也不代表数学上已证明不存在更快姿态。

各轮结果保留在checks/*_slicing.json，选用下半件r3、上半件r4和面板r1；r5有机树形、r6混合树形实测没有更快。默认流量下继续实现24小时，需要明确是否允许结构/分件改变，或提供实际耗材流量标定数据。

手册第69章已合入所有新支撑图和首层图。检查参考[GitHub codex-cad](https://github.com/alexanderkoller/codex-cad/blob/main/cad/SKILL.md)、[OrcaSlicer树形支撑参数](https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_tree)。本机为Bambu Studio 02.08.02.61。
