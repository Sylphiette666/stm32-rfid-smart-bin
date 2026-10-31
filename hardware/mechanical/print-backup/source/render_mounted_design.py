"""Render four measured-layout previews from the final mounted CAD.

Read-only with respect to CAD, design metadata, and Word.  Only the four named
PNG files are written. Green PCB/battery/speaker envelopes and standard hardware
are explanatory assembly geometry, not additional printable models.
"""
from pathlib import Path
import json,math,sys,time
import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont,ImageChops
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
from module_clamps_a import build_holder

ROOT=SOURCE.parent/'mounted-20261031'
PREVIEW=ROOT/'preview';PREVIEW.mkdir(exist_ok=True)
DESIGN=json.loads((ROOT/'source/design.json').read_text(encoding='utf-8'))
MODULES={m['id']:m for m in DESIGN['modules']}
COLOURS={'base':'#477e9f','body':'#aab4bc','lid':'#e9a64e',
         'keeper':'#367fba','detent':'#48a780','board':'#3e7c68',
         'metal':'#a6b4bc','battery':'#405b85','speaker':'#46525d'}
FONT='C:/Windows/Fonts/msyh.ttc'
MESH_CACHE={}

def font(size):return ImageFont.truetype(FONT,size)
def box(x,y,z,l,w,h):
    return cq.Workplane('XY').box(l,w,h,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h,direction=(0,0,1)):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*direction))
def rigid(shape,xy,rotation=0,z=5):
    return shape.rotate((0,0,0),(0,0,1),rotation).translate((xy[0],xy[1],z))
def load(name):
    path=ROOT/'step'/(name+'.step')
    for attempt in range(4):
        try:return cq.importers.importStep(str(path)).val()
        except Exception:
            if attempt==3:raise
            time.sleep(1)

def mesh(shape):
    key=id(shape)
    if key in MESH_CACHE:return MESH_CACHE[key][1]
    vertices,faces=shape.tessellate(.09,.08)
    points=vtk.vtkPoints();points.SetDataTypeToDouble()
    for vertex in vertices:points.InsertNextPoint(*vertex.toTuple())
    cells=vtk.vtkCellArray()
    for face in faces:
        tri=vtk.vtkTriangle()
        for i,n in enumerate(face):tri.GetPointIds().SetId(i,n)
        cells.InsertNextCell(tri)
    data=vtk.vtkPolyData();data.SetPoints(points);data.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(data)
    normals.SetFeatureAngle(45);normals.SplittingOn();normals.ConsistencyOn();normals.Update()
    data=vtk.vtkPolyData();data.ShallowCopy(normals.GetOutput())
    MESH_CACHE[key]=(shape,data)
    return data

def render(shapes,size,camera,focal,scale,up=(0,0,1),labels=None):
    renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1)
    import matplotlib.colors as mc
    keep=[]
    for record in shapes:
        shape,colour=record[:2];alpha=record[2] if len(record)>2 else 1
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(mesh(shape))
        actor=vtk.vtkActor();actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*mc.to_rgb(colour))
        actor.GetProperty().SetOpacity(alpha);actor.GetProperty().SetAmbient(.32)
        actor.GetProperty().SetDiffuse(.68);actor.GetProperty().SetSpecular(.12)
        actor.GetProperty().SetSpecularPower(25)
        renderer.AddActor(actor);keep.append(actor)
    cam=renderer.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*focal)
    cam.SetViewUp(*up);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1)
    window.SetSize(*size);window.SetMultiSamples(8);window.AddRenderer(renderer)
    window.Render()
    projected={}
    for key,point in (labels or {}).items():
        renderer.SetWorldPoint(*point,1);renderer.WorldToDisplay();x,y,z=renderer.GetDisplayPoint()
        projected[key]=(x,size[1]-y)
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff();capture.Update()
    array=vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
    im=Image.fromarray(np.flipud(array.reshape((size[1],size[0],3))).copy())
    window.Finalize()
    return im,projected

def text(draw,xy,value,size=40,fill='#18323f',anchor=None):
    draw.text(xy,value,font=font(size),fill=fill,anchor=anchor,
              stroke_width=2,stroke_fill='white')

