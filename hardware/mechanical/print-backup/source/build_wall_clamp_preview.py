"""Preview only: edge-keyed hold-down clamps reuse upper-platform holes; walls stay flush."""
from pathlib import Path
import json,math,csv
import cadquery as cq
import trimesh
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamp-preview-20261103'
for p in ['step','qa_meshes','preview','checks','source']:(O/p).mkdir(parents=True,exist_ok=True)
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def fuse(s,*others):
    for o in others:s=s.fuse(o)
    return s
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(min(getattr(aa,k+'max'),getattr(bb,k+'max'))<=max(getattr(aa,k+'min'),getattr(bb,k+'min'))+1e-7 for k in 'xyz'):return 0.
    return a.intersect(b).Volume()
def prism(poly,z,h):return cq.Workplane('XY').polyline(list(poly.exterior.coords)[:-1]).close().extrude(h).translate((0,0,z)).val()
platform=cq.importers.importStep(str(B/'step/P02_light.step')).val()
tray=cq.importers.importStep(str(B/'step/P04_servo_adjustable_tray.step')).val().translate((0,170,5))
stand=cq.importers.importStep(str(B/'step/P03_servo_adjustable_stand.step')).val().translate((0,186,10))
walls={
 'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],
 'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],
 'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],
 'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
wallshapes={n:cq.importers.importStep(str(B/'wall-panels-20261102/step'/f'{n}.step')).val().transformGeometry(cq.Matrix(m)) for n,m in walls.items()}
specs=[
 {'id':'C1_LEFT_REAR','anchor':[10,10],'pressure':[90,13],'edge':'left','anchor_type':'platform_corner','anchor_screw':'M3x16'},
 {'id':'C2_LEFT_FRONT','anchor':[230,10],'pressure':[170,13],'edge':'left','anchor_type':'platform_corner','anchor_screw':'M3x16'},
 {'id':'C3_RIGHT_FRONT','anchor':[230,180],'pressure':[170,177],'edge':'right','anchor_type':'platform_corner','anchor_screw':'M3x16'},
 {'id':'C4_RIGHT_REAR','anchor':[70,180],'pressure':[90,177],'edge':'right','anchor_type':'shared_servo_tray','anchor_screw':'M3x20'}]
parts={};metal={};pads={};records=[]
for v in specs:
    ident=v['id'];ax,ay=v['anchor'];fx,fy=v['pressure']
    if v['anchor_type']=='platform_corner':
        x0=min(ax,fx-12);length=max(ax,fx+12)-x0
        s=fuse(cyl(ax,ay,5,7,6),box(x0,-2.7,5,length,10.4,6),box(x0,-2.7,0,length,2.4,5.8))
        s=fuse(s,box(fx-5,6.7,10,10,10.8,5),box(fx-11.5,6.7,5,2.2,8.1,5.2),box(fx+9.3,6.7,5,2.2,8.1,5.2))
        if v['edge']=='right':
            # Mirror around the platform's middle Y=95. X and Z stay in the assembly datum.
            s=s.mirror('XZ').translate((0,190,0))
            # The anchor was defined at its true side already; relocate its mirrored circular pad.
            # Replace the first-pad location: mirrored Y=10 is the actual intended Y=180.
            wrong=cyl(ax,10,5,7,6)
            s=s.cut(wrong).fuse(cyl(ax,180,5,7,6))
        anchor_top=11
    else:
        route=unary_union([LineString([(70,180),(90,180)]).buffer(5,resolution=12),Point(70,180).buffer(6.5,resolution=12)])
        s=prism(route,10,4)
        s=fuse(s,box(85,172.5,10,10,10.8,5),
          box(84,182.3,5,18,3.2,9),box(99.3,175.2,5,2.2,8.1,5.2),
          box(78,183,10,6,5,4),box(80.3,184,6,2.4,4,4.3))
        anchor_top=14
    s=s.cut(cyl(ax,ay,0,1.7,18)).cut(cyl(fx,fy,8,1.7,12))
    # A captive ordinary M3 nut is above the foot. It drives a hold-down screw, not a foot through-bolt.
    # Bottom-loaded pocket: a 2.4mm roof captures the upward reaction from the pressure screw.
    nutpocket=cq.Workplane('XY').polygon(6,5.9/math.cos(math.pi/6)).extrude(2.7).translate((fx,fy,9.9)).val()
    s=s.cut(nutpocket).clean()
    assert s.isValid() and len(s.Solids())==1,(ident,'not one valid solid')
    pad=cyl(fx,fy,8.2,4,1.2).cut(cyl(fx,fy,9.1,1,.4))
    # The M3x8 pressure screw has an intentionally floating head above the captive nut.
    pressure=fuse(cyl(fx,fy,9.4,1.5,8),cyl(fx,fy,17.4,2.85,1.65))
    nut=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.4).translate((fx,fy,10.2)).val().cut(cyl(fx,fy,10,1.5,4))
    boltlen=16 if anchor_top==11 else 20
    anchorbolt=fuse(cyl(ax,ay,anchor_top+.5-boltlen,1.5,boltlen),cyl(ax,ay,anchor_top+.5,2.85,1.65))
    washer=cyl(ax,ay,anchor_top,3,.5).cut(cyl(ax,ay,anchor_top-.1,1.6,.7))
    metals=[pressure,nut,anchorbolt,washer]
    hosts={'P02':platform,'P04_TRAY':tray,'P03_STAND':stand,**wallshapes}
    collisions=[]
    for h,shape in hosts.items():
        q=overlap(s,shape)
        if q>1e-4:collisions.append([ident,h,q])
        q=overlap(pad,shape)
        if q>1e-4:collisions.append([ident+'_pad',h,q])
        for mi,shape2 in enumerate(metals):
            q=overlap(shape2,shape)
            if q>1e-4:collisions.append([ident+'_metal'+str(mi),h,q])
    assert not collisions,collisions
    assert overlap(s,pad)<1e-4 and overlap(s,pressure)<1e-4 and overlap(s,nut)<1e-4
    cq.exporters.export(s,str(O/'step'/f'{ident}_CONCEPT.step'))
    cq.exporters.export(s,str(O/'qa_meshes'/f'{ident}.stl'),tolerance=.03,angularTolerance=.08)
    mesh=trimesh.load_mesh(O/'qa_meshes'/f'{ident}.stl');mesh.merge_vertices(digits_vertex=5)
    assert mesh.is_watertight and len(mesh.split())==1
    parts[ident]=s;pads[ident]=pad;metal[ident]=metals
    v.update(anchor_top_z=anchor_top,pressure_pad_top_z=9.4,nut_top_z=12.6,nut_roof_thickness_mm=2.4,nut_insertion='from underside before clamp installation',pressure_bolt_under_head_z=17.4,
      footprint_size_mm=[s.BoundingBox().xlen,s.BoundingBox().ylen,s.BoundingBox().zlen],volume_mm3=s.Volume(),collision_check='PASS')
    records.extend([{'part':ident,'role':'existing anchor','x':ax,'y':ay,'hole':3.4},
      {'part':ident,'role':'pressure screw above existing foot','x':fx,'y':fy,'hole':3.4}])
    print(ident,v['footprint_size_mm'],'PASS',flush=True)
