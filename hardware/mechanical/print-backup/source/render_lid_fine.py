"""Old-seat repair previews and actual all-layer path checks; no physical fit claim."""
from pathlib import Path
import json,math,re,zipfile
import cadquery as cq
import vtk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image,ImageDraw,ImageFont
B=Path(__file__).resolve().parents[1];R=B.parents[2];BASE=B/'wall-panels-20261102';O=B/'lid-fine-20261103';W=R.parent/'.p2s-lid-fine-20261103'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def actor(s,col,alpha=1):
    vs,fs=s.tessellate(.03);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vs:pts.InsertNextPoint(v.x,v.y,v.z)
    for f in fs:
        t=vtk.vtkTriangle()
        for i,j in enumerate(f):t.GetPointIds().SetId(i,j)
        cells.InsertNextCell(t)
    p=vtk.vtkPolyData();p.SetPoints(pts);p.SetPolys(cells);norm=vtk.vtkPolyDataNormals();norm.SetInputData(p);norm.SetFeatureAngle(30);norm.Update();mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(norm.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(*col);a.GetProperty().SetOpacity(alpha);a.GetProperty().SetAmbient(.2);return a
blue=(.38,.66,.76);gold=(.91,.65,.28);green=(.27,.55,.42);gray=(.48,.52,.55)
def render(items,name,pos,focal,scale,up=(0,1,0)):
    r=vtk.vtkRenderer();r.SetBackground(1,1,1)
    for s,col,alpha in items:r.AddActor(actor(s,col,alpha))
    c=r.GetActiveCamera();c.SetPosition(*pos);c.SetFocalPoint(*focal);c.SetViewUp(*up);c.ParallelProjectionOn();c.SetParallelScale(scale)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(900,650);win.AddRenderer(r);win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();w=vtk.vtkPNGWriter();w.SetInputConnection(f.GetOutputPort());w.SetFileName(str(O/'preview'/name));w.Write();win.Finalize();return Image.open(O/'preview'/name).convert('RGB')

parts={n:cq.importers.importStep(str(O/'step'/f'{n}_ASSEMBLY.step')).val() for n in ['L01_LIGHT_LID','L02_HINGE_SHOE','L03_LINK_ARM','L04_SWITCH_FOOT','L05_SWITCH_TONGUE']}
mov=list(parts.values())+[parts['L02_HINGE_SHOE'].translate((0,64,0))]
wm={'W01_FRONT':[[0,0,1,207],[1,0,0,23],[0,1,0,5],[0,0,0,1]],'W02_REAR':[[0,0,-1,53],[-1,0,0,167],[0,1,0,5],[0,0,0,1]],'W03_LEFT':[[1,0,0,50],[0,0,-1,23],[0,1,0,5],[0,0,0,1]],'W04_RIGHT':[[-1,0,0,210],[0,0,1,167],[0,1,0,5],[0,0,0,1]]}
walls=[cq.importers.importStep(str(BASE/'step'/f'{n}.step')).val().transformGeometry(cq.Matrix(m)) for n,m in wm.items()]
def page(name,title,a,b,notes):
 im=Image.new('RGB',(1800,1070),'white');dr=ImageDraw.Draw(im);dr.text((35,20),title,font=font(42),fill='#203c49');im.paste(a,(0,100));im.paste(b,(900,100))
 for i,t in enumerate(notes):dr.text((35,780+i*62),t,font=font(32),fill='#203c49')
 im.save(O/'preview'/name)
a=render([(s,blue,1) for s in walls]+[(s,gold,1) for s in mov],'closed.png',(450,430,390),(130,95,115),150,(0,0,1))
b=render([(s,blue,1) for s in walls]+[(s.rotate((46.5,0,185),(46.5,1,185),-70),gold,1) for s in mov],'open.png',(450,430,390),(120,95,175),190,(0,0,1))
page('01_lid_closed_open.png','轻量桶盖与附件   闭合 / 打开70°',a,b,['橙色为随盖运动的打印件；蓝色为已打印筒壁。','含两只合页连接座、连杆臂、可调开关触片和手动提盖边。','盖板约21.7g，全部移动打印件约26.3g；还需计入金属件及连杆。','合页轴偏移采用名义包络，先打印小样试装；尚未完成实物验收。'])
a=render([(parts['L01_LIGHT_LID'],gold,1)],'underside.png',(380,380,-150),(130,95,185),100,(0,1,0))
small=[]
for i,n in enumerate(['L02_HINGE_SHOE','L03_LINK_ARM','L04_SWITCH_FOOT','L05_SWITCH_TONGUE']):
 s=cq.importers.importStep(str(O/'step'/f'{n}_PRINT.step')).val();small.append((s.translate(((i%2)*45,(i//2)*40,0)),gold,1))
b=render(small,'accessories.png',(120,-90,140),(35,28,5),46,(0,0,1))
page('02_lid_parts.png','盖板底面加强筋与随盖附件',a,b,['左：封闭面厚0.56mm，底面加筋；缓冲接触区留平面。','右：合页连接座×2、连杆臂×1、开关支脚×1、触片×1。','原金属合页、SG90舵盘、M2双球头连杆和两处EVA缓冲垫继续用。','超声波、LED及开关本体留在固定支架上；触片不承担闭盖重量。'])
