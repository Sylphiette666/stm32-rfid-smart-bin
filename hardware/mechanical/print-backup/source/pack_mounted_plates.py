"""Pack every manufactured part on two beds, all independently touching Z=0.

Small flat latch parts may occupy an open holder/window; these are separate
objects on the bed. Low fixtures may occupy the cradle's empty bed cells below
the inclined base. Exact CAD intersections are checked after rectangle packing.
"""
from pathlib import Path
import json,math,random,zipfile,hashlib
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mounted-20261031'
DESIGN=json.loads((OUT/'source/design.json').read_text(encoding='utf-8'))
PARTS={p['id']:p for p in DESIGN['parts']}
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
    return cq.importers.importStep(str(OUT/p['step'])).val().translate(tuple(p['normalising_translation']))
def rotated(s,angle):
    s=s.rotate((0,0,0),(0,0,1),angle);b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,0))
def matrix(w,h,angle=0,xy=(0,0)):
    a=math.radians(angle);c=round(math.cos(a));s=round(math.sin(a))
    points=np.array([[0,0],[w,0],[0,h],[w,h]])@np.array([[c,s],[-s,c]])
    shift=-points.min(axis=0)+np.array(xy)
    result=np.eye(4);result[:2,:2]=[[c,-s],[s,c]];result[:2,3]=shift
    return result

# Load all normalized CAD once for later exact nesting/intersection checks.
CAD={p:flat_cad(p) for p in PARTS}
NESTED={};USED=set();nest_audit=[]
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

top=[p for p in PARTS.values() if p['id'] not in USED]
tray_shape=cq.importers.importStep(str(ROOT/'step/P04_servo_adjustable_tray.step')).val()
tb=tray_shape.BoundingBox();tray_shape=tray_shape.translate((-tb.xmin,-tb.ymin,-tb.zmin))
top.append({'id':'P04_TRAY','print_extents':[80,40,5]})
CAD['P04_TRAY']=tray_shape

# Free rectangles are bed cells, not simple projections of the inclined board.
# Tall items shift right until they have >=3 mm below the board's lower plane.
REGIONS=[
 {'name':'A_cell1','plate':1,'rect':[20,25,179,111],'under_base':True},
 {'name':'A_cell2','plate':1,'rect':[20,125,179,211],'under_base':True},
 # The frame's furthest solid foot ends at X=187. The board only reaches
 # X=189.8 near Z=214, far above every <=31.4-mm independent fixture.
 {'name':'A_right','plate':1,'rect':[190,3,253,253]},
 # This overlaps A_right deliberately; every placement subtracts its occupied
 # rectangle from ALL regions on its plate, as in ordinary MaxRects packing.
 {'name':'A_back','plate':1,'rect':[3,229.5,253,253]},
 {'name':'B_right','plate':2,'rect':[200,194,255,255]},
]

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

def attempt(seed,gap):
    rng=random.Random(seed)
    if seed%4==0:items=sorted(top,key=lambda p:-p['print_extents'][0]*p['print_extents'][1])
    elif seed%4==1:items=sorted(top,key=lambda p:-max(p['print_extents'][:2]))
    else:items=sorted(top,key=lambda p:-p['print_extents'][0]*p['print_extents'][1]*rng.uniform(.35,1.65))
    spaces=[dict(r,free=[r['rect'][:]]) for r in REGIONS];result=[]
    for item in items:
        w0,h0,height=item['print_extents'];choices=[]
        for i,space in enumerate(spaces):
            need_x=6+5*math.sin(math.radians(50))+(height+3)/math.tan(math.radians(50)) if space.get('under_base') else 0
            for r in space['free']:
                for angle,w,h in [(0,w0,h0),(90,h0,w0)]:
                    left=max(r[0],need_x-gap/2)
                    for x in {left,r[2]-w-gap}:
                      if x<left-1e-6:continue
                      for y in {r[1],r[3]-h-gap}:
                        if y<r[1]-1e-6 or x+w+gap>r[2]+1e-6 or y+h+gap>r[3]+1e-6:continue
                        a=r[2]-left-w-gap;b=r[3]-r[1]-h-gap
                        if seed%3==0:score=(min(a,b),max(a,b),x+y*.1)
                        elif seed%3==1:score=((r[2]-r[0])*(r[3]-r[1])-(w+gap)*(h+gap),min(a,b),y)
                        else:score=(y+h,x+w,min(a,b))
                        choices.append((score,i,x,y,angle,w,h))
        if not choices:return None
        _,i,x,y,angle,w,h=min(choices)
        occupied=[x,y,x+w+gap,y+h+gap]
        for target in spaces:
            if target['plate']==spaces[i]['plate']:
                target['free']=split_free(target['free'],occupied)
        result.append({'id':item['id'],'plate':spaces[i]['plate'],'region':spaces[i]['name'],
                       'xy':[x+gap/2,y+gap/2],'angle':angle,'size':[w,h,height]})
    return result

