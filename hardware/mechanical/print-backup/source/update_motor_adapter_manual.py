from pathlib import Path
import shutil,re,hashlib
from docx import Document
from docx.shared import Cm,Pt
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-adapter-20261101';W=R.parent/'.p2s-motor-adapter-20261101/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
assert src.read_bytes()==(R.parent/N).read_bytes(),'Published copies diverged'
if not (W/'before.docx').exists():shutil.copy2(src,W/'before.docx')
assert src.read_bytes()==(W/'before.docx').read_bytes()
d=Document(W/'before.docx');before=Document(W/'before.docx')
h=d.add_paragraph('66.10  电机穿槽转接座',style='Heading 2');h.paragraph_format.page_break_before=True
texts=[
'用户已试配确认：B件槽12×2.4 mm、槽中心距21 mm、承托厚3 mm合适；固定片从上向下穿入，宽头实测高5 mm。新版宽头腔6 mm，固定耳总高9 mm，电机贴合面不加文字。',
'打印motor-adapter-20261101/P2S_D06_ADAPTER_PAIR_028.3mf，两种座各1件，预计46分30秒、16.3 g。0.28 mm层高、4墙、40%填充，保持100%尺寸。图中分耳座用于非舵机侧，偏耳座用于舵机侧，偏耳四孔翼朝车头。',
'先装固定片、电机和轮子，再放到底板下断电试摆。检查轮胎全周净隙至少约3 mm、两轴共线、宽头和紧固件不顶住。候选孔位只经数字避让，完整轮组尚未验证，暂不钻底板；试摆后再确认孔位。',
'最终连接拟用8颗M3×20低圆头螺栓、16片OD≤6 mm/厚0.5 mm垫圈、8颗高4 mm锁母，贯穿5 mm底板实心区和固定耳。装好轮组后量Hb，再按实测Hb与万向球高度20 mm决定垫高件。无承重或行驶验收结论。']
for t in texts:
 p=d.add_paragraph(t);p.paragraph_format.space_after=Pt(5)
 for r in p.runs:r.font.size=Pt(10)
d.add_paragraph().add_run().add_picture(str(O/'preview/installation.png'),width=Cm(15.5))
p=d.add_paragraph('图解64  电机转接座实物模型与安装剖面；图示固定片用于说明穿入方向，不代表完整轮组已验证。')
for r in p.runs:r.font.size=Pt(9)
steps=lambda a:[p.text for p in a.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(d)==steps(before) and len(steps(d))==330 and len(d.tables)==len(before.tables)
d.save(W/N)
print(hashlib.sha256((W/'before.docx').read_bytes()).hexdigest())