def framed_image(im,title,subtitle=None,top=110,bottom=120):
    canvas=Image.new('RGB',(im.width,im.height+top+bottom),'white')
    canvas.paste(im,(0,top));draw=ImageDraw.Draw(canvas)
    text(draw,(55,25),title,46)
    if subtitle:text(draw,(55,im.height+top+28),subtitle,32,fill='#435866')
    return canvas

def crop_white(im,padding=65,width=2200):
    difference=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L')
    bounds=difference.point(lambda x:255 if x>12 else 0).getbbox()
    if bounds:
        x0,y0,x1,y1=bounds
        im=im.crop((max(0,x0-padding),max(0,y0-padding),
                    min(im.width,x1+padding),min(im.height,y1+padding)))
    return im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)

def assembly_scene():
    shapes=[(load('P01_MOUNTED_BASE'),COLOURS['base'])]
    centres={}
    for ident,m in MODULES.items():
        xy=m['layout_origin'];rot=m.get('rotation',0);l,w,t=m['board_size']
        if ident.startswith('M'):
            for role in ['body','lid','keeper','detent']:
                shapes.append((rigid(load(ident+'_'+role),xy,rot),COLOURS[role]))
            board=box(-l/2,-w/2,m['seat_height'],l,w,t)
            shapes.append((rigid(board,xy,rot),COLOURS['board']))
            centres[ident]=(*xy,5+m['seat_height']+t+.4)
        elif ident=='A1':
            shapes.append((box(xy[0]-l/2,xy[1]-w/2,5+m['seat_height'],l,w,t),COLOURS['board']))
            for h in m['mount_holes']:
                hx,hy=h['xy'];shapes.append((cyl(hx,hy,5,2.7,10),COLOURS['metal']))
            centres[ident]=(*xy,17)
        elif ident=='BUCK':
            shapes.append((rigid(load('P06_BUCK_cradle'),xy),COLOURS['body']))
            shapes.append((box(xy[0]-l/2,xy[1]-w/2,5+m['seat_height'],l,w,t),'#4677a0'))
            centres[ident]=(*xy,5+m['seat_height']+t+.4)
        elif ident=='SPK':
            shapes.append((rigid(load('P07_SPEAKER_cradle'),xy),COLOURS['body']))
            shapes.append((cyl(*xy,7,20,14),COLOURS['speaker']))
            centres[ident]=(*xy,21.4)
        elif ident=='BAT':
            # The finished CAD cradle is X-long, irrespective of an earlier
            # input-coordinate rotation convention in the metadata.
            shapes.append((rigid(load('P05_BATTERY_cradle'),xy),COLOURS['body']))
            for side in ['L','R']:
                for role in ['keeper','detent']:
                    shapes.append((rigid(load('BAT_'+side+'_'+role),xy),COLOURS[role]))
            shapes.append((box(xy[0]-38,xy[1]-20,9.4,76,40,20),COLOURS['battery']))
            centres[ident]=(*xy,29.8)
    return shapes,centres

