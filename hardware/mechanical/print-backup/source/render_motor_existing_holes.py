"""Draw current-hole coordinates and actual CAD assembly without invented motor envelopes."""
from pathlib import Path
import json,csv,math
import cadquery as cq
import vtk
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,Rectangle
from matplotlib.backends.backend_pdf import PdfPages
B=Path(__file__).resolve().parents[1];O=B/'motor-existing-holes-20261102'
d=json.loads((O/'checks/design.json').read_text(encoding='utf-8-sig'))
base=json.loads((B/'flat-split-20261101/source/design.json').read_text(encoding='utf-8-sig'))
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
colors={'LEFT':'#3580a3','RIGHT':'#b87932'}

# Coordinate page is a top projection of the original chassis, not a mirrored bottom view.
fig,ax=plt.subplots(figsize=(12,10));ax.add_patch(Rectangle((0,0),280,220,facecolor='#edf2f3',edgecolor='#273d48',lw=2))
ax.axvline(138,color='#9ca8ad',ls='--',lw=1)
for h in base['mount_holes']:
    ax.add_patch(Circle(h['xy'],1.7,fill=False,edgecolor='#a6afb5',lw=.7))
for p in base['joint']['new_holes']:ax.add_patch(Circle(p,1.7,fill=False,edgecolor='#a6afb5',lw=.7))
for name,v in d['variants'].items():
    c=colors[name];ax.add_patch(Polygon(v['outline'],facecolor=c,alpha=.24,edgecolor=c,lw=2))
    for i,a in enumerate(v['anchors'],1):
        x,y=a['xy'];ax.plot(x,y,'o',color=c,ms=7);ax.annotate(f'{"L" if name=="LEFT" else "R"}{i}',(x,y),xytext=(5,7),textcoords='offset points',fontsize=10,color=c,weight='bold')
    for x,y in v['seat_connection_holes']:ax.plot(x,y,'x',color=c,ms=7,mew=1.8)
    x,y=v['retained_motor_seat_datum'];ax.plot(x,y,'+',color='#c53036',ms=14,mew=2)
ax.annotate('车头 +X',(277,110),(230,110),arrowprops={'arrowstyle':'->','color':'#273d48'},fontsize=12,va='center')
ax.text(-7,110,'车尾',rotation=90,va='center',ha='right',fontsize=12)
ax.text(65,-11,'非舵机侧 LEFT',ha='center',fontsize=12,color=colors['LEFT'])
ax.text(145,232,'舵机侧 RIGHT',ha='center',fontsize=12,color=colors['RIGHT'])
ax.set(xlim=(-18,290),ylim=(-18,242),aspect='equal',xlabel='X / mm  从车尾边起算',ylabel='yb / mm  从非舵机侧边起算')
ax.set_title('底板现有孔位与新转接板位置\n从上向下投影，转接板实际位于底板下方',fontsize=17,pad=20)
ax.grid(alpha=.15);fig.text(.12,.02,'圆点：共用现有孔  ·  叉号：新转接板与原穿槽座连接孔  ·  红十字：原穿槽基准，不是轮轴实测位置',fontsize=10)
fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(O/'preview/01_existing_hole_layout.png',dpi=180);plt.close(fig)

def actor(shape,color):
    vertices,faces=shape.tessellate(.12);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vertices:pts.InsertNextPoint(v.x,v.y,v.z)
    for f in faces:
        tri=vtk.vtkTriangle()
        for i,j in enumerate(f):tri.GetPointIds().SetId(i,j)
        cells.InsertNextCell(tri)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells);mp=vtk.vtkPolyDataMapper();mp.SetInputData(poly)
    a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(*color);return a

for name,v in d['variants'].items():
    carrier=cq.importers.importStep(str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val()
    seat=cq.importers.importStep(str(O/'step'/f'D06_SEAT_{name}_ASSEMBLY.step')).val()
    renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1)
    renderer.AddActor(actor(carrier,(.29,.58,.69)));renderer.AddActor(actor(seat,(.88,.62,.26)))
    bb=carrier.BoundingBox();cx=(bb.xmin+bb.xmax)/2;cy=(bb.ymin+bb.ymax)/2
    camera=renderer.GetActiveCamera();camera.SetPosition(cx-110,cy-150,-110);camera.SetFocalPoint(cx,cy,4);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();renderer.ResetCamera()
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1100,760);window.AddRenderer(renderer);window.Render()
    f=vtk.vtkWindowToImageFilter();f.SetInput(window);f.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(O/'preview'/f'{name}_stack.png'));writer.SetInputConnection(f.GetOutputPort());writer.Write();window.Finalize()

