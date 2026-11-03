"""Stage a chapter update without overwriting concurrent user edits."""
from pathlib import Path
import json,hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2]
W=R.parent/'codex_readback/integrated_pla_manual_20261104';W.mkdir(exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
src=R/'docs/manual'/NAME;baseline=W/'before.docx'
if not baseline.exists():shutil.copy2(src,baseline)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)==sha(baseline),'Manual changed; merge before replacing'
d=Document(baseline);steps=[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
for q in d.paragraphs[:120]:
 if q.text.startswith('装配版本'):q.text='装配版本 2026 年 11 月 4 日 PCB B1及PLA一体结构'
 if q.text.startswith('保留原版330个步骤和既有图解。当前采用'):
  q.text='保留原版330个步骤和既有图解。当前电气施工先读第67章B1 PCB与190端点接线表，机械施工先读第68章PLA一体结构；旧版资料保留参考。'
table_changes=[]
for ti,t in enumerate(d.tables[:1]):
 for ri,row in enumerate(t.rows):
  if row.cells[0].text=='轻型机械结构':
   c=row.cells[1];old=c.text;new='PLA一体底板及上平台筒壁，操作面板和活动盖可拆，见第68章。'
   c.text=new;table_changes.append({'table':ti,'row':ri,'cell':1,'before':old,'after':new})
for sec in d.sections:
 for footer in [sec.footer,sec.first_page_footer,sec.even_page_footer]:
  for node in footer._element.iter(qn('w:t')):
   if node.text:node.text=node.text.replace('2026年11月3日','2026年11月4日').replace('2026 年 11 月 3 日','2026 年 11 月 4 日')
assert len(steps)==330
oldtables=[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
def p(text):
 q=d.add_paragraph(text);q.paragraph_format.space_after=Pt(6);q.paragraph_format.line_spacing=1.1
 for r in q.runs:
  r.font.name='宋体';r.font.size=Pt(10.5);r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
 return q
def h(text,level=2,page=False):
 q=d.add_paragraph(text,f'Heading {level}');q.paragraph_format.page_break_before=page
 for r in q.runs:r.font.color.rgb=RGBColor(0,0,0)
def pic(name,width=16):d.add_picture(str(O/'preview'/name),width=Cm(width))
def table(head,rows,widths):
 t=d.add_table(rows=1,cols=len(head));t.style='Table Grid';t.autofit=False
 for c,v in zip(t.rows[0].cells,head):c.text=v
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for i,w in enumerate(widths):t.columns[i].width=Cm(w)
 for ri,row in enumerate(t.rows):
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  for i,c in enumerate(row.cells):
   c.width=Cm(widths[i]);pr=c._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');bd.append(e)
   pr.append(bd)
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DCE7EE');pr.append(sh)
   for q in c.paragraphs:
    q.paragraph_format.space_before=Pt(4);q.paragraph_format.space_after=Pt(4)
    for r in q.runs:r.font.name='宋体';r.font.size=Pt(10)
h('68  PLA一体结构与精细打印',1,True)
p('本章对应2026年11月4日的一体结构修订，配合第67章B1 PCB使用。打印设备按用户最新确认：拓竹P2S、0.4 mm喷嘴、纹理PEI板、256×256×256 mm成形空间，材料为PLA；其他聊天中的PETG参数不用于本版。原330步骤和历史图解保留，机械一体化的差异以本章为准。')
pic('UPPER_INTEGRATED_iso.png',15)
p('图68-1  上半主体。240×190 mm上平台、四面筒壁、固定传感器座、操作仓和超声横梁连续成一件。四角连接件与筒壁固定转接脚取消。前操作面板仍用原四颗螺钉拆开；活动桶盖、模块压框、压条和锁片继续作为可拆附件，不封死检修入口。')
p('桶体主体外形160×150×180 mm。在上平台坐标内，后边距50 mm、前边距30 mm、左右边距20 mm；操作仓外凸不计入该距离。上下平台继续用四根60 mm立柱连接，平台相对底板的坐标偏移为X+20、Y+15、Z+65 mm。')
h('68.1  一体底板与模块位置',2,True)
pic('layout_dimensions.png',17)
p('图68-2  底板左下角为原点，X指向车头，Y指向舵机侧，底板底面Z=0。板外形280×220×5 mm。模块固定底座、电机承托、循迹支架和万向轮增高架均直接连接底板；无需旧底板拼接片、模块座脚固定螺钉或16 mm孔位转接厚板。')
table(['位置或接口','本版坐标与尺寸'],[
 ('B1 PCB','外形125×100×1.6 mm；左下角(110,60)，承托面Z=25；孔中心(115,65)、(205,65)、(115,155)、(205,155)，孔距90×90 mm。'),
 ('电机槽基准','左右中心(96,14)、(96,206)；接触面Z=−25，承托厚3；穿槽12×2.4、槽距21、轮侧薄边1.3 mm。'),
 ('万向轮','两孔(240,90)、(240,130)，孔距40 mm；安装面Z=−41。'),
 ('三路循迹','两孔(185,80.25)、(185,139.75)，孔距59.5 mm；安装面Z=−43.4。探头突出8 mm为用户数据，板厚1.6 mm暂按设计值。'),
 ('移位模块','MPU6050中心(253,170)，转90°；蜂鸣器(252,65)；喇叭(256,120)，安装耳沿Y，耳孔(256,96)/(256,144)。其余模块沿原布局。')],[3.1,14.2])
h('68.2  紧固与维修',2,True)
pic('LOWER_H41_B1_bottom.png',15)
p('图68-3  一体底板底面。电机旧固定耳已取消，原配T形金属固定片从上方贯通窗口装入，宽头落在承托腔，保留原配横向电机螺栓。先装轮组，再装电子模块；电机接触面不加文字。')
p('模块翻盖、拨片和簧片沿用原套件；翻盖铰链仍使用M3金属轴，不能把活动部分粘死。拨片轴和簧片锚钉继续贯穿底板。B1改用一体绝缘柱，建议M3×35通螺栓、外径不超过6 mm垫圈与螺母；PCB四孔周围不得压住器件或焊点。')
p('DC-DC的两个真实安装孔保持不变，一体底座取消原底部封闭螺母窝的装配方式，改为从底板下方配M2.5螺母的贯穿紧固，候选M2.5×16，装配时核对突出长度。喇叭安装耳使用原可调螺母托住，M3×30螺柱不穿入PCB占位区。不可依靠拧紧螺母把喇叭耳片拉弯。')
p('万向轮和循迹模块采用贯穿紧固，按实际金属片厚度复核M3×55候选螺钉；螺钉头在底板上方预留沉孔，底部配小垫圈与螺母。循迹探头应低于螺钉末端，避免螺钉先擦地。')
p('H41来自原手册66.19的名义尺寸链：32.5 mm轮半径＋12.5 mm原轴偏移＋16 mm下移=61 mm离地，扣除20 mm万向轮总高得到41 mm。它不是新测出的离地高度。按1.6 mm循迹板厚计算，探头名义离地8 mm；装车后检查三轮同时着地，并通过软件和实测校验循迹工作距离。')
p('光敏压条和红外对射压盖沿用66.16的修复版本，红外压盖必须有底部托肩，不能换回旧直压条。操作面板拆下后再接急停、屏幕及按钮线束；保留22 mm已测插线空间。')
p('MPU6050固定座绕Z旋转90°，原固件显示的roll/pitch方向随安装朝向改变。装好后重新做水平零点校准，并分别向车体前后、左右倾斜验证报警；以后若按车体坐标使用姿态量，需对应调整轴映射。本轮不覆盖正在修改的固件文件。')
h('68.3  打印精度与轻量化',2,True)
table(['项目','设置或检查依据'],[
 ('材料与热床','PLA；Generic PLA P2S基础预设；喷嘴220℃、纹理PEI热床55℃，最大体积速度8 mm³/s。'),
 ('层高与速度','层高0.08 mm，首层0.16 mm；外墙/顶面25、内墙50 mm/s，首层20 mm/s；外墙加速度600 mm/s²。'),
 ('壳与填充','下半件5墙、20%螺旋体；上半件4墙、15%螺旋体；顶底各10层，最小厚度0.8 mm。'),
 ('树形支撑','自动混合树形；枝径3 mm、分支角35°、2道支撑壁；上下Z间隙0.16 mm，XY间隙0.35 mm，上接触3层、下接触2层，接触间距0.35 mm。'),
 ('边界','下半件竖立、盘内转45°；上半件倾斜，分盘打印、100%比例；外侧裙边6 mm。必须以最终项目实际切片后的支撑和挤出路径确认256 mm边界。'),
 ('减重','下板在既有浅腔中心保留2 mm连续面皮，保留原12 mm网格主筋及孔周加厚；筒壁保留1.6 mm面皮。仅深化浅腔去掉约14.7 cm³实体，耗材重量以实际切片为准。')],[3.1,14.2])
p('0.08 mm是本机0.4 mm喷嘴配置的最细支持层高，不代表尺寸误差为±0.08 mm。名义孔槽和100%模型比例保持，未依据实物校准结果擅自补偿孔径、流量或整体缩放。更细层高主要改善斜面台阶；接触支撑的表面仍需清理后试配。')
p('已检查实体闭合、关键孔槽、PCB和活动夹具的静态空间、平台立柱及操作面板。新的整件打印、支撑拆除、车轮完整扫掠、层间承载、疲劳及实际尺寸精度仍需实物验证；不能把数字通过称为已验证的额定承重或绝对最轻结构。首件先空壳试装，再逐步增加电池与负载。')
p('建模检查参考GitHub alexanderkoller/codex-cad；树形参数含义参考OrcaSlicer官方wiki support_settings_tree，并以本机Bambu Studio接受的配置和最终路径为准。当前环境没有FreeCAD，未将CadQuery的STEP回读检查冒称为FreeCAD独立验证。')
h('68.4  打印方向与补充视图',2,True)
q=d.add_paragraph()
for n in ['LOWER_H41_B1_print_orientation.png','UPPER_INTEGRATED_print_orientation.png']:q.add_run().add_picture(str(O/'preview'/n),width=Cm(8.3))
p('图68-4  左：下半主体竖立、盘内转45°；右：上半主体倾斜。灰色面为256×256 mm打印盘。这里只显示模型朝向，不显示树形支撑。不要自动摆正或按比例缩小；以3MF内的100%摆放为准。')
q=d.add_paragraph()
for n in ['LOWER_H41_B1_iso.png','UPPER_INTEGRATED_bottom.png']:q.add_run().add_picture(str(O/'preview'/n),width=Cm(8.3))
p('图68-5  左：下半主体顶侧固定座；右：上半主体底面。图68-2给出模块与孔位坐标，图68-3给出底部承托。模型实际可拆压框、锁片和活动桶盖需沿用旧附件，不能把参考装配中的全部零件当成一个打印件。')
h('68.5  实际切片首层',2,True)
q=d.add_paragraph()
for n in ['LOWER_H41_B1','UPPER_INTEGRATED']:q.add_run().add_picture(str(O/'preview'/f'first_layer_{n}.png'),width=Cm(8.3))
p('图68-6  左为下半件、右为上半件的实际首层路径，坐标范围均为0—256 mm。蓝色为模型及裙边，棕色为支撑。检查覆盖全部层的实际挤出路径，包括树形支撑与裙边，不只检查模型外框。')
pic('first_layer_PANEL_COVER.png',7.5)
p('图68-7  可拆操作面板单独平放，无支撑；四螺钉检修方式保持。')
rows=[]
for n,label in [('LOWER_H41_B1','下半主体'),('UPPER_INTEGRATED','上半主体'),('PANEL_COVER','可拆操作面板')]:
 s=json.loads((O/'checks'/f'{n}_slicing.json').read_text(encoding='utf8'))['result']['sliced_plates'][0]
 sec=round(s['total_predication']);grams=sum(v['total_used_g'] for v in s['filaments'])
 rows.append((label,f'{sec//3600}小时{sec%3600//60}分；PLA含支撑约{grams:.1f} g'))
table(['工程','本机切片估算'],rows,[4,13.3])
p('耗时及重量为当前PLA 0.08 mm工程的切片估算，不是已实打结果。更换材料预设、打印速度或支撑参数后需重新切片。')
assert [q.text for q in d.paragraphs if re.match(r'步骤 \d{3}',q.text)]==steps
assert [[[c.text for c in row.cells] for row in t.rows] for t in d.tables[:len(oldtables)]]==oldtables
out=W/NAME;d.save(out)
(W/'edit-audit.json').write_text(json.dumps({'source_sha256':sha(baseline),'steps_preserved':330,'original_tables_preserved_except_listed_changes':len(oldtables),'table_changes':table_changes,'new_chapter':68,'staged_docx':str(out)},ensure_ascii=False,indent=2),encoding='utf8')
print(out)
