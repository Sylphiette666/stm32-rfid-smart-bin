"""Verify unchanged native geometry and publish the 0.16 mm print-profile revision."""
from pathlib import Path
import hashlib,json,zipfile

R=Path(__file__).resolve().parents[4]
B=R/'hardware/mechanical/print-backup'
BASE=B/'wall-panels-20261102'
O=B/'wall-panels-fine-20261102'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def save(p,d):write(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')

slicing=load(O/'checks/slicing.json');paths=load(O/'checks/path_review.json')
allowed={'layer_height','top_shell_layers','bottom_shell_layers','outer_wall_speed','top_surface_speed','support_top_z_distance','support_bottom_z_distance','print_settings_id'}
diffs=[]
for e in slicing['plates']:
 i=e['plate'];new=O/'projects'/e['project'];old=next((BASE/'projects').glob(f'P2S_WALL_{i:02d}_*.3mf'))
 assert sha(new)==e['sha256'] and e['native_matches_tested'] and not e['warning_message']
 with zipfile.ZipFile(old) as x,zipfile.ZipFile(new) as y:
  models=sorted(n for n in x.namelist() if n.endswith('.model'))
  assert models==sorted(n for n in y.namelist() if n.endswith('.model'))
  assert all(x.read(n)==y.read(n) for n in models)
  assert y.testzip() is None
  a=json.loads(x.read('Metadata/project_settings.config'));b=json.loads(y.read('Metadata/project_settings.config'))
  delta={k:{'old':a.get(k),'new':b.get(k)} for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
  assert set(delta)==allowed
  assert b['layer_height']=='0.16' and b['initial_layer_print_height']=='0.2'
  assert b['top_shell_layers']==b['bottom_shell_layers']=='6'
  assert b['wall_loops']=='3' and b['support_type']=='tree(auto)'
  diffs.append({'plate':i,'baseline_project':old.name,'native_geometry_byte_identical':True,'model_sha256':{n:hashlib.sha256(y.read(n)).hexdigest() for n in models},'settings_changes':delta})
 p=paths[str(i)]
 assert p['objects_on_first_layer']==p['expected_objects']==e['objects']
 assert p['all_extrusions_in_bed'] and p['G39_absent']
save(O/'checks/settings_diff.json',diffs)
save(O/'checks/visual_review.json',{'status':'PASS','actual_first_layers_visually_reviewed':[1,2,3,4],'geometry_and_packing_unchanged':True,'physical_print_tested':False})

rows=[]
for e,label in zip(slicing['plates'],['前壁及操作面板','后壁及附件','左壁及附件','右壁及附件']):
 sec=round(e['estimated_seconds']);h,rem=divmod(sec,3600);m,s=divmod(rem,60)
 rows.append(f"| {e['plate']}：{label} | [{e['project']}](projects/{e['project']}) | {h}小时{m}分{s}秒 | {e['filament_g']:.1f} g |")
write(O/'README.md','''# 筒壁精细版：四盘平放，0.16 mm

这是原四盘筒壁的打印参数升级版。四盘全部改为0.16 mm层高；模型尺寸、孔位、附件数量及摆放与原版逐字节一致。使用P2S、0.4 mm喷嘴、PLA和纹理PEI板。

| 盘号 | 打印工程 | 切片预计时间 | PLA |
|---|---|---|---|
'''+ '\n'.join(rows)+'''

四台同时打印，预计最长约9小时24分，总耗材约529.1 g；原普通版最长约7小时20分。实际时间以本机重新切片结果为准。

## 已保存的参数

- 层高0.16 mm；首层0.20 mm。
- 外墙60 mm/s；顶面80 mm/s；内墙150 mm/s。
- 墙层3；15%螺旋体填充；顶底各6层，避免降低层高时壳体随之变薄。
- 外侧裙边2 mm，间隙0.1 mm；需要处自动树状支撑，支撑上下Z间距0.16 mm。
- 树状支撑其余参数沿用原版GitHub来源，见[原始来源记录](../wall-panels-20261102/source/github_support_source.json)。

在Bambu Studio中将3MF作为工程打开，保留项目参数、100%比例及现有摆放，再点击“切片单盘”。这些文件是可编辑工程，未向打印机发送任务。请按实际PLA选择耗材槽位。

本次主要改善层纹和外表面，不代表所有孔径配合误差都会自动消除。装配方法及孔位沿用[原筒壁说明](../wall-panels-20261102/README.md)和同名图解手册66.11节；精细版的打印参数、耗时以本页为准。旧普通版文件保留。

## 校验范围

四个工程的模型及摆放与原版完全相同；原生工程与实测切片使用的模型一致。实际首层15/19/26/4件齐全，所有层的挤出路径在平台内，四张首层检查图已人工查看。checks/settings_diff.json记录全部参数差异。preview内是切片质量核查图，不是新增装配图；本次没有改动Word装配说明。实物打印、元件配合及整机承载尚未由本次参数修改验证。
''')
nav=B/'README.md';t=nav.read_text(encoding='utf-8')
if 'wall-panels-fine-20261102/README.md' not in t:
 write(nav,'# 筒壁精细版：0.16 mm四盘\n\n[新版打印文件及参数](wall-panels-fine-20261102/README.md)：四盘平放，外墙60 mm/s、顶面80 mm/s；四台并行最长约9小时24分，模型与原版一致。\n\n'+t)
doc=R/'docs/manual/ASSEMBLY.md';t=doc.read_text(encoding='utf-8')
if 'wall-panels-fine-20261102/README.md' not in t:
 write(doc,t+'\n筒壁精细打印版本：[四盘0.16 mm工程](../../hardware/mechanical/print-backup/wall-panels-fine-20261102/README.md)。模型及装配沿用66.11节；外墙60 mm/s、顶面80 mm/s，顶底6层，四台并行约9小时24分、529.1 g。此版本打印参数和耗时以新版README为准；上文7小时20分是普通版估算。\n')
attrs=R/'.gitattributes';t=attrs.read_text(encoding='utf-8');prefix=O.relative_to(R).as_posix()
if prefix+'/** -text' not in t:write(attrs,t+'\n# Fine wall print profiles: preserve checked bytes\n'+prefix+'/** -text\n'+prefix+'/projects/*.3mf binary\n')
sources=[B/'source'/n for n in ['slice_wall_panels_fine.py','review_wall_panels_fine.py','finalize_wall_fine_release.py']]
normal=sources+[attrs,nav,doc]
for p in normal+[p for p in O.rglob('*') if p.is_file() and p.suffix in ['.json','.md']]:p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
save(O/'checks/release.json',{'status':'PASS_DIGITAL_CHECKS','project_files':[e['project'] for e in slicing['plates']],'parallel_estimated_seconds':max(e['estimated_seconds'] for e in slicing['plates']),'total_filament_g':sum(e['filament_g'] for e in slicing['plates']),'geometry_unchanged':True,'printer_jobs_sent':False,'physical_print_tested':False,'source_sha256':{p.name:sha(p) for p in sources}})
save(O/'checks/SHA256.json',{p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
manifest=R/'MANIFEST.sha256';entries={l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for p in normal+[p for p in O.rglob('*') if p.is_file()]:entries[p.relative_to(R).as_posix()]=sha(p)
write(manifest,''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())))
print(json.dumps(load(O/'checks/release.json'),ensure_ascii=False))
