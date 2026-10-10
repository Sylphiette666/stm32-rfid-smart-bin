from diagram_common import *

items=[]
def add(d,id,anchor,caption,alt):
    d.save(id);items.append(dict(id=id,file='figures/'+id+'.png',anchor=anchor,position='before',caption=caption,alt=alt))

d=Diagram('万用表先选对插孔和档位','左图测电压可通电；右图测通断必须先拔电池和所有 USB。',900)
def meter(x,y,display,mode):
    d.rect((x,y,x+310,y+430),'#EDF2F5',INK,4,18)
    d.rect((x+28,y+25,x+282,y+110),'#FFFFFF',INK,3,7);d.center((x+28,y+25,x+282,y+110),display,43,bold=True)
    d.circle((x+155,y+215),60,'#D3DDE3',INK,3)
    d.line([(x+155,y+215),(x+155,y+161)],BLUE,12)
    d.center((x+12,y+285,x+298,y+325),mode,32)
    for xx,label,c in [(x+50,'A',MUTED),(x+155,'COM',INK),(x+260,'VΩ',RED)]:
        d.circle((xx,y+389),15,c);d.text((xx,y+338),label,31,c,anchor='mt')
    d.line([(x+32,y+369),(x+68,y+407)],RED,5)
    d.line([(x+68,y+369),(x+32,y+407)],RED,5)
    return (x+155,y+389),(x+260,y+389)
d.text((55,150),'① 直流电压',38,bold=True)
b,r=meter(70,215,'5.00 V','直流 V 档')
d.rect((535,280,815,485),'#F6F7F2',INK,3,8);d.center((535,280,815,375),'5 V 母线',36)
d.circle((590,420),10,RED);d.circle((760,420),10,INK)
d.text((590,374),'+5 V',30,RED,anchor='mt');d.text((760,374),'GND',30,anchor='mt')
d.line([b,(b[0],755),(825,755),(825,535),(760,535),(760,420)],INK,5)
d.line([r,(460,r[1]),(460,525),(590,525),(590,420)],RED,5)
d.text((495,175),'两支表笔跨接被测两点',30)
d.text((505,600),'黑笔接 GND\n红笔接 +5 V',34)
d.text((970,150),'② 断电通断',38,bold=True)
b,r=meter(970,215,'接近 0 Ω','通断 / 蜂鸣档')
d.text((1360,220),'只测一段导线\n或一个开关',34)
d.circle((1400,420),10,INK);d.circle((1675,420),10,RED)
d.line([(1400,420),(1505,420),(1580,420),(1675,420)],BLUE,8)
d.line([b,(b[0],755),(1370,755),(1370,510),(1400,510),(1400,420)],INK,5)
d.line([r,(r[0]+35,r[1]),(r[0]+35,790),(1730,790),(1730,420),(1675,420)],RED,5)
d.text((1380,550),'导通时接近零欧\n断开时显示 OL\n先短接表笔自检',34)
d.footer('两种测法都用 COM 与 VΩ 孔；图中 A 电流孔不使用。表盘与显示按自己的仪表识别。')
add(d,'g01_multimeter','步骤 002  测电压','测电压时表笔并接两点；测通断前先断电，不能只把旋钮换档。','万用表直流电压与断电通断的两幅接线示意，黑笔COM红笔VΩ。')

d=Diagram('电源线从剪线到压紧','以螺丝压线端子为例；剥线长度最终按所购端子的说明确定。',820)
for x,n,title in [(40,1,'量长和剥线'),(635,2,'压接端头'),(1230,3,'插到底再压紧')]:
    d.number((x+27,181),n);d.text((x+70,157),title,37,bold=True)
# stripped wire
d.line([(70,330),(355,330)],RED,52)
for yy in [-16,-8,0,8,16]:d.line([(355,330+yy),(465,330+yy)],'#B98540',5)
d.dim((355,405),(465,405),'约 4–6 mm',(0,50))
d.text((60,510),'铜丝不被割断\n捻齐散开的细丝\n线长留约 30 mm 余量',34)
d.arrow([(530,345),(595,345)])
# crimp collar and ferrule
d.line([(665,330),(795,330)],RED,48)
d.rect((795,287,890,373),'#DFE7ED',INK,3,8)
d.rect((890,307,1090,353),'#BDC8D1',INK,3)
d.line([(930,307),(947,353),(965,307)],MUTED,3)
d.text((700,428),'绝缘套',32);d.arrow([(780,418),(833,377)],MUTED,3)
d.text((960,428),'金属管',32);d.arrow([(1005,418),(1005,357)],MUTED,3)
d.text((655,510),'选匹配线径的冷压端头\n用压线钳压牢\n端子不适配时按厂家方法接线',34)
d.arrow([(1125,345),(1190,345)])
# terminal screw wire
d.rect((1435,265,1725,426),'#88B89C',INK,4,9)
d.circle((1590,310),29,'#D4D9DE',INK,3);d.line([(1569,310),(1611,310)],INK,5)
d.rect((1440,354,1535,400),'#30383D',INK,2)
d.line([(1265,378),(1440,378)],RED,45)
d.line([(1440,378),(1490,378)],'#B98540',16)
d.line([(1373,350),(1435,350),(1435,403),(1373,403)],INK,3)
d.arrow([(1720,485),(1650,410),(1590,343)],BLUE,4)
d.text((1525,442),'旋紧螺丝',32)
d.text((1250,510),'铜线藏在端子内\n外面不留散丝或大锡团\n轻拉检查，不松动才合格',34)
d.footer('接线完成后贴同名标签；主电源和执行器供电用相应线径，不用细杜邦线代替。')
add(d,'g02_wire_terminal','步骤 004  制作一条电源线','剥线、压接、锁紧、轻拉检查按顺序完成；裸铜不能伸到相邻端子。','三步电源线剥皮、压冷压端头和插入螺丝端子的示意。')

