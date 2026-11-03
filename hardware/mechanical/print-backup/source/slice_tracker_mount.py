"""Slice and package the tracker frame and optional spacer pairs for P2S."""
from pathlib import Path
import json,subprocess,zipfile,hashlib,shutil
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'tracker-mount-20261103';W=R.parent/'.p2s-tracker-20261103';W.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
process=load(B/'sensor-retainers-fix-20261103/checks/slicing.json')['process']
process.update({'name':'P2S tracker mount fine 012 PLA','layer_height':'0.12','initial_layer_print_height':'0.2','wall_loops':'4','sparse_infill_density':'30%','sparse_infill_pattern':'gyroid','top_shell_layers':'6','bottom_shell_layers':'6','enable_support':'0','brim_type':'outer_only','brim_width':'4','brim_object_gap':'0.1'})
cfg=R.parent/'.p2s-pack-20261030/slicer-validation'
for n,d in [('process',process),('machine',load(cfg/'machine.json')),('filament',load(cfg/'filament.json'))]:save(W/f'{n}.json',d)
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(O/'TRACKER_LIGHT_GEOMETRY.3mf')]
with (W/'slice.log').open('w') as f:r=subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,(r.returncode,(W/'slice.log').read_text(errors='replace')[-1500:])
res=load(W/'result.json');p=res['sliced_plates'][0];assert not p['warning_message'],p['warning_message']
i=cmd.index('--slice');del cmd[i:i+2];cmd[cmd.index('--export-3mf')+1]='P2S_TRACKER_LIGHT_FINE_012.3mf';cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as f:r=subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
project=O/'P2S_TRACKER_LIGHT_FINE_012.3mf'
with zipfile.ZipFile(project) as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
    assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
    for n in z.namelist():
        if n.endswith('.model'):assert z.read(n)==tested.read(n)
    c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.12' and c['enable_support']=='0'
report={'status':'SLICED','project':project.name,'objects':7,'material':'Generic PLA','printer':'Bambu Lab P2S 0.4 nozzle','layer_mm':0.12,'estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'physical_trial_fit':False}
save(O/'checks/slicing.json',report);print(json.dumps(report,ensure_ascii=False))
