"""Three flat beds, retained clamp nesting and independently bed-contacting parts."""
from pathlib import Path
import json,math,random,zipfile,csv
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'flat-split-20261101'
DESIGN=json.loads((OUT/'source/design.json').read_text(encoding='utf-8'))
PARTS={p['id']:p for p in DESIGN['parts']}
for i in range(1,4):PARTS[f'JOIN_BRIDGE_{i}']=dict(PARTS['P01_SPLICE_BRIDGE'],id=f'JOIN_BRIDGE_{i}')
del PARTS['P01_SPLICE_BRIDGE']

def write3mf(items,path):
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',ns)
    tag=lambda s:f'{{{ns}}}{s}'
    root=ET.Element(tag('model'),{'unit':'millimeter'})
    resources=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'))
    for i,(name,m) in enumerate(items,1):
        obj=ET.SubElement(resources,tag('object'),{'id':str(i),'name':name,'type':'model'})
        mesh=ET.SubElement(obj,tag('mesh'));vertices=ET.SubElement(mesh,tag('vertices'))
        triangles=ET.SubElement(mesh,tag('triangles'))
        for v in m.vertices:
            ET.SubElement(vertices,tag('vertex'),dict(zip(['x','y','z'],[f'{n:.8f}' for n in v])))
        for f in m.faces:
            ET.SubElement(triangles,tag('triangle'),dict(zip(['v1','v2','v3'],[str(n) for n in f])))
        ET.SubElement(build,tag('item'),{'objectid':str(i)})
    with zipfile.ZipFile(ROOT/'3mf/P2S/P01_light_upright45.3mf') as template,zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in ['[Content_Types].xml','_rels/.rels']:z.writestr(f,template.read(f))
        z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))

def block(x,y,z,a,b,c):return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()

def bbox(s):
    b=s.BoundingBox();return [[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]]

def flat_cad(ident):
    p=PARTS[ident]
    s=cq.importers.importStep(str(OUT/p['step'])).val()
    if ident in ['P01_REAR_HALF','P01_FRONT_HALF','P02_UPPER']:s=s.rotate((0,0,0),(1,0,0),180)
    elif ident=='P03_STAND':s=s.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,0,1),90)
    b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

def rotated(s,angle):
    s=s.rotate((0,0,0),(0,0,1),angle);b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,0))

def matrix(w,h,angle=0,xy=(0,0)):
    a=math.radians(angle);c=round(math.cos(a));s=round(math.sin(a))
    points=np.array([[0,0],[w,0],[0,h],[w,h]])@np.array([[c,s],[-s,c]])
    shift=-points.min(axis=0)+np.array(xy)
    result=np.eye(4);result[:2,:2]=[[c,-s],[s,c]];result[:2,3]=shift
    return result

def try_nest(child,parent,locations):
    if child in USED:return True
    shape=CAD[child];ext=PARTS[child]['print_extents'];host=CAD[parent]
    for angle,cx,cy in locations:
        candidate=rotated(shape,angle);b=candidate.BoundingBox()
        candidate=candidate.translate((cx-b.xlen/2,cy-b.ylen/2,0))
        # A nested part must stay within the parent's allocated rectangle and
        # must lift out vertically; a low part below an overhanging ledge is
        # not a removable nested print merely because the solids do not touch.
        cb=candidate.BoundingBox();hb=host.BoundingBox()
        if cb.xmin<hb.xmin+.6 or cb.ymin<hb.ymin+.6 or cb.xmax>hb.xmax-.6 or cb.ymax>hb.ymax-.6:continue
        removal=block(cb.xmin,cb.ymin,cb.zmin+.02,cb.xlen,cb.ylen,hb.zmax+1)
        if removal.intersect(host).Volume()>1e-6:continue
        if candidate.intersect(host).Volume()>1e-6:continue
        if candidate.distance(host)<.8:continue
        collision=False
        for other in NESTED.get(parent,[]):
            if candidate.intersect(other['cad']).Volume()>1e-6 or candidate.distance(other['cad'])<1.2:
                collision=True;break
        if collision:continue
        b=candidate.BoundingBox()
        NESTED.setdefault(parent,[]).append({'id':child,'angle':angle,'xy':[b.xmin,b.ymin],'cad':candidate})
        USED.add(child);nest_audit.append({'part':child,'inside':parent,'angle':angle,
            'local_xy':[b.xmin,b.ymin],'bed_z':b.zmin,'minimum_parent_gap_mm':candidate.distance(host),
            'vertical_removal_clear':True})
        return True
    return False

