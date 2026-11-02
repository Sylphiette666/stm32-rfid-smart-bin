"""Four flat-print shell jobs. Dimensions mm; electronics and fasteners need dry fitting."""
from pathlib import Path
import json, math, shutil
import cadquery as cq
import trimesh
from wall_sensor_interfaces import extend

B=Path(__file__).resolve().parents[1];R=B.parents[2]
O=B/'wall-panels-20261102';W=R.parent/'.p2s-wall-panels-20261102'
for p in [O/'parts',O/'step',O/'checks',O/'source',O/'preview',O/'projects']:p.mkdir(parents=True,exist_ok=True)
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h,axis=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*axis))
def union(s,*others):
 for v in others:s=s.fuse(v)
 return s
def hole(s,x,y,z=0,r=1.7,h=20,csk=False):
 s=s.cut(cyl(x,y,z-1,r,h+2))
 if csk:s=s.cut(cq.Solid.makeCone(3.2,r,1.5,cq.Vector(x,y,z)))
 return s
def slot(s,x,y,length,width,z=-1,h=30,angle=0):
 cut=cq.Workplane('XY').center(x,y).slot2D(length,width,angle).extrude(h).translate((0,0,z)).val()
 return s.cut(cut)
parts={};report={};packing={1:[],2:[],3:[],4:[]}
def save(name,s):
 s=s.clean();assert s.isValid() and len(s.Solids())==1,(name,'solid')
 parts[name]=s;cq.exporters.export(s,str(O/'step'/f'{name}.step'))
 bb=s.BoundingBox();flat=s.translate((-bb.xmin,-bb.ymin,-bb.zmin))
 cq.exporters.export(flat,str(O/'parts'/f'{name}.stl'),tolerance=.025,angularTolerance=.08)
 m=trimesh.load_mesh(O/'parts'/f'{name}.stl');assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,name
 report[name]={'size_mm':m.extents.tolist(),'solid_volume_mm3':s.Volume(),'watertight':True,'solid_count':1}
 return s
def pack(plate,name,x,y,rot=0,copy=1):packing[plate].append({'name':name,'x':x,'y':y,'rotation':rot,'copy':copy})

# Local coordinates: u across wall, v upward, z outward. Smooth inside face z=0.
def wall(width,side=False):
 s=box(0,0,0,width,180,1.6)
 for x in [0,width-12]:s=s.fuse(box(x,0,1.6,12,180,1.4))
 for y in [0,174]:s=s.fuse(box(0,y,1.6,width,6,1.4))
 # Shallow outer ribs retain smooth inner face, avoid corner bearing pads.
 for y in [46,90,134]:s=s.fuse(box(12,y,1.6,width-24,2.4,3.4))
 for x in [width/3,2*width/3]:s=s.fuse(box(x,6,1.6,2.4,168,3.4))
 for x in ([9,width-9] if side else [6,width-6]):
  for y in [22,158]:s=hole(s,x,y,h=6,csk=True)
 if side:
  for x in [40,120]:
   s=union(s,box(x-9,0,0,18,3.2,15),box(x-9,0,1.6,3,14,6),box(x+6,0,1.6,3,14,6))
   s=s.cut(cyl(x,-1,10,1.7,6,(0,1,0)))
 return s

left=wall(160,True);right=wall(160,True)
# Continuous outer pads, not guessed sensor holes: a future measured carrier can bolt to these.
for x in [40,120]:
 left=left.fuse(box(x-10,145,1.6,20,20,2.4));right=right.fuse(box(x-10,145,1.6,20,20,2.4))
save('W03_LEFT',left);save('W04_RIGHT',right)
rear=wall(144)
for cx in [40,104]:
 rear=rear.fuse(box(cx-12,164,1.6,24,16,1.4))
 for x in [cx-6,cx+6]:
  rear=hole(rear,x,173,r=1.4,h=8)
  rear=rear.cut(cq.Solid.makeCone(2.6,1.4,1.2,cq.Vector(x,173,0)))
save('W02_REAR',rear)

# External control bay: 144x88 cover, nominal60mm depth, detachable front.
# The 1.6mm back wall separates waste from the electronics.
front=wall(144);bay_y=45;depth=60
for x in [0,141.6]:front=front.fuse(box(x,bay_y,1.6,2.4,88,depth-1.6))
for y in [bay_y,bay_y+85.6]:front=front.fuse(box(0,y,1.6,144,2.4,depth-1.6))
# Reinforce the thin bay skins with intermediate outside ribs.
for x in [0,139.2]:front=front.fuse(box(x,bay_y+42,1.6,4.8,2.4,depth-1.6))
for x in [48,94]:
 for y in [bay_y,bay_y+83.2]:front=front.fuse(box(x,y,1.6,2.4,4.8,depth-1.6))
