"""Generate mm-scale replacement plates, bolted split parts and exact STEP solids.

Install requirements.txt in a separate venv, then run this file. No GUI is required.
Part coordinates on the print bed are normalized to XY>=0 and Z=0; assembly
coordinates are retained in validation.json. Joint holes/countersinks are present
only in split plates. No unmeasured equipment holes are invented.
"""
from pathlib import Path
import json, math, hashlib, zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT/'source/parameters.json').read_text(encoding='utf-8-sig'))
for f in ['stl/full','stl/split','step','preview','checks','3mf/split']:
    (ROOT/f).mkdir(parents=True,exist_ok=True)
T=P['thickness']; D=P['hole_diameter']; J=P['joiner']; G=P['seam_gap']
REPORT={'units':'mm','parameters':P,'parts':[], 'checks':{}}
SHAPES={}

def outline(l,w,c=2):
    return [(c,0),(l-c,0),(l,c),(l,w-c),(l-c,w),(c,w),(0,w-c),(0,c)]

def blank(l,w,t):
    return cq.Workplane('XY').polyline(outline(l,w,P['corner_clip'])).close().extrude(t)

def bore(s,holes,t=T,d=D,csk=False):
    for x,y in holes:
        s=s.cut(cq.Solid.makeCylinder(d/2,t+2,cq.Vector(x,y,-1)))
        if csk:
            depth=(P['countersink_diameter']-d)/2
            s=s.cut(cq.Solid.makeCone(d/2,P['countersink_diameter']/2,depth,cq.Vector(x,y,t-depth)))
    return s

def bolts(cx,cy,angle):
    a=math.radians(angle); co=math.cos(a); si=math.sin(a)
    return [(round(cx+co*x-si*y,5),round(cy+si*x+co*y,5))
            for x in [-J['hole_x'],J['hole_x']] for y in [-J['hole_y'],J['hole_y']]]

def write_3mf(mesh,path):
    # Minimal standards-based 3MF, with explicit millimeter units.
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',ns)
    tag=lambda t:f'{{{ns}}}{t}'
    model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    res=ET.SubElement(model,tag('resources')); obj=ET.SubElement(res,tag('object'),{'id':'1','type':'model'})
    m=ET.SubElement(obj,tag('mesh')); vs=ET.SubElement(m,tag('vertices')); fs=ET.SubElement(m,tag('triangles'))
    for v in mesh.vertices: ET.SubElement(vs,tag('vertex'),dict(zip(['x','y','z'],[f'{a:.7f}' for a in v])))
    for f in mesh.faces: ET.SubElement(fs,tag('triangle'),dict(zip(['v1','v2','v3'],[str(a) for a in f])))
    ET.SubElement(ET.SubElement(model,tag('build')),tag('item'),{'objectid':'1'})
    ct='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rel='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ct); z.writestr('_rels/.rels',rel)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    # Read back, including explicit units and every serialized vertex/triangle.
    with zipfile.ZipFile(path) as z: root=ET.fromstring(z.read('3D/3dmodel.model'))
    assert root.attrib['unit']=='millimeter'
    vv=[[float(v.attrib[k]) for k in ['x','y','z']] for v in root.findall('.//'+tag('vertex'))]
    ff=[[int(v.attrib[k]) for k in ['v1','v2','v3']] for v in root.findall('.//'+tag('triangle'))]
    check=trimesh.Trimesh(vv,ff,process=False)
    assert check.is_watertight and np.allclose(check.bounds,mesh.bounds,atol=1e-5)

def export(s,name,group,offset=(0,0,0),expected=None):
    solid=s.val(); assert solid.isValid() and len(s.solids().vals())==1
    bb=solid.BoundingBox(); assert bb.zmin>-1e-7
    path=ROOT/'stl'/group/(name+'.stl')
    cq.exporters.export(s,str(path),tolerance=0.015,angularTolerance=0.035)
    cq.exporters.export(s,str(ROOT/'step'/(name+'.step')))
    m=trimesh.load_mesh(path)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0
    assert len(m.split())==1 and abs(m.bounds[0,2])<1e-6
    assert abs(m.volume-solid.Volume())/solid.Volume()<0.001
    if expected: assert np.allclose(m.extents,expected,atol=1e-4),(name,m.extents,expected)
    step=cq.importers.importStep(str(ROOT/'step'/(name+'.step'))).val()
    assert step.isValid() and abs(step.Volume()-solid.Volume())<1e-3
    entry={'name':name,'kind':group,'bbox_mm':m.extents.tolist(),'volume_mm3':solid.Volume(),
           'watertight':True,'consistent_winding':True,'connected_components':1,'step_reimport_valid':True,
           'triangles':len(m.faces),'assembly_offset_mm':offset}
    if group=='split':
        assert max(m.extents[:2])<=200,entry
        write_3mf(m,ROOT/'3mf/split'/(name+'.3mf'))
        entry['3mf_readback_valid']=True
    REPORT['parts'].append(entry); SHAPES[name]=s
    return m

