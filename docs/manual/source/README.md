# 文档与示意图源文件

五份JSON分别保存配件、机械、电气、软件和收尾验收内容。`figure_map.json`关联七张装配图，`diagram_spec.json`保存机械坐标数据。

`build_manual.py`使用Python及`python-docx`生成上一级目录的Word。它会覆盖同名文档，运行前先保留需保留的人工修改；在Word中更新目录和页码后再检查分页。运行环境需有“微软雅黑”字体。`draw_manual.py`及`draw_geometry.py`使用Pillow和Windows字体生成示意图。

仓库中的Word是已完成排版检查的交付版本；仅重新运行生成脚本不等于完成了页码更新或视觉复核。`../ASSEMBLY.md`是同一内容的GitHub阅读版。
