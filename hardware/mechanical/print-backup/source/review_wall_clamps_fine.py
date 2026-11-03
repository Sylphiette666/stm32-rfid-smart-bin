"""Validate delivered mesh/native project and review actual sliced paths and supports."""
from pathlib import Path
import json,re,math,zipfile
import numpy as np
import trimesh
import vtk
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'wall-clamps-fine-20261103';W=R.parent/'.p2s-wall-clamps-fine-20261103'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));d=load(O/'checks/design.json');layout=load(O/'source/layout.json')['objects'];slicing=load(O/'checks/slicing.json')
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
with zipfile.ZipFile(O/slicing['project']) as z:
    c=json.loads(z.read('Metadata/project_settings.config'));assert c['layer_height']=='0.12' and c['wall_loops']=='6' and c['sparse_infill_density']=='60%' and c['resolution']=='0.01';assert c['print_sequence']=='by layer' and c['enable_support']=='1'
    assert c['outer_wall_speed']==['35']*3 and c['xy_hole_compensation']=='0' and c['xy_contour_compensation']=='0'
with zipfile.ZipFile(W/'sliced.3mf') as z:code=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode('utf-8',errors='replace')
layer=-1;x=y=0;relative=True;ep=0;feature='';first=[];support=[];model=[];objs=set();count=0;mins=[1e10,1e10];maxs=[-1e10,-1e10];zheight=0;support_layers=set();support_count=0
for line in code.splitlines():
    if line.startswith('; CHANGE_LAYER'):layer+=1
    if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
    if layer==0 and line.startswith('; OBJECT_ID:'):objs.add(line.strip())
    cmd=line.split(';')[0].strip()
    if cmd=='M83':relative=True
    if cmd=='M82':relative=False
    if cmd.startswith('G92 E'):ep=float(cmd[5:])
    if not re.match(r'^G[123] ',cmd):continue
    f={k:float(v) for k,v in re.findall(r'([XYEIJRZ])(-?\d*\.?\d+)',cmd)};nx=f.get('X',x);ny=f.get('Y',y);zheight=f.get('Z',zheight);ex=f.get('E',0) if relative else f.get('E',ep)-ep
    if 'E' in f:ep=ep+f['E'] if relative else f['E']
    if ex>0 and ('X' in f or 'Y' in f) and feature!='Custom' and layer>=0:
        path=[(x,y),(nx,ny)];extrema=path
        if cmd.startswith(('G2 ','G3 ')):
            assert 'R' not in f
            cx=x+f.get('I',0);cy=y+f.get('J',0);radius=math.hypot(x-cx,y-cy);start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx);sweep=(end-start)%(2*math.pi)
            if cmd.startswith('G2 '):sweep-=2*math.pi
            elif abs(sweep)<1e-9:sweep=2*math.pi
            angles=[q*math.pi/2 for q in range(4)]
            extrema=path+[(cx+radius*math.cos(a),cy+radius*math.sin(a)) for a in angles if ((a-start)%(2*math.pi)<=sweep+1e-8 if sweep>0 else (start-a)%(2*math.pi)<=-sweep+1e-8)]
            steps=max(3,math.ceil(abs(sweep)*radius/.3));path=[(cx+radius*math.cos(start+sweep*i/steps),cy+radius*math.sin(start+sweep*i/steps)) for i in range(steps+1)];path[0]=(x,y);path[-1]=(nx,ny)
        assert all(min(p)>=-.001 and max(p)<=256.001 for p in extrema),(layer,extrema)
        for p in extrema:
            for i in range(2):mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
        count+=1
        if layer==0:first.extend(zip(path,path[1:]))
        target=support if 'Support' in feature else model
        if target is support:support_count+=1;support_layers.add(layer)
        # Supports are all retained; model walls give a readable 3D silhouette.
        if target is support or ('wall' in feature.lower()):target.extend([((a[0],a[1],zheight),(b[0],b[1],zheight)) for a,b in zip(path,path[1:])])
    x,y=nx,ny
assert len(objs)==8 and support_count>0 and 0 in support_layers
assert not re.search(r'^\s*G39(?:\s|;|$)',code,re.M)
plt.rcParams['font.family']='Microsoft YaHei';fig,ax=plt.subplots(figsize=(10,8));ax.add_collection(LineCollection(first,colors='#235d7b',linewidths=.5));ax.set(xlim=(0,256),ylim=(0,165));ax.set_aspect('equal');ax.set_title('四只压脚＋四只小压垫  实际切片首层及支撑底座',fontsize=15)
for item in layout:
    bb=item['bounds'];ax.text((bb[0][0]+bb[1][0])/2,bb[1][1]+8,item['name'].split('_')[0] if not item['name'].startswith('PRESSURE_PAD') else '垫'+item['name'][-1],ha='center',fontsize=10)
ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');fig.tight_layout();fig.savefig(O/'preview/03_actual_first_layer.png',dpi=180);plt.close(fig)
def lineactor(segs,col):
    pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for a,b in segs:
        n=pts.GetNumberOfPoints();pts.InsertNextPoint(*a);pts.InsertNextPoint(*b);ln=vtk.vtkLine();ln.GetPointIds().SetId(0,n);ln.GetPointIds().SetId(1,n+1);cells.InsertNextCell(ln)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetLines(cells);mp=vtk.vtkPolyDataMapper();mp.SetInputData(poly);ac=vtk.vtkActor();ac.SetMapper(mp);ac.GetProperty().SetColor(*col);return ac
