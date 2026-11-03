from pathlib import Path
import json,math,cadquery as cq,trimesh
O=Path(__file__).resolve().parents[1];B=O.parent
# User dimensional inputs and nominal derived heights; physical fit not yet validated.
H=41;TRACKER_DROP=H+20-8-1.6-8
# H+20 nominal ground; 8 mm probe; provisional1.6 board; target8mm sensor gap.
def box(x,y,z,a,b,c):return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()
def cy(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def rib(p,q,z,h,w):
 dx=q[0]-p[0];dy=q[1]-p[1];l=math.hypot(dx,dy);a=-dy/l*w/2;b=dx/l*w/2
 return cq.Workplane('XY').polyline([(p[0]+a,p[1]+b),(q[0]+a,q[1]+b),(q[0]-a,q[1]-b),(p[0]-a,p[1]-b)]).close().extrude(h).translate((0,0,z)).val()
s=cq.importers.importStep(str(B/'step/P01_light.step')).val();add=[]
# Rebuild only necessary fastener passages. Integral bases need no foot bolts.
service_holes=[]
# Motor contact plane and slot datums remain identical to existing assembled stack.
for side,cx,yy in [('LEFT',96,14),('RIGHT',96,206)]:
 seat=cq.importers.importStep(str(B/'motor-existing-holes-20261102/step'/f'D06_SEAT_{side}_ASSEMBLY.step')).val()
 # Delete obsolete mounting ears/bolt holes while preserving the confirmed core.
 ymin=-13 if side=='LEFT' else -15
 seat=seat.intersect(box(82,yy+ymin,-26,28,28,12)).clean()
 add.append(seat)
 # Two full-height inboard load paths, preserving wheel-facing envelope.
 for xx in [82,107]:add.append(box(xx,yy-12,-22,3,24,24))
 # Upper cross braces transfer loads into the continuous deck.
 for xx in [82,107]:add.append(box(xx-2,yy-12,-5,7,24,7))
# B1 uses the original 90 x 90 mm hole pitch, with 20 mm integral standoffs.
posts=[(115,65),(205,65),(115,155),(205,155)]
for x,y in posts:
 add.append(cy(x,y,3,5.5,22))
 for dx,dy in [(8,0),(-8,0),(0,8),(0,-8)]:add.append(rib((x,y),(x+dx,y+dy),4,5,2.4))
# Extract measured specs without executing the old generator or rewriting its outputs.
import ast
old=ast.parse((B/'source/build_mounted_design.py').read_text(encoding='utf-8-sig'))
specs=next([{k.arg:ast.literal_eval(k.value) for k in call.keywords} for call in n.value.elts] for n in old.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPECS' for t in n.targets))
fixed=[]
for sp in specs:
 xy=sp['xy']
 if sp['id']=='M09':xy=[252,65]
 if sp['id']=='M08':xy=[253,170];sp['rotation']=90
 body=cq.importers.importStep(str(B/'mounted-20261031/step'/(sp['id']+'_body.step'))).val().rotate((0,0,0),(0,0,1),sp['rotation']).translate((*xy,5))
 add.append(body);fixed.append((sp['id'],body))
 # Preserve moving latch axis/leaf anchor with access through the integral deck.
 dims=json.loads((B/'mounted-20261031/source/design.json').read_text(encoding='utf-8'))
 mod=next(m for m in dims['modules'] if m['id']==sp['id'])
 for key in ['lock_axis_xy','lock_anchor_xy']:
  p=mod['mechanism'][key];a=math.radians(sp['rotation'])
  service_holes.append((xy[0]+p[0]*math.cos(a)-p[1]*math.sin(a),xy[1]+p[0]*math.sin(a)+p[1]*math.cos(a),1.7))
for name,xy in [('P06_BUCK_cradle',(202.5,187.5)),('P07_SPEAKER_cradle',(256,120)),('P05_BATTERY_cradle',(176,30))]:
 body=cq.importers.importStep(str(B/'mounted-20261031/step'/(name+'.step'))).val()
 if name=='P07_SPEAKER_cradle':body=body.rotate((0,0,0),(0,0,1),90)
 body=body.translate((*xy,5));add.append(body);fixed.append((name,body))
service_holes += [(256,96,1.7),(256,144,1.7),(188,196,1.4),(217,179,1.4)]
for h in dims['mount_holes']:
 if h['name'].startswith('BAT_') and not h['name'].endswith('foot'):
  service_holes.append((*h['xy'],1.7))
# Full material beneath the functional through-bolts, not the obsolete foot holes.
deck_envelope=cq.importers.importStep(str(B/'step/P01_full.step')).val()
for x,y,r in service_holes:add.append(cy(x,y,0,5.3,5).intersect(deck_envelope))
# Direct caster pads: no mounting adapter; connect to base with conical roots and perimeter ribs.
for y in [90,130]:
 add.append(cy(240,y,-H,7.5,H+3));add.append(cq.Solid.makeCone(7.5,13,8,cq.Vector(240,y,-8)))
add.append(rib((240,90),(240,130),-H, H+2,3))
# Line module centres exactly59.5mm; height stays parameterized pending ground datum.
for y in [80.25,139.75]:
 add.append(cy(185,y,-TRACKER_DROP,5.5,TRACKER_DROP+3))
 add.append(cq.Solid.makeCone(5.5,11,8,cq.Vector(185,y,-8)))
add.append(rib((185,80.25),(185,139.75),-TRACKER_DROP,TRACKER_DROP+2,3))
# Check whether original holders obstruct the new T-head insertion channels.
holder_conflicts=[]
for i,(na,aa) in enumerate(fixed):
 for nb,bb in fixed[i+1:]:
  vv=aa.intersect(bb).Volume()
  if vv>1e-5:holder_conflicts.append({'a':na,'b':nb,'intersection_mm3':vv})
print('holder conflicts',holder_conflicts,flush=True)
access_conflicts=[]
for ident,body in fixed:
 for yy in [14,206]:
  for dy in [-10.5,10.5]:
   v=body.intersect(box(87,yy+dy-2,-22,18,4,70)).Volume()
   if v>1e-5:access_conflicts.append({'holder':ident,'motor_side_y':yy,'channel_y':yy+dy,'intersection_mm3':v})
(O/'checks/cabled_holder_access.json').write_text(json.dumps({'holder_conflicts':holder_conflicts,'conflicts':access_conflicts,'m09_new_xy':[252,65],'m08_new_xy':[253,170],'m08_rotation':90,'speaker_new_xy':[256,120],'speaker_rotation':90,'obsolete_foot_holes_removed':True},indent=2),encoding='utf-8')
print('access conflicts',access_conflicts,flush=True)
print('fusing lower cabled draft',flush=True);s=s.fuse(*add).clean()
before_light=s.Volume()
# Deepen the centres of the existing relief pockets, leaving a 2 mm closed skin.
# Existing 12 mm grid ribs and original full-thickness motor/column regions remain.
par=json.loads((B/'source/parameters.json').read_text(encoding='utf-8-sig'))
guards=[cy(x,y,-1,10.3,7) for x,y in posts]
guards += [cy(x,y,-1,8.3,7) for x,y,r in service_holes]
guards += [cy(185,y,-1,14,7) for y in [80.25,139.75]]
for x0,y0,x1,y1 in par['plates'][0]['pockets']:
 tool=cq.Workplane('XY').box(x1-x0-6,y1-y0-6,1.2,centered=False).translate((x0+3,y0+3,1.8)).edges('|Z').fillet(3).val()
 for g in guards:tool=tool.cut(g)
 s=s.cut(tool)
(O/'checks/lightweight.json').write_text(json.dumps({'lower_before_mm3':before_light,'lower_after_mm3':s.Volume(),'saved_mm3':before_light-s.Volume(),'minimum_deck_skin_mm':2,'wall_skin_mm':1.6,'load_validated':False},indent=2),encoding='utf8')
for x,y,r in service_holes:s=s.cut(cy(x,y,-1,r,9))
# Through channels permit T-head insertion from above; exact hardware swept envelope still to verify.
for yy in [14,206]:
 for dy in [-10.5,10.5]:s=s.cut(box(87,yy+dy-2,-22,18,4,28))
# Through-fastener access; counterbores on accessible deck face.
for x,y,z in [(240,90,-H),(240,130,-H),(185,80.25,-TRACKER_DROP),(185,139.75,-TRACKER_DROP)]:
 s=s.cut(cy(x,y,z-1,1.7,7-z));s=s.cut(cy(x,y,2.5,3.4,4))
for x,y in posts:s=s.cut(cy(x,y,-1,1.7,28))
s=s.clean();print('solids',len(s.Solids()),'valid',s.isValid(),flush=True)
assert s.isValid() and len(s.Solids())==1
p=O/'step/LOWER_H41_B1.step';cq.exporters.export(s,str(p));r=cq.importers.importStep(str(p)).val();assert r.isValid() and len(r.Solids())==1
v,f=s.tessellate(.035,.07);m=trimesh.Trimesh([[p.x,p.y,p.z] for p in v],f);m.merge_vertices(digits_vertex=5)
d={'status':'DRAFT_NOT_RELEASED','units':'mm','solid_count':len(s.Solids()),'valid_brep':s.isValid(),'step_roundtrip':True,'mesh_watertight':bool(m.is_watertight),'volume_mm3':s.Volume(),'caster_H_mm':H,'caster_H_provenance':'manual 66.19: nominal Hb61 minus wheel20 = H41; derived not measured','caster_centres':[[240,90],[240,130]],'tracker_centres':[[185,80.25],[185,139.75]],'tracker_probe_projection_user_mm':8,'tracker_drop_mm':TRACKER_DROP,'tracker_drop_provisional':True,'pcb_concept_outline':[125,100],'pcb_origin':[110,60],'pcb_posts':posts,'pcb_seating_z':25,'pcb_not_frozen':False,'not_checked':['actual ground datum','motor wheel full swept envelope','T-head insertion and fastener reach','caster base footprint/hole diameter','printed strength','slicing and supports','battery retaining hardware','speaker and remaining module seats']}
(O/'checks/lower_cabled_draft.json').write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8');print('saved draft',flush=True)
