from pathlib import Path
import json, cadquery as cq, trimesh, numpy as np
O=Path(__file__).resolve().parents[1];B=O.parent
for d in ['step','checks','preview']:(O/d).mkdir(exist_ok=True)
def box(x,y,z,a,b,c):return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def get(n):return cq.importers.importStep(str(B/'wall-panels-20261102/step'/f'{n}.step')).val()
def trans(s,m):return s.transformGeometry(cq.Matrix(m))
T={
'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],
'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],
'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],
'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
parts=[]
for n,m in T.items():
 s=get(n);side=n in ['W03_LEFT','W04_RIGHT'];w=160 if side else 144
 # Fill obsolete corner fastener bores. Preserve all sensor/hinge features.
 for x in ([9,w-9] if side else [6,w-6]):
  for y in [22,158]:s=s.fuse(cyl(x,y,0,3.3,3))
 if side:
  # Remove old outward base fixing feet; a continuous root replaces them.
  s=s.cut(box(-1,-1,5,162,16,12))
 if n=='W01_FRONT':
  # Open control bay lower face for installation and support extraction.
  # Keep original bay bottom; removable front supplies access.
  # The panel back faces the bay; existing component clearances retained.
  panel=trans(get('PANEL_COVER'),[[1,0,0,0],[0,1,0,45],[0,0,-1,62.4],[0,0,0,1]])
  cq.exporters.export(trans(panel,m),str(O/'step/PANEL_REMOVABLE_REFERENCE.step'))
 parts.append(trans(s,m))
upper=cq.importers.importStep(str(B/'step/P02_light.step')).val()
# Solid root strips unite wall/platform and reinforce four continuous corners.
roots=[box(49,19,4,162,5,5),box(49,166,4,162,5,5),box(49,23,4,5,144,5),box(206,23,4,5,144,5)]
for x in [50,205]:
 for y in [20,165]:roots.append(box(x,y,5,5,5,180))
print('fusing shell',flush=True)
s=upper.fuse(*parts,*roots).clean()
report=json.loads((B/'wall-panels-20261102/checks/design.json').read_text(encoding='utf-8'))
fixed={'BEAM_SEAT','DHT_SEAT','POWER_POD','BEAM_LEDGE','LID_SOFTSTOP_SEAT','CABLE_SADDLE','LED_INSERT','LID_SWITCH_PLATE','LIGHT_CRADLE','OBSTACLE_CRADLE'}
added=[]
for ins in report['sensor_instances']:
 n=ins['name']
 if n not in fixed:continue
 if 'wall' not in ins:continue
 q=get(n);p=ins['origin'];a=ins.get('matrix',np.eye(3).tolist())
 local=[a[i]+[p[i]] for i in range(3)]+[[0,0,0,1]]
 q=trans(trans(q,local),T[ins['wall']]);s=s.fuse(q);added.append(n)
print('sensor seats fused',added,flush=True)
# Original ultrasonic span is in shell-local coordinates; preserve aperture exactly.
beam=trans(get('ULTRASONIC_BEAM'),[[0,1,0,67.5],[1,0,0,23],[0,0,1,167],[0,0,0,1]])
# Positive-overlap landing webs, outside the sensor aperture, reach both sidewalls.
webs=[box(67.5,22,164,35,15,3.2),box(67.5,153,164,35,15,3.2)]
s=s.fuse(beam,*webs).clean()
print('solids',len(s.Solids()),'valid',s.isValid(),flush=True)
assert s.isValid() and len(s.Solids())==1
p=O/'step/UPPER_INTEGRATED.step';cq.exporters.export(s,str(p))
r=cq.importers.importStep(str(p)).val();assert r.isValid() and len(r.Solids())==1
assert abs(r.Volume()-s.Volume())/s.Volume()<1e-6
v,f=s.tessellate(.035,.07);m=trimesh.Trimesh([[p.x,p.y,p.z] for p in v],f);m.merge_vertices(digits_vertex=5)
# Search rigid orientations on exact tessellation, with a bed margin; no slicer claim.
best=[]
for rx in range(0,91,5):
 for rz in range(0,91,5):
  mat=trimesh.transformations.euler_matrix(np.radians(rx),0,np.radians(rz),'sxyz')
  vv=trimesh.transform_points(m.vertices,mat);ext=np.ptp(vv,axis=0)
  if np.all(ext<=[240,240,250]):best.append({'rx':rx,'rz':rz,'extent_mm':ext.tolist()})
bb=s.BoundingBox()
d={'status':'DRAFT_NOT_RELEASED','units':'mm','valid_brep':s.isValid(),'solid_count':len(s.Solids()),'step_roundtrip':True,'volume_mm3':s.Volume(),'bounds_mm':[[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]],'fixed_sensor_seats':added,'mesh_watertight':bool(m.is_watertight),'mesh_winding':bool(m.is_winding_consistent),'orientation_candidates_with_8mm_xy_margin':best,'not_checked':['component insertion and fastener tools','corrected light/IR retainers','servo and lid swept volume','all electronics interference','independent FreeCAD verification','slicing and removable supports','physical strength and print accuracy'],'panel_access':'user confirmed removable panel matching original four-screw scheme; separate accessory','source':'original STEP and explicit transforms from render_wall_clamp_preview.py'}
(O/'checks/upper_draft.json').write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:d[k] for k in ['solid_count','bounds_mm','mesh_watertight']},ensure_ascii=False),flush=True)
print('orientation candidates',len(best),flush=True)
