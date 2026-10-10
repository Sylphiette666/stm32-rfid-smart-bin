from pathlib import Path
import math, json
from docx import Document
from diagram_common import Diagram, manifest, INK, MUTED, BLUE, RED, GREEN, ORANGE, GREY

ROOT=Path(__file__).parent
BASE=ROOT.parent/'source'
MODEL=json.loads((BASE/'diagram_spec.json').read_text(encoding='utf-8'))
MECH=json.loads((BASE/'mechanical.json').read_text(encoding='utf-8'))
DOC=Document(ROOT.parent/'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册.docx')
WOOD='#E8C995'; PVC='#DAEAF4'; PP='#D5ECDD'; STEEL='#B9C3CC'; NYLON='#F1E8CE'
items=[]

def poly(d,pts,fill,outline=INK,width=3):
    d.d.polygon(pts,fill=fill);d.line(pts+[pts[0]],outline,width)

def dashed(d,a,b,color=MUTED,width=3,dash=13):
    dx,dy=b[0]-a[0],b[1]-a[1]; le=math.hypot(dx,dy)
    for n in range(0,int(le),dash*2):
        t1=n/le;t2=min(n+dash,le)/le
        d.line([(a[0]+dx*t1,a[1]+dy*t1),(a[0]+dx*t2,a[1]+dy*t2)],color,width)

def leader(d,txt,xy,pts,size=32,color=INK):
    d.text(xy,txt,size,color);d.arrow(pts,color,3,12)

def screw(d,x,ya,yb,head_at='top',col=STEEL):
    d.rect((x-7,ya,x+7,yb),col,INK,2)
    for y in range(int(ya+10),int(yb-5),10): d.line([(x-7,y+4),(x+7,y-4)],INK,2)
    hy=ya if head_at=='top' else yb
    d.rect((x-26,hy-9,x+26,hy+9),col,INK,2,4)
    d.line([(x-14,hy),(x+14,hy)],INK,3)

def washer(d,x,y,w=64):d.rect((x-w/2,y-5,x+w/2,y+5),'#DEE4E7',INK,2)

def nylon(d,x,y1,y2,w=90):
    poly(d,[(x-w/2+12,y1),(x+w/2-12,y1),(x+w/2,y1+15),(x+w/2,y2-15),(x+w/2-12,y2),(x-w/2+12,y2),(x-w/2,y2-15),(x-w/2,y1+15)],NYLON)
    d.line([(x-w/2+15,y1+10),(x-w/2+15,y2-10)],'#B8AA85',2)
    for yy,dy in [(y1,1),(y2,-1)]:
        d.rect((x-11,min(yy,yy+dy*43),x+11,max(yy,yy+dy*43)),'white',INK,2)
    dashed(d,(x,y1+50),(x,y2-50),MUTED,2,9)

def save(d,ident,mnum,caption,alt):
    d.save(ident)
    anchor=next(p.text for p in DOC.paragraphs if p.text.startswith('步骤') and f' {mnum} ' in p.text)
    items.append({'id':ident,'file':f'figures/{ident}.png','anchor':anchor,'position':'before','caption':caption,'alt':alt})

