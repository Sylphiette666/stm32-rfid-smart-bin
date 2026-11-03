from pathlib import Path
import json,re,shutil,hashlib,ast
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2];W=R.parent/'codex_readback/integrated_pla_fast_manual_20261104';W.mkdir(exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
src=R/'docs/manual'/NAME;baseline=W/'before.docx';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if not baseline.exists():shutil.copy2(src,baseline)
assert sha(src)==sha(baseline),'Concurrent manual change; merge before publication'
d=Document(baseline);steps=lambda doc:[p.text for p in doc.paragraphs if re.match(r'步骤 \d{3}',p.text)]
oldsteps=steps(d);assert len(oldsteps)==330
for q in d.paragraphs[:120]:
 if q.text.startswith('保留原版330个步骤和既有图解。当前电气施工先读'):
  q.text='保留原版330个步骤和既有图解。电气施工先读第67章B1 PCB，机械结构读第68章，快速树形支撑和24小时目标的实际结果读第69章。旧版工程保留参考。'
tree=ast.parse((B/'integrated-pla-20261104/source/update_manual.py').read_text())
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['p','h','pic','table']:exec(compile(ast.Module(body=[n],type_ignores=[]),'<format helper>','exec'))
selection=json.loads((O/'checks/selection.json').read_text());rows=[];total=0;mass=0
for n,label in [('LOWER_H41_B1','下半主体'),('UPPER_INTEGRATED','上半主体'),('PANEL_COVER','可拆操作面板')]:
 r=json.loads((O/'checks'/f"{selection['variants'][n]}_{n}_slicing.json").read_text());v=r['result']['sliced_plates'][0]
 sec=v['total_predication'];g=sum(x['total_used_g'] for x in v['filaments']);total+=sec;mass+=g
 rows.append((label,r['process']['layer_height']+' mm',f'{int(sec)//3600}小时{int(sec)%3600//60}分',f'{g:.1f} g'))
h('69  PLA树形支撑与快速打印检查',1,True)
p('本章响应用户将打印时间缩短到24小时以内的要求。多轮真实切片后，当前选定方案合计约47小时42分，上半主体仍约33小时，24小时目标尚未达到。这里交付的是已检查的最快候选，不把提高未校准流量或关闭必要支撑当作已达标。')
table(['打印件','层高','预计时间','PLA含支撑'],rows,[4.2,3,5,4.1])
p('设备保持P2S、0.4 mm喷嘴、256×256 mm纹理PEI板和PLA；喷嘴220℃、热床55℃，使用官方Generic PLA的12 mm³/s最大体积流量。三件合计耗材约'+f'{mass:.1f} g。估算包含各盘启动流程，不包含换盘、冷却取件和人工拆支撑。')
p('主体改为0.28 mm层高、3道墙、10%螺旋体填充，顶底3层且最小0.8 mm；面板盖为0.20 mm。主体外墙120 mm/s、内墙230 mm/s，实际速度受流量、加速度和悬垂限速约束。与第68章0.08 mm工程相比，斜面台阶更明显，薄槽与孔仍需清理试配；不能声称保留同等表面精细度。')
p('主体采用自动细树形支撑：枝径3 mm、分支间距5 mm、分支角40°、支撑阈值35°、1道支撑壁；关闭独立支撑层高，使支撑与模型层对齐；上下Z间隙0.28 mm、XY间隙0.35 mm；上下接触各2层、接触间距0.5 mm；6 mm外侧裙边。面板盖平放无需支撑，使用3 mm裙边。')
p('下半主体保持原竖立方向；上半件重新搜索刚性旋转方向以减少悬垂支撑，模型未缩放，孔位与STEP结构未改。工程在integrated-pla-fast-20261104/projects，作为完整工程打开3MF并保留方向及100%比例。不得对它再用旧0.08 mm预设覆盖后仍引用本章时间。')
p('若24小时为硬性总时限，需要继续确认可调整条件：重新分件并改变支撑需求，或者提供实际PLA的流量标定结果。若24小时指单件，上半件也暂未达标。新结构的实物强度、层间结合、打印成功率和支撑拆除尚未验证。')
h('69.1  实际树形支撑路径',2,True)
for n in ['LOWER_H41_B1','UPPER_INTEGRATED']:
 pic(n+'_supports.png',10)
 p(('图69-1 下半主体。' if n.startswith('LOWER') else '图69-2 上半主体。')+'棕色由实际切片刀路每3层抽取1层显示，半透明蓝色为原尺寸模型；这不是手画的示意树。打印时使用完整3MF重新切片，不能拿抽样图代替全层路径。')
h('69.2  首层范围与检查结论',2,True)
q=d.add_paragraph()
for n in ['LOWER_H41_B1','UPPER_INTEGRATED']:q.add_run().add_picture(str(O/'preview'/f'first_layer_{n}.png'),width=Cm(8.3))
p('图69-3 左为下半件，右为上半件。蓝色模型与裙边、棕色树形支撑均取自实际首层。全部层的挤出路径另行检查均位于0—256 mm范围内。')
pic('first_layer_PANEL_COVER.png',7)
p('图69-4 可拆操作面板首层。该面板盖不需要树形支撑；强行加树形会增加耗材和清理工作。')
p('检查包括三件切片无最终警告、完整刀路床面范围和高度、支撑路径存在、工程几何与已检查切片一致，以及上半件旋转前后的模型坐标一致。CAD配合复用第68章检查；本轮没有重新宣称实物装配或承重验收。GitHub codex-cad与OrcaSlicer树形参数文档为流程参考，参数以本机Bambu Studio 02.08.02.61实际切片为准。')
assert steps(d)==oldsteps
d.save(W/NAME)
(W/'edit-audit.json').write_text(json.dumps({'baseline_sha256':sha(baseline),'chapter':69,'original_steps':330,'table_changes':[]},indent=2),encoding='utf8')
print(W/NAME)
