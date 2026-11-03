from pathlib import Path
import json,math,ast,cadquery as cq
O=Path(__file__).resolve().parents[1];B=O.parent
def box(x,y,z,a,b,c):return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()
def cy(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def get(folder,name):return cq.importers.importStep(str(B/folder/'step'/f'{name}.step')).val()
def overlap(a,b):
 aa=a.BoundingBox();bb=b.BoundingBox()
 if any(getattr(aa,k+'max')<=getattr(bb,k+'min') or getattr(bb,k+'max')<=getattr(aa,k+'min') for k in 'xyz'):return 0.
 return a.intersect(b).Volume()
lower=get(O.name,'LOWER_H41_B1');upper=get(O.name,'UPPER_INTEGRATED').translate((20,15,65))
d=json.loads((B/'mounted-20261031/source/design.json').read_text());fixed=[];moving=[];modules=[];fail=[]
for sp in d['modules']:
 n=sp['id']
 if not n.startswith('M'):continue
 xy=sp['layout_origin'];a=sp['rotation']
 if n=='M09':xy=[252,65]
 if n=='M08':xy=[253,170];a=90
 def place(s):return s.rotate((0,0,0),(0,0,1),a).translate((*xy,5))
 for role in ['body','lid','keeper','detent']:
  sh=place(get('mounted-20261031',n+'_'+role));(fixed if role=='body' else moving).append((n+'_'+role,sh))
 l,w,t=sp['board_size'];z=sp['seat_height']
 modules.append((n,place(box(-l/2,-w/2,z,l,w,t))))
for n,xy in [('P05_BATTERY_cradle',(176,30)),('P06_BUCK_cradle',(202.5,187.5)),('P07_SPEAKER_cradle',(256,120))]:
 sh=get('mounted-20261031',n)
 if n=='P07_SPEAKER_cradle':sh=sh.rotate((0,0,0),(0,0,1),90)
 fixed.append((n,sh.translate((*xy,5))))
for i,(n,a) in enumerate(fixed+moving):
 for m,b in (fixed+moving)[i+1:]:
  if n.split('_')[0]==m.split('_')[0]:continue
  v=overlap(a,b)
  if v>1e-4:fail.append([n,m,v])
 for x,y in [(30,25),(250,25),(30,195),(250,195)]:
  v=overlap(a,cy(x,y,5,5,60))
  if v>1e-4:fail.append([n,'pillar',x,y,v])
 v=overlap(a,upper)
 if v>1e-4:fail.append([n,'upper',v])
pcbpath=B.parents[1]/'current-low-cost/pcb-b/mechanical/SmartBin_B.step'
# KiCad export uses Y negative. Flip Y by a proper 180-degree X rotation would
# also flip components; instead rotate 180 around Z and translate to align holes.
# CAD PCB coordinates 0..125, -100..0 become design 110..235,60..160 by translation.
pcb=cq.importers.importStep(str(pcbpath)).val().translate((110,160,25))
for y in [96,144]:
 stud=cy(256,y,-3.5,3.3,34)
 if overlap(stud,pcb)>1e-4:fail.append(['speaker_stud','PCB',y])
 if overlap(stud,cy(240,90,-41,13,41))>1e-4:fail.append(['speaker_stud','caster_root',y])
v=overlap(lower,pcb)
if v>1e-3:fail.append(['PCB','lower',v])
for n,a in moving:
 v=overlap(a,pcb)
 if v>1e-4:fail.append([n,'PCB',v])
holes=[]
for x,y in [(115,65),(205,65),(115,155),(205,155)]:
 v=overlap(lower,cy(x,y,-1,1.69,28));holes.append({'xy':[x,y],'bore_core_intersection_mm3':v})
 if v>1e-5:fail.append(['blockedPCBhole',x,y,v])
for x,y in [(240,90),(240,130),(185,80.25),(185,139.75)]:
 v=overlap(lower,cy(x,y,-42,1.69,48));holes.append({'xy':[x,y],'bore_core_intersection_mm3':v})
 if v>1e-5:fail.append(['blockedundersidehole',x,y,v])
report={'status':'PASS' if not fail else 'FAIL','conflicts':fail,'holes':holes,
 'pcb_outline_mm':[125,100,1.6],'pcb_bottom_z':25,'pcb_origin':[110,60],
 'pcb_vs_lower_intersection_mm3':overlap(lower,pcb),'upper_offset_xyz':[20,15,65],
 'caster_H':41,'nominal_ground_z':-61,'tracker_board_thickness_assumed_mm':1.6,
 'tracker_probe_protrusion_user_mm':8,'nominal_probe_ground_clearance_mm':8,
 'caster_height_provenance':'Manual 66.19 nominal dimensional chain, not a measured ground height',
 'module_clamps':len(moving),'physical_strength_tested':False,
 'limitations':['connector cable bend radius and actual solder joints require fit check','full motor wheel solid unavailable','load and fatigue not tested']}
(O/'checks/assembly_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