def fig_standoffs():
    d=Diagram('隔离柱怎样夹住板：60 mm 承重柱与 10 mm 托板柱','分解剖面示意｜柱两端都是内螺纹；图中垫片与螺钉略分开，装好后贴紧')
    d.text((95,150),'4 根 × 60 mm：连接上下木板',36,BLUE,True)
    d.text((980,150),'12 根 × 10 mm：固定 3 块托板',36,GREEN,True)
    x=425
    d.rect((235,255,615,290),WOOD); d.rect((235,575,615,610),WOOD)
    nylon(d,x,290,575,105)
    washer(d,x,245);washer(d,x,620)
    screw(d,x,228,330);screw(d,x,535,665,'bottom')
    d.dim((650,290),(650,575),'60 mm',(74,0))
    d.text((75,310),'P02：5 mm 木板',32);d.arrow([(210,353),(300,281)],INK,3)
    d.text((70,495),'P01：5 mm 木板',32);d.arrow([(210,537),(300,586)],INK,3)
    d.text((580,190),'M3×10 + 平垫',32);d.arrow([(680,233),(453,239)],INK,3)
    d.text((590,650),'下端同样夹紧',32);d.arrow([(675,648),(458,623)],INK,3)
    x=1250
    d.rect((1080,325,1415,345),PVC);d.rect((1080,450,1415,485),WOOD)
    nylon(d,x,345,450,105)
    washer(d,x,313);washer(d,x,499)
    screw(d,x,275,379);screw(d,x,415,552,'bottom')
    d.dim((1450,345),(1450,450),'10 mm',(85,0))
    d.text((1030,214),'薄托板：上端 M3×6 试配',32);d.arrow([(1310,258),(1250,276)],INK,3)
    d.text((1450,291),'托板',32);d.arrow([(1470,330),(1390,335)],INK,3)
    d.text((980,580),'5 mm 支承板：下端 M3×10 试配',32)
    d.text((980,645),'先试拧：螺钉不能顶住内孔底部。',32,RED)
    d.footer('示意不按比例。孔径约 3.4 mm；有效咬合按实物确认；尼龙柱轻拧，不能靠大力消除间隙。')
    save(d,'mech01_standoff_stack','M09','先按剖面试装一根，确认板被夹紧且螺钉未顶底，再装其余立柱。','60毫米双通柱位于两块5毫米木板之间；10毫米双通柱位于薄托板和支承板之间，两端分别加平垫及螺钉。')

def fig_wheels():
    d=Diagram('两驱轮与前万向球：先让三个支点同时落地','侧视｜左右驱动轮在图中重叠；两侧轮径、支架和轴高必须相同')
    ground=660
    d.line([(210,ground),(1550,ground)],INK,5)
    d.rect((300,445,1350,465),WOOD);d.rect((360,200,1290,220),WOOD)
    for x in [390,1240]:nylon(d,x,220,445,38)
    d.circle((620,530),130,'#343F46',INK,4);d.circle((620,530),88,'#65747E',INK,3);d.circle((620,530),21,STEEL,INK,3)
    d.line([(460,465),(460,492)],STEEL,13)
    d.rect((420,490,590,563),'#E8D36B',INK,3,10)
    d.line([(580,530),(620,530)],STEEL,15)
    d.rect((1180,465,1270,510),WOOD)
    d.rect((1170,510,1280,532),STEEL)
    d.line([(1190,530),(1190,580),(1210,602)],STEEL,16)
    d.line([(1260,530),(1260,580),(1240,602)],STEEL,16)
    d.circle((1225,630),30,'#EDF0F2',INK,4)
    d.dim((1510,465),(1510,660),'Hb = 45 参考',(110,0))
    d.dim((1370,510),(1370,660),'Hc 实测',(58,0))
    d.text((145,225),'上平台 P02',32);d.arrow([(286,270),(380,210)],INK,3)
    d.text((155,345),'底板 P01',32);d.arrow([(270,389),(370,453)],INK,3)
    d.text((755,252),'60 mm 柱 + 两层板',34,BLUE)
    d.text((795,320),'Ø65 轮：轴心离地约 32.5',32)
    d.arrow([(930,364),(690,499)],INK,3)
    d.text((1000,150),'刚性垫块厚度 = Hb − Hc',32,ORANGE)
    d.arrow([(1320,193),(1330,400),(1250,487)],ORANGE,4)
    d.text((780,686),'先在平桌上轻压四角：不能晃，驱动轮不能悬空。',32,GREEN)
    d.footer('Hc 是万向球组件总安装高度，不能用球直径替代。若 Hb 改变，整机所有 Z 参考值一起调整。')
    save(d,'mech02_wheel_level','M14','测万向球总高度，再配刚性垫块；以驱动轮接地可靠、车体不摇晃为准。','两驱轮和前万向球的侧视图，标出5毫米底板、60毫米立柱、参考45毫米底板离地高度，以及万向球总高与刚性垫块。')

