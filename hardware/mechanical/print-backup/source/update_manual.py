from pathlib import Path
from collections import Counter
import hashlib,shutil,re,json,zipfile
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
REPO=Path(__file__).resolve().parents[4];ROOT=REPO/'hardware/mechanical/print-backup'
WORK=REPO.parent/'.p2s-light-20261030/manual';WORK.mkdir(parents=True,exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
source=REPO/'docs/manual'/NAME;before=WORK/'before.docx'
if not before.exists():shutil.copy2(source,before)
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(before.read_bytes()).digest()
doc=Document(before);old=Document(before)
steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert len(steps(old))==330
anchor=next(p for p in doc.paragraphs if p.text=='65  底板与上平台的3D打印备用件')
body=doc._element.body;start=list(body).index(anchor._p)
for el in list(body)[start:]:
 if el.tag!=qn('w:sectPr'):body.remove(el)
kept_tables=len(doc.tables);assert kept_tables==66
ns=dict(globals());ns.update({'doc':doc,'audit':{'figures':[]}})
exec((REPO/'docs/manual/pcb-a-update-20261012/retained_formatting.py').read_text(encoding='utf-8'),ns)
heading,para,figure,table=[ns[k]for k in ['heading','para','figure','table']]
heading('65  底板与上平台的3D打印备用件',1,True)
para('按用户指定的PLA改为保守轻量版：两片板均保持整片，安装面连续3mm、底面减薄2mm，筋与已知安装区保留5mm。P01侧立，P02安装面贴床、凹腔朝上打印；外形、四柱孔和60mm柱的高度链保持。')
heading('65.1  整片尺寸和打印文件')
figure(ROOT/'preview/01_dimensions.png','图解 50  浅蓝区域为底面减薄腔；连续面3mm、外框和筋5mm，原四孔保持。','轻量版底板8个凹腔，上平台6个凹腔；凹腔从底面减薄2毫米，上表面连续3毫米。',17.5)
table(['文件，位于3mf/P2S/','包络 mm','CAD体积减少'],[
 ('P01_light_upright45.3mf','201.53×201.53×220','14.6%'),('P02_light_face_down.3mf','240×190×5','14.1%'),('C01_upright_hole_test.3mf','70×5×24','试孔片')
],[8.0,6.0,3.5],size=9.5,center=(1,2))
para('减少比例是对原5mm实心几何的体积比较，不是实际切片耗材或强度保留比例。按毫米、100%导入，各主板独立打印。通用3MF只有方向和几何，不含机器预设与G-code；需选择实际P2S、喷嘴、热床和PLA后切片。',10)
para('轻量STEP为P01_light.step、P02_light.step；3mf/reference/保留原5mm厚板作为对照和备选。电机等孔槽仍按实物增补。',10)
heading('65.2  P2S侧立方向与切片检查',2,True)
figure(ROOT/'preview/03_P01_upright.png','图解 51  280mm长边在热床内走对角线，220mm边向上；灰面为256mm热床。','整片底板侧立并绕打印机Z轴转45度，模型包络约201.53乘201.53乘220毫米。',14.5)
para('P2S官方成型空间为256×256×256mm。底板先绕原X轴转90°，再绕打印机Z轴转45°，平移到XY中心(128,128)、最低点Z=0。模型厚度也计入投影：(280+5)/√2≈201.53mm。不能把280mm边直接朝上，也不要点自动朝向令大面躺平。',10)
table(['项目','本版试制起点与检查'],[
 ('P01侧立','可从12mm外侧brim开始；含brim保守包络225.53×225.53×220mm。文件本身不含brim，需在切片中启用并检查首层接触、高层晃动和孔顶桥接。'),
 ('P02翻面平放','连续安装面贴床、减薄腔朝上；可从5mm brim开始，包络250×200×5mm。打印后翻回装车方向。'),
 ('PLA试制起点','0.20mm层高、4道壁、30% gyroid填充、顶底各8层。竖板用较低外壁速度和加速度，检查凹腔45°收口与孔顶桥接；以实际切片和试打调整。')
],[3.5,14.0],size=9.5)
para('规格依据：Bambu Lab官方P2S介绍及BambuStudio官方P2S 0.4配置；入口见模型README。包络检查通过不等于实际切片或打印成功。',9.5)
heading('65.3  加强区和装车验证',2,True)
figure(ROOT/'preview/04_underside.png','图解 52  底面减薄，外框、加强筋和安装区完整保留5mm；没有大面积贯穿孔。','PLA轻量版底面凹腔示意，连续面3毫米、筋间距至少12毫米；已知安装区保留5毫米。',15.4)
for t in [
 '1．四柱孔周围半径14mm的原板内区域保留5mm。底板电机转接参考区与前万向球转接区保留厚料；上平台桶壳壁脚周围24mm宽支撑带保留5mm。凹腔平面圆角R3、腔根圆角R0.6。',
 '2．先试C01水平孔，再打印两片主板。底板凹腔收口沿打印向上方向用45°坡面过渡；上平台凹腔朝上，避免跨整个凹腔打印平顶。',
 '3．沿用四根60mm柱，上平台相对底板偏移(20,15)，总高度链70mm。新增受力孔优先放5mm厚料区；穿过3mm区时先补局部实心台，不直接沿用5mm板的紧固件长度。',
 '4．断电按真实支承点逐步加载到计划载荷，检查挠曲、层间裂纹、孔边白化和松动；异常时换回厚板或加强后再验。合格后再手推、架空轮组及低速试车。'
]:para(t,10)
para('用户未指定最大载荷，本版没有额定承重值。数字几何检查通过，但局部减薄会降低局部刚度；不声称与原5mm实心板等强。尚未做实际切片、有限元、打印和承重试验；原330步骤与当前电气路线保持。',10)
out=WORK/NAME;doc.save(out);new=Document(out)
assert steps(old)==steps(new)
tabs=lambda d:[[[c.text for c in r.cells]for r in t.rows]for t in d.tables]
assert tabs(old)[:66]==tabs(new)[:66]
# All media referenced before chapter65 remain byte-identical; later obsolete media are detached.
audit={'baseline_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'steps_preserved':330,'original_tables_preserved':66,
 'chapter_replaced':65,'figures':[50,51,52],'output':str(out)}
(WORK/'edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
