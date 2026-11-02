"""Publish the reviewed lightweight variant and synchronized same-name manual."""
from pathlib import Path
import argparse,json,hashlib,shutil,zipfile
import xml.etree.ElementTree as E
import numpy as np
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];BASE=B/'motor-existing-holes-20261102';O=B/'motor-existing-holes-light-20261103';W=R.parent/'.p2s-motor-existing-holes-light-20261103/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
parser=argparse.ArgumentParser();parser.add_argument('--checked-pages',required=True);a=parser.parse_args();checked=sorted(map(int,a.checked_pages.split(',')))
audit=load(W/'raster_audit.json');assert checked==audit['changed_pages'];assert audit['same_page_bodies']==239
assert audit['original_steps_preserved']==330 and audit['all_baseline_tables_preserved']==79
assert sha(W/N)==audit['docx_sha256']
targets=[R/'docs/manual'/N,R.parent/N];assert all(sha(p)==audit['baseline_sha256'] for p in targets),'Manual changed concurrently'
d=load(O/'checks/design.json');baseline=load(BASE/'checks/design.json');paths=load(O/'checks/geometry_and_path_review.json');slicing=load(O/'checks/slicing.json');old=load(BASE/'checks/slicing.json');comparison=load(O/'checks/comparison.json')
assert paths['status']=='PASS' and paths['all_paths_in_bed'] and paths['support_moves']==0
assert not slicing['warning_message'] and slicing['native_matches_tested'] and comparison['filament_saved_percent']>0
for key in set(old['process'])|set(slicing['process']):
    if key!='name':assert old['process'].get(key)==slicing['process'].get(key),key
for name,v in d['variants'].items():
    assert v['anchors']==baseline['variants'][name]['anchors'] and v['seat_connection_holes']==baseline['variants'][name]['seat_connection_holes']
    assert v['protected_load_paths_preserved'] and v['lower_5mm_original_material_preserved']
with zipfile.ZipFile(R.parent/'.p2s-motor-existing-holes-light-20261103/CARRIER_PAIR.3mf') as z:
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};root=E.fromstring(z.read('3D/3dmodel.model'))
    for ob,(name,offset) in zip(root.findall('.//m:object',ns),[('LEFT',[12,30,0]),('RIGHT',[115,30,0])]):
        vertices=np.array([[float(p.attrib[k]) for k in ['x','y','z']] for p in ob.findall('.//m:vertex',ns)])
        mesh=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl')
        assert vertices.shape==mesh.vertices.shape and np.max(np.abs(vertices-(mesh.vertices+offset)))<1e-6
with zipfile.ZipFile(O/slicing['project']) as z:assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
for p in targets:shutil.copy2(W/N,p)
audit.update(status='PASS',visually_checked_pages=checked,visual_qa_pending=False,published_copies_match=True,toc_and_page_fields_updated=True)
save(O/'checks/manual_qa.json',audit)
save(O/'checks/visual_review.json',{'status':'PASS','actual_CAD_oblique_views_reviewed':['LEFT','RIGHT'],'four_views_reviewed':['LEFT','RIGHT'],'actual_first_layer_reviewed':True,'pocket_location_sheets_reviewed':['LEFT','RIGHT'],'manual_changed_pages':checked,'physical_strength_tested':False})
p=O/'README.md';t=p.read_text(encoding='utf-8').replace('安装图及浅腔定位将合入同名Word第66.13节，保留原330步骤；最终同步状态见checks/manual_qa.json。上一版厚板文件保留。','安装图及浅腔定位已合入同名Word第66.13节、图解76—78。已更新目录和页码、渲染242页，前239页正文与上一版像素一致，新增3页逐页检查，330个步骤和此前79张表保持。记录见checks/manual_qa.json。上一版厚板文件保留。');p.write_text(t,encoding='utf-8',newline='\n')
nav=B/'README.md';t=nav.read_text(encoding='utf-8');assert 'motor-existing-holes-light-20261103/README.md' not in t
nav.write_text('# 当前电机转接板 保守轻量化版\n\n[两块轻量化转接板与打印工程](motor-existing-holes-light-20261103/README.md)：孔位、16mm安装高度及原穿槽座保持，保留主筋和孔台，新增7处浅腔。同参数切片约136g、9小时41分，比上一版省料7.5%、省时89分钟；承力区保留不等于实物等强验证。\n\n'+t,encoding='utf-8',newline='\n')
assembly=R/'docs/manual/ASSEMBLY.md';t=assembly.read_text(encoding='utf-8');assert '### 66.13' not in t
t+='\n### 66.13 电机转接板保守轻量化\n\n[轻量化打印文件、浅腔定位和检查记录](../../hardware/mechanical/print-backup/motor-existing-holes-light-20261103/README.md)。保持66.12节的9个底板共孔、8个原座连接孔、16mm安装高度、原穿槽座和M3×30/M3×25五金。左板3处、右板4处11mm深上开口浅腔，轻量化区留下5mm底层，孔台和直接承力筋保留全高。原五金避空和原最薄4mm处保持。同参数0.16mm/6墙/60%填充切片，预计147g降至136g，省料7.5%；11小时10分降至9小时41分，省时89分钟。CAD体积减少17.2%，不能当作实际省料比例。未证明与厚板等强，仍需按实际计划载荷逐步加载检查。图解76—78已合入同名Word第66.13节，原330步骤及此前79张表保持。\n'
assembly.write_text(t,encoding='utf-8',newline='\n')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:t+='\n# Ribbed lightweight D06 carrier exports\n'+prefix+'/** -text\n'+prefix+'/*.3mf binary\n'+prefix+'/parts/** binary\n'+prefix+'/step/** binary\n'
attrs.write_text(t,encoding='utf-8',newline='\n')
sources=[B/'source'/f'{name}.py' for name in ['build_motor_carriers_light','slice_motor_carriers_light','review_motor_carriers_light','check_motor_carriers_light_views','render_motor_carriers_light','update_motor_carriers_light_manual','check_motor_carriers_light_manual','finalize_motor_carriers_light']]
normal=sources+[nav,assembly,attrs]
for p in normal:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/release.json',{'status':'PASS_DIGITAL_CHECKS_PHYSICAL_STRENGTH_PENDING','project':slicing['project'],'filament_g':slicing['filament_g'],'estimated_seconds':slicing['estimated_seconds'],'filament_saved_percent':comparison['filament_saved_percent'],'CAD_volume_saved_percent':comparison['CAD_volume_saved_percent'],'time_saved_minutes':comparison['time_saved_minutes'],'new_chassis_holes':0,'shared_existing_holes':9,'interfaces_unchanged':True,'protected_load_paths_preserved':True,'manual_sha256':sha(targets[0]),'manual_visually_checked':True,'printer_jobs_sent':False,'physical_load_tested':False,'equal_strength_to_original_claimed':False})
for p in O.rglob('*'):
    if p.is_file() and p.suffix in ['.md','.csv','.json']:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for p in normal+[targets[0]]+[p for p in O.rglob('*') if p.is_file()]:entries[p.relative_to(R).as_posix()]=sha(p)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
