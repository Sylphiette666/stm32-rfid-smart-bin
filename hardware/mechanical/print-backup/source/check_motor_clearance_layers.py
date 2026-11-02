"""Render the checked packed geometry and the actual slicer's first layer."""
from pathlib import Path
import json,re,zipfile,math,argparse
import numpy as np
import trimesh
import vtk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]/'motor-adapter-clearance-20261102'
# Work directory is outside the repository and holds slicer intermediate code.
WORK=Path(__file__).resolve().parents[5]/'.p2s-motor-clearance-20261102'
parser=argparse.ArgumentParser()
parser.add_argument('--work',type=Path,default=WORK)
parser.add_argument('--output',type=Path,default=ROOT)
parser.add_argument('--objects',type=int,default=2)
parser.add_argument('--report',default='first_layers.json')
args=parser.parse_args();WORK=args.work;ROOT=args.output
packing={'plates':[{'plate':1,'objects':args.objects}]}
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
plt.rcParams['font.family']='Microsoft YaHei'
plt.rcParams['axes.unicode_minus']=False

def actor(mesh,color):
    points=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in mesh.vertices:points.InsertNextPoint(*v)
    for f in mesh.faces:
        t=vtk.vtkTriangle()
        for i,n in enumerate(f):t.GetPointIds().SetId(i,int(n))
        cells.InsertNextCell(t)
    p=vtk.vtkPolyData();p.SetPoints(points);p.SetPolys(cells)
    m=vtk.vtkPolyDataMapper();m.SetInputData(p);a=vtk.vtkActor();a.SetMapper(m)
    a.GetProperty().SetColor(*to_rgb(color));a.GetProperty().SetAmbient(.3)
    return a

reports={}
for plate in [1]:
    folder=WORK
    with zipfile.ZipFile(folder/'sliced.3mf') as z:
        files=[n for n in z.namelist() if n.endswith('.gcode')]
        assert len(files)==1
        code=z.read(files[0]).decode('utf-8',errors='replace')
    layer=-1;feature='';x=y=0;segments=[];brims=[];relative=True;e_position=0;objects=set()
    for line in code.splitlines():
        if line.startswith('; CHANGE_LAYER'):
            layer+=1
            if layer>0:break
        if layer==0 and line.startswith('; OBJECT_ID:'):objects.add(line.strip())
        if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
        command=line.split(';',1)[0].strip()
        if command=='M83':relative=True
        if command=='M82':relative=False
        if command.startswith('G92 E'):e_position=float(command[5:])
        if not re.match(r'^G[123] ',command):continue
        fields={k:float(v) for k,v in re.findall(r'([XYEFIJR])(-?\d*\.?\d+)',command)}
        nx=fields.get('X',x);ny=fields.get('Y',y)
        extrusion=fields.get('E',0) if relative else fields.get('E',e_position)-e_position
        if 'E' in fields:e_position=e_position+fields['E'] if relative else fields['E']
        if layer==0 and extrusion>0 and ('X'in fields or 'Y'in fields) and feature!='Custom':
            path=[(x,y),(nx,ny)]
            if command.startswith(('G2 ','G3 ')):
                assert 'R' not in fields,'Radius-mode arc needs explicit handling'
                cx=x+fields.get('I',0);cy=y+fields.get('J',0)
                radius=math.hypot(x-cx,y-cy)
                start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx)
                sweep=(end-start)%(2*math.pi)
                if command.startswith('G2 '):sweep-=2*math.pi
                elif abs(sweep)<1e-9:sweep=2*math.pi
                steps=max(8,math.ceil(abs(sweep)*radius/.05))
                path=[(cx+radius*math.cos(start+sweep*i/steps),cy+radius*math.sin(start+sweep*i/steps)) for i in range(steps+1)]
                path[0]=(x,y);path[-1]=(nx,ny)
            (brims if feature=='Brim' else segments).extend(zip(path,path[1:]))
        x,y=nx,ny
    points=np.array(segments).reshape((-1,2));assert len(points)>100
    assert np.all(points>=-1e-4) and np.all(points<=256.001),points
    expected=next(p['objects'] for p in packing['plates'] if p['plate']==plate)
    assert len(objects)==expected,(plate,'missing first-layer objects',len(objects),expected)
    if brims:
        brim_points=np.array(brims).reshape((-1,2))
        assert np.all(brim_points>=-1e-4) and np.all(brim_points<=256.001)
    fig,ax=plt.subplots(figsize=(9,9.4))
    ax.add_collection(LineCollection(brims,colors='#a8c2cc',linewidths=.55))
    ax.add_collection(LineCollection(segments,colors='#225d7d',linewidths=.6))
    ax.set(xlim=(0,256),ylim=(0,256),xlabel='X / mm',ylabel='Y / mm');ax.set_aspect('equal');ax.grid(alpha=.16)
    ax.set_title(f'电机转接座 {args.objects} 件 · 实际切片首层路径',fontsize=15,pad=15)
    fig.text(.12,.02,'避让试装版：平放贴床，无防翘边；圆弧按0.05mm弧长采样。',fontsize=10)
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(WORK/f'printer_{plate+1:02d}_first_layer.png',dpi=160);plt.close(fig)
    reports[str(plate)]={'first_layer_segment_count':len(segments),
        'first_layer_model_bounds':np.array([points.min(axis=0),points.max(axis=0)]).tolist(),
        'objects_with_first_layer_id':len(objects),'all_model_extrusions_within_bed':True,
        'G39_absent':not bool(re.search(r'^\s*G39(?:\s|;|$)',code,re.M))}
(ROOT/'checks'/args.report).write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(reports,ensure_ascii=False))
