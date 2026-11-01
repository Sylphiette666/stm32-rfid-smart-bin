from pathlib import Path
import vtk,json
from PIL import Image,ImageDraw,ImageFont
B=Path(__file__).resolve().parents[1];O=B/'motor-adapter-20261101'
font=lambda size:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
canvas=Image.new('RGB',(1800,1330),'white');d=ImageDraw.Draw(canvas)
d.text((50,20),'电机转接座：保持 3 mm 穿槽区，外围加固',font=font(40),fill='#153845')
for i,name in enumerate(['LEFT','RIGHT']):
 rd=vtk.vtkSTLReader();rd.SetFileName(str(O/'parts'/f'D06_ADAPTER_{name}.stl'));rd.Update()
 mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(rd.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mp);a.GetProperty().SetColor(.25,.52,.66)
 r=vtk.vtkRenderer();r.SetBackground(1,1,1);r.AddActor(a);b=rd.GetOutput().GetBounds();c=r.GetActiveCamera();cx=(b[0]+b[1])/2;cy=(b[2]+b[3])/2;c.SetPosition(cx-25,cy-65,95);c.SetFocalPoint(cx,cy,3);c.SetViewUp(0,1,0);c.ParallelProjectionOn();r.ResetCamera()
 w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(820,510);w.AddRenderer(r);w.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(w);f.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(O/'preview'/f'{name}.png'));wr.SetInputConnection(f.GetOutputPort());wr.Write();w.Finalize()
 canvas.paste(Image.open(O/'preview'/f'{name}.png'),(40+i*900,125));d.text((55+i*900,88),('分耳座：非舵机侧（LEFT文件）' if i==0 else '偏耳座：舵机侧（RIGHT文件）'),font=font(30),fill='#153845')
d.text((50,645),'安装剖面示意（非等比例，固定片与电机省略部分轮廓）',font=font(30),fill='#153845')
# Cross section through one head: adapter top shelf at3, chassis underside at9.
x0=100;y0=1120;scale=24
Y=lambda z:y0-z*scale
d.rectangle((x0,Y(14),1050,Y(9)),fill='#d4dce1',outline='#44535c',width=3)
d.text((1100,Y(14)+25),'底板：5 mm 厚加强区',font=font(29),fill='#263943')
d.rectangle((x0+20,Y(9),x0+130,Y(0)),fill='#4085a8');d.rectangle((900,Y(9),1030,Y(0)),fill='#4085a8')
d.rectangle((x0+20,Y(3),490,Y(0)),fill='#4085a8');d.rectangle((550,Y(3),1030,Y(0)),fill='#4085a8')
d.rectangle((490,Y(3),550,Y(-4)),fill='#b98c4c');d.rectangle((440,Y(8),600,Y(3)),fill='#b98c4c',outline='#72562e',width=2)
d.text((650,Y(8)+12),'T形宽头实测 5 mm',font=font(27),fill='#72562e')
d.text((1100,Y(7)),'宽头腔：6 mm\n留约 1 mm 装配余量',font=font(28),fill='#263943',spacing=8)
d.text((1100,Y(2)),'穿槽区：3 mm\n电机在其下方',font=font(28),fill='#263943',spacing=8)
d.text((50,1240),'先装固定片和电机，再放到底板下试摆。尚未确定轮胎净隙，暂不要按候选坐标钻孔。',font=font(28),fill='#8a4519')
canvas.save(O/'preview/installation.png')