def fig_shell():
    d=Diagram('3 mm PVC 桶壳：五片关系与外角码','固定壳外包络 160×150×180 mm；前后壁夹在两块侧壁之间，壳底由上平台直接承托')
    d.text((75,155),'下料：四壁 + 一底',36,BLUE,True)
    d.rect((65,270,260,555),PVC);d.rect((95,240,290,525),PVC)
    d.text((65,590),'侧壁 ×2\n160×180×3',32)
    d.rect((340,290,515,575),'#EAF2F7');d.rect((370,260,545,545),'#EAF2F7')
    d.text((335,610),'前后壁 ×2\n144×180×3',32)
    d.rect((595,320,820,530),'#BAD5E6')
    d.text((585,560),'壳底 ×1\n154×144×3',32)
    d.arrow([(870,430),(1040,430)],BLUE,7,20)
    # Isometric assembly; front face is shown pale so the seated bottom is visible.
    a=(1110,335);b=(1430,245);c=(1640,360);e=(1320,450)
    h=220
    poly(d,[a,b,(b[0],b[1]+h),(a[0],a[1]+h)],'#AFCADC')
    poly(d,[b,c,(c[0],c[1]+h),(b[0],b[1]+h)],'#C5DCEA')
    poly(d,[(a[0],a[1]+h),(b[0],b[1]+h),(c[0],c[1]+h),(e[0],e[1]+h)],'#C9DFEC')
    poly(d,[a,e,(e[0],e[1]+h),(a[0],a[1]+h)],'#E9F2F7')
    poly(d,[e,c,(c[0],c[1]+h),(e[0],e[1]+h)],'#DCEAF3')
    d.line([a,b,c,e,a],INK,5)
    # Small external angle plates at front corner, never full-height internal timber.
    for yy in [495,590]:
        poly(d,[(1292,yy-12),(1320,yy),(1352,yy-9),(1352,yy+20),(1320,yy+30),(1292,yy+15)],'#E7C38D',ORANGE,3)
        d.circle((1307,yy+8),5,INK);d.circle((1336,yy+7),5,INK)
    d.text((1115,165),'口内不要加全高角木',32,RED,True)
    d.arrow([(1270,208),(1300,342)],RED,4)
    d.text((1495,475),'外角码',32,ORANGE)
    d.arrow([(1505,525),(1354,597)],ORANGE,4)
    d.text((1035,700),'壳底落在 P02 上；角码也固定在外侧。',32)
    d.footer('先用胶带无胶试拼，再描孔。内部螺钉端不能钩袋；按装袋内胆的实际外包络检查取出通道。')
    save(d,'mech03_pvc_shell','M27','前后壁夹入侧壁，外侧短角码固定；壳底平铺平台，不在底下再塞木条。','五片PVC桶壳下料示意和三维拼装图，侧壁160×180两片、前后144×180两片、底154×144一片，外角码不侵占内胆路径。')