canvas=Image.new('RGB',(1800,1000),'white');draw=ImageDraw.Draw(canvas)
draw.text((50,28),'新厚转接板与原穿槽座安装关系',font=font(43),fill='#203a46')
for i,name in enumerate(['LEFT','RIGHT']):
    im=Image.open(O/'preview'/f'{name}_stack.png');im.thumbnail((850,690));canvas.paste(im,(30+900*i,150))
    draw.text((65+900*i,110),'非舵机侧  LEFT（5个现有孔）' if i==0 else '舵机侧  RIGHT（4个现有孔）',font=font(29),fill='#203a46')
draw.text((50,840),'蓝色：新增16mm厚转接板；橙色：已试配合适的原穿槽座，继续复用。',font=font(31),fill='#203a46')
draw.text((50,900),'转接板上表面贴底板；原穿槽座固定在其下方。图中未画电机、轮胎和全部五金。',font=font(28),fill='#42505a')
canvas.save(O/'preview/02_stack_assembly.png')

canvas=Image.new('RGB',(1700,1150),'white');draw=ImageDraw.Draw(canvas)
draw.text((45,25),'共孔固定与预埋螺母装配剖面',font=font(41),fill='#203a46')
draw.text((45,100),'A  模块底座共孔处  M3×30',font=font(30),fill='#203a46')
# Schematic, explicitly not a drill template.
x=70;w=610;y=180;s=13
draw.rectangle((x+170,y,x+390,y+31),fill='#c69a61');draw.text((x+400,y),'原模块座脚 2.4mm',font=font(24),fill='#203a46')
draw.rectangle((x,y+31,x+w,y+96),fill='#ccd7df');draw.text((x+35,y+50),'原底板 5mm',font=font(25),fill='#203a46')
draw.rectangle((x,y+96,x+w,y+304),fill='#5294aa');draw.text((x+30,y+170),'新转接板 16mm',font=font(28),fill='white')
draw.rectangle((x+255,y-10,x+305,y+355),fill='#697780');draw.ellipse((x+235,y-30,x+325,y-5),fill='#697780')
draw.rectangle((x+235,y+310,x+325,y+362),fill='#59676f');draw.text((x+345,y+320),'垫圈＋防松螺母',font=font(24),fill='#203a46')
draw.text((850,100),'B  原穿槽座连接处  M3×25',font=font(30),fill='#203a46')
x=875
draw.rectangle((x,y,x+650,y+65),fill='#ccd7df');draw.text((x+30,y+15),'原底板 5mm',font=font(25),fill='#203a46')
draw.rectangle((x,y+65,x+650,y+273),fill='#5294aa')
draw.rectangle((x+225,y+65,x+335,y+143),fill='white')
draw.rectangle((x+245,y+85,x+315,y+137),fill='#59676f')
draw.rectangle((x+265,y+72,x+295,y+424),fill='#697780')
draw.rectangle((x,y+273,x+650,y+390),fill='#c69a61')
draw.ellipse((x+235,y+405,x+325,y+430),fill='#697780')
draw.text((x+355,y+90),'先放垫圈和M3锁母',font=font(23),fill='#203a46')
draw.text((x+355,y+165),'新转接板 16mm',font=font(25),fill='white')
draw.text((x+355,y+295),'原穿槽座 9mm',font=font(25),fill='#203a46')
draw.text((x+355,y+405),'从下面向上拧入',font=font(24),fill='#203a46')
lines=[
 '1  先把4组垫圈＋锁母放进每块转接板朝底板面的六角窝，螺丝尾端低于贴合面。',
 '2  先把T形片穿入原座，再用4颗M3×25把原座连接转接板，最后装电机。',
 '3  共孔螺丝换成M3×30；右板共用靠舵机侧拼接片（中心138,138）的2孔。',
 '4  拼接片处不叠模块座脚，已有拼接片坐入右板预留凹位；不能重复夹入原下螺母。',
 '5  共孔螺丝一颗一颗更换，所有螺纹先带上再交替轻紧，不把PLA压白或压裂。',
 '剖面为安装关系示意，不按图片比例加工。实物孔轴、轮胎净隙及承载需装配后验证。']
