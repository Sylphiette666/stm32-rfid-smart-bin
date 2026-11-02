"""Actual CAD previews and locating dimensions for the new rounded blind pockets."""
from pathlib import Path
import json
import cadquery as cq
import vtk
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
from matplotlib.backends.backend_pdf import PdfPages
B=Path(__file__).resolve().parents[1];BASE=B/'motor-existing-holes-20261102';O=B/'motor-existing-holes-light-20261103'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
d=load(O/'checks/design.json');old=load(BASE/'checks/slicing.json');new=load(O/'checks/slicing.json')
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
font=lambda size:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
def actor(shape,col):
    vertices,faces=shape.tessellate(.10);pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vertices:pts.InsertNextPoint(v.x,v.y,v.z)
    for f in faces:
        tri=vtk.vtkTriangle()
        for i,j in enumerate(f):tri.GetPointIds().SetId(i,j)
        cells.InsertNextCell(tri)
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells);norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(30);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*col);a.GetProperty().SetAmbient(.12);a.GetProperty().SetDiffuse(.85);return a
for name,v in d['variants'].items():
    carrier=cq.importers.importStep(str(O/'step'/f'D06_CARRIER_{name}_ASSEMBLY.step')).val();seat=cq.importers.importStep(str(BASE/'step'/f'D06_SEAT_{name}_ASSEMBLY.step')).val()
    r=vtk.vtkRenderer();r.SetBackground(1,1,1);r.AddActor(actor(carrier,(.27,.57,.69)));r.AddActor(actor(seat,(.86,.61,.29)))
    bb=carrier.BoundingBox();cx=(bb.xmin+bb.xmax)/2;cy=(bb.ymin+bb.ymax)/2
    cam=r.GetActiveCamera();cam.SetPosition(cx-95,cy-125,105);cam.SetFocalPoint(cx,cy,-8);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();r.ResetCamera()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1050,750);win.AddRenderer(r);win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update();w=vtk.vtkPNGWriter();w.SetFileName(str(O/'preview'/f'{name}_light.png'));w.SetInputConnection(f.GetOutputPort());w.Write();win.Finalize()
canvas=Image.new('RGB',(2200,1190),'white');draw=ImageDraw.Draw(canvas)
draw.text((55,25),'电机转接板轻量化版',font=font(47),fill='#203d49')
for i,name in enumerate(['LEFT','RIGHT']):
    draw.text((55+1100*i,115),'LEFT 非舵机侧  3处轻量化浅腔' if i==0 else 'RIGHT 舵机侧  4处轻量化浅腔',font=font(32),fill='#203d49')
    canvas.paste(Image.open(O/'preview'/f'{name}_light.png'),(25+1100*i,170))
draw.text((55,940),'保留16mm总厚度、孔周承力台与主要连接筋；轻量化浅腔深11mm，底层留5mm。',font=font(33),fill='#203d49')
mass=100*(1-new['filament_g']/old['filament_g']);minutes=(old['estimated_seconds']-new['estimated_seconds'])/60
draw.text((55,1010),f"同参数切片：{old['filament_g']:.1f}g → {new['filament_g']:.1f}g，省料{mass:.1f}%；缩短约{minutes:.0f}分钟。",font=font(33),fill='#203d49')
draw.text((55,1080),'孔位、M3×30/M3×25螺丝、安装高度和原穿槽座保持；打印后仍需承载试装。',font=font(31),fill='#455760')
canvas.save(O/'preview/01_lightweight_assembly.png')

with PdfPages(O/'lightening_pockets.pdf') as pdf:
    for name,v in d['variants'].items():
        fig,(ax,tab)=plt.subplots(1,2,figsize=(11.69,8.27),gridspec_kw={'width_ratios':[1.25,1]})
        ax.add_patch(Polygon(v['outline'],facecolor='#cbdde5',edgecolor='#243e4b',lw=1.5))
        for p in v['top_reliefs']:ax.add_patch(Circle(p['xy'],4,fill=False,ls=':',ec='#9ba7ad',lw=.65))
        rows=[]
        for p in v['pockets']:
            ax.add_patch(Polygon(p['outline_xy'],facecolor='white',edgecolor='#3a7c95',lw=1.4))
            for ring in p['protected_island_rings_xy']:ax.add_patch(Polygon(ring,facecolor='#cbdde5',edgecolor='#3a7c95',lw=1))
            x0,y0,x1,y1=p['bounds_mm'];ax.text((x0+x1)/2,(y0+y1)/2,p['id'],fontsize=10,ha='center',va='center',color='#a96320')
            rows.append([p['id'],f'{x0:.2f}\n{y0:.2f}',f'{x1-x0:.2f}\n{y1-y0:.2f}','11\n5'])
        for p in [a['xy'] for a in v['anchors']]+v['seat_connection_holes']:ax.add_patch(Circle(p,1.7,fill=False,ec='#172e38',lw=.8))
        ax.autoscale_view();ax.set_aspect('equal');ax.set_xlabel('X / mm');ax.set_ylabel('yb / mm');ax.grid(alpha=.15);ax.set_title('贴底板面正投影',fontsize=13)
        tab.axis('off');table=tab.table(cellText=rows,colLabels=['浅腔','左下角\nX / yb','包络宽\n包络高','深度\n底层'],colWidths=[.17,.3,.3,.23],loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,3.2)
        for (ri,ci),cell in table.get_celld().items():cell.set_edgecolor('#b5c1c7');cell.set_facecolor('#dce8ef' if ri==0 else 'white')
        fig.suptitle(f'{name} 轻量化浅腔定位  mm',fontsize=18,y=.96)
        fig.text(.07,.15,'浅腔轮廓圆角名义R2；表中包络仅用于定位，实际形状按模型和轮廓点表。',fontsize=10)
        fig.text(.07,.11,'X=0车尾边，yb=0非舵机侧边。9个底板孔和原座连接孔按第66.12节保持。',fontsize=10)
        fig.text(.07,.07,'原五金避空、六角窝及拼接片凹位保持；原最薄4mm避空处不再减薄。',fontsize=10)
        fig.tight_layout(rect=[.03,.20,.98,.92]);pdf.savefig(fig);fig.savefig(O/'preview'/f'{name}_pocket_dimensions.png',dpi=160);plt.close(fig)
comparison={'baseline_filament_g':old['filament_g'],'light_filament_g':new['filament_g'],'filament_saved_percent':mass,'baseline_seconds':old['estimated_seconds'],'light_seconds':new['estimated_seconds'],'time_saved_minutes':minutes,'CAD_volume_saved_percent':d['total_volume_reduction_percent'],'same_slicing_parameters':True,'physical_strength_equivalence_claimed':False}
(O/'checks/comparison.json').write_text(json.dumps(comparison,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(comparison))
