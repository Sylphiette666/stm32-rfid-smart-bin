"""Locally slice unchanged integral models using a bounded PLA process."""
from pathlib import Path
import json,sys,shutil,subprocess,zipfile,hashlib
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2]
BASE=B/'integrated-pla-20261104';OLD=R.parent/'.p2s-integrated-pla-20261104'
W=R.parent/'.p2s-integrated-pla-fast-20261104'
cli=Path('C:/Users/35462/AppData/Local/Temp/smartbin-bambu-cli-20261030/portable/BambuCliHost.exe')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
idx={p.stem:p for p in (cli.parent/'resources/profiles/BBL').rglob('*.json')}
def resolve(n):
 d=load(idx[n]);parent=d.pop('inherits',None);a=resolve(parent) if parent else {};a.update(d);return a
for d in ['checks','projects','preview']:(O/d).mkdir(parents=True,exist_ok=True)
variant=sys.argv[1];names=sys.argv[2:] or ['LOWER_H41_B1','UPPER_INTEGRATED','PANEL_COVER']
for name in names:
 work=W/variant/name;work.mkdir(parents=True,exist_ok=True)
 machine=load(OLD/name/'machine.json');filament=resolve('Generic PLA @BBL P2S')
 process=load(OLD/name/'process.json');process.update(resolve('0.24mm Standard @BBL P2S'))
 process.update({'name':'SmartBin PLA Fast Tree '+variant,'layer_height':'0.24','initial_layer_print_height':'0.2',
 'wall_loops':'4' if name.startswith('LOWER') else '3','sparse_infill_density':'15%',
 'sparse_infill_pattern':'gyroid','top_shell_layers':'4','bottom_shell_layers':'4',
 'top_shell_thickness':'0.8','bottom_shell_thickness':'0.8','outer_wall_speed':'120',
 'inner_wall_speed':'230','top_surface_speed':'120','default_acceleration':'5000','outer_wall_acceleration':'2000',
 'initial_layer_speed':'35','initial_layer_infill_speed':'60','resolution':'0.01','enable_arc_fitting':'0',
 'enable_support':'1','support_type':'tree(auto)','support_style':'tree_slim',
 'support_on_build_plate_only':'0','support_threshold_angle':'40','tree_support_branch_angle':'40',
 'tree_support_branch_diameter':'3','tree_support_branch_distance':'5','tree_support_wall_count':'1',
 'support_top_z_distance':'0.2','support_bottom_z_distance':'0.2','support_object_xy_distance':'0.35',
 'support_interface_top_layers':'2','support_interface_bottom_layers':'2','support_interface_spacing':'0.5',
 'support_base_pattern_spacing':'2.5','support_speed':['150']*3,'support_interface_speed':['80']*3,
 'independent_support_layer_height':'1','brim_type':'outer_only','brim_width':'6','brim_object_gap':'0.1'})
 if name=='PANEL_COVER':process.update({'enable_support':'0','brim_width':'3','layer_height':'0.20'})
 patch=O/'source'/f'{variant}.json'
 if patch.exists():
  patches=load(patch);process.update(patches.get('process',{}));process.update(patches.get(name,{}));filament.update(patches.get('filament',{}))
 for n,d in [('process',process),('machine',machine),('filament',filament)]:save(work/f'{n}.json',d)
 geo=O/'source'/f"{'r4' if variant in ['r4','r5','r6'] else variant}_geometry"/f'{name}.3mf'
 shutil.copy2(geo if geo.exists() else OLD/name/'geometry.3mf',work/'geometry.3mf')
 cmd=[str(cli),'--datadir',str(work/'isolated-data'),'--load-settings',str(work/'machine.json')+';'+str(work/'process.json'),
 '--load-filaments',str(work/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work),'--debug','2',str(work/'geometry.3mf')]
 print(variant,name,'start',flush=True)
 with (work/'slice.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 report={'returncode':r.returncode,'process':process,'filament':filament,'machine':machine['name'],'physical_print_tested':False,'variant':variant}
 if (work/'result.json').exists():report['result']=load(work/'result.json')
 save(O/'checks'/f'{variant}_{name}_slicing.json',report)
 assert r.returncode==0,(name,(work/'slice.log').read_text(errors='replace')[-2000:])
 p=report['result']['sliced_plates'][0]
 print(name,'hours',p['total_predication']/3600,'grams',sum(x['total_used_g'] for x in p['filaments']),'warning',p['warning_message'],flush=True)
 assert not p['warning_message'],p['warning_message']
 i=cmd.index('--slice');del cmd[i:i+2];cmd[cmd.index('--export-3mf')+1]='project.3mf'
 with (work/'export.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0
 with zipfile.ZipFile(work/'project.3mf') as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
  assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
  assert all(z.read(n)==tested.read(n) for n in z.namelist() if n.endswith('.model'))
 print(name,'export checked',flush=True)
