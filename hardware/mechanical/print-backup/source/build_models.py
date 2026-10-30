"""Whole replacement plates and rigidly oriented P2S geometry; no splitting.

Run in a separate Python 3.12 environment with requirements.txt. The 3MF files
contain geometry and millimeter units, not machine presets or printable G-code.
"""
from pathlib import Path
import json,math,hashlib,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
import vtk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
P=json.loads((R/'source/parameters.json').read_text(encoding='utf-8-sig'))
for d in ['stl/full','stl/design','stl/P2S','stl/reference','3mf/P2S','3mf/reference','step','preview','checks']:(R/d).mkdir(parents=True,exist_ok=True)
REPORT={'status':'PASS','units':'mm','printer':P['printer'],'whole_parts_only':True,'parts':[],
 'physical_print_test':False,'load_test':False,'slicer_toolpath_test':False,'material':'PLA','rated_load_kg':None}
T=P['thickness'];D=P['hole_diameter']

def outline(l,w):
 c=P['corner_clip'];return [(c,0),(l-c,0),(l,c),(l,w-c),(l-c,w),(c,w),(0,w-c),(0,c)]
def plate(p):
 l,w=p['size'];s=cq.Workplane('XY').polyline(outline(l,w)).close().extrude(T)
 for x,y in p['holes']:
  s=s.cut(cq.Solid.makeCylinder(D/2,T+2,cq.Vector(x,y,-1)))
  assert s.val().intersect(cq.Solid.makeCylinder(D/2-.02,T+2,cq.Vector(x,y,-1))).Volume()<1e-7
 analytic=(l*w-2*P['corner_clip']**2-len(p['holes'])*math.pi*(D/2)**2)*T
 assert abs(s.val().Volume()-analytic)<1e-5
 return s

def write3mf(m,path):
 ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
 tag=lambda t:f'{{{ns}}}{t}'
 root=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
 obj=ET.SubElement(ET.SubElement(root,tag('resources')),tag('object'),{'id':'1','type':'model'})
 mesh=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(mesh,tag('vertices'));ts=ET.SubElement(mesh,tag('triangles'))
 for v in m.vertices:ET.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],[f'{n:.8f}'for n in v])))
 for f in m.faces:ET.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],[str(n)for n in f])))
 ET.SubElement(ET.SubElement(root,tag('build')),tag('item'),{'objectid':'1'})
 ct='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
 rel='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED)as z:
  z.writestr('[Content_Types].xml',ct);z.writestr('_rels/.rels',rel)
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 with zipfile.ZipFile(path)as z:root=ET.fromstring(z.read('3D/3dmodel.model'))
 assert root.attrib['unit']=='millimeter'
 vv=[[float(v.attrib[k])for k in ['x','y','z']]for v in root.findall('.//'+tag('vertex'))]
 ff=[[int(v.attrib[k])for k in ['v1','v2','v3']]for v in root.findall('.//'+tag('triangle'))]
 mm=trimesh.Trimesh(vv,ff,process=False)
 assert mm.is_watertight and mm.is_winding_consistent and np.allclose(mm.bounds,m.bounds,atol=1e-6)

def export(s,name,group,extents,brim=None):
 assert s.val().isValid()and len(s.solids().vals())==1
 dest=R/'stl'/group/(name+'.stl');cq.exporters.export(s,str(dest),tolerance=.015,angularTolerance=.035)
 m=trimesh.load_mesh(dest);assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 assert np.allclose(m.extents,extents,atol=1e-4)
 assert abs(m.volume-s.val().Volume())/s.val().Volume()<.001
 cq.exporters.export(s,str(R/'step'/(name+'.step')))
 back=cq.importers.importStep(str(R/'step'/(name+'.step'))).val();assert back.isValid()and abs(back.Volume()-s.val().Volume())<1e-3
 q={'name':name,'group':group,'bbox_mm':m.extents.tolist(),'bounds_mm':m.bounds.tolist(),'volume_mm3':s.val().Volume(),
    'connected_components':1,'watertight':True,'step_readback':True}
 if group in ['P2S','reference']:
  write3mf(m,R/'3mf'/group/(name+'.3mf'));q['3mf_readback']=True
  lim=np.array(P['printer']['build_volume_mm'])
  assert np.all(m.bounds[0]>=-1e-5)and np.all(m.bounds[1]<=lim+1e-5)
  padded=m.bounds.copy();padded[0,:2]-=brim;padded[1,:2]+=brim
  assert np.all(padded[0]>=-1e-5)and np.all(padded[1]<=lim+1e-5)
  q.update({'brim_allowance_mm':brim,'brim_conservative_bounds_mm':padded.tolist(),'within_p2s_nominal_volume':True})
 REPORT['parts'].append(q);return m

