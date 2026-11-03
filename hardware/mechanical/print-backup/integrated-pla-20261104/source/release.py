"""Publish only checked models/projects; retain physical-validation limits."""
from pathlib import Path
import json,zipfile,hashlib,shutil,re,subprocess
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2]
W=R.parent/'.p2s-integrated-pla-20261104';M=R.parent/'codex_readback/integrated_pla_manual_20261104'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
assert load(O/'checks/assembly_audit.json')['status']=='PASS'
assert load(O/'checks/critical_dimensions.json')['status']=='PASS'
assembly=load(O/'checks/assembly_step.json')
assert assembly['valid'] and assembly['solid_count']==3 and assembly['volume_relative_error']<.0001
assert max(assembly['bounds_max_difference_each_mm'])<.01
paths=load(O/'checks/path_review.json');records=[]
for n,label in [('LOWER_H41_B1','下半主体'),('UPPER_INTEGRATED','上半主体'),('PANEL_COVER','可拆操作面板')]:
 f=O/'projects'/f'P2S_{n}_PLA_008.3mf';r=load(O/'checks'/f'{n}_slicing.json')
 assert r['returncode']==0
 plate=r['result']['sliced_plates'][0];assert plate['warning_message']==''
 assert paths[n]['all_extrusions_in_bed'] and paths[n]['maximum_print_z_mm']<=256
 with zipfile.ZipFile(f) as z,zipfile.ZipFile(W/n/'sliced.3mf') as tested:
  assert z.testzip() is None and not any(k.endswith('.gcode') for k in z.namelist())
  assert all(z.read(k)==tested.read(k) for k in z.namelist() if k.endswith('.model'))
  c=json.loads(z.read('Metadata/project_settings.config'))
  assert c['layer_height']=='0.08' and set(c['filament_type'])=={'PLA'}
  assert 'P2S' in c['printer_settings_id']
  assert c['curr_bed_type']=='Textured PEI Plate'
  if n!='PANEL_COVER':
   assert c['support_type']=='tree(auto)' and c['support_style']=='tree_hybrid'
   assert c['enable_support']=='1' and c['brim_width']=='6'
 records.append({'id':n,'label':label,'project':f.relative_to(O).as_posix(),'sha256':sha(f),
 'seconds':plate['total_predication'],'grams':sum(v['total_used_g'] for v in plate['filaments']),
 'native_geometry_matches_sliced':True,'layer_height_mm':.08,'material':'PLA',
 'source_step_sha256':sha(O/'step'/f'{n}.step'),'warning_message':''})
qa=load(M/'qa.json');assert qa['status']=='STRUCTURAL_CHECKS_PASS' and qa['steps_preserved']==330
name='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
assert sha(M/name)==qa['docx_sha256']
for dst in [R/'docs/manual'/name,R.parent/name]:
 assert sha(dst) in {qa['baseline_sha256'],qa['docx_sha256']},'Manual changed after baseline; merge first'
for dst in [R/'docs/manual'/name,R.parent/name]:shutil.copy2(M/name,dst)
save(O/'checks/manual_qa.json',qa)
save(O/'checks/word_render.json',load(M/'word-render.json'))
summary={'status':'DIGITAL_GEOMETRY_AND_SLICE_CHECKS_PASS_PHYSICAL_TRIAL_REQUIRED','printer':'P2S 0.4 nozzle',
 'bed':'Textured PEI','bed_mm':[256,256,256],'material_user_confirmed':'PLA','slicer_version':'Bambu Studio 02.08.02.61 via local CLI host',
 'principal_integral_bodies':2,'separate_service_cover':True,'files':records,'no_print_job_sent':True,
 'physical_print_tested':False,'load_tested':False,'freecad_independent_check_performed':False,
 'checked':['valid single solid for each principal body','closed manifold meshes','STEP roundtrip','motor contact face identity',
 'PCB and closed module fixture interference','four platform pillars','functional through holes','removable panel interference',
 'full extruded-path bed bounds including supports and brim','project geometry identical to sliced geometry','manual original 330 steps preserved'],
 'limitations':['H41 is a nominal derived value, not measured Hb','tracker board thickness assumed 1.6 mm',
 'actual solder joints and cable bend space require trial fit','full wheel and lid moving envelopes not available',
 'PLA layer adhesion, load, fatigue, and support removal not physically tested','minimum mass is not proven by optimization or FEA']}
