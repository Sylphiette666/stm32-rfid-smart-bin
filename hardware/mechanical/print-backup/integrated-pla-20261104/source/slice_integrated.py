"""Orient exact-size solids, export native projects, and locally dry-slice PLA."""
from pathlib import Path
import sys,json,zipfile,subprocess,xml.etree.ElementTree as E
import cadquery as cq,numpy as np,trimesh
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import differential_evolution
O=Path(__file__).resolve().parents[1]; B=O.parent; R=B.parents[2]
W=R.parent/'.p2s-integrated-pla-20261104';W.mkdir(exist_ok=True)
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
idx={p.stem:p for p in (cli.parent/'resources/profiles/BBL').rglob('*.json')}
def resolve(n):
 d=load(idx[n]);parent=d.pop('inherits',None);a=resolve(parent) if parent else {};a.update(d);return a
machine=load(R.parent/'.p2s-pack-20261030/slicer-validation/machine.json')
assert machine['nozzle_diameter']==['0.4'] and machine['min_layer_height']==['0.08']
filament=resolve('Generic PLA @BBL P2S')
filament['filament_max_volumetric_speed']=['8','8','8']
process=load(B/'wall-clamps-fine-20261103/checks/slicing.json')['process']
process.update(resolve('0.08mm High Quality @BBL P2S'))
process.update({'name':'SmartBin Integral PLA Fine 008','layer_height':'0.08','initial_layer_print_height':'0.16',
 'wall_loops':'4','sparse_infill_density':'15%','sparse_infill_pattern':'gyroid','top_shell_layers':'10','bottom_shell_layers':'10',
 'top_shell_thickness':'0.8','bottom_shell_thickness':'0.8','outer_wall_speed':'25','inner_wall_speed':'50','top_surface_speed':'25',
 'sparse_infill_speed':'60','initial_layer_speed':'20','initial_layer_infill_speed':'30','default_acceleration':'1500',
 'outer_wall_acceleration':'600','top_surface_acceleration':'600','resolution':'0.01',
 'enable_support':'1','support_type':'tree(auto)','support_style':'tree_hybrid','support_on_build_plate_only':'0',
 'support_threshold_angle':'45','tree_support_branch_angle':'35','tree_support_branch_diameter':'3',
 'tree_support_wall_count':'2','support_top_z_distance':'0.16','support_bottom_z_distance':'0.16',
 'support_object_xy_distance':'0.35','support_interface_top_layers':'3','support_interface_bottom_layers':'2',
 'support_interface_spacing':'0.35','support_speed':['60','60','60'],'support_interface_speed':['35','35','35'],
 'brim_type':'outer_only','brim_width':'6','brim_object_gap':'0.1','enable_arc_fitting':'0'})
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
names=sys.argv[1:] or ['LOWER_H41_B1','UPPER_INTEGRATED']
for name in names:
 work=W/name;work.mkdir(exist_ok=True)
 s=cq.importers.importStep(str(O/'step'/f'{name}.step')).val()
 v,f=s.tessellate(.01,.05);mesh=trimesh.Trimesh([[p.x,p.y,p.z] for p in v],f);mesh.merge_vertices(digits_vertex=5)
 mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices()
 if not mesh.is_watertight:
  counts=np.bincount(mesh.edges_unique_inverse);bad=mesh.vertices[mesh.edges_unique[counts!=2]]
  print('NONMANIFOLD',len(bad),np.round(bad[:30],6),flush=True)
 assert mesh.is_watertight and mesh.is_winding_consistent
 hull=mesh.vertices[ConvexHull(mesh.vertices).vertices];lim=np.array([240,240,250])
 def cost(x):return max(np.ptp(Rotation.from_euler('xyz',x,degrees=True).apply(hull),axis=0)/lim)
 if name=='PANEL_COVER':rot=Rotation.identity()
 elif name.startswith('LOWER'):rot=Rotation.from_euler('xyz',[90,0,45],degrees=True)
 else:
  opt=differential_evolution(cost,[(0,360)]*3,seed=44,popsize=18,maxiter=220,tol=1e-7)
  rot=Rotation.from_euler('xyz',opt.x,degrees=True)
 rv=rot.as_rotvec();ang=np.linalg.norm(rv)
 oriented=s if ang<1e-9 else s.rotate((0,0,0),tuple(rv/ang),float(np.degrees(ang)))
 bb=oriented.BoundingBox()
 ext=np.array([bb.xlen,bb.ylen,bb.zlen]);assert np.all(ext<=lim),(name,ext)
 # Bed-centred, preserve the exact geometry and its rotation separately.
 mat=np.eye(4);mat[:3,:3]=rot.as_matrix();mesh.apply_transform(mat)
 shift=np.array([128,128,0])-np.r_[mesh.bounds.mean(axis=0)[:2],mesh.bounds[0,2]]
 mesh.apply_translation(shift);mat[:3,3]=shift
 save(O/'checks'/f'{name}_orientation.json',{'scale':1,'units':'mm','matrix_design_to_print':mat.tolist(),
 'exact_brep_extent_mm':ext.tolist(),'mesh_bounds_mm':mesh.bounds.tolist(),'mesh_faces':len(mesh.faces),
 'watertight':True,'winding_consistent':True,'cad_volume_mm3':s.Volume(),'tessellation_linear_mm':.01,
 'bed_mm':[256,256,256],'reserved_xy_each_side_mm':8,'source_material':'PLA'})
 root=E.Element(tag('model'),{'unit':'millimeter'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'))
 ob=E.SubElement(resources,tag('object'),{'id':'1','name':name,'type':'model'});me=E.SubElement(ob,tag('mesh'))
 vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
 for v in mesh.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
 for f in mesh.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
 E.SubElement(build,tag('item'),{'objectid':'1'})
 geo=work/'geometry.3mf'
 with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geo,'w',zipfile.ZIP_DEFLATED) as z:
  for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
  z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
 cfg=process.copy()
 if name.startswith('LOWER'):cfg.update({'wall_loops':'5','sparse_infill_density':'20%'})
 if name=='PANEL_COVER':cfg.update({'enable_support':'0','brim_width':'3'})
 for n,d in [('process',cfg),('machine',machine),('filament',filament)]:save(work/f'{n}.json',d)
 cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(work/'machine.json')+';'+str(work/'process.json'),
 '--load-filaments',str(work/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work),'--debug','2',str(geo)]
 print(name,'slice start',ext,flush=True)
 with (work/'slice.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 report={'returncode':r.returncode,'process':cfg,'filament':filament,'machine':machine['name'],'physical_print_tested':False}
 if (work/'result.json').exists():report['result']=load(work/'result.json')
 save(O/'checks'/f'{name}_slicing.json',report)
 assert r.returncode==0,(name,(work/'slice.log').read_text(errors='replace')[-3000:])
 plate=report['result']['sliced_plates'][0];print(name,plate,flush=True)
 assert not plate['warning_message'],plate['warning_message']
 i=cmd.index('--slice');del cmd[i:i+2];cmd[cmd.index('--export-3mf')+1]=f'P2S_{name}_PLA_008.3mf';cmd[cmd.index('--outputdir')+1]=str(O/'projects')
 with (work/'export.log').open('w') as log:r=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
 assert r.returncode==0
 with zipfile.ZipFile(O/'projects'/f'P2S_{name}_PLA_008.3mf') as z,zipfile.ZipFile(work/'sliced.3mf') as tested:
  assert z.testzip() is None
  assert all(z.read(n)==tested.read(n) for n in z.namelist() if n.endswith('.model'))
 print(name,'native project exported',flush=True)
