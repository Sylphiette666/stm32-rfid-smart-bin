"""Two-anchor, two-column caster riser; assembly coordinates in mm."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import cadquery as cq
import trimesh
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
B=Path(__file__).resolve().parents[1];O=B/'caster-riser-20261103'
for n in ('parts','step','checks','preview','source'):(O/n).mkdir(parents=True,exist_ok=True)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
a=[(205,65),(205,155)];c=[(240,90),(240,130)]
d=json.loads((B/'flat-split-20261101/source/design.json').read_text(encoding='utf8'))
assert all(any(h['name']=='A1_M3' and h['xy']==list(p) for h in d['mount_holes']) for p in a)
outline=unary_union([
 LineString([a[0],(218,76),c[0]]).buffer(4,cap_style=1,join_style=1),
 LineString([a[1],(218,144),c[1]]).buffer(4,cap_style=1,join_style=1),
 LineString(c).buffer(4,cap_style=1,join_style=1),
 *[Point(*p).buffer(7.5,resolution=32) for p in a+c]]).buffer(0)
assert outline.geom_type=='Polygon'
frame=cq.Workplane('XY').polyline(list(outline.exterior.coords)).close().extrude(4).val().translate((0,0,-4))
for x,y in c:frame=frame.fuse(cq.Solid.makeCylinder(8,3,cq.Vector(x,y,-7)))
for x,y in a:frame=frame.cut(cq.Solid.makeCylinder(1.7,6,cq.Vector(x,y,-5)))
for x,y in c:
 frame=frame.cut(cq.Solid.makeCylinder(1.7,9,cq.Vector(x,y,-8)))
 frame=frame.cut(cq.Solid.makeCylinder(3.2,2.2,cq.Vector(x,y,-2.2)))
frame=frame.clean();assert frame.isValid() and len(frame.Solids())==1
base=cq.importers.importStep(str(B/'flat-split-20261101/step/P01_FRONT_HALF.step')).val()
right=cq.importers.importStep(str(B/'motor-existing-holes-light-20261103/step/D06_CARRIER_RIGHT_ASSEMBLY.step')).val()
left=cq.importers.importStep(str(B/'motor-existing-holes-light-20261103/step/D06_CARRIER_LEFT_ASSEMBLY.step')).val()
tracker=cq.importers.importStep(str(B/'tracker-mount-20261103/step/TRACKER_FRAME_ASSEMBLY.step')).val()
for name,s in [('base',base),('right_motor',right),('left_motor',left),('tracker',tracker)]:assert frame.intersect(s).Volume()<1e-5,(name,frame.intersect(s).Volume())
for p in a+c:
 x,y=p; ann=cq.Solid.makeCylinder(4,5,cq.Vector(x,y,0)).cut(cq.Solid.makeCylinder(1.7,5,cq.Vector(x,y,0)))
 assert ann.cut(base).Volume()<1e-4,('deck_landing',p)
cq.exporters.export(frame,str(O/'step/CASTER_FRAME_ASSEMBLY.step'))
flat=frame.rotate((0,0,0),(1,0,0),180);bb=flat.BoundingBox();flat=flat.translate((-bb.xmin,-bb.ymin,-bb.zmin))
cq.exporters.export(flat,str(O/'parts/CASTER_FRAME_PRINT.stl'),tolerance=.02,angularTolerance=.05)
vol={};meshes={}
for H in (35,40,45):
 h=H-7
 # 13 mm outer diameter and 3.4 mm metal-fastener clearance: 4.8 mm radial wall.
 s=cq.Solid.makeCylinder(6.5,h).cut(cq.Solid.makeCylinder(1.7,h))
 assert s.isValid() and len(s.Solids())==1
 cq.exporters.export(s,str(O/'step'/f'CASTER_COLUMN_{H}.step'))
 path=O/'parts'/f'CASTER_COLUMN_{H}_PRINT.stl';cq.exporters.export(s,str(path),tolerance=.02,angularTolerance=.05)
 vol[H]=s.Volume()
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns);tag=lambda n:'{'+ns+'}'+n
template=B/'flat-split-20261101/geometry/PLATE_3_GEOMETRY.3mf'
for H in (35,40,45):
 items=[]
 for name,path,xy in [('CASTER_FRAME',O/'parts/CASTER_FRAME_PRINT.stl',(25,25)),('COLUMN_A',O/'parts'/f'CASTER_COLUMN_{H}_PRINT.stl',(145,35)),('COLUMN_B',O/'parts'/f'CASTER_COLUMN_{H}_PRINT.stl',(170,35))]:
  mesh=trimesh.load_mesh(path);mesh.merge_vertices(digits_vertex=5)
  assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,name
  mesh.apply_translation((*xy,0));items.append((name,mesh))
 root=ET.Element(tag('model'),{'unit':'millimeter'});resources=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'))
 for i,(name,m) in enumerate(items,1):
  obj=ET.SubElement(resources,tag('object'),{'id':str(i),'name':name,'type':'model'});me=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(me,tag('vertices'));ts=ET.SubElement(me,tag('triangles'))
  for v in m.vertices:ET.SubElement(vs,tag('vertex'),dict(zip(('x','y','z'),map(str,v))))
  for f in m.faces:ET.SubElement(ts,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,f))))
  ET.SubElement(build,tag('item'),{'objectid':str(i)})
 out=O/f'CASTER_RISER_H{H}_GEOMETRY.3mf'
 with zipfile.ZipFile(template) as z0,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for n in ('[Content_Types].xml','_rels/.rels'):z.writestr(n,z0.read(n))
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
save(O/'checks/geometry.json',{'status':'CAD_GEOMETRY_CHECKED','base_holes_mm':a,'caster_holes_mm':c,'caster_hole_pitch_mm':40,'base_to_caster_top_drop_variants_mm':[35,40,45],'frame_thickness_mm':4,'caster_pad_total_depth_mm':7,'counterbore_diameter_mm':6.4,'counterbore_depth_mm':2.2,'column_outer_diameter_mm':13,'column_bore_mm':3.4,'frame_volume_mm3':frame.Volume(),'column_volume_each_mm3':vol,'collision_checks':['split base','both motor carriers','tracker frame'],'caster_plate_hole_diameter_unmeasured':True,'caster_plate_footprint_unmeasured':True,'actual_Hb_unmeasured':True,'physical_strength_tested':False})
print((O/'checks/geometry.json').read_text(encoding='utf8'))