save(O/'checks/release.json',summary)
req=load(O/'checks/requirements.json');req['status']='USER_REQUIREMENTS_CONFIRMED_AND_DIGITAL_CHECKS_COMPLETE';save(O/'checks/requirements.json',req)
for file in ['lower_cabled_draft.json','upper_draft.json']:
 p=O/'checks'/file;d=load(p);d['status']='CAD_GEOMETRY_CHECKED_SEE_RELEASE_JSON';d['not_checked']=['physical printing, loads and dimensional accuracy','complete motor wheel and lid motion envelope','real cable routing','FreeCAD independent verification'];save(p,d)
lines=[]
for r in records:
 sec=round(r['seconds']);lines.append(f"| [{r['label']}]({r['project']}) | {sec//3600}小时{sec%3600//60}分 | {r['grams']:.1f} g |")
readme='''# PLA两主体一体结构与0.08 mm打印工程

本版以用户2026-11-04最后确认为准：PLA、拓竹P2S、0.4 mm喷嘴、纹理PEI、256×256 mm打印盘。保留B1 PCB的125×100 mm外形及90×90 mm孔距。请先读同名装配手册第68章；旧的PETG工程和分片结构不用于本版。

| 打印工程 | 切片估算耗时 | PLA含支撑 |
|---|---:|---:|
'''+ '\n'.join(lines)+'''

作为**工程**打开3MF，保留100%比例、已保存方向及项目参数，选择实际PLA料盘，再在Bambu Studio重新切片检查。下半件竖立并在盘内转45°；上半件倾斜；可拆操作面板单独平放。文件没有预制G-code，也没有发送打印任务。0.08 mm是当前0.4 mm喷嘴配置的最细层高，耗时较长，不等同于±0.08 mm尺寸精度。

## 结构

- 下半主体：280×220×5 mm底板，九种模块底座、电池托架、降压座、喇叭座、四个PCB支柱、电机承托、循迹支架和H41万向轮增高架均一体。原底板拼接片、模块座脚紧固件、电机16 mm厚孔位转接板取消。
- 上半主体：240×190 mm平台、160×150×180 mm筒壁、操作仓、固定传感器底座和超声横梁一体，四角连接件取消。操作面板仍可用原四颗螺钉打开。
- 活动盖、模块压框/锁片、传感器压盖仍可拆。复用已有附件；光敏压条和红外下托压盖采用[sensor-retainers-fix-20261103](../sensor-retainers-fix-20261103/README.md)的修复版，不能用会掉探头的旧直压条。
- STEP零件在step/，ASSEMBLY_REFERENCE.step只用于查看整体装配，不能当成一件打印。源码在source/；重建需要本仓库已有的原始STEP和CAD环境。

![底板布局](preview/layout_dimensions.png)

## 关键配合与强度安排

电机接触核心与用户已试配成功模型逐体比对，差异0 mm³：12×2.4 mm槽、21 mm槽距、3 mm承托厚、1.3 mm轮侧薄边保留；槽中心为(96,14)/(96,206)，接触面Z=−25。新增根部承力筋直接连接底板，去除旧固定耳。所有坐标单位mm，底板底面为Z=0。

B1承托面Z=25，四孔(115,65)/(205,65)/(115,155)/(205,155)。MPU6050位于(253,170)并旋转90°；蜂鸣器(252,65)，喇叭(256,120)，喇叭耳孔(256,96)/(256,144)。MPU安装后重新校准零点，并检查车体前后/左右倾斜报警；若需要车体坐标姿态，按新安装方向调整轴映射。

万向轮孔距40、安装面Z=−41；H41来自原手册66.19的名义61 mm离地高度减20 mm轮高，并非新实测。循迹孔距59.5，安装面Z=−43.4；按用户8 mm探头突出量和暂定1.6 mm板厚，探头名义离地8 mm。装车后检查三轮着地和探头不擦地。

在原浅腔中心减薄到2 mm连续面皮，保留12 mm主筋和孔周厚料，仅此项约去掉14.7 cm³实体；筒壁保留原1.6 mm面皮。下半件5墙/20%螺旋体，上半件4墙/15%，顶底0.8 mm。此为受安装与承力约束的轻量化，尚无载荷试验或有限元证据证明等强或绝对最轻。

## PLA精细参数与检查

层高0.08、首层0.16 mm；外墙/顶面25、内墙50 mm/s，外墙加速度600 mm/s²；喷嘴220℃、纹理PEI床55℃、最大体积速度8 mm³/s。保留基础PLA流量，未无依据更改缩放、孔补偿或Z偏移。

混合自动树形支撑，枝径3 mm、分支角35°、2道支撑壁；上下Z间隙0.16、XY间隙0.35 mm；上接触3层、下接触2层，接触间距0.35 mm；独立支撑层高已启用。两主体6 mm外侧裙边。每件的完整参数、耗时及材料见checks/*_slicing.json。

已经检查实体/网格、关键孔槽、PCB与活动夹具静态空间、平台立柱、面板和实际挤出路径。支撑和裙边的路径均在256 mm床面内。图与切片不代表已实物打印：完整轮胎/桶盖运动、实际排针焊点、线束弯曲、支撑拆除和承载仍需试装；当前环境未运行FreeCAD独立验证。

建模与检查使用[GitHub codex-cad技能](https://github.com/alexanderkoller/codex-cad/blob/main/cad/SKILL.md)的参数、实体、网格、测量和切片流程；支撑含义参考[OrcaSlicer树形支撑文档](https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_tree)，并核对[Bambu Studio实际配置定义](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp)。3MF按项目打印交付需要保留。
'''
(O/'README.md').write_text(readme,encoding='utf8',newline='\n')
nav=B/'README.md';prefix='# 当前一体打印结构 2026-11-04\n\n[PLA两主体一体结构和0.08 mm工程](integrated-pla-20261104/README.md)：P2S、0.4 mm喷嘴、纹理PEI、256×256 mm打印盘；底板和上平台筒壁各一体，操作面板可拆；匹配B1 PCB。历史分片/PETG工程保留归档。\n\n'
if not nav.read_text(encoding='utf8').startswith('# 当前一体打印结构 2026-11-04'):
 nav.write_text(prefix+nav.read_text(encoding='utf8'),encoding='utf8',newline='\n')