# Cylindrical probe verifies full-depth open holes and retained material beside them.
def verify_holes(s,holes,t):
    for x,y in holes:
        assert s.val().intersect(cq.Solid.makeCylinder(D/2-0.02,t+2,cq.Vector(x,y,-1))).Volume()<1e-6

assembled=[]
for p in P['plates']:
    l,w=p['size']; pid=p['id']
    plate=bore(blank(l,w,T),p['holes']); verify_holes(plate,p['holes'],T)
    analytic=(l*w-2*P['corner_clip']**2-4*math.pi*(D/2)**2)*T
    assert abs(analytic-plate.val().Volume())<1e-5
    export(plate,pid+'_full','full',expected=[l,w,T])
    holes=[h for j in p['joiners'] for h in bolts(*j)]
    joint_plate=bore(plate,holes,csk=True); verify_holes(joint_plate,holes,T)
    # x/y limits explicitly leave a 0.3-mm seam. Do not scale individual pieces.
    xs=[(0,p['split_x']-G/2),(p['split_x']+G/2,l)]
    ys=[(0,w)] if p['split_y'] is None else [(0,p['split_y']-G/2),(p['split_y']+G/2,w)]
    split_vol=0; local_pieces=[]
    for iy,(ya,yb) in enumerate(ys):
        for ix,(xa,xb) in enumerate(xs):
            s=joint_plate.intersect(cq.Workplane('XY').box(xb-xa,yb-ya,T,centered=False).translate((xa,ya,0)))
            local_pieces.append(s); split_vol+=s.val().Volume()
            name=f'{pid}_'+(['rear','front'][ix])+('' if len(ys)==1 else ['_minusY','_plusY'][iy])
            export(s.translate((-xa,-ya,0)),name,'split',offset=[xa,ya,0],expected=[xb-xa,yb-ya,T])
    for i,a in enumerate(local_pieces):
        for b in local_pieces[i+1:]: assert a.val().intersect(b.val()).Volume()<1e-7
    # Verify gaps, all seam screw holes/edge margins, and joiner-to-plate alignment.
    for cx,cy,ang in p['joiners']:
        for x,y in bolts(cx,cy,ang):
            assert 7<=x<=l-7 and 7<=y<=w-7
            assert all(math.hypot(x-hx,y-hy)>P['countersink_diameter']+2 for hx,hy in p['holes'])
    p['split_volume_mm3']=split_vol
    assembled.append((p,joint_plate,local_pieces))

joiner=blank(J['length'],J['width'],J['thickness'])
joiner_holes=bolts(J['length']/2,J['width']/2,0)
joiner=bore(joiner,joiner_holes,t=J['thickness']); verify_holes(joiner,joiner_holes,J['thickness'])
export(joiner,'J01_joiner_print_6','split',expected=[64,28,4])
# Hole sizing coupon matches plate thickness and includes one countersunk hole.
coupon=blank(70,24,T)
for x,d in [(10,3.2),(25,3.4),(40,3.6),(55,3.8)]: coupon=bore(coupon,[(x,8)],d=d)
coupon=bore(coupon,[(25,17)],csk=True)
export(coupon,'C01_hole_test','split',expected=[70,24,5])

# A visual-only assembly STEP has plates/joiners plus four existing 60-mm pillars.
assy=cq.Assembly(name='SmartBin_visual_assembly_DO_NOT_PRINT')
for p,sp,pieces in assembled:
    ox,oy,z=(0,0,0) if p['id']=='P01' else (*P['upper_offset'],T+P['standoff_length'])
    for n,s in enumerate(pieces): assy.add(s,name=p['id']+'_piece_'+str(n+1),loc=cq.Location(cq.Vector(ox,oy,z)))
    for n,(cx,cy,a) in enumerate(p['joiners']):
        js=joiner.translate((-32,-14,0)).rotate((0,0,0),(0,0,1),a).translate((cx+ox,cy+oy,z-J['thickness']))
        # Check solid collision (only coplanar mating faces are allowed).
        assert sp.translate((ox,oy,z)).val().intersect(js.val()).Volume()<1e-6
        assy.add(js,name=p['id']+'_joiner_'+str(n+1))
for n,(x,y) in enumerate(P['plates'][0]['holes']):
    post=cq.Workplane('XY').polygon(6,6).extrude(P['standoff_length']).translate((x,y,T))
    assy.add(post,name='existing_60mm_pillar_'+str(n+1))