# 3-mm continuous mounting face and 2-mm underside pockets; original pads are 5 mm.
# The pocket closing edge satisfies y+z<=ymax, a 45-degree ramp in the
# original Y direction (P01's print-up direction), avoiding a wide pocket roof.
def lighten(s,p):
 depth=P['lightweight']['pocket_depth_mm'];skin=P['lightweight']['skin_mm']
 assert abs(T-depth-skin)<1e-8
 for i,(xa,ya,xb,yb) in enumerate(p['pockets']):
  for xc,yc,xd,yd in p['pockets'][i+1:]:
   dx=max(xa-xd,xc-xb,0);dy=max(ya-yd,yc-yb,0)
   assert math.hypot(dx,dy)>=P['lightweight']['minimum_grid_rib_mm']-1e-8
 for x0,y0,x1,y1 in p['pockets']:
  tool=cq.Workplane('XY').box(x1-x0,y1-y0,depth,centered=False).translate((x0,y0,0)).edges('|Z').fillet(3)
  tool=tool.edges('>Z').fillet(P['lightweight']['root_radius_mm'])
  wedge=cq.Workplane('YZ',origin=(x0-1,0,0)).polyline([(y0-1,0),(y1,0),(y1-depth,depth),(y0-1,depth)]).close().extrude(x1-x0+2)
  s=s.cut(tool.intersect(wedge))
 # Mounting pads and measured reference mounting zones remain the full thickness.
 for x,y in p['holes']:
  pad=cq.Solid.makeCylinder(14,T,cq.Vector(x,y,0)).cut(cq.Solid.makeCylinder(D/2,T,cq.Vector(x,y,0)))
  assert pad.intersect(plate(p).val()).cut(s.val()).Volume()<1e-6,(p['id'],x,y)
 for x0,y0,x1,y1 in p['solid_rectangles']:
  guard=cq.Workplane('XY').box(x1-x0,y1-y0,T,centered=False).translate((x0,y0,0)).val()
  assert guard.cut(s.val()).Volume()<1e-6
 # Entire 3-mm upper slab is unchanged, including original holes.
 slab=cq.Workplane('XY').box(p['size'][0],p['size'][1],skin,centered=False).translate((0,0,depth)).intersect(plate(p))
 assert slab.val().cut(s.val()).Volume()<1e-6
 return s

SOLID_PLATES=[plate(p)for p in P['plates']]
PLATES=[lighten(s,p)for s,p in zip(SOLID_PLATES,P['plates'])]
REPORT['lightweight_comparison']=[]
for p,solid,s in zip(P['plates'],SOLID_PLATES,PLATES):
 export(solid,p['id']+'_full','full',p['size']+[T])
 export(s,p['id']+'_light','design',p['size']+[T])
 v0=solid.val().Volume();v1=s.val().Volume()
 REPORT['lightweight_comparison'].append({'id':p['id'],'solid5_volume_mm3':v0,'light_volume_mm3':v1,'cad_volume_saved_percent':100*(1-v1/v0),'pocket_count':len(p['pockets']),'continuous_face_mm':P['lightweight']['skin_mm'],'full_mount_pad_mm':5,'guards_preserved':True})
def upright(s):
 out=s.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(0,0,1),45)
 b=out.val().BoundingBox();cx,cy=P['printer']['p01_bed_center_mm']
 return out.translate((cx-(b.xmin+b.xmax)/2,cy-(b.ymin+b.ymax)/2,-b.zmin))
