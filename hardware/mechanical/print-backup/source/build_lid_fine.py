"""Light closed-skin lid, original wall holes and purchased metal hinges retained.

Millimetres in P02 coordinates. Hinge knuckle offset is a labelled nominal
envelope, not a measurement of the user's hinges. No servo power is applied.
"""
from pathlib import Path
import json, math
import cadquery as cq
import numpy as np
import trimesh

B=Path(__file__).resolve().parents[1]; O=B/'lid-fine-20261103'; OLD=B/'wall-panels-20261102'
for d in ['step','parts','checks','preview','source']:(O/d).mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def box(x,y,z,a,b,c):return cq.Solid.makeBox(a,b,c,cq.Vector(x,y,z))
def cyl(x,y,z,r,h,axis=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*axis))
def slot(x,y,z,l,w,h):return cq.Workplane('XY').center(x,y).slot2D(l,w).extrude(h).translate((0,0,z)).val()
def fuse(items):
    out=items[0]
    for s in items[1:]:out=out.fuse(s)
    return out.clean()
def pose(s,deg):return s.rotate((46.5,0,185),(46.5,1,185),-deg)
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(min(getattr(aa,k+'max'),getattr(bb,k+'max'))-max(getattr(aa,k+'min'),getattr(bb,k+'min'))<1e-6 for k in 'xyz'):return 0.
    return a.intersect(b).Volume()

Z=185.; TOP=185.56
# Closed opaque skin, stiffening on the underside; no unnecessary closed skirt.
lid=box(48.5,18,Z,166.5,154,.56)
# Knuckle reliefs use the nominal original 20mm hinge width plus 1mm each end.
for y in [52,116]:lid=lid.cut(box(47,y,184.5,3.1,22,2))
ribpieces=[box(57,24,183.6,148,1.2,1.4),box(57,164.8,183.6,148,1.2,1.4),
           box(57,24,183.6,1.2,142,1.4),box(203.8,24,183.6,1.2,142,1.4)]
for x in [85,115,145,175]:ribpieces.append(box(x,24,183.8,1.2,142,1.2))
for y in [50,80,110,140]:ribpieces.append(box(57,y,183.8,148,1.2,1.2))
ribs=fuse(ribpieces)
for y in [23,154]:ribs=ribs.cut(box(110,y,182,20,13,3.01))
lid=lid.fuse(ribs)
mounts=[(63,y) for y in [57,69,121,133]]+[(60,163.5),(75,163.5),(203,134),(203,144)]
for x,y in mounts:lid=lid.fuse(cyl(x,y,182.6,3.2,2.4))
# Integrated manual lift lip, clear of the fixed front wall and IR shelf.
lid=lid.fuse(box(211.5,87,184,11.5,16,1.56))
for x,y in mounts:lid=lid.cut(cyl(x,y,181,1.4,6))
lid=lid.clean()

# A removable moving shoe sits on the lid. Countersunk M2 heads are installed
# BEFORE fitting the shoe, so no bolt head hangs into the rear wall.
shoe=fuse([box(50.1,53,TOP,17.9,20,1.54),box(59,53,187.1,9,20,2)])
for y in [57,69]:
    shoe=shoe.cut(slot(54.5,y,185.4,4.5,2.3,3))
    cutter=(cq.Workplane('XY').workplane(offset=TOP-.001).center(54.5,y).slot2D(6.2,4)
            .workplane(offset=.85).slot2D(4.5,2.3).loft(combine=True).val())
    shoe=shoe.cut(cutter).cut(cyl(63,y,185,1.4,6))
shoe=shoe.clean()

# Reuse original SG90 horn and M2 dual-ball linkage; do not print a spline.
ball=(46.5+20*math.cos(math.radians(20)),185+20*math.sin(math.radians(20)))
arm=box(55,161,TOP,25,14,2)
pts=[(55,TOP),(80,TOP),(79,191),(ball[0]+2.8,194.7),(ball[0]-2.8,194.7),(55,189)]
web=cq.Workplane('XZ').polyline(pts).close().extrude(3).val()
bb=web.BoundingBox();web=web.translate((0,172-bb.ymin,0));arm=arm.fuse(web)
for x in [60,75]:arm=arm.cut(slot(x,163.5,185,6,2.8,5))
arm=arm.cut(cyl(ball[0],171,ball[1],1.1,6,(0,1,0))).clean()