attrs=R/'.gitattributes';line='hardware/mechanical/print-backup/integrated-pla-20261104/** -text'
if line not in attrs.read_text(encoding='utf8'):attrs.write_text(attrs.read_text(encoding='utf8')+'\n# Integral PLA artifacts retain exact bytes\n'+line+'\n',encoding='utf8',newline='\n')
step_attr='hardware/mechanical/print-backup/integrated-pla-20261104/step/*.step -diff -merge -text'
if step_attr not in attrs.read_text(encoding='utf8'):attrs.write_text(attrs.read_text(encoding='utf8')+step_attr+'\n',encoding='utf8',newline='\n')
agents=R/'AGENTS.md';marker='## 2026-11-04 PLA一体结构'
if marker not in agents.read_text(encoding='utf8'):
 agents.write_text(agents.read_text(encoding='utf8')+'\n\n'+marker+'\n\n用户最后确认材料仍为PLA，P2S 0.4 mm喷嘴、纹理PEI、256×256 mm。当前两主体工程在hardware/mechanical/print-backup/integrated-pla-20261104/，0.08 mm层高，B1 PCB承托面Z25，H41名义万向轮增高，循迹探头突出8 mm；操作面板仍可拆。见手册第68章和release.json；数字通过不等于实打/承重通过，H41不是实测Hb。\n',encoding='utf8',newline='\n')
artifact=O/'projects/result.json'
if artifact.exists():artifact.unlink()
for p in (O/'source').glob('*.py'):p.write_text(p.read_text(encoding='utf8').rstrip()+'\n',encoding='utf8',newline='\n')
for p in (O/'checks').iterdir():
 if p.suffix in {'.json','.csv'}:p.write_text(p.read_text(encoding='utf8').rstrip()+'\n',encoding='utf8',newline='\n')
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf8').splitlines() if '  ' in l}
files=[p for p in O.rglob('*') if p.is_file()]+[nav,attrs,agents,R/'docs/manual'/name]
for p in files:entries[p.relative_to(R).as_posix()]=sha(p)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf8',newline='\n')
archive=R.parent/'智能垃圾桶_PLA一体结构_高精度008_20261104.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O).as_posix())
 z.write(M/name,name)
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'archive':str(archive),'archive_sha256':sha(archive),'files':records,'manual_sha256':sha(M/name)},ensure_ascii=False,indent=2))