rot=upright(PLATES[0]);span=(280+T)/math.sqrt(2)
export(rot,'P01_light_upright45','P2S',[span,span,220],P['printer']['p01_brim_mm'])
# Continuous mounting face on the bed; recesses face up, with no broad bridge.
flat=PLATES[1].rotate((0,0,0),(1,0,0),180).translate((8,223,5))
export(flat,'P02_light_face_down','P2S',[240,190,5],P['printer']['p02_brim_mm'])
export(upright(SOLID_PLATES[0]),'P01_solid5_upright45','reference',[span,span,220],12)
export(SOLID_PLATES[1].translate((8,33,0)),'P02_solid5_flat','reference',[240,190,5],5)
assert abs(rot.val().Volume()-PLATES[0].val().Volume())<1e-5
# A coupon has the same 5-mm thickness; an edge-standing one tests horizontal holes.
cp={'size':[70,24],'holes':[]};coupon=plate(cp)
for x,d in [(10,3.2),(25,3.4),(40,3.6),(55,3.8)]:coupon=coupon.cut(cq.Solid.makeCylinder(d/2,7,cq.Vector(x,12,-1)))
coupon=coupon.rotate((0,0,0),(1,0,0),90).translate((93,130.5,0))
export(coupon,'C01_upright_hole_test','P2S',[70,5,24],5)
assert np.array_equal(np.array(P['plates'][0]['holes']),np.array(P['plates'][1]['holes'])+P['upper_offset'])
REPORT['checks']={'minimum_12mm_inter_pocket_ribs_verified':True,'continuous_3mm_face_verified':True,'full_5mm_pads_and_reference_mount_zones_verified':True,'pocket_depth_mm':2,'pocket_closing_roof_degrees':45,'four_standoff_holes_coaxial':True,'no_split_or_joint_holes':True,'rigid_orientation_preserves_dimensions_and_volume':True,
 'p01_rotation':'Rotate original plate +90 degrees about X, then +45 degrees about printer Z; translate to center (128,128), bottom Z=0.',
 'p01_height_mm':220,'p01_with_12mm_brim_envelope_mm':[span+24,span+24,220],
 'p02_with_5mm_brim_envelope_mm':[250,200,5],'layer_gap_between_plates_mm':60,'base_bottom_to_upper_top_mm':70}

plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
fig,axs=plt.subplots(1,2,figsize=(13,6.2))
for ax,p in zip(axs,P['plates']):
 l,w=p['size'];ax.add_patch(Polygon(outline(l,w),fc='#edf5f8',ec='#2b4c60',lw=1.7))
 for x,y in p['holes']:
  ax.add_patch(Circle((x,y),D/2,fc='white',ec='#244c64'))
  ax.plot([x-4,x+4],[y,y],color='#397ca8',lw=.8);ax.plot([x,x],[y-4,y+4],color='#397ca8',lw=.8)
  ax.text(x,y+(12 if y<w/2 else -15),f'({x:g}, {y:g})',ha='left'if x<l/2 else'right',fontsize=14)
 ax.text(l/2,w+27,f'{p["id"]} {p["name"]}  {l:g}×{w:g}×5 mm',ha='center',fontsize=16,fontweight='bold')
 for x0,y0,x1,y1 in p.get('pockets',[]):
  from matplotlib.patches import FancyBboxPatch
  ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle='round,pad=0,rounding_size=3',fc='#b9d7e5',ec='#6591a7',lw=.8))
 ax.text(l/2,w+10,'底面示意 · 减薄腔深2 mm',ha='center',fontsize=12,color='#397ca8')
 ax.annotate('',(0,-18),(l,-18),arrowprops={'arrowstyle':'<->'});ax.text(l/2,-15,f'{l:g} mm',ha='center',fontsize=15)
 ax.annotate('',(-17,0),(-17,w),arrowprops={'arrowstyle':'<->'});ax.text(-23,w/2,f'{w:g} mm',rotation=90,ha='center',fontsize=15)
 ax.set_xlim(-38,l+28);ax.set_ylim(-40,w+48);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('PLA 整片轻量版 · 底面加强筋与减薄腔',fontsize=21,fontweight='bold')