# Four M3 through bolts run down external corner pillars; heads flush on inside face.
for x in [6,138]:
 for y in [bay_y+6,bay_y+82]:
  front=front.fuse(cyl(x,y,0,5.5,depth))
  front=hole(front,x,y,h=depth+2,csk=True)
# Cable exits through bottom of bay toward lower electronics deck, not into waste.
front=front.cut(box(59,bay_y-1,12,26,8,12))
save('W01_FRONT',front)

cover=box(0,0,0,144,88,2.4)
for x in [6,138]:
 for y in [6,82]:cover=hole(cover,x,y,h=10)
# Display glass clearance; top-left board orientation measured by user.
cover=cover.cut(box(9.5,54.5,-1,25,15,10))
oled_holes=[(11.25,72.25),(32.75,72.25)]
for x,y in oled_holes:
 cover=cover.fuse(cyl(x,y,2.4,3.3,3))
 cover=slot(cover,x,y,4.8,2.8,z=-1,h=12)
# Supporting lower PCB corners, leaving components and glass free.
for x in [9,32.5]:cover=cover.fuse(box(x,47.25,2.4,2.5,3,3))
# Encoder bushing through plate; side pin bank has its own front-facing hood.
cover=hole(cover,65,62,r=3.7,h=12)
cover=cover.cut(box(45,50,-1,10,24,10))
for x,y in [(42,48),(42,76),(57,48),(57,76)]:cover=hole(cover,x,y,r=1.4,h=12)
# Button openings are slotted to permit board position adjustment.
for x in [96,122]:
 cover=slot(cover,x,63,16,12.4,z=-1,h=12)
 for xx in [x-10,x+10]:cover=slot(cover,xx,57,10,2.8,z=-1,h=12,angle=90)
# RC522 antenna window retains a continuous1.2mm membrane (not open).
cover=cover.cut(box(13,8,1.2,62,40,4))
# Adjustable rail screws sit outside board rather than using uncertain tangent holes.
for x in [10,79]:
 for y in [15,40]:cover=slot(cover,x,y,5,2.8,z=-1,h=12)
# Emergency stop reinforced ring and four shallow radial ribs.
cover=cover.fuse(cyl(111,26,2.4,19.5,1.6))
cover=hole(cover,111,26,r=11.3,h=15)
for x,y,w,h in [(83,24,10,3),(129,24,12.4,3),(109,3,3,5),(109,44,3,6)]:cover=cover.fuse(box(x,y,2.4,w,h,1.6))
save('PANEL_COVER',cover)

# External pin hood; flat closed roof on bed, open rim faces panel after assembly.
hood=box(0,0,0,19,32,2)
hood=union(hood,box(0,0,2,2,32,23),box(17,0,2,2,32,23),box(2,0,2,15,2,23),box(2,30,2,15,2,23))
for x in [2,17]:
 for y in [2,30]:
  hood=hood.fuse(cyl(x,y,0,3.8,25));hood=hole(hood,x,y,r=1.4,h=28)
save('ENCODER_PIN_HOOD',hood)

# Button carriers capture board edges with two removable bars; slotted mounting permits adjustment.
def button_carrier():
 s=box(0,0,0,24,25,2)
 s=s.cut(box(6.5,4,-1,11,17,5))
 for x in [2,19]:s=s.fuse(box(x,2,2,3,21,2))
 for x in [2,22]:s=slot(s,x,12.5,10,2.8,z=-1,h=10,angle=90)
 return s
save('BUTTON_CARRIER',button_carrier())
bar=box(0,0,0,24,25,2).cut(box(5.8,2,-1,12.4,21,5))
for x in [2,22]:bar=slot(bar,x,12.5,10,2.8,z=-1,h=8,angle=90)
save('BUTTON_RETAINER',bar)
spacer=cyl(3,3,0,3,8.2).cut(cyl(3,3,-1,1.4,11));save('BUTTON_SPACER',spacer)
# RFID edge rails adjustable on existing cover slots, plus two clamp bars.
rail=box(0,5,0,10,35,2)
rail=rail.fuse(box(7,5,2,3,35,2))
for y in [8,33]:rail=slot(rail,3,y,5,2.8,z=-1,h=8)
save('RFID_EDGE_RAIL',rail)
ret=box(0,5,0,10,35,2)
for y in [8,33]:ret=slot(ret,3,y,5,2.8,z=-1,h=8)
save('RFID_RETAINER',ret)

# External right-angle corner join: two horizontal-axis holes. Prints on12mm end.
angle=union(box(0,0,0,15,3,12),box(12,0,0,3,15,12))
angle=angle.cut(cyl(3,-1,6,1.7,5,(0,1,0))).cut(cyl(11,12,6,1.7,5,(1,0,0)))
save('CORNER_ANGLE',angle)
# Local optional shims provide adjustment without reprinting a wall.
for thick in [1,2]:
 shim=box(0,0,0,8,8,thick);shim=hole(shim,4,4,r=1.4,h=5);save(f'SHIM_{thick}',shim)

