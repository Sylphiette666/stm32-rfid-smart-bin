from pathlib import Path
import json,cadquery as cq
O=Path(__file__).resolve().parents[1];B=O.parent
def box(x,y,z,a,b,c):return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()
s=cq.importers.importStep(str(O/'step/LOWER_H41_B1.step')).val();checks=[]
for side,y in [('LEFT',14),('RIGHT',206)]:
 old=cq.importers.importStep(str(B/'motor-existing-holes-20261102/step'/f'D06_SEAT_{side}_ASSEMBLY.step')).val()
 ymin=-13 if side=='LEFT' else -15
 datum=box(82,y+ymin,-25,28,28,3)
 a=old.intersect(datum);b=s.intersect(datum)
 change=a.cut(b).Volume()+b.cut(a).Volume();assert change<1e-4,(side,change)
 for dy in [-10.5,10.5]:
  void=box(90.001,y+dy-1.199,-26,11.998,2.398,33)
  assert s.intersect(void).Volume()<1e-5
 checks.append({'side':side,'slot_centre_datum':[96,y],'slot_size':[12,2.4],'slot_pitch':21,
 'contact_plane_z':-25,'contact_thickness':3,'contact_geometry_difference_mm3':change,'wheel_side_ligament':1.3})
upper=cq.importers.importStep(str(O/'step/UPPER_INTEGRATED.step')).val()
panel=cq.importers.importStep(str(O/'step/PANEL_REMOVABLE_REFERENCE.step')).val()
inter=upper.intersect(panel).Volume();assert inter<1e-4,inter
r={'units':'mm','status':'PASS','motor':checks,'removable_panel_vs_upper_intersection_mm3':inter,
 'lower_outline':[280,220,5],'upper_platform_outline':[240,190,5],
 'upper_platform_offset_from_lower':[20,15,65],'main_shell_outer':[160,150,180],
 'shell_position_on_upper':[50,20,5],'pcb_holes':[[115,65],[205,65],[115,155],[205,155]],
 'caster_holes':[[240,90],[240,130]],'caster_seat_z':-41,
 'tracker_holes':[[185,80.25],[185,139.75]],'tracker_seat_z':-43.4,
 'physical_fit_confirmed':'only previous separate motor core user fit; all new integral assembly unprinted'}
(O/'checks/critical_dimensions.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r))
