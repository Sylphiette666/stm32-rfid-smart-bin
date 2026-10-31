"""Publish human-readable release notes from the actual final check results."""
from pathlib import Path
import ast,json,csv,hashlib
import trimesh

REPO=Path(__file__).resolve().parents[4]
ROOT=Path(__file__).resolve().parents[1]/'mounted-20261031'
design=json.loads((ROOT/'source/design.json').read_text(encoding='utf-8'))
# Refresh the final wording after a packing run that may have read metadata
# before the independent hardware reviewer completed its text-only update.
tree=ast.parse((ROOT.parent/'source/build_mounted_design.py').read_text(encoding='utf-8'))
hardware_node=next(n for n in tree.body if isinstance(n,ast.Assign) and
    any(isinstance(t,ast.Name) and t.id=='hardware' for t in n.targets))
design['hardware']=ast.literal_eval(hardware_node.value)
printing=json.loads((ROOT/'checks/final_printing.json').read_text(encoding='utf-8'))
packing=json.loads((ROOT/'checks/packing.json').read_text(encoding='utf-8'))
assert printing['status']==packing['status']=='PASS'
assert len(printing['plates'])==2 and sum(p['objects'] for p in printing['plates'])==47

def duration(s):
    m=round(s/60);return f'{m//60}小时{m%60:02d}分'