fig.text(.5,.06,'浅蓝区域为底面凹腔；连续板面3 mm，筋与安装区5 mm；轮廓及原四个立柱孔保持。',ha='center',fontsize=14)
fig.savefig(R/'preview/01_dimensions.png',dpi=180);fig.savefig(R/'preview/01_dimensions.svg');plt.close(fig)
f=R/'preview/01_dimensions.svg';f.write_bytes((chr(10).join(s.rstrip()for s in f.read_text(encoding='utf-8').splitlines())+chr(10)).encode())

# Raster preview uses real tessellated solids and depth-buffered offscreen VTK.
def render(shapes,path,caption,subtitle,position,focal,scale,bed=False):
 ren=vtk.vtkRenderer();ren.SetBackground(.96,.98,.99);actors=[]
 if bed:shapes=[(cq.Workplane('XY').box(256,256,1,centered=False).translate((0,0,-1)),'#cbd4da')]+shapes
 for s,color in shapes:
  vs,fs=s.val().tessellate(.1);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
  for v in vs:pts.InsertNextPoint(*v.toTuple())
  for face in fs:
   tri=vtk.vtkTriangle()
   for i,n in enumerate(face):tri.GetPointIds().SetId(i,n)
   cells.InsertNextCell(tri)
  poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly);a=vtk.vtkActor();a.SetMapper(mapper)
  import matplotlib.colors as mc
  a.GetProperty().SetColor(*mc.to_rgb(color));a.GetProperty().SetAmbient(.3);a.GetProperty().SetDiffuse(.7)
  ren.AddActor(a);actors.append(a)
 cam=ren.GetActiveCamera();cam.SetPosition(*position);cam.SetFocalPoint(*focal);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1600,1050);win.SetMultiSamples(8);win.AddRenderer(ren);win.Render()
 cap=vtk.vtkWindowToImageFilter();cap.SetInput(win);cap.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(cap.GetOutputPort());writer.Write();win.Finalize()
 im=Image.open(path).convert('RGB');canvas=Image.new('RGB',(1600,1210),'white');canvas.paste(im,(0,100));d=ImageDraw.Draw(canvas)
 font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
 d.text((800,18),caption,font=font(40),anchor='mt',fill='#173749')
 d.text((800,1160),subtitle,font=font(24),anchor='mt',fill='#526774');canvas.save(path)
shapes=[(PLATES[0],'#397ca8'),(PLATES[1].translate((20,15,65)),'#54a9aa')]
for x,y in P['plates'][0]['holes']:shapes.append((cq.Workplane('XY').polygon(6,6).extrude(60).translate((x,y,5)),'#74808b'))
render(shapes,R/'preview/02_assembly.png','两片整板装配预览','四根灰柱为现有60 mm立柱示意；上平台偏移 (20,15,65) mm。',(450,-500,350),(140,110,32),176)
render([(rot,'#397ca8')],R/'preview/03_P01_upright.png','P2S 轻量底板整片打印方向','显示凹腔侧；实际文件已定向，包络约201.5×201.5×220 mm。灰面为256 mm热床。',(-230,490,390),(128,128,100),196,True)
render([(PLATES[0].rotate((0,0,0),(1,0,0),180),'#397ca8'),(PLATES[1].rotate((0,0,0),(1,0,0),180).translate((310,0,0)),'#54a9aa')],R/'preview/04_underside.png','PLA轻量版底面结构','上表面保持连续3 mm；5 mm外框、加强筋和安装区连接成整片。',(420,-650,460),(260,-110,0),218)
# Assembly STEP is a visual reference only; primary print files are under 3mf/P2S.
assy=cq.Compound.makeCompound([s.val()for s,c in shapes]);cq.exporters.export(assy,str(R/'step/ASSEMBLY_VIEW_ONLY.step'))
(R/'checks/validation.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for folder in ['stl','step','3mf']for p in sorted((R/folder).rglob('*'))if p.is_file()}
(R/'checks/SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','parts':len(REPORT['parts']),'checks':REPORT['checks']},ensure_ascii=False))
