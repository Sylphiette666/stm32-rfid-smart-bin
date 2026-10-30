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
WORK=REPO.parent/'.p2s-whole-20261030/manual';WORK.mkdir(parents=True,exist_ok=True)
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
para('2026年10月30日按用户指定的拓竹P2S修订：底板和上平台均保留完整单件。P01侧立并沿热床对角线打印，P02整片平放；撤下原分块和连接片方案。原外形、5mm板厚、四个立柱孔与60mm柱的高度链保持。')
heading('65.1  整片尺寸和打印文件')
figure(ROOT/'preview/01_dimensions.png','图解 50  P01与P02完整板件；蓝色十字为原四个Ø3.4立柱孔。','P01为280乘220乘5，P02为240乘190乘5，每片只有原四个立柱孔，没有拼缝、连接片和拼接孔。',17.5)
table(['文件，位于3mf/P2S/','数量','摆放包络 mm'],[
 ('P01_upright45.3mf','1','201.53×201.53×220'),('P02_flat.3mf','1','240×190×5'),('C01_upright_hole_test.3mf','1，先试孔','70×5×24')
],[8.4,2.8,6.3],center=(1,2))
para('全部以毫米、100%比例导入。通用3MF已写入几何方向，但不含P2S机器预设、切片结果或G-code。Bambu Studio中选择实际P2S、喷嘴、热床和耗材，各主板分成独立打印任务。',10)
para('原坐标STEP在step/P01_full.step和P02_full.step，供增补实物孔槽。stl/full/中的P01是原始平放几何；打印应使用P2S目录内的侧立文件，避免直接平放超出热床。',10)
heading('65.2  P2S侧立方向与切片检查',2,True)
figure(ROOT/'preview/03_P01_upright.png','图解 51  280mm长边在热床内走对角线，220mm边向上；灰面为256mm热床。','整片底板侧立并绕打印机Z轴转45度，模型包络约201.53乘201.53乘220毫米。',14.5)
para('P2S官方成型空间为256×256×256mm。底板先绕原X轴转90°，再绕打印机Z轴转45°，平移到XY中心(128,128)、最低点Z=0。模型厚度也计入投影：(280+5)/√2≈201.53mm。不能把280mm边直接朝上，也不要点自动朝向令大面躺平。',10)
table(['项目','本版试制起点与检查'],[
 ('P01侧立','可从12mm外侧brim开始；含brim保守包络225.53×225.53×220mm。文件本身不含brim，需在切片中启用并检查首层接触、高层晃动和孔顶桥接。'),
 ('P02平放','可从5mm brim开始，包络250×200×5mm。逐层查看边角和孔位，不缩放整块板。'),
 ('配置与速度','选择实际P2S与耗材预设，0.20mm Standard可作起点；竖板需较低外壁速度和加速度。支撑、brim间隙与最终速度以切片和试打印决定。')
],[3.5,14.0],size=9.5)
para('规格依据：Bambu Lab官方P2S介绍及BambuStudio官方P2S 0.4配置；入口见模型README。包络检查通过不等于实际切片或打印成功。',9.5)
heading('65.3  试孔与整板装车',2,True)
figure(ROOT/'preview/02_assembly.png','图解 52  两块整板通过原四根60mm柱连接，不增加拼接紧固件。','完整底板和上平台通过四根现有60毫米柱连接，上平台相对底板偏移20、15、65毫米。',15.7)
for t in [
 '1．先打印C01立式试片。沿原X从左到右孔径为3.2、3.4、3.6、3.8mm，孔心距底12mm；底板孔轴水平，须检查孔顶下垂和缩径。必要时调整孔补偿或打印后夹紧修孔。',
 '2．P01和P02各打印一片，清理brim及所需的可拆辅助支撑。量完整外形、5mm板厚与四柱孔，检查板面平整、层间和孔边无裂纹。',
 '3．上平台左下角相对底板偏移(20,15)，四柱孔自然对齐。沿用60mm双通柱；底板底面至上平台顶面仍为70mm。原立柱螺钉按5mm板厚复核咬合和顶底。',
 '4．电机转接、电池绑带、万向球、桶壳及电子托板孔槽按实物增补。无需原分块连接片和24套拼接紧固件；立柱、轮组等原有紧固件仍保留。',
 '5．断电按真实支承点逐步加载，检查挠曲、层间裂纹、孔边破坏和松动；合格后再手推、架空轮组及低速试车。竖向打印塑料的性能不能按胶合板推定。'
]:para(t,10)
para('数字检查已完成：完整单件、封闭网格、STEP/3MF回读、旋转不缩放、四柱孔同轴和带brim名义包络。尚未进行Bambu Studio实际切片、实物打印或承重验证。原330步骤保留，电气制作路线不变。',10)
out=WORK/NAME;doc.save(out);new=Document(out)
assert steps(old)==steps(new)
tabs=lambda d:[[[c.text for c in r.cells]for r in t.rows]for t in d.tables]
assert tabs(old)[:66]==tabs(new)[:66]
# All media referenced before chapter65 remain byte-identical; later obsolete media are detached.
audit={'baseline_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),'steps_preserved':330,'original_tables_preserved':66,
 'chapter_replaced':65,'figures':[50,51,52],'output':str(out)}
(WORK/'edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
