"""Append print release instructions and reviewed actual slice illustrations."""
from pathlib import Path
import hashlib,shutil,re,json
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamps-fine-20261103';W=R.parent/'.p2s-wall-clamps-fine-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert src.read_bytes()==(R.parent/N).read_bytes()
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx')
before=Document(W/'before.docx');d=Document(W/'before.docx');assert not any(p.text.startswith('66.15') for p in d.paragraphs)
def para(t,size=10):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(4);p.paragraph_format.line_spacing=1.1
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def pic(name,cap,width):
    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/name),width=Cm(width));para(cap,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
p=d.add_paragraph('66.15 筒壁压脚高精度打印与试装',style='Heading 2')
for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
para('本节为66.14节预览之后的可打印版，使用wall-clamps-fine-20261103/P2S_WALL_CLAMPS_AND_PADS_FINE_012.3mf。一盘含四只压脚和四只小压垫，不含筒壁、平台、原托片或金属五金。固定孔和施压点沿用图解82，P02不钻孔、筒壁不垫高。')
pic('01_print_layout.png','图解83  压脚侧放、小压垫平放的保存朝向；打开3MF时选择作为工程加载，保持100%比例。',16.5)
para('预设P2S、0.4mm喷嘴、Generic PLA、纹理PEI板、0.12mm层高和0.20mm首层；6道墙、60%螺旋体填充、顶底各12层、外壁35mm/s、外墙加速度700mm/s²。自动树状支撑仅从热床生成，接触Z间隙0.12mm、外裙边5mm。已生成并检查实际支撑，无需重新自动朝向。')
para('三只长压脚增加45°过渡斜撑，长外缘R0.6；短压脚下外缘R0.4。保留底装M3螺母窝和2.4mm上挡肩。网格线性偏差设置0.01mm，0.12mm为层高，均不表示实物尺寸公差保证。需要使用匹配实际耗材的配置，不能把PLA配置直接用于其他材料。')
para('切片预计3小时20分钟、30.5g，含模型与支撑等切片统计。已检查8件首层、168层共97430段挤出运动以及STEP重读、孔腔、网格和原件干涉；3MF保存几何与测试切片一致，不附带可直接执行的G-code，未向打印机发送任务。实际耗时、用料和装配精度以机器结果为准。',9.5)
para('打印后冷却取件，先清除裙边及支撑，尤其检查圆孔、六角螺母窝和贴平台的面；不要削薄挡肩。先试装普通M3螺母与M3螺丝，螺母应能完全贴到上挡肩，再按下一页顺序安装。实物有翘曲、裂纹或孔腔明显过紧时先停止装配，不强压。',9.5)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21);s.left_margin=Cm(1.5);s.right_margin=Cm(1.5);s.top_margin=Cm(1.5);s.bottom_margin=Cm(1.5)
pic('04_actual_support_review.png','图解84  实际全层切片预览，橙色为支撑；并非打印完成照片。',20.5)
para('试装顺序：先将四颗普通M3螺母分别从压脚底面放入；放好原筒壁，将四只小压垫平放在四个底脚孔上方；装压脚，先松装固定端，再逐只轻调M3×8至小压垫贴紧底脚。螺丝头必须悬空，不能拧至贴住压脚。',9.5)
para('固定端拟用三颗M3×16接原立柱，一颗M3×20共用P04托片孔，配原垫片与锁母；装入前核对原立柱盲孔和实际螺丝头，不能靠硬拧消除间隙。打印件未做实物承载或长期抗蠕变验证；完成试装后再逐步加载，观察松动、发白、裂纹或永久变形。',9.5)
steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N);print(str(W/N))