# The existing fixed microswitch is retained; trigger tongue is separately
# adjustable. It is a trigger, never the load-bearing closed-lid stop.
strike=fuse([box(200,131,TOP,20,16,2.4),box(218,131,180.5,2,16,9.5)])
for y in [134,144]:
    strike=strike.cut(slot(203,y,185,8,2.8,6))
    strike=strike.cut(cyl(217,y,187,1.4,5,(1,0,0)))
strike=strike.clean()
tongue=box(220,131,182,1.6,16,10)
for y in [134,144]:
    q=cq.Workplane('YZ').center(y,187).slot2D(7,2.8,angle=90).extrude(4).translate((219,0,0)).val()
    tongue=tongue.cut(q)
tongue=tongue.clean()
coupon=lid.intersect(box(48.5,50,181,23.5,26,10)).clean()
parts={'L01_LIGHT_LID':(lid,1,'x180'),'L02_HINGE_SHOE':(shoe,2,'none'),
       'L03_LINK_ARM':(arm,1,'none'),'L04_SWITCH_FOOT':(strike,1,'y90'),
       'L05_SWITCH_TONGUE':(tongue,1,'y90'),'T01_HINGE_FIT_COUPON':(coupon,1,'x180')}
records={}
for n,(s,qty,ori) in parts.items():
    assert s.isValid() and len(s.Solids())==1,(n,'BRep')
    cq.exporters.export(s,str(O/'step'/f'{n}_ASSEMBLY.step'))
    p=s.rotate((0,0,0),(1,0,0),180) if ori=='x180' else (s.rotate((0,0,0),(0,1,0),90) if ori=='y90' else s)
    bb=p.BoundingBox();shift=[-bb.xmin,-bb.ymin,-bb.zmin];p=p.translate(shift)
    cq.exporters.export(p,str(O/'step'/f'{n}_PRINT.step'))
    cq.exporters.export(p,str(O/'parts'/f'{n}_PRINT.stl'),tolerance=.01,angularTolerance=.05)
    m=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');m.merge_vertices(digits_vertex=5)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,(n,'mesh')
    err=abs(m.volume-s.Volume())/s.Volume();assert err<.002,(n,err)
    reopened=cq.importers.importStep(str(O/'step'/f'{n}_PRINT.step')).val();assert reopened.isValid() and len(reopened.Solids())==1
    records[n]={'copies':qty,'print_orientation':ori,'normalization_translation':shift,'size_mm':m.extents.tolist(),
                'volume_mm3':s.Volume(),'solid_PLA_mass_g_at_1_24':s.Volume()*.00124,'mesh_relative_volume_error':err,
                'valid_single_solid':True,'watertight_connected':True,'STEP_reopened':True}
    print(n,records[n],flush=True)

