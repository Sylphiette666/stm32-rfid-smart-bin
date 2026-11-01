from pathlib import Path
import sys,json,math,copy,zipfile,xml.etree.ElementTree as E,ast,shutil
import cadquery as cq
import numpy as np
import trimesh
BASE=Path(__file__).resolve().parents[1];OLD=BASE/'mounted-20261031';PREV=BASE/'parallel-after-old-plate2-20261101';OUT=BASE/'labeled-bases-20261101'
for d in ['step','parts','geometry','projects','checks']:(OUT/d).mkdir(parents=True,exist_ok=True)
design=json.loads((OLD/'source/design.json').read_text(encoding='utf-8'));mods={m['id']:m for m in design['modules']};parts={p['id']:p for p in design['parts']}
labels={'M01_body':'STM32','M02_body':'MCP23017','M03_body':'FLASH','M04_body':'TB6612','M05_body':'3.3V','M06_body':'DFPLAYER','M07_body':'HC-05','M08_body':'MPU6050','M09_body':'BUZZER','P05_BATTERY_cradle':'BAT 2S','P06_BUCK_cradle':'5V BUCK','P07_SPEAKER_cradle':'SPEAKER'}
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def world(s,ident):
 m=mods[parts[ident]['module']];return s.rotate((0,0,0),(0,0,1),m.get('rotation',0)).translate((*m['layout_origin'],5))
def bb(s):
 b=s.BoundingBox();return np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
def intersection(a,b):
 x,y=bb(a),bb(b)
 return a.intersect(b).Volume() if np.all(x[0]<y[1]) and np.all(y[0]<x[1]) else 0
cad={n:cq.importers.importStep(str(OLD/p['step'])).val() for n,p in parts.items() if p['module'] in mods and p['module']!='A1'}
obstacles={n:world(s,n) for n,s in cad.items()}
holes=[cq.Solid.makeCylinder(3.4,5,cq.Vector(*h['xy'],4.9)) for h in design['mount_holes']]
added=[];records=[];newmesh={}
for ident,text in labels.items():
 s=cad[ident];bounds=bb(s);found=None
 if '--speaker-only' in sys.argv and ident!='P07_SPEAKER_cradle':
  prior=json.loads((OUT/'checks/labels.json').read_text(encoding='utf-8'))['labels'];records.append(next(r for r in prior if r['id']==ident));result=cq.importers.importStep(str(OUT/'step'/f'{ident}.step')).val();added.append(world(result.cut(s),ident));newmesh[ident]=trimesh.load_mesh(OUT/'parts'/f'{ident}.stl');continue
 glyph=cq.Workplane('XY').text(text,4,.65,font='Arial',kind='bold',halign='center',valign='center',combine=True).val();gb=bb(glyph);length=max(18,float(gb[1,0]-gb[0,0])+4)
 for side in ['bottom','top','left','right']:
  vertical=side in ['left','right'];axis=1 if vertical else 0
  for center in np.linspace(bounds[0,axis]+length/2-2,bounds[1,axis]-length/2+2,11):
   if vertical:
    cx=bounds[0,0]-2 if side=='left' else bounds[1,0]+2;cy=center;w,h=8,length
   else:
    cx=center;cy=bounds[0,1]-2 if side=='bottom' else bounds[1,1]+2;w,h=length,8
   if ident=='P07_SPEAKER_cradle':side='right';vertical=True;cx=23.2;cy=-15.5;w=8;h=length
   plate=cq.Workplane('XY').box(w,h,1.8,centered=(True,True,False)).edges('|Z').fillet(1).translate((cx,cy,0)).val()
   if intersection(plate,s)<8:continue
   # Text sits on the outboard half of the plaque, clear of the holder itself.
   tx=cx+(-1 if side=='left' else 1 if side=='right' else 0);ty=cy+(-1 if side=='bottom' else 1 if side=='top' else 0)
   letters=glyph.rotate((0,0,0),(0,0,1),90 if vertical else 0).translate((tx,ty,1.79))
   if ident=='P07_SPEAKER_cradle':
    if intersection(plate,box(-3,-30,0,6,14,8))>1e-6:continue
    if intersection(plate,s)<8:continue
   if intersection(letters,s)>1e-6:continue
   tag=plate.fuse(letters).clean();g=world(tag,ident);bounds_global=bb(g)
   if min(bounds_global[0,:2])<1 or bounds_global[1,0]>279 or bounds_global[1,1]>219:continue
   if any(intersection(g,o)>1e-5 for n,o in obstacles.items() if n!=ident):continue
   if any(intersection(g,o)>1e-5 for o in added+holes):continue
   result=s.fuse(tag).clean()
   if not result.isValid() or len(result.Solids())!=1:continue
   found=(result,tag,side);break
  if found:break
 assert found is not None,('No safe label location',ident)
 result,tag,side=found;added.append(world(tag,ident));cq.exporters.export(result,str(OUT/'step'/f'{ident}.step'))
 flat=result.translate(tuple(-bb(result)[0]));file=OUT/'parts'/f'{ident}.stl';cq.exporters.export(flat,str(file),tolerance=.018,angularTolerance=.05)
 mesh=trimesh.load_mesh(file);mesh.merge_vertices(digits_vertex=5);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();assert mesh.is_watertight and mesh.is_winding_consistent,ident;mesh.export(file);newmesh[ident]=mesh
 records.append({'id':ident,'label':text,'module':parts[ident]['module'],'side':side,'plate_thickness_mm':1.8,'raised_text_mm':.64,'text_height_mm':4,'assembly_tag_bounds':bb(world(tag,ident)).tolist(),'original_material_retained':True,'existing_part_collision':False,'mount_hardware_clear':True,'in_current_jobs':ident!='P07_SPEAKER_cradle'})
 print(ident,text,side,flush=True)
ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'};E.register_namespace('',ns['m']);tag=lambda s:'{'+ns['m']+'}'+s
# Independent, separated objects replace the old nested layout on the two fine beds.
packing=[]
for job in [1,2]:
 shutil.copy2(PREV/f'geometry/PLATE_{job}_GEOMETRY.3mf',OUT/f'geometry/PLATE_{job}_GEOMETRY.3mf')
 packing.append({'plate':job,'objects':1,'base_geometry_unchanged':True})
