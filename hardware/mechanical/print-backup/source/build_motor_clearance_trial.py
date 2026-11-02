"""D06 slot-edge clearance trial; no measured wheel envelope or load rating."""
from pathlib import Path
import json,math,zipfile,subprocess,xml.etree.ElementTree as E
import cadquery as cq
import trimesh,numpy as np
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'motor-adapter-clearance-20261102';W=R.parent/'.p2s-motor-clearance-20261102'
for p in [O/'parts',O/'step',O/'checks',O/'preview',W]:p.mkdir(parents=True,exist_ok=True)
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def intersect(a,b):
 aa=a.BoundingBox();bb=b.BoundingBox()
 if aa.xmax<=bb.xmin or bb.xmax<=aa.xmin or aa.ymax<=bb.ymin or bb.ymax<=aa.ymin or aa.zmax<=bb.zmin or bb.zmax<=aa.zmin:return 0
 return a.intersect(b).Volume()
THICK=3;CLEAR=6;HEIGHT=THICK+CLEAR
fit=cq.importers.importStep(str(B/'motor-fit-20261101/fast/b_only/thin3/plain/step/FIT_B.step')).val()
# Remove 3 mm from each slot-side perimeter, retain 3.3 mm outside slots.
original_fit=fit
fit=fit.intersect(box(-14,-15,0,28,30,THICK)).clean()
assert abs(fit.BoundingBox().ylen-30)<1e-6 and fit.isValid()
variants={
 'LEFT':{'centre':[96,14],'holes':[[-20,-6],[-20,6],[20,-6],[20,6]]},
 'RIGHT':{'centre':[96,206],'holes':[[16,-22],[16,-10],[32,-22],[32,-10]]}}
meshes={};shapes={}
def web(p,q,width,z,height):
 dx=q[0]-p[0];dy=q[1]-p[1];d=math.hypot(dx,dy);nx=-dy/d*width/2;ny=dx/d*width/2
 pts=[(p[0]+nx,p[1]+ny),(q[0]+nx,q[1]+ny),(q[0]-nx,q[1]-ny),(p[0]-nx,p[1]-ny)]
 return cq.Workplane('XY').polyline(pts).close().extrude(height).translate((0,0,z)).val()
for name,v in variants.items():
 s=fit
 for x in [-14,11]:s=s.fuse(box(x,-15,3,3,30,CLEAR))
 for x,y in v['holes']:
  root=(12 if x>0 else -12,max(-15,min(15,y)))
  s=s.fuse(cyl(x,y,0,5.5,HEIGHT)).fuse(web(root,(x,y),10,0,3)).fuse(web(root,(x,y),3,3,CLEAR))
 for y in [-10.5,10.5]:s=s.cut(box(-6,y-1.2,-1,12,2.4,HEIGHT+2))
 s=s.cut(box(-7,-6,-1,14,12,HEIGHT+2))
 for x,y in v['holes']:s=s.cut(cyl(x,y,-1,1.7,HEIGHT+2))
 s=s.clean();assert s.isValid() and len(s.Solids())==1,name
 # Preserve the reduced coupon, slot positions, and the coplanar contact face.
 assert fit.cut(s).Volume()<1e-6,name
 for y in [-10.5,10.5]:
  assert intersect(s,box(-6,y-1.2,-1,12,2.4,12))<1e-6
  assert intersect(s,box(-8.5,y-1.5,3,17,3,CLEAR))<1e-6
 old=cq.importers.importStep(str(B/'motor-adapter-20261101/step'/f'D06_ADAPTER_{name}.step')).val()
 for x,y in v['holes']:
  land=cyl(x,y,0,5.5,HEIGHT)
  assert old.intersect(land).cut(s).Volume()<1e-6,(name,'bolt land changed')
 critical=box(-8.5,-13.5,0,17,27,HEIGHT)
 assert old.intersect(critical).cut(s).Volume()<1e-6,(name,'slot bearing changed')
 assert s.intersect(critical).cut(old).Volume()<1e-6,(name,'slot cavity changed')
 v['removed_material_mm3']=old.cut(s).Volume()
 cq.exporters.export(s,str(O/'step'/f'D06_ADAPTER_{name}.step'))
 bb=s.BoundingBox();flat=s.translate((-bb.xmin,-bb.ymin,0));stl=O/'parts'/f'D06_ADAPTER_{name}.stl'
 cq.exporters.export(flat,str(stl),tolerance=.018,angularTolerance=.05)
 mesh=trimesh.load_mesh(stl);assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,name
 meshes[name]=mesh;shapes[name]=s;v['size_mm']=mesh.extents.tolist()
# Investigate bolt-head clearances against current labeled fixtures; no guessed wheel geometry.
design=json.loads((B/'flat-split-20261101/source/design.json').read_text(encoding='utf-8'))
mods={d['id']:d for d in design['modules']};fixtures=[]
for p in design['parts']:
 if p.get('module') not in mods or p.get('module')=='A1':continue
 source=B/'labeled-bases-20261101/step'/f"{p['id']}.step"
 if not source.exists():source=B/'mounted-20261031'/p['step']
 shape=cq.importers.importStep(str(source)).val();mdata=mods[p['module']]
 shape=shape.rotate((0,0,0),(0,0,1),mdata['rotation']).translate((*mdata['layout_origin'],5));fixtures.append((p['id'],shape))