walls={
 'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],
 'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],
 'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],
 'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
fixed={n:cq.importers.importStep(str(OLD/'step'/f'{n}.step')).val().transformGeometry(cq.Matrix(t)) for n,t in walls.items()}
data=json.loads((OLD/'checks/design.json').read_text(encoding='utf-8-sig'))
for i,r in enumerate(data['sensor_instances']):
    mat=np.eye(4)
    if 'world_origin' in r:
        mat[:3,:3]=r['world_matrix'];mat[:3,3]=np.array(r['world_origin'])+[50,20,5]
    else:
        mat[:3,:3]=r.get('matrix',np.eye(3));mat[:3,3]=r['origin'];mat=np.array(walls[r['wall']])@mat
    fixed[f"{r['name']}_{i}"]=cq.importers.importStep(str(OLD/'step'/f"{r['name']}.step")).val().transformGeometry(cq.Matrix(mat.tolist()))
fixed['P03_SERVO_STAND']=cq.importers.importStep(str(B/'step/P03_servo_adjustable_stand.step')).val().translate((0,186,10))
fixed['P04_SERVO_TRAY']=cq.importers.importStep(str(B/'step/P04_servo_adjustable_tray.step')).val().translate((0,170,5))
moving={'LID':lid,'HINGE_SHOE_A':shoe,'HINGE_SHOE_B':shoe.translate((0,64,0)),'LINK_ARM':arm,'SWITCH_FOOT':strike,'SWITCH_TONGUE':tongue}
# Fixed knuckle/vertical leaf and moving leaf are dimensioned reference ONLY.
metal_moving={}
for y in [53,117]:
    leaf=box(48.6,y,175,1.4,20,8)
    for yy in [y+4,y+16]:leaf=leaf.cut(cyl(47,yy,178,1.5,5,(1,0,0)))
    fixed[f'NOMINAL_HINGE_FIXED_{y}']=leaf
    fixed[f'NOMINAL_KNUCKLE_{y}']=cyl(46.5,y,185,3.25,20,(0,1,0))
    metal_moving[f'NOMINAL_MOVING_LEAF_{y}']=leaf.rotate((46.5,0,185),(46.5,1,185),-90)
# EVA reuse, nominal 2mm uncompressed on the original 183mm stops.
for y in [23,155]:fixed[f'REUSE_EVA_{y}']=box(114,y,183,12,12,2)

failures=[];tested=0;kinematics=[]
for angle in range(0,71,2):
    transformed={n:pose(s,angle) for n,s in moving.items()}
    for n,s in transformed.items():
        for fn,fs in fixed.items():
            v=overlap(s,fs);tested+=1
            if v>.02:failures.append({'angle_deg':angle,'moving':n,'fixed':fn,'overlap_mm3':v})
    # Equal 20mm cranks with a 50mm rod, ground distance41.5mm. This is NOT
    # the old 50/20 parallelogram; never copy old servo pulse endpoints.
    phi=math.radians(20+angle);px=46.5+20*math.cos(phi);pz=185+20*math.sin(phi)
    dx=px-5;dz=pz-185;dist=math.hypot(dx,dz);c=(dist*dist+20*20-50*50)/(40*dist)
    assert abs(c)<=1
    theta=math.atan2(dz,dx)+math.acos(c)
    sx=5+20*math.cos(theta);sz=185+20*math.sin(theta)
    rod_error=abs(math.hypot(px-sx,pz-sz)-50);assert rod_error<1e-8
    # Outboard ball centres use Y179. The nominal rod/cup capsule radius4
    # stays below Y183, 3mm clear of the fixed stand at Y186.
    rod=cyl(sx,179,sz,2.0,50,((px-sx)/50,0,(pz-sz)/50))
    for fn,fs in fixed.items():
        if fn.startswith('NOMINAL_'):continue
        v=overlap(rod,fs)
        if v>.02:failures.append({'angle_deg':angle,'moving':'NOMINAL_ROD_R2','fixed':fn,'overlap_mm3':v})
    kinematics.append({'lid_deg':angle,'servo_crank_geometric_angle_deg':math.degrees(theta),'rod_length_error_mm':rod_error,'lid_ball_xz':[px,pz],'servo_ball_xz':[sx,sz]})
    if angle%10==0:print('sweep',angle,'failures',len(failures),flush=True)
assert not failures,failures[:12]
# For reusable previews: P02 frame, all wall accessory transforms, moving parts.
assembly=cq.Assembly()
for n,s in fixed.items():assembly.add(s,name=n,color=cq.Color('#79aabc') if n.startswith('W0') else cq.Color('#819096'))
for n,s in moving.items():assembly.add(s,name=n,color=cq.Color('#edb85f'))
for n,s in metal_moving.items():assembly.add(s,name=n,color=cq.Color('#cccccc'))
assembly.save(str(O/'step/LID_CLOSED_REFERENCE_ASSEMBLY.step'))
for y in [57,69]:
    assert overlap(shoe,cyl(53.5,y,185.6,1,3.4))<1e-5,'M2 hinge screw gauge'
    assert overlap(shoe,cyl(63,y,185,1.25,7))<1e-5,'M2.5 shoe screw gauge'
internal=[]
items=list(moving.items())+list(metal_moving.items())
for i,(n,s) in enumerate(items):
    for nn,ss in items[i+1:]:
        v=overlap(s,ss)
        if v>.02:internal.append([n,nn,v])
assert not internal,internal
total=sum(r['solid_PLA_mass_g_at_1_24']*r['copies'] for n,r in records.items() if n.startswith('L'))
report={'status':'PASS_NOMINAL_CAD_PHYSICAL_FIT_PENDING','parts':records,'print_objects':6,'coordinates':'P02 mm; X0 rear, Y190 servo side, platform top Z5',
 'lid_skin_size_mm':[166.5,154,.56],'lid_outer_with_lift_lip_mm':[174.5,154],'reinforced_max_thickness_mm':2.96,'hinge_axis_nominal_xz':[46.5,185],
 'original_wall_hole_centres_yz':[[y,178] for y in [57,69,121,133]],'metal_hinge_unfolded_mm':[20,20,1.4],
 'metal_hinge_hole_rectangle_mm':[14,12],'metal_hinge_barrel_diameter_mm':6.5,'hinge_shoe_nominal_standoff_mm':1.54,
 'hinge_hole_slot_mm':[4.5,2.3],'hinge_shoe_flat_M2_head_max_diameter_mm':4,
 'hinge_offset_evidence':'Nominal envelope only; actual knuckle-to-leaf plane not measured. Hand-fit original hinges before full print or powered motion; revise shim thickness if needed.',
 'closed_lid_z_mm':185,'reuse_two_softstops_and_2mm_EVA':True,'nominal_motion_checks':tested,'sweep_degrees':list(range(0,71,2)),
 'fixed_interferences':failures,'moving_internal_interferences':internal,'moving_printed_mass_solid_PLA_g':total,'bare_lid_solid_PLA_g':records['L01_LIGHT_LID']['solid_PLA_mass_g_at_1_24'],
 'moving_assembly_weighing_target_g':40,'moving_assembly_weighing_limit_g':45,'metal_hardware_and_linkage_mass_measured':False,
 'old_parallelogram_reused':False,'ground_distance_mm':41.5,'cranks_mm':[20,20],'rod_hole_centre_length_mm':50,
 'linkage_plane_y_mm':179,'nominal_ball_envelope_radius_mm':4,'ball_envelope_measured':False,'servo_horn_original_retained':True,
 'kinematics':kinematics,'mesh_tolerance_mm':.01,'angular_tolerance_rad':.05,
 'sweep_limitations':['Discrete 2-degree CAD samples, not continuous certified clearance','No actual wire harness, bolt/nut envelopes or hinge knuckle offset verified','Switch lever not measured: adjustable strike must be hand-set','Servo horn zero, shaft position and20mm effective crank require hand calibration','PLA stiffness, fatigue, impact and actual lid mass not tested'],
 'no_firmware_or_servo_endpoint_change_made':True,'physical_trial_fit_or_strength_tested':False}
save(O/'checks/design.json',report)
save(O/'source/design_plan.json',{'intent':'Closed thin-skin lightweight lid and ALL moving attachments, retain printed walls and two20mm metal hinges/M2 linkage',
 'deliverables':['six-object native P2S fine3MF','five parameterized printable shapes STEP/STL','closed/open assembly evidence','original holes and sampled motion audit','updated same-name manual'],
 'included_accessories':['two moving hinge shoes with recessed screw heads','20mm lid linkage arm','adjustable microswitch foot and separate strike tongue','integral finger lift lip','EVA contact reliefs'],
 'retained_fixed_accessories':['two20mm metal hinges','M2 dual ball rod and original SG90 horn','original microswitch bracket','two existing softstops and2mm EVA','fixed HC-SR04 beam and LED'],
 'backend':'CadQuery/OCCT, no native SolidWorks claim','critical_unverified_interfaces':['actual hinge leaf-to-axis offset','servo/horn physical zero and crank','microswitch lever envelope'],
 'physical_strength_guarantee':False})
print('moving printed solid mass',total,flush=True)
