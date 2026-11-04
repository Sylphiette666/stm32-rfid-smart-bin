"""Record the user's per-body time target and selected unchanged-structure fallback."""
from pathlib import Path
import sys,json,hashlib,shutil,zipfile
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2]
W=R.parent/'codex_readback/integrated_pla_fast_confirmed_20261104';W.mkdir(exist_ok=True)
NAME='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
intro='用户已明确24小时指每个主体，并选择保持当前结构和PLA材料，交付最快已检查设置。现有切片中，下半主体约13小时41分，达到单件24小时目标；上半主体约32小时58分，仍未达到。按用户选择保留当前两主体结构并交付本章方案，不将它标为全部达标。'
ending='本次交付按用户确认保留现有结构和PLA材料，采用已测试候选中最快的组合；不再以整套合计24小时作为验收条件，也不擅自重新分件或提高未标定的材料流量。上半主体超出单件24小时的结果如实保留。实物强度、层间结合、打印成功率和支撑拆除尚未验证。'
if sys.argv[1]=='stage':
 from docx import Document
 src=R/'docs/manual'/NAME;baseline=W/'before.docx'
 if not baseline.exists():shutil.copy2(src,baseline)
 assert sha(src)==sha(baseline),'Concurrent manual change'
 d=Document(baseline);changed=[]
 for p in d.paragraphs:
  if p.text.startswith('本章响应用户将打印时间缩短到24小时以内的要求。'):changed.append(p.text);p.text=intro
  if p.text.startswith('若24小时为硬性总时限，'):changed.append(p.text);p.text=ending
 assert len(changed)==2
 d.save(W/NAME);save(W/'edit-audit.json',{'table_changes':[],'changed_paragraphs_before':changed,'baseline_sha256':sha(baseline)})
 print(W/NAME);sys.exit(0)
assert sys.argv[1]=='publish'
qa=load(W/'qa.json');assert qa['status']=='STRUCTURAL_CHECKS_PASS' and sha(W/NAME)==qa['docx_sha256']
for dst in [R/'docs/manual'/NAME,R.parent/NAME]:assert sha(dst) in {qa['baseline_sha256'],qa['docx_sha256']}
r=load(O/'checks/release.json')
for f in r['files']:assert sha(O/f['project'])==f['project_sha256'],'Printing project changed'
r.update({'status':'SELECTED_BEST_TESTED_SETTINGS_UPPER_24H_UNMET','target_scope':'each principal body, not total',
 'user_fallback_selection':'保持当前结构和材料，交付最快可靠设置','user_clarification':'每个主体不超过24小时',
 'time_target_met_by_principal_body':{f['part']:f['estimated_seconds']<=86400 for f in r['files'] if f['part']!='PANEL_COVER'}})
r['limitations'][0]='Upper body exceeds per-body 24-hour target; user selected the fastest checked settings while preserving structure and material'
save(O/'checks/release.json',r)
s=load(O/'checks/selection.json');s.pop('target_total_hours',None);s.update({'status':r['status'],'target_per_principal_body_hours':24,'user_fallback_selection':r['user_fallback_selection']});save(O/'checks/selection.json',s)
save(O/'checks/user_decision.json',{'date':'2026-11-04','time_target':'每个主体不超过24小时','priority':'保持当前结构和材料，交付最快可靠设置','preserve_two_integral_bodies':True,'material':'PLA','rerun_slicing_required':False,'reason':'printing projects unchanged; user clarified target scope and accepted retaining structure/material'})
p=O/'README.md';t=p.read_text(encoding='utf8')
t=t.replace('**24小时目标尚未达到。** 三件合计约47小时42分，上半件单件约33小时。此次提供可检查的候选，不称为24H成品方案。','**已按用户选择交付保持结构和PLA材料的最快已检查方案。** 24小时按每个主体计算：下半件约13小时41分，达标；上半件约32小时58分，仍未达标。用户选择保留当前结构与材料，不重新分件。整套约47小时42分仅供排期参考。')
t=t.replace('默认流量下继续实现24小时，需要明确是否允许结构/分件改变，或提供实际耗材流量标定数据。','用户已选择保持当前结构和材料，采用上述最快已检查组合；上半件超时如实记录。这里的已检查指数字切片及刀路检查，不代表实物可靠性已经验证。')
p.write_text(t,encoding='utf8',newline='\n')
nav=B/'README.md';t=nav.read_text(encoding='utf8').replace('整套约47小时42分，24小时目标尚未达到；主体0.28 mm，原模型孔位不变。','用户确认24小时按单件；已选择保留结构和PLA交付最快候选，下半件约13小时41分，上半件约32小时58分仍超时；主体0.28 mm，原模型孔位不变。');nav.write_text(t,encoding='utf8',newline='\n')
agents=R/'AGENTS.md';t=agents.read_text(encoding='utf8').replace('是否允许分件调整或经过标定的更高PLA流量仍待明确。','用户后续已明确24H为每个主体，并选择“保持当前结构和材料，交付最快可靠设置”。按此交付当前最快已检查方案，保持两主体与PLA，不再询问分件/材料更改；下半件达单件24H，上半件仍超时，不得声称全部达标或已经实物可靠性验证。');agents.write_text(t,encoding='utf8',newline='\n')
for dst in [R/'docs/manual'/NAME,R.parent/NAME]:shutil.copy2(W/NAME,dst)
save(O/'checks/manual_qa.json',qa);save(O/'checks/word_render.json',load(W/'word-render.json'))
for p in (O/'source').glob('*.py'):p.write_text(p.read_text(encoding='utf8').rstrip()+'\n',encoding='utf8',newline='\n')
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
mf=R/'MANIFEST.sha256';e={l.split('  ',1)[1]:l.split('  ',1)[0] for l in mf.read_text(encoding='utf8').splitlines() if '  ' in l}
for p in [x for x in O.rglob('*') if x.is_file()]+[nav,agents,R/'docs/manual'/NAME]:e[p.relative_to(R).as_posix()]=sha(p)
mf.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(e.items())),encoding='utf8',newline='\n')
archive=R.parent/'智能垃圾桶_PLA树形支撑_保留结构最快候选_20261104.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(O).as_posix())
 z.write(W/NAME,NAME)
assert zipfile.ZipFile(archive).testzip() is None
print(json.dumps({'archive':str(archive),'sha256':sha(archive),'printing_projects_unchanged':True},ensure_ascii=False))
