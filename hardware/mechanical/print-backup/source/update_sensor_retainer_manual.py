"""Document replacement retainers on the previously printed seats, preserving 330 steps."""
from pathlib import Path
import hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.section import WD_SECTION_START,WD_ORIENT
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'sensor-retainers-fix-20261103';W=R.parent/'.p2s-sensor-retainers-fix-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert src.read_bytes()==(R.parent/N).read_bytes()
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert sha(src)==sha(W/'before.docx')
before=Document(W/'before.docx');d=Document(W/'before.docx');assert not any(p.text.startswith('66.16') for p in d.paragraphs)
def para(t,size=10):
    p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5);p.paragraph_format.line_spacing=1.1
    for r in p.runs:r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p
def pic(name,cap):
    p=d.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(O/'preview'/name),width=Cm(16.5));para(cap,9)
s=d.add_section(WD_SECTION_START.NEW_PAGE);s.orientation=WD_ORIENT.PORTRAIT;s.page_width=Cm(21);s.page_height=Cm(29.7);s.left_margin=Cm(2);s.right_margin=Cm(2);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8)
p=d.add_paragraph('66.16 光敏压条与对射压盖的旧底座修复',style='Heading 2')
for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
para('本节针对已打印旧底座：图一两根光敏压条不能对准，图二红外对射外壳向下滑落。保留旧LIGHT_CRADLE、BEAM_SEAT和筒壁，只更换两根L压条及两个IR下托压盖。使用sensor-retainers-fix-20261103/P2S_LIGHT_BARS_IR_CUPS_FIX_FINE_012.3mf，一盘共4件。')
pic('01_light_old_seat_fix.png','图解85  旧光敏底座继续使用；新条带横向槽和内侧接触台阶，示意PCB不含实际元件。')
para('适用旧光敏底座的数字模型外形44×30mm，左右孔距36mm、上下孔距23mm；原对应压条名义孔距也为36mm。此次未重测旧打印实物，不能把失配原因认定为某个已测尺寸。新版条长50mm、厚3mm，双槽10×3.4mm，槽中心仍以36mm为基准，理论孔距覆盖29.4～42.6mm；实际调节还需避让螺母、垫片和元件。')
para('两根L压条完全相同，内侧0.3mm台阶朝向PCB边。下条直接安装，上条在平面内转180°，使两个台阶相向；沿用2mm厚PCB包络，台阶与旧底座支撑面共同限位。先将四颗螺丝都穿过槽并松带螺母，压条对正边缘后交替轻拧，不能压到芯片、光敏电阻或接插件，也不能把PCB拧弯。')
para('光敏位置按M3×20、平垫和普通M3螺母估算；实际叠层及露牙需试装核对。不要把原47mm的前方红外PCB压条放到此处；新件用L标记区分。接触面有残留裙边时先清理，保持原底座、筒壁孔及整体比例。')
para('打印工程沿用P2S 0.4mm／Generic PLA、0.12mm层高、6墙、60%螺旋体、顶底12层，宽平面贴床，无支撑、3mm裙边。预计约41分钟、3.6g。已检查4件首层及94层路径；层高和0.01mm网格设置不是实物公差保证，仍需打印后试装。',9.5)
d.add_page_break()
pic('02_beam_lower_support_fix.png','图解86  新IR压盖在旧对射夹座前方增加两个下托肩，中央线槽开放；灰色为名义外壳包络。')
para('原BEAM_SEAT底部开放，旧直压条只在前方压住外壳，没有防止其向下滑动的托面。这是本次修正的结构遗漏。新IR压盖保留22mm孔距和2.4mm前盖厚度，在两侧增加托肩；托面位于旧座局部Y＝3.7mm，托住10×20×9mm名义外壳下沿，光学窗口不变。')
para('中间8mm线槽向前和下方开放，不需要把已有线束穿过封闭小孔。先断电，一手扶住旧夹座再拆原直压条；放好红外外壳，将底部线束放入槽内，盖上IR新压盖。确认壳体下沿确实落在两个托肩上，线束没有夹在托面或螺丝下面，然后交替轻拧两颗固定螺丝。')
para('两端对射各换一个IR压盖，按四颗M3×25、平垫和普通M3螺母估算；已有符合长度的五金可复用，以实际叠层和露牙确认。安装后先断电轻晃确认外壳不再下滑，再恢复对射遮挡测试。若实际外壳尺寸与上述包络不同，不硬压。')
para('已用旧STEP检查新盖与底座不穿透、螺丝通道和光学窗口保持，并以外壳向下及向外各移0.1mm的几何交叠验证止挡存在；8mm出线通道保持开放。此检查只证明名义模型的限位关系，不代表真实模块、线束及打印公差已验收。原两类旧附件保留作历史文件，本节新打印及重打采用修复3MF。',9.5)
steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N);print(str(W/N))