def fig_liner():
    d=Diagram('PP 内胆：扎带在外、袋底承托、整胆能提出来','五片 1 mm PP；实物装袋后再量最大外包络，包含折边和扎带锁头')
    d.text((65,150),'① 接缝孔与扎带',36,BLUE,True)
    d.text((630,150),'② 袋口向外折',36,BLUE,True)
    d.text((1220,150),'③ 取出净空',36,BLUE,True)
    # Corner unfolded local detail.
    d.rect((70,290,285,615),PP);d.rect((305,290,520,615),'#E6F3E9')
    dashed(d,(295,285),(295,625),MUTED)
    for yy in [390,520]:
        d.circle((260,yy),11,'white',INK,3);d.circle((330,yy),11,'white',INK,3)
        d.line([(260,yy),(260,yy-22),(330,yy-22),(330,yy)],GREEN,10)
        d.rect((307,yy-36,342,yy-13),GREEN,INK,2)
    d.text((70,217),'拆开板片后垫木钻孔',32)
    d.dim((260,660),(285,660),'孔中心距边 ≥5',(0,40))
    d.text((85,630),'约 Ø3',32);d.arrow([(210,634),(260,534)],INK,3)
    # Cross-section of one wall and bag folded externally.
    d.rect((835,300,857,655),PP)
    d.line([(730,650),(820,650),(820,310),(830,285),(866,285),(877,310),(877,400)],BLUE,9)
    d.text((645,235),'内侧',32);d.text((920,235),'外侧',32)
    d.arrow([(765,270),(812,310)],BLUE,4)
    d.dim((943,292),(943,400),'10～15',(65,0))
    d.text((642,445),'PE 袋贴壁\n袋底落在\n内胆底部',32,BLUE)
    d.arrow([(780,597),(803,640)],BLUE,4)
    d.rect((860,500,892,532),GREEN,INK,2)
    d.text((905,570),'扎带头朝外',32,GREEN)
    d.arrow([(1030,563),(890,524)],GREEN,3)
    # Cross-section of shell and liner; arrow shows complete lift path.
    d.rect((1200,300,1222,645),PVC);d.rect((1670,300,1692,645),PVC)
    d.rect((1270,363,1622,635),PP);d.rect((1292,363,1600,615),'white',PP,2)
    d.line([(1280,610),(1280,353),(1256,340),(1256,390)],BLUE,8)
    d.line([(1612,610),(1612,353),(1637,340),(1637,390)],BLUE,8)
    d.rect((1640,465,1655,484),GREEN,INK,2)
    d.arrow([(1447,600),(1447,265)],GREEN,8,23)
    d.dim((1222,687),(1256,687),'≥2',(0,33))
    d.dim((1655,687),(1670,687),'≥2',(0,33))
    d.text((1205,213),'先摘外凸袋夹，再整胆上提',32)
    d.footer('两方向、全高度都要留每侧至少约 2 mm。图中净空放大；“154×144”只是名义内口，不能代替实测。')
    save(d,'mech04_pp_ties_bag_clearance','M35','扎带孔中心距边至少 5 mm；装袋后试提整胆，折边和锁头均计入净空。','三个局部图显示PP板接缝两侧约3毫米孔、向外的扎带锁头、PE袋外折10到15毫米及整胆提取至少每侧2毫米净空。')

def fig_weight():
    d=Diagram('称重时要算哪些：整套“随盖运动的零件”','新盖 160×150×2 mm PVC 发泡板；整套目标 ≤40 g，本设计上限 45 g')
    d.text((70,155),'放到秤上：盖 + 随盖零件',38,BLUE,True)
    # Scale and tray.
    d.rect((90,574,810,625),STEEL,INK,4,12)
    poly(d,[(150,625),(750,625),(805,712),(95,712)],'#D9E1E6')
    d.rect((285,640,620,698),'#E7F1D9',INK,3,7);d.center((285,640,620,698),'实测  ____ g',36,GREEN,True)
    # Lid and attached arm on weighing tray.
    poly(d,[(120,393),(565,270),(762,365),(317,488)],PVC,INK,4)
    poly(d,[(317,488),(762,365),(762,378),(317,501)],'#ABC6D8')
    d.line([(290,400),(360,325)],ORANGE,15);d.circle((360,325),12,'white',INK,3)
    for pt in [(235,369),(310,346)]:
        d.circle(pt,10,STEEL,INK,2)
    d.rect((454,409,521,451),'#C9A77A',INK,2)
    d.text((65,215),'盖板、侧臂、加强片、螺钉、胶带',32)
    d.text((80,510),'活动铰链半片也计入；不能分开时整只计入。',32)
    # Fixed assembly identified outside scale.
    d.line([(945,185),(945,715)],GREY,4)
    d.text((1010,155),'固定在桶体：不随盖称量',38,GREEN,True)
    d.rect((1080,405,1135,676),WOOD)
    d.rect((1020,334,1222,420),'#67A3D4',INK,4,10)
    d.rect((1080,310,1160,337),STEEL)
    d.circle((1120,310),16,STEEL,INK,3)
    d.line([(1215,410),(1260,450),(1260,645)],'#703D35',5)
    d.rect((1310,295,1685,327),PVC)
    d.rect((1390,330,1580,392),'#285A8A',INK,3)
    d.circle((1430,390),24,STEEL,INK,3);d.circle((1540,390),24,STEEL,INK,3)
    d.text((1000,230),'舵机本体与立架',32)
    d.arrow([(1110,277),(1110,332)],INK,3)
    d.text((1300,435),'固定传感器横梁',32)
    d.arrow([(1480,429),(1550,320)],INK,3)
    d.text((1290,540),'固定压条、桶壳\n不要为了减秤数\n移到盖上再不计重量。',32,RED)
    d.footer('拉杆质量不能完全分摊时可全部计入。质量达标后仍需做 20 次开闭与发热、卡滞检查。')
    save(d,'mech05_lid_weight','M45','把所有随盖运动的小零件一起称量，记录实测质量，再做开闭循环检查。','左侧电子秤上放置盖板和其活动附件；右侧独立显示固定舵机、立架及传感器横梁，强调40克目标和45克上限。')

