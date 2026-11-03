"""Append B1 instructions to the current manual, with a recoverable baseline."""
from pathlib import Path
import json,hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
REPO=Path(__file__).resolve().parents[3]
PCB=REPO/'hardware/current-low-cost/pcb-b'
STAGE=REPO.parent/'codex_readback/pcb_b_manual_release'
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
SRC=REPO/'docs/manual'/NAME
STAGE.mkdir(parents=True,exist_ok=True)
baseline=STAGE/'before.docx'
if not baseline.exists():shutil.copy2(SRC,baseline)
source_hash=hashlib.sha256(baseline.read_bytes()).hexdigest()
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==source_hash,'Current manual changed; merge first'
checks=json.loads((PCB/'checks/pcb-drc.json').read_text(encoding='utf-8'))
assert all(not checks[k] for k in ['violations','unconnected_items','schematic_parity'])
d=Document(baseline)
steps=[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert len(steps)==330
old_tables=[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
text_updates=[];table_updates=[]
for p in d.paragraphs[:120]:
 old=p.text;new=old
 if old.startswith('装配版本'):new='装配版本 2026 年 11 月 3 日 PCB B1'
 elif '当前按' in old and 'SmartBin_A A1' in old:new='保留原版330个步骤和既有图解。当前采用SmartBin_B B1模块线束PCB，施工先读第67章及随包190端点接线表；第63章A1资料保留参考。'
 elif old.startswith('当前电气施工先读第63章'):new='当前B1电气施工先读第67章和随包接线表，再按原330步骤逐项调试。第63章A1和第61章洞洞板资料保留归档；B1的制造文件、接口和供电选择以第67章为准。模块仍按实物信号名称逐线连接。'
 elif old.startswith('PCB A1施工顺序'):new='PCB B1施工顺序：先看第67章确认版号、贴片器件和线束，再回到步骤091—194逐模块检查，最后上软件及整机功能验收。旧版接口变化以第67章为准。'
 if new!=old:p.text=new;text_updates.append({'before':old,'after':new})
for ti,t in enumerate(d.tables[:2]):
 for ri,row in enumerate(t.rows):
  for ci,c in enumerate(row.cells):
   new=c.text.replace('PCB A1','PCB B1').replace('SmartBin_A A1','SmartBin_B B1')
   if new!=c.text:
    table_updates.append({'table':ti,'row':ri,'cell':ci,'before':c.text,'after':new});c.text=new;old_tables[ti][ri][ci]=new
for section in d.sections:
 for footer in [section.footer,section.first_page_footer,section.even_page_footer]:
  # Mutate only text nodes; assigning Run.text would destroy PAGE field codes.
  for node in footer._element.iter(qn('w:t')):
   if node.text:node.text=node.text.replace('2026年10月12日','2026年11月3日').replace('2026 年 10 月 12 日','2026 年 11 月 3 日')
for p in d.paragraphs:
 if p.text=='63  PCB A1手焊装配与模块连接':p.text='63  PCB A1手焊装配与模块连接（旧版参考）'
 if p.text.startswith('本章是当前施工入口。用一块SmartBin_A'):
  old=p.text;p.text=old.replace('本章是当前施工入口。','本章是A1旧版参考；B1施工入口见第67章。');text_updates.append({'before':old,'after':p.text})
def paragraph(text):
 p=d.add_paragraph();p.paragraph_format.space_after=Pt(6);p.paragraph_format.line_spacing=1.1
 r=p.add_run(text);r.font.name='宋体';r.font.size=Pt(10.5);r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体');return p
def heading(text,level=2,new_page=False):
 p=d.add_paragraph(text,f'Heading {level}');p.paragraph_format.page_break_before=new_page;return p
def table(headers,rows,widths):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
 for i,v in enumerate(headers):t.rows[0].cells[i].text=v
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 for row in rows:
  cells=t.add_row().cells
  for cell,text in zip(cells,row):cell.text=str(text)
 for row in t.rows:
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  for i,c in enumerate(row.cells):
   c.width=Cm(widths[i])
   for p in c.paragraphs:
    p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
    for r in p.runs:r.font.size=Pt(10);r.font.name='宋体';r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
 for i,w in enumerate(widths):t.columns[i].width=Cm(w)
 return t
heading('67  PCB B1手焊装配与模块线束',1,True)
paragraph('本章对应新版 SmartBin B1。使用 KiCad 设计，现有模块以排针和杜邦线接入，取消面包板；电池、电机、舵机和语音供电仍走接线端子。安装 B1 时，本章及随包的190端点接线表优先于第63章A1接口说明。原330步骤编号保留。')
d.add_picture(str(PCB/'renders/board-3d.png'),width=Cm(16))
paragraph('图 B1-1  元件面俯视。裸板125×100 mm、双层、厚1.6 mm；右侧新增七路输入缓冲。方焊盘表示1脚。空的可选电阻位按BOM的DNP列保留，不能全部补焊。')
paragraph('四个安装孔为Ø3.2 mm。以元件面左上角为原点，中心坐标为(5,5)、(95,5)、(5,95)、(95,95) mm，孔距90×90 mm。右侧新增25 mm板宽，一体打印底座须按新外形检查邻近模块和线束空间。')
heading('67.1  B1接口变更与电源分区',2,True)
table(['接口','B1接法与用途'],[
 ('J6','1=5V_BUS，2=GND；DFPlayer独立电源线。喇叭只接模块SPK1/SPK2。'),
 ('J31','1=GND，2=DF_RX，3=DF_BUSY_RAW。BUSY通过U8转换到MCP GPA6；DFPlayer TX仍不接。'),
 ('J33 电源','1=3V3_EXT，2=5V_BUS，3=GND。按具体传感器选择一种VCC，不可把1、2脚相连。'),
 ('J33 信号','4=IR0_RAW→GPB0；5=IR1_RAW→GPB1；6=IR2_RAW→GPB2；7=IR3_RAW→GPB3；8=IR4_RAW→PB8；9=IR5_RAW→PA12。'),
 ('J34','三脚都是GND，分别连接MCP的A0/A1/A2，地址0x20。'),
 ('J35 / J36 / J37','分别为CORE 3.3V / EXT 3.3V / 5V辅助口，均1脚为电源、2脚为GND，只接低功耗逻辑。'),
 ('其余接口','逐针沿用原方案；完整表以本次connector-map.csv为准。自定义PCB针序不等于商品模块物理针序，逐根按模块丝印连接。')],[3.5,13.8])
paragraph('U2—U8使用SN74LVC1G17DBVR，SOT-23-5封装；1=NC、2=A、3=GND、4=Y、5=VCC。它们不反相，处理六路红外DO和语音BUSY，RAW输入工作范围限定为共地0—5.25V。不能把这个耐压范围套用到其他未缓冲接口。')
paragraph('U6、U7由3V3_CORE供电，输出分别到PB8、PA12；其余新增缓冲器由3V3_EXT供电，输出到MCP。CORE与EXT共地但不能并联。每路串1kΩ、上拉10kΩ、去耦100nF；无源器件为0805。')
paragraph('J28仍接已焊好的AO3400A转接模块，J23仍可接DHT双向电平转换成品模块；按原供电选择设置JP8。这两块是独立小模块，不用面包板。全部模块保留原有排针。')
heading('67.2  焊接顺序与首次上电',2,True)
d.add_picture(str(PCB/'renders/cam-bottom.png'),width=Cm(16))
paragraph('图 B1-2  实际Gerber生成的焊接面，已按从底部观察显示。对照孔位和方焊盘识别方向，不要再次镜像后照抄。')
paragraph('先焊7颗SOT-23-5和21颗0805，再焊低矮直插件、排针、端子和电容，最后装U1芯片。U1用SN74AHCT125N，不用74HC125。按BOM核对DNP；确认电解电容、晶体管和芯片方向。')
paragraph('断电检查焊桥、极性、两路3.3V隔离和线束。先单独调整降压至5.0V，再按既有步骤分阶段接逻辑和传感器。不同模块断电时，不应继续从外部给信号脚送电。电机、舵机和语音电源不用细杜邦线。')
paragraph('架空车轮验证急停及释放后不自动续跑，再测试舵机和负载。原急停只关闭轮电机驱动，不切断舵机供电；外部3.3V失电时的硬件联锁限制仍保留。')
heading('67.3  检查结果与实物验收边界')
paragraph('最终KiCad检查为ERC 0违规、PCB DRC 0违规、0未连接、0原理图差异；126个位号、372个连接管脚和8个NC逐脚一致。原33段粗电源铜线保留；制造ZIP的钻孔位置与板数据逐一核对。源工程、BOM、190端点接线表和报告随设计包提供。')
paragraph('这些是数字设计检查，尚未实焊、带载、测温或进行EMC验证。双层板局部回流绕行、原C8距离和模块线长仍需整机测试。原手册的电源检查、模块测试和故障记录继续执行。')
assert [p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]==steps
assert [[[c.text for c in row.cells] for row in t.rows] for t in d.tables[:len(old_tables)]]==old_tables
out=STAGE/NAME;d.save(out)
report={'source_sha256':source_hash,'source':str(SRC),'output':str(out),'steps_preserved':330,'old_tables_preserved_except_explicit_changes':len(old_tables),'table_changes':table_updates,'text_changes':text_updates,'added_chapter':67,'images_added':2}
(STAGE/'edit-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
