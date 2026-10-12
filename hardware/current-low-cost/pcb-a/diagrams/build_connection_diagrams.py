"""Editable vector + raster technical diagrams. No PCB geometry or module pin order is inferred."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from html import escape
import json,math,hashlib

OUT=Path(__file__).parent
X=json.loads((OUT.parent/'circuit.json').read_text(encoding='utf-8'))
P={p['ref']:p for p in X['parts']}
assert P['J7']['pins']=={'1':'5V_BUS','2':'GND','3':'3V3_EXT'}
assert P['J10']['pins']=={'1':'3V3_EXT','2':'GND','3':'I2C_SCL','4':'I2C_SDA','5':'MCP_RESET_N'}
assert P['U1']['pins']['9']=='PB9' and P['U1']['pins']['10']=='GND'
assert P['J23']['pins']['4']=='PB11' and P['J23']['pins']['5']=='DHT_DATA_RAW'
assert P['JP8']['pins']=={'1':'PB11','2':'DHT_DATA_RAW'}
INK='#182C39'; GREY='#687884'; LIGHT='#F4F7F9'; LINE='#CAD4DA'
RED='#B8383B'; BLACK='#30373B'; BLUE='#196B9C'; GREEN='#23764D'; PURPLE='#7655A2'; ORANGE='#A96316'
F='C:/Windows/Fonts/msyh.ttc'; FB='C:/Windows/Fonts/msyhbd.ttc'

class D:
 def __init__(self,title,subtitle,H=2180):
  self.W=1800;self.H=H;self.im=Image.new('RGB',(self.W,H),'white');self.dr=ImageDraw.Draw(self.im);self.svg=[];self.text_bounds=[]
  self.rect(0,0,self.W,H,fill='white',outline=None)
  self.text(50,32,title,58,bold=True);self.text(50,116,subtitle,37,color=GREY)
 def font(self,size,bold=False):return ImageFont.truetype(FB if bold else F,size)
 def text(self,x,y,t,size=40,color=INK,bold=False,anchor='left'):
  for n,line in enumerate(str(t).split('\n')):
   yy=y+n*(size+14);fo=self.font(size,bold);b=self.dr.textbbox((0,0),line,font=fo);w=b[2]-b[0]
   xx=x-w/2 if anchor=='center' else x-w if anchor=='right' else x
   self.dr.text((xx,yy),line,font=fo,fill=color)
   ascent=fo.getmetrics()[0]
   self.svg.append(f'<text x="{xx:.1f}" y="{yy+ascent:.1f}" fill="{color}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{escape(line)}</text>')
   self.text_bounds.append([xx,yy+b[1],xx+w,yy+b[3],line])
 def rect(self,x,y,w,h,fill=None,outline=INK,width=3):
  self.dr.rectangle((x,y,x+w,y+h),fill=fill,outline=outline,width=width)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "none"}" stroke="{outline or "none"}" stroke-width="{width}"/>')
 def line(self,pts,color=BLUE,width=5,dash=False):
  self.dr.line(pts,fill=color,width=width,joint='curve')
  q=' '.join(f'{x},{y}' for x,y in pts)
  self.svg.append(f'<polyline points="{q}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="12 8"' if dash else '')+'/>')
 def arrow(self,pts,color=BLUE,width=5,head=18):
  self.line(pts,color,width);x,y=pts[-1];a=math.atan2(y-pts[-2][1],x-pts[-2][0]);pp=[(x,y),(x-head*math.cos(a-.45),y-head*math.sin(a-.45)),(x-head*math.cos(a+.45),y-head*math.sin(a+.45))]
  self.dr.polygon(pp,fill=color);self.svg.append('<polygon points="'+' '.join(f'{u:.2f},{v:.2f}' for u,v in pp)+f'" fill="{color}"/>')
 def dot(self,x,y,color=BLUE,r=7):
  self.dr.ellipse((x-r,y-r,x+r,y+r),fill=color);self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
 def block(self,x,y,w,h,title,lines=(),size=40):
  self.rect(x,y,w,h,LIGHT);self.text(x+w/2,y+17,title,44,bold=True,anchor='center')
  for i,t in enumerate(lines):self.text(x+w/2,y+80+i*(size+13),t,size,anchor='center')
 def resistor_h(self,x,y,w=150,label='10 kΩ',color=BLUE):
  self.line([(x,y),(x+25,y)],color);self.rect(x+25,y-17,w-50,34,'white',color,4);self.line([(x+w-25,y),(x+w,y)],color);self.text(x+w/2,y-83,label,40,anchor='center')
 def resistor_v(self,x,y,h=110,label='10 kΩ',side='right',color=BLUE):
  self.line([(x,y),(x,y+20)],color);self.rect(x-17,y+20,34,h-40,'white',color,4);self.line([(x,y+h-20),(x,y+h)],color)
  self.text(x+38 if side=='right' else x-38,y+h/2-26,label,39,anchor='left' if side=='right' else 'right')
 def gnd(self,x,y):
  self.line([(x,y),(x,y+14)],BLACK,4)
  for i,w in enumerate((44,28,12)):self.line([(x-w/2,y+14+i*9),(x+w/2,y+14+i*9)],BLACK,4)
 def save(self,name):
  bad=[b for b in self.text_bounds if b[0]<0 or b[2]>self.W or b[1]<0 or b[3]>self.H]
  if bad:raise ValueError((name,'text outside',bad))
  self.im.save(OUT/(name+'.png'),dpi=(300,300))
  (OUT/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}" height="{self.H}" viewBox="0 0 {self.W} {self.H}">'+''.join(self.svg)+'</svg>',encoding='utf-8')
  return {'file':name,'width':self.W,'height':self.H,'text_boxes':len(self.text_bounds),'bounds_pass':True}

def power():
 d=D('47｜板外电源与 PCB 三支路','电气连接示意；位置不是板上摆位。红：正电源，黑：共地。')
 d.block(50,210,270,260,'保护电池组',['2S 18650','最高 8.4 V'],40)
 d.rect(410,270,220,80,LIGHT);d.text(520,277,'保险丝',43,anchor='center',bold=True)
 d.text(520,202,'5×20 mm',38,anchor='center');d.text(520,357,'3 A 初选',38,anchor='center')
 d.rect(760,270,290,80,LIGHT);d.text(905,277,'总开关',43,anchor='center',bold=True)
 d.rect(1280,210,450,260,LIGHT);d.text(1505,230,'J1  BAT_SW',45,bold=True,anchor='center')
 d.text(1320,285,'1  VBAT_SW',41,color=RED);d.text(1320,385,'2  GND',41,color=BLACK)
 d.arrow([(320,310),(410,310)],RED,7);d.arrow([(630,310),(760,310)],RED,7);d.arrow([(1050,310),(1280,310)],RED,7)
 d.line([(320,410),(1280,410)],BLACK,7);d.dot(1280,310,RED);d.dot(1280,410,BLACK)
 d.text(820,427,'电池与降压主干：20 AWG',39,anchor='center')
 # J1 and J2 are connected on PCB, not an external replacement wire.
 d.line([(1450,470),(1450,580)],RED,7);d.line([(1550,470),(1550,580)],BLACK,7)
 d.text(1310,505,'PCB 内同网',38,anchor='right',color=GREY)
 d.rect(1280,580,450,280,LIGHT);d.text(1505,600,'J2  BUCK_IN',44,bold=True,anchor='center')
 d.text(1320,648,'1  VBAT_SW',41,color=RED);d.text(1320,748,'2  GND',41,color=BLACK)
 d.rect(560,570,560,360,LIGHT);d.text(840,591,'板外 5 V 降压',44,bold=True,anchor='center')
 for y,c,left,right in ((670,RED,'OUT+','IN+'),(770,BLACK,'OUT−','IN−')):
  d.text(600,y-26,left,39,color=c);d.text(1080,y-26,right,39,color=c,anchor='right')
  d.line([(1280,y),(1120,y)],c,7) if c==BLACK else d.arrow([(1280,y),(1120,y)],c,7)
  d.line([(560,y),(450,y)],c,7) if c==BLACK else d.arrow([(560,y),(450,y)],c,7)
 d.text(840,850,'实测持续 ≥3 A',39,anchor='center')
 d.rect(50,580,400,280,LIGHT);d.text(250,600,'J3  BUCK_OUT',43,bold=True,anchor='center')
 d.text(90,648,'1  +5 V',41,color=RED);d.text(90,748,'2  GND',41,color=BLACK)
 d.text(1280,902,'降压 OUT 不接电池电压',37,color=ORANGE)
 # Two common buses with distinct branch pairs; dots indicate junctions.
 d.line([(170,860),(170,1010),(1390,1010)],RED,8);d.line([(280,860),(280,1060),(1570,1060)],BLACK,8)
 d.text(950,942,'板内星形配电；实点相接，交叉无点不相接',40,anchor='center',color=GREY)
 groups=[(50,'J4  MOTOR','TB6612 电机电源',['VM → +5 V','动力 GND → 地']),(650,'J5  SERVO','SG90 舵机电源',['红线 → +5 V','棕/黑线 → 地']),(1250,'J6  LOGIC','5 V 逻辑分配',['DFPlayer／超声等','另供 J7、J8 的 5 V'])]
 for x,title,load,lines in groups:
  px=x+140;gx=x+320
  d.line([(px,1010),(px,1120)],RED,7);d.dot(px,1010,RED)
  d.line([(gx,1060),(gx,1120)],BLACK,7);d.dot(gx,1060,BLACK)
  d.rect(x,1120,480,160,LIGHT);d.text(x+240,1134,title,43,bold=True,anchor='center')
  d.text(x+65,1210,'1  +5 V',38,color=RED);d.text(x+282,1210,'2  GND',38,color=BLACK)
  d.line([(px,1280),(px,1360)],RED,7);d.line([(gx,1280),(gx,1360)],BLACK,7)
  d.block(x,1360,480,200,load,lines,37)
 d.text(395,1300,'22 AWG',37);d.text(995,1300,'22 AWG',37);d.text(1595,1300,'按负载',36)
 d.line([(50,1585),(1740,1585)],LINE,3)
 d.text(50,1600,'独立 3.3 V：共地；CORE 与 EXT 两路输出不能并联',43,bold=True)
 # External 3.3V regulator triple wire interface.
 d.rect(50,1690,490,360,LIGHT);d.text(295,1703,'J7  EXT_REG',42,bold=True,anchor='center')
 d.rect(770,1690,490,360,LIGHT);d.text(1015,1703,'板外 3.3 V 稳压',42,bold=True,anchor='center')
 rows=[(1800,'1  5V_BUS','IN+ / VIN',RED),(1900,'2  GND','GND',BLACK),(2000,'3  3V3_EXT','OUT 3.3 V',GREEN)]
 for y,lp,rp,c in rows:
  d.text(85,y-25,lp,39,color=c);d.text(810,y-25,rp,39,color=c)
  d.line([(540,y),(770,y)],c,6) if c==BLACK else d.arrow([(540,y),(770,y)] if c!=GREEN else [(770,y),(540,y)],c,6)
 d.rect(1350,1690,400,360,LIGHT);d.text(1550,1703,'J8 与核心板',42,bold=True,anchor='center')
 d.text(1380,1780,'1 → 核心 5V',38,color=RED);d.text(1380,1870,'2 → 核心 GND',38,color=BLACK)
 d.text(1380,1960,'3 ← 核心 3V3',38,color=PURPLE)
 d.text(50,2065,'J7.3 只到 3V3_EXT；J8.3 只到 3V3_CORE。',40,color=PURPLE)
 d.text(50,2125,'动力正负线成对回配电点；不得用杜邦线承载电机、舵机或电池主电流。',37,color=GREY)
 return d.save('47_power')

def modules():
 d=D('48｜核心、MCP 与模块接口总览','每条粗线代表一组独立线束；按针名逐线接，不按商品排针位置直插。',H=2200)
 # The schematic board does not represent physical placement.
 d.rect(590,220,550,1820,'white',BLUE,4);d.text(865,242,'新 PCB 接口',46,bold=True,anchor='center')
 d.text(865,305,'内部按网表连接',36,color=GREY,anchor='center')
 d.block(50,220,410,390,'STM32 核心板',[],40)
 d.text(255,300,'已从教学底板拆下',37,anchor='center')
 d.text(80,375,'PA组＋电源：17 根',37)
 d.text(80,472,'PB组＋共地：16 根',37)
 for y,n in ((410,'J8'),(507,'J9')):
  d.line([(460,y),(590,y)],BLUE,10);d.text(623,y-29,n,42,bold=True)
 d.text(50,640,'SWD：PA13 / PA14 / GND',37)
 d.text(50,694,'整机接线完成后不插核心 USB',37,color=ORANGE)
 # Explicit MCP five plus seven plus seven bundles.
 d.rect(50,800,410,980,LIGHT);d.text(255,824,'MCP23017 模块',42,bold=True,anchor='center')
 d.text(80,911,'VDD / GND / SCL',36);d.text(80,964,'SDA / RESET',36)
 d.line([(460,1000),(590,1000)],GREEN,10);d.text(526,945,'5 根',37,anchor='center',color=GREEN)
 d.text(618,972,'J10',42,bold=True)
 d.text(80,1110,'GPA0—GPA6',40)
 d.text(80,1167,'方向、RST、灯、BUSY',34)
 d.line([(460,1230),(590,1230)],GREEN,10);d.text(526,1175,'7 根',37,anchor='center',color=GREEN)
 d.text(618,1202,'J11',42,bold=True)
 d.text(80,1340,'GPB0—GPB6',40)
 d.text(80,1397,'循迹、靠近、按键',36)
 d.line([(460,1460),(590,1460)],GREEN,10);d.text(526,1405,'7 根',37,anchor='center',color=GREEN)
 d.text(618,1432,'J12',42,bold=True)
 d.text(80,1548,'合计 5＋7＋7＝19 根',38,bold=True)
 d.text(80,1615,'A0/A1/A2：模块侧接地',34)
 d.text(80,1671,'GPA7/GPB7 留空',37);d.text(80,1722,'软件设输出 0',37)
 d.text(50,1840,'3V3_EXT 供 MCP 与外设',36,color=GREEN)
 d.text(50,1900,'3V3_CORE 只作规定参考',36,color=PURPLE)
 d.text(50,1960,'两路 3.3 V 不并接',39,color=PURPLE,bold=True)
 # Module groups. The J mapping is comprehensive; exact pins are in the accompanying table.
 data=[
 (220,185,'I²C 外设',['J13  OLED','J14  MPU6050（JP5 选供电）'],'I²C',BLUE),
 (445,195,'SPI 外设',['J15  RC522：PA4 片选','J16  FLASH：PA15 片选'],'SPI',BLUE),
 (680,190,'串口',['J17  HC05（JP6 选供电）','J18  USB 串口：TX/RX 交叉'],'UART',BLUE),
 (910,190,'动力控制信号',['J19  TB6612（主电源 J4）','J20  SG90（主电源 J5）'],'PWM',BLUE),
 (1140,190,'超声与温湿度',['J21  HC-SR04','J22  DHT；J23 条件电平转换'],'传感',BLUE),
 (1370,215,'旋钮与安全接点',['J24 编码器；J25 按键/闭盖','J26 碰撞；J27 双 NC 急停'],'接点',BLUE),
 (1625,210,'照明与提示',['J28 MOS转接；J29 LED','J30 蜂鸣；J31 DFPlayer信号'],'输出',BLUE),
 (1875,170,'光敏与红外输入',['J32 光敏；J33 六路红外','5 V 数字输出先适配 → 图49'],'输入',ORANGE)]
 for y,h,title,lines,short,c in data:
  d.block(1220,y,530,h,title,lines,35)
  yy=y+h/2;d.line([(1140,yy),(1220,yy)],c,8)
  d.text(1095,yy-29,short,37,color=c,anchor='right')
 d.text(865,608,'SCK / MISO / MOSI 共享',35,color=GREY,anchor='center')
 d.text(50,2095,'AO3400A 是裸管：先焊转接板，核对 G/S/D，再接 J28。',40,color=ORANGE)
 d.text(50,2150,'所有模块的供电、接口针号、DNP 和跳帽状态，以本章逐针表为准。',37,color=GREY)
 return d.save('48_modules')

def conditions():
 d=D('49｜外置条件适配与选择跳帽','只对实物需要的分支施工；5 V 数据不能凭接口名字直接接 MCU。',H=2200)
 d.text(50,207,'A｜单路 5 V DO → 3.3 V 输入：外置 NPN 适配，会反相',43,bold=True)
 d.text(90,338,'模块 DO',42,color=ORANGE)
 d.text(90,394,'0 / 5 V',39,color=ORANGE)
 d.line([(300,430),(460,430)],ORANGE,6);d.resistor_h(460,430,190,'10 kΩ',ORANGE)
 d.line([(650,430),(820,430)],BLUE,5);d.dot(735,430)
 # NPN logical schematic: emitter at bottom, collector at top. Not a package pin drawing.
 d.line([(820,355),(820,505)],BLACK,7)
 d.line([(820,390),(965,305),(965,280)],BLACK,5)
 d.line([(820,472),(965,560),(965,600)],BLACK,5)
 d.arrow([(879,509),(949,550)],BLACK,5,18)
 d.text(858,353,'C',37);d.text(778,387,'B',37,anchor='right');d.text(987,550,'E',37)
 d.line([(965,280),(1510,280)],BLUE,6)
 d.text(1510,318,'接对应一路输入',39,anchor='right',color=BLUE)
 d.text(1510,372,'J33.4—9 / J31.3 BUSY',37,anchor='right',color=BLUE)

 # Supply pullup placed below header at right, routed up to output node.
 d.resistor_v(1620,333,135,'',side='left',color=GREEN)
 d.text(1575,482,'10 kΩ',39,anchor='right',color=GREEN)
 d.line([(1510,280),(1620,280),(1620,333)],BLUE,5)
 d.line([(1620,468),(1620,545)],GREEN,5);d.dot(1620,545,GREEN)
 d.text(1620,585,'3V3_EXT',39,color=GREEN,anchor='center')
 d.line([(735,430),(735,475)],BLUE,5);d.resistor_v(735,475,120,'100 kΩ',side='left')
 d.gnd(735,595);d.gnd(965,600)
 d.text(1020,461,'2N3904',39,bold=True)
 d.text(90,661,'每个 DO 单独适配；DO 高→C低，DO 低→C高。脚序按实物核对。',38,color=GREY)
 d.line([(50,742),(1750,742)],LINE,3)
 d.text(50,771,'B｜DHT 必须 5 V 时：外置 BSS138 双向开漏转换',43,bold=True)
 d.text(50,838,'JP7＝2–3；JP8 保持开路。DHT 本体仍接 J22。',39,color=ORANGE)
 d.rect(70,924,520,460,LIGHT);d.text(330,942,'PCB  J23',44,bold=True,anchor='center')
 d.rect(1130,924,600,460,LIGHT);d.text(1430,942,'外置 BSS138 成品模块',42,bold=True,anchor='center')
 rows=[(1040,'1  3V3_EXT','LV',GREEN),(1110,'2  5V_BUS','HV',RED),(1180,'3  GND','GND',BLACK),(1250,'4  PB11','LV1',BLUE),(1320,'5  DHT_DATA_RAW','HV1',BLUE)]
 for y,l,r,c in rows:
  d.text(110,y-28,l,37,color=c);d.text(1170,y-28,r,39,color=c)
  d.line([(590,y),(1130,y)],c,5)
  if r in ('LV1','HV1'):
   d.arrow([(790,y),(880,y)],c,4,13);d.arrow([(880,y),(790,y)],c,4,13)
 d.text(50,1417,'J23.5 与 J22.3 是同一 DATA 网；不短接 JP8 绕过转换器。',39,color=GREY)
 d.text(50,1480,'若实物支持 3.3 V：JP7＝1–2、JP8 闭合，不接此转换模块。',39,color=GREEN)
 d.line([(50,1562),(1750,1562)],LINE,3)
 d.text(50,1590,'C｜蜂鸣器：控制电平与模块供电分开选择',43,bold=True)
 d.text(450,1670,'JP3 选 1–2：3.3 V 控制',39,anchor='center',color=BLUE)
 d.text(1320,1670,'JP3 选 2–3：5 V 控制',39,anchor='center',color=BLUE)
 for cx,pair in ((450,(1,2)),(1320,(2,3))):
  xx=[cx-190,cx,cx+190];y=1775
  d.rect(cx-230,y-34,460,68,LIGHT,LINE,3)
  for i,(xx0,label) in enumerate(zip(xx,('1  PB9','2  IN','3  AHCT')),1):
   d.rect(xx0-15,y-15,30,30,'white',BLUE,4);d.text(xx0,y+35,label,35,anchor='center')
  a=xx[pair[0]-1];b=xx[pair[1]-1]
  d.rect(a-26,y-30,b-a+52,60,None,ORANGE,7)
 d.text(50,1895,'每组只能一只跳帽；JP4 另按模块额定电压选 3.3 V 或 5 V。',39)
 d.text(50,1960,'R36 下拉：高有效；R37 上拉 CORE：低有效。两者只装一只。',39)
 d.text(50,2025,'即使不接蜂鸣，也保留其中一只偏置，避免 AHCT 输入浮空。',39)
 d.text(50,2110,'上述均是条件接线示意；不是商品模块排针顺序，也不替代断电通断检查。',37,color=GREY)
 return d.save('49_conditions')

reports=[power(),modules(),conditions()]
manifest=[]
captions={
'47_power':'图47 板外电源与PCB三支路：保险和总开关在电池正线上；动力采用独立粗线回路，外设与核心的两路3.3V输出不并接。',
'48_modules':'图48 新PCB模块接口总览：核心与模块逐线按信号连接；MCP五根总线/电源/复位加两组七根GPIO，共19根线。',
'49_conditions':'图49 条件适配：5V数字DO使用反相NPN适配；5V DHT使用BSS138且断开JP8；蜂鸣控制与供电、复位偏置分别选择。'}
for r in reports:
 manifest.append({**r,'id':int(r['file'][:2]),'file':str(OUT/(r['file']+'.png')),'svg':str(OUT/(r['file']+'.svg')),'caption':captions[r['file']],'alt':captions[r['file']]})
(OUT/'electrical-diagram-manifest.json').write_text(json.dumps({'circuit_sha256':hashlib.sha256((OUT.parent/'circuit.json').read_bytes()).hexdigest(),'figures':manifest,'qa_status':'bounds checked; awaiting actual image view'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(reports,ensure_ascii=False))