for i,(a,s) in enumerate(parts.items()):
    for b,t in list(parts.items())[i+1:]:assert overlap(s,t)<1e-4,(a,b)
scene=cq.Assembly();scene.add(platform,name='EXISTING_P02',color=cq.Color('#526b7a'));scene.add(tray,name='EXISTING_P04_TRAY',color=cq.Color('#a991bc'));scene.add(stand,name='EXISTING_P03_STAND',color=cq.Color('#b28b66'))
for n,s in wallshapes.items():scene.add(s,name=n,color=cq.Color('#7bb2c5'))
for n,s in parts.items():
    scene.add(s,name=n,color=cq.Color('#66a77c'));scene.add(pads[n],name=n+'_PRESSURE_PAD',color=cq.Color('#edb96b'))
    for i,m in enumerate(metal[n]):scene.add(m,name=n+'_HARDWARE_'+str(i),color=cq.Color('#929da6'))
scene.save(str(O/'step/WALL_CLAMPS_ASSEMBLY_PREVIEW.step'))
save(O/'checks/design.json',{'status':'CONCEPT_PREVIEW_GEOMETRY_CHECKED_NOT_PRINT_RELEASE','clamps':specs,
 'new_platform_holes':0,'wall_position_changed':False,'wall_lift_mm':0,
 'platform_size_mm':[240,190,5],'wall_main_frame_origin_xy':[50,20],
 'anchors_used':[[10,10],[230,10],[230,180],[70,180]],'corner_hole_left_free':[10,180],
 'shared_servo_tray_hole':[70,180],'foot_pressure_points':[[90,13],[170,13],[170,177],[90,177]],
 'pressure_uses_existing_foot_hole':False,'pressure_pad_diameter_mm':8,'pressure_pad_thickness_mm':1.2,
 'corner_bolt_engagement_nominal_mm':4.5,'shared_tray_bolt_projection_below_P02_mm':5.5,
 'new_parts':{'clamp_bodies':4,'pressure_pads':4},'provisional_hardware':{'M3x16_corner':3,'M3x20_tray':1,'M3x8_pressure':4,'ordinary_M3_nut_for_pressure':4},
 'full_wall_platform_tray_stand_and_modeled_fastener_interference':'PASS',
 'physical_fit_tested':False,'load_tested':False,'print_project_released':False,
 'limits':['Model dimensions only; no physical clamp/creep test','Pressure screw must be finger-light; it must not crack the existing 3.2mm foot','Corner post blind depth and actual screw heads must be checked before print release','CAD preview does not prove rated strength']})
save(O/'source/design_plan.json',{'scope':'Preview requested by user; no print-ready 3MF or printer dispatch','architecture':'Three edge-keyed corner hold-downs plus short servo-tray-keyed hold-down','principle':'Press existing feet from above without drilling the P02 floor or lifting the bin','review_plan':['Exact existing-hole alignment','Full wall/servo interference','Nut/screw geometry','Oblique and plan previews','Manual append as concept only'],'release_gate':'User reviews appearance; detailed print orientation and physical fit validation remain subsequent work'})
with (O/'source/connector_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
