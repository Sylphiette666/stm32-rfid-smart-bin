"""Show sampled actual support toolpaths; do not invent support geometry."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,re
import vtk
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parents[1];R=O.parent.parents[2];W=R.parent/'.p2s-integrated-pla-fast-20261104'
selected=json.loads((O/'checks/selection.json').read_text())['variants']
for name in ['LOWER_H41_B1','UPPER_INTEGRATED']:
 work=W/selected[name]/name
 with zipfile.ZipFile(work/'geometry.3mf') as z:root=E.fromstring(z.read('3D/3dmodel.model'))
 pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
 for v in root.findall('.//{*}vertex'):pts.InsertNextPoint(*(float(v.attrib[k]) for k in ['x','y','z']))
 for f in root.findall('.//{*}triangle'):
  t=vtk.vtkTriangle()
  for i,k in enumerate(['v1','v2','v3']):t.GetPointIds().SetId(i,int(f.attrib[k]))
  cells.InsertNextCell(t)
 pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells);mp=vtk.vtkPolyDataMapper();mp.SetInputData(pd);a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(.25,.5,.62);a.GetProperty().SetOpacity(.2)
 sp=vtk.vtkPoints();sc=vtk.vtkCellArray();x=y=z=0;layer=-1;feature=''
 with (work/'plate_1.gcode').open(encoding='utf8') as stream:
  for line in stream:
   if line.startswith('; CHANGE_LAYER'):layer+=1
   if line.startswith('; FEATURE:'):feature=line.split(':',1)[1]
   if not line.startswith('G1 '):continue
   f={k:float(v) for k,v in re.findall(r'([XYZE])(-?\d*\.?\d+)',line)};nx=f.get('X',x);ny=f.get('Y',y);nz=f.get('Z',z)
   if layer>=0 and layer%3==0 and 'Support'in feature and f.get('E',0)>0 and ('X'in f or 'Y'in f):
    p=sp.InsertNextPoint(x,y,z);q=sp.InsertNextPoint(nx,ny,nz);sc.InsertNextCell(2);sc.InsertCellPoint(p);sc.InsertCellPoint(q)
   x,y,z=nx,ny,nz
 pd2=vtk.vtkPolyData();pd2.SetPoints(sp);pd2.SetLines(sc);mp2=vtk.vtkPolyDataMapper();mp2.SetInputData(pd2);b=vtk.vtkActor();b.SetMapper(mp2);b.GetProperty().SetColor(.7,.39,.11);b.GetProperty().SetLineWidth(1.2)
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1);ren.AddActor(a);ren.AddActor(b)
 cam=ren.GetActiveCamera();cam.SetPosition(460,-430,360);cam.SetFocalPoint(128,128,110);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(170)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1300,1200);win.AddRenderer(ren);win.Render()
 f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();wr=vtk.vtkPNGWriter();path=O/'preview'/f'{name}_supports.png';wr.SetFileName(str(path));wr.SetInputConnection(f.GetOutputPort());wr.Write();win.Finalize()
 im=Image.open(path).convert('RGB');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',29)
 label='下半主体' if name.startswith('LOWER') else '上半主体'
 d.text((35,20),label+'　实际树形支撑刀路',font=font,fill='#243f49')
 d.text((35,1140),'棕色：每3层抽取1层支撑路径；半透明蓝色：原尺寸模型。',font=font,fill='#444444');im.save(path)
 print(name,'support preview',sp.GetNumberOfPoints(),flush=True)
