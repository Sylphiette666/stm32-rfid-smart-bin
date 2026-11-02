"""One RIGHT motor adapter for quick dimensional fitting only, not structural service."""
from pathlib import Path
import json,zipfile,subprocess,xml.etree.ElementTree as E,copy
import numpy as np
B=Path(__file__).resolve().parents[1];R=B.parents[2]
O=B/'motor-adapter-clearance-20261102/quick-fit';W=R.parent/'.p2s-motor-quick-fit-20261102'
O.mkdir(parents=True,exist_ok=True);(O/'checks').mkdir(exist_ok=True);W.mkdir(exist_ok=True)
geometry=R.parent/'.p2s-motor-clearance-20261102/ADAPTER_PAIR.3mf'
process=json.loads((B/'motor-adapter-clearance-20261102/checks/slicing.json').read_text(encoding='utf-8'))['process']
process.update({'name':'D06 RIGHT quick dimensional fit 0.28','wall_loops':'2','sparse_infill_density':'15%','top_shell_layers':'3','bottom_shell_layers':'3','outer_wall_speed':['90']*3,'inner_wall_speed':['200']*3,'default_acceleration':['5000']*3,'outer_wall_acceleration':['2000']*3,'travel_acceleration':['6000']*3,'small_perimeter_speed':['70%']*3})
config=R.parent/'.p2s-pack-20261030/slicer-validation'
for name,data in [('process',process),('machine',json.loads((config/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((config/'filament.json').read_text(encoding='utf-8')))]:
 (W/f'{name}.json').write_text(json.dumps(data),encoding='utf-8')
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
# Only the photographed RIGHT adapter is exported for a low-material dry fit.
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
E.register_namespace('',ns)
tag=lambda n:'{'+ns+'}'+n
def mesh_data(mesh):
 raw=[tuple(float(v.attrib[k]) for k in ('x','y','z')) for v in mesh.find(tag('vertices'))]
 origin=[min(v[i] for v in raw) for i in range(3)]
 # Native projects recenter object coordinates and store float32 coordinates.
 vertices=[tuple(v[i]-origin[i] for i in range(3)) for v in raw]
 faces=[tuple(int(v.attrib[k]) for k in ('v1','v2','v3')) for v in mesh.find(tag('triangles'))]
 return np.array(vertices),np.array(faces)
parallel={}
with zipfile.ZipFile(geometry) as original:
 original_model=E.fromstring(original.read('3D/3dmodel.model'))
 for i,label in [(2,'RIGHT')]:
  model=copy.deepcopy(original_model);resources=model.find(tag('resources'));build=model.find(tag('build'))
  for ob in list(resources):
   if ob.attrib.get('id')!=str(i):resources.remove(ob)
  for item in list(build):
   if item.attrib.get('objectid')!=str(i):build.remove(item)
  expected=mesh_data(model.find('.//'+tag('mesh')))
  work=W/label;work.mkdir(exist_ok=True);single=work/'geometry.3mf'
  with zipfile.ZipFile(single,'w',zipfile.ZIP_DEFLATED) as z:
   for name in original.namelist():z.writestr(name,E.tostring(model,encoding='utf-8',xml_declaration=True) if name=='3D/3dmodel.model' else original.read(name))
  filename='P2S_D06_RIGHT_QUICK_FIT_028.3mf'
  job=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work),'--debug','2',str(single)]
  with (work/'slice.log').open('w') as log:done=subprocess.run(job,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
  assert done.returncode==0
  result=json.loads((work/'result.json').read_text(encoding='utf-8'));plate=result['sliced_plates'][0];assert not plate['warning_message']
  n=job.index('--slice');del job[n:n+2];job[job.index('--export-3mf')+1]=filename;job[job.index('--outputdir')+1]=str(O)
  with (work/'export.log').open('w') as log:done=subprocess.run(job,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
  assert done.returncode==0
  with zipfile.ZipFile(O/filename) as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
   assert z.testzip() is None and not any(n.endswith('.gcode') for n in z.namelist())
   meshes=[]
   for name in z.namelist():
    if name.endswith('.model'):
     assert z.read(name)==tested.read(name)
     meshes.extend(E.fromstring(z.read(name)).findall('.//'+tag('mesh')))
   assert len(meshes)==1
   actual=mesh_data(meshes[0]);assert np.array_equal(actual[1],expected[1]) and np.allclose(actual[0],expected[0],rtol=0,atol=1e-5)
  parallel[label]={'purpose':'DIMENSIONAL_FIT_ONLY_NOT_LOAD_BEARING','process':process,'project':filename,'estimated_seconds':plate['total_predication'],'filament_g':sum(f['total_used_g'] for f in plate['filaments']),'native_matches_tested':True,'mesh_identical_within_export_precision':True,'max_vertex_delta_mm':float(np.abs(actual[0]-expected[0]).max()),'warning_message':plate['warning_message']}
  print(json.dumps({k:v for k,v in parallel[label].items() if k!='process'}))
(O/'checks/slicing.json').write_text(json.dumps(parallel,indent=2)+'\n',encoding='utf-8',newline='\n')
if (O/'result.json').exists():(O/'result.json').unlink()
