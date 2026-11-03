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
B=Path(__file__).resolve().parents[1];R=B.parents[2];BASE=B/'wall-panels-20261102';O=B/'sensor-retainers-fix-20261103';W=R.parent/'.p2s-sensor-retainers-fix-20261103'
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
old={n:cq.importers.importStep(str(BASE/'step'/f'{n}.step')).val() for n in ['LIGHT_CRADLE','BEAM_SEAT']};bar=cq.importers.importStep(str(O/'step/LIGHT_BAR_V2_ASSEMBLY.step')).val();cup=cq.importers.importStep(str(O/'step/BEAM_CUP_V2_ASSEMBLY.step')).val()
lo=bar.translate((-3,.7,7.3));hi=bar.rotate((25,2.8,0),(25,2.8,1),180).translate((-3,23.7,7.3));pcb=cq.Workplane('XY').box(28,20,2,centered=False).translate((8,5,5)).val()
sensor=cq.Workplane('XY').box(10,20,9,centered=False).translate((10,3.7,3.3)).val()
def sheet(name,title,left,right,labels,notes):
    im=Image.new('RGB',(1800,1090),'white');dr=ImageDraw.Draw(im);dr.text((40,18),title,font=font(43),fill='#203c49');dr.text((40,87),labels[0],font=font(29),fill='#203c49');dr.text((940,87),labels[1],font=font(29),fill='#203c49');im.paste(left,(0,140));im.paste(right,(900,140))
    for i,t in enumerate(notes):dr.text((40,810+52*i),t,font=font(29),fill='#203c49')
    im.save(O/'preview'/name)
a=render([(old['LIGHT_CRADLE'],blue,1),(lo,gold,1),(hi,gold,1),(pcb,green,1)],'raw_light_assembly.png',(75,-30,105),(22,15,6),25)
b=render([(bar,gold,1)],'raw_light_underside.png',(75,35,-60),(25,2.8,1.5),22)
sheet('01_light_old_seat_fix.png','图一修复  旧光敏底座配两根可调压条',a,b,['蓝色旧底座保留，橙色两条更换','新压条底面：内侧有0.3mm接触台阶'],[
 '旧底座数字模型左右孔距36mm；新条长50mm，孔改为10×3.4mm横向槽。',
 '两根都是同一款L压条；上条在平面内转180°，接触台阶均朝PCB边缘。',
 '名义可调孔距29.4～42.6mm，实际还需避让垫片及元件；绿色仅为PCB尺寸示意。',
 '仅换压条，保留旧底座及筒壁；不要把另一款47mm红外PCB压条混入本位置。'])
a=render([(old['BEAM_SEAT'],blue,1),(cup,gold,1),(sensor,gray,.75)],'raw_beam_assembly.png',(65,-40,95),(15,13,7),21)
b=render([(cup,gold,1)],'raw_beam_cup.png',(65,-50,95),(15,6,8),18)
sheet('02_beam_lower_support_fix.png','图二修复  旧对射夹座配带下托的压盖',a,b,['旧夹座保留，外壳在新压盖后方','独立压盖：两侧下托，中间开放线槽'],[
 '仍用旧夹座两个孔，中心距22mm；新下托顶面位于旧座局部Y＝3.7mm。',
 '两只托肩托住10×20×9mm名义外壳的底边，不依赖前压条的摩擦防止下滑。',
 '中间8mm线槽向前和下方开放；先把线放进槽，再装压盖，不夹线。',
 '光学窗口保持；灰色只是外形包络示意。先轻拧试装，再做对射遮挡测试。'])
