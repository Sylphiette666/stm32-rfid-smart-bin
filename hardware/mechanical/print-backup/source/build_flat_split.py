"""Flat P2S revision: preserve the 280 x 220 chassis and bolt two halves together.
No electronic fixture, original post or wheel/caster reference zone is moved.
Run with the project's CadQuery environment. No physical strength claim.
"""
from pathlib import Path
import json, shutil, math
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'mounted-20261031'
OUT=ROOT/'flat-split-20261101'
for name in ['parts','step','source','checks','geometry','projects','preview']:(OUT/name).mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def box(x,y,z,w,h,t):return cq.Workplane('XY').box(w,h,t,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def bounds(s):
 b=s.BoundingBox();return [[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]]
def plate(x,y,w,h,t,r=0):
 s=cq.Workplane('XY').box(w,h,t,centered=False)
 if r:s=s.edges('|Z').fillet(r)
 return s.val().translate((x,y,0))
def export(ident,shape,flat):
 assert shape.isValid() and len(shape.Solids())==1,ident
 cq.exporters.export(shape,str(OUT/'step'/f'{ident}.step'))
 b=flat.BoundingBox();flat=flat.translate((-b.xmin,-b.ymin,-b.zmin))
 path=OUT/'parts'/f'{ident}.stl';cq.exporters.export(flat,str(path),tolerance=.018,angularTolerance=.05)
 m=trimesh.load_mesh(path);m.merge_vertices(digits_vertex=5);m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,ident
 assert abs(m.volume-shape.Volume())/shape.Volume()<.005
 m.export(path)
 return {'id':ident,'stl':f'parts/{ident}.stl','step':f'step/{ident}.step','print_extents':m.extents.tolist(),'assembly_bounds':bounds(shape),'volume_mm3':shape.Volume()}
# Preserve all published fixtures exactly; they have already passed fit/motion CAD audits.
design=load(OLD/'source/design.json')
for r in design['parts']:
 for key in ['stl','step']:shutil.copy2(OLD/r[key],OUT/r[key])
base=cq.importers.importStep(str(OLD/'step/P01_MOUNTED_BASE.step')).val()
original=base
# Continuous joint land plus flat seats under three separately bolted splice plates.
lands=[box(130,0,0,17,220,5)]+[box(118,y-12,0,40,24,5) for y in [82,110,138]]
base=base.fuse(*lands).clean()
# Recut every original through-hole, including any crossed by added lands.
original_holes=design['mount_holes']+[{'xy':[x,y],'diameter':3.4} for x,y in [(30,25),(250,25),(30,195),(250,195)]]
for h in original_holes:base=base.cut(cyl(*h['xy'],-1,h['diameter']/2,7))
joint_holes=[(x,y+d) for y in [82,110,138] for x in [126,150] for d in [-6,6]]
for x,y in joint_holes:base=base.cut(cyl(x,y,-1,1.7,7))
# Two horizontal insertion tongues locate the halves; bolts/plates carry the seam load.
left=base.intersect(box(-1,-1,-1,138.85,222,7)) # ends at X=137.85
right=base.intersect(box(138.15,-1,-1,142.85,222,7))
for y in [32,174]:
 tongue=plate(136,y,8,16,5,.8)
 recess=plate(135.75,y-.25,8.5,16.5,5,.8)
 left=left.fuse(tongue)
 right=right.cut(recess)
left=left.clean();right=right.clean()
# Flat underside splice plates, with four bolts each. Keep wheels/caster zones clear.
bridge=plate(-20,-12,40,24,5,2)
for x in [-12,12]:
 for y in [-6,6]:bridge=bridge.cut(cyl(x,y,-1,1.7,7))
bridge=bridge.clean()
newparts=[]
for ident,s in [('P01_REAR_HALF',left),('P01_FRONT_HALF',right)]:newparts.append(export(ident,s,s.rotate((0,0,0),(1,0,0),180)))
newparts.append(export('P01_SPLICE_BRIDGE',bridge,bridge))
# Retain upper/stand/tray unchanged; standardize flat printing orientation.
for ident,f,rotation in [('P02_UPPER','P02_UPPER_DESIGN.step',True),('P03_STAND','P03_STAND_DESIGN.step',False),('P04_TRAY','P04_TRAY_DESIGN.step',False)]:
 s=cq.importers.importStep(str(OLD/'step'/f)).val()
 flat=s.rotate((0,0,0),(1,0,0),180) if rotation else s
 if ident=='P03_STAND':flat=s.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,0,1),90)
 newparts.append(export(ident,s,flat))
