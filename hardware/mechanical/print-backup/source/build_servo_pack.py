"""Build servo fixtures and a four-object, by-layer 256-mm plate.

The saved multi-object 3MF contains independent objects with baked positions.
It is not a printer preset or prevalidated G-code. This script also rebuilds the
underlying whole plates so tray mounting holes remain consistent everywhere.
"""
from pathlib import Path
import runpy,json,math,hashlib,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import MultiPoint,box
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle

R=Path(__file__).resolve().parents[1]
ns=runpy.run_path(str(R/'source/build_models.py'))
P=ns['P'];S=P['servo'];C=P['combined_plate'];render=ns['render'];export=ns['export']
(R/'3mf/combined').mkdir(parents=True,exist_ok=True)
(R/'stl/combined').mkdir(parents=True,exist_ok=True)

# P03 is a complete L stand, not a generic plate that still needs corner braces.
# CAD axes: x across 60-mm wall, y outward across 24-mm foot, z upward 190 mm.
stand=cq.Workplane('XY').box(60,5,190,centered=False)
stand=stand.union(cq.Workplane('XY').box(60,24,5,centered=False))
for x0 in [0,55]:
 gus=cq.Workplane('YZ',origin=(x0,0,0)).polyline([(5,5),(24,5),(5,45)]).close().extrude(5)
 stand=stand.union(gus)
# Slots use actual M3 clearance, but are generic adaptor rails, NOT servo ears.
for x in S['rail_x_mm']:
 tool=cq.Workplane('XY').box(3.4,7,36,centered=False).translate((x-1.7,-1,140))
 for z in [140,176]:tool=tool.union(cq.Solid.makeCylinder(1.7,7,cq.Vector(x,-1,z),cq.Vector(0,1,0)))
 stand=stand.cut(tool)
for x in S['foot_slot_x_mm']:
 tool=cq.Workplane('XY').box(3.4,6,7,centered=False).translate((x-1.7,11,-1))
 for y in [11,17]:tool=tool.union(cq.Solid.makeCylinder(1.7,7,cq.Vector(x,y,-1)))
 stand=stand.cut(tool)
stand=stand.clean()
# Tray has a U notch so the rear standoff screw remains accessible.
tray=cq.Workplane('XY').polyline(ns['outline'](80,40)).close().extrude(5)
notch=cq.Workplane('XY').box(12,10,7,centered=False).translate((4,0,-1)).union(cq.Solid.makeCylinder(6,7,cq.Vector(10,10,-1)))
tray=tray.cut(notch)
for x,y in S['tray_platform_holes_mm']+S['tray_stand_holes_mm']:
 tray=tray.cut(cq.Solid.makeCylinder(1.7,7,cq.Vector(x,y,-1)))
export(stand,'P03_servo_adjustable_stand','design',[60,24,190])
export(tray,'P04_servo_adjustable_tray','design',[80,40,5])
# Individual stand defaults to its broad wall face for more reliable separate printing.
stand_back=stand.rotate((0,0,0),(1,0,0),90).translate((98,223,0))
export(stand_back,'P03_stand_back_down','P2S',[60,190,24],12)
export(tray.translate((88,108,0)),'P04_tray_flat','P2S',[80,40,5],12)

# Verify the tray/upper platform interface in actual assembly coordinates.
upper=ns['PLATES'][1];stand_on_tray=stand.translate(tuple(S['stand_origin_on_tray_mm']))
assert tray.val().intersect(stand_on_tray.val()).Volume()<1e-7
assert upper.val().intersect(tray.translate(tuple(S['tray_origin_on_upper_mm'])).val()).Volume()<1e-7
for (u,v),(x,y) in zip(S['tray_platform_holes_mm'],P['plates'][1]['extra_holes']):assert (u,v+170)==(x,y)
for x,y in S['tray_stand_holes_mm']:
 # Tray fixed hole at v=28 falls inside the stand's y=11..17 adjustment slot.
 assert 11<=y-S['stand_origin_on_tray_mm'][1]<=17 and x in S['foot_slot_x_mm']
