"""Document four concurrent P2S body jobs; retain all prior assembly content."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
OUT = BASE / 'parallel-four-p2s-20261101'
WORK = REPO.parent / '.p2s-parallel-20261101/manual'
WORK.mkdir(parents=True, exist_ok=True)
NAME = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
data = load(OUT / 'checks/final_printing.json')
assert data['status'] == 'PASS' and len(data['plates']) == 4
first = load(OUT / 'checks/first_layers.json')
assert sum(p['objects_with_first_layer_id'] for p in first.values()) == 8
contents = ['底板后半片', '底板前半片', '完整上平台', '舵机支架＋喇叭圈＋3块连接片']


def duration(s):
    s = round(s)
    return f'{s//3600}小时{s%3600//60}分{s%60}秒'


readme = '''# 四台空闲P2S并行打印剩余主体

1号机继续当前43件附件精细盘，不用停止。下面四份工程分别给另外四台P2S，每份只打印一次；2至5号是便于分工的标签，不是设备序列号。无需等1号机结束。

| 机器 | 打印文件 | 内容 | 件数 | 预计时间 | PLA |
| --- | --- | --- | ---: | --- | ---: |
'''
for i, p in enumerate(data['plates'], 2):
    readme += f"| {i}号 | [{Path(p['file']).name}]({p['file']}) | {contents[i-2]} | {p['objects']} | {duration(p['estimated_seconds'])} | {p['filament_g']:.1f} g |\n"
readme += f"\n四台同时启动，新增任务约 **{duration(data['parallel_elapsed_seconds_if_started_together'])}** 全部完成，不必把四台耗时相加；建议先启动时间最长的上平台。整套何时完成，还要取决于1号机附件盘的剩余时间。四台共约{data['total_filament_g']:.1f} g PLA。\n"
readme += '''
四份分别作为项目打开，检查所选机器是对应的空闲P2S、0.4 mm喷嘴、PLA和纹理PEI板，然后保持工程参数重新切片，逐台发送。不要把四个文件合并成一盘。保持100%比例、原朝向和排布、逐层打印、标准100%速度；开启调平，检查首层后再离开。

主体保持0.24 mm层高、首层0.20 mm、4墙、30% gyroid、顶底7层/最小1.6 mm、外墙60/内墙100 mm/s。大板居中平放，所有工程的外侧防翘边增为5 mm、间隙0；自动支撑和擦料塔关闭。Generic PLA喷嘴220℃、纹理PEI 60℃，实际耗材和板型必须一致。保留喷嘴缠料检测关闭，相机炒面检测可开。正在打印的附件工程仍是0.16 mm，不能用本版参数覆盖它。

本版只重新分盘和移动XY位置，零件网格形状、尺寸和打印朝向不变。底板仍按已允许的原尺寸拼接方案，用两个平放半片和三块连接片组装；上平台整片平放。四台8件加正在打印的43件正好51件，没有重复附件。后续不要再打印旧body-after-accessories三盘或flat-split全量三盘。

底板连接五金和装配见[原尺寸拼接说明](../flat-split-20261101/README.md#底板如何拼接)：新增12颗M3×16低圆头螺钉、24片外径≤6 mm且厚0.5 mm垫圈、12颗高4 mm M3防松螺母。先拼接，再装PCB；夹具五金另计。

四项实际切片返回0且无警告；原生工程与受测模型一致、不含G-code。已核对8件直接贴床，首层模型和防翘边均在床内，43件附件未重复。尚未实物打印、承重或寿命验证。
'''
(OUT / 'README.md').write_text(readme, encoding='utf-8', newline='\n')

source = REPO / 'docs/manual' / NAME
if not (WORK / 'before.docx').exists():
    shutil.copy2(source, WORK / 'before.docx')
assert sha(source) == sha(WORK / 'before.docx'), 'Published document changed during preparation.'
doc = Document(WORK / 'before.docx')
assert not any('66.8' in p.text for p in doc.paragraphs)
h = doc.add_paragraph('66.8  五台P2S并行打印分工', style='Heading 2')
h.paragraph_format.page_break_before = True
h.paragraph_format.space_before = Pt(0)
h.paragraph_format.space_after = Pt(10)
for run in h.runs:
    run.font.color.rgb = RGBColor(0, 0, 0)


def paragraph(text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.15
    for run in p.runs:
        run.font.size = Pt(10.5)
    return p


paragraph('1号机继续当前43件附件精细盘。其余四台P2S可同时打印下表内容，不用等附件盘完成；2至5号只是分工标签，发送时选择相应空闲设备。')
t = doc.add_table(rows=1, cols=5)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
widths = [1.2, 5.8, 1, 4, 2.5]
for c, w in zip(t.columns, widths):
    c.width = Cm(w)
headers = ['机器', '内容', '件数', '预计时间', 'PLA']
for cell, text in zip(t.rows[0].cells, headers):
    cell.text = text
for i, p in enumerate(data['plates'], 2):
    for cell, value in zip(t.add_row().cells, [f'{i}号', contents[i-2], str(p['objects']), duration(p['estimated_seconds']), f"{p['filament_g']:.1f} g"]):
        cell.text = value
borders = OxmlElement('w:tblBorders')
for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
    b = OxmlElement('w:' + side)
    for k, v in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
        b.set(qn('w:' + k), v)
    borders.append(b)
t._tbl.tblPr.append(borders)
t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
for ri, row in enumerate(t.rows):
    row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    for ci, cell in enumerate(row.cells):
        cell.width = Cm(widths[ci])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        pr = cell._tc.get_or_add_tcPr()
        margins = OxmlElement('w:tcMar')
        for side in ['top', 'left', 'bottom', 'right']:
            e = OxmlElement('w:' + side)
            e.set(qn('w:w'), '80')
            e.set(qn('w:type'), 'dxa')
            margins.append(e)
        pr.append(margins)
        if ri == 0:
            shade = OxmlElement('w:shd')
            shade.set(qn('w:fill'), 'E7EFF3')
            pr.append(shade)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 1 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            for run in p.runs:
                run.font.size = Pt(9.5)
                run.bold = ri == 0
paragraph(f"四台同时启动，新增任务约{duration(data['parallel_elapsed_seconds_if_started_together'])}完成，共用PLA约{data['total_filament_g']:.1f} g。整套完成时间取决于上述最长任务与1号机附件盘剩余时间；不要将四台耗时相加。建议先启动上平台。")
paragraph('文件位于parallel-four-p2s-20261101/projects/：')
for p in data['plates']:
    q = paragraph(Path(p['file']).name)
    q.paragraph_format.space_after = Pt(3)
    for run in q.runs:
        run.font.size = Pt(9)
paragraph('四个文件分别作为项目打开，确认对应设备、P2S 0.4 mm、PLA和实际板型，重新切片后逐台发送。保持100%比例、原朝向、逐层打印及标准100%速度；每台都检查首层。')
paragraph('主体沿用0.24 mm层高、首层0.20 mm、4墙、30% gyroid、顶底7层/最小1.6 mm；外墙60/内墙100 mm/s。外侧防翘边增至5 mm、间隙0；自动支撑和擦料塔关闭。正在打印的附件盘保持0.16 mm。')
paragraph('本版仅分盘及平移位置，尺寸和打印朝向不变。底板两半与三块连接片仍按66.1、66.2组装，上平台一整片；8件加43件正好51件。无需再打印66.7的三盘主体或66.3至66.5全套盘，避免重复。')
paragraph('四盘已完成实际切片及首层床面边界检查，尚未实物打印、承重或寿命验证；底板拼接五金及试装要求仍按本章执行。')
old = Document(WORK / 'before.docx')
steps = lambda d: [p.text for p in d.paragraphs if re.match(r'步骤 \d{3}', p.text)]
tables = lambda d: [[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
assert steps(doc) == steps(old) and len(steps(doc)) == 330
assert tables(doc)[:len(old.tables)] == tables(old)
doc.save(WORK / NAME)
(WORK / 'authoring_checks.json').write_text(json.dumps({'original_steps_preserved': 330,
    'all_existing_tables_preserved': len(old.tables), 'baseline_sha256': sha(WORK / 'before.docx')}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'staged_manual': str(WORK / NAME), 'four_jobs_elapsed_seconds': data['parallel_elapsed_seconds_if_started_together']}, ensure_ascii=False))
