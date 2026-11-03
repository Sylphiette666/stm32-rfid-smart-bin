"""Publish verified candidate with an explicit UNMET 24-hour target."""
from pathlib import Path
import json,zipfile,hashlib,shutil,xml.etree.ElementTree as E
import numpy as np
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2];BASE=B/'integrated-pla-20261104'
W=R.parent/'.p2s-integrated-pla-fast-20261104';OLD=R.parent/'.p2s-integrated-pla-20261104';M=R.parent/'codex_readback/integrated_pla_fast_manual_20261104'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
sel=load(O/'checks/selection.json');paths=load(O/'checks/path_review.json');records=[]
def vertices(p):
 with zipfile.ZipFile(p) as z:t=E.fromstring(z.read('3D/3dmodel.model'))
 return np.array([[float(x.attrib[k]) for k in ['x','y','z']] for x in t.findall('.//{*}vertex')]),[tuple(x.attrib[k] for k in ['v1','v2','v3']) for x in t.findall('.//{*}triangle')]
for n,v in sel['variants'].items():
 work=W/v/n;r=load(O/'checks'/f'{v}_{n}_slicing.json');assert r['returncode']==0;p=r['result']['sliced_plates'][0];assert not p['warning_message']
 assert paths[n]['all_extrusions_in_bed'] and paths[n]['maximum_print_z_mm']<=256
 a,fa=vertices(OLD/n/'geometry.3mf');b,fb=vertices(work/'geometry.3mf');assert fa==fb
 if n=='UPPER_INTEGRATED':
  old=np.array(load(BASE/'checks/UPPER_INTEGRATED_orientation.json')['matrix_design_to_print']);new=np.array(load(O/'checks/r4_orientation.json')['matrix_design_to_print'])
  delta=new@np.linalg.inv(old);pred=a@delta[:3,:3].T+delta[:3,3];error=float(np.abs(pred-b).max());assert error<1e-8
 else:error=float(np.abs(a-b).max());assert error==0
 with zipfile.ZipFile(work/'project.3mf') as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
  assert z.testzip() is None and not any(x.endswith('.gcode') for x in z.namelist())
  assert all(z.read(x)==tested.read(x) for x in z.namelist() if x.endswith('.model'))
  c=json.loads(z.read('Metadata/project_settings.config'))
  assert c['filament_type']==['PLA'] and 'P2S' in c['printer_settings_id'] and c['curr_bed_type']=='Textured PEI Plate'
  assert float(c['layer_height'])==float(r['process']['layer_height'])
  if n!='PANEL_COVER':assert c['support_style']=='tree_slim' and c['enable_support']=='1' and paths[n]['support_extrusion_moves']>0
 dest=O/'projects'/f'P2S_{n}_PLA_FAST_CANDIDATE.3mf';shutil.copy2(work/'project.3mf',dest)
 records.append({'part':n,'variant':v,'project':dest.relative_to(O).as_posix(),'project_sha256':sha(dest),'estimated_seconds':p['total_predication'],
 'grams':sum(x['total_used_g'] for x in p['filaments']),'max_vertex_error_after_rigid_transform_mm':error,'source_step_sha256':sha(BASE/'step'/f'{n}.step'),'scale':1,'layer_height_mm':float(c['layer_height'])})
total=sum(x['estimated_seconds'] for x in records);assert total>86400
save(O/'checks/release.json',{'status':'CANDIDATE_CHECKED_24H_TARGET_NOT_MET','target_seconds':86400,'estimated_total_seconds':total,
 'estimated_total_grams':sum(x['grams'] for x in records),'files':records,'physical_print_tested':False,'print_job_sent':False,
 'manual_chapter':69,'slicer':'Bambu Studio 02.08.02.61','nozzle_mm':.4,'material':'Generic PLA','max_volumetric_speed_mm3_s':12,
 'limitations':['24 hours unmet for total AND for upper part','0.28 mm reduces surface finish relative to 0.08 mm','physical adhesion, strength and support removal untested'],
 'log_review':['Final sliced plate warning fields empty','Voronoi automatic input rotation warning occurred for upper; completed slice and full path bounds verified','T65535 analyzer message is from unchanged official P2S machine_end_gcode AMS unloading block; no manufacturing G-code shipped']})
qa=load(M/'qa.json');name='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';assert sha(M/name)==qa['docx_sha256']
for dst in [R/'docs/manual'/name,R.parent/name]:assert sha(dst) in {qa['baseline_sha256'],qa['docx_sha256']},'Concurrent manual modification'
for dst in [R/'docs/manual'/name,R.parent/name]:shutil.copy2(M/name,dst)
save(O/'checks/manual_qa.json',qa);save(O/'checks/word_render.json',load(M/'word-render.json'))
table=['|打印件|预计时间|PLA含支撑|','|---|---:|---:|']
labels={'LOWER_H41_B1':'下半主体','UPPER_INTEGRATED':'上半主体','PANEL_COVER':'面板盖'}
for x in records:
 t=int(x['estimated_seconds']);table.append(f"|[{labels[x['part']]}]({x['project']})|{t//3600}小时{t%3600//60}分|{x['grams']:.1f} g|")