existing=[h['xy'] for h in design['mount_holes']]+[[30,25],[250,25],[30,195],[250,195]]
rear=cq.importers.importStep(str(B/'flat-split-20261101/step/P01_REAR_HALF.step')).val()
fixtures.append(('actual_speaker_body_clearance',cyl(68,198,7,20,14)))
for name,v in variants.items():
 cx,cy=v['centre'];pts=[(cx+x,cy+y) for x,y in v['holes']];v['candidate_base_holes']=pts
 for x,y in pts:
  assert all(math.dist((x,y),q)>=8 for q in existing),(name,x,y,'existing hole')
  assert cyl(x,y,0,5.5,5).cut(rear).Volume()<1e-6,(name,x,y,'bearing land')
  assert not [(n,intersect(cyl(x,y,5,3,2.2),f)) for n,f in fixtures if intersect(cyl(x,y,5,3,2.2),f)>1e-6],(name,x,y,'head interference')
 assert intersect(shapes[name].translate((cx,cy,-HEIGHT)),rear)<1e-6
report={'status':'GEOMETRY_CHECKED_WHEEL_PLACEMENT_PENDING','variants':variants,'slot_mm':[12,2.4],'slot_centre_distance_mm':21,'contact_thickness_mm':3,'head_cavity_mm':CLEAR,'head_height_measured_mm':5,'quantity':2,'identical_parts':False,'text_on_part':False,'closed_valid_solids':True,'watertight_meshes':True,'proven_coupon_material_preserved':False,'reduced_coupon_preserved':True,'slot_body_width_before_mm':36,'slot_body_width_after_mm':30,'edge_setback_each_side_mm':3,'slot_outer_ligament_mm':3.3,'actual_wheel_gap_mm':None,'release_type':'DRY_FIT_TRIAL','candidate_bolt_heads_clear':True,'base_drilling_authorized_by_this_drawing':False,'physical_load_test':False,'motor_wheel_full_envelope_verified':False,'final_drilling_requires_dry_fit':True,'all_candidate_feet_bear_on_full_5mm_chassis':True}
(O/'checks/design.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';E.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
root=E.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'});resources=E.SubElement(root,tag('resources'));build=E.SubElement(root,tag('build'))
for i,(name,xy) in enumerate([('LEFT',(60,105)),('RIGHT',(130,105))],1):
 mesh=meshes[name].copy();mesh.apply_translation([*xy,0]);ob=E.SubElement(resources,tag('object'),{'id':str(i),'name':f'D06_ADAPTER_{name}','type':'model'});me=E.SubElement(ob,tag('mesh'));vs=E.SubElement(me,tag('vertices'));ts=E.SubElement(me,tag('triangles'))
 for v in mesh.vertices:E.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],map(str,v))))
 for f in mesh.faces:E.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
 E.SubElement(build,tag('item'),{'objectid':str(i)})
geometry=W/'ADAPTER_PAIR.3mf'
with zipfile.ZipFile(B/'labeled-bases-20261101/geometry/PLATE_3_GEOMETRY.3mf') as template,zipfile.ZipFile(geometry,'w',zipfile.ZIP_DEFLATED) as z:
 for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,template.read(n))
 z.writestr('3D/3dmodel.model',E.tostring(root,encoding='utf-8',xml_declaration=True))
process=json.loads((B/'motor-fit-20261101/fast/b_only/thin3/plain/checks/validation.json').read_text(encoding='utf-8'))['process']
process.update({'name':'D06 clearance trial pair 0.28','wall_loops':'4','sparse_infill_density':'40%','top_shell_layers':'4','bottom_shell_layers':'4','brim_type':'no_brim','brim_width':'0','brim_object_gap':'0.1'})
config=R.parent/'.p2s-pack-20261030/slicer-validation'
for name,data in [('process',process),('machine',json.loads((config/'machine.json').read_text(encoding='utf-8'))),('filament',json.loads((config/'filament.json').read_text(encoding='utf-8')))]:
 (W/f'{name}.json').write_text(json.dumps(data),encoding='utf-8')
cli=Path(r'C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe')
cmd=[str(cli),'--datadir',str(cli.parent.parent/'isolated-data'),'--load-settings',str(W/'machine.json')+';'+str(W/'process.json'),'--load-filaments',str(W/'filament.json'),'--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf','--outputdir',str(W),'--debug','2',str(geometry)]
with (W/'slice.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
result=json.loads((W/'result.json').read_text(encoding='utf-8'));p=result['sliced_plates'][0];assert not p['warning_message']
n=cmd.index('--slice');del cmd[n:n+2];cmd[cmd.index('--export-3mf')+1]='P2S_D06_CLEARANCE_TRIAL_PAIR_028.3mf';cmd[cmd.index('--outputdir')+1]=str(O)
with (W/'export.log').open('w') as log:done=subprocess.run(cmd,cwd=cli.parent,stdout=log,stderr=subprocess.STDOUT)
assert done.returncode==0
with zipfile.ZipFile(O/'P2S_D06_CLEARANCE_TRIAL_PAIR_028.3mf') as z,zipfile.ZipFile(W/'sliced.3mf') as tested:
 assert not any(n.endswith('.gcode') for n in z.namelist())
 for n in z.namelist():
  if n.endswith('.model'):assert z.read(n)==tested.read(n)
report={'status':'PASS','estimated_seconds':p['total_predication'],'filament_g':sum(f['total_used_g'] for f in p['filaments']),'warning_message':p['warning_message'],'process':process,'native_matches_tested':True,'physical_test':False}
(O/'checks/slicing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
if (O/'result.json').exists():(O/'result.json').unlink()
print(json.dumps({'slice_seconds':report['estimated_seconds'],'filament_g':report['filament_g'],'variants':list(variants)},ensure_ascii=False))