tree=ast.parse((BASE/'source/pack_flat_split.py').read_text(encoding='utf-8'));helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['contains','overlaps','split_free']];exec(compile(ast.Module(body=helpers,type_ignores=[]),'helpers','exec'))
for job in [3,4]:
 with zipfile.ZipFile(PREV/f'geometry/PLATE_{job}_GEOMETRY.3mf') as z:root=E.fromstring(z.read('3D/3dmodel.model'))
 meshes={}
 for o in root.findall('m:resources/m:object',ns):
  name=o.get('name')
  if name in newmesh:meshes[name]=newmesh[name].copy()
  else:
   v=[[float(v.get(k)) for k in ['x','y','z']] for v in o.findall('m:mesh/m:vertices/m:vertex',ns)];f=[[int(t.get(k)) for k in ['v1','v2','v3']] for t in o.findall('m:mesh/m:triangles/m:triangle',ns)];m=trimesh.Trimesh(v,f,process=False);m.apply_translation(-m.bounds[0]);meshes[name]=m
 free=[[4,4,252,252]];placements=[]
 for name,m in sorted(meshes.items(),key=lambda p:-np.prod(p[1].extents[:2])):
  w,h=m.extents[:2];choices=[]
  for region in free:
   for rot,a,b in [(0,w,h),(90,h,w)]:
    if a+7<=region[2]-region[0] and b+7<=region[3]-region[1]:choices.append(((region[2]-region[0])*(region[3]-region[1])-(a+7)*(b+7),region,rot,a,b))
  assert choices,('Bed does not fit',job,name)
  _,r,rot,a,b=min(choices,key=lambda v:v[0]);x,y=r[:2]
  if rot:m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1]));m.apply_translation(-m.bounds[0])
  m.apply_translation([x+3.5,y+3.5,0]);free=split_free(free,[x,y,x+a+7,y+b+7]);placements.append({'id':name,'bounds':m.bounds.tolist()})
 resources=root.find('m:resources',ns);build=root.find('m:build',ns);resources.clear();build.clear()
 for i,(name,m) in enumerate(meshes.items(),1):
  obj=E.SubElement(resources,tag('object'),{'id':str(i),'name':name,'type':'model'});me=E.SubElement(obj,tag('mesh'));vs=E.SubElement(me,tag('vertices'));fs=E.SubElement(me,tag('triangles'))
  for v in m.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],[f'{n:.8f}' for n in v])))
  for f in m.faces:E.SubElement(fs,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
  E.SubElement(build,tag('item'),{'objectid':str(i)})
 with zipfile.ZipFile(PREV/f'geometry/PLATE_{job}_GEOMETRY.3mf') as z,zipfile.ZipFile(OUT/f'geometry/PLATE_{job}_GEOMETRY.3mf','w',zipfile.ZIP_DEFLATED) as out:
  for p in ['[Content_Types].xml','_rels/.rels']:out.writestr(p,z.read(p))
  out.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
 packing.append({'plate':job,'objects':len(meshes),'placements':placements,'separate_objects_gap_mm':7})
(OUT/'checks/labels.json').write_text(json.dumps({'status':'PASS','labels':records,'optional_speaker_not_in_current_print_jobs':True,'physical_test':False},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'checks/packing.json').write_text(json.dumps({'status':'PASS','plates':packing,'total_objects':48},ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(PREV/'checks/route_coverage.json',OUT/'checks/route_coverage.json')