def contains(a,b):return a[0]<=b[0]+1e-8 and a[1]<=b[1]+1e-8 and a[2]>=b[2]-1e-8 and a[3]>=b[3]-1e-8

def overlaps(a,b):return a[0]<b[2]-1e-8 and a[2]>b[0]+1e-8 and a[1]<b[3]-1e-8 and a[3]>b[1]+1e-8

def split_free(free,used):
    out=[]
    for r in free:
        if not overlaps(r,used):out.append(r);continue
        if used[0]>r[0]:out.append([r[0],r[1],used[0],r[3]])
        if used[2]<r[2]:out.append([used[2],r[1],r[2],r[3]])
        if used[1]>r[1]:out.append([r[0],r[1],r[2],used[1]])
        if used[3]<r[3]:out.append([r[0],used[3],r[2],r[3]])
    clean=[]
    for i,r in enumerate(out):
        if r[2]-r[0]<1 or r[3]-r[1]<1:continue
        if any(i!=j and contains(s,r) and (s!=r or j<i) for j,s in enumerate(out)):continue
        clean.append(r)
    return clean
CAD={p:flat_cad(p) for p in PARTS}
NESTED={};USED=set();nest_audit=[]
for module in [f'M{i:02d}' for i in range(1,10)]:
    parent=module+'_body';shift=PARTS[parent]['normalising_translation'];cx,cy=shift[:2]
    # Large/medium PCB pin windows hold both low parts without supporting them.
    det=module+'_detent';keep=module+'_keeper'
    success=try_nest(det,parent,[(0,cx,cy-4.5),(0,cx,cy),(90,cx-5,cy)])
    if success:
        try_nest(keep,parent,[(90,cx,cy+4.7),(90,cx+10,cy),(0,cx+8,cy)])
    else:
        try_nest(keep,parent,[(90,cx,cy),(0,cx,cy),(90,cx+2,cy)])
    # A lid window is also clear down to the actual bed, never a support surface.
    if det not in USED:
        lid=module+'_lid';sx,sy=PARTS[lid]['normalising_translation'][:2]
        try_nest(det,lid,[(0,sx,sy),(0,sx,sy-1),(90,sx,sy)])

# The open centre of the battery floor takes remaining small pieces/shims.
bat_parent='P05_BATTERY_cradle';bcx,bcy=PARTS[bat_parent]['normalising_translation'][:2]
for child in ['BAT_L_keeper','BAT_R_keeper','BAT_L_detent','BAT_R_detent']:
    try_nest(child,bat_parent,[(angle,bcx+dx,bcy+dy)
             for angle in [0,90] for dy in [-11,-3,5,12] for dx in [-8,8,0]])

FIXED={1:[('P01_REAR_HALF',90,(8,8))],2:[('P01_FRONT_HALF',90,(8,8))],3:[('P02_UPPER',0,(8,2)),('P03_STAND',0,(8,194)),('P07_SPEAKER_cradle',90,(200.8,194.8))]}
fixed_ids={p[0] for parts in FIXED.values() for p in parts}
top=[p for p in PARTS.values() if p['id'] not in USED|fixed_ids]
REGIONS=[{'name':'A_back','plate':1,'rect':[3,158,253,253]}, {'name':'B_back','plate':2,'rect':[3,155,253,253]}, {'name':'A_side','plate':1,'rect':[234,3,253,155]}, {'name':'B_side','plate':2,'rect':[234,3,253,152]}]
def attempt(seed,gap):
 rng=random.Random(seed)
 items=sorted(top,key=lambda p:-p['print_extents'][0]*p['print_extents'][1]*(1 if seed%3==0 else rng.uniform(.5,1.5)))
 spaces=[dict(r,free=[r['rect'][:]]) for r in REGIONS];result=[]
 for item in items:
  w0,h0,height=item['print_extents'];choices=[]
  for i,sp in enumerate(spaces):
   for r in sp['free']:
    for angle,w,h in [(0,w0,h0),(90,h0,w0)]:
     x,y=r[:2]
     if x+w+gap>r[2]+1e-6 or y+h+gap>r[3]+1e-6:continue
     a=r[2]-x-w-gap;b=r[3]-y-h-gap
     score=(min(a,b),max(a,b),x+y*.1) if seed%2 else ((r[2]-r[0])*(r[3]-r[1])-(w+gap)*(h+gap),min(a,b),y)
     choices.append((score,i,x,y,angle,w,h))
  if not choices:return None
  _,i,x,y,angle,w,h=min(choices)
  for target in spaces:
   if target['plate']==spaces[i]['plate']:target['free']=split_free(target['free'],[x,y,x+w+gap,y+h+gap])
  result.append({'id':item['id'],'plate':spaces[i]['plate'],'xy':[x+gap/2,y+gap/2],'angle':angle,'size':[w,h,height]})
 return result
