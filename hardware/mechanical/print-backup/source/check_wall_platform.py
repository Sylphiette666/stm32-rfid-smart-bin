"""Check four proposed mounting points in the existing P02 solid; no drilling action."""
from pathlib import Path
import cadquery as cq
import json
B=Path(__file__).resolve().parents[1];O=B/'wall-panels-20261102'
s=cq.importers.importStep(str(B/'step/P02_light.step')).val()
checks=[]
for x,y in [(90,13),(170,13),(90,177),(170,177)]:
 probe=cq.Solid.makeCylinder(4.5,5,cq.Vector(x,y,0))
 void=probe.cut(s).Volume();assert void<1e-5,(x,y,void)
 checks.append({'P02_local_xy_mm':[x,y],'material_test_diameter_mm':9,'material_test_height_mm':5,'missing_material_mm3':void})
(O/'checks/platform_mounts.json').write_text(json.dumps({'status':'PASS_GEOMETRY_ONLY','proposed_drill_diameter_mm':3.4,'points':checks,'drill_only_after_physical_dry_fit':True,'existing_platform_modified':False},indent=2)+'\n',encoding='utf-8')
print('All four platform locations have full 5 mm material in 9 mm diameter lands')