# Four views of the two actual replacement shapes.
for n,s in [('LIGHT_BAR_V2',bar),('BEAM_CUP_V2',cup)]:
    bb=s.BoundingBox();ctr=((bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,(bb.zmin+bb.zmax)/2);x,y,z=ctr;scale=max(bb.xlen*.48,12);im=Image.new('RGB',(1800,1420),'white');dr=ImageDraw.Draw(im)
    for i,(label,pos,up) in enumerate([('ISO',(x+70,y-70,z+90),(0,1,0)),('TOP',(x,y,z+100),(0,1,0)),('FRONT',(x,y-100,z),(0,0,1)),('RIGHT',(x+100,y,z),(0,0,1))]):
        pic=render([(s,gold,1)],f'qa_{n}_{label}.png',pos,ctr,scale,up);im.paste(pic,(900*(i%2),710*(i//2)+45));dr.text((25+900*(i%2),8+710*(i//2)),label,font=font(29),fill='#203c49')
    im.save(O/'preview'/f'qa_{n}_four_views.png')
with zipfile.ZipFile(W/'sliced.3mf') as z:code=z.read(next(n for n in z.namelist() if n.endswith('.gcode'))).decode('utf-8',errors='replace')
layer=-1;x=y=0;relative=True;ep=0;feature='';first=[];objs=set();count=support=0;mins=[1e9,1e9];maxs=[-1e9,-1e9]
for line in code.splitlines():
    if line.startswith('; CHANGE_LAYER'):layer+=1
    if line.startswith('; FEATURE:'):feature=line.split(':',1)[1].strip()
    if layer==0 and line.startswith('; OBJECT_ID:'):objs.add(line.strip())
    cmd=line.split(';')[0].strip()
    if cmd=='M83':relative=True
    if cmd=='M82':relative=False
    if cmd.startswith('G92 E'):ep=float(cmd[5:])
    if not re.match(r'^G[123] ',cmd):continue
    f={k:float(v) for k,v in re.findall(r'([XYEIJR])(-?\d*\.?\d+)',cmd)};nx=f.get('X',x);ny=f.get('Y',y);ex=f.get('E',0) if relative else f.get('E',ep)-ep
    if 'E' in f:ep=ep+f['E'] if relative else f['E']
    if ex>0 and ('X' in f or 'Y' in f) and feature!='Custom' and layer>=0:
        path=[(x,y),(nx,ny)];extrema=path
        if cmd.startswith(('G2 ','G3 ')):
            assert 'R' not in f;cx=x+f.get('I',0);cy=y+f.get('J',0);rad=math.hypot(x-cx,y-cy);start=math.atan2(y-cy,x-cx);end=math.atan2(ny-cy,nx-cx);sweep=(end-start)%(2*math.pi)
            if cmd.startswith('G2 '):sweep-=2*math.pi
            elif abs(sweep)<1e-9:sweep=2*math.pi
            extrema=path+[(cx+rad*math.cos(a),cy+rad*math.sin(a)) for a in [q*math.pi/2 for q in range(4)] if ((a-start)%(2*math.pi)<=sweep+1e-8 if sweep>0 else (start-a)%(2*math.pi)<=-sweep+1e-8)]
            if layer==0:
                steps=max(3,math.ceil(abs(sweep)*rad/.1));path=[(cx+rad*math.cos(start+sweep*i/steps),cy+rad*math.sin(start+sweep*i/steps)) for i in range(steps+1)];path[0]=(x,y);path[-1]=(nx,ny)
        assert all(min(p)>=-.001 and max(p)<=256.001 for p in extrema)
        for p in extrema:
            for i in range(2):mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
        count+=1
        if 'Support' in feature:support+=1
        if layer==0:first.extend(zip(path,path[1:]))
    x,y=nx,ny
assert len(objs)==4 and support==0 and not re.search(r'^\s*G39(?:\s|;|$)',code,re.M)
plt.rcParams['font.family']='Microsoft YaHei';fig,ax=plt.subplots(figsize=(11,6));ax.add_collection(LineCollection(first,colors='#235d7b',linewidths=.55));ax.set(xlim=(15,210),ylim=(20,85));ax.set_aspect('equal');ax.set_title('两根L压条＋两个IR下托压盖  实际切片首层');ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');fig.tight_layout();fig.savefig(O/'preview/03_actual_first_layer.png',dpi=170);plt.close(fig)
report={'status':'PASS_ALL_LAYER_PATHS','first_layer_objects':len(objs),'layers':layer+1,'extrusions_checked':count,'bounds':[mins,maxs],'support_moves':support,'all_paths_in_bed':True,'G39_absent':True,'physical_trial_fit':False};(O/'checks/path_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report),flush=True)