def layout(shapes):
    im,_=render(shapes,(1680,1320),(140,110,650),(140,110,0),110,up=(0,1,0))
    plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
    fig=plt.figure(figsize=(14.6,10.8),dpi=180)
    grid=fig.add_gridspec(1,2,width_ratios=[3.5,1.55],wspace=.055)
    ax=fig.add_subplot(grid[0]);legend=fig.add_subplot(grid[1])
    ax.imshow(im,extent=[0,280,0,220],zorder=1)
    ax.set_xlim(-18,299);ax.set_ylim(-16,237);ax.set_aspect('equal')
    ax.set_xticks([0,50,100,150,200,250,280]);ax.set_yticks([0,50,100,150,200,220])
    ax.tick_params(labelsize=11);ax.grid(alpha=.17,zorder=3)
    ax.set_xlabel('X / mm   车尾 → 车头',fontsize=15,labelpad=10)
    ax.set_ylabel('底板局部 Y / mm',fontsize=14)
    for ident,m in MODULES.items():
        x,y=m['layout_origin'];c='white' if ident in {'SPK','BAT'} else '#17333d'
        ax.text(x,y,ident,ha='center',va='center',fontsize=14,fontweight='bold',color=c,zorder=5,
                path_effects=[pe.withStroke(linewidth=2.4,foreground='#22313b' if c=='white' else 'white')])
    def arrow(label,start,end,xytext,ha='center'):
        ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','lw':1.8,'color':'#1c516d'},zorder=6)
        ax.text(*xytext,label,ha=ha,va='center',fontsize=12,color='#184861',zorder=7,
                path_effects=[pe.withStroke(linewidth=3,foreground='white')])
    arrow('USB',(5,68),(-8,68),(-13,77))
    arrow('SWD',(58,68),(69,68),(65,62))
    arrow('TF卡',(12,113),(-7,113),(-13,121))
    arrow('天线',(25,184),(25,195),(22,204))
    arrow('端子接线区',(210,110),(240,110),(244,118))
    arrow('电池出线',(214,30),(238,30),(247,39))
    for x,y in [[30,25],[250,25],[30,195],[250,195]]:
        ax.plot(x,y,'o',ms=7,mfc='none',mec='#324650',mew=1.3,zorder=5)
    legend.axis('off')
    legend.text(0,1,'底板上的模块',fontsize=18,fontweight='bold',va='top',transform=legend.transAxes)
    labels=[
        ('M01','STM32核心板'),('M02','MCP23017'),('M03','FLASH存储'),
        ('M04','TB6612驱动'),('M05','3.3V稳压'),('M06','DFPlayer'),
        ('M07','HC-05蓝牙'),('M08','MPU6050'),('M09','蜂鸣器'),
        ('A1','100×100主PCB'),('BUCK','5V降压'),('SPK','小喇叭'),('BAT','2S串联电池')]
    for i,(ident,name) in enumerate(labels):
        y=.925-i*.058
        legend.text(0,y,ident,fontsize=15,fontweight='bold',va='top',transform=legend.transAxes,color='#245b79')
        legend.text(.24,y,name,fontsize=15,va='top',transform=legend.transAxes)
    legend.text(0,.125,'接口箭头已按安装旋转换算\nM08板上 X→、Y↑\n圆圈：四个原立柱孔',fontsize=13,linespacing=1.7,va='top',transform=legend.transAxes,color='#405662')
    fig.suptitle('底板模块布置  280×220 mm 一整片',fontsize=22,fontweight='bold',y=.975)
    fig.text(.06,.035,'实际CAD俯视图；电子板以尺寸包络示意。接口和排针最终按实物复核。',fontsize=13,color='#405662')
    fig.subplots_adjust(left=.06,right=.98,top=.92,bottom=.10)
    fig.savefig(PREVIEW/'01_layout.png',dpi=180,facecolor='white');plt.close(fig)

def overview(shapes,centres):
    im,points=render(shapes,(2200,1480),(455,-390,350),(140,110,10),166,labels=centres)
    d=ImageDraw.Draw(im)
    for ident,(x,y) in points.items():
        text(d,(x,y),ident,40,fill='white' if ident in {'BAT','SPK'} else '#17333d',anchor='mm')
    im=crop_white(im)
    out=framed_image(im,'整片底板与可拆模块夹具',
       '蓝灰：底板  灰：卡座  橙：压框  蓝：拨片  绿：定位簧片；绿色板体仅示尺寸。')
    d=ImageDraw.Draw(out)
    text(d,(55,out.height-38),'现成五金为装配示意；此图不是打印摆放，不代表已实物试装。',30,fill='#435866')
    out.save(PREVIEW/'02_base_3d.png')

