"""Render actual concept BReps; positional diagram is explicitly a mounting scheme."""
from pathlib import Path
import json, math
import cadquery as cq
import vtk
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
B=Path(__file__).resolve().parents[1];O=B/'wall-clamp-preview-20261103'
d=json.loads((O/'checks/design.json').read_text(encoding='utf-8'))
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
P=cq.importers.importStep(str(B/'step/P02_light.step')).val()
T=cq.importers.importStep(str(B/'step/P04_servo_adjustable_tray.step')).val().translate((0,170,5))
S=cq.importers.importStep(str(B/'step/P03_servo_adjustable_stand.step')).val().translate((0,186,10))
transforms={
 'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],
 'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],
 'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],
 'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
W={n:cq.importers.importStep(str(B/'wall-panels-20261102/step'/f'{n}.step')).val().transformGeometry(cq.Matrix(m)) for n,m in transforms.items()}
C={v['id']:cq.importers.importStep(str(O/'step'/f"{v['id']}_CONCEPT.step")).val() for v in d['clamps']}
pad=lambda x,y:cq.Solid.makeCylinder(4,1.2,cq.Vector(x,y,8.2)).cut(cq.Solid.makeCylinder(1,.4,cq.Vector(x,y,9.1)))
def cy(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def hardware(v):
    x,y=v['pressure'];ax,ay=v['anchor'];z=v['anchor_top_z'];l=16 if z==11 else 20
    nut=cq.Workplane('XY').polygon(6,5.5/math.cos(math.pi/6)).extrude(2.4).translate((x,y,10.2)).val().cut(cy(x,y,10,1.5,4))
    return [cy(x,y,9.4,1.5,8).fuse(cy(x,y,17.4,2.85,1.65)),nut,cy(ax,ay,z+.5-l,1.5,l).fuse(cy(ax,ay,z+.5,2.85,1.65)),cy(ax,ay,z,3,.5).cut(cy(ax,ay,z-.1,1.6,.7))]
gray=(.48,.58,.64);blue=(.53,.74,.81);green=(.19,.59,.37);orange=(.95,.64,.25);metal=(.56,.59,.63);purple=(.68,.57,.76)
def actor(shape,color,zclip=None):
    vertices,faces=shape.tessellate(.09);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vertices:pts.InsertNextPoint(v.x,v.y,v.z)
    for f in faces:
        tr=vtk.vtkTriangle()
        for i,j in enumerate(f):tr.GetPointIds().SetId(i,j)
        cells.InsertNextCell(tr)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(30);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    if zclip is not None:
        plane=vtk.vtkPlane();plane.SetOrigin(0,0,zclip);plane.SetNormal(0,0,-1);mapper.AddClippingPlane(plane)
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color);a.GetProperty().SetAmbient(.18);a.GetProperty().SetDiffuse(.8)
    return a
def scene(mode='all',exploded=False):
    items=[]
    if mode!='part':
        items=[(P,gray,None),(T,purple,None),(S,(.66,.55,.45),32)]
        items += [(w,blue,30) for w in W.values()]
    for v in d['clamps']:
        n=v['id']
        if mode=='part' and n!='C1_LEFT_REAR':continue
        items.append((C[n],green,None))
        x,y=v['pressure'];items.append((pad(x,y),orange,None))
        items += [(m,metal,None) for m in hardware(v)]
    return items
def render(items,name,pos,focal,scale,size=(1800,1050),marks=None,up=(0,0,1)):
    r=vtk.vtkRenderer();r.SetBackground(1,1,1)
    for sh,col,clip in items:r.AddActor(actor(sh,col,clip))
    cam=r.GetActiveCamera();cam.SetPosition(*pos);cam.SetFocalPoint(*focal);cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(*size);win.AddRenderer(r);win.Render()
    f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();w=vtk.vtkPNGWriter();w.SetFileName(str(O/'preview'/name));w.SetInputConnection(f.GetOutputPort());w.Write()
    coords=[]
    for label,pt in marks or []:
        r.SetWorldPoint(*pt,1);r.WorldToDisplay();x,y,z=r.GetDisplayPoint();coords.append((label,x,size[1]-y))
    win.Finalize();im=Image.open(O/'preview'/name).convert('RGB');dr=ImageDraw.Draw(im)
    for lab,x,y in coords:
        dr.ellipse((x-24,y-24,x+24,y+24),fill='white',outline='#20583a',width=3);dr.text((x,y-1),lab,font=font(29),fill='#20583a',anchor='mm')
    im.save(O/'preview'/name);return im
def sheet(im,name,title,subtitle,lines):
    out=Image.new('RGB',(1800,1390),'white');dr=ImageDraw.Draw(out)
    dr.text((45,20),title,font=font(43),fill='#152d37');dr.text((45,78),subtitle,font=font(29),fill='#4b5e67')
    out.paste(im,(0,130))
    for i,line in enumerate(lines):dr.text((45,1190+46*i),line,font=font(30),fill='#203d49')
    out.save(O/'preview'/name)
marks=[(f'C{i+1}',(*v['pressure'],20)) for i,v in enumerate(d['clamps'])]
im=render(scene(),'raw_overview.png',(-180,-290,420),(125,100,6),145,marks=marks)
sheet(im,'01_mounting_overview.png','筒壁免钻孔压脚转接件  方案预览','绿色＝新压脚；蓝色＝原筒壁；灰色＝P02上平台；紫色＝原舵机托片',[
 '筒壁仍贴着上平台：不垫高、不新增P02孔；4只压脚压住原底脚。',
 'C1／C2／C3共用立柱孔；C4共用舵机托片孔，保留后角孔的工具通道。',
 '为看清底脚，筒壁和舵机竖架只显示下部；实际筒壁高度仍为180mm。',
 '概念模型：尚未发布打印工程，未做实物承载与塑料蠕变验证。'])
im=render(scene(),'raw_regular.png',(-45,-86,96),(55,8,8),37,marks=[('1',(10,10,14)),('2',(47,-2,3)),('3',(90,13,21)),('4',(90,13,8.8))])
sheet(im,'02_pressure_clamp_detail.png','普通压脚 C1  安装关系','压脚压在原底脚上方；螺丝通过金属螺母施压，不穿入上平台',[
 '1  固定端：借用现有立柱孔，拟用M3×16和原立柱连接。',
 '2  贴边挡肩：沿P02外边缘限位；底脚两侧的小挡块限制前后滑动。',
 '3  M3×8调压螺丝＋底装M3螺母；上留2.4mm挡肩，螺丝头保持悬空。',
 '4  橙色小压垫：Ø8×1.2mm，跨过原底脚孔，轻压3.2mm厚底脚。'])
im=render(scene(),'raw_servo.png',(150,255,110),(69,181,10),36,marks=[('1',(70,180,17)),('2',(81,187,8)),('3',(90,177,22))])
sheet(im,'03_servo_side_detail.png','舵机侧后压脚 C4  绕开原托片','紫色托片不改孔；压脚固定端坐在托片上方，末端压住筒壁底脚',[
 '1  共用舵机托片现有孔（70,180），拟换M3×20；下方继续用锁母固定。',
 '2  绕过托片X＝80的边缘，并设置挡肩防转；不占用原竖架。',
 '3  末端压住原底脚（90,177）；橙色压垫和调压螺丝同普通压脚。',
 '后角立柱孔（10,180）保持可用，本局部图未显示；位置见下一张图。'])
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(12,8.6));ax.add_patch(Rectangle((0,0),240,190,fc='#eef2f5',ec='#4c6676',lw=2));ax.add_patch(Rectangle((50,20),160,150,fc='#d0e6ec',ec='#458ca0',lw=2));ax.add_patch(Rectangle((53,23),154,144,fc='white',ec='#458ca0',lw=1));ax.add_patch(Rectangle((0,170),80,40,fc='#e0d0e9',ec='#8f72a4',lw=1.5))
for v in d['clamps']:
    n=v['id'].split('_')[0];a=v['anchor'];p=v['pressure'];ax.plot([a[0],p[0]],[a[1],p[1]],color='#338557',lw=8,alpha=.8);ax.plot(*a,'o',ms=10,mfc='#255536',mec='white');ax.plot(*p,'s',ms=9,mfc='#eeae56',mec='#7d521c')
    mid=(a[0]+p[0])/2;yy=-18 if p[1]<50 else 224 if n=='C4' else 207
    ax.annotate(f'{n}  固定({a[0]},{a[1]}) → 压点({p[0]},{p[1]})',xy=(mid,(a[1]+p[1])/2),xytext=(mid,yy),ha='center',fontsize=10,arrowprops=dict(arrowstyle='-',color='#697e86'))
