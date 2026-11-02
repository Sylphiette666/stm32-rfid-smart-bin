"""Append reviewed wall instructions; preserve original steps and existing content."""
from pathlib import Path
import shutil,re,hashlib,json
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.section import WD_SECTION_START,WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-panels-20261102';W=R.parent/'.p2s-wall-panels-20261102/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
assert src.read_bytes()==(R.parent/N).read_bytes(),'Published copies diverged'
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert src.read_bytes()==(W/'before.docx').read_bytes(),'User edits detected'
d=Document(W/'before.docx');before=Document(W/'before.docx')
def p(t,size=10):
 q=d.add_paragraph(t);q.paragraph_format.space_after=Pt(5)
 for r in q.runs:r.font.size=Pt(size)
 return q
def heading(t):
 q=d.add_paragraph(t,style='Heading 2');q.paragraph_format.page_break_before=True
 return q
heading('66.11  四块平放筒壁与元件安装')
p('本节对应wall-panels-20261102版。四壁各为一体，PLA平放打印，小附件分配到四盘；保持正常质量，不使用电机座的快速试配参数。模型与切片检查通过，实物装配和传感器功能仍待验证。')
p('四台P2S可同时运行四个项目：01前壁和操作面板约7小时20分、192.4g；02后壁及附件约4小时48分、126.6g；03左壁及附件约4小时9分、107.2g；04右壁及附件约2小时54分、85.8g。最长一盘约7小时20分，另计设备准备和冷却。')
p('打开对应3MF项目并保持100%比例及现有摆盘，选择P2S 0.4mm、实际PLA耗材和纹理PEI板，再切片发送。前盘0.20mm、其余0.24mm，首层0.20mm，3墙、15%螺旋体填充、上下4层。需要支撑的附件已采用自动树状支撑；参数和官方GitHub来源记录见随件README及source/github_support_source.json。')
q=d.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.add_run().add_picture(str(O/'preview/installation.png'),width=Cm(15.5))
p('图解65  四壁与元件安装座；图中省略电子件、螺钉及活动盖。',9)
heading('66.11.1  安装顺序和首次试配')
for t in [
'冷却取件、去除支撑后，先试装小附件。前操作面板集成OLED、编码器、两个按钮、RC522和急停。OLED按孔和下缘承托固定；编码器用原套筒螺母；按钮用可调托架、隔柱和压框；RC522用边缘托轨和压条。只压PCB空白边缘，不能压玻璃、元件或排针。',
'用8个外侧角码连接四壁，内侧平面朝垃圾腔，外侧筋朝外。桶体名义外形160×150×180mm，主面厚1.6mm，边缘及螺孔局部加强。现有P02上平台连续平整面朝上作裸桶底，不套袋、不加内胆；数字检查确认桶内底面连续，但接缝和FDM表面不防水。',
'整体放到上平台试摆，确认与立柱、电机和舵机立架相容后才划线开孔。四底脚候选孔在P02原模型局部坐标(90,13)、(170,13)、(90,177)、(170,177)mm，通孔Ø3.4mm；四处已核实有5mm完整材料。平台坐标不同于后附壁板u/v坐标，本次未直接改孔或重印上平台。',
'前操作腔向外深60mm，约超出上平台前缘29mm、底板前缘9mm。先试装急停原螺母、触点块及接线，再盖操作面板；不能挤压端子。按钮用长孔和1/2mm垫片调整高度；编码器前出排针有独立罩。KCD1总开关在左壁下部外置盒，19.4×12.4mm可换孔片需试卡扣。',
'前壁上部红外托架放31×20mm模块，探头越过板边10mm朝人，排针侧开放。左右对射光轴在桶底上150mm，先用长孔对准，再紧固压条；不用歧义的模块安装孔。左壁外侧分别装DHT11裸探头通风罩和光敏夹座，保持探头、感光区和插线口开放。',
'超声横梁底面距桶底162mm，探头朝下，以板边压条固定，不能把M2螺丝硬塞进Ø1.5mm板孔。导线走中央缺口，横梁可拆。前壁内侧微动开关用M2螺丝装到9.5mm孔距可调片，触片装原活动盖；两侧止挡加2mm软垫承受盖重，开关只负责信号。',
'原活动盖、合页和舵机沿用；先断电手动检查完整开合行程，再做按键回弹、RFID读卡、红外开盖、对射遮挡和超声测距等功能试验。模型检查未覆盖实物电子元件、全部五金和舵机连杆的运动包络。']:
 p(t)
heading('66.11.2  五金和孔位读图')
p('四盘包含64个打印实例、33种零件。紧固件长度按模型叠层估算，最终按实际螺母、垫圈及PCB高度选用；螺钉末端不能顶到电路。PLA孔采用穿螺栓加螺母，不假定已有螺纹。完整文件与按零件分类的参数位于hardware/mechanical/print-backup/wall-panels-20261102。')
for t in [
'M3×10约20颗：角码16、超声横梁两端2、盖触片2。M3×12约16颗：平台脚4、横梁托耳4、红外架2、止挡4、微动片2。',
'M3×16共4颗用于红外压条；M3×20约14颗用于DHT罩2、光敏压条4、线夹8；M3×25共4颗用于两端对射座。',
'总开关盒约用4颗M3×45；前操作腔四角用4颗M3×70贯穿。长螺栓按实物堆叠核对，不靠拧紧来拉弯面板。',
'M2.5×8/10/12/16/20/35分别约8/2/6/4/4/4颗，对应合页/OLED/LED与超声压条/RFID/按钮/排针罩。微动开关另需2颗M2，长度取决于实物厚度。配对应螺母、垫圈、PCB绝缘垫和两块2mm软止挡垫。',
'图解66—70按模型坐标标孔，不按图片比例取尺寸。壁板从外侧看，操作面板从背面看，u向右、v向上，原点在各零件左下角，单位mm；孔号对应interface_positions.csv。长孔表中的尺寸为槽宽×总长，图中矩形仅表示范围，实际两端为半圆。',
'数字核查包括57个打印件装配实例的实体碰撞、85处壁板/面板孔轴贯通、四盘首层对象数及圆弧路径边界。均通过，但并非实物承重、耐久或整机运动验证。前避障、循迹和碰撞横杠仍在底盘低位；其余底板模块维持原安装位置。']:
 p(t)
# Engineering sheets need a landscape page to retain readable table type.
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21)
s.left_margin=Cm(1.5);s.right_margin=Cm(1.5);s.top_margin=Cm(1.5);s.bottom_margin=Cm(1.5)
for i,n in enumerate(['W01_FRONT','W02_REAR','W03_LEFT','W04_RIGHT','PANEL_COVER']):
 q=d.add_paragraph();q.paragraph_format.page_break_before=(i>0);q.paragraph_format.space_after=Pt(0)
 q.paragraph_format.line_spacing=1.0;q.paragraph_format.keep_with_next=True
 q.add_run().add_picture(str(O/'preview'/f'coordinates_{n}.png'),width=Cm(24.0))
 cap=p(f'图解{66+i}  {n}安装孔坐标与窗口；壁板脚孔另见图下注记。',9)
 cap.paragraph_format.line_spacing=1.0;cap.paragraph_format.space_before=Pt(0);cap.paragraph_format.space_after=Pt(0)
steps=lambda a:[p.text for p in a.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N)
print(json.dumps({'staged':str(W/N),'baseline_sha256':hashlib.sha256((W/'before.docx').read_bytes()).hexdigest()},ensure_ascii=False))