packing=None
for gap in [2.0,1.6]:
    for seed in range(1500):
        packing=attempt(seed,gap)
        if packing:break
    if packing:break
assert packing is not None,'No two-bed packing found; adjust regions or nest additional low parts.'
(OUT/'checks/packing_plan.json').write_text(json.dumps({'phase':'rectangle_plan_only',
    'gap_mm':gap,'seed':seed,'top_level':packing,'nested':nest_audit},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Build a wide one-piece printing cradle around the revised but unsplit base.
base=cq.importers.importStep(str(OUT/'step/P01_MOUNTED_BASE.step')).val()
base=base.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,1,0),-50).translate((6,228,5*math.cos(math.radians(50))))
surface=lambda z:5*math.sin(math.radians(50))+z/math.tan(math.radians(50))
from shapely.geometry import Polygon
def prism_xz(points,y,width):return cq.Workplane('XZ',origin=(0,y+width/2,0)).polyline(points).close().extrude(width).val()
braces=[]
for y in [10,110,210]:
    outer=Polygon([(surface(0)+2,0),(181,0),(surface(205)+2,205)])
    inner=outer.buffer(-4,join_style=2)
    frame=prism_xz(list(outer.exterior.coords)[:-1],y,3.2).cut(prism_xz(list(inner.exterior.coords)[:-1],y,4))
    braces.extend([frame,block(surface(0)+2,y-6,0,181-surface(0)-2,12,3.2)])
    for z in range(0,201,20):
        braces.append(prism_xz([(surface(z)-.2,z),(surface(z)+2.2,z),
            (surface(z+3.6)+2.2,z+3.6),(surface(z+3.6)-.2,z+3.6)],y,1.6))
for x in [surface(0)+2,175]:braces.append(block(x,2,0,6,216,3.2))
braces.append(block(5*math.sin(math.radians(50))-.2,2,0,5,216,.48))
cradle=braces[0].fuse(*braces[1:]).clean().translate((6,8,0))
supported=base.fuse(cradle).clean();assert supported.isValid() and len(supported.Solids())==1
cq.exporters.export(supported,str(OUT/'step/P01_PRINT_WITH_CRADLE.step'))
cq.exporters.export(base,str(OUT/'step/P01_PRINT_BOARD_ONLY.step'))
cq.exporters.export(cradle,str(OUT/'step/P01_PRINT_CRADLE_ONLY.step'))

stand=cq.importers.importStep(str(ROOT/'step/P03_servo_adjustable_stand.step')).val()
stand=stand.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,0,1),90)
b=stand.BoundingBox();stand=stand.translate((8-b.xmin,194-b.ymin,-b.zmin))
upper=cq.importers.importStep(str(ROOT/'step/P02_light.step')).val().rotate((0,0,0),(1,0,0),180).translate((8,192,5))

SCENES={1:[('P01_BASE_WITH_CRADLE',supported,'#477f9f')],2:[('P02_UPPER',upper,'#4c9a97'),('P03_STAND',stand,'#bc8d5e')]}
placements=[]
for record in packing:
    ident=record['id'];shape=CAD[ident]
    transformed=rotated(shape,record['angle']).translate((*record['xy'],0))
    colour={'body':'#a1aab1','lid':'#dba052','keeper':'#3d7fb8','detent':'#69a28d'}.get(PARTS.get(ident,{}).get('role'),'#9a87b4')
    SCENES[record['plate']].append((ident,transformed,colour));placements.append(record)
    if ident in NESTED:
        parent_ext=PARTS[ident]['print_extents']
        pm=matrix(*parent_ext[:2],record['angle'],record['xy'])
        for child in NESTED[ident]:
            ci=child['id'];cs=CAD[ci];ce=PARTS[ci]['print_extents']
            cm=matrix(*ce[:2],child['angle'],child['xy']);combined=pm@cm
            # Proper rigid transform retains flat Z=0 for each nested child.
            # Construct an actual rigid gp_Trsf via rotate/translate. Feeding
            # gp_GTrsf coefficients through Matrix can retain an "Other" form
            # flag and fail Trsf() even for a numerically orthogonal matrix.
            assert np.allclose(combined[:3,:3].T@combined[:3,:3],np.eye(3),atol=1e-9)
            ca=math.degrees(math.atan2(combined[1,0],combined[0,0]))
            transformed=cs.rotate((0,0,0),(0,0,1),ca).translate(tuple(combined[:3,3]))
            role=PARTS[ci]['role'];colour={'keeper':'#3d7fb8','detent':'#69a28d'}[role]
            SCENES[record['plate']].append((ci,transformed,colour))
            b=transformed.BoundingBox();placements.append({'id':ci,'plate':record['plate'],'nested_inside':ident,
                'bounds':bbox(transformed),'bed_z':b.zmin})

