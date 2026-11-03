"""Publish the checked native print project and synchronized manual without printer dispatch."""
from pathlib import Path
import json,hashlib,shutil,argparse,zipfile
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamps-fine-20261103';W=R.parent/'.p2s-wall-clamps-fine-20261103/manual';N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=argparse.ArgumentParser();p.add_argument('--checked-pages',required=True);args=p.parse_args();checked=sorted(map(int,args.checked_pages.split(',')))
a=load(W/'raster_audit.json');assert a['changed_pages']==checked and a['same_page_bodies']==246 and a['original_steps_preserved']==330 and a['all_baseline_tables_preserved']==79
assert sha(W/N)==a['docx_sha256']
s=load(O/'checks/slicing.json');paths=load(O/'checks/path_review.json');d=load(O/'checks/design.json');assert paths['status']=='PASS_DIGITAL_PRINT_CHECKS' and paths['all_paths_in_bed'] and paths['first_layer_object_count']==8
assert load(O/'checks/native_geometry.json')['status']=='PASS_NATIVE_ROUNDTRIP'
assert s['native_matches_tested'] and not s['warning_message'] and sha(O/s['project'])==s['sha256']
with zipfile.ZipFile(O/s['project']) as z:assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
targets=[R/'docs/manual'/N,R.parent/N];assert all(sha(t)==a['baseline_sha256'] for t in targets),'Manual changed concurrently'
for t in targets:shutil.copy2(W/N,t)
alias=R.parent/'筒壁免钻孔压脚及压垫_P2S_高精度012.3mf';shutil.copy2(O/s['project'],alias);assert sha(alias)==s['sha256']
a.update(status='PASS',visually_checked_pages=checked,toc_and_page_fields_updated=True,published_copies_match=True,visual_qa_pending=False);save(O/'checks/manual_qa.json',a)
save(O/'checks/visual_review.json',{'status':'PASS','actual_CAD_four_views_reviewed':[v['id'] for v in d['variants']],'saved_print_orientation_reviewed':True,'actual_first_layer_reviewed':True,'actual_all_layer_support_reviewed':True,'manual_changed_pages':checked,'physical_print_or_load_tested':False})
save(O/'checks/release.json',{'status':'PRINT_PROJECT_RELEASED_PHYSICAL_FIT_PENDING','project':s['project'],'object_count':8,'layer_height_mm':.12,'mesh_linear_tolerance_mm':.01,'dimensional_accuracy_guarantee':False,'estimated_seconds':s['estimated_seconds'],'filament_g':s['filament_g'],'support':'tree(auto)','manual_section':'66.15','manual_sha256':sha(targets[0]),'new_P02_holes':0,'wall_lift_mm':0,'physical_printed':False,'load_tested':False,'printer_jobs_sent':False})
nav=B/'README.md';t=nav.read_text(encoding='utf-8');assert 'wall-clamps-fine-20261103/README.md' not in t
nav.write_text('# 筒壁免钻孔压脚 高精度打印版\n\n[一盘四只压脚与四只小压垫的P2S工程](wall-clamps-fine-20261103/README.md)：0.12mm层高、6墙、60%填充、树状支撑，预计约3小时20分钟、30.5g。原孔位和筒壁高度保持；打印后仍需清理支撑、试装并逐步加载。\n\n'+t,encoding='utf-8',newline='\n')
assembly=R/'docs/manual/ASSEMBLY.md';t=assembly.read_text(encoding='utf-8');assert '### 66.15' not in t
t+='\n### 66.15 筒壁压脚高精度打印与试装\n\n[打印3MF及清理试装说明](../../hardware/mechanical/print-backup/wall-clamps-fine-20261103/README.md)。本节继续66.14节预览，发布一盘8件的P2S 0.4mm／PLA工程，0.12mm层高、6墙、60%螺旋体、顶底12层、外壁35mm/s，树状支撑及5mm裙边。三只长压脚新增45°斜撑与R0.6外缘，短脚R0.4；原固定孔、压点、2.4mm螺母挡肩保持。预计3小时20分钟、30.5g，8件首层及168层路径检查通过。0.12mm层高和0.01mm网格不代表实物公差保证；打印后清理孔腔、先放底装金属M3螺母，调压螺丝只轻压且头部悬空。固定端三颗M3×16、一颗M3×20的实际长度与立柱深度仍需核对，未做实物承载或抗蠕变验证。图解83—84合入同名Word并更新目录页码，330步骤及此前79张表保持。\n'
assembly.write_text(t,encoding='utf-8',newline='\n')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:t+='\n# Fine-print wall hold-down release exports\n'+prefix+'/** -text\n'+prefix+'/*.3mf binary\n'+prefix+'/step/** binary\n'+prefix+'/parts/** binary\n'
attrs.write_text(t,encoding='utf-8',newline='\n')
sources=[B/'source'/f'{n}.py' for n in ['build_wall_clamps_fine','slice_wall_clamps_fine','review_wall_clamps_fine','check_wall_clamps_native','update_wall_clamps_fine_manual','check_wall_clamps_fine_manual','finalize_wall_clamps_fine']];normal=sources+[nav,assembly,attrs]
for f in normal:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
for f in O.rglob('*'):
    if f.is_file() and f.suffix in ['.md','.json','.csv']:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/SHA256.json',{f.relative_to(O).as_posix():sha(f) for f in sorted(O.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for f in normal+[targets[0]]+[f for f in O.rglob('*') if f.is_file()]:entries[f.relative_to(R).as_posix()]=sha(f)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
ip=R.parent/'codex_readback/arrival_20261019/inventory_status_20261019.json';inv=load(ip);inv['wall_clamps_fine_20261103']={'status':'native_3MF_and_manual_released_physical_fit_pending','directory':prefix,'project':s['project'],'root_copy':str(alias),'object_count':8,'layer_height_mm':.12,'filament_g':s['filament_g'],'estimated_seconds':s['estimated_seconds'],'new_P02_holes':0,'wall_lift_mm':0,'M3x20_stock_unconfirmed':True,'actual_post_depth_unconfirmed':True,'physical_print_or_load_tested':False,'printer_jobs_sent':False,'manual_section':'66.15'};inv['current_task']='筒壁免钻孔压脚高精度3MF已生成并检查；一盘4压脚+4小压垫，P2S/PLA/0.12mm，打印后清理支撑并试装。';save(ip,inv)
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
