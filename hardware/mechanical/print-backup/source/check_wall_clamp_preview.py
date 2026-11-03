"""Reopen the saved concept solids and verify hole, nut-pocket, and retaining-roof geometry."""
from pathlib import Path
import json,math,hashlib
import cadquery as cq
import trimesh
B=Path(__file__).resolve().parents[1];O=B/'wall-clamp-preview-20261103';d=json.loads((O/'checks/design.json').read_text(encoding='utf-8'));records=[]
for v in d['clamps']:
    n=v['id'];p=O/'step'/f'{n}_CONCEPT.step';s=cq.importers.importStep(str(p)).val();x,y=v['pressure'];ax,ay=v['anchor']
    assert s.isValid() and len(s.Solids())==1
    hole=cq.Solid.makeCylinder(1.65,20,cq.Vector(ax,ay,0));assert s.intersect(hole).Volume()<1e-5
    free=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.39).translate((x,y,10.205)).val();assert s.intersect(free).Volume()<1e-5
    roof=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.39).translate((x,y,12.605)).val().cut(cq.Solid.makeCylinder(1.71,3,cq.Vector(x,y,12.5)))
    assert abs(s.intersect(roof).Volume()-roof.Volume())<1e-5,'Pressure reaction roof missing'
    mesh=trimesh.load_mesh(O/'qa_meshes'/f'{n}.stl');mesh.merge_vertices(digits_vertex=5);assert mesh.is_watertight and len(mesh.split())==1
    records.append({'part':n,'STEP_reopened_valid_one_solid':True,'existing_anchor_bore_clear':True,'bottom_nut_insertion_pocket_clear':True,'retaining_roof_2_4_mm_present':True,'watertight_connected_QA_mesh':True,'STEP_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
a=cq.importers.importStep(str(O/'step/WALL_CLAMPS_ASSEMBLY_PREVIEW.step')).val();assert a.isValid()
result={'status':'PASS_CONCEPT_GEOMETRY_ONLY','parts':records,'assembly_STEP_reopened':True,'assembly_solid_count':len(a.Solids()),'manual_or_actual_load_test':False,'printing_profile_validated':False,'rated_strength_claimed':False}
(O/'checks/reopened_geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result))
