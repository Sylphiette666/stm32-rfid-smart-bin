"""Derive supported fine-print clamps from checked preview, retaining all assembly datums."""
from pathlib import Path
import json,math,hashlib
import cadquery as cq
import trimesh
B=Path(__file__).resolve().parents[1];BASE=B/'wall-clamp-preview-20261103';O=B/'wall-clamps-fine-20261103'
for p in ['step','parts','checks','preview','source']:(O/p).mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
d=load(BASE/'checks/design.json');specs=d['clamps'];parts={};report=[]
hosts={'P02':cq.importers.importStep(str(B/'step/P02_light.step')).val(),'P04':cq.importers.importStep(str(B/'step/P04_servo_adjustable_tray.step')).val().translate((0,170,5)),'P03':cq.importers.importStep(str(B/'step/P03_servo_adjustable_stand.step')).val().translate((0,186,10))}
transforms={'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
for n,m in transforms.items():hosts[n]=cq.importers.importStep(str(B/'wall-panels-20261102/step'/f'{n}.step')).val().transformGeometry(cq.Matrix(m))
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(min(getattr(aa,k+'max'),getattr(bb,k+'max'))<=max(getattr(aa,k+'min'),getattr(bb,k+'min'))+1e-7 for k in 'xyz'):return 0.
    return a.intersect(b).Volume()
for v in specs:
    n=v['id'];x,y=v['pressure'];s=cq.importers.importStep(str(BASE/'step'/f'{n}_CONCEPT.step')).val();original=s
    if v['anchor_type']=='platform_corner':
        # Outside the existing foot, a 45-degree gusset supports the cap during side printing.
        gusset=cq.Workplane('YZ',origin=(x-5,0,0)).polyline([(2.7,11),(6.7,11),(6.7,15)]).close().extrude(10).val()
        if v['edge']=='right':gusset=gusset.mirror('XZ').translate((0,190,0))
        s=s.fuse(gusset).clean();yy=-2.7 if v['edge']=='left' else 192.7
        selected=[e for e in s.Edges() if e.geomType()=='LINE' and abs(e.BoundingBox().ymin-yy)<1e-5 and abs(e.BoundingBox().ymax-yy)<1e-5 and e.BoundingBox().xlen>40 and any(abs(e.Center().z-z)<1e-5 for z in [0,11])]
        assert len(selected)==2,(n,'Expected outer long top and bottom edges',len(selected))
        s=s.fillet(.6,selected).clean();fillet=.6;orientation=90 if v['edge']=='left' else -90
    else:
        selected=[e for e in s.Edges() if e.geomType()=='LINE' and abs(e.Center().y-185.5)<1e-5 and abs(e.Center().z-5)<1e-5 and e.Length()>10]
        assert len(selected)==1,(n,len(selected));s=s.fillet(.4,selected).clean();fillet=.4;orientation=-90
    assert s.isValid() and len(s.Solids())==1
    collisions={h:overlap(s,sh) for h,sh in hosts.items()};assert max(collisions.values())<1e-4,(n,collisions)
    for cx,cy in [v['anchor'],v['pressure']]:assert overlap(s,cq.Solid.makeCylinder(1.65,30,cq.Vector(cx,cy,-2)))<1e-5
    nut=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.39).translate((x,y,10.205)).val();assert overlap(s,nut)<1e-5
    roof=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.39).translate((x,y,12.605)).val().cut(cq.Solid.makeCylinder(1.71,3,cq.Vector(x,y,12.5)));assert abs(overlap(s,roof)-roof.Volume())<1e-5
    cq.exporters.export(s,str(O/'step'/f'{n}_ASSEMBLY.step'));parts[n]=s
    sp=s.rotate((0,0,0),(1,0,0),orientation);bb=sp.BoundingBox();shift=[-bb.xmin,-bb.ymin,-bb.zmin];sp=sp.translate(shift)
    cq.exporters.export(sp,str(O/'step'/f'{n}_PRINT.step'));cq.exporters.export(sp,str(O/'parts'/f'{n}_PRINT.stl'),tolerance=.01,angularTolerance=.05)
    mesh=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');mesh.merge_vertices(digits_vertex=5);assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
    assert abs(mesh.volume-s.Volume())/s.Volume()<.001
    reopened=cq.importers.importStep(str(O/'step'/f'{n}_PRINT.step')).val();assert reopened.isValid() and len(reopened.Solids())==1
    report.append({**v,'actual_convex_edge_radius_mm':fillet,'fillet_edge_count':len(selected),'gusset_angle_deg':45 if v['anchor_type']=='platform_corner' else None,'assembly_to_print_rotation_x_deg':orientation,'normalization_translation':shift,'print_size_mm':mesh.extents.tolist(),'print_volume_mm3':s.Volume(),'mesh_relative_volume_error':abs(mesh.volume-s.Volume())/s.Volume(),'triangles':len(mesh.faces),'host_interference_mm3':collisions,'nut_pocket_and_2_4_mm_roof_checked':True,'orientation_note':'outer side toward bed; keep saved orientation; automatic tree support'});print(n,'PASS',mesh.extents.tolist(),flush=True)
pad=cq.Solid.makeCylinder(4,1.2).cut(cq.Solid.makeCylinder(1,.4,cq.Vector(0,0,.9)))
cq.exporters.export(pad,str(O/'step/PRESSURE_PAD_PRINT.step'));cq.exporters.export(pad,str(O/'parts/PRESSURE_PAD_PRINT.stl'),tolerance=.01,angularTolerance=.05)
mesh=trimesh.load_mesh(O/'parts/PRESSURE_PAD_PRINT.stl');mesh.merge_vertices(digits_vertex=5);assert mesh.is_watertight and len(mesh.split())==1
scene=cq.Assembly()
for n,s in hosts.items():scene.add(s,name=n,color=cq.Color('#7bb2c5' if n.startswith('W') else '#8997a3'))
for v in specs:scene.add(parts[v['id']],name=v['id'],color=cq.Color('#399262'));scene.add(pad.translate((*v['pressure'],8.2)),name=v['id']+'_PAD',color=cq.Color('#edb96b'))
scene.save(str(O/'step/WALL_CLAMPS_PRINT_DESIGN_ASSEMBLY.step'))
save(O/'checks/design.json',{'status':'PASS_DIGITAL_GEOMETRY_PHYSICAL_FIT_PENDING','variants':report,'pressure_pad':{'diameter_mm':8,'thickness_mm':1.2,'copies':4,'flat_face_on_bed':True},'clamps':4,'total_print_objects':8,'nominal_anchor_and_pressure_positions_unchanged':True,'new_P02_holes':0,'wall_lift_mm':0,'minimum_nut_retaining_roof_mm':2.4,'mesh_linear_tolerance_mm':.01,'mesh_angular_tolerance_radian':.05,'actual_screw_head_and_post_depth_unmeasured':True,'physical_fit_tested':False,'physical_load_tested':False})
save(O/'source/design_plan.json',{'user_request':'High precision print-ready .3MF','printer':'existing Bambu P2S 0.4mm nozzle','material_assumption':'Generic PLA, matching previous released projects','construction':'Bottom-loaded metal M3 nut; floating-head pressure screw; original flush wall position','changes_from_preview':['45 degree cap gussets on three long clamps','R0.6 outer long edges on C1/C2/C3','R0.4 outer lower edge on C4','Fine .01mm mesh; side-print bodies; pads flat; tree supports as sliced'],'review_plan':['Exact BRep interference','Nut roof and bores','Watertight meshes and STEP reopen','Slicer warnings and all-layer bounds','Actual support and first layer images','Same-name Word update'],'printer_dispatch':False})
