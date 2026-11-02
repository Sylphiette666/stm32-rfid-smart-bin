"""Publish the reviewed four-plate CAD package and hash-guarded manual."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
R=Path(__file__).resolve().parents[4];B=R/'hardware/mechanical/print-backup';O=B/'wall-panels-20261102';W=R.parent/'.p2s-wall-panels-20261102/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
a=argparse.ArgumentParser();a.add_argument('--checked-pages',required=True);args=a.parse_args()
checked=[int(n) for n in args.checked_pages.split(',')]
audit=load(W/'raster_audit.json');assert sorted(checked)==audit['changed_pages']
assert audit['original_steps_preserved']==330 and audit['original_tables_preserved']==78
assert sha(W/N)==audit['docx_sha256']
targets=[R/'docs/manual'/N,R.parent/N]
assert all(sha(p) in [audit['baseline_sha256'],audit['docx_sha256']] for p in targets),'Published manual changed concurrently'
d=load(O/'checks/design.json');assert d['all_walls_flat'] and len(d['parts'])==33
assert sum(len(x) for x in d['plates'].values())==64
assert all(x['watertight'] and x['solid_count']==1 for x in d['parts'].values())
assembly=load(O/'checks/assembly_audit.json');assert assembly['status']=='PASS_GEOMETRY_ONLY' and not assembly['collisions']
assert assembly['bare_floor_void_mm3']<1e-5
holes=load(O/'checks/hole_positions.json');assert len(holes)==85 and all(x['centreline_void'] for x in holes)
assert load(O/'checks/platform_mounts.json')['status']=='PASS_GEOMETRY_ONLY'
slice_report=load(O/'checks/slicing.json');assert slice_report['status']=='PASS' and len(slice_report['plates'])==4
paths=load(O/'checks/path_review.json')
for entry in slice_report['plates']:
 assert entry['native_matches_tested'] and not entry['warning_message']
 f=O/'projects'/entry['project'];assert sha(f)==entry['sha256']
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
  c=json.loads(z.read('Metadata/project_settings.config'))
  assert c['wall_loops']=='3' and c['support_type']=='tree(auto)' and c['enable_support']=='1'
  assert c['layer_height']==('0.2' if entry['plate']==1 else '0.24')
 p=paths[str(entry['plate'])]
 assert p['objects_on_first_layer']==p['expected_objects']==entry['objects']
 assert p['all_extrusions_in_bed'] and p['G39_absent']
for t in targets:shutil.copy2(W/N,t)
audit.update(visual_qa_pending=False,visually_checked_pages=checked,published_copies_match=True,status='PASS',toc_scope='Existing Heading 1 only TOC preserved and updated; 66.11 is a Heading 2 subsection.')
save(O/'checks/manual_qa.json',audit)
save(O/'checks/visual_review.json',{'status':'PASS','plates_and_actual_first_layers':[1,2,3,4],'assembly_front_rear_cutaway_reviewed':True,'instruction_and_five_coordinate_sheets_reviewed':True,'manual_changed_pages':checked,'physical_print_or_load_test':False})
p=O/'README.md';t=p.read_text(encoding='utf-8').replace('安装图和孔位图将同步同名Word手册66.11节；完成状态见checks/manual_qa.json。','安装图和孔位图已同步同名Word手册66.11节、图解65—70。原330步骤和78张表保留；234页已渲染，新8页已逐页检查，前226页正文像素与旧版一致。记录见checks/manual_qa.json。');p.write_text(t,encoding='utf-8')
nav=B/'README.md';t=nav.read_text(encoding='utf-8')
if 'wall-panels-20261102/README.md' not in t:t='# 四块平放筒壁与元件安装件\n\n[四盘打印文件及装配说明](wall-panels-20261102/README.md)：前、后、左、右壁各自一体平放，含可拆元件夹座。正常质量、需要处自动树状支撑，四台并行最长约7小时20分；实物配合与开盖行程需首次试装。\n\n'+t
if 'motor-adapter-clearance2-20261102/README.md' not in t:t='# 轮子侧再次减薄的电机座试配版\n\n[左右两件快速试配](motor-adapter-clearance2-20261102/README.md)：轮子侧槽外壁3.3→1.3mm，仅用于尺寸试配，两件约31分34秒。\n\n'+t
nav.write_text(t,encoding='utf-8')
assemblydoc=R/'docs/manual/ASSEMBLY.md';t=assemblydoc.read_text(encoding='utf-8')
if '### 66.11' not in t:t+='\n### 66.11 四块平放筒壁与元件安装\n\n[四盘打印文件、元件位置、螺丝清单和装配顺序](../../hardware/mechanical/print-backup/wall-panels-20261102/README.md)。四壁分别一体平放，正常质量。前操作面板集成OLED、编码器、MODE/BACK、RC522和急停；另有开盖红外托架、对射夹座、DHT11裸探头通风座、光敏夹座、KCD1盒、超声横梁、闭盖开关可调片、LED片、线夹与角码。原P02连续面朝上作裸桶底，不加内胆、不套袋，不防水。平台候选孔须实物试摆后钻；活动盖/连杆全行程和电子件实际插线空间仍需核对。四台并行最长约7小时20分、总耗材约512g。图解65—70及孔位坐标已合入同名Word，原330步骤保留。\n'
assemblydoc.write_text(t,encoding='utf-8')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8')
for folder in [O,B/'motor-adapter-clearance2-20261102']:
 prefix=folder.relative_to(R).as_posix()
 if prefix+'/** -text' not in t:t+='\n# Checked CAD exports\n'+prefix+'/** -text\n'+prefix+'/**/*.3mf binary\n'+prefix+'/*.3mf binary\n'+prefix+'/parts/** binary\n'+prefix+'/step/** binary\n'
attrs.write_text(t,encoding='utf-8')
sources=[B/'source'/f'{n}.py' for n in ['build_wall_panels','wall_sensor_interfaces','slice_wall_panels','review_wall_panels','audit_wall_interfaces','document_wall_interfaces','update_wall_metadata','update_wall_manual','check_wall_manual','check_wall_platform','finalize_wall_release']]
normal=sources+[attrs,nav,assemblydoc]
for p in normal:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/release.json',{'status':'PASS_DIGITAL_CHECKS_FIRST_ARTICLE','project_files':[e['project'] for e in slice_report['plates']],'parallel_estimated_seconds':max(e['estimated_seconds'] for e in slice_report['plates']),'total_filament_g':sum(e['filament_g'] for e in slice_report['plates']),'manual_sha256':sha(targets[0]),'manual_visually_checked':True,'physical_fit_verified':False,'physical_load_tested':False,'printer_jobs_sent':False,'cad_source_sha256':{p.name:sha(p) for p in sources}})
for p in O.rglob('*'):
 if p.is_file() and p.suffix in ['.md','.json','.csv']:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='SHA256.json')
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in files})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for p in normal+[targets[0]]+[p for p in O.rglob('*') if p.is_file()]:entries[p.relative_to(R).as_posix()]=sha(p)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
