"""Existing-hole load spreaders. Preserve the confirmed D06 motor seats as separate parts."""
from pathlib import Path
import json, math, hashlib
import cadquery as cq
import trimesh
import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon

B = Path(__file__).resolve().parents[1]
R = B.parents[2]
O = B / 'motor-existing-holes-20261102'
for sub in ['parts', 'step', 'checks', 'preview', 'source']:
    (O / sub).mkdir(parents=True, exist_ok=True)

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def cylinder(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def prism(poly,z,h):
    return cq.Workplane('XY').polyline(list(poly.exterior.coords)[:-1]).close().extrude(h).translate((0,0,z)).val()

def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if aa.xmax<=bb.xmin or bb.xmax<=aa.xmin or aa.ymax<=bb.ymin or bb.ymax<=aa.ymin or aa.zmax<=bb.zmin or bb.zmax<=aa.zmin:
        return 0.0
    return a.intersect(b).Volume()

d=json.loads((B/'flat-split-20261101/source/design.json').read_text(encoding='utf-8-sig'))
old=json.loads((B/'motor-adapter-clearance2-20261102/checks/design.json').read_text(encoding='utf-8-sig'))
existing=d['mount_holes']+[{'name':'P01_splice','xy':p,'diameter':3.4} for p in d['joint']['new_holes']]
selected={
 'LEFT': [('M05_foot',[46.5,28]),('M05_foot',[68.5,28]),('M09_foot',[86,36.5]),('M09_foot',[108,36.5]),('M01_foot',[57,52])],
 'RIGHT':[('P01_splice',[126,144]),('P01_splice',[150,144]),('M08_foot',[131.5,206]),('BUCK_base',[189.5,187.5])],
}
baseparts=[cq.importers.importStep(str(B/'flat-split-20261101/step'/f'P01_{p}_HALF.step')).val() for p in ['REAR','FRONT']]
base=baseparts[0].fuse(baseparts[1])
models={}; reports={}
for name, anchors in selected.items():
    v=old['variants'][name]; cx,cy=v['centre']
    seat=cq.importers.importStep(str(B/'motor-adapter-clearance2-20261102/step'/f'D06_ADAPTER_{name}.step')).val()
    # The STEP seat is centered at the previously published slot datum, not normalized STL coordinates.
    original_holes=[(cx+x,cy+y) for x,y in v['holes']]
    support=[(cx-14,cy-13),(cx+14,cy-13),(cx-14,cy+13),(cx+14,cy+13)]
    outline=MultiPoint([xy for _,xy in anchors]+original_holes+support).convex_hull.buffer(8,resolution=12)
    # Preserve the confirmed wheel-facing envelope. The extension is entirely inboard.
    wheel_limit=cy-13 if name=='LEFT' else cy+13
    clip=Polygon([(0,wheel_limit),(280,wheel_limit),(280,220),(0,220)]) if name=='LEFT' else Polygon([(0,0),(280,0),(280,wheel_limit),(0,wheel_limit)])
    outline=outline.intersection(clip)
    carrier=prism(outline,0,16)
    bridge_reliefs=[]
    for bx,by in d['joint']['bridge_centres']:
        cutpoly=Polygon([(bx-20.5,by-12.5),(bx+20.5,by-12.5),(bx+20.5,by+12.5),(bx-20.5,by+12.5)])
        if outline.intersects(cutpoly):
            # Exact 5mm seating depth at splice anchors; only XY has 0.5mm insertion clearance.
            carrier=carrier.cut(prism(cutpoly,11,6))
            bridge_reliefs.append({'centre':[bx,by],'size':[41,25],'depth':5})
    for ref,xy in anchors:
        assert any(h['name']==ref and math.dist(xy,h['xy'])<1e-7 for h in existing), (ref,xy)
        # Only the original deck holes are used; landing on full-thickness original material is checked.
        land=cylinder(*xy,0,3.8,5).cut(cylinder(*xy,-.1,1.70001,5.2))
        assert land.cut(base).Volume()<1e-5,(name,ref,xy,'not full 5mm landing')
        carrier=carrier.cut(cylinder(*xy,-1,1.7,18))
    # Top-loading captive DIN985 nuts; their screw tips remain below the deck mating face.
    for xy in original_holes:
        carrier=carrier.cut(cylinder(*xy,-1,1.7,18))
        hx=cq.Workplane('XY').polygon(6,6/math.cos(math.pi/6)).extrude(7).translate((*xy,10)).val()
        carrier=carrier.cut(hx)
    shared=[xy for _,xy in anchors]
    relief=[]
    for h in existing:
        xy=h['xy']
        if any(math.dist(xy,p)<1e-6 for p in shared):continue
        if outline.intersects(Point(*xy).buffer(4)):
            depth=12 if h['name']=='P01_splice' else 8
            carrier=carrier.cut(cylinder(*xy,16-depth,4,depth+1))
            relief.append({'source':h['name'],'xy':xy,'diameter':8,'depth_from_top':depth})
    carrier=carrier.clean()
    assert carrier.isValid() and len(carrier.Solids())==1, name
    seatglobal=seat.translate((cx,cy,-9))
    assert overlap(carrier,seatglobal)<1e-6
    bridge=cq.importers.importStep(str(B/'flat-split-20261101/step/P01_SPLICE_BRIDGE.step')).val()
    for bx,by in d['joint']['bridge_centres']:
        assembled_bridge=bridge.translate((bx,by,11))
        assert overlap(carrier,assembled_bridge)<1e-6,(name,'bridge collision',bx,by)
    for h in existing:
        if h['name']!='P01_splice' or any(math.dist(h['xy'],xy)<1e-6 for xy in shared):continue
        # Original M3x16 splice bolt ends 10.5mm below the deck; keep a 0.5mm margin.
        xy=h['xy']
        assert overlap(carrier,cylinder(*xy,5,3.3,6))<1e-6,(name,'splice nut collision',xy)
    # Fastener envelopes use actual final screw stacks, including exposed tips and socket head envelopes.
    for ref,xy in anchors:
        foot=0 if ref=='P01_splice' else (3.2 if ref=='BUCK_base' else 2.4)
        upper=16+5+foot+.5
        end=upper-30
        shank=cylinder(*xy,end,1.5,30)
        nut=cylinder(*xy,-4.5,3.3,4)
        washer=cylinder(*xy,-.5,3,.5)
        assert overlap(shank,seatglobal)<1e-6,(name,xy,'shared screw hits motor seat')
        assert overlap(nut,seatglobal)<1e-6,(name,xy,'shared nut hits motor seat')
        assert overlap(washer,seatglobal)<1e-6,(name,xy,'shared washer hits motor seat')
    for xy in original_holes:
        # M3x25 from below the retained 9mm seat, with 0.5mm head washer.
        screw_end=-9-.5+25
        assert abs(screw_end-15.5)<1e-6 and 16-screw_end>=.5-1e-7
        assert screw_end-(10+.5+4)>=1-1e-7
    # STEP files use the chassis assembly datum: original deck underside Z=0.
    cq.exporters.export(carrier.translate((0,0,-16)),str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step'))
    cq.exporters.export(seatglobal.translate((0,0,-16)),str(O/'step'/f'D06_SEAT_{name}_ASSEMBLY.step'))
    # Flat underside on bed; all captive-nut and hardware recesses face upward and stay open.
    printed=carrier
    bb=printed.BoundingBox(); shift=(-bb.xmin,-bb.ymin,-bb.zmin)
    printed=printed.translate(shift)
    cq.exporters.export(printed,str(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl'),tolerance=.025,angularTolerance=.05)
    mesh=trimesh.load_mesh(O/'parts'/f'D06_CARRIER_{name}_PRINT.stl')
    # Clean only numerical seam duplicates; do not repair geometry after export.
    mesh.merge_vertices(digits_vertex=5)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,name
    models[name]=mesh
    # Use a global assembly for interference and inspection; it does not alter the chassis.
    compound=cq.Compound.makeCompound([carrier.translate((0,0,-16)),seatglobal.translate((0,0,-16))])
    cq.exporters.export(compound,str(O/'step'/f'D06_STACK_{name}_ASSEMBLY.step'))
    reports[name]={'anchors':[{'source':r,'xy':xy,'diameter':3.4} for r,xy in anchors],
      'retained_motor_seat_datum':v['centre'],'seat_connection_holes':[list(p) for p in original_holes],
      'outline':list(outline.exterior.coords),'wheel_facing_limit_y':wheel_limit,
      'body_thickness':16,'top_reliefs':relief,'splice_clearance_recesses':bridge_reliefs,'volume_mm3':carrier.Volume(),
      'print_extents':mesh.extents.tolist(),'print_normalizing_translation':shift,
      'shape_valid':True,'watertight_mesh':True,'shared_fasteners_clear_seat':True,'splice_and_original_splice_nuts_clear':True,
      'motor_seat_source_sha256':hashlib.sha256((B/'motor-adapter-clearance2-20261102/step'/f'D06_ADAPTER_{name}.step').read_bytes()).hexdigest()}
    print(name,mesh.extents.tolist(),round(carrier.Volume()),'anchors',len(anchors),'reliefs',len(relief),flush=True)

report={'status':'DESIGN_GEOMETRY_CHECKED_PHYSICAL_LOAD_NOT_TESTED','variants':reports,
 'new_chassis_holes':0,'shared_existing_holes':9,'carrier_thickness_mm':16,
 'retained_seat_height_mm':9,'stack_height_mm':25,'additional_motor_drop_mm':16,
 'slot_mm':[12,2.4],'slot_pitch_mm':21,'motor_contact_thickness_mm':3,
 'hardware':{'carrier_to_chassis_M3x30':9,'seat_to_carrier_M3x25':8,'DIN985_M3_nuts':17,'M3_washers_OD_at_most_6_t0p5':34},
 'seat_bolt_tip_clearance_to_chassis_mm':.5,'seat_nut_full_engagement_protrusion_mm':1,
 'existing_module_locations_changed':False,'existing_motor_seat_locations_changed':False,
 'actual_motor_axle_to_slot_offset_measured':False,
 'physical_wheel_clearance_tested':False,'physical_load_tested':False,'rated_payload_kg':None,
 'strength_basis':'16mm load spreader, 5/4 through-bolt anchors, captive steel nuts, no screws into PLA; no rated load asserted'}
save(O/'checks/design.json',report)
save(O/'source/design_plan.json',{'objective':'Reuse current chassis holes, retain confirmed motor seats and published slot datums',
 'process':'PLA FDM','architecture':'Two new load-spreader carriers plus two previously fitted removable motor seats',
 'assumptions':['No rated payload requested','Original 96mm slot datum retained; actual axle offset is not a measured dimension'],
 'review_plan':['Coordinate match to current split chassis','Hardware clearance','STEP and watertight mesh','Slicer and actual paths','Images','DOCX preserve 330 steps','Physical dry fit and incremental load before drive']})
