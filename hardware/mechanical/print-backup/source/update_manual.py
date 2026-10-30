from pathlib import Path
import hashlib, shutil, re, json, zipfile
from collections import Counter
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

REPO=Path(__file__).resolve().parents[4]
ROOT=REPO/'hardware/mechanical/print-backup'
WORK=REPO.parent/'.mechanical-print-20261030/manual'; WORK.mkdir(parents=True,exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
source=REPO/'docs/manual'/NAME
baseline=WORK/'before.docx'
if not baseline.exists(): shutil.copy2(source,baseline)
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(baseline.read_bytes()).digest(),'Manual changed concurrently; reconcile before replacing.'
doc=Document(baseline)
old_steps=[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert len(old_steps)==330
assert not any(p.text.startswith('65  底板') for p in doc.paragraphs)
# Same formatting helpers as the retained illustrated manual; original content is untouched.
ns=dict(globals()); ns.update({'doc':doc,'audit':{'figures':[]}})
exec((REPO/'docs/manual/pcb-a-update-20261012/retained_formatting.py').read_text(encoding='utf-8'),ns)
para=ns['para']; heading=ns['heading']; table=ns['table']; figure=ns['figure']
heading('65  底板与上平台的3D打印备用件',1,True)
para('木板锯错时，可按本章打印P01与P02备用板。原外形、5mm板厚、四个立柱孔和60mm柱的高度链保留。用户热床约220×220或256×256mm，故本版采用底板四块、上平台两块加底面连接片；塑料拼板的承载能力仍须实测，不能等同于原胶合板。')
heading('65.1  文件和分块尺寸')
figure(ROOT/'preview/01_dimensions.png','图解 50  蓝色十字为原立柱孔，灰色为底面连接片，虚线处留0.3mm拼缝。','P01为280乘220乘5，P02为240乘190乘5；立柱孔坐标标在图中，底板四块、上平台两块。',17.5)
table(['打印件','每件尺寸 mm','数量'],[
 ('P01四个分块','139.85×109.85×5','各1，共4'),
 ('P02两个分块','119.85×190×5','各1，共2'),
 ('J01底面连接片','64×28×4','6'),
 ('C01孔径试片','70×24×5','1，先试打印')
],[7.0,7.0,3.5],center=(1,2))
para('打印入口：hardware/mechanical/print-backup/3mf/split/ 或 stl/split/。所有文件按毫米、100%导入并逐件排版，不能整体缩小。前后方向、文件名、零件数量和孔径试片读法见该目录README.md。整片版只供更大热床使用。',10)
para('电机转接槽、电池绑带槽、万向球、桶壳及电子托板固定孔仍按实物测量。模型未虚构这些孔槽，打印前须确认布置并避开拼缝、连接片与新增紧固件。',10)
heading('65.2  连接片与打印设置',2,True)
para('分块连接另需24颗M3×16、90°沉头机螺钉，24颗M3金属螺母及24片M3平垫；不包含原立柱、轮组等原有紧固件。沉头顶口Ø6.4、贯通孔Ø3.4，沉头深1.5mm。先用试片核对实际头径、锥角和孔配合，确保螺钉顶面不凸起。')
table(['连接位置','安装顺序与要求'],[
 ('每块连接片4孔','从板上表面向下穿沉头螺钉；板底为4mm连接片，再加平垫、金属螺母。轻拧到不松动，不在打印塑料里直接攻丝。'),
 ('底板4块连接片','X=140两处和yb=110两处，各跨一条拼缝。每块连接片两颗螺钉固定拼缝一侧、另两颗固定另一侧。'),
 ('上平台2块连接片','位于局部(120,47.5)与(120,142.5)，连接X=120拼缝。沉头须齐平，避免顶起桶壳底板。'),
 ('板底新增空间','连接片、螺母及M3×16螺钉形成约11mm局部包络。核对离地、轮组、循迹传感器及上层下方模块/线束净空。')
],[4.0,13.5])
para('建议先用PETG试制，选匹配打印机和耗材的厂家预设。试制起点为0.4mm喷嘴、0.2mm层高、6道壁、顶底各8层、40% gyroid填充；连接片可用100%填充。全部大面朝下、沉头朝上，无需支撑；可从5mm brim试起，热床实际禁区仍以切片预览为准。')
para('以上是未经本机实打的起始参数，不是额定承重保证。C01靠y=8一排从左到右为Ø3.2、3.4、3.6、3.8；另一个为Ø3.4/顶口Ø6.4沉头。若间隙不合适，调整孔补偿或模型参数，不要缩放整板。')
para('材料与翘曲说明参考Prusa官方：help.prusa3d.com/article/petg_2059 和 /article/warping_2011。PETG的热床表面和隔离层按厂家说明选择。')
heading('65.3  拼装和装车检查',2,True)
figure(ROOT/'preview/02_assembly.png','图解 51  四根灰柱为现有60mm立柱；连接片在板底，紧固件和其它实物未显示。','两层分块板通过现有四柱连接，上平台相对底板偏移20、15、65毫米；只示意装配关系。',16.8)
for text in [
 '1．先试孔，再打印6块主板和6块连接片。平面朝下打印；去毛刺后检查板面平整、孔边和层间无裂纹。',
 '2．P01两条拼缝各留0.3mm，拼后量280×220；P02拼缝留0.3mm，拼后量240×190。量对角、松装连接片，再对称紧固；不可挤掉拼缝。',
 '3．P02左下角相对P01偏移(20,15)，4个立柱孔自然对齐。沿用60mm双通柱；底板底面至P02顶面仍为70mm。原立柱螺钉须按5mm板厚检查咬合和顶底。',
 '4．按实物布置电机、电池、万向球与桶壳，确认固定点不在拼缝边、板底紧固件不擦轮、不碰地、不压线。',
 '5．断电，按真实支承点逐步加载到计划载荷，检查下挠、拼缝张开、孔边白化及松动；再手推，最后才架空车轮与低速试车。变形或开裂就停用，改厚或增加连续金属加强条后重新检查高度链。'
]: para(text,10)
para('验证边界：数字模型的封闭网格、STEP/3MF回读、四柱孔同轴和拼接几何已检查；尚未进行实物打印、承重、长期蠕变及整机动态验证。原330步骤保留，完成本章试验不代表电气或整机验收完成。',10)
# Request Word to refresh fields on open; isolated render also refreshes the TOC now.
sett=doc.settings.element
el=sett.find(qn('w:updateFields'))
if el is None:el=OxmlElement('w:updateFields');sett.append(el)
el.set(qn('w:val'),'true')
out=WORK/NAME;doc.save(out)
new=Document(out)
assert old_steps==[p.text for p in new.paragraphs if re.match(r'步骤 \d{3}',p.text)]
old=Document(baseline)
assert [[[c.text for c in r.cells]for r in t.rows]for t in old.tables]==[[[c.text for c in r.cells]for r in t.rows]for t in new.tables[:len(old.tables)]]
def medias(p):
 with zipfile.ZipFile(p)as z:return Counter(hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()if n.startswith('word/media/'))
a,b=medias(baseline),medias(out);assert all(b[k]>=v for k,v in a.items())
audit={'baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'staging':str(out),'steps_preserved':330,'existing_tables_preserved':len(old.tables),'original_media_preserved':True,'added_chapter':65,'added_figures':[50,51]}
(WORK/'edit_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