for i,t in enumerate(lines):draw.text((48,690+i*65),t,font=font(26 if i<5 else 24),fill='#203a46')
canvas.save(O/'preview/03_fastener_sections.png')

# All functional holes and recesses have specifications and original chassis datum coordinates.
records=[]
with PdfPages(O/'interface_coordinates.pdf') as pdf:
    for name,v in d['variants'].items():
        fig,(ax,tableax)=plt.subplots(1,2,figsize=(16.54,11.69),gridspec_kw={'width_ratios':[1.05,1]})
        ax.add_patch(Polygon(v['outline'],facecolor='#e3eef3',edgecolor='#243c48',lw=1.5))
        rows=[];idx=0
        for kind,points in [('现有孔共用',[a['xy'] for a in v['anchors']]),('原座连接',v['seat_connection_holes'])]:
            for p in points:
                idx+=1;code=f'{name[0]}{idx}';ax.add_patch(Circle(p,1.7,fill=False,ec='#1d4354'));ax.annotate(code,p,xytext=(4,5),textcoords='offset points',fontsize=9)
                spec='通孔Ø3.4' if kind=='现有孔共用' else 'Ø3.4＋对边6.0六角窝深6'
                rows.append([code,f'{p[0]:g}',f'{p[1]:g}',spec])
                records.append({'part':name,'id':code,'kind':kind,'x_mm':p[0],'yb_mm':p[1],'spec':spec})
        for i,p in enumerate(v['top_reliefs'],1):
            ax.add_patch(Circle(p['xy'],4,fill=False,ec='#949ba0',ls='--',lw=.6))
            rows.append([f'P{i}',f"{p['xy'][0]:g}",f"{p['xy'][1]:g}",f"Ø8盲避空 深{p['depth_from_top']}"])
            records.append({'part':name,'id':f'P{i}','kind':'top hardware relief','x_mm':p['xy'][0],'yb_mm':p['xy'][1],'spec':rows[-1][-1]})
        for i,p in enumerate(v['splice_clearance_recesses'],1):
            x,y=p['centre'];ax.add_patch(Rectangle((x-20.5,y-12.5),41,25,fill=False,ec='#666666',ls=':'))
            rows.append([f'J{i}',f'{x:g}',f'{y:g}','41×25避空 深5'])
            records.append({'part':name,'id':f'J{i}','kind':'splice bridge recess','x_mm':x,'yb_mm':y,'spec':'41x25 depth5 from top'})
        ax.autoscale_view();ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_xlabel('X / mm');ax.set_ylabel('yb / mm')
        ax.set_title('贴底板面正投影  原底板全局坐标',fontsize=13)
        tableax.axis('off');t=tableax.table(cellText=rows,colLabels=['编号','X','yb','规格 mm'],loc='center',cellLoc='center',colWidths=[.12,.15,.15,.58]);t.auto_set_font_size(False);t.set_fontsize(9);t.scale(1,1.7)
        for (r,c),cell in t.get_celld().items():cell.set_edgecolor('#b3bdc4');cell.set_facecolor('#dce8ef' if r==0 else 'white')
        fig.suptitle(f'D06 {name} 现有孔转接板 16mm厚  接口坐标图',fontsize=19,y=.96)
        fig.text(.08,.075,'X=0车尾，yb=0非舵机侧底板边。所有通孔均在新转接板上；底板不增加孔。',fontsize=11)
        fig.text(.08,.045,'装配孔距以坐标表为准；PLA、100%打印。配合间隙需实物试装，非额定承重证明。',fontsize=11)
        fig.tight_layout(rect=[.03,.1,.98,.93]);pdf.savefig(fig);fig.savefig(O/'preview'/f'{name}_coordinates.png',dpi=140);plt.close(fig)
with (O/'source/interface_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
print('Rendered layout, actual CAD stack, sections and complete interface coordinate sheets')