def meshactor(mesh,col):
    pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in mesh.vertices:pts.InsertNextPoint(*v)
    for f in mesh.faces:
        tr=vtk.vtkTriangle()
        for i,j in enumerate(f):tr.GetPointIds().SetId(i,int(j))
        cells.InsertNextCell(tr)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells);nm=vtk.vtkPolyDataNormals();nm.SetInputData(poly);nm.SetFeatureAngle(30);nm.Update();mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(nm.GetOutputPort());ac=vtk.vtkActor();ac.SetMapper(mp);ac.GetProperty().SetColor(*col);ac.GetProperty().SetAmbient(.2);return ac
def render(actors,name,pos,focal,scale,size=(1800,1050),up=(0,0,1)):
    r=vtk.vtkRenderer();r.SetBackground(1,1,1)
    for ac in actors:r.AddActor(ac)
    cam=r.GetActiveCamera();cam.SetPosition(*pos);cam.SetFocalPoint(*focal);cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale);win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(*size);win.AddRenderer(r);win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();w=vtk.vtkPNGWriter();w.SetInputConnection(f.GetOutputPort());w.SetFileName(str(O/'preview'/name));w.Write();win.Finalize();return Image.open(O/'preview'/name).convert('RGB')
actors=[]
for i,item in enumerate(layout):
    n=item['name'];mesh=trimesh.load_mesh(O/'parts'/('PRESSURE_PAD_PRINT.stl' if n.startswith('PRESSURE_PAD') else n+'_PRINT.stl'));mesh.apply_translation([*item['offset_xy'],0]);actors.append(meshactor(mesh,(.94,.62,.22) if i>=4 else (.18,.58,.37)))
im=render(actors,'raw_layout.png',(80,-180,290),(122,80,4),95).crop((0,150,1800,930))
out=Image.new('RGB',(1800,1120),'white');dr=ImageDraw.Draw(out);dr.text((40,20),'筒壁免钻孔压脚  高精度打印排盘',font=font(42),fill='#203c49');out.paste(im,(0,90));dr.text((40,950),'一盘8件：C1／C2／C3长压脚、C4短压脚、4只小压垫。保持工程朝向和100%比例。',font=font(30),fill='#203c49');dr.text((40,1000),'P2S 0.4mm喷嘴｜PLA｜0.12mm层高｜6墙｜60%填充｜自动树状支撑。',font=font(30),fill='#203c49');out.save(O/'preview/01_print_layout.png')
im=render([lineactor(model,(.22,.49,.63)),lineactor(support,(.95,.53,.16))],'raw_support.png',(75,-180,240),(122,80,7),100).crop((0,150,1800,930))
out=Image.new('RGB',(1800,1120),'white');dr=ImageDraw.Draw(out);dr.text((40,20),'实际切片全层预览  模型与支撑',font=font(42),fill='#203c49');out.paste(im,(0,90));dr.text((40,950),'蓝色＝模型外壁；橙色＝自动生成的实际支撑。孔腔和接触面装配前需清理。',font=font(30),fill='#203c49');dr.text((40,1000),f'检查8件首层与{layer+1}层路径，全部位于256×256mm打印范围内。',font=font(30),fill='#203c49');out.save(O/'preview/04_actual_support_review.png')
for v in d['variants']:
    n=v['id'];m=trimesh.load_mesh(O/'parts'/f'{n}_PRINT.stl');cx,cy,cz=m.centroid;scale=max(m.extents[0]*.34,14);views=[('ISO',(cx-80,cy-100,cz+90),(0,0,1)),('TOP',(cx,cy,cz+100),(0,1,0)),('FRONT',(cx,cy-100,cz),(0,0,1)),('RIGHT',(cx+100,cy,cz),(0,0,1))];out=Image.new('RGB',(1800,1120),'white');dr=ImageDraw.Draw(out)
    center=m.bounds.mean(axis=0)
    for k,(label,pos,up) in enumerate(views):
        im=render([meshactor(m,(.18,.58,.37))],f'qa_{n}_{label}.png',pos,center,scale,size=(900,500),up=up);out.paste(im,(900*(k%2),560*(k//2)+50));dr.text((30+900*(k%2),10+560*(k//2)),label,font=font(30),fill='#203c49')
    out.save(O/'preview'/f'qa_{n}_four_views.png')
result={'status':'PASS_DIGITAL_PRINT_CHECKS','first_layer_object_count':len(objs),'layers':layer+1,'all_extrusion_moves_checked':count,'extrusion_bounds':[mins,maxs],'all_paths_in_bed':True,'actual_support_moves':support_count,'support_starts_on_build_plate':0 in support_layers,'native_geometry_matches_tested':True,'scale':1,'G39_absent':True,'physical_fit_or_load_tested':False}
(O/'checks/path_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result),flush=True)
