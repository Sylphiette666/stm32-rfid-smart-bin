"""Correct the current running job and document the matching 48-part continuation."""
from pathlib import Path
import hashlib,json,re,shutil
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE=Path(__file__).resolve().parents[1];REPO=BASE.parents[2]
OUT=BASE/'parallel-after-old-plate2-20261101'
WORK=REPO.parent/'.p2s-after-old-plate2-20261101/manual';WORK.mkdir(parents=True,exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=load(OUT/'checks/final_printing.json');packing=load(OUT/'checks/packing.json')
assert len(data['plates'])==4 and sum(p['objects'] for p in data['plates'])==48
assert [p['objects'] for p in packing['plates']]==[1,1,23,23]
def duration(s):
 s=round(s);return f'{s//3600}小时{s%3600//60}分{s%60}秒'
contents=['底板后半片','底板前半片','精细附件A（含托片、2块连接片）','精细附件B（含电池托架、1块连接片）']
rows=[[f'{i}号',contents[i-2],str(p['objects']),duration(p['estimated_seconds']),f"{p['filament_g']:.1f} g"] for i,p in enumerate(data['plates'],2)]
readme='''# 当前正确分工：昨天第二盘继续，其余四台打印底板与精细附件

1号机正在打印的是昨天的P2S_MOUNTED_PLATE_2.3mf，内容为完整上平台、舵机支架、喇叭圈，共3件。继续此任务，不用停止。本目录四份新任务排除了这三件。

刚才parallel-four-p2s-20261101按“精细附件盘正在打印”安排，不适用于实际状态，请勿用于本次；也不要再打印43件附件合盘或旧主体三盘，否则会重复。

| 机器 | 文件 | 内容 | 件数 | 预计时间 | PLA |
| --- | --- | --- | ---: | --- | ---: |
'''
for i,p in enumerate(data['plates'],2):
 readme+=f"| {i}号 | [{Path(p['file']).name}]({p['file']}) | {contents[i-2]} | {p['objects']} | {duration(p['estimated_seconds'])} | {p['filament_g']:.1f} g |\n"
readme+=f"\n四台同时开打，新增48件约 **{duration(data['parallel_elapsed_seconds_if_started_together'])}** 完成，PLA合计{data['total_filament_g']:.1f} g。整套完成时间还取决于1号机昨天第二盘的剩余时间。2至5号为分工标签，不是设备序列号。\n"
readme+='''
每份文件各打印一次。分别作为项目打开，保持工程参数、100%比例、原排布与逐层打印，重新切片后选择对应的空闲P2S发送。喷嘴0.4 mm、PLA、纹理PEI，标准100%速度；清洁板面、调平并检查首层。不要将四份合并为一盘。

2/3号底板：平放，层高0.24 mm、首层0.20 mm、4墙、30% gyroid、顶底7层/最小1.6 mm，外墙60/内墙100 mm/s，5 mm外侧防翘边。

4/5号附件：层高0.16 mm、首层0.20 mm、4墙、30% gyroid、顶底10层/最小1.6 mm，外墙40/内墙80 mm/s，3 mm外侧防翘边。原卡座、压框、拨片、簧片、托片尺寸和摆放均保留，同一模块夹具保持在同一盘；只新增放入3块底板连接片。层高改善层向细节，不保证孔径公差，不要整体缩放。

所有新任务自动支撑及擦料塔关闭，防翘边间隙0，保留喷嘴缠料检测关闭；相机炒面检测可开。Generic PLA喷嘴220℃、纹理PEI 60℃，实际板型/耗材需一致。正在打印的昨天第二盘不改参数。

底板保持原280×220外形，两片平放打印后拼接；上平台正在以整片打印。新增12颗M3×16低圆头螺钉、24片外径≤6 mm且厚0.5 mm垫圈、12颗高4 mm M3防松螺母；原夹具五金另计。装配见[底板拼接说明](../flat-split-20261101/README.md#底板如何拼接)和同名手册66.1、66.2。

4号机夹具组：M02、M03、M05、M07、M08，另有托片和2块连接片。5号机：M01、M04、M06、M09、电池托架及双锁片、降压托架、1块连接片。详细对象清单见checks/packing.json。按原模块安装图识别，先去防翘边，再分离套排小件。

正在打印的3件＋新增48件正好覆盖整套51件，无重复或遗漏。四项实际切片均返回0且无警告，首层对象1/1/23/23件与防翘边均在床内；原生3MF与受测模型一致，不含G-code。尚未实物打印、承重或寿命验证。
'''
(OUT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
source=REPO/'docs/manual'/NAME
if not (WORK/'before.docx').exists():shutil.copy2(source,WORK/'before.docx')
assert sha(source)==sha(WORK/'before.docx')
doc=Document(WORK/'before.docx');old=Document(WORK/'before.docx')
start=next(p._p for p in doc.paragraphs if p.text.startswith('66.8'))
body=doc._element.body;children=list(body);index=children.index(start)
for child in children[index:]:
 if child.tag!=qn('w:sectPr'):body.remove(child)
assert len(doc.tables)==77
h=doc.add_paragraph('66.8  昨天第二盘运行时的四台补打分工',style='Heading 2')
h.paragraph_format.page_break_before=True;h.paragraph_format.space_before=Pt(0);h.paragraph_format.space_after=Pt(10)
for r in h.runs:r.font.color.rgb=RGBColor(0,0,0)
def para(text,size=10.5):
 p=doc.add_paragraph(text);p.paragraph_format.space_after=Pt(7);p.paragraph_format.line_spacing=1.15
 for r in p.runs:r.font.size=Pt(size)
 return p
para('1号机正在打印昨天的P2S_MOUNTED_PLATE_2.3mf，即完整上平台、舵机支架与喇叭圈，共3件。继续原任务；另外四台只打印下表48件。此前按“附件盘在打印”安排的四台主体方案不适用于本次。')
t=doc.add_table(rows=1,cols=5);t.autofit=False;widths=[1.2,5.8,1,4,2.5]
for c,w in zip(t.columns,widths):c.width=Cm(w)
for cell,value in zip(t.rows[0].cells,['机器','内容','件数','预计时间','PLA']):cell.text=value
for values in rows:
 for cell,value in zip(t.add_row().cells,values):cell.text=value
borders=OxmlElement('w:tblBorders')
for side in ['top','left','bottom','right','insideH','insideV']:
 b=OxmlElement('w:'+side)
 for k,v in [('val','single'),('sz','4'),('color','D9D9D9')]:b.set(qn('w:'+k),v)
 borders.append(b)
t._tbl.tblPr.append(borders);t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
for ri,row in enumerate(t.rows):
 row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
 for ci,c in enumerate(row.cells):
  c.width=Cm(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
  margins=OxmlElement('w:tcMar')
  for side in ['top','left','bottom','right']:
   e=OxmlElement('w:'+side);e.set(qn('w:w'),'80');e.set(qn('w:type'),'dxa');margins.append(e)
  c._tc.get_or_add_tcPr().append(margins)
  if ri==0:
   e=OxmlElement('w:shd');e.set(qn('w:fill'),'E7EFF3');c._tc.get_or_add_tcPr().append(e)
  for p in c.paragraphs:
   p.alignment=WD_ALIGN_PARAGRAPH.LEFT if ci==1 else WD_ALIGN_PARAGRAPH.CENTER
   p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(2)
   for r in p.runs:r.font.size=Pt(9.5);r.bold=ri==0
para(f"四台同时启动，新增任务约{duration(data['parallel_elapsed_seconds_if_started_together'])}完成，PLA共{data['total_filament_g']:.1f} g；整套还需等1号机剩余任务完成。2至5号只是分工标签，发送时选对应空闲设备。")
para('文件位于parallel-after-old-plate2-20261101/projects/：')
for p in data['plates']:
 q=para(Path(p['file']).name,9);q.paragraph_format.space_after=Pt(3)
para('每份各打印一次。作为项目打开，保留参数、100%比例、原排布和逐层打印，重新切片后发送。P2S 0.4 mm、PLA、纹理PEI，标准100%速度；每台调平并检查首层。')
para('2/3号底板平放，0.24 mm层高、顶底7层、5 mm防翘边；4/5号附件0.16 mm层高、顶底10层、3 mm防翘边。均为首层0.20 mm、4墙、30% gyroid，自动支撑与擦料塔关闭。原夹具尺寸不改，同一模块夹具在同一盘。')
para('底板仍是原280×220尺寸的两片拼接，按66.1、66.2使用三块连接片及新增12套M3×16螺钉固定；上平台在1号机整片打印。正在打印3件＋本版48件合计51件，无重复或遗漏。')
para('不要再打印原43件附件合盘、旧主体三盘或此前“附件盘在打印”的四台文件。四份新工程已切片及检查首层，尚未实物打印、承重或寿命验证。')
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
tables=lambda d:[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
assert steps(doc)==steps(old) and len(steps(doc))==330
assert tables(doc)[:77]==tables(old)[:77]
doc.save(WORK/NAME)
(WORK/'authoring_checks.json').write_text(json.dumps({'original_steps_preserved':330,'original_tables_preserved':77,'corrected_table':'66.8 current running job corrected by user','baseline_sha256':sha(WORK/'before.docx')},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','manual':str(WORK/NAME)},ensure_ascii=False))