packing=None
for gap in [3.0,2.4,2.0]:
 for seed in range(1200):
  packing=attempt(seed,gap)
  if packing:break
 if packing:break
assert packing is not None,'No three-bed packing; keep whole objects, never shrink.'
SCENES={1:[],2:[],3:[]};placements=[]
for bed,parts in FIXED.items():
 for ident,angle,xy in parts:packing.append({'id':ident,'plate':bed,'angle':angle,'xy':xy,'fixed':True})
for rec in packing:
 ident=rec['id'];shape=rotated(CAD[ident],rec['angle']).translate((*rec['xy'],0))
 SCENES[rec['plate']].append((ident,shape));placements.append(dict(rec,bounds=bbox(shape)))
 if ident in NESTED:
  pm=matrix(*PARTS[ident]['print_extents'][:2],rec['angle'],rec['xy'])
  for child in NESTED[ident]:
   ci=child['id'];cm=matrix(*PARTS[ci]['print_extents'][:2],child['angle'],child['xy']);m=pm@cm
   ca=math.degrees(math.atan2(m[1,0],m[0,0]))
   s=CAD[ci].rotate((0,0,0),(0,0,1),ca).translate(tuple(m[:3,3]))
   SCENES[rec['plate']].append((ci,s));placements.append({'id':ci,'plate':rec['plate'],'nested_inside':ident,'bounds':bbox(s)})
assert set(p['id'] for p in placements)==set(PARTS)
qa=[]
for bed,items in SCENES.items():
 converted=[]
 for ident,s in items:
  b=s.BoundingBox();assert abs(b.zmin)<1e-5 and min(b.xmin,b.ymin)>=.99 and max(b.xmax,b.ymax)<=255.01,(ident,bbox(s))
  file=OUT/'geometry'/f'{ident}_bed{bed}.stl';cq.exporters.export(s,str(file),tolerance=.018,angularTolerance=.05)
  m=trimesh.load_mesh(file);m.merge_vertices(digits_vertex=4);m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
  assert m.is_watertight and m.is_winding_consistent and sum(q.volume>0 for q in m.split(only_watertight=False))==1,ident
  m.export(file);converted.append((ident,m))
 for i,(na,a) in enumerate(items):
  aa=a.BoundingBox()
  for nb,b in items[i+1:]:
   bb=b.BoundingBox()
   if aa.xmax<bb.xmin or bb.xmax<aa.xmin or aa.ymax<bb.ymin or bb.ymax<aa.ymin:continue
   assert a.intersect(b).Volume()<1e-5,(na,nb)
 write3mf(converted,OUT/'geometry'/f'PLATE_{bed}_GEOMETRY.3mf')
 qa.append({'plate':bed,'objects':len(items),'all_objects_directly_on_bed':True,'all_meshes_watertight':True,'solid_intersections':0,'maximum_height_mm':max(s.BoundingBox().zmax for _,s in items)})
report={'status':'PASS','plates':qa,'placements':placements,'nested_low_parts':nest_audit,'gap_mm':gap,'seed':seed,'total_objects':len(placements),'print_jobs':3,'base_flat_halves':True,'upper_flat_one_piece':True,'physical_print_test':False}
(OUT/'checks/packing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (OUT/'source/parts_index.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['id','plate','x_min_mm','y_min_mm','z_max_mm','nested_inside'])
 for r in sorted(placements,key=lambda r:(r['plate'],r['id'])):writer.writerow([r['id'],r['plate'],*r['bounds'][0][:2],r['bounds'][1][2],r.get('nested_inside','')])
print(json.dumps({k:v for k,v in report.items() if k not in ['placements','nested_low_parts']},ensure_ascii=False),flush=True)