rows=[]
parts={p['id']:p for p in design['parts']}
with (ROOT/'source/parts_index.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.writer(stream)
    writer.writerow(['盘号','物体ID','所属模块','角色','X最小/mm','Y最小/mm','X最大/mm','Y最大/mm','高度/mm','局部单件STL'])
    for plate in [1,2]:
        for file in sorted((ROOT/'geometry').glob(f'*_bed{plate}.stl')):
            ident=file.stem.removesuffix('_bed'+str(plate));m=trimesh.load_mesh(file)
            p=parts.get(ident,{})
            writer.writerow([plate,ident,p.get('module','主体'),p.get('role','主体'),
                *[round(v,3) for v in [*m.bounds[0,:2],*m.bounds[1,:2],m.extents[2]]],p.get('stl','见已排盘工程')])

for i,p in enumerate(printing['plates'],1):
    rows.append(f"| 第{i}盘 | [{Path(p['file']).name}]({p['file']}) | {p['objects']} | {duration(p['estimated_seconds'])} | {p['filament_g']:.0f} g |")

hardware='\n'.join(f"| {h['name']} | {h['spec']} | {h['quantity']} | {h.get('used_for','')}；{h.get('notes','')} |" for h in design['hardware'])
text=f'''# 一体底板、上平台与方案A活动夹具 · 两盘版

用户已选择方案A。底板280×220×5mm、上平台240×190×5mm均保持一整片；另配9套可开启模块夹具、电池托架双锁片、降压载座和喇叭定位圈。四个主体及43个附件合计47件，实际排在两盘。

## 打印只打开这两份工程

| 任务 | Bambu Studio工程 | 物体数 | 实际切片估算 | PLA |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(rows)}
| 合计 | 分两次启动，人工换盘另计 | 47 | {duration(printing['total_seconds'])} | {printing['total_filament_g']:.0f} g |

第一盘为完整底板及宽底斜撑、舵机托片和全部夹具小件（喇叭圈除外）；第二盘为平放上平台、平放舵机支架及喇叭圈。工程不含可直接执行的G-code，打开为**项目**后按实际P2S、0.4mm喷嘴、PLA和热床重新切片。

保持100%比例、原朝向、原位置和**逐层打印**。不要自动排布、自动朝向或切到逐件打印。所有物体各自贴床；部分小件放在卡座/压框的镂空区和斜撑的空区内，经过实体无交集与取件通道检查。不要将设计用的ASSEMBLY_VIEW_ONLY.step或绿色电子板示意体当作打印文件。

P2S 0.4mm，0.24mm层高、首层0.2mm、4道墙、30% gyroid、顶底7层/最小1.6mm、PLA热床60℃。第一盘3mm防翘边，第二盘1mm，间隙0；模型已有专用斜撑，全局自动支撑关闭。第二盘后缘达到Y254mm，**保留工程中的喷嘴缠料检测关闭**；这项会占用后侧检测区，相机炒面检测是独立功能，可保持开启。已核对最终测试G-code没有执行G39。不要擅自加宽第二盘防翘边。

底板50°斜放，三组三角框架高205mm、杆宽4mm/厚3.2mm，撑脚宽12mm/厚3.2mm、展开约175mm，底轨连接。完全冷却后托住板面，用斜口钳逐个剪掉短连接点、框架与起始边，再修平残留；不扭折或切开板件本体。首层及中途若脱底、翘起或明显晃动应停止处理。几何加强不能保证零失败。

![第一盘](preview/05_plate1.png)
![第二盘](preview/06_plate2.png)

## 模块固定与取件

![模块位置](preview/01_layout.png)
![方案A开启](preview/03_clamp_open_closed.png)

先转开蓝色锁片，再翻开橙色压框。金属M3铰链轴与刚性拨片承载；独立PLA簧片只定位，不作承载钩。轴座已补偿实际落座高度，锁母留0.1–0.2mm轴向转动间隙。簧片锚点上方垫圈外径不得超过6mm，不在拨片轴座与拨片间另加圆垫圈遮住凸点。

拆下小件前按[零件索引](source/parts_index.csv)的盘号、XY位置和模块ID做好标记。先去除防翘边，细簧片不要直接扭断；保持1.16mm自由梁完整。各电子板先空装试合，压框仅搭角边，不能压弯PCB；排针塑壳、焊点及插好杜邦线后的弯线包络须按实物复核。接口方向与20mm等架空高度见design.json。维护时可先拆上平台。

电池76×40×20mm、2S串联，托条铺2mm EVA，双锁片只约束端部塑料外壳、不挤压电芯；出线朝+X。喇叭Ø40×14、耳距48mm，耳高未实测，使用可调螺母与垫圈，不能强压耳片。5V降压两安装孔按用户实测(7,19)/(36,2)、Ø3mm，四角焊盘不作安装孔；M2.5螺母先装入底面六角窝，再固定载座。

## 五金（不含原四柱与舵机转接件）

| 名称 | 规格 | 数量 | 用途与注意 |
| --- | --- | ---: | --- |
{hardware}

P03/P04原接口保持，托片和支架脚另需4套M3×16、平垫与螺母。P03顶端调节槽仍为通用转接接口，不是已经测定的SG90安装耳孔。

## 验证与文件

已完成47件封闭网格、床面/边界、逐对实体相交、套排件取出、9套压框开盖和最终P2S实际切片检查。两份原生工程不含G-code；重读后的全部model XML与实际切片时一致。首层路径见preview/07、08，详细记录见checks/。

**新版尚未实物打印、循环寿命或承重验证，无额定载荷。**背针角落塑壳、喇叭耳高仍需试装；电机支架、万向球、循迹/碰撞模块、保险与总开关的真实孔距未提供，未伪造已测安装孔。安装后按原手册逐步加载检查。

parts/为归零的独立小件STL，step/为CAD与整片板源，geometry/为已排盘网格，source/design.json记录孔位、模块朝向和五金。构建与渲染源在上一级source/。旧四件侧立同盘曾倾倒，停止推荐；旧仅支撑原型的22小时45分不适用于新增43件安装机构的本版。
'''
(ROOT/'README.md').write_text(text,encoding='utf-8')

mechanical=ROOT.parent/'README.md'
old=mechanical.read_text(encoding='utf-8');start=old.index('# PLA 四件同盘打印包')
history=old[start:].replace('# PLA 四件同盘打印包','# 历史：四件侧立同盘（曾倾倒，停止推荐）',1)
history=history.replace('推荐打开 **`3mf/combined/P2S_ALL4_PLA_0p4_READY.3mf`**','历史工程 **`3mf/combined/P2S_ALL4_PLA_0p4_READY.3mf`**',1)
mechanical.write_text('# 当前打印文件：方案A模块夹具，两盘版\n\n'+
    '[打开最新模型、两份打印工程与装配说明](mounted-20261031/README.md)。底板和上平台各为一整片，四个主体＋43个固定附件共47件，已排两盘并完成实际切片。合计约'+duration(printing['total_seconds'])+f"、{printing['total_filament_g']:.0f}g PLA，尚未实打。图解已更新到同名Word第65章。\n\n旧的侧立同盘已发生倾倒，下方仅作历史记录。仅支撑原型未经模块安装位集成，不是本轮打印文件。\n\n---\n\n"+history,encoding='utf-8')

readme=REPO/'README.md';lines=readme.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
    if line.startswith('6. [底板与上平台3D打印备用件]'):
        lines[i]='6. [底板、上平台及方案A模块夹具两盘打印版](hardware/mechanical/print-backup/mounted-20261031/README.md)：两片各自一体，底板50°宽底斜撑，上平台和舵机支架平放；四个主体＋43个附件共47件，两次打印合计约'+duration(printing['total_seconds'])+f"/{printing['total_filament_g']:.0f}g PLA。已实际切片，尚未实物验证。Word第65章含模块位置、开闭机构和双盘图解。"
readme.write_text('\n'.join(lines)+'\n',encoding='utf-8')

assembly=REPO/'docs/manual/ASSEMBLY.md';old=assembly.read_text(encoding='utf-8');prefix=old[:old.index('## 65 底板与上平台3D打印备用件')]
assembly.write_text(prefix+'''## 65 整片平台、模块位置与方案A夹具

最新[两盘打印与安装说明](../../hardware/mechanical/print-backup/mounted-20261031/README.md)，图解50–57已合入同名Word第65章。原330步保持编号。

底板280×220×5mm、上平台240×190×5mm均整片打印，无切块或拼接。底板保留连续3mm面和5mm筋/安装加强，新增52处安装孔。四柱、60mm柱高、上平台(20,15)偏移和舵机托片接口保持。

13个模块位置、板面/排针方向、USB/SWD/TF/蓝牙天线方向及安装高度以布局图和source/design.json为准。9个无孔小板采用可开启压框＋M3金属铰链＋90°刚性拨片＋独立定位簧片；电池采用独立托架及两端旋转片，5V降压用实测大安装孔，喇叭用Ø40圈/48mm耳距/可调螺母。

第一盘为完整底板＋三组宽底可拆斜撑、舵机托片及夹具（喇叭圈除外）；第二盘为平放上平台、平放舵机支架和喇叭圈。43个附件与四主体共47件，都各自贴床。按原工程位置100%、逐层打印，关闭自动排布/朝向、全局自动支撑；第二盘保留1mm防翘边、喷嘴缠料检测关闭，相机炒面检测独立保留。

实际切片时间与用量、所有五金、取件与装配顺序见最新README和同名Word。旧四件侧立同盘已发生倾倒，停止推荐；旧仅支撑版本的估算不用于新增夹具版本。

新版仅完成几何、运动包络、封闭网格和实际切片检查，尚未完成实物打印/承重/循环寿命验证。电机等下侧真实孔距、背针塑壳和线缆实际包络仍须实物核对；数字检查不能保证零失败。
''',encoding='utf-8')
design['status']='two_plate_native_projects_slice_verified_unprinted'
(ROOT/'source/design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','total':duration(printing['total_seconds']),'objects':47},ensure_ascii=False))
