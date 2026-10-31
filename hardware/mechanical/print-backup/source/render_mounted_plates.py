"""Render the checked packed geometry and the actual slicer's first layer."""
from pathlib import Path
import json,re,zipfile
import numpy as np
import trimesh
import vtk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]/'mounted-20261031'
# Work directory is outside the repository and holds slicer intermediate code.
WORK=Path(__file__).resolve().parents[5]/'.p2s-mounted-20261031/slicing'
packing=json.loads((ROOT/'checks/packing.json').read_text(encoding='utf-8'))
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

for plate in [1,2]:
    renderer=vtk.vtkRenderer();renderer.SetBackground(.96,.98,.99)
    bed=trimesh.creation.box(extents=[256,256,1]);bed.apply_translation([128,128,-.5])
    renderer.AddActor(actor(bed,'#d9e1e4'))
    for file in sorted((ROOT/'geometry').glob(f'*_bed{plate}.stl')):
        mesh=trimesh.load_mesh(file)
        color='#a2afb9'
        if 'P01_' in file.name:color='#4e85a6'
        elif 'P02_' in file.name:color='#4c9b98'
        elif 'P03_' in file.name:color='#c48c58'
        elif 'P04_' in file.name:color='#9882b2'
        elif '_lid_' in file.name:color='#e2a04d'
        elif '_keeper_' in file.name:color='#347db6'
        elif '_detent_' in file.name:color='#65a087'
        renderer.AddActor(actor(mesh,color))
    camera=renderer.GetActiveCamera()
    camera.SetPosition(480,-380,350 if plate==1 else 460)
    camera.SetFocalPoint(128,128,82 if plate==1 else 5)
    camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();camera.SetParallelScale(188)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1)
    window.SetSize(1400,1000);window.AddRenderer(renderer);window.SetMultiSamples(8);window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.Update()
    file=ROOT/'preview'/('05_plate1.png' if plate==1 else '06_plate2.png')
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(file));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()
    im=Image.open(file).convert('RGB');canvas=Image.new('RGB',(1400,1110),'white');canvas.paste(im,(0,110));d=ImageDraw.Draw(canvas)
    count=next(p['objects'] for p in packing['plates'] if p['plate']==plate)
    d.text((30,12),f'第{plate}盘 · {count}个独立物体 · 所有零件各自贴床',font=font,fill='#19384a')
    d.text((30,59),'保持工程方向与位置；逐层打印，禁止自动排盘。',font=small,fill='#475d69')
    canvas.save(file)

reports={}
for plate in [1,2]:
    folder=WORK/f'PLATE_{plate}_GEOMETRY'
    with zipfile.ZipFile(folder/'sliced.3mf') as z:
        files=[n for n in z.namelist() if n.endswith('.gcode')]
        assert len(files)==1
        code=z.read(files[0]).decode('utf-8',errors='replace')
    layer=-1;feature='';x=y=0;segments=[];brims=[];relative=True;e_position=0;objects=set()
    for line in code.splitlines():
        if line.startswith('; CHANGE_LAYER'):
            layer+=1
            if layer>0:break
        if layer==0 and 'start printing object' in line:objects.add(line.strip())
        if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
        command=line.split(';',1)[0].strip()
        if command=='M83':relative=True
        if command=='M82':relative=False
        if command.startswith('G92 E'):e_position=float(command[5:])
        if not re.match(r'^G[123] ',command):continue
        fields={k:float(v) for k,v in re.findall(r'([XYEF])(-?\d*\.?\d+)',command)}
        nx=fields.get('X',x);ny=fields.get('Y',y)
        extrusion=fields.get('E',0) if relative else fields.get('E',e_position)-e_position
        if 'E' in fields:e_position=e_position+fields['E'] if relative else fields['E']
        if layer==0 and extrusion>0 and ('X'in fields or 'Y'in fields) and feature!='Custom':
            (brims if feature=='Brim' else segments).append(((x,y),(nx,ny)))
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
    ax.set_title(f'第{plate}盘 · 实际切片首层路径（含防翘边）',fontsize=15,pad=15)
    fig.text(.12,.02,'每个小件直接贴床；镂空区套排的小件与外框之间留有拆边间隙。',fontsize=10)
    fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(ROOT/'preview'/('07_plate1_bed.png' if plate==1 else '08_plate2_bed.png'),dpi=160);plt.close(fig)
    reports[str(plate)]={'first_layer_segment_count':len(segments),
        'first_layer_model_bounds':np.array([points.min(axis=0),points.max(axis=0)]).tolist(),
        'objects_with_first_layer_comment':len(objects),'all_model_extrusions_within_bed':True,
        'G39_absent':not bool(re.search(r'^\s*G39(?:\s|;|$)',code,re.M))}
(ROOT/'checks/first_layers.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(reports,ensure_ascii=False))