def clamp_demo():
    m=MODULES['M01'];l,w,t=m['board_size'];meta=m['mechanism']
    specimen=dict(id='M01',l=l,w=w,seat_height=m['seat_height'],component_height=9,
                  headers_face='back',header_protrusion=9,interfaces=m['interfaces'])
    constructed=build_holder(specimen)
    closed={r:load('M01_'+r) for r in ['body','lid','keeper','detent']}
    for r,s in closed.items():
        assert abs(s.Volume()-constructed[r].Volume())<.02,(r,'STEP differs from current mechanism constructor')
    hinge=meta['hinge_axis']['point'];degrees=meta['hinge_axis']['nominal_open_degrees']
    lock=meta['lock_axis_xy']
    opened=dict(closed)
    opened['lid']=closed['lid'].rotate(tuple(hinge),(hinge[0]+1,hinge[1],hinge[2]),degrees)
    opened['keeper']=closed['keeper'].rotate((lock[0],lock[1],0),(lock[0],lock[1],1),90)
    board=box(-l/2,-w/2,m['seat_height'],l,w,t)
    # Metal shaft geometry is explanatory and is not exported as a print part.
    hinge_shaft=cyl(-15,hinge[1],hinge[2],1.45,30,(1,0,0))
    lock_shaft=cyl(lock[0],lock[1],0,1.45,meta['part_bounds_mm']['keeper'][1][2]+2)
    common=[(board,COLOURS['board']),(hinge_shaft,COLOURS['metal']),(lock_shaft,COLOURS['metal'])]
    left=[(s,COLOURS[r]) for r,s in closed.items()]+common
    right=[(s,COLOURS[r]) for r,s in opened.items()]+common
    im1,_=render(left,(1100,910),(95,120,85),(0,1,22),40)
    im2,_=render(right,(1100,910),(95,120,85),(0,1,27),44)
    canvas=Image.new('RGB',(2200,1580),'white');canvas.paste(im1,(0,140));canvas.paste(im2,(1100,140))
    d=ImageDraw.Draw(canvas)
    text(d,(55,24),'方案A  先旋开拨片，再翻开压框',46)
    text(d,(90,105),'闭合：拨片0°',40)
    text(d,(1160,105),f'开启：拨片90°／压框{degrees:g}°',40)
    detail=[(closed['keeper'],COLOURS['keeper']),(closed['detent'],COLOURS['detent'])]
    im3,_=render(detail,(860,400),(35,65,65),(-7,20,25),12)
    canvas.paste(im3,(30,1100))
    text(d,(70,1060),'拨片与簧片局部（底座隐去）',36)
    text(d,(980,1100),'金属M3轴承载；不靠PLA自攻螺纹',38)
    text(d,(980,1170),'刚性拨片重叠2.3 mm，限制压框抬起',38)
    text(d,(980,1240),'独立簧片厚1.16 mm，仅防误转',38)
    text(d,(980,1310),'名义挠度0.25 mm；硬止挡限制0°／90°',38)
    text(d,(70,1490),'以STM32夹具本地坐标示意；中心与接口开放，反面排针在20 mm架空区内。',34,fill='#435866')
    canvas.save(PREVIEW/'03_clamp_open_closed.png')

def battery_speaker():
    battery=[(load('P05_BATTERY_cradle'),COLOURS['body'])]
    for side in ['L','R']:
        for r in ['keeper','detent']:battery.append((load('BAT_'+side+'_'+r),COLOURS[r]))
    for x in [-22,22]:battery.append((box(x-4,-18.2,2.4,8,36.4,2),'#34424c'))
    battery.append((box(-38,-20,4.4,76,40,20),COLOURS['battery']))
    spk=load('P07_SPEAKER_cradle')
    speaker=[(spk,COLOURS['body']),(cyl(0,0,2,20,14),COLOURS['speaker'],.22)]
    im1,projected=render(battery,(1100,900),(150,-155,115),(0,0,12),58,labels={'wire':(40,0,10)})
    im2,_=render(speaker,(1100,900),(100,-135,110),(0,0,4),36)
    canvas=Image.new('RGB',(2200,1370),'white');canvas.paste(im1,(0,150));canvas.paste(im2,(1100,150))
    d=ImageDraw.Draw(canvas)
    text(d,(55,24),'电池托架与喇叭可调安装座',46)
    text(d,(80,112),'2S串联电池  76×40×20 mm',40)
    text(d,(1190,112),'喇叭  Ø40×14 mm',40)
    text(d,(75,1080),'两端拨片限位，压在塑料壳边',38)
    text(d,(75,1145),'支承条铺2 mm EVA；+X侧留出线口',38)
    text(d,(1160,1080),'耳孔中心距48 mm；座孔Ø3.4 mm',38)
    text(d,(1160,1145),'耳片高度未定，用上下螺母与垫片调平',38)
    text(d,(70,1270),'灰色托架与定位圈来自最终CAD；电池、EVA及喇叭仅为尺寸／装配包络，不能当作实物照片。',31,fill='#435866')
    canvas.save(PREVIEW/'04_battery_speaker.png')

if __name__=='__main__':
    scene,centres=assembly_scene()
    layout(scene)
    print('01_layout.png',flush=True)
    overview(scene,centres)
    print('02_base_3d.png',flush=True)
    clamp_demo()
    print('03_clamp_open_closed.png',flush=True)
    battery_speaker()
    print('04_battery_speaker.png',flush=True)