ax.add_patch(Circle((10,180),3.5,fc='white',ec='#596a76',lw=1.5));ax.annotate('后角孔保留',xy=(10,180),xytext=(-5,135),fontsize=10,arrowprops=dict(arrowstyle='->'))
ax.text(130,99,'原筒壁主框 160×150\n位置保持\nP02继续作为桶底',ha='center',va='center',fontsize=15,color='#315465');ax.text(36,193,'原舵机托片',ha='center',fontsize=10,color='#634c75')
ax.text(245,93,'前\nX=240',ha='left',fontsize=11);ax.text(-5,82,'后\nX=0',ha='right',fontsize=11);ax.text(130,180,'舵机侧',ha='center',fontsize=11);ax.text(130,8,'非舵机侧',ha='center',fontsize=11)
ax.set_xlim(-24,270);ax.set_ylim(-34,237);ax.set_aspect('equal');ax.set_xlabel('X / mm   原点为P02后侧与非舵机侧的外角');ax.set_ylabel('Y / mm');ax.grid(alpha=.13)
fig.suptitle('现有固定孔与原底脚压点的位置关系  概念定位图',fontsize=17,y=.97);fig.text(.1,.025,'绿圆＝借用现有孔；橙方＝施压点，不是新钻孔。筒壁外置控制盒未画。',fontsize=11);fig.tight_layout(rect=[.02,.05,.98,.94]);fig.savefig(O/'preview/04_anchor_plan.png',dpi=170);plt.close(fig)
# Four-view review of actual solids, independent of dimension scheme.
for v in d['clamps']:
    n=v['id'];bb=C[n].BoundingBox();cx=(bb.xmin+bb.xmax)/2;cyy=(bb.ymin+bb.ymax)/2;cz=(bb.zmin+bb.zmax)/2
    views=[('ISO',(cx-80,cyy-100,cz+90),(0,0,1)),('TOP',(cx,cyy,cz+100),(0,1,0)),('FRONT',(cx,cyy-100,cz),(0,0,1)),('RIGHT',(cx+100,cyy,cz),(0,0,1))]
    out=Image.new('RGB',(1800,1120),'white');dr=ImageDraw.Draw(out)
    for k,(label,pos,up) in enumerate(views):
        im=render([(C[n],green,None)],f'qa_{n}_{label}.png',pos,(cx,cyy,cz),max(bb.xlen*.34,14),size=(900,500),up=up);out.paste(im,(900*(k%2),560*(k//2)+50));dr.text((30+900*(k%2),10+560*(k//2)),label,font=font(30),fill='#243e4b')
    out.save(O/'preview'/f'qa_{n}_four_views.png')
print('Actual CAD views and anchor diagram rendered.',flush=True)