def fig_linkage():
    d=Diagram('连杆先认尺寸，再装球头；维护只拆连接端，不旋短拉杆','两摇臂孔心半径各 20 mm；拉杆两孔中心距 50 mm；两固定轴中心距 50 mm')
    d.text((60,150),'闭合：盖水平，两臂前上方 20°',34,BLUE,True)
    O2=(200,470);O1=(650,470);r=180;angle=math.radians(20)
    A=(O2[0]+r*math.cos(angle),O2[1]-r*math.sin(angle));B=(O1[0]+r*math.cos(angle),O1[1]-r*math.sin(angle))
    d.rect((155,470,245,580),'#67A3D4',INK,3,8)
    d.line([O1,(900,470)],INK,9)
    d.line([O2,A],ORANGE,12);d.line([O1,B],ORANGE,12);d.line([A,B],GREEN,12)
    for p in [O2,O1,A,B]:d.circle(p,12,'white',INK,3)
    dashed(d,O2,O1)
    d.text((290,495),'20',33,ORANGE,True);d.text((756,497),'20',33,ORANGE,True)
    d.dim((A[0],355),(B[0],355),'孔心距 50',(0,-30))
    d.dim((O2[0],630),(O1[0],630),'固定轴距 50',(0,36))
    d.text((110,595),'舵机轴',32);d.text((620,580),'盖铰链轴',32)
    # Raised arm and lid in small inset within same schematic.
    dashed(d,O1,(650,275),BLUE,4)
    dashed(d,O1,(727,260),BLUE,4)
    d.text((670,212),'开启后：臂约 90°',32,BLUE)
    d.text((725,272),'盖开约 70°',32,BLUE)
    d.text((65,708),'示意不按比例；连杆运动平面在桶外。',30,MUTED)
    d.line([(955,150),(955,735)],GREY,3)
    d.text((1000,150),'球头连接的剖面顺序',36,GREEN,True)
    xx=1280
    screw(d,xx,252,600)
    washer(d,xx,332,94)
    d.rect((1230,365,1330,411),GREEN,INK,3,15)
    d.circle((xx,388),25,STEEL,INK,3)
    d.rect((1330,378,1640,399),GREEN,INK,3)
    d.rect((1252,445,1308,470),STEEL,INK,3)
    d.rect((1140,503,1410,525),ORANGE,INK,3)
    washer(d,xx,562,94)
    poly(d,[(1250,592),(1310,592),(1320,617),(1310,642),(1250,642),(1240,617)],STEEL)
    d.circle((xx,617),15,'white',INK,3)
    d.text((1030,221),'M2 螺钉',32);d.arrow([(1200,261),(1255,252)],INK,3)
    d.text((1430,321),'球头可自由摆动',32);d.arrow([(1450,366),(1320,391)],INK,3)
    d.text((1000,425),'按实物加隔套',32);d.arrow([(1160,461),(1250,456)],INK,3)
    d.text((1435,488),'摇臂孔',32);d.arrow([(1475,535),(1408,516)],INK,3)
    d.text((1420,592),'平垫 + 防松螺母',32);d.arrow([(1470,638),(1320,617)],INK,3)
    d.text((1020,692),'不能夹死球头；断电后可卸这一端。',32,RED)
    d.footer('图中螺钉、垫片、隔套为分解示意。实际长度按叠厚试配；SG90 舵盘中心仍用原配螺钉。')
    save(d,'mech06_linkage_joint','M52','先量两孔中心距，再装连接端；球头应可摆动，维护拆端头连接螺钉即可。','左侧识别20毫米摇臂、50毫米杆距及固定轴距；右侧展示M2螺钉、平垫、球头、隔套、摇臂和防松螺母的装配剖面。')

