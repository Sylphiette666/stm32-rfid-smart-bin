"""Build four native Bambu projects and slice using GitHub-backed tree settings."""
from pathlib import Path
import json,zipfile,subprocess,math,hashlib,xml.etree.ElementTree as E
import trimesh
B=Path(__file__).resolve().parents[1];R=B.parents[2];BASE=B/'wall-panels-20261102';O=B/'wall-panels-fine-20261102';W=R.parent/'.p2s-wall-panels-fine-20261102'
for q in [O/'projects',O/'checks',O/'preview',W]:q.mkdir(parents=True,exist_ok=True)
d=json.loads((BASE/'checks/design.json').read_text(encoding='utf-8'))
source=json.loads((BASE/'source/github_support_source.json').read_text(encoding='utf-8'))
source_cfg=source['profile']
keys=['support_type','support_style','support_threshold_angle','tree_support_branch_angle','tree_support_branch_diameter','tree_support_wall_count','support_interface_top_layers','support_interface_bottom_layers','support_interface_spacing','support_object_xy_distance','support_base_pattern_spacing','support_on_build_plate_only']
support={k:source_cfg[k] for k in keys};support['enable_support']='1'
baseline=json.loads((B/'motor-adapter-20261101/checks/slicing.json').read_text(encoding='utf-8'))['process']
cfg=R.parent/'.p2s-pack-20261030/slicer-validation';cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
report={'status':'PASS','source_url':source['url'],'source_blob_sha':source['blob_sha'],'support_from_github':support,'plates':[]}
names=['FRONT_CONTROLS','REAR','LEFT','RIGHT']
for pid,items in d['plates'].items():
 i=int(pid);work=W/f'plate_{i}';work.mkdir(exist_ok=True)
 root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'))
 for j,item in enumerate(items,1):
  mesh=trimesh.load_mesh(BASE/'parts'/f"{item['name']}.stl")
  if item['rotation']:mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(item['rotation']),[0,0,1]));mesh.apply_translation(-mesh.bounds[0])
  mesh.apply_translation([item['x'],item['y'],0]);ob=E.SubElement(resources,tag('object'),{'id':str(j),'name':f"{item['name']}_{item['copy']}",'type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
  for v in mesh.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
  for f in mesh.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
  E.SubElement(build,tag('item'),{'objectid':str(j)})
 geometry=work/'geometry.3mf'
 with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
  for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
  z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
 height='0.16'
 process={**baseline,**support,'name':f'Wall {i} FINE 016 PLA','layer_height':height,'wall_loops':'3','sparse_infill_density':'15%','sparse_infill_pattern':'gyroid','top_shell_layers':'6','bottom_shell_layers':'6','support_top_z_distance':height,'support_bottom_z_distance':height,'brim_width':'2','brim_type':'outer_only','brim_object_gap':'0.1','enable_prime_tower':'0','outer_wall_speed':['60']*3,'inner_wall_speed':['150']*3,'top_surface_speed':['80']*3}
 for n,data in [('process',process),('machine',json.loads((cfg/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((cfg/'filament.json').read_text(encoding='utf-8')))]:
  (work/f'{n}.json').write_text(json.dumps(data),encoding='utf-8')
 cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(work/'machine.json')+';'+str(work/'process.json'),'--load-filaments',str(work/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work),'--debug','2',str(geometry)]
 with (work/'slice.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 assert done.returncode==0,(i,done.returncode)
 result=json.loads((work/'result.json').read_text(encoding='utf-8'));p=result['sliced_plates'][0]
 assert not p['warning_message'],(i,p['warning_message'])
 target=f'P2S_WALL_{i:02d}_{names[i-1]}_FINE_016.3mf';n=cmd.index('--slice');del cmd[n:n+2];cmd[cmd.index('--export-3mf')+1]=target;cmd[cmd.index('--outputdir')+1]=str(O/'projects')
 with (work/'export.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 assert done.returncode==0
 with zipfile.ZipFile(O/'projects'/target) as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
  assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
  for n in z.namelist():
   if n.endswith('.model'):assert z.read(n)==tested.read(n)
  c=json.loads(z.read('Metadata/project_settings.config'));assert c['enable_support']=='1' and c['support_type']=='tree(auto)'
 assert c['layer_height']=='0.16' and c['top_shell_layers']=='6' and c['bottom_shell_layers']=='6'
 assert c['outer_wall_speed']==['60']*3 and c['top_surface_speed']==['80']*3
 entry={'plate':i,'project':target,'objects':len(items),'estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'native_matches_tested':True,'native_contains_gcode':False,'sha256':hashlib.sha256((O/'projects'/target).read_bytes()).hexdigest(),'process':process}
 report['plates'].append(entry);(O/'checks/slicing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in entry.items() if k!='process'}),flush=True)
if (O/'projects/result.json').exists():(O/'projects/result.json').unlink()