# Rear upper standoff (10,180) maps to tray (10,10), the center of the open notch.
assert np.linalg.norm(np.array([10,180])-np.array([0,170])-S['access_notch_center_mm'])<1e-8
access_probe=cq.Solid.makeCylinder(5,7,cq.Vector(10,10,-1));assert tray.val().intersect(access_probe).Volume()<1e-7
probe_above_upper=cq.Solid.makeCylinder(5,220,cq.Vector(10,180,5))
assert stand_on_tray.translate(tuple(S['tray_origin_on_upper_mm'])).val().intersect(probe_above_upper).Volume()<1e-7

# Two upright, PARALLEL panels; a flat upper panel cannot share this layout.
p01=ns['rot'].translate(tuple(C['p01_translation_from_individual_mm']))
d=C['p02_normal_offset_mm'];p02=ns['upright'](upper).translate((-d/math.sqrt(2),d/math.sqrt(2),0)).translate(tuple(C['p02_translation_after_normal_offset_mm']))
p03=stand.translate(tuple(C['p03_foot_origin_xyz']))
p04=tray.translate(tuple(C['p04_origin_xyz']))
items=[('P01_base',p01,'#397ca8'),('P02_upper',p02,'#54a9aa'),('P03_stand',p03,'#bd8859'),('P04_tray',p04,'#9c84b5')]
meshes=[];footprints=[];layout=[]
for name,shape,color in items:
 path=R/'stl/combined'/(name+'.stl');cq.exporters.export(shape,str(path),tolerance=.015,angularTolerance=.035)
 m=trimesh.load_mesh(path);assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 assert np.all(m.bounds[0]>=-1e-6)and np.all(m.bounds[1]<=[256,256,256])
 footprint=MultiPoint(m.vertices[:,:2]).convex_hull
 buffered=footprint.buffer(C['brim_mm'],quad_segs=48)
 assert box(0,0,256,256).covers(buffered),name
 assert buffered.intersection(box(*C['reserved_wrapping_zone_xy_mm'])).area<1e-7,name
 footprints.append(buffered);meshes.append(m)
 layout.append({'object':name,'bounds_mm':m.bounds.tolist(),'brim_mm':12,'within_p2s_volume':True,'full_xy_projection_with_brim_inside_bed':True})
clearances=[]
for i,(na,sa,ca) in enumerate(items):
 for j in range(i+1,len(items)):
  nb,sb,cb=items[j]
  assert sa.val().intersect(sb.val()).Volume()<1e-7
  assert footprints[i].intersection(footprints[j]).area<1e-7
  clearances.append({'a':na,'b':nb,'brim_edge_gap_mm':footprints[i].distance(footprints[j])})
assert min(c['brim_edge_gap_mm']for c in clearances)>2

# Standards-compliant multi-object 3MF with each object individually editable.
ns3='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns3);tag=lambda t:f'{{{ns3}}}{t}'
root=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
res=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'))
for oid,((name,s,c),m) in enumerate(zip(items,meshes),1):
 obj=ET.SubElement(res,tag('object'),{'id':str(oid),'type':'model','name':name})
 mesh=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(mesh,tag('vertices'));fs=ET.SubElement(mesh,tag('triangles'))
 for v in m.vertices:ET.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],[f'{n:.8f}'for n in v])))
 for f in m.faces:ET.SubElement(fs,tag('triangle'),dict(zip(['v1','v2','v3'],[str(n)for n in f])))
 ET.SubElement(build,tag('item'),{'objectid':str(oid)})
path=R/'3mf/combined/P2S_ALL4_BY_LAYER.3mf'
with zipfile.ZipFile(R/'3mf/P2S/P01_light_upright45.3mf')as old:
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
  for n in ['[Content_Types].xml','_rels/.rels']:z.writestr(n,old.read(n))
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
with zipfile.ZipFile(path)as z:rr=ET.fromstring(z.read('3D/3dmodel.model'))
assert len(rr.findall('.//'+tag('object')))==4 and len(rr.find(tag('build')))==4
for obj,original in zip(rr.findall('.//'+tag('object')),meshes):
 vv=[[float(v.attrib[k])for k in ['x','y','z']]for v in obj.findall('.//'+tag('vertex'))]
 ff=[[int(t.attrib[k])for k in ['v1','v2','v3']]for t in obj.findall('.//'+tag('triangle'))]
 back=trimesh.Trimesh(vv,ff,process=False);assert back.is_watertight and np.allclose(back.bounds,original.bounds,atol=1e-6)