d=Diagram('洞洞板正反面与焊点检查','示例是独立圆焊盘洞洞板；同一排小孔并不会自动导通。',940)
for x,title in [(45,'元件面'),(645,'焊接面')]:
    d.text((x,155),title,38,bold=True)
    d.rect((x,232,x+475,615),'#F0E9CC',INK,3,6)
    for row in range(4):
        for col in range(5):
            xx=x+57+col*90;yy=282+row*87
            d.circle((xx,yy),22,'#C39A55' if x>500 else '#A29872');d.circle((xx,yy),9,'white')
# resistor top, leads
d.line([(102,369),(102,412),(372,412),(372,456)],INK,5)
d.rect((181,393,294,431),'#BADEF0',INK,3,7)
d.text((70,662),'先焊一个脚定位\n校正后再焊其余脚',34)
# solder bottom mirrored conceptual separate connection
d.line([(1062,369),(1062,543),(972,543)],BLUE,9)
for xy in [(1062,369),(792,456),(972,543)]:d.circle(xy,27,'#C7D0D6',INK,3);d.circle(xy,7,INK)
d.text((670,662),'翻面后孔位左右镜像\n蓝线另接指定焊盘',34)
d.text((1200,155),'放大看焊点',38,bold=True)
def pad(cx,cy,kind):
    d.circle((cx,cy),60,'#C49B58',INK,3)
    d.circle((cx,cy),43,'#C4CFD6',INK,2);d.circle((cx,cy),9,INK)
    if kind=='cold':
        d.circle((cx,cy),30,None,RED,7)
    if kind=='bridge':
        d.circle((cx+155,cy),60,'#C49B58',INK,3);d.circle((cx+155,cy),40,'#C4CFD6',INK,2)
        d.line([(cx+33,cy),(cx+120,cy)],'#C4CFD6',27)
pad(1280,285,'good');d.text((1400,248),'合格\n焊盘与引脚润湿',32,GREEN)
pad(1280,463,'cold');d.text((1400,425),'重焊\n有裂纹或活动',32,RED)
pad(1280,653,'bridge');d.text((1515,617),'清理\n相邻连锡',32,RED)
d.text((52,802),'焊接顺序：同时加热焊盘和引脚 → 送锡 → 先撤锡丝 → 撤烙铁 → 冷却再剪脚',33)
d.footer('每焊一组，用断电通断档确认应通的通、应断的断；图示布线只说明方法，不是 IO 板完整接线图。')
add(d,'g03_perfboard','步骤 005  完成一个焊点','先识别洞洞板铜箔结构，再焊导线建立网络；焊点发亮程度不能单独证明接触可靠。','独立焊盘洞洞板的元件面、焊接面及合格、裂纹和连锡焊点放大图。')

d=Diagram('先单独调压再接核心板和模块','首次使用限流电源；负载和电池替换顺序仍按步骤 097 至 102 完成。',920)
d.block((50,210,410,390),'限流电源\n模拟 2S 输入',size=37)
d.block((635,210,1035,390),'可调降压模块\nIN   →   OUT',size=37)
d.arrow([(410,255),(635,255)],RED,6);d.text((450,198),'+ 输入',31,RED)
d.line([(410,345),(635,345)],INK,5);d.text((440,363),'GND',31)
d.line([(1035,255),(1230,255)],RED,6);d.circle((1230,255),9,RED)
d.line([(1035,345),(1230,345)],INK,5);d.circle((1230,345),9,INK)
d.rect((1400,195,1750,395),'#ECF2F5',INK,3,12);d.center((1400,208,1750,312),'5.00 V',48,bold=True)
d.center((1400,310,1750,385),'万用表直流档',32)
d.line([(1230,255),(1400,255)],RED,5);d.line([(1230,345),(1400,345)],INK,5)
d.arrow([(842,475),(842,393)],BLUE);d.text((500,480),'① 调到约 5 V，核对极性与稳定性',36)
d.text((500,546),'② 先做规定的空载与分级负载测试',36)
d.text((500,612),'③ 断电，确认母线低于 0.5 V，再接模块',36)
d.text((500,678),'④ 上电复测 5V_BUS 和 3V3_EXT',36)
d.block((65,522,377,707),'待接模块\n此时先不连接',size=35)
d.text((64,765),'5 V 供电由配电点分支；3V3_EXT 与核心板自身 3V3 是两个输出，不相互短接。',34)
d.footer('电机、舵机的大电流供电不穿过核心板；所有支路的 GND 接到公共地。')
add(d,'g04_voltage_first','步骤 097  E007 安装降压板并单独调压','万用表跨在降压输出端，先调压和做负载检查；断电后才接下一块模块。','限流电源、降压模块和万用表的单独调压接线以及四步接入顺序。')

manifest('general',items)
print('generated',len(items))
