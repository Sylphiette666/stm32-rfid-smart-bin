"""Release notes and staged Word update for the flat, bolted chassis revision."""
from pathlib import Path
import json,hashlib,shutil,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
OUT=ROOT/'flat-split-20261101';WORK=REPO.parent/'.p2s-flat-split-20261101/manual';WORK.mkdir(parents=True,exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
printing=load(OUT/'checks/final_printing.json');design=load(OUT/'source/design.json');packing=load(OUT/'checks/packing.json')
assert printing['status']=='PASS' and len(printing['plates'])==3 and packing['total_objects']==51
# Correct descriptive metadata only; slicing and native geometry stay unchanged.
printing['notes']=[v.replace('两项任务','三项任务') for v in printing['notes']]
(OUT/'checks/final_printing.json').write_text(json.dumps(printing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'projects/result.json').unlink(missing_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def time(s):
 s=round(s);return f'{s//3600}小时{s%3600//60}分{s%60}秒'
rows=[]
contents=['底板后半片＋部分卡座及连接片','底板前半片＋托片及其余卡座/连接片','整片上平台＋平放舵机支架＋喇叭圈']
for i,p in enumerate(printing['plates'],1):rows.append([str(i),contents[i-1],str(p['objects']),time(p['estimated_seconds']),f"{p['filament_g']:.1f} g"])
readme='''# 当前打印版：原尺寸底板平放拼接，上平台一体平放

旧50°底板斜撑方案已停用。用户允许在缩短底板会影响原方案时改为拼接。本版保留280×220×5 mm外形、原4个立柱孔、52个模块孔、原电机与前万向球实心加强区、上平台偏移(20,15)和60 mm立柱。没有缩放模块、卡座或螺丝孔。

缩短为250 mm会截掉原前万向球加强区X=214..270的一部分，并改变X=250的前柱和上平台定位，因此没有采用缩短方案。

## 打印只打开这三份工程

| 盘号 | 文件 | 内容 | 预计时间 | PLA |
| --- | --- | --- | --- | --- |
'''
for i,p in enumerate(printing['plates'],1):readme+=f"| {i} | [{Path(p['file']).name}]({p['file']}) | {contents[i-1]} | {time(p['estimated_seconds'])} | {p['filament_g']:.1f} g |\n"
readme+=f"\n合计 **{time(printing['total_seconds'])}、{printing['total_filament_g']:.1f} g PLA**，共51件。含三次起止脚本，不含人工换板。较上一版同套夹具的斜撑任务28小时53分减少约6小时、64 g；换盘次数从2次任务增为3次。当前排布已验证，但不宣称三盘是所有任意形状套排的数学最优解。\n"
readme+='''
以“项目”打开，保留100%比例、原位置、朝向及逐层打印。不要自动排盘或逐件打印。模型均直接贴床，底板与上平台的连续平面朝床、减重槽朝上；装车时翻回光滑面朝上。工程不含G-code，按实际P2S/0.4 mm喷嘴/PLA/板型重新切片。

参数已写入：0.24 mm层高，首层0.20 mm，4墙，30% gyroid，顶底7层/最小1.6 mm，Generic PLA 220℃、纹理PEI 60℃。第1、2盘外侧防翘边2 mm，第3盘1 mm，间隙0；自动支撑、擦料塔关闭。保留喷嘴缠料检测关闭，第三盘占后侧检测区；相机炒面检测可开。使用标准100%速度、打印前调平并清洁床面。

![第1盘](preview/05_plate1.png)
![第2盘](preview/06_plate2.png)
![第3盘](preview/09_plate3.png)

## 底板如何拼接

两片在X≈138 mm处连接，主体接缝名义0.30 mm。两个定位舌只用于对齐；定位槽每侧留0.25 mm间隙。三块40×24×5 mm连接片装在底板下面，中心为(138,82)、(138,110)、(138,138)。连接片与底板接触处补为5 mm实心厚度。

![拼接位置](preview/01_join_layout.png)
![紧固剖面](preview/02_join_section.png)

新增12孔Ø3.4 mm：X=126/150，Y=76/88/104/116/132/144。每片连接片的孔距为24×12 mm。新增五金（原方案夹具五金另计）：

| 五金 | 规格 | 数量 |
| --- | --- | ---: |
| 螺钉 | M3×16，ISO7380低圆头，头Ø5.7/高1.65 | 12 |
| 平垫圈 | 内径3.2、外径≤6、厚0.5 mm | 24 |
| 防松螺母 | M3 DIN985，高4 mm | 12 |

先去毛边、在平桌上侧向插合两片，量外形280×220并检查板面齐平。将三块连接片放到底面，螺钉从光滑板面向下穿：头下垫圈→底板→连接片→垫圈→防松螺母。先将12颗全部带上，再交替轻拧到连接片贴紧；不得压裂PLA。定位舌不能强掰。完成拼接后再装A1 PCB和其他模块。

M3×16螺钉最低点在原底板下10.5 mm；按原底板底面离地45 mm参考，名义余量34.5 mm。上方头部含垫圈高2.15 mm，距A1板底名义7.85 mm。实际轮组、导线及A1背部焊脚包络仍需试装；未知实物尺寸没有被数字检查替代。

## 校验与试装边界

两片底板、三块连接片及其余小件共51个独立封闭网格；所有件直接贴床、无实体相交。原56个孔逐孔检查保留，新增12孔检查；三个原电机/万向球加强区无被切除部分。新增螺钉头与已有夹具没有数字模型交集。三盘官方P2S CLI切片返回0且无警告；原生3MF几何和摆放与实际受测工程一致，实际首层23/25/3个对象都在256 mm床内。未修改用户打印机或发送打印任务。

尚未进行实物打印、接缝承重或疲劳验证，无额定承重值。装配后先空载、再逐步加实际使用重量检查接缝开口、板面弯曲、螺母松动及轮组/导线干涉；不能把PCB当作接缝连接件。原43件模块夹具的尺寸和固定方式仍按第65章；旧65.6–65.11斜撑排布仅归档，打印以本版/第66章为准。

项目入口是projects/的三份3MF。parts/是独立平放STL；step/是装配坐标CAD源；source/parts_index.csv用于按盘号和XY坐标辨认小件。source/assembly_*.stl与P01_ASSEMBLY_VIEW_ONLY.step只供看装配，不能当作一件送去打印。
'''
readme=readme.replace('旧50°底板斜撑方案已停用。','**已先打印附件精细盘的用户：后续请用[主体补打三盘](../body-after-accessories-20261101/README.md)，不要再打印下表全量盘中的重复附件。**\n\n旧50°底板斜撑方案已停用。')
(OUT/'README.md').write_text(readme,encoding='utf-8')
# Stage a new manual while preserving an exact recoverable baseline.
published=REPO/'docs/manual'/NAME
if not (WORK/'before.docx').exists():shutil.copy2(published,WORK/'before.docx')
assert sha(published)==sha(WORK/'before.docx'),'Published manual changed while staging.'
doc=Document(WORK/'before.docx')
for i,p in enumerate(doc.paragraphs):
 if p.style.name=='Heading 1' and p.text.startswith('65 '):
  p.text='65  模块位置与方案A夹具（旧打印排布归档）'
  doc.paragraphs[i+1].text='本章保留模块位置、安装孔与方案A可开启压框的装配资料。底板打印已改为第66章的原尺寸平放拼接版，上平台仍整片平放；本章旧两盘斜撑工程已停用。'
  doc.paragraphs[i+2].text='本章65.6至65.11仅作旧排布归档，不能据此再次启动斜撑打印。模块卡座尺寸和固定方式继续有效；实际底板接缝、三盘工程、时间与参数以第66章为准。'
 for old,new in [('65.6  打印项目和实际切片记录','65.6  旧打印项目和切片记录（已停用）'),('65.7  第一项打印任务的摆放','65.7  旧第一盘摆放（已停用）'),('65.8  第一项打印任务的热床核对','65.8  旧第一盘热床记录'),('65.9  第二项打印任务的摆放','65.9  旧第二盘摆放（已停用）'),('65.10  第二项打印任务的热床核对','65.10  旧第二盘热床记录'),('65.11  打印检查和拆除辅助结构','65.11  旧斜撑拆除说明（仅归档）')]:
  if p.style.name=='Heading 2' and p.text==old:p.text=new

def paragraph(s):
 p=doc.add_paragraph(s);p.paragraph_format.space_after=Pt(6);return p

def heading(s,level=2):
 p=doc.add_heading(s,level);p.paragraph_format.page_break_before=True;return p

def table(headers,data,widths=None):
 t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=False
 for c,v in zip(t.rows[0].cells,headers):c.text=v
 for row in data:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for ri,row in enumerate(t.rows):
  row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
  for ci,c in enumerate(row.cells):
   if widths:c.width=Cm(widths[ci])
   for p in c.paragraphs:
    p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3)
    for run in p.runs:run.font.size=Pt(9);run.bold=(ri==0)
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E7EFF3');c._tc.get_or_add_tcPr().append(sh)
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 return t

def figure(file,caption,width=15.4):
 p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(3)
 p.add_run().add_picture(str(OUT/'preview'/file),width=Cm(width))
 q=paragraph(caption);q.alignment=WD_ALIGN_PARAGRAPH.CENTER
 for r in q.runs:r.font.size=Pt(9)

heading('66  原尺寸底板平放拼接与三盘打印',1)
paragraph('本版替代旧底板斜撑方案。底板外形保持280×220×5 mm，以两片平放打印后螺栓连接；上平台240×190×5 mm保持一整片。电子模块、卡座、原4个立柱孔与52个模块孔不缩放、不移动。')
paragraph('未采用250 mm短底板：原前万向球实心加强区到X=270，前柱在X=250，上平台仍按(20,15)定位；缩短会改变这些结构条件。按用户允许的备选路线，保留原机械坐标并设计接缝。')
table(['盘号','打印内容','件数','实际切片估算','PLA'],rows,[1,6,1,4,2.8])
paragraph(f"总计{time(printing['total_seconds'])}，{printing['total_filament_g']:.1f} g PLA。三项任务均含机器起止脚本，不含人工换板。较上版同套安装夹具的两盘斜撑任务节省约6小时、64 g，但需要多一次打印启动和换板。")
paragraph('三盘全部平放，最高约31.4 mm；自动支撑关闭。已完成几何、装配净空和实际切片检查，尚未实物打印或做接缝承重测试。')
paragraph('打印入口：flat-split-20261101/projects/ 下 P2S_FLAT_SPLIT_PLATE_1.3mf、P2S_FLAT_SPLIT_PLATE_2.3mf、P2S_FLAT_SPLIT_PLATE_3.3mf。作为项目打开，不能只导入网格。')
heading('66.1  定位舌与底部连接片')
figure('01_join_layout.png','图解 58  底板原尺寸拼接位置；橙色是底面连接片投影。',14.7)
paragraph('主体接缝名义0.30 mm；两处定位槽每侧留0.25 mm。定位舌负责对齐，三块底部连接片及螺钉承担接缝连接；不能仅插合定位舌就带载使用。')
heading('66.2  接缝螺钉与装配顺序')
figure('02_join_section.png','图解 59  M3×16螺钉从光滑板面向下穿，连接片位于底板下面。',15.7)
table(['新增五金（原夹具五金另计）','规格','数量'],[['低圆头螺钉','M3×16，ISO7380，头Ø5.7/高1.65 mm','12'],['平垫圈','内径3.2、外径≤6、厚0.5 mm','24'],['防松螺母','M3 DIN985，高4 mm','12']],[5,8,1.8])
paragraph('先去毛边并侧向插合两片，在平桌上量280×220外形、核对板面齐平。三块连接片各穿四颗螺钉；全部带上螺母后交替轻拧到贴紧，不压裂PLA。先完成拼接，再装A1 PCB。')
paragraph('连接片中心：(138,82)/(138,110)/(138,138)。新增孔Ø3.4，X=126/150与Y=76/88/104/116/132/144组合，共12孔。原模块孔不改变。')
for i,(file,title) in enumerate([('05_plate1.png','后半片及部分夹具'),('06_plate2.png','前半片、托片及其余夹具'),('09_plate3.png','上平台、舵机支架与喇叭圈')],1):
 heading(f'66.{i+2}  第{i}盘：{title}')
 figure(file,f'图解 {59+i}  第{i}盘原生工程排布；所有零件各自贴床。',15.7)
 p=printing['plates'][i-1];paragraph(f"文件：{Path(p['file']).name}。预计{time(p['estimated_seconds'])}，耗材{p['filament_g']:.1f} g，{p['objects']}个对象。保持100%比例与原位置，不自动排盘。")
 paragraph('板件连续平面贴床、减重槽朝上，装车时翻回光滑面朝上。小拨片和簧片可能套排在卡座镂空中，取下前按parts_index.csv标记；冷却后先切开防翘边，再分别取件。')
heading('66.6  参数、首层检查与装车复核')
table(['参数','本版工程设置'],[['机型/喷嘴/耗材','P2S / 0.4 mm / Generic PLA；按实际耗材核对'],['层高/首层','0.24 / 0.20 mm'],['墙/填充/顶底','4墙；30% gyroid；顶底各7层、最小1.6 mm'],['温度/热床','PLA 220℃；纹理PEI 60℃，实际板型必须一致'],['防翘边','第1、2盘2 mm；第3盘1 mm；间隙0'],['支撑/顺序/擦料塔','自动支撑关；逐层；擦料塔关'],['检测/速度','喷嘴缠料检测关；相机炒面检测可开；标准100%']],[4.5,10.3])
paragraph('第三盘使用后侧检测区，因此保留喷嘴缠料检测关闭；它与相机炒面检测是不同功能。三份工程不含G-code，重新切片后发送。打印前清洁板面、开启调平，首层若脱底或翘起应停止处理。')
paragraph('新增螺钉最低点距原底板下表面10.5 mm。按原Hb=45参考，名义离地余量34.5 mm；实际轮组、万向球转接片和导线需要试装。新增头部含垫圈高2.15 mm，距A1板底名义7.85 mm；背部焊脚不能碰到金属头部。')
paragraph('数字检查保留原56孔和电机/万向球加强区，新孔、连接片与现有夹具无冲突；实际首层23/25/3对象全部在床内。没有进行实物打印、额定承重或疲劳验证。先空载，再逐步增加实际使用重量，检查接缝张开、板面弯曲、螺母松动及走线干涉；PCB不得承担接缝连接作用。')
# Optional immediate fine-accessory route: cover the remaining eight objects exactly once.
fine=load(ROOT/'accessories-fine-20261101/checks/final_printing.json')
rest=load(ROOT/'body-after-accessories-20261101/checks/final_printing.json')
heading('66.7  先打印精细附件，再补打主体')
paragraph('附件精细盘基于原两盘版第一盘，只删除底板及相连斜撑，保留43件原尺寸附件与托片，原位置不变。文件为P2S_ORIGINAL_PLATE1_NO_BASE_FINE_016.3mf。')
paragraph('精细参数：层高0.16 mm、首层0.20 mm、外墙40/内墙80 mm/s，4墙、30% gyroid、顶底10层/最小1.6 mm。其余保持原工程设置。层高改善层向细节，不等同于孔径公差保证，不要整体缩放卡座或改变孔径补偿。')
paragraph(f"附件盘实际切片{time(fine['total_seconds'])}，{fine['total_filament_g']:.1f} g PLA。作为项目打开后重新切片，用标准100%速度。工程已无底板及斜撑。")
paragraph('采用附件精细盘后，后续只使用body-after-accessories-20261101/projects/内三份主体补打文件；不要再打印本章66.3和66.4的全量盘，否则会重复打印附件。')
rest_rows=[]
for i,p in enumerate(rest['plates'],1):rest_rows.append([str(i),['后半片＋连接片2块','前半片＋连接片1块','上平台＋舵机支架＋喇叭圈'][i-1],str(p['objects']),time(p['estimated_seconds'])])
table(['主体补打盘','内容','件数','预计时间'],rest_rows,[2,6.3,1,5.5])
paragraph('三份主体文件名为P2S_BODY_AFTER_ACCESSORIES_PLATE_1.3mf至PLATE_3.3mf，保留0.24 mm层高。精细43件和主体8件互不重复，合计仍是51件；底板拼接的螺钉和连接方法仍按66.1、66.2执行。')
paragraph(f"精细附件＋主体补打共四次任务，约{time(fine['total_seconds']+rest['total_seconds'])}、{fine['total_filament_g']+rest['total_filament_g']:.1f} g PLA，人工换板另计。若尚未打印任何附件且更重视打印次数，可使用本章前三盘全量0.24 mm方案；两条路线不能叠加重复打印。")

# Preserve original procedures and all existing tables.
old=Document(WORK/'before.docx');steps=lambda d:[p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(doc)==steps(old) and len(steps(doc))==330
old_tables=[[[c.text for c in r.cells] for r in t.rows] for t in old.tables]
assert [[ [c.text for c in r.cells] for r in t.rows] for t in doc.tables][:len(old_tables)]==old_tables
doc.save(WORK/NAME)
(WORK/'authoring_checks.json').write_text(json.dumps({'original_steps_preserved':330,'original_tables_preserved':len(old_tables),'baseline_sha256':sha(WORK/'before.docx'),'staged_docx':str(WORK/NAME)},ensure_ascii=False,indent=2),encoding='utf-8')
# Update navigation and textual assembly addendum; leave archive artifacts byte-identical.
f=ROOT/'README.md';text=f.read_text(encoding='utf-8');lines=text.splitlines();lines[0]='# 当前打印文件：原尺寸底板平放拼接，三盘版';lines[2]='[打开最新三盘工程与拼接装配说明](flat-split-20261101/README.md)。保留280×220底板外形与原孔位，两片平放后螺栓连接；上平台一整片平放。51件约22小时45分/649g PLA，已切片，未实打。旧mounted-20261031斜撑工程已停用，夹具尺寸仍有效。新图解见同名Word第66章。';f.write_text('\n'.join(lines)+'\n',encoding='utf-8')
f=REPO/'README.md';text=f.read_text(encoding='utf-8');text=re.sub(r'^6\. \[底板、上平台及方案A模块夹具两盘打印版\].*$', '6. [底板平放拼接、上平台及方案A夹具三盘打印版](hardware/mechanical/print-backup/flat-split-20261101/README.md)：底板保留280×220及原孔位，以两片平放后螺栓连接；上平台一体平放，51件约22小时45分/649g PLA。已切片，未实打或承重验证；同名Word第66章为当前打印说明。旧斜撑工程已停用。',text,flags=re.M);f.write_text(text,encoding='utf-8')
f=REPO/'docs/manual/ASSEMBLY.md';text=f.read_text(encoding='utf-8');text=text.replace('最新[两盘打印与安装说明]','历史[两盘打印与安装说明]');cut=text.find('\n## 66 原尺寸底板平放拼接');text=text[:cut] if cut>=0 else text;text+='\n\n## 66 原尺寸底板平放拼接\n\n当前以[三盘平放工程及连接图](../../hardware/mechanical/print-backup/flat-split-20261101/README.md)为准。第65章夹具尺寸与模块位置继续有效，旧65.6至65.11斜撑排布已停用。底板280×220外形与原孔位不变，两个平放半片用三块40×24×5连接片和12颗M3×16低圆头螺钉拼接；上平台一整片。新增24片OD≤6/厚0.5垫圈、12颗高4 mm M3防松螺母。51件共三盘，实际切片约22小时45分、649g PLA。未实打、未承重验证。图58至62已合入同名手册第66章。\n';f.write_text(text,encoding='utf-8')
f=ROOT/'README.md'
s=f.read_text(encoding='utf-8');s=s.replace('# 当前打印文件：原尺寸底板平放拼接，三盘版','# 当前打印文件：附件精细盘＋主体平放补打')
s=s.replace('\n\n[打开最新三盘工程','\n\n现在先打印：[原第一盘去底板、0.16 mm精细版](accessories-fine-20261101/README.md)。完成后用[主体补打三盘](body-after-accessories-20261101/README.md)，避免重复附件。\n\n[打开最新三盘工程',1)
f.write_text(s,encoding='utf-8')
print(str(WORK/NAME),flush=True)