# All major wall faces lie flat. Four independent files, with small fittings in unused space.
extras, sensor_instances, interface_features = extend(parts, save, box, cyl, hole, slot, union)
extras+=['BUTTON_RETAINER']*2+['BUTTON_SPACER']*4
pack(1,'W01_FRONT',5,5,90);pack(1,'PANEL_COVER',5,158)
pack(1,'ENCODER_PIN_HOOD',199,8)
for i in range(2):pack(1,'BUTTON_CARRIER',199,52+i*33,copy=i+1)
for i,n in enumerate(['RFID_EDGE_RAIL','RFID_EDGE_RAIL','RFID_RETAINER','RFID_RETAINER']):pack(1,n,155+i*18,158,copy=i+1)
for i in range(6):pack(1,'SHIM_1' if i<3 else 'SHIM_2',155+i*14,218,copy=i+1)
pack(2,'W02_REAR',8,8)
for i in range(4):pack(2,'CORNER_ANGLE',170+i%2*30,15+i//2*30,copy=i+1)
pack(3,'W03_LEFT',8,8);pack(4,'W04_RIGHT',8,8)
for plate in [3,4]:
 for i in range(2):pack(plate,'CORNER_ANGLE',185,15+i*30,copy=i+1)
pack(4,'APPROACH_SHELF',193,85)
extras.remove('APPROACH_SHELF')

# Pack new fittings into the remaining four plates; no wall is divided or tilted.
def footprint(name,rot=0):
 e=report[name]['size_mm'];return (e[1],e[0]) if rot==90 else (e[0],e[1])
copies={}
for name in sorted(extras,key=lambda n:-report[n]['size_mm'][0]*report[n]['size_mm'][1]):
 found=False
 for pid in [2,3,4,1]:
  occupied=[(q['x'],q['y'],*footprint(q['name'],q['rotation'])) for q in packing[pid]]
  for rot in [0,90]:
   w,h=footprint(name,rot)
   for y in range(5, int(251-h)+1,2):
    for x in range(5,int(251-w)+1,2):
     if all(not (x<xx+ww+12 and x+w>xx-12 and y<yy+hh+12 and y+h>yy-12) for xx,yy,ww,hh in occupied):
      copies[name]=copies.get(name,0)+1;pack(pid,name,x,y,rot,copies[name]);found=True;break
    if found:break
   if found:break
  if found:break
 if not found:raise RuntimeError(('Cannot fit four jobs',name))

for plate,items in packing.items():
 bounds=[]
 for item in items:
  m=trimesh.load_mesh(O/'parts'/f"{item['name']}.stl")
  if item['rotation']:m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(item['rotation']),[0,0,1]));m.apply_translation(-m.bounds[0])
  m.apply_translation([item['x'],item['y'],0]);a,b=m.bounds
  assert min(a[:2])>=4 and max(b[:2])<=251,(plate,item['name'],m.bounds)
  for aa,bb,n in bounds:assert not (a[0]<bb[0]+3 and b[0]>aa[0]-3 and a[1]<bb[1]+3 and b[1]>aa[1]-3),(plate,item['name'],n,'packing gap')
  bounds.append((a,b,item['name']))
  item['bounds']=m.bounds.tolist()
save_report={'status':'CAD_CHECKED_PENDING_SLICE_AND_DRY_FIT','parts':report,'plates':packing,
 'shell_outer_nominal_mm':[160,150,180],'skin_mm':1.6,'ribs_max_mm':5,'corner_bearing_mm':3,
 'control_bay_depth_mm':60,'emergency_cutout_mm':22.6,'emergency_mount_land_mm':4,
 'rear_depth_with_wires_verified':False,'sensor_specific_mounts_complete':True,
 'sensor_instances':sensor_instances,'interface_features':interface_features,
 'bottom':'Existing P02 upper platform continuous face UP supports bare bin; no new liner or bag. Surface beneath160x150 footprint verified solid at localZ3..5; not watertight. Four jobs exclude moving lid.',
 'hinge_hole_centres':[[34,173],[46,173],[98,173],[110,173]],
 'physical_print_test':False,'load_rating':None,'all_walls_flat':True}
(O/'checks/design.json').write_text(json.dumps(save_report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
measure=json.loads((W/'measurements.json').read_text(encoding='utf-8'));measure['emergency_stop_product_drawing'].update(mounting_neck_diameter_user_measured=22,latest_dimension_reference_confirmed=True)
(O/'source/measurements.json').write_text(json.dumps(measure,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copy2(W/'github_support_source.json',O/'source/github_support_source.json')
print(json.dumps({'parts':len(parts),'plate_counts':{p:len(v) for p,v in packing.items()}},ensure_ascii=False))
