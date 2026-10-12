# PCB A1 图解增强版手册交付 QA

状态：可由根代理替换同名 canonical 与仓库文件。子代理未替换或上传任何 canonical 文件。

## 定稿文件

- Word：`D:\Work\嵌入式课设\.pcb-lowcost-20261012\a-manual\staging\STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx`
- Word SHA-256：`e372c23d2ecc6cd6eccb2e3e2e680ce35942d956c96c20b01de713b023563885`
- PDF：`D:\Work\嵌入式课设\.pcb-lowcost-20261012\a-manual\render_release2\manual.pdf`
- PDF SHA-256：`7464bf74994f583f1cab3358a1883e85be1f48085315ef512d60964a81177ec4`
- 可检索全文：`D:\Work\嵌入式课设\.pcb-lowcost-20261012\a-manual\render_release2\word_text.txt`
- 结构检查：`audit_render_release2.json`
- Word 隔离渲染：`word_render_release2.json`
- 可复现编辑源：`build_manual.py` 与 `build_audit.json`

## 内容与保留检查

- 198 页，330 个原始“步骤 xxx”标题完全相同且顺序不变。
- 原 52 幅内嵌图字节全部保留；追加图 45–49 后共有 57 幅内嵌图，其中操作图解 49 幅。5 张新图的嵌入字节与最终源图完全一致。
- 64 张表；原 51 张表只发生脚本记录的授权修订；181 个接口端点均唯一且与最终 connector-map.csv 的网络、外接名称一致。
- 无未完成图占位。实际上电验收表的空白记录栏有意保留，不冒填实测通过。
- 同名原文件保持原始 SHA-256 f7d0c5ce51f904e58d40f9733fe5b030d29f31db53e26faf53ad6d21b3713187，未触碰用户主文件。
- 封面与前文切换到 PCB A1；章节 61、图 36–39、旧 142 条导线和五拆六增标为历史归档；章节 63 为当前施工入口。章节 60/62 机械内容继续保留。
- 目录已更新：第 62 章在 170 页、第 63 章在 177 页；页脚日期为 2026 年 10 月 12 日。

## 视觉复核

已生成本版全部 198 页 PNG 与 PDF。文档技能规定的 render_docx.py 先行尝试，当前环境无 LibreOffice；诊断保留在 render_skill_01.log。随后用已验证归属的独立 Word COM 实例完成更新目录、保存、PDF 导出和逐页 PNG 渲染。

前期对全部发生修订的页段进行联系表复核，并对主要电气、装配表格和机械归档边界的页面放大检查；原版 102 页正文像素完全一致，可继承旧版已完成的视觉验收。新增与变化合计 96 页，详见结构审计中的逐页列表。

最终对新增第 63 章 177–198 页全部逐页放大查看，另复核封面、目录末页及旧章尾页 169。检查了五幅新图完整性、字号、标签清晰程度、图注、镜像方向、跨页表头、内容边界与页码。无裁切、重叠、误空页或无法辨认的表格列。图内密集 PCB 位号需按图注放大电子图核查，正文另外给出完整逐针表。

最后补充了图 45 下方的极性说明：板上“PIN 1=SQUARE PAD”只用于 J/JP 接口；电解电容按“＋”确认正脚，不凭轮廓猜测。对此重新全量渲染。render_release2 与先前已逐页审阅的 render_release 的 198 张 PNG 比较，仅第 178 页不同；该页已重新放大复看，说明完整放在同页、未导致后续移页。

最终输出目录必须使用 **render_release2**，不要采用旧 render_final 或 render_release。

## 电气与制造结论的边界

独立电气审阅确认新章的接线条件与设计相符。手册注明 5V 星形三支路、CORE/EXT 不并联但仍有反灌路径、独立 USB 台架拔全部核心线束、AHCT 第 3 路固定使能及 R36/R37 互斥、跳帽条件、模块按针名接线与急停实际边界。

制造数字审查由根代理与独立审核人完成，当前冻结 PCB SHA-256 为 b16aad367273b6b39cf8452db6615a54745bc44198ac9485f1a253c8de96b066，Gerber ZIP SHA-256 为 d613507ebb631bb055847faf6cc9197b1f7f826a0880b4674f329b2af03ee1cf。review/07-final-manufacturing-review.md 记录 32 项 PASS、0 FAIL、0 PENDING；本次原理图 ERC 为 0 错误/0 警告，PCB 按项目规则 DRC 为 0 违规/0 未连/0 一致性差异。手册明确保留规则配置和忽略项的检查范围；这些结论不代表实物焊接、通电或全部固件已经完成。

## 用户进程与发布

最后 Word COM 实例归属已验证：专用 PID 27852；渲染前用户 Word PID 为 [14952, 41796]。日志 user_instances_touched=false，无清理警告。没有关闭、操作或保存用户打开的 Word 文档。

根代理下一步：按本报告的 SHA 复制暂存 Word 到原同名文件与仓库；复制对应 PDF/图源/QA 所需材料，执行既有 GitHub 上传授权。无需再次改写该 Word。