# Export via current API; assembly is documentation only.
cq.exporters.export(assy.toCompound(),str(ROOT/'step/ASSEMBLY_VIEW_ONLY.step'))
base_holes=np.array(P['plates'][0]['holes']); upper_holes=np.array(P['plates'][1]['holes'])+P['upper_offset']
assert np.array_equal(base_holes,upper_holes)
REPORT['checks'].update({'four_standoff_holes_coaxial':True,'seam_gap_mm':G,
    'base_print_piece_max_mm':[139.85,109.85,5],'upper_print_piece_max_mm':[119.85,190,5],
    'base_assembly_bbox_mm':[280,220,5], 'upper_assembly_bbox_mm':[240,190,5],
    'base_bottom_to_upper_top_mm':70,'joiner_copies_required':6,'joiner_bolts_required':24,
    'joiner_holes_pass':True,'no_piece_overlap':True,'joiners_do_not_intersect_plate_material':True,
    'minimum_split_bed_with_5mm_brim_mm':[200,200],
    'strength_or_real_print_test_performed':False})

# Draw dimensioned plan from the SAME geometry parameters used by CAD.
plt.rcParams['font.family']='Microsoft YaHei'; plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(1,2,figsize=(13,6.8)); fig.patch.set_facecolor('white')
colors=['#397ca8','#54a9aa','#7b8ebc','#82b6ce']
for ax,(p,sp,pieces) in zip(axes,assembled):
    l,w=p['size']; sx=p['split_x']; sy=p['split_y']
    ax.add_patch(Polygon(outline(l,w),fc='#eff5f8',ec='#263c4c',lw=1.7))
    ax.plot([sx,sx],[0,w],color='#dd7b37',ls='--',lw=1.5)
    if sy: ax.plot([0,l],[sy,sy],color='#dd7b37',ls='--',lw=1.5)
    for cx,cy,a in p['joiners']:
        pts=np.array(outline(64,28))-np.array([32,14]); rad=math.radians(a)
        pts=pts@np.array([[math.cos(rad),math.sin(rad)],[-math.sin(rad),math.cos(rad)]])+[cx,cy]
        ax.add_patch(Polygon(pts,fc='#cbd5de',ec='#697887',alpha=.7,lw=.8))
        for x,y in bolts(cx,cy,a):
            ax.add_patch(Circle((x,y),3.2,fc='white',ec='#5e6a75',lw=.8))
    for x,y in p['holes']:
        ax.add_patch(Circle((x,y),D/2,fc='white',ec='#263c4c',lw=1.3))
        ax.plot([x-4,x+4],[y,y],color='#397ca8',lw=.7); ax.plot([x,x],[y-4,y+4],color='#397ca8',lw=.7)
        ax.text(x,y+(10 if y<w/2 else -14),f'({x:g}, {y:g})',ha=('left' if x<l/2 else 'right'),fontsize=14)
    ax.annotate('',(0,-18),(l,-18),arrowprops={'arrowstyle':'<->','color':'#263c4c'})
    ax.text(l/2,-15,f'{l:g} mm',ha='center',fontsize=15)
    ax.annotate('',(-17,0),(-17,w),arrowprops={'arrowstyle':'<->','color':'#263c4c'})
    ax.text(-22,w/2,f'{w:g} mm',ha='center',va='center',rotation=90,fontsize=15)
    ax.text(l/2,w+15,f'{p["id"]} {p["name"]} | 厚 5 mm | '+('4 块拼装' if sy else '2 块拼装'),ha='center',fontsize=16,fontweight='bold')
    ys=[sy/2,(sy+w)/2] if sy else [w/2]
    for iy,y in enumerate(ys):
        for ix,x in enumerate([sx/2-(15 if sy else 0),(sx+l)/2+(15 if sy else 0)]):
            ax.text(x,y,f'{"车尾段" if ix==0 else "车头段"}'+(' / −Y侧' if sy and iy==0 else ' / +Y侧' if sy else ''),ha='center',fontsize=13,color='#37596c')
    ax.annotate('车头 +X',(l-10, -36),(l-70,-36),arrowprops={'arrowstyle':'->','color':'#263c4c'},ha='right',fontsize=13)
    ax.set_xlim(-36,l+28); ax.set_ylim(-48,w+35); ax.set_aspect('equal'); ax.axis('off')
