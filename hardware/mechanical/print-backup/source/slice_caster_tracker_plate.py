"""Create and validate one unsliced P2S project for all caster and tracker parts."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

B = Path(__file__).resolve().parents[1]
R = B.parents[2]
O = B/'caster-tracker-plate-20261103'
W = R.parent/'.p2s-caster-tracker-20261103'
W.mkdir(exist_ok=True)
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
save = lambda p,d: p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
process = load(B/'motor-existing-holes-light-20261103/checks/slicing.json')['process']
process.update({'name':'P2S caster H41 plus tracker all parts 012 PLA',
                'layer_height':'0.12','initial_layer_print_height':'0.2',
                'wall_loops':'6','sparse_infill_density':'45%',
                'sparse_infill_pattern':'gyroid','top_shell_layers':'8',
                'bottom_shell_layers':'8','enable_support':'0',
                'brim_type':'outer_only','brim_width':'5','brim_object_gap':'0.1'})
cfg = R.parent/'.p2s-pack-20261030/slicer-validation'
for name, data in [('process',process),('machine',load(cfg/'machine.json')),
                   ('filament',load(cfg/'filament.json'))]:
    save(W/f'{name}.json',data)
cli = Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
source = O/'CASTER_H41_TRACKER_ALL_GEOMETRY.3mf'
project = O/'P2S_CASTER_H41_TRACKER_ALL_012.3mf'
cmd = [str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),
       '--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),
       '--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0',
       '--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),
       '--debug','2',str(source)]
with (W/'slice.log').open('w') as f:
    result = subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
assert result.returncode == 0, (result.returncode,(W/'slice.log').read_text(errors='replace')[-1500:])
plate = load(W/'result.json')['sliced_plates'][0]
assert not plate['warning_message'],plate['warning_message']
cmd[cmd.index('--slice'):cmd.index('--slice')+2] = []
cmd[cmd.index('--export-3mf')+1] = project.name
cmd[cmd.index('--outputdir')+1] = str(O)
with (W/'export.log').open('w') as f:
    result = subprocess.run(cmd,cwd=cli.parent,stdout=f,stderr=subprocess.STDOUT)
assert result.returncode == 0, (result.returncode,(W/'export.log').read_text(errors='replace')[-1500:])
with zipfile.ZipFile(project) as package, zipfile.ZipFile(W/'sliced.3mf') as tested:
    assert package.testzip() is None and not any(n.endswith('.gcode') for n in package.namelist())
    for n in package.namelist():
        if n.endswith('.model'):
            assert package.read(n) == tested.read(n)
    config = json.loads(package.read('Metadata/project_settings.config'))
    assert config['layer_height'] == '0.12' and config['enable_support'] == '0'
report = {'status':'PASS','project':project.name,'objects':10,
          'printer':'Bambu Lab P2S 0.4 nozzle','material':'Generic PLA',
          'layer_mm':0.12,'wall_loops':6,'infill':'45% gyroid',
          'estimated_seconds':plate['total_predication'],
          'filament_g':sum(x['total_used_g'] for x in plate['filaments']),
          'warning_message':plate['warning_message'],
          'sha256':hashlib.sha256(project.read_bytes()).hexdigest(),
          'physical_print_tested':False}
save(O/'slicing_check.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
