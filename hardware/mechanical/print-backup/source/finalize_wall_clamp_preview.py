"""Publish a visually checked concept preview without changing any print release."""
from pathlib import Path
import argparse,json,hashlib,shutil
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamp-preview-20261103';W=R.parent/'.p2s-wall-clamp-preview-20261103/manual'
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
p=argparse.ArgumentParser();p.add_argument('--checked-pages',required=True);args=p.parse_args();checked=sorted(map(int,args.checked_pages.split(',')))
audit=load(W/'raster_audit.json');assert checked==audit['changed_pages'];assert audit['original_steps_preserved']==330 and audit['all_baseline_tables_preserved']==79
assert audit['same_page_bodies']==242 and audit['new_pages']==246
assert sha(W/N)==audit['docx_sha256']
d=load(O/'checks/design.json');g=load(O/'checks/reopened_geometry.json');assert g['status']=='PASS_CONCEPT_GEOMETRY_ONLY'
assert d['new_platform_holes']==0 and d['wall_lift_mm']==0 and not d['print_project_released']
for v in g['parts']:assert v['STEP_sha256']==sha(O/'step'/f"{v['part']}_CONCEPT.step")
targets=[R/'docs/manual'/N,R.parent/N];assert all(sha(t)==audit['baseline_sha256'] for t in targets),'Manual changed concurrently'
for t in targets:shutil.copy2(W/N,t)
audit.update(status='PASS',visually_checked_pages=checked,toc_and_page_fields_updated=True,published_copies_match=True,visual_qa_pending=False)
save(O/'checks/manual_qa.json',audit)
save(O/'checks/visual_review.json',{'status':'PASS_CONCEPT_VISUAL_REVIEW','actual_CAD_overview_reviewed':True,'actual_CAD_regular_clamp_reviewed':True,'actual_CAD_servo_tray_clamp_reviewed':True,'four_views_reviewed':[v['id'] for v in d['clamps']],'anchor_plan_reviewed':True,'manual_changed_pages':checked,'physical_fit_or_load_tested':False,'final_print_project':False})
nav=B/'README.md';t=nav.read_text(encoding='utf-8');assert 'wall-clamp-preview-20261103/README.md' not in t
nav.write_text('# 筒壁免钻孔压脚 方案预览\n\n[四只压脚与现有孔安装关系](wall-clamp-preview-20261103/README.md)：筒壁不垫高，三个立柱孔和一个舵机托片孔固定，从上方轻压原底脚。仅供方案查看，尚未作为最终打印件发布。\n\n'+t,encoding='utf-8',newline='\n')
assembly=R/'docs/manual/ASSEMBLY.md';t=assembly.read_text(encoding='utf-8');assert '### 66.14' not in t
t+='\n### 66.14 筒壁免钻孔压脚转接件方案预览\n\n[概念模型及安装预览](../../hardware/mechanical/print-backup/wall-clamp-preview-20261103/README.md)。P02不新增孔、筒壁不垫高，原160×150×180mm主框位置保持。三只长压脚共用立柱孔，短压脚共用P04孔（70,180）；原后角孔（10,180）保持。底装普通M3螺母，上留2.4mm挡肩，通过M3×8和Ø8×1.2mm小压垫轻压原3.2mm底脚；螺丝头悬空。固定端拟用三颗M3×16及一颗M3×20，长度和立柱盲孔深度待最终打印版核对。完整几何干涉、STEP重读及网格检查通过不等于承载验证。此节为预览，未发布3MF或打印朝向方案，不替换已发布筒壁或电机件。图解79—82合入同名Word，目录和页码更新，保留330步骤和此前79张表。\n'
assembly.write_text(t,encoding='utf-8',newline='\n')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:t+='\n# Concept wall hold-down preview: preserve checked bytes\n'+prefix+'/** -text\n'+prefix+'/step/** binary\n'+prefix+'/qa_meshes/** binary\n'
attrs.write_text(t,encoding='utf-8',newline='\n')
names=['build_wall_clamp_preview','render_wall_clamp_preview','check_wall_clamp_preview','update_wall_clamp_preview_manual','check_wall_clamp_preview_manual','finalize_wall_clamp_preview']
sources=[B/'source'/f'{n}.py' for n in names]
normal=sources+[nav,assembly,attrs]
for f in normal:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/preview_status.json',{'status':'REVIEWABLE_CONCEPT_PREVIEW','new_platform_holes':0,'wall_lift_mm':0,'new_clamps':4,'new_pressure_pads':4,'STEP_reopen_checked':True,'manual_sha256':sha(targets[0]),'manual_section':'66.14','figures':[79,80,81,82],'print_project_released':False,'printer_jobs_sent':False,'physical_fit_tested':False,'load_tested':False})
for f in O.rglob('*'):
    if f.is_file() and f.suffix in ['.md','.json','.csv']:f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/SHA256.json',{f.relative_to(O).as_posix():sha(f) for f in sorted(O.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for f in normal+[targets[0]]+[f for f in O.rglob('*') if f.is_file()]:entries[f.relative_to(R).as_posix()]=sha(f)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())),encoding='utf-8',newline='\n')
inventory=R.parent/'codex_readback/arrival_20261019/inventory_status_20261019.json';inv=load(inventory)
inv['wall_clamp_preview_20261103']={'status':'concept_preview_only_no_print_release','directory':prefix,'manual_section':'66.14','new_platform_holes':0,'wall_lift_mm':0,'anchors':d['anchors_used'],'pressure_points':d['foot_pressure_points'],'M3x20_stock_unconfirmed':True,'physical_fit_or_load_tested':False,'user_printing_report':'User previously said 已打印完毕; no inference that these new clamps have been printed','next_action':'User reviews structure; subsequent print engineering and physical fit remain separate work'}
inv['current_task']='筒壁免钻孔压脚已完成概念预览；四只压脚复用现有孔，P02不钻孔、筒壁不垫高；尚未发布打印版或进行实物验证。'
save(inventory,inv)
print(json.dumps(load(O/'checks/preview_status.json'),ensure_ascii=False))
