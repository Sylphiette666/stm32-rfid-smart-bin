# PCB A1 图解增强版手册更新归档（2026-10-12）

本目录保存一次已完成的 Word 更新源与校验记录，**不是可直接重复运行的当前手册生成器**。当前正式同名 Word 位于上一级 docs/manual；本目录不再存一份 Word、PDF 或全量页面图片。

本轮结果为 **198 页、57 幅内嵌图、64 张表**；完整保留 **330 个原步骤标题**及原 **52 幅内嵌图**。新增图解 45—49，因此操作图解总计 49 幅。章节 61 的洞洞板内容已标注历史归档，第 63 章为 PCB A1 当前施工入口。图 45 附近特别注明：板上 PIN 1=SQUARE PAD 提示用于 J/JP 接口；电解只按“＋”标记确认正脚。

## 输入基线与发布结果

- 输入基线：Git 提交 `2c79ddb9` 中同名图解增强版 Word，175 页、52 幅内嵌图、51 张表。
- 必须逐字节匹配的输入 SHA-256：`f7d0c5ce51f904e58d40f9733fe5b030d29f31db53e26faf53ad6d21b3713187`。
- 最终经过 Word 更新目录和渲染保存的输出 SHA-256：`e372c23d2ecc6cd6eccb2e3e2e680ce35942d956c96c20b01de713b023563885`。
- 本轮最终 QA 为 `FINAL_QA.md`、`audit_render_release2.json`、`word_render_release2.json`；完整交接路径/哈希见 `FINAL_HANDOFF.json`。
- `build_audit.json` 是进入 Word COM 排版前的原始编辑记录。其状态和输出哈希反映生成当时的暂存阶段；不要把它当成最终发布判定。后续目录更新、保存形成上述最终 SHA。
- 记录中的 `D:/Work/...` 是当轮机器上的证据位置，不能假定其他机器存在。

## 本目录文件

- `build_manual.py`：在特定基线的固定段落/表格索引上进行修订，追加 PCB A1 章节和图解。
- `audit_manual.py`：核原 330 步骤、52 图、表格变更、181 个接口端点、图源新鲜度及渲染差异。
- `retained_formatting.py`、`artifact.md`：保留原文档样式的辅助源和编辑约束。
- `baseline_inventory.json`、`baseline_steps.json`、`baseline_tables.json`、`baseline_parts.json`：基线结构及内容审计快照；它们不替代基线 Word。
- `build_audit.json`：本轮每项段落/表格修改和新图插入的记录。
- `audit_render_release2.json`、`FINAL_QA.md`、`FINAL_HANDOFF.json`、`word_render_release2.json`：最终结构、视觉与隔离渲染证据。
- `render_skill_01.log`：标准渲染器缺少 LibreOffice 的诊断；本轮随后使用专属 Word COM 实例完成排版，没有操作用户现有 Word 进程。
- `contact-169-180.png`、`contact-181-192.png`、`contact-193-198.png`：归档尾部/机械章节交界与整个新增章节的联系表；它们便于浏览，不代替报告中已完成的逐页放大 QA。
- `SOURCE_MANIFEST.json`：本归档目录文件的 SHA-256。

## 需要复现本次更新时

**不要在当前正式 Word 上重复应用脚本；也不要直接在本归档目录运行。** 脚本依靠固定段落和表格索引，只支持上述 175 页精确基线。当前 198 页版本及后续任何手改版均不是输入。源文件按本轮原样归档，没有为了搬迁而修改内容。

在独立、可丢弃的工作目录中恢复下面布局；所有输出仍先写副本，审阅完再按项目流程发布：

```text
reproduction-root/
  STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx  ← 175 页基线副本，仅供审计核对
  .cutting-diagrams-20261010/
    retained_formatting.py
    render_final/page-*.png  ← 若需要原版逐页像素差异，则恢复原版渲染
  .pcb-lowcost-20261012/
    a-design/
      circuit.json
      connector-map.csv
      diagrams/45_pcb_top.png … 49_conditions.png
    a-manual/
      before.docx  ← 从提交 2c79ddb9 提取的基线，必须匹配上述 SHA
      build_manual.py
      audit_manual.py
      baseline_tables.json
      staging/  ← 只放暂存输出
```

当前设计输入可从仓库 `hardware/current-low-cost/pcb-a/` 的对应文件恢复到该独立 a-design 目录；应结合本轮 `build_audit.json` 的电气输入与图源哈希核对，避免拿未来修改版重建旧版本。恢复 Git 中二进制 Word 时使用能保留原始二进制内容的方法，不能通过旧 PowerShell 文本重定向写出文件。先核 SHA，再运行。

`build_manual.py` 现有启动检查要求 `before.docx` 精确匹配基线 SHA；缺少它或不匹配就停止。仍不得用 Python 优化选项绕过断言。`--final` 仅调整构建记录状态，不代表排版/制造/实物已经通过。`audit_manual.py --render render_release2` 需要把本轮副本重新渲染到相应目录后使用。审计中的 `original_still_unchanged` 指复现目录下放置的原基线副本，不是现在仓库的正式手册。

所需 Python 包：python-docx、Pillow；另外要有可用 Word 或 LibreOffice 完成目录更新、分页与 PDF 渲染。字体应具有微软雅黑或核对后替代；不同排版引擎可能改变页数。更新后仍须完整内容审计与实际视觉检查；只执行源脚本不等于完成文档发布。

## 验收边界

本轮确认设计文件检查、手册内容与排版。原理图 ERC 和 PCB DRC 的具体范围、配置与忽略项见硬件发布报告。检查结果不代表实际焊接、通电或全部固件功能完成；手册的实测记录栏保持空白待制作时填写。
