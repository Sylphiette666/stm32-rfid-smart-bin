"""Add the checked tracker mount to the same-name illustrated manual."""
from pathlib import Path
import hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'tracker-mount-20261103';W=R.parent/'.p2s-tracker-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
assert src.read_bytes()==(R.parent/N).read_bytes()
shutil.copy2(src,W/'before.docx')
before=Document(src);d=Document(src)
assert not any(p.text.startswith('66.18') for p in d.paragraphs)
def para(t,size=10):
 p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.1
 for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
 return p
def pic(name,caption):
 p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.add_run().add_picture(str(O/'preview'/name),width=Cm(16.2));para(caption,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
d.add_paragraph('66.18 三路红外循迹模块轻量转接架',style='Heading 2')
para('适用于已打印的P01分体底板及轻量电机转接板。三路循迹模块按商品尺寸图67×27mm、两孔中心距59.5mm、孔径Φ3mm设计；实物孔距与探头凸出量仍须首件复核。模块长边沿左右，三个探头朝地，中央探头位于底板Y=110mm中心线。')
pic('01_tracker_layout.png','图解89  底板下方安装位置。A/B复用现有拼接孔；C/D为循迹板孔。橙色为已打印电机转接板，粉色为万向轮设计保留区。')
para('孔位表（底板车尾左下角为原点，X向车头，Y向舵机侧，单位mm）：A=(150,88)、B=(150,116)为原拼接孔；C=(185,80.25)、D=(185,139.75)为模块孔，C/D=59.5mm。模块名义外形X=171.5～198.5、Y=76.5～143.5；最前沿距万向轮设计保留区起点X=214为15.5mm。实际轮胎、万向轮全转动范围和线束仍要试装留至少3mm净隙。')
d.add_page_break()
pic('02_tracker_stack.png','图解90  原底板、拼接片、新支架、垫柱及循迹板叠层示意。垫柱长度需按实测离地空间选择。')
para('断电后只卸A/B两颗原M3×16拼接螺钉，保留拼接片与其余螺钉。用两颗M3×20低圆头螺钉由上向下穿过原孔、底板、拼接片和新支架；上下面各一片OD≤6mm、厚约0.5mm平垫，下面加M3防松螺母，均匀轻紧。不能让拼接片悬空或压裂PLA。')
para('在C/D孔用同一长度的两只垫柱。螺钉从模块探头面经Φ3孔、垫片、垫柱和支架穿出，上面用垫片及M3防松螺母。14mm垫柱配M3×25，18mm配M3×30，22mm配M3×35；螺钉头和垫片不能遮挡探头或压住焊点。先用14mm试装，轮子落地后测探头最低点离地距离，再按实测工作距离选择。静态和轻压车体时均不能擦地。')
para('手转两侧轮胎与前万向轮一整圈，检查模块、支架、螺钉和后引线都不碰轮胎或地面。线束向后上方固定。打印工程tracker-mount-20261103/P2S_TRACKER_LIGHT_FINE_012.3mf含一块镂空支架和14/18/22mm垫柱各两只；P2S、0.4mm喷嘴、Generic PLA、0.12mm层高、4墙、30%填充、4mm裙边、无支撑，切片约1小时09分、9.6g。实际打印、离地、振动和循迹功能尚未验收。')
steps=lambda x:[p.text for p in x.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
out=W/N;d.save(out);print(out)
