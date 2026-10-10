from draw_manual import *
im,d=start('底板与上平台定位  全局XY坐标  单位mm',1730)
s=4.25;ox=135;oy=820
def P(x,y):return(ox+x*s,oy-y*s)
for coords,col,w in [((0,110,280,-110),INK,5),((20,95,260,-95),GRAY,3),((70,75,230,-75),BLUE,5)]:
 x1,y1,x2,y2=coords;d.rectangle([P(x1,y1),P(x2,y2)],outline=col,width=w)
for y in [-126,126]:
 d.rectangle([P(57.5,y+13),P(122.5,y-13)],outline=INK,width=4)
for lab,x,y in [('H1',30,-85),('H2',250,-85),('H3',30,85),('H4',250,85)]:
 a=P(x,y);d.ellipse((a[0]-10,a[1]-10,a[0]+10,a[1]+10),fill=BLUE)
 txt(d,(a[0]+17,a[1]-38),lab,28)
for x,y,lab,col in [(240,0,'前球轮参考',GREEN),(200,0,'循迹阵列参考',GRAY)]:
 a=P(x,y);d.ellipse((a[0]-13,a[1]-13,a[0]+13,a[1]+13),fill=col)
txt(d,P(110,28),'桶壳\n160 × 150',32)
txt(d,(1400,210),'统一基准\nX  车尾0 → 车头280\nY  中心线0  两侧±110\nZ  地面0  竖直向上',32)
txt(d,(1400,480),'四柱中心\nH1  (30, −85)\nH2  (250, −85)\nH3  (30, +85)\nH4  (250, +85)',33)
txt(d,(1400,835),'孔位转换到板件角点\n底板 yb = Y + 110\n平台 xp = X − 20\n平台 yp = Y + 95',30)
txt(d,(1400,1080),'实物决定的孔不预钻\n电机支架  核心板\n球轮底座  舵机架\n传感器  电池绑带槽',29)
dim(d,P(0,150),P(280,150),'280')
txt(d,(150,1450),'外框P01为280×220；内层平台P02为240×190。\n轮心参考(90, ±126)，26宽轮与板边各留约3mm。\n舵机侧托片需让开H3顶螺丝，留直径≥10mm检修孔或缺口。\n灰点为下方循迹阵列(200,0)；绿点为前支撑球参考(240,0)。',30)
im.save(R/'base_layout_new.png')

im,d=start('整机侧视与高度链  参考底板离地45mm',1610)
s=2.65;ox=180;oz=1400
def P(x,z):return(ox+x*s,oz-z*s)
ln(d,P(-10,0),P(320,0),GRAY,3)
for coords,col,w in [((0,50,280,45),INK,5),((20,115,260,110),INK,5),((70,295,230,115),BLUE,5),((80,241,220,120),GRAY,3)]:
 x1,z1,x2,z2=coords;d.rectangle([P(x1,z1),P(x2,z2)],outline=col,width=w)
q=P(90,32.5);r=32.5*s;d.ellipse((q[0]-r,q[1]-r,q[0]+r,q[1]+r),outline=INK,width=5)
for x in [30,250]:ln(d,P(x,50),P(x,110),INK,6)
q=P(240,7.5);r=7.5*s;d.ellipse((q[0]-r,q[1]-r,q[0]+r,q[1]+r),outline=INK,width=4);ln(d,P(240,15),P(240,45),INK,5)
ln(d,P(75,297),P(235,297),INK,7)
ln(d,P(75,297),P(75+160*math.cos(math.radians(70)),297+160*math.sin(math.radians(70))),BLUE,7)
ln(d,P(80,265),P(220,265),RED,3)
d.rectangle([P(98,283),P(112,280)],outline=GREEN,width=5)
txt(d,(450,880),'内胆约\n140×130×121',29)
txt(d,(740,150),'工作开盖70°\n最高约450mm',31)
txt(d,(1280,190),'高度基准  Z 单位mm',35)
levels=[('地面',0),('底板下表面',45),('底板上表面',50),('上平台下表面',110),('上平台上表面',115),('壳内底板上表面',118),('PP内胆外底  含2mm垫',120),('PP内胆名义口沿',241),('对射光束参考',265),('超声探头面参考',280),('桶壳口沿',295)]
for i,(t,v) in enumerate(levels):txt(d,(1280,280+i*73),f'{t}   {v}',30)
txt(d,(1280,1140),'盖铰链轴Z1按实物确定\n舵机轴同高  两轴距50\n上图铰链高度仅示意',31)
txt(d,(120,1450),'底板高度改变时，全部参考高度同步平移；支撑球直径不等于球轮安装总高。\n新内胆更矮，满桶阈值按真实袋口重测；不能沿用旧45mm满桶值。',29,GRAY)
im.save(R/'height_layout_new.png')

im,d=start('两张木板排料  每张300×300×5mm',1570)
for off,num in [(100,1),(1200,2)]:
 ss=2.9;top=220
 d.rectangle((off,top,off+870,top+870),outline=INK,width=4)
 if num==1:parts=[(5,5,280,220,'底板 280×220'),(5,230,190,60,'舵机立架 190×60'),(200,230,80,40,'托片\n80×40')]
 else:parts=[(5,5,240,190,'上平台 240×190'),(5,200,290,95,'余料\n按实物做转接片和三角撑')]
 for x,y,w,h,t in parts:
  d.rectangle((off+x*ss,top+y*ss,off+(x+w)*ss,top+(y+h)*ss),outline=BLUE,width=3)
  txt(d,(off+x*ss+12,top+y*ss+15),t,27)
 txt(d,(off,1170),f'第{num}张  300×300×5',32)
txt(d,(100,1290),'相邻下料边预留约5mm加工间距，图示尺寸是净尺寸，不包含锯缝。\n先裁大件，再从完整余料中取立架和托片；不要先把剩料切碎。\n轮组实物若需要更大的转接片，另按实物补料。',32)
txt(d,(100,1490),'本图用于排料，不是等比例打印裁切模板。',28,GRAY)
im.save(R/'wood_nesting.png')
print('3 geometry diagrams complete')
