"""Publish checked old-seat repairs, with historical-project notices and synchronized manual."""
from pathlib import Path
import argparse,json,hashlib,shutil,zipfile
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'sensor-retainers-fix-20261103';W=R.parent/'.p2s-sensor-retainers-fix-20261103/manual';N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=argparse.ArgumentParser();p.add_argument('--checked-pages',required=True);args=p.parse_args();checked=sorted(map(int,args.checked_pages.split(',')))
a=load(W/'raster_audit.json');assert a['changed_pages']==checked and a['same_page_bodies']==248 and a['original_steps_preserved']==330 and a['all_baseline_tables_preserved']==79
assert sha(W/N)==a['docx_sha256']
s=load(O/'checks/slicing.json');paths=load(O/'checks/path_review.json');d=load(O/'checks/design.json');g=load(O/'checks/native_geometry.json')
assert paths['status']=='PASS_ALL_LAYER_PATHS' and paths['all_paths_in_bed'] and paths['first_layer_objects']==4 and paths['support_moves']==0 and g['all_objects_verified']==4
assert not s['warning_message'] and s['native_matches_tested'] and sha(O/s['project'])==s['sha256']
with zipfile.ZipFile(O/s['project']) as z:assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
targets=[R/'docs/manual'/N,R.parent/N];assert all(sha(t)==a['baseline_sha256'] for t in targets),'Manual changed concurrently'
for t in targets:shutil.copy2(W/N,t)
alias=R.parent/'光敏压条与红外下托压盖_旧底座修复_P2S_012.3mf';shutil.copy2(O/s['project'],alias);assert sha(alias)==s['sha256']
a.update(status='PASS',visually_checked_pages=checked,toc_and_page_fields_updated=True,published_copies_match=True,visual_qa_pending=False);save(O/'checks/manual_qa.json',a)
save(O/'checks/visual_review.json',{'status':'PASS','old_seat_assembly_previews_reviewed':['LIGHT_CRADLE','BEAM_SEAT'],'replacement_four_views_reviewed':['LIGHT_BAR_V2','BEAM_CUP_V2'],'actual_first_layer_reviewed':True,'manual_pages_reviewed':checked,'physical_trial_fit':False})
save(O/'checks/release.json',{'status':'REPLACEMENT_PRINT_PROJECT_RELEASED_PHYSICAL_FIT_PENDING','project':s['project'],'objects':4,'retained_original_seats':True,'old_light_pitch_nominal_mm':36,'old_beam_pitch_mm':22,'actual_old_print_not_remeasured':True,'light_adjustable_hole_pitch_ideal_mm':[29.4,42.6],'beam_lower_shoulders_added':True,'open_wire_gap_mm':8,'estimated_seconds':s['estimated_seconds'],'filament_g':s['filament_g'],'layer_height_mm':.12,'manual_section':'66.16','manual_sha256':sha(targets[0]),'printer_jobs_sent':False,'physical_trial_fit':False})
nav=B/'README.md';t=nav.read_text(encoding='utf-8');assert 'sensor-retainers-fix-20261103/README.md' not in t
nav.write_text('# 已打印旧底座的附件修复\n\n[光敏可调L压条和红外对射IR下托压盖](sensor-retainers-fix-20261103/README.md)：只重打两根压条与两个压盖，旧底座和筒壁保持；P2S/PLA/0.12mm，一盘约41分钟、3.6g。实物装配待试装确认。\n\n'+t,encoding='utf-8',newline='\n')
assembly=R/'docs/manual/ASSEMBLY.md';t=assembly.read_text(encoding='utf-8');assert '### 66.16' not in t
t+='\n### 66.16 光敏压条与对射压盖的旧底座修复\n\n[四件附件修复3MF及安装说明](../../hardware/mechanical/print-backup/sensor-retainers-fix-20261103/README.md)。保留已打印LIGHT_CRADLE、BEAM_SEAT与筒壁；L压条改50mm长、双10×3.4mm调节槽，名义孔距仍36mm，理论覆盖29.4～42.6mm，0.3mm内侧台阶朝PCB边，上条转180°。旧实物未重测，不认定失配具体原因。IR压盖保留22mm孔距，补两只下托肩和8mm开放线槽，修正旧夹座没有下托的遗漏。名义外壳下移与外移止挡、光学通道及旧座干涉检查通过，实际模块和线束待试装。四件一盘P2S/PLA/0.12mm，无支撑，约41分钟/3.6g；94层路径及原生模型还原通过。按M3×20光敏/M3×25对射、普通螺母和平垫估算，实际露牙需核对。图解85—86合入同名Word第66.16节，330步骤及此前79张表保持。\n';assembly.write_text(t,encoding='utf-8',newline='\n')
history=[]
for folder in ['wall-panels-20261102','wall-panels-fine-20261102']:
    rd=B/folder/'README.md';t=rd.read_text(encoding='utf-8');assert 'sensor-retainers-fix-20261103/README.md' not in t
    notice='> 2026-11-03附件修复：光敏旧底座继续用，改装可调L压条；红外对射旧夹座继续用，直压条改为带下托的IR压盖。[只需重打四件的修复工程](../sensor-retainers-fix-20261103/README.md)。本目录整盘文件保留历史；新打印这两类附件采用修复工程，其他零件保持。\n\n'
    rd.write_text(notice+t,encoding='utf-8',newline='\n');hp=B/folder/'checks/SHA256.json';h=load(hp)
    if 'README.md' in h:h['README.md']=sha(rd)
    save(hp,h);history += [rd,hp]
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:t+='\n# Previously printed sensor-seat retainer repairs\n'+prefix+'/** -text\n'+prefix+'/*.3mf binary\n'+prefix+'/step/** binary\n'+prefix+'/parts/** binary\n'
attrs.write_text(t,encoding='utf-8',newline='\n')
sources=[B/'source'/f'{n}.py' for n in ['build_sensor_retainer_fix','slice_sensor_retainer_fix','review_sensor_retainer_fix','check_sensor_retainer_native','update_sensor_retainer_manual','check_sensor_retainer_manual','finalize_sensor_retainer_fix']];normal=sources+[nav,assembly,attrs]+history
for f in normal:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
for f in O.rglob('*'):
    if f.is_file() and f.suffix in ['.md','.json','.csv']:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/SHA256.json',{f.relative_to(O).as_posix():sha(f) for f in sorted(O.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for f in normal+[targets[0]]+[f for f in O.rglob('*') if f.is_file()]:entries[f.relative_to(R).as_posix()]=sha(f)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
ip=R.parent/'codex_readback/arrival_20261019/inventory_status_20261019.json';inv=load(ip);inv['sensor_retainer_fix_20261103']={'status':'replacement_four_piece_3MF_released_physical_fit_pending','old_base_previously_printed_user_confirmed':True,'directory':prefix,'project':s['project'],'root_copy':str(alias),'replacement_parts':{'LIGHT_BAR_V2':2,'BEAM_CUP_V2':2},'old_seat_nominal_pitch_LIGHT':36,'old_seat_actual_pitch_not_remeasured':True,'old_walls_and_seats_retained':True,'open_wire_gap_mm':8,'manual_section':'66.16','new_parts_printed_or_fitted':False,'printer_jobs_sent':False};inv['current_task']='旧底座附件修复：保留光敏与对射旧座，重打2根可调L条和2个IR下托压盖；0.12mm无支撑3MF已检查，实物待试装。';save(ip,inv)
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