assert left.intersect(right).Volume()<1e-6
assembled=left.fuse(right)
for h in original_holes:
 assert assembled.intersect(cyl(*h['xy'],-1,1.69,7)).Volume()<1e-5,h
# Original protected motor and front caster zones remain geometrically unchanged.
zones=[(45,0,135,50),(45,170,135,220),(214,78,270,142)]
for x0,y0,x1,y1 in zones:
 region=box(x0,y0,-.1,x1-x0,y1-y0,5.2)
 assert original.intersect(region).cut(assembled).Volume()<1e-5,(x0,y0)
# Remove prior base only for checking top-side screw envelopes against all existing fixtures.
fixture_shapes=[]
for m in design['modules']:
 for r in [p for p in design['parts'] if p['module']==m['id']]:
  s=cq.importers.importStep(str(OLD/r['step'])).val().rotate((0,0,0),(0,0,1),m['rotation']).translate((*m['layout_origin'],5))
  fixture_shapes.append((r['id'],s))
metal_errors=[]
for x,y in joint_holes:
 head=cyl(x,y,5,3,2.15) # OD6 washer and ISO7380 head envelope, conservative cylinder.
 for ident,s in fixture_shapes:
  if head.intersect(s).Volume()>1e-5:metal_errors.append([x,y,ident])
assert not metal_errors,metal_errors
bridge_assembly=[]
for y in [82,110,138]:
 s=bridge.translate((138,y,-5));bridge_assembly.append(s)
 assert s.intersect(left).Volume()<1e-6 and s.intersect(right).Volume()<1e-6
 for x0,y0,x1,y1 in zones:assert s.intersect(box(x0,y0,-10,x1-x0,y1-y0,20)).Volume()<1e-6
scene=cq.Assembly();scene.add(left,name='P01_REAR_HALF',color=cq.Color('#4186a3'));scene.add(right,name='P01_FRONT_HALF',color=cq.Color('#70a9b4'))
for i,s in enumerate(bridge_assembly):scene.add(s,name=f'BRIDGE_{i+1}',color=cq.Color('#d59b4b'))
scene.save(str(OUT/'step/P01_ASSEMBLY_VIEW_ONLY.step'))
# Assembly STL exports are for rendering, never offered as printing geometry.
for ident,s in [('rear',left),('front',right)]+[(f'bridge{i+1}',s) for i,s in enumerate(bridge_assembly)]:cq.exporters.export(s,str(OUT/'source'/f'assembly_{ident}.stl'))
design.update({'status':'flat_split_geometry_checked_slicing_pending','base_one_piece':False,'upper_one_piece':True,'parts':design['parts']+newparts,'joint':{'split_x':138,'gap_mm':.3,'tongue_clearance_each_side_mm':.25,'bridge_size_mm':[40,24,5],'bridge_centres':[[138,y] for y in [82,110,138]],'new_holes':joint_holes,'hardware':'12 x M3x16 ISO7380 low round head, 24 x OD6 washer 0.5, 12 x DIN985 M3 locknut height4','below_base_extension_mm':10.5,'above_base_extension_mm':2.15},'print_notes':['所有板件完全平放；不使用原斜撑工程。','底板组装尺寸仍为280x220x5；两片定位后用三个底部连接片和12颗M3螺钉固定。','上平台一整片；模块卡座和原孔位不缩放、不移动。'],'decision':'250mm shortened base would truncate original caster land X214..270 and change original front post/upper registration; preserve original dimensions using newly authorized split option.'})
write(OUT/'source/design.json',design)
report={'status':'PASS','original_envelope_mm':[280,220,5],'original_hole_count_preserved':len(original_holes),'new_join_hole_count':12,'halves_no_intersection':True,'single_solid_each_part':True,'fixture_head_collisions':metal_errors,'original_motor_caster_zones_unchanged':True,'original_posts_and_upper_offset_preserved':True,'joint_hardware_below_A1_board_clearance_mm':7.85,'new_bridge_intrusion_below_original_base_mm':10.5,'reference_ground_clearance_mm':34.5,'reference_Hb_mm':45,'actual_underbody_geometry_unmeasured':True,'physical_print_test':False,'load_tested':False,'parts_added':newparts}
write(OUT/'checks/assembly.json',report)
print(json.dumps(report,ensure_ascii=False),flush=True)
