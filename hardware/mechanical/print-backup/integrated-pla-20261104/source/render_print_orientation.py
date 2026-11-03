from pathlib import Path
import trimesh,vtk
import zipfile,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parents[1];R=O.parent.parents[2];W=R.parent/'.p2s-integrated-pla-20261104'
def actor(m,color):
 pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
 for v in m.vertices:pts.InsertNextPoint(*v)
 for f in m.faces:
  t=vtk.vtkTriangle()
  for i,k in enumerate(f):t.GetPointIds().SetId(i,int(k))
  cells.InsertNextCell(t)
 data=vtk.vtkPolyData();data.SetPoints(pts);data.SetPolys(cells)
 norm=vtk.vtkPolyDataNormals();norm.SetInputData(data);norm.SetFeatureAngle(35)
 mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(norm.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(*color);return a
for name,label in [('LOWER_H41_B1','底板竖立　盘内旋转45°'),('UPPER_INTEGRATED','上平台与筒壁整体倾斜')]:
 with zipfile.ZipFile(W/name/'geometry.3mf') as z:root=ET.fromstring(z.read('3D/3dmodel.model'))
 vertices=[[float(v.attrib[k]) for k in ('x','y','z')] for v in root.findall('.//{*}vertex')]
 faces=[[int(v.attrib[k]) for k in ('v1','v2','v3')] for v in root.findall('.//{*}triangle')]
 assert len(root.findall('.//{*}object'))==1 and not any(v.get('transform') for v in root.findall('.//{*}item'))
 m=trimesh.Trimesh(vertices=vertices,faces=faces,process=False);bed=trimesh.creation.box([256,256,1]);bed.apply_translation([128,128,-.5])
 r=vtk.vtkRenderer();r.SetBackground(1,1,1);r.AddActor(actor(m,(.4,.62,.7)));r.AddActor(actor(bed,(.87,.88,.89)))
 cam=r.GetActiveCamera();cam.SetPosition(460,-430,360);cam.SetFocalPoint(128,128,110);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(235)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1200,1000);win.AddRenderer(r);win.Render()
 f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();wr=vtk.vtkPNGWriter();path=O/'preview'/f'{name}_print_orientation.png';wr.SetFileName(str(path));wr.SetInputConnection(f.GetOutputPort());wr.Write();win.Finalize()
 im=Image.open(path).convert('RGB');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27)
 d.text((36,20),label+'　256×256 mm打印盘',font=font,fill='#243f49')
 d.text((36,950),'此图仅显示模型摆放，树形支撑以3MF实际切片为准；比例100%。',font=font,fill='#444444');im.save(path)
print('print orientation images saved')