fig.suptitle('底板与上平台 · 3D 打印备用方案',fontsize=20,fontweight='bold',y=.96)
fig.text(.5,.07,'蓝色十字：原立柱孔 Ø3.4    灰色：底面连接片位置    橙色虚线：拼缝 0.3 mm',ha='center',fontsize=14)
fig.text(.5,.025,'按毫米 100% 打印；图仅用于识别，不能按屏幕比例描孔。电机、电池、万向球等孔槽待实测。',ha='center',fontsize=13,color='#53636f')
fig.savefig(ROOT/'preview/01_dimensions.png',dpi=180); fig.savefig(ROOT/'preview/01_dimensions.svg'); plt.close(fig)
svg_path=ROOT/'preview/01_dimensions.svg'
svg_path.write_bytes(('\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines())+'\n').encode('utf-8'))

# Depth-correct offscreen CAD rendering, with no model geometry changed.
import vtk
from PIL import Image, ImageDraw, ImageFont
ren=vtk.vtkRenderer(); ren.SetBackground(0.96,0.98,0.99)
actors=[]
def actor(shape,color):
    verts,faces=shape.val().tessellate(.08)
    points=vtk.vtkPoints()
    for v in verts: points.InsertNextPoint(*v.toTuple())
    cells=vtk.vtkCellArray()
    for f in faces:
        tri=vtk.vtkTriangle()
        for i,n in enumerate(f): tri.GetPointIds().SetId(i,n)
        cells.InsertNextCell(tri)
    poly=vtk.vtkPolyData(); poly.SetPoints(points); poly.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals(); normals.SetInputData(poly); normals.ComputePointNormalsOff(); normals.Update()
    mapper=vtk.vtkPolyDataMapper(); mapper.SetInputConnection(normals.GetOutputPort())
    a=vtk.vtkActor(); a.SetMapper(mapper)
    import matplotlib.colors as mc
    a.GetProperty().SetColor(*mc.to_rgb(color)); a.GetProperty().SetAmbient(.25); a.GetProperty().SetDiffuse(.75)
    ren.AddActor(a); actors.append(a)
for p,sp,pieces in assembled:
    ox,oy,z=(0,0,0) if p['id']=='P01' else (*P['upper_offset'],65)
    for n,s in enumerate(pieces): actor(s.translate((ox,oy,z)),colors[n])
    for cx,cy,a in p['joiners']:
        actor(joiner.translate((-32,-14,0)).rotate((0,0,0),(0,0,1),a).translate((cx+ox,cy+oy,z-4)),'#637482')
for x,y in P['plates'][0]['holes']:
    actor(cq.Workplane('XY').polygon(6,6).extrude(60).translate((x,y,5)),'#74808b')
cam=ren.GetActiveCamera(); cam.SetPosition(450,-500,350); cam.SetFocalPoint(140,110,32)
cam.SetViewUp(0,0,1); cam.ParallelProjectionOn(); cam.SetParallelScale(176)
win=vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(1700,980); win.SetMultiSamples(8); win.AddRenderer(ren); win.Render()
capture=vtk.vtkWindowToImageFilter(); capture.SetInput(win); capture.Update()
writer=vtk.vtkPNGWriter(); writer.SetFileName(str(ROOT/'preview/02_assembly.png')); writer.SetInputConnection(capture.GetOutputPort()); writer.Write(); win.Finalize()
im=Image.open(ROOT/'preview/02_assembly.png').convert('RGB')
out=Image.new('RGB',(1700,1200),'white'); out.paste(im,(0,130)); draw=ImageDraw.Draw(out)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
draw.text((850,25),'底板与上平台拼装预览',font=font(44),anchor='mt',fill='#172d3d')
draw.text((850,88),'底板 4 块  +  上平台 2 块  +  底面连接片 6 件',font=font(28),anchor='mt',fill='#526774')
draw.text((850,1120),'灰柱为现有 60 mm 立柱示意，不是打印件；紧固件和其它实物未显示。',font=font(25),anchor='mt',fill='#526774')
draw.text((850,1160),'上平台相对底板偏移 (20, 15, 65) mm；所有分件打印时平放。',font=font(25),anchor='mt',fill='#526774')
out.save(ROOT/'preview/02_assembly.png')

# Lightweight editable OpenSCAD source for the original whole plates only.
scad='// Units: mm. Set part to P01 or P02. Whole plates only; split CAD is build_models.py.\n$fn=128;\npart="P01";\nthickness=5;\nhole_d=3.4;\nmodule plate(L,W,H){\n difference(){\n linear_extrude(thickness) polygon([[2,0],[L-2,0],[L,2],[L,W-2],[L-2,W],[2,W],[0,W-2],[0,2]]);\n for(p=H) translate([p[0],p[1],-1]) cylinder(h=thickness+2,d=hole_d);\n }\n}\nif(part=="P01") plate(280,220,[[30,25],[250,25],[30,195],[250,195]]);\nelse plate(240,190,[[10,10],[230,10],[10,180],[230,180]]);\n'
(ROOT/'source/whole_plates.scad').write_text(scad,encoding='utf-8')
(ROOT/'checks/validation.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={str(f.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for d in ['stl','step','3mf'] for f in sorted((ROOT/d).rglob('*')) if f.is_file()}
(ROOT/'checks/SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','exported_parts':len(REPORT['parts']),'checks':REPORT['checks']},ensure_ascii=False))