expected=set(PARTS)|{'P04_TRAY'}
assert {q['id'] for q in placements}==expected
qa=[];meshes={}
# A revised packing may move an accessory between beds. Remove only stale
# generated bed meshes, so previews and the CSV cannot include an old copy.
expected_meshes={f'{ident}_bed{plate}.stl' for plate,items in SCENES.items() for ident,_,_ in items}
for stale in (OUT/'geometry').glob('*_bed[12].stl'):
    if stale.name not in expected_meshes:stale.unlink()
for plate,items in SCENES.items():
    converted=[]
    for ident,shape,color in items:
        b=shape.BoundingBox();assert abs(b.zmin)<1e-5,(ident,'not on bed')
        assert min(b.xmin,b.ymin)>=.99 and max(b.xmax,b.ymax)<=255.01,(ident,bbox(shape))
        if plate==1 and ident!='P01_BASE_WITH_CRADLE':
            assert shape.intersect(supported).Volume()<1e-5,(ident,'cradle collision')
        path=OUT/'geometry'/(ident+'_bed'+str(plate)+'.stl')
        cq.exporters.export(shape,str(path),tolerance=.018,angularTolerance=.05)
        m=trimesh.load_mesh(path);m.merge_vertices(digits_vertex=4)
        m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
        assert m.is_watertight and m.is_winding_consistent,(ident,'mesh')
        assert sum(s.volume>0 for s in m.split(only_watertight=False))==1,ident
        m.export(path);converted.append((ident,m));meshes[ident]=m
    for i,(na,a,ca) in enumerate(items):
        for nb,b,cb in items[i+1:]:
            aa=a.BoundingBox();bb=b.BoundingBox()
            if aa.xmax<bb.xmin or bb.xmax<aa.xmin or aa.ymax<bb.ymin or bb.ymax<aa.ymin:continue
            assert a.intersect(b).Volume()<1e-5,(na,nb,'physical intersection')
    write3mf(converted,OUT/'geometry'/f'PLATE_{plate}_GEOMETRY.3mf')
    qa.append({'plate':plate,'objects':len(items),'every_object_directly_on_bed':True,
               'all_meshes_watertight':True,'physical_intersections':0})

report={'status':'PASS','plates':qa,'placements':placements,'nested_low_parts':nest_audit,
 'rectangle_gap_mm':gap,'successful_seed':seed,'base_angle_degrees':50,
 'base_and_upper_are_whole_parts':True,'total_objects':sum(p['objects'] for p in qa),
 'every_part_directly_on_bed':True,'overlapping_projections_but_no_solid_contact':True,
 'packing_regions':REGIONS,'physical_print_test':False,
 'plate2_uses_wrapping_detection_area':True,
 'wrapping_detection_must_be_disabled':True,
 'wrapping_area_evidence':'Official P2S bed_exclude_area empty; PrintConfig get_bed_shape_with_excluded_area only subtracts wrapping_exclude_area when enable_wrapping_detection is true.'}
(OUT/'checks/packing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
DESIGN['status']='two_plate_geometry_validated_slicing_pending'
DESIGN['print_notes'].extend(['所有小件各自贴床，有些位于卡座/压框镂空区或斜板下空区，不能自动排布。','第二盘使用后侧检测区，保留工程的喷嘴缠料检测关闭；这与相机炒面检测不同。'])
(OUT/'source/design.json').write_text(json.dumps(DESIGN,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'plates':qa,'nested_parts':len(nest_audit),'gap':gap,'seed':seed,'total_objects':report['total_objects']},ensure_ascii=False),flush=True)
