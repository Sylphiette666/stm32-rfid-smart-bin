"""Derive a finer print profile without changing the physically confirmed geometry."""
from pathlib import Path
import json,zipfile,subprocess
B=Path(__file__).resolve().parents[1];R=B.parents[2]
O=B/'motor-adapter-20261101/fine-016';W=R.parent/'.p2s-motor-adapter-fine-20261102'
O.mkdir(parents=True,exist_ok=True);(O/'checks').mkdir(exist_ok=True);W.mkdir(exist_ok=True)
geometry=R.parent/'.p2s-motor-adapter-20261101/ADAPTER_PAIR.3mf'
process=json.loads((B/'motor-adapter-20261101/checks/slicing.json').read_text(encoding='utf-8'))['process']
process.update({'name':'D06 adapter fine 0.16','layer_height':'0.16','outer_wall_speed':['40','40','40'],'inner_wall_speed':['80','80','80'],'top_surface_speed':['60','60','60'],'top_shell_layers':'7','bottom_shell_layers':'7'})
config=R.parent/'.p2s-pack-20261030/slicer-validation'
for name,data in [('process',process),('machine',json.loads((config/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((config/'filament.json').read_text(encoding='utf-8')))]:
 (W/f'{name}.json').write_text(json.dumps(data),encoding='utf-8')
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
result=json.loads((W/'result.json').read_text(encoding='utf-8'));p=result['sliced_plates'][0];assert not p['warning_message']
n=cmd.index('--slice');del cmd[n:n+2];cmd[cmd.index('--export-3mf')+1]='P2S_D06_ADAPTER_PAIR_FINE_016.3mf';cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
with zipfile.ZipFile(O/'P2S_D06_ADAPTER_PAIR_FINE_016.3mf') as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
 assert not any(n.endswith('.gcode') for n in z.namelist())
 for n in z.namelist():
  if n.endswith('.model'):assert z.read(n)==tested.read(n)
report={'status':'PASS','estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'process':process,'native_matches_tested':True,'physical_test':False}
(O/'checks/slicing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps({'slice_seconds':report['estimated_seconds'],'filament_g':report['filament_g']},ensure_ascii=False))
