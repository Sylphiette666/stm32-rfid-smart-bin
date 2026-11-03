"""P2S native projects for three caster drop heights."""
from pathlib import Path
import json,subprocess,zipfile,hashlib
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'caster-riser-20261103';W=R.parent/'.p2s-caster-20261103';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
process=load(B/'motor-existing-holes-light-20261103/checks/slicing.json')['process']
process.update({'name':'P2S caster riser strong light 016 PLA','layer_height':'0.16','initial_layer_print_height':'0.2','wall_loops':'6','sparse_infill_density':'45%','sparse_infill_pattern':'gyroid','top_shell_layers':'8','bottom_shell_layers':'8','enable_support':'0','brim_type':'outer_only','brim_width':'5','brim_object_gap':'0.1'})
cfg=R.parent/'.p2s-pack-20261030/slicer-validation'
for n,data in [('process',process),('machine',load(cfg/'machine.json')),('filament',load(cfg/'filament.json'))]:save(W/f'{n}.json',data)
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
reports={}
for H in (35,40,45):
 v=W/f'H{H}';v.mkdir(exist_ok=True)
 src=O/f'CASTER_RISER_H{H}_GEOMETRY.3mf';pname=f'P2S_CASTER_RISER_H{H}_LIGHT_016.3mf'
 cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(v),'--debug','2',str(src)]
 with (v/'slice.log').open('w') as f:r=subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==0,(H,r.returncode,(v/'slice.log').read_text(errors='replace')[-1200:])
 res=load(v/'result.json');p=res['sliced_plates'][0];assert not p['warning_message'],(H,p['warning_message'])
 i=cmd.index('--slice');del cmd[i:i+2];cmd[cmd.index('--export-3mf')+1]=pname;cmd[cmd.index('--outputdir')+1]=str(O)
 with (v/'export.log').open('w') as f:r=subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==0
 project=O/pname
 with zipfile.ZipFile(project) as z,zipfile.ZipFile(v/'sliced.3mf') as tested:
  assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
  for n in z.namelist():
   if n.endswith('.model'):assert z.read(n)==tested.read(n)
  c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.16' and c['enable_support']=='0'
 reports[H]={'project':pname,'objects':3,'estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'warning_message':p['warning_message']}
save(O/'checks/slicing.json',{'status':'PASS','printer':'Bambu Lab P2S 0.4 nozzle','material':'Generic PLA','layer_mm':0.16,'variants':reports,'physical_test':False})
print((O/'checks/slicing.json').read_text(encoding='utf8'))
