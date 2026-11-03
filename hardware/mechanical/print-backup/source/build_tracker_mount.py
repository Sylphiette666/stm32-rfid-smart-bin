"""Light tracker mount using two existing P01 splice holes (mm)."""
from pathlib import Path
import json, math, zipfile, xml.etree.ElementTree as ET
import cadquery as cq
import trimesh
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

B = Path(__file__).resolve().parents[1]
O = B/'tracker-mount-20261103'
for n in ('parts','step','checks','source'):(O/n).mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
anchors=[(150,88),(150,116)]
sensor=[(185,80.25),(185,139.75)]
design=load(B/'flat-split-20261101/source/design.json')
assert all(list(p) in design['joint']['new_holes'] for p in anchors)
lines=[LineString([(150,88),(170,88),(185,80.25)]).buffer(4,cap_style=1,join_style=1),
       LineString([(150,116),(170,116),(185,139.75)]).buffer(4,cap_style=1,join_style=1),
       LineString([(170,88),(170,116)]).buffer(3.5,cap_style=1)]
outline=unary_union(lines+[Point(*p).buffer(6,resolution=24) for p in anchors+sensor]).buffer(0)
assert outline.geom_type=='Polygon'
plate=cq.Workplane('XY').polyline(list(outline.exterior.coords)).close().extrude(3).val().translate((0,0,-8))
for x,y in anchors+sensor:plate=plate.cut(cq.Solid.makeCylinder(1.7,5,cq.Vector(x,y,-9)))
plate=plate.clean()
assert plate.isValid() and len(plate.Solids())==1
base=cq.importers.importStep(str(B/'flat-split-20261101/step/P01_FRONT_HALF.step')).val()
bridge=cq.importers.importStep(str(B/'flat-split-20261101/step/P01_SPLICE_BRIDGE.step')).val()
right=cq.importers.importStep(str(B/'motor-existing-holes-light-20261103/step/D06_CARRIER_RIGHT_ASSEMBLY.step')).val()
left=cq.importers.importStep(str(B/'motor-existing-holes-light-20261103/step/D06_CARRIER_LEFT_ASSEMBLY.step')).val()
for name,shape in [('base',base),('left_carrier',left),('right_carrier',right)]:
    assert plate.intersect(shape).Volume()<1e-5,(name,plate.intersect(shape).Volume())
for y in (82,110,138):assert plate.intersect(bridge.translate((138,y,-5))).Volume()<1e-5
other_bolts=[p for p in design['joint']['new_holes'] if list(p) not in [list(a) for a in anchors]]
for x,y in other_bolts:
    assert plate.intersect(cq.Solid.makeCylinder(3.3,7,cq.Vector(x,y,-11))).Volume()<1e-5,(x,y)
# A conservative complete board envelope: its 27 mm dimension follows the vehicle X axis.
board=cq.Workplane('XY').box(27,67,1.6).val().translate((185,110,-27.6))
assert board.intersect(right).Volume()<1e-5
assert board.intersect(left).Volume()<1e-5
assert 214-board.BoundingBox().xmax>=15
cq.exporters.export(plate,str(O/'step/TRACKER_FRAME_ASSEMBLY.step'))
bb=plate.BoundingBox();flat=plate.translate((-bb.xmin,-bb.ymin,8))
cq.exporters.export(flat,str(O/'parts/TRACKER_FRAME_PRINT.stl'),tolerance=.02,angularTolerance=.05)
spacers={}
for h in (14,18,22):
    s=cq.Solid.makeCylinder(4,h).cut(cq.Solid.makeCylinder(1.7,h))
    assert s.isValid() and len(s.Solids())==1
    cq.exporters.export(s,str(O/'parts'/f'SPACER_{h}_PRINT.stl'),tolerance=.02,angularTolerance=.05)
    cq.exporters.export(s,str(O/'step'/f'SPACER_{h}.step'))
    spacers[h]=s.Volume()
meshes=[]
layout=[('TRACKER_FRAME_PRINT',flat,(25,25))]+[(f'SPACER_{h}_PRINT',s,(90+i*18,25+j*18)) for i,h in enumerate((14,18,22)) for j in (0,1)]
for name,shape,(x,y) in layout:
    m=trimesh.load_mesh(O/'parts'/f'{name}.stl');m.merge_vertices(digits_vertex=5)
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,name
    m.apply_translation((x,y,0));meshes.append((name,m))
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
tag=lambda n:'{'+ns+'}'+n
root=ET.Element(tag('model'),{'unit':'millimeter'});resources=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'))
for i,(name,m) in enumerate(meshes,1):
    obj=ET.SubElement(resources,tag('object'),{'id':str(i),'name':name,'type':'model'});me=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(me,tag('vertices'));ts=ET.SubElement(me,tag('triangles'))
    for v in m.vertices:ET.SubElement(vs,tag('vertex'),dict(zip(('x','y','z'),map(str,v))))
    for f in m.faces:ET.SubElement(ts,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,f))))
    ET.SubElement(build,tag('item'),{'objectid':str(i)})
out=O/'TRACKER_LIGHT_GEOMETRY.3mf'
with zipfile.ZipFile(B/'flat-split-20261101/geometry/PLATE_3_GEOMETRY.3mf') as z0,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for n in ('[Content_Types].xml','_rels/.rels'):z.writestr(n,z0.read(n))
    z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
report={'status':'CAD_GEOMETRY_CHECKED','anchors_mm':anchors,'tracker_holes_mm':sensor,'tracker_hole_pitch_mm':59.5,'frame_thickness_mm':3,'board_envelope_mm':[27,67,1.6],'front_caster_protected_zone_start_x_mm':214,'board_to_zone_nominal_xy_gap_mm':15.5,'spacer_lengths_mm':[14,18,22],'volume_mm3':plate.Volume(),'spacer_volume_mm3':spacers,'collision_checks':['split base','three splice bridges','both motor carriers','other splice bolt envelopes','board versus motor carriers'],'physical_ground_height_unmeasured':True,'actual_caster_envelope_unmeasured':True,'actual_sensor_component_depth_unmeasured':True,'slicer_tested':False}
save(O/'checks/geometry.json',report)
print(json.dumps(report,ensure_ascii=False))