def fig_sensors():
    d=Diagram('传感器要对准哪里：桶体侧剖面高度链','参考 Z 从地面起算；本图按上平台面 Z=115 mm 展示，实际口沿、袋边和探头面重新测量')
    z=lambda zz:900-2.2*zz
    left,right=520,1120
    # Platform and fixed shell.
    d.rect((465,z(115),1180,z(110)),WOOD)
    d.rect((left,z(295),left+15,z(115)),PVC);d.rect((right-15,z(295),right,z(115)),PVC)
    d.rect((left+15,z(118),right-15,z(115)),PVC)
    # Liner floor and walls, PE bag blue.
    ll,rr=570,1070
    d.rect((ll,z(241),ll+10,z(120)),PP);d.rect((rr-10,z(241),rr,z(120)),PP)
    d.rect((ll,z(121),rr,z(120)),PP)
    d.line([(ll+18,z(122)),(ll+18,z(242)),(ll-7,z(246)),(ll-7,z(228))],BLUE,5)
    d.line([(rr-18,z(122)),(rr-18,z(242)),(rr+7,z(246)),(rr+7,z(228))],BLUE,5)
    # Ultrasound bridge and downward module.
    d.rect((left-10,z(291),right+10,z(285)),PVC)
    d.rect((690,z(285),850,z(280)),'#367BAC',INK,3)
    d.circle((725,z(280)),18,STEEL,INK,3);d.circle((815,z(280)),18,STEEL,INK,3)
    d.arrow([(770,z(277)),(770,z(140))],BLUE,5)
    dashed(d,(710,z(277)),(640,z(130)),BLUE,2)
    dashed(d,(830,z(277)),(950,z(130)),BLUE,2)
    # deposit opposed beam on walls.
    d.rect((left-27,z(270),left+5,z(260)),INK)
    d.rect((right-5,z(270),right+27,z(260)),INK)
    dashed(d,(left+10,z(265)),(right-10,z(265)),RED,5,16)
    d.text((70,204),'盖及铰链在上方',32);d.arrow([(300,244),(510,z(295))],INK,3)
    d.text((68,305),'红色：投放对射\n只检测物体经过',32,RED)
    d.arrow([(365,337),(490,z(265))],RED,3)
    d.text((67,465),'蓝色：超声向下测距\n不能用袋边遮住声路',32,BLUE)
    d.arrow([(370,522),(684,z(188))],BLUE,3)
    d.text((70,629),'PP 底 + EVA + 壳底\n均由上平台承托',32)
    for zz,txt,yy,col in [(280,'探头面 Z≈280',232,BLUE),(265,'对射 Z≈265',300,RED),(241,'PP 口沿 Z≈241',379,GREEN),(120,'PP 外底 Z≈120',578,GREEN)]:
        p=(right+30,z(zz));d.line([(right,p[1]),p],col,3)
        d.line([p,(1240,p[1]),(1270,yy+21)],col,3)
        d.text((1290,yy),txt,33,col,True)
    d.text((1260,465),'袋边降低有效口沿\n满桶阈值按实物重算',32,RED)
    d.text((1280,649),'图中均为名义高度',32,MUTED)
    d.footer('候选满桶距离约 60～65 mm、清除约 80～85 mm，只供起调；袋折边变化后重新验证，不沿用旧 45/65。')
    save(d,'mech07_sensor_height','M57','超声向下、对射横穿桶口；装上内胆与袋后，实测有效口沿并重标定满桶距离。','桶体剖面显示上平台115、PP外底120、口沿241、投放对射265和超声探头面280毫米的参考高度，以及袋边避开检测路径。')

def mini_bucket(d,x,y,w=260,h=250,lid_angle=0,basket=False):
    # Hinge at back left; lid opens toward the rear.
    d.rect((x,y,x+w,y+h),PVC,INK,3)
    d.rect((x+17,y+18,x+w-17,y+h-17),'white',None)
    if basket:
        d.rect((x+42,y+85,x+w-42,y+h-28),PP,INK,3)
        d.rect((x+55,y+85,x+w-55,y+h-45),'white',PP,2)
    L=w;end=(x+L*math.cos(math.radians(lid_angle)),y-L*math.sin(math.radians(lid_angle)))
    d.line([(x,y),end],BLUE,8);d.circle((x,y),8,ORANGE,INK,2)
    return (x,y),end

