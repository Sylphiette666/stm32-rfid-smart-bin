"""Replace only the light bars and beam retainer; reuse the existing printed seats/walls."""
from pathlib import Path
import json
import cadquery as cq
import trimesh
B=Path(__file__).resolve().parents[1];BASE=B/'wall-panels-20261102';O=B/'sensor-retainers-fix-20261103'
for p in ['parts','step','checks','preview','source']:(O/p).mkdir(parents=True,exist_ok=True)
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def overlap(a,b):return a.intersect(b).Volume()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
old={n:cq.importers.importStep(str(BASE/'step'/f'{n}.step')).val() for n in ['LIGHT_CRADLE','BEAM_SEAT','LIGHT_EDGE_BAR','BEAM_RETAINER']}
# Two equal parts. Long transverse slots tolerate the old printed base; mark L to distinguish them.
bar=box(0,0,0,50,5.6,3).fuse(box(11,4.3,-.3,28,1.3,.3))
for x in [7,43]:bar=bar.cut(cq.Workplane('XY').center(x,2.8).slot2D(10,3.4).extrude(8).translate((0,0,-2)).val())
mark=cq.Workplane('XY').text('L',3.2,.3,font='Arial',combine=True).translate((25,2.6,2.75)).val();bar=bar.cut(mark).clean()
lower=bar.translate((-3,.7,7.3));upper=bar.rotate((25,2.8,0),(25,2.8,1),180).translate((-3,23.7,7.3))
pcb=box(8,5,5,28,20,2)
assert max(overlap(s,old['LIGHT_CRADLE']) for s in [lower,upper])<1e-5
assert max(overlap(s,pcb) for s in [lower,upper])<1e-5
for y in [3.5,26.5]:
    for x in [4,40]:
        b=lower if y<10 else upper;assert overlap(b,cyl(x,y,4,1.55,10))<1e-5
# Cap in original BEAM_SEAT coordinates. The two lower shoulders physically stop downward sliding.
cup=box(0,1.3,12.3,30,9.9,2.4)
for x in [7.4,19]:cup=cup.fuse(box(x,1.3,3.3,3.6,2.4,11.4))
# Open-front fork gap, not a closed hole: fitted wires do not have to be threaded through it.
cup=cup.cut(box(11,0,2,8,5.2,15))
for x in [4,26]:cup=cup.cut(cyl(x,8.7,11,1.7,6))
mark=cq.Workplane('XY').text('IR',3,.3,font='Arial',combine=True).translate((15,8.7,14.45)).val();cup=cup.cut(mark).clean()
assert overlap(cup,old['BEAM_SEAT'])<1e-5
sensor=box(10,3.7,3.3,10,20,9)
assert overlap(sensor,old['BEAM_SEAT'])<1e-5 and overlap(sensor,cup)<1e-5
drop=overlap(sensor.translate((0,-.1,0)),cup);pull=overlap(sensor.translate((0,0,.1)),cup)
assert drop>1 and pull>1,(drop,pull)
wire_gauge=box(11.01,-4,4,7.98,8,8)
assert overlap(wire_gauge,cup)<1e-5
optical=cq.Solid.makeCylinder(3.5,20,cq.Vector(15,19.2,-2))
assert overlap(optical,cup)<1e-5
for x in [4,26]:assert overlap(cup,cyl(x,8.7,0,1.55,25))<1e-5
pieces={'LIGHT_BAR_V2':bar,'BEAM_CUP_V2':cup};records={}
for n,s in pieces.items():
    assert s.isValid() and len(s.Solids())==1
    cq.exporters.export(s,str(O/'step'/f'{n}_ASSEMBLY.step'))
    sp=s.rotate((0,0,0),(1,0,0),180);bb=sp.BoundingBox();shift=[-bb.xmin,-bb.ymin,-bb.zmin];sp=sp.translate(shift)
    cq.exporters.export(sp,str(O/'step'/f'{n}_PRINT.step'));cq.exporters.export(sp,str(O/'parts'/f'{n}_PRINT.stl'),tolerance=.01,angularTolerance=.05)
    mesh=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');mesh.merge_vertices(digits_vertex=5)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1 and abs(mesh.volume-s.Volume())/s.Volume()<.001
    reopened=cq.importers.importStep(str(O/'step'/f'{n}_PRINT.step')).val();assert reopened.isValid() and len(reopened.Solids())==1
    records[n]={'copies':2,'size_mm':mesh.extents.tolist(),'volume_mm3':s.Volume(),'print_rotation_x_deg':180,'normalization_translation':shift,'mesh_relative_volume_error':abs(mesh.volume-s.Volume())/s.Volume(),'valid_single_solid':True,'watertight_connected':True,'STEP_reopened':True};print(n,records[n],flush=True)
