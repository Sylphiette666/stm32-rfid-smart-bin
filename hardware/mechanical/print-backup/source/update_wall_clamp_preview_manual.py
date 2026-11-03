"""Append the requested preview, keeping the released mechanical designs and steps intact."""
from pathlib import Path
import hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamp-preview-20261103';W=R.parent/'.p2s-wall-clamp-preview-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert src.read_bytes()==(R.parent/N).read_bytes()
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx')
before=Document(W/'before.docx');d=Document(W/'before.docx');assert not any(p.text.startswith('66.14') for p in d.paragraphs)
def para(t,size=10):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(4);p.paragraph_format.line_spacing=1.1
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def picture(name,caption,width=16.5):
    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/name),width=Cm(width));para(caption,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
p=d.add_paragraph('66.14 筒壁免钻孔压脚转接件方案预览',style='Heading 2')
for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
para('P02上平台没有原筒壁底脚对应孔。本节给出利用现有孔从上方压住底脚的概念方案：筒壁主框仍位于X＝50～210、Y＝20～170，保持160×150mm外廓和180mm高度，筒壁不垫高，P02继续作为桶底。暂不按旧底脚孔位钻孔。')
picture('01_mounting_overview.png','图解79  四只免钻孔压脚的整体位置；原筒壁和舵机竖架只显示下部，实际零件未切矮。')
para('固定端使用三个现有立柱孔和一个舵机托片孔；长压脚贴着P02外边缘设置挡肩，底脚两侧设置小挡块。舵机侧后压脚绕过P04托片边缘并借其限位，保留（10,180）后角孔与原工具通道。各压脚末端通过金属M3螺母、调压螺丝和小压垫向下压住原底脚。')
para('压脚底面装入普通M3螺母，螺母上方留2.4mm实体挡肩承受向上的反力；需在把压脚装到平台前放入螺母。Ø8×1.2mm压垫跨过原底脚孔；原孔不作为穿入P02的螺栓孔。调压螺丝头保持悬空，只允许轻压，不得将螺丝头拧至贴紧压脚。')
para('初步五金为三颗M3×16固定三个立柱端、一颗M3×20共用托片端、四颗M3×8调压螺丝和四颗普通M3螺母；固定端配垫片，托片下方复用锁母。长度依当前模型估算，立柱盲孔深度、实际螺丝头及工具空间仍需在最终打印版前核对，不能因已有M3×16便认定全部螺丝齐备。',9.5)
para('本节是结构预览，未发布打印工程。已检查四个新实体的连通性、封闭网格以及与完整筒壁、P02、P04、P03和模型化五金的几何关系；这不代表实物承载或长期抗蠕变验证。后续仍需确定材料、打印朝向和过渡圆角，再进行试装与逐步加载。',9.5)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21);s.left_margin=Cm(1.5);s.right_margin=Cm(1.5);s.top_margin=Cm(1.5);s.bottom_margin=Cm(1.5)
for i,(name,cap) in enumerate([
    ('02_pressure_clamp_detail.png','图解80  普通压脚C1的固定端、贴边挡肩、底装螺母和小压垫；C2与C3按各自孔位布置。'),
    ('03_servo_side_detail.png','图解81  舵机侧后压脚C4借用P04托片孔并绕过其边缘；保留原P03竖架。'),
    ('04_anchor_plan.png','图解82  现有固定孔与底脚压点坐标；绿圆为借用孔，橙方为施压点，不是P02新钻孔。')]):
    p=d.add_paragraph();p.paragraph_format.page_break_before=(i>0);p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/name),width=Cm(22.1 if i<2 else 23.4))
    p=para(cap,9);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N);print(str(W/N))
