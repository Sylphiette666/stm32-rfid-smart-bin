"""Reproduce the measured deck's conservative hardware envelope review.

This is a mechanical envelope check, not a physical pin/connector fit test.
M3 heads use their ISO7380 maximum OD5.7 x 1.65 cylinder; washer OD6 x .5;
DIN985 nuts use a conservative OD6.4 x 4 cylinder. Threads are not meshed.
Run after build_mounted_design.py, using the same CadQuery interpreter.
"""
from pathlib import Path
import ast
import hashlib
import json
import math
import sys
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mounted-20261031'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from module_clamps_a import build_holder,make_lock

def assignment(name):
    tree=ast.parse((ROOT/'source/build_mounted_design.py').read_text(encoding='utf-8'))
    n=next(n for n in tree.body if isinstance(n,ast.Assign) and
           any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return eval(compile(ast.Expression(n.value),'<literal-spec>','eval'),{'dict':dict})

def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def ring(x,y,z,r,h,inner=1.6):
    return cyl(x,y,z,r,h).cut(cyl(x,y,z-.1,inner,h+.2))

def block(x,y,z,a,b,c):
    return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()

def rigid(s,xy,angle=0,z=0):
    return s.rotate((0,0,0),(0,0,1),angle).translate((xy[0],xy[1],z))

def overlap(a,b):
    x=a.BoundingBox();y=b.BoundingBox()
    return not(x.xmax<=y.xmin or y.xmax<=x.xmin or x.ymax<=y.ymin or
               y.ymax<=x.ymin or x.zmax<=y.zmin or y.zmax<=x.zmin)

def volume(a,b):
    return a.intersect(b).Volume() if overlap(a,b) else 0.0

def compound(parts):
    return cq.Compound.makeCompound(parts)

def down_screw(x,y,top,length,foot_top,nut_height=2.4):
    # Under-head top=foot_top+.5; head above the foot, nut below 5-mm plate.
    return compound([cyl(x,y,top,2.85,1.65),cyl(x,y,top-length,1.5,length),
        ring(x,y,foot_top,3,.5),ring(x,y,-5.5,3,.5),
        ring(x,y,-5.5-nut_height,3.2,nut_height,1.5)])

def up_screw(x,y,length,load_top,play=0):
    return compound([cyl(x,y,-7.15,2.85,1.65),ring(x,y,-5.5,3,.5),
        cyl(x,y,-5.5,1.5,length),ring(x,y,load_top+play,3,.5),
        ring(x,y,load_top+play+.5,3.2,4,1.5)])

def hinge_screw(point):
    # Model along X, then translate to hinge Y/Z.  23-mm ear span + 2 washers.
    def x_cyl(x,r,h):
        return cq.Solid.makeCylinder(r,h,cq.Vector(x,0,0),cq.Vector(1,0,0))
    def x_ring(x,r,h):return x_cyl(x,r,h).cut(x_cyl(x-.1,1.6,h+.2))
    s=compound([x_cyl(-13.65,2.85,1.65),x_cyl(-12,1.5,30),
                x_ring(-12,3,.5),x_ring(11.5,3,.5),x_ring(12,3.2,4)])
    return s.translate((0,point[1],point[2]))

def standard_length(value):
    return next(x for x in [12,16,20,25,30,35,40,45,50] if x+1e-8>=value)

def main():
    specs=assignment('SPECS');hardware_bill=assignment('hardware')
    design=json.loads((OUT/'source/design.json').read_text(encoding='utf-8'))
    fixtures=[];metals=[];holders=[];lengths=[];bearing_sweeps=[]
    def addmetal(name,shape,owner):metals.append({'id':name,'shape':shape,'owner':owner})
    def addfixture(name,shape):fixtures.append({'id':name,'shape':shape})
    for s in specs:
        h=build_holder(s);holders.append((s,h))
        for key in ['body','lid','keeper','detent']:
            addfixture(s['id']+'_'+key,rigid(h[key],s['xy'],s['rotation'],5))
        for i,(x,y) in enumerate(h['mount_holes_xy']):
            addmetal(s['id']+f'_foot{i+1}',rigid(down_screw(x,y,2.9,12,2.4),s['xy'],s['rotation'],5),s['id'])
        addmetal(s['id']+'_hinge',rigid(hinge_screw(h['dimensions']['hinge_axis']['point']),s['xy'],s['rotation'],5),s['id'])
        zmax=h['keeper'].BoundingBox().zmax
        head_top=h['detent'].BoundingBox().zmin+1.16
        # Two .5 washers + 4-mm locknut + target 1-mm exposed thread.
        min_axis=5+zmax+1+4+1+.15
        min_anchor=5+head_top+1+4+1
        la,lb=standard_length(min_axis),standard_length(min_anchor)
        for kind,pt,ln,zt,play in [('axis',h['dimensions']['lock_axis_xy'],la,zmax,.15),
                                  ('anchor',h['dimensions']['lock_anchor_xy'],lb,head_top,0)]:
            addmetal(s['id']+'_'+kind,rigid(up_screw(*pt,ln,zt,play),s['xy'],s['rotation'],5),s['id'])
        lengths.append({'id':s['id'],'seat_height_mm':s['seat_height'],
            'axis_minimum_mm':round(min_axis,3),'axis_length_mm':la,
            'anchor_minimum_mm':round(min_anchor,3),'anchor_length_mm':lb})
        for a in [0,15,30,45,60,75,90]:
            pt=h['dimensions']['lock_axis_xy'];moved=h['keeper'].rotate((*pt,0),(*pt,1),a)
            v=volume(h['body'],moved)
            assert v<1e-5,(s['id'],'keeper',a,v)
            bearing_sweeps.append({'id':s['id'],'degrees':a,'volume_mm3':v})
    # Existing exports below are unchanged by the clamp-only refinements.
    fixed_extras=[('P05_BATTERY_cradle',[176,30]),('P06_BUCK_cradle',[202.5,187.5]),
                  ('P07_SPEAKER_cradle',[68,198])]
    for name,xy in fixed_extras:
        shape=cq.importers.importStep(str(OUT/'step'/f'{name}.step')).val()
        addfixture(name,rigid(shape,xy,z=5))
    for side,x,y,a in [('L',-42.2,-10,90),('R',42.2,10,-90)]:
        lock=make_lock(base_z=0,catch_top_z=24.4)
        for role in ['keeper','detent']:
            addfixture('BAT_'+side+'_'+role,rigid(rigid(lock[role],[x,y],a),[176,30],z=5))
        for kind,pt,zt,play in [('axis',lock['axis_xy'],27.8,.15),
                               ('anchor',lock['anchor_xy'],24.37,0)]:
            metal=rigid(up_screw(*pt,40,zt,play),[x,y],a)
            addmetal('BAT_'+side+'_'+kind,rigid(metal,[176,30],z=5),'BAT')
        lengths.append({'id':'BAT_'+side,'axis_minimum_mm':38.95,'axis_length_mm':40,
                        'anchor_minimum_mm':35.37,'anchor_length_mm':40})
    for x in [-24,24]:
        for y in [-24,24]:addmetal(f'BAT_foot_{x}_{y}',rigid(down_screw(x,y,2.9,12,2.4),[176,30],z=5),'BAT')
    for x in [-13,13]:addmetal('BUCK_foot_'+str(x),rigid(down_screw(x,0,3.7,16,3.2,4),[202.5,187.5],z=5),'BUCK')
    for x,y in [(-14.5,8.5),(14.5,-8.5)]:
        screw=compound([cyl(x,y,.2,1.25,8),cyl(x,y,8.2,2.35,1.5),
                        ring(x,y,.2,5/math.sqrt(3),2,1.25)])
        # Hex pocket AF5.4; use true hex nut rather than a circular corner disc.
        nut=cq.Workplane('XY').polygon(6,5/math.cos(math.pi/6)).extrude(2).translate((x,y,.2)).val()
        nut=nut.cut(cyl(x,y,0,1.25,3))
        screw=compound([cyl(x,y,.2,1.25,8),cyl(x,y,8.2,2.35,1.5),nut])
        addmetal('BUCK_M2.5_'+str(x),rigid(screw,[202.5,187.5],z=5),'BUCK')
    a1=next(x for x in design['modules'] if x['id']=='A1')
    for i,hole in enumerate(a1['mount_holes']):
        x,y=hole['xy']
        lo=compound([cyl(x,y,-2.15,2.85,1.65),ring(x,y,-.5,3,.5),cyl(x,y,-.5,1.5,10)])
        hi=compound([cyl(x,y,17.1,2.85,1.65),ring(x,y,16.6,3,.5),cyl(x,y,11.1,1.5,6)])
        addmetal('A1_lower_'+str(i),lo,'A1');addmetal('A1_upper_'+str(i),hi,'A1')
    # Provisional ear underside E=12 above deck top and thickness t=2.
    for x in [44,92]:
        y=198;ear_bottom=17;ear_top=19
        sp=compound([cyl(x,y,-2.15,2.85,1.65),ring(x,y,-.5,3,.5),cyl(x,y,-.5,1.5,30),
            ring(x,y,ear_bottom-.5,3,.5),ring(x,y,ear_bottom-2.9,3.2,2.4,1.5),
            ring(x,y,ear_top,3,.5),ring(x,y,ear_top+.5,3.2,4,1.5)])
        addmetal('SPK_ear_'+str(x),sp,'SPK')
    static_errors=[];tested_static=0
    for metal in metals:
        for part in fixtures:
            if overlap(metal['shape'],part['shape']):
                tested_static+=1;v=volume(metal['shape'],part['shape'])
                if v>1e-5:static_errors.append({'metal':metal['id'],'printed':part['id'],'volume_mm3':v})
    mutual_errors=[];tested_pairs=0
    for i,a in enumerate(metals):
        for b in metals[i+1:]:
            if overlap(a['shape'],b['shape']):
                tested_pairs+=1;v=volume(a['shape'],b['shape'])
                if v>1e-5:mutual_errors.append({'a':a['id'],'b':b['id'],'volume_mm3':v})
    opening_errors=[];lid_body_errors=[];lid_samples=0;tested_motion=0
    for s,h in holders:
        a=h['dimensions']['hinge_axis']['point']
        for angle in [0,15,30,45,60,75,90,105]:
            lid_samples+=1
            local_lid=h['lid'].rotate(a,[a[0]+1,a[1],a[2]],angle)
            own_volume=volume(local_lid,h['body'])
            if own_volume>1e-5:lid_body_errors.append({'lid':s['id'],'degrees':angle,'volume_mm3':own_volume})
            moved=rigid(local_lid,s['xy'],s['rotation'],5)
            for metal in metals:
                if overlap(moved,metal['shape']):
                    tested_motion+=1;v=volume(moved,metal['shape'])
                    if v>1e-5:opening_errors.append({'lid':s['id'],'degrees':angle,'metal':metal['id'],'volume_mm3':v})
    latch_motion_errors=[];latch_samples=0
    for s,h in holders:
        pt=h['dimensions']['lock_axis_xy']
        for angle in [0,15,30,45,60,75,90]:
            latch_samples+=1
            moved=rigid(h['keeper'].rotate((*pt,0),(*pt,1),angle),s['xy'],s['rotation'],5)
            for metal in metals:
                v=volume(moved,metal['shape'])
                if v>1e-5:latch_motion_errors.append({'keeper':s['id'],'degrees':angle,'metal':metal['id'],'volume_mm3':v})
    for side,x,y,a in [('L',-42.2,-10,90),('R',42.2,10,-90)]:
        lock=make_lock(base_z=0,catch_top_z=24.4)
        for angle in [0,15,30,45,60,75,90]:
            latch_samples+=1
            moved=rigid(rigid(lock['keeper'].rotate((0,0,0),(0,0,1),angle),[x,y],a),[176,30],z=5)
            for metal in metals:
                v=volume(moved,metal['shape'])
                if v>1e-5:latch_motion_errors.append({'keeper':'BAT_'+side,'degrees':angle,'metal':metal['id'],'volume_mm3':v})
    errors=static_errors+mutual_errors+opening_errors+lid_body_errors+latch_motion_errors
    result={'status':'PASS_WITH_UNMEASURED_PHYSICAL_FIT_ITEMS' if not errors else 'FAIL',
        'units':'mm','scope':'Added module mounts only; original chassis/servo hardware excluded.',
        'hardware_envelopes':{'M3_button_head':[5.7,1.65],'M3_washer':[3.2,6,.5],
            'M3_locknut_circumscribed_diameter_height':[6.4,4],
            'M3_plain_nut_circumscribed_diameter_height':[6.4,2.4],
            'threads_modelled':False,'contact_tolerance_mm3':1e-5},
        'hardware_groups':len(metals),'printed_fixture_parts':len(fixtures),
        'static_intersection_pairs_tested':tested_static,'static_errors':static_errors,
        'metal_pair_tests':tested_pairs,'metal_pair_errors':mutual_errors,
        'lid_motion_samples':lid_samples,'lid_hardware_pairs_tested':tested_motion,'lid_motion_errors':opening_errors,
        'lid_own_body_errors':lid_body_errors,
        'keeper_motion_samples':latch_samples,'keeper_motion_errors':latch_motion_errors,
        'bearing_body_sweeps':bearing_sweeps,'lock_fastener_lengths':lengths,
        'length_assumptions':{'deck_thickness':5,'washer_thickness_each':.5,'locknut_height':4,
             'target_exposed_thread':1,'keeper_axial_play':.15,
             'axis_formula':'5 + keeper_top + 2*0.5 + 4 + 1 + 0.15',
             'anchor_formula':'5 + fixed_spring_head_top + 2*0.5 + 4 + 1'},
        'hardware_bill':hardware_bill,
        'vertical_axis_anchor_bolt_counts':{'M3x25':10,'M3x30':2,'M3x40':10},
        'all_added_bolt_counts':{'M3x6':4,'M3x10':4,'M3x12':22,'M3x16':2,
            'M3x25':10,'M3x30':13,'M3x40':10,'M2.5x8':2},
        'upper_platform_hardware_clearance_mm':25.5,
        'interface_design_checks':{'M01_USB_central_window_width':12,
            'M06_TF_end_open':True,'M07_antenna_end_open':True,
            'M07_front_header_crossbar_top':5,'M07_PCB_bottom':5,
            'M07_left_foot_xy_local':holders[6][1]['mount_holes_xy'][0]},
        'battery_nominal_fit':{'case':[76,40,20],'cradle_inner_xy':[77.2,41.2],
            'EVA_thickness':2,'keeper_bottom_above_deck_top':24.6,
            'case_top_above_deck_top':24.4,'retention_gap':.2,'rigid_overlap':2.3,
            'right_wire_preferred_corridor_relative_battery_center':{'x':[38,50],'y':[-5,1]},
            'wire_note':'Route out the right central slot toward its negative-Y half; confirm both keepers turn freely without touching wires. Retain plastic end edges, never press a cell.'},
        'physical_fit_pending':[
            'Corner pad overlap .8mm must be checked against actual solder joints, header plastic and densely packed corner components; their exact XY envelopes were not measured.',
            'USB cable boot, SWD plug, TF ejection travel and actual mated Dupont wire bending envelopes are not measured.',
            'Back header tip clearance above deck: MCU/MCP 11mm; DFP12mm; regulator5mm before mating connectors/wire bends.',
            'A1 total populated height28mm is known, but its split below PCB is not; confirm the10mm standoffs clear every underside joint/pin.',
            'Speaker ear underside height E and ear thickness t remain unmeasured. M3x30 assumes E+t<=19mm with the selected washers/locknut. Never bend ears or lift the body clear of the locating lips.',
            'Battery dimensions and EVA compression are nominal; confirm .2mm keeper clearance and end contact on hard case edges. Route wires away from the full keeper sweep.',
            'Check actual standoff internal thread depth: lower screw engagement4.5mm, upper3.9mm.',
            'Physical print, load/creep, vibration and endurance testing have not been performed.'],
        'source_sha256':{f:hashlib.sha256((ROOT/'source'/f).read_bytes()).hexdigest() for f in ['build_mounted_design.py','module_clamps_a.py']},
        'checked_local_step_sha256':{f:hashlib.sha256((OUT/'step'/f).read_bytes()).hexdigest() for f in ['P05_BATTERY_cradle.step','P06_BUCK_cradle.step','P07_SPEAKER_cradle.step']},
        'physical_test':False,'load_test':False,
        'standards_sources':[
            {'item':'M3 ISO7380 head OD5.7 height1.65 pitch.5','url':'https://www.accu.co.uk/socket-button-screws/8104-SSB-M3-12-A2'},
            {'item':'M3 DIN985 locknut height4 pitch.5','url':'https://www.accu.co.uk/hexagon-nylon-locking-nuts/495536-HNN-M3-0-5-C8-Z'},
            {'item':'M3 ISO7092 washer ID3.2 OD6, about.5 thick; page max.55','url':'https://www.accu.co.uk/metric-flat-washers/629061-HRDW-M3-6-0-A4-BL'}]}
    (OUT/'checks/hardware_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','hardware_groups','static_errors','metal_pair_errors','lid_motion_errors','keeper_motion_errors']},ensure_ascii=False),flush=True)
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