readme='''# PLA树形支撑加速候选

**24小时目标尚未达到。** 三件合计约47小时42分，上半件单件约33小时。此次提供可检查的候选，不称为24H成品方案。

'''+ '\n'.join(table)+'''

仍为P2S、0.4 mm喷嘴、纹理PEI、256×256 mm、PLA。两个主体0.28 mm层高，面板盖0.20 mm；三墙、主体10%螺旋体，顶底不低于0.8 mm。外墙120、内墙230 mm/s；实际受官方Generic PLA的12 mm³/s体积流量和悬垂限速约束。未假定未知PLA能支持更高流量。

树形为自动细树形，枝径3、分支间距5、分支角40°、阈值35°、一道支撑壁；支撑与模型同步层高，上下Z间隙0.28、XY间隙0.35 mm，接触上下各两层、间距0.5 mm，主体6 mm裙边。面板盖平放无需支撑。

![下半件实际支撑](preview/LOWER_H41_B1_supports.png)
![上半件实际支撑](preview/UPPER_INTEGRATED_supports.png)

棕色图形抽取实际刀路每3层中的1层显示。支撑已真实生成并检查完整床面范围。作为工程打开projects/内3MF，保持100%比例和已保存方向后重新切片；文件包含模型和参数，不含机器G-code，也没有启动打印。

原CAD模型与安装孔槽未改变，仅刚性旋转、平移上半件。STEP仍使用[上一版模型](../integrated-pla-20261104/README.md)。本版降低层精细度和墙数，不能声称与0.08 mm版本表面质量或强度相同；实打、载荷和拆支撑尚未验证。当前最快候选也不代表数学上已证明不存在更快姿态。

各轮结果保留在checks/*_slicing.json，选用下半件r3、上半件r4和面板r1；r5有机树形、r6混合树形实测没有更快。默认流量下继续实现24小时，需要明确是否允许结构/分件改变，或提供实际耗材流量标定数据。

手册第69章已合入所有新支撑图和首层图。检查参考[GitHub codex-cad](https://github.com/alexanderkoller/codex-cad/blob/main/cad/SKILL.md)、[OrcaSlicer树形支撑参数](https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_tree)。本机为Bambu Studio 02.08.02.61。
'''
(O/'README.md').write_text(readme,encoding='utf8',newline='\n')
nav=B/'README.md';prefix='# 2026-11-04 树形支撑加速候选\n\n[快速打印检查](integrated-pla-fast-20261104/README.md)：整套约47小时42分，24小时目标尚未达到；主体0.28 mm，原模型孔位不变。0.08 mm方案继续保留。\n\n'
if not nav.read_text(encoding='utf8').startswith(prefix):nav.write_text(prefix+nav.read_text(encoding='utf8'),encoding='utf8',newline='\n')
attrs=R/'.gitattributes';line='hardware/mechanical/print-backup/integrated-pla-fast-20261104/** -text'
if line not in attrs.read_text():attrs.write_text(attrs.read_text()+'\n'+line+'\n',encoding='utf8',newline='\n')
agents=R/'AGENTS.md';marker='## 2026-11-04 树形支撑加速候选'
if marker not in agents.read_text(encoding='utf8'):agents.write_text(agents.read_text(encoding='utf8')+'\n\n'+marker+'\n\n用户要求24H以内，当前多轮实际切片最快候选仍为整套47小时42分，上半件32小时58分，目标未达。候选在integrated-pla-fast-20261104，手册第69章；不能称24H达标版。材料/喷嘴保持PLA与0.4，主体0.28 mm层高，支撑已生成及路径检查，实际强度未验。是否允许分件调整或经过标定的更高PLA流量仍待明确。\n',encoding='utf8',newline='\n')
for p in O.rglob('*'):
 if p.is_file() and p.suffix in {'.json','.py','.md'}:p.write_text(p.read_text(encoding='utf8').rstrip()+'\n',encoding='utf8',newline='\n')
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
mf=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in mf.read_text(encoding='utf8').splitlines() if '  'in l}
for p in [x for x in O.rglob('*') if x.is_file()]+[nav,attrs,agents,R/'docs/manual'/name]:entries[p.relative_to(R).as_posix()]=sha(p)
mf.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf8',newline='\n')
archive=R.parent/'智能垃圾桶_PLA树形支撑_加速候选_未达24H_20261104.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O).as_posix())
 z.write(M/name,name)
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'archive':str(archive),'estimated_hours':total/3600,'target_met':False,'sha256':sha(archive)},ensure_ascii=False))