def fig_maintenance():
    d=Diagram('维护取袋必须按顺序：先隔离电源，再解除机械遮挡','普通 70° 开盖只供投放；以下动作均在车轮停止、执行器断电后进行')
    cuts=[40,480,920,1360]
    for i,x in enumerate(cuts):
        if i:d.line([(x-20,150),(x-20,737)],GREY,3)
        d.number((x+28,180),i+1)
    d.text((cuts[0]+70,153),'停机并断电',34,BLUE,True)
    d.text((cuts[1]+70,153),'拆一端拉杆',34,BLUE,True)
    d.text((cuts[2]+70,153),'撑开约 120°',34,BLUE,True)
    d.text((cuts[3]+70,153),'移横梁取内胆',34,BLUE,True)
    x=cuts[0]
    d.text((x+88,260),'2S 电池包',32)
    d.rect((x+50,315,x+330,458),'#E1E5E7',INK,4,12)
    for yy in [342,398]:
        d.rect((x+70,yy,x+255,yy+32),'#7199AF',INK,2,14)
        d.rect((x+255,yy+8,x+270,yy+24),STEEL,INK,2)
    d.line([(x+80,458),(x+80,500),(x+160,500)],RED,7)
    d.rect((x+160,480,x+205,520),'#E9B942',INK,3,5)
    d.rect((x+255,480,x+300,520),'#E9B942',INK,3,5)
    d.line([(x+300,500),(x+350,500),(x+350,445)],RED,7)
    d.arrow([(x+208,557),(x+252,557)],RED,5)
    d.text((x+40,604),'按停机流程隔离电源\n不靠软件“停止”\n代替执行器断电',32,RED)
    x=cuts[1]
    d.rect((x+110,440,x+330,465),ORANGE,INK,3)
    d.rect((x+30,392,x+230,410),GREEN,INK,3)
    d.circle((x+230,401),28,GREEN,INK,3);d.circle((x+230,401),15,STEEL,INK,3)
    screw(d,x+230,280,365)
    d.arrow([(x+270,385),(x+270,285)],BLUE,5)
    d.text((x+34,514),'拆连接螺钉，托住盖',32)
    d.text((x+30,613),'不旋转球头调节螺纹\n杆长保持已标定数值',32,RED)
    x=cuts[2]
    pivot,end=mini_bucket(d,x+180,435,190,150,120)
    d.line([(x+180,585),(x+113,480),(x+130,349)],ORANGE,9)
    d.text((x+32,225),'手动开盖并可靠支撑',32)
    d.text((x+30,614),'用固定支撑或限位绳\n不让盖自由落下',32,RED)
    x=cuts[3]
    mini_bucket(d,x+90,465,220,130,120)
    dashed(d,(x+65,438),(x+345,438),'#8C7BB1',4,12)
    poly(d,[(x+309,344),(x+381,274),(x+392,285),(x+320,355)],'#8C7BB1',INK,3)
    d.arrow([(x+300,415),(x+350,350)],'#6C5796',5)
    d.rect((x+115,315,x+285,456),PP,INK,3)
    d.rect((x+129,315,x+271,439),'white',PP,2)
    d.arrow([(x+200,413),(x+200,235)],GREEN,6)
    d.text((x+26,614),'拔有标识的横梁接头\n摘袋夹，垂直提胆',32,GREEN)
    d.footer('取袋后逆序恢复：装回横梁和连杆，接回插头，确认盖闭合与传感器正常，再退出维护状态。')
    save(d,'mech08_maintenance_four_steps','M76','断电、拆杆、支撑盖、移横梁，再提内胆；清理后逆序恢复并检查互锁。','四格维护示意依次为隔离电池执行电源、拆一端球头连接螺钉、手动撑开盖约120度、移走超声横梁并垂直提内胆。')

if __name__=='__main__':
    fig_standoffs();fig_wheels();fig_shell();fig_liner();fig_weight();fig_linkage();fig_sensors();fig_maintenance()
    manifest('mechanical',items)