scene=cq.Assembly();scene.add(old['LIGHT_CRADLE'],name='RETAIN_OLD_LIGHT_CRADLE',color=cq.Color('#82abb8'));scene.add(lower,name='NEW_LOWER_BAR',color=cq.Color('#e6b260'));scene.add(upper,name='NEW_UPPER_BAR',color=cq.Color('#e6b260'));scene.add(pcb,name='PCB_ENVELOPE_ONLY',color=cq.Color('#4d8c6f'));scene.save(str(O/'step/LIGHT_REPAIR_ASSEMBLY.step'))
scene=cq.Assembly();scene.add(old['BEAM_SEAT'],name='RETAIN_OLD_BEAM_SEAT',color=cq.Color('#82abb8'));scene.add(cup,name='NEW_FORK_CUP',color=cq.Color('#e6b260'));scene.add(sensor,name='SENSOR_ENVELOPE_ONLY',color=cq.Color('#667277'));scene.save(str(O/'step/BEAM_REPAIR_ASSEMBLY.step'))
save(O/'checks/design.json',{'status':'PASS_DIGITAL_FIT_OLD_PRINT_PHYSICAL_FIT_PENDING','parts':records,'total_print_objects':4,'old_seats_and_walls_reprinted':False,'light':{'old_seat_nominal_hole_pitch_x_mm':36,'old_seat_nominal_hole_pitch_y_mm':23,'old_matched_bar_nominal_pitch_mm':36,'actual_old_print_not_remeasured':True,'new_bar_length_mm':50,'slot_length_mm':10,'slot_width_mm':3.4,'slot_centre_pitch_mm':36,'ideal_hole_pitch_adjustment_range_mm':[29.4,42.6],'range_requires_hardware_clearance_check':True,'inner_contact_step_mm':.3,'nominal_PCB_thickness_mm':2,'PCB_and_old_seat_collision_mm3':0,'mounts':[{'origin':[-3,.7,7.3],'rotate_z':0},{'origin':[-3,23.7,7.3],'rotate_z':180,'rotation_centre_xy':[25,2.8]}]},'beam':{'old_two_hole_pitch_mm':22,'new_cap_plate_thickness_mm':2.4,'cap_holes_in_old_seat_xy':[[4,8.7],[26,8.7]],'lower_shoulders_x_mm':[[7.4,11],[19,22.6]],'lower_stop_y_mm':3.7,'open_wire_gap_mm':8,'sensor_nominal_envelope_mm':[10,20,9],'sensor_origin':[10,3.7,3.3],'downward_0_1mm_blocked_intersection_mm3':drop,'outward_0_1mm_blocked_intersection_mm3':pull,'optical_gauge_diameter_mm':7,'old_seat_interference_mm3':0,'wire_gauge_clear':True},'mesh_tolerance_mm':.01,'physical_trial_fit_or_load_tested':False})
save(O/'source/design_plan.json',{'user_reports':['Fig1 upper strips do not align with previously printed base','Fig2 IR housing can slip out downwards'],'scope':'Reuse original LIGHT_CRADLE and BEAM_SEAT and all wall holes. Replace two L bars and two IR fork caps only.','evidence_limit':'Original light digital matched pair both nominal36mm; actual old printed pitch was not measured. Do not claim the physical mismatch cause identified.','changes':['Adjustable slots and equal two L bars, existing PCB contact band maintained','Two lower positive support shoulders and front capture, open8mm wiring slot'],'review_plan':['Saved old STEP fit','Nominal PCB/sensor envelopes, holes and optical opening','Downward and outward motion stops','Fine mesh and print flat-face setup','Native P2S slice, full paths and geometry roundtrip','Manual update with old parts retained'],'physical_dimensions_or_strength_guaranteed':False})
