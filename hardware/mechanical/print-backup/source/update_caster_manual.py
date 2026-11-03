"""Append D05 caster riser instructions to the same-name illustrated manual."""
from pathlib import Path
import shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'caster-riser-20261103';W=R.parent/'.p2s-caster-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
assert src.read_bytes()==(R.parent/N).read_bytes();shutil.copy2(src,W/'before.docx')
before=Document(src);d=Document(src);assert not any(p.text.startswith('66.19') for p in d.paragraphs)
def para(t,size=10):
 p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.1
 for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
 return p
def pic(name,caption):
 p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.add_run().add_picture(str(O/'preview'/name),width=Cm(16.2));para(caption,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
d.add_paragraph('66.19 D05万向轮轻量增高支架',style='Heading 2')
para('按用户在“制定智能垃圾桶搭建步骤1”中的实测，D05万向轮总安装高度为20mm、两个安装孔中心距40mm。已打印的电机转接板让驱动轮下移16mm；旧方案Hb=45mm仅为旧轮组参考，当前底板实际离地高度Hb尚未实测。因此先选支架位置，再用装好两侧轮子后的Hb决定增高量H=Hb−20mm。')
pic('01_caster_layout.png','图解91  复用A1主PCB前侧已有孔A/B，C/D为万向轮40mm孔距；支架位于底板前部实心加强区。')
para('底板坐标：车尾左下角为原点，X向车头、Y向舵机侧。A=(205,65)、B=(205,155)为原A1固定孔；C=(240,90)、D=(240,130)为万向轮连接孔，中心(240,110)。数字检查显示支架与已打印两块电机转接板及循迹模块支架无相交。万向轮安装片真实外形、孔径及转动包络尚未测量，需实装确认。')
d.add_page_break()
pic('02_caster_stack.png','图解92  4mm双支臂、孔位7mm承力台、可换立柱和万向轮安装片的叠层；示例为H40。')
para('先装两侧电机和65mm轮子，让轮胎承重，万向轮暂不装。测平桌面至底板下表面的垂直距离Hb，左右各测一次。Hb约55/60/65mm时，分别使用H35/H40/H45打印工程；若偏离这些高度，先按实测调整模型，不能硬装。三份工程均含支架一块和等长立柱两只，切片估算16.6/18.1/19.7g。')
para('断电并移开A1线束。先将C/D两颗M3低圆头螺钉从支架上面沉孔穿入，头下配外径不超过6mm、厚约0.5mm的平垫；螺钉头和平垫应完全低于贴底板的平面。再套两只同高立柱，接万向轮安装片，下面加平垫及M3防松螺母。按安装片约2mm参考，H35/H40/H45分别先试M3×45/×50/×55；实物片厚、孔径和露牙需核对，螺钉不能碰滚轮。')
para('把组装好的支架贴底板下表面，A/B与A1主PCB的10mm绝缘柱共用原孔。按PCB 1.6mm、绝缘柱10mm、底板5mm、支架4mm的参考叠层，先试两颗M3×30；不得碰PCB背面焊点。紧固后放在平桌上，确认驱动轮和万向轮同时接地且底板大致水平，手转各轮一整圈，并查循迹模块和线束净隙至少3mm。先空载手推，再逐步加载；实物承重、疲劳和行驶尚未验收。')
para('打印使用P2S 0.4mm喷嘴、PLA、0.16mm层高、6墙、45% gyroid、5mm brim，无支撑。只打开与实测Hb对应的一份P2S_CASTER_RISER_Hxx_LIGHT_016.3mf，保持100%比例和保存的朝向。')
steps=lambda x:[p.text for p in x.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(before)==steps(d) and len(steps(d))==330 and len(before.tables)==len(d.tables)
out=W/N;d.save(out);print(out)
