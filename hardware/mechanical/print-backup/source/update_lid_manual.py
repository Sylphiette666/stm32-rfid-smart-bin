"""Document replacement retainers on the previously printed seats, preserving 330 steps."""
from pathlib import Path
import hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'lid-fine-20261103';W=R.parent/'.p2s-lid-fine-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert src.read_bytes()==(R.parent/N).read_bytes()
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx')
before=Document(W/'before.docx');d=Document(W/'before.docx');assert not any(p.text.startswith('66.17') for p in d.paragraphs)
def para(t,size=10):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.1
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def pic(name,cap):
    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/name),width=Cm(16.5));para(cap,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)

d.add_paragraph('66.17 轻量桶盖与随盖附件',style='Heading 2')
para('本节为适配已打印筒壁的桶盖试装版，保留两只20×20mm金属合页和M2双球头连杆。整盖打印工程P2S_LID_FINE_012.3mf共6件；先用P2S_HINGE_TRIAL_FINE_012.3mf的局部盖片和一只合页连接座确认实物接口。原合页轴心到页片的偏移尚未实测，小样通过后才打印整盖。')
pic('01_lid_closed_open.png','图解87  名义模型闭合与打开70°；不代表真实合页及线束已完成运动验收。')
para('闭合盖面166.5×154mm，含前方提盖边外包174.5×154mm。封闭面0.56mm、底面加强筋，最大局部厚度2.96mm。PLA按1.24g/cm³实心体积估算盖板21.7g、移动打印件26.3g；加上金属合页活动部分、螺丝、垫片和连杆后，必须实称，目标40g以内、不得超过原方案45g限制。尚未验证刚度、冲击及疲劳。')
para('P2S 0.4mm喷嘴、Generic PLA、0.12mm层高、首层0.20mm、4墙、20%填充、5mm裙边，无支撑。整盖约2小时41分钟、26.9g；小样约21分钟、1.8g。作为工程打开，100%比例，保持保存的朝向。网格公差0.01mm不等于实物打印精度保证。')
para('后壁现有合页孔继续用：P02坐标下Y为57、69、121、133mm，高度Z178mm。名义轴为X46.5、Z185mm。合页连接座有4.5×2.3mm调节槽，底部沉头槽容纳头径不超过4mm的M2沉头螺丝；先从底部装入螺丝，再把连接座固定到盖板，螺丝头不能凸出底面。普通圆头不能直接替代。')
d.add_page_break()
pic('02_lid_parts.png','图解88  盖板底面与四类附件；合页连接座需要两只。')
para('试装顺序：先用一只原合页接到后壁原孔，再用M2沉头螺丝连接L02，最后装T01局部盖片。手动检查闭合盖面与壁顶关系、轴筒是否擦碰、连接座是否平贴；若不符，记录偏移后修改连接座厚度，不能靠拧弯盖片调整。小样只验接口，不作整盖承载验证。')
para('连接座与盖板每只用两颗M2.5螺丝；连杆臂和开关支脚各用两颗M2.5，触片再用两颗M2.5。以8～12mm长度配普通螺母和平垫试配，确保露牙且不碰壁；M2球头螺钉长度按原球头实际叠层。沉头M2另备4颗，参考长度8mm，实际核对。所有打印孔按通孔配金属螺母使用。')
para('L03连杆臂在舵机侧，名义有效半径20mm；原SG90舵盘保留。名义合页轴到舵机轴距离改为41.5mm，双曲柄20mm、连杆孔心距50mm，已经不是原50mm轴距平行四边形。闭盖到开盖70°，计算的舵机曲柄几何角约56°到115°，这不是可直接写入固件的舵机角度或PWM。必须先拆杆校准零位，再手动联杆确认行程，之后重新设置开合限位；本次没有修改固件。')
para('L04支脚的横槽调前后位置，L05触片的竖槽调触发高度。先把触片调高，缓慢闭盖，再逐渐下调到开关可靠动作；闭盖重量由原两处2mm EVA缓冲垫承受。保留加强筋上的平面接触区。实际开关拨杆外形未建模，不强压开关。')
para('名义0～70°每2°位置检查通过；核对对象包括旧筒壁、固定传感器支架、舵机架及名义合页包络。实际金属轴偏移、螺钉螺母、球头和线束仍需试装。整盖166层、小样29层全部挤出路径在打印范围内，原生3MF网格回读一致。此版可用于小样验证，实物接口通过前不称为最终装配验收。')
steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N);print(W/N)
