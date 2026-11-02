"""Publish only the reviewed mechanical change and matching manual, with concurrency guards."""
from pathlib import Path
import argparse,json,hashlib,shutil,zipfile,csv
import numpy as np
import xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-existing-holes-20261102';W=R.parent/'.p2s-motor-existing-holes-20261102/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
arg=argparse.ArgumentParser();arg.add_argument('--checked-pages',required=True);a=arg.parse_args()
checked=sorted(map(int,a.checked_pages.split(',')));audit=load(W/'raster_audit.json');assert checked==audit['changed_pages']
assert audit['original_steps_preserved']==330 and audit['original_tables_preserved']==78 and audit['all_pages_rasterized']
assert sha(W/N)==audit['docx_sha256']
targets=[R/'docs/manual'/N,R.parent/N];assert all(sha(t)==audit['baseline_sha256'] for t in targets),'Manual changed concurrently'
design=load(O/'checks/design.json');paths=load(O/'checks/geometry_and_path_review.json');slicing=load(O/'checks/slicing.json')
assert design['new_chassis_holes']==0 and design['shared_existing_holes']==9
assert paths['status']=='PASS' and paths['all_paths_in_bed'] and paths['support_moves']==0
assert slicing['status']=='PASS' and not slicing['warning_message'] and slicing['native_matches_tested']
# Re-exported meshes and the tested/native project's embedded meshes must still match point-for-point.
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
with zipfile.ZipFile(R.parent/'.p2s-motor-existing-holes-20261102/CARRIER_PAIR.3mf') as z:
    root=E.fromstring(z.read('3D/3dmodel.model'))
    objects=root.findall('.//m:object',ns)
    for obj,(name,offset) in zip(objects,[('LEFT',[12,30,0]),('RIGHT',[115,30,0])]):
        verts=np.array([[float(v.attrib[k]) for k in ['x','y','z']] for v in obj.findall('.//m:vertex',ns)])
        mesh=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl')
        assert verts.shape==mesh.vertices.shape and np.max(np.abs(verts-(mesh.vertices+offset)))<1e-6
with zipfile.ZipFile(O/slicing['project']) as z:
    assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())

for target in targets:shutil.copy2(W/N,target)
audit.update(status='PASS',visually_checked_pages=checked,visual_qa_pending=False,published_copies_match=True,toc_and_page_fields_updated=True)
save(O/'checks/manual_qa.json',audit)
save(O/'checks/visual_review.json',{'status':'PASS','layout_and_stack_and_sections_reviewed':True,'coordinate_pages_reviewed':['LEFT','RIGHT'],'four_views_reviewed':['LEFT','RIGHT'],'actual_first_layer_reviewed':True,'physical_load_tested':False})
p=O/'README.md';t=p.read_text(encoding='utf-8').replace('安装图和接口坐标将同步同名Word第66.12节，保留原330个步骤。最终同步状态见checks/manual_qa.json。','安装图和接口坐标已同步同名Word第66.12节、图解71—75。更新目录和页码后渲染239页，233页正文与已检查基线一致，6个变化页已逐页检查，原330步骤及78张表保留。记录见checks/manual_qa.json。')
t+='\nSTEP装配文件保持原底板XY坐标，并以底板下表面Z=0为基准：新板Z=−16～0，原座Z=−25～−16mm。打印STL已独立归零并保留正确平放方向，不把装配STEP直接当作摆盘工程。\n'
p.write_text(t,encoding='utf-8',newline='\n')
nav=B/'README.md';t=nav.read_text(encoding='utf-8')
entry='# 当前电机固定方案 复用底板现有孔\n\n[两块16mm厚转接板与安装说明](motor-existing-holes-20261102/README.md)：不新增底板孔，原已试配穿槽座继续用；共用9个现有孔，电机下移16mm。两块同盘约11小时10分、147g，0.16mm层高、6墙、60%填充。原直装钻孔方案作为历史记录。\n\n'
assert 'motor-existing-holes-20261102/README.md' not in t;nav.write_text(entry+t,encoding='utf-8',newline='\n')
assembly=R/'docs/manual/ASSEMBLY.md';t=assembly.read_text(encoding='utf-8');assert '### 66.12' not in t
t+='\n### 66.12 电机转接板复用底板现有孔\n\n[现有孔转接板打印文件、孔位和安装顺序](../../hardware/mechanical/print-backup/motor-existing-holes-20261102/README.md)。本节取代66.10节的另钻底板孔方案，原已试配穿槽座继续用，补打两块16mm厚板。LEFT共用1117座2孔、蜂鸣器座2孔、STM32座1孔；RIGHT共用靠舵机侧拼接片2孔、MPU6050座1孔、降压托架1孔。底板不增加孔，模块位置及原穿槽XY基准不变，电机下移16mm。共孔换9颗M3×30，原座用8颗M3×25接新板；配17颗4mm高锁母和34片小平垫，按已有可用库存复用。原T形片先穿入再连接新板，预埋螺丝端不能顶出贴合面。已复核孔位、拼接和五金避让、封闭网格及切片路径，尚无实物承载或额定载重结论。万向球垫高按实装Hb−20mm另定。图解71—75已同步同名Word，原330步骤保留。\n'
assembly.write_text(t,encoding='utf-8',newline='\n')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:t+='\n# Existing-hole D06 carriers checked exports\n'+prefix+'/** -text\n'+prefix+'/*.3mf binary\n'+prefix+'/parts/** binary\n'+prefix+'/step/** binary\n'
attrs.write_text(t,encoding='utf-8',newline='\n')
sources=[B/'source'/f'{n}.py' for n in ['build_motor_existing_holes','slice_motor_existing_holes','render_motor_existing_holes','review_motor_existing_holes','check_motor_existing_holes_views','update_motor_existing_holes_manual','check_motor_existing_holes_manual','finalize_motor_existing_holes']]
normal=sources+[nav,assembly,attrs]
for p in normal:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/release.json',{'status':'PASS_DIGITAL_CHECKS_FIRST_ARTICLE_PENDING','project':slicing['project'],'estimated_seconds':slicing['estimated_seconds'],'filament_g':slicing['filament_g'],'new_chassis_holes':0,'shared_existing_holes':9,'additional_motor_drop_mm':16,'original_motor_seats_reused':True,'manual_sha256':sha(targets[0]),'manual_visually_checked':True,'original_steps_preserved':330,'physical_load_tested':False,'rated_payload_kg':None,'printer_jobs_sent':False})
for p in O.rglob('*'):
    if p.is_file() and p.suffix in ['.md','.json','.csv']:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256.json');save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in files})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for p in normal+[targets[0]]+[p for p in O.rglob('*') if p.is_file()]:entries[p.relative_to(R).as_posix()]=sha(p)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