# Bed-layout drawing uses conservative full-height XY projections with 12-mm brim.
fig,ax=plt.subplots(figsize=(9,9));colors=[c for n,s,c in items]
for footprint,(name,shape,c),m in zip(footprints,items,meshes):
 xy=np.array(footprint.exterior.coords);ax.fill(xy[:,0],xy[:,1],color=c,alpha=.18)
 hull=np.array(MultiPoint(m.vertices[:,:2]).convex_hull.exterior.coords);ax.fill(hull[:,0],hull[:,1],color=c,alpha=.85)
 lab={'P01_base':(160,132),'P02_upper':(82,135),'P03_stand':(204,44),'P04_tray':(58,200)}[name]
 ax.text(*lab,name.split('_')[0],ha='center',va='center',fontsize=16,fontweight='bold',color='#122c3b')
ax.add_patch(plt.Rectangle((0,0),256,256,fill=False,ec='#263b48',lw=2));ax.set_xlim(-8,264);ax.set_ylim(-8,264)
ax.set_aspect('equal');ax.set_xticks([0,64,128,192,256]);ax.set_yticks([0,64,128,192,256]);ax.grid(alpha=.15)
ax.set_title('P2S 四件同盘排布 · 必须逐层打印',fontsize=19,pad=18);ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm')
fig.text(.5,.02,f'浅色为12 mm brim保守预留；最小brim间隙 {min(c["brim_edge_gap_mm"]for c in clearances):.1f} mm。',ha='center',fontsize=12)
fig.savefig(R/'preview/05_combined_bed.png',dpi=170);plt.close(fig)
render([(s,c)for n,s,c in items],R/'preview/06_combined_3d.png','P2S 四件同盘整片打印','两块大板竖放；P03支架底脚着床；P04托片平放。必须按层打印。',(460,400,380),(128,128,105),205,True)
render([(stand,'#bd8859'),(tray.translate((85,0,0)),'#9c84b5')],R/'preview/07_servo_parts.png','舵机调节支架与托片','支架60×190×5 mm立板 + 60×24 mm底脚与双三角撑；托片80×40×5 mm。',(320,-360,260),(65,12,85),130)

report={'status':'PASS','printer':'Bambu Lab P2S','print_sequence_required':'by layer','brim_mm':12,'objects':layout,'pair_clearances':clearances,
 'minimum_brim_edge_gap_mm':min(c['brim_edge_gap_mm']for c in clearances),'independent_objects_in_3mf':4,'three_mf_roundtrip':True,
 'upper_has_two_new_tray_mount_holes_mm':P['plates'][1]['extra_holes'],'tray_upper_mapping_verified':True,'rear_standoff_tool_access_mm':10,
 'stand_tray_interfaces_verified':True,'original_four_standoff_holes_preserved':True,'servo_ear_pattern_verified':False,
 'physical_print_verified':False,'slicer_toolpath_verified':False,'reserved_wrapping_detection_zone_avoided':True,'rated_load_kg':None}
# Actual machine assembly reference with all four parts, preserving the two plate offsets.
servo_tray=tray.translate((20,185,70))
servo_stand=stand.translate((20,201,75))
assembly=[(ns['PLATES'][0],'#397ca8'),(upper.translate((20,15,65)),'#54a9aa'),(servo_tray,'#9c84b5'),(servo_stand,'#bd8859')]
for x,y in P['plates'][0]['holes']:
 assembly.append((cq.Workplane('XY').polygon(6,6).extrude(60).translate((x,y,5)),'#74808b'))
render(assembly,R/'preview/08_servo_install.png','支架、托片与平台装配关系','托片外伸20 mm；默认支架底脚位于托片局部(0,16)，后柱保留Ø10检修通道。',(430,-480,370),(140,110,110),203)
(R/'checks/combined_plate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Include fixture exports in the usual geometric validation record.
(R/'checks/validation.json').write_text(json.dumps(ns['REPORT'],ensure_ascii=False,indent=2),encoding='utf-8')
manifest={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for d in ['stl','step','3mf']for p in sorted((R/d).rglob('*'))if p.is_file()}
(R/'checks/SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','combined_objects':4,'minimum_brim_gap_mm':report['minimum_brim_edge_gap_mm'],'layout':layout},ensure_ascii=False))
