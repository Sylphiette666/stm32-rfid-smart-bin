"""Actual-mesh previews and actual sliced-path checks, not simulated print success."""
from pathlib import Path
import json,math,re,zipfile
import numpy as np
import trimesh,vtk
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
O=Path(__file__).resolve().parents[1];B=O.parent;R=B.parents[2];BASE=B/'wall-panels-20261102';W=R.parent/'.p2s-integrated-pla-20261104'
import sys
d={'plates':{n:[n] for n in (sys.argv[1:] or ['LOWER_H41_B1','UPPER_INTEGRATED'])}}
font=lambda s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s)
def actor(mesh,col):
 p=vtk.vtkPoints();c=vtk.vtkCellArray()
 for v in mesh.vertices:p.InsertNextPoint(*v)
 for f in mesh.faces:
  t=vtk.vtkTriangle()
  for i,n in enumerate(f):t.GetPointIds().SetId(i,int(n))
  c.InsertNextCell(t)
 pd=vtk.vtkPolyData();pd.SetPoints(p);pd.SetPolys(c);mp=vtk.vtkPolyDataMapper();mp.SetInputData(pd);a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(*col);a.GetProperty().SetAmbient(.3);return a
def render(items,path,camera,target,size=(1400,1000)):
 r=vtk.vtkRenderer();r.SetBackground(1,1,1)
 for m,col in items:r.AddActor(actor(m,col))
 c=r.GetActiveCamera();c.SetPosition(*camera);c.SetFocalPoint(*target);c.SetViewUp(0,0,1);c.ParallelProjectionOn();r.ResetCamera()
 w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(*size);w.AddRenderer(r);w.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(w);f.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(path));wr.SetInputConnection(f.GetOutputPort());wr.Write();w.Finalize()
def mesh(name):return trimesh.load_mesh(BASE/'parts'/f'{name}.stl')
def placed(name,rows):
 m=mesh(name);mat=np.eye(4);mat[:3]=rows;m.apply_transform(mat);return m
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
checks={}
def gcode_lines(path):
 with zipfile.ZipFile(path) as z:
  with z.open(next(n for n in z.namelist() if n.endswith('.gcode'))) as stream:
   for line in stream:yield line.decode('utf-8',errors='replace').rstrip('\r\n')
for pid,items in d['plates'].items():
 g39=False
 layer=-1;x=y=0;relative=True;ep=0;feature='';segs=[];support=[];objs=set();support_total=0;zheights=[]
 for line in gcode_lines(W/pid/'sliced.3mf'):
  if re.match(r'^\s*G39(?:\s|;|$)',line):g39=True
  if line.startswith('; CHANGE_LAYER'):layer+=1
  if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
  if line.startswith('; Z_HEIGHT:'):zheights.append(float(line.split(':')[1]))
  if layer==0 and line.startswith('; OBJECT_ID:'):objs.add(line.strip())
  cmd=line.split(';')[0].strip()
  if cmd=='M83':relative=True
  if cmd=='M82':relative=False
  if cmd.startswith('G92 E'):ep=float(cmd[5:])
  if not re.match(r'^G[123] ',cmd):continue
  f={k:float(v) for k,v in re.findall(r'([XYEIJR])(-?\d*\.?\d+)',cmd)};nx=f.get('X',x);ny=f.get('Y',y);ex=f.get('E',0) if relative else f.get('E',ep)-ep
  if 'E'in f:ep=ep+f['E'] if relative else f['E']
  if ex>0 and ('X'in f or 'Y'in f) and feature!='Custom' and layer>=0:
   path=[(x,y),(nx,ny)];extrema=path
   if cmd.startswith(('G2 ','G3 ')):
    assert 'R' not in f,'Unsupported radius arc'
    cx=x+f.get('I',0);cy=y+f.get('J',0);radius=math.hypot(x-cx,y-cy)
    start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx);sweep=(end-start)%(2*math.pi)
    if cmd.startswith('G2 '):sweep-=2*math.pi
    elif abs(sweep)<1e-9:sweep=2*math.pi
    angles=[q*math.pi/2 for q in range(4)]
    extrema=path+[(cx+radius*math.cos(a),cy+radius*math.sin(a)) for a in angles if ((a-start)%(2*math.pi) <= sweep+1e-8 if sweep>0 else (start-a)%(2*math.pi)<=-sweep+1e-8)]
    if layer==0:
     steps=max(8,math.ceil(abs(sweep)*radius/.05));path=[(cx+radius*math.cos(start+sweep*i/steps),cy+radius*math.sin(start+sweep*i/steps)) for i in range(steps+1)];path[0]=(x,y);path[-1]=(nx,ny)
   assert all(min(pt)>=-.001 and max(pt)<=256.001 for pt in extrema),(pid,layer,extrema)
   if 'Support'in feature:support_total+=1
   if layer==0:(support if 'Support'in feature else segs).extend(zip(path,path[1:]))
  x,y=nx,ny
 assert len(objs)==len(items),(pid,len(objs),len(items))
 fig,ax=plt.subplots(figsize=(8,8));ax.add_collection(LineCollection(segs,colors='#235d7b',linewidths=.55));ax.add_collection(LineCollection(support,colors='#bc7a24',linewidths=.7));ax.set(xlim=(0,256),ylim=(0,256));ax.set_aspect('equal');ax.set_title(f'第{pid}盘实际首层 蓝色模型及裙边 棕色支撑');fig.savefig(O/'preview'/f'first_layer_{pid}.png',dpi=140);plt.close(fig)
 assert zheights and max(zheights)<=256.001,(pid,'height',max(zheights))
 checks[pid]={'objects_on_first_layer':len(objs),'expected_objects':len(items),'all_extrusions_in_bed':True,'maximum_print_z_mm':max(zheights),'layer_count':len(zheights),'support_extrusion_moves':support_total,'G39_absent':not g39}
 print(pid,'path check passed',flush=True)
(O/'checks/path_review.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks))
