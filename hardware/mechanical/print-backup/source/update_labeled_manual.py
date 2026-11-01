from pathlib import Path
import json,shutil,hashlib,re
from docx import Document
from docx.shared import Cm,Pt
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'labeled-bases-20261101';W=R.parent/'.p2s-labeled-20261101/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
d=json.loads((O/'checks/final_printing.json').read_text(encoding='utf-8'));labels=json.loads((O/'checks/labels.json').read_text(encoding='utf-8'))['labels']
def time(s):
 s=round(s);return f'{s//3600}小时{s%3600//60}分'
text='# 模块底座带一体标牌版\n\n当前1号机继续昨天第二盘，上平台、舵机支架、喇叭圈不重复打印。2/3号机底板形状与上一版相同；4/5号机附件改用本目录带标牌工程，旧附件文件不再使用。\n\n| 机器 | 文件 | 预计时间 | PLA |\n| --- | --- | --- | --- |\n'
for i,p in enumerate(d['plates'],2):text+=f"| {i}号 | [{Path(p['file']).name}]({p['file']}) | {time(p['estimated_seconds'])} | {p['filament_g']:.1f} g |\n"
text+='\n本轮11个待打印底座添加名称小板，上盖、拨片、簧片和托片不加标牌；9个模块座、电池托架、5V降压托架已更换。标牌厚1.8 mm、字高4 mm、凸字高0.64 mm，圆角边缘，与底座一体打印。静态装配模型及安装螺钉通道已避让，原安装孔保留。\n\n名称对应：STM32核心板、MCP23017扩展、FLASH存储、TB6612电机驱动、3.3V稳压、DFPLAYER播放器、HC-05蓝牙、MPU6050姿态模块、BUZZER蜂鸣器、BAT 2S串联电池、5V BUCK降压。\n\n喇叭底座已在运行中的昨天第二盘内；另提供可选带SPEAKER标牌的parts/P07_SPEAKER_cradle.stl和对应STEP，不放入当前任务，不需要为它停止打印或重复打印。A1主PCB直接装在底板上，没有独立附件底座，本次不改底板。\n\n4/5号机两盘各23件，重新分开排布，保留0.16 mm层高、4墙、30% gyroid、3 mm防翘边、外墙40/内墙80 mm/s；自动支撑关闭。作为项目打开，保持100%比例、原排布和逐层打印，重新切片，标准100%速度。2/3号机仍为0.24 mm层高与5 mm防翘边。\n\n四份工程实际切片无警告；首层1/1/23/23件均在床内。与正在打印的3件合计51件，无重复。改变底座只增加标牌，未改变上盖和活动零件几何；连接片和底板拼接按手册66.1、66.2。尚未实物打印、接线或寿命试验；装配时核实实际导线与标牌的距离。\n\n![底座标牌总览](preview/labels_overview.png)\n'
(O/'README.md').write_text(text,encoding='utf-8')
source=R/'docs/manual'/N
if not (W/'before.docx').exists():shutil.copy2(source,W/'before.docx')
assert source.read_bytes() in [(W/'before.docx').read_bytes(),(W/N).read_bytes()] if (W/N).exists() else source.read_bytes()==(W/'before.docx').read_bytes()
a=Document(W/'before.docx');old=Document(W/'before.docx')
h=a.add_paragraph('66.9  模块底座名称标牌',style='Heading 2');h.paragraph_format.page_break_before=True
for t in ['本轮11个待打印底座加一体名称标牌；上盖、拨片、簧片和托片不加。原孔位和夹持结构不变。标牌厚1.8 mm，凸字高0.64 mm，字高4 mm。', '附件改用labeled-bases-20261101/projects/中的P2S_PRINTER_04_LABELED_CLAMPS_A.3mf与P2S_PRINTER_05_LABELED_CLAMPS_B.3mf；各23件，0.16 mm层高，预计5小时17分和5小时34分。2/3号底板仍按上一版打印。', '昨天第二盘继续；喇叭带标牌版仅提供可选STL/STEP，不重复安排。BUZZER为蜂鸣器，BAT 2S为串联电池，5V BUCK为5V降压。其余标牌使用模块型号。']:
 p=a.add_paragraph(t);p.paragraph_format.space_after=Pt(6)
 for r in p.runs:r.font.size=Pt(10)
p=a.add_paragraph();p.add_run().add_picture(str(O/'preview/labels_overview.png'),width=Cm(14.5))
p=a.add_paragraph('图解63  模块底座名称标牌；SPEAKER为可选喇叭底座。静态避让与切片已检查，实际接线和装配仍需核实。')
for r in p.runs:r.font.size=Pt(9)
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(a)==steps(old) and len(steps(a))==330
assert len(a.tables)==len(old.tables)==78
a.save(W/N)
