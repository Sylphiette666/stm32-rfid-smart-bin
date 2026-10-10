from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import math,json
R=Path(__file__).parent;F='C:/Windows/Fonts/msyh.ttc'
INK='#1f2933';BLUE='#285b75';GRAY='#637581';RED='#a33a32';GREEN='#267356'
def start(title,h=1450):
 im=Image.new('RGB',(2200,h),'white');d=ImageDraw.Draw(im);txt(d,(60,35),title,44);return im,d
def txt(d,xy,s,size=29,fill=INK):d.multiline_text(xy,s,font=ImageFont.truetype(F,size),fill=fill,spacing=12)
def ln(d,a,b,color=INK,w=4):d.line([a,b],fill=color,width=w)
def ar(d,a,b,color=BLUE,w=5):
 ln(d,a,b,color,w);theta=math.atan2(b[1]-a[1],b[0]-a[0]);L=18
 for k in [-.45,.45]:ln(d,b,(b[0]-L*math.cos(theta+k),b[1]-L*math.sin(theta+k)),color,w)
def rect(d,r,t,size=29):
 d.rectangle(r,outline=BLUE,width=3);txt(d,(r[0]+20,r[1]+20),t,size)
def dim(d,a,b,label):
 ln(d,a,b,GRAY,2)
 if a[1]==b[1]:
  for x,y in [a,b]:ln(d,(x,y-12),(x,y+12),GRAY,2)
  txt(d,((a[0]+b[0])/2-len(label)*9,a[1]-50),label,27,GRAY)
 else:
  for x,y in [a,b]:ln(d,(x-12,y),(x+12,y),GRAY,2)
  txt(d,(a[0]+18,(a[1]+b[1])/2-25),label,27,GRAY)

im,d=start('五片式PP内胆下料与连接  单位mm',1540)
rect(d,(110,180,670,700),'底板  140 × 130\n1 mm PP  1片',34)
rect(d,(850,180,1410,660),'前后板  140 × 120\n1 mm PP  共2片',34)
rect(d,(1590,180,2102,660),'左右板  128 × 120\n1 mm PP  共2片',34)
dim(d,(110,770),(670,770),'140');dim(d,(60,180),(60,700),'130')
txt(d,(780,760),'侧板立在底板上；左右板夹在前后板之间。\n外包络约140 × 130 × 121，孔位先试装再标记。',32)
# corner schematic
rect(d,(120,915,750,1370),'',28)
ln(d,(120,1060),(750,1060),BLUE,8);ln(d,(280,915),(280,1370),BLUE,8)
for x,y in [(240,1110),(325,1020)]:d.ellipse((x-16,y-16,x+16,y+16),outline=INK,width=4)
ln(d,(240,1110),(325,1020),GREEN,8)
txt(d,(390,1150),'配对孔约Ø3\n孔心距边≥5',29)
txt(d,(840,970),'1  五片裁好后去毛刺，直角试拼。\n2  每条接缝先做两处扎带固定。\n3  扎带头朝外，尾端剪平。\n4  底板落在平台上，不悬空吊袋。\n5  30 × 40 cm袋折口，袋边不挡光束。',34)
txt(d,(100,1460),'本图是尺寸示意，不是1比1打印模板；不使用旧0.5 mm折叠展开图。',28,GRAY)
im.save(R/'pp_liner_new.png')

im,d=start('供电分支与信号电压  接线前先测空载输出',1510)
rect(d,(65,180,485,360),'成品保护2S电池\n7.4 V标称  8.4 V满电',29)
rect(d,(610,180,1080,360),'3 A初选保险 → 总开关\nBAT_SW为开关后电池电压',29)
rect(d,(1210,180,1665,360),'降压模块\n输出先调至5.00 V',30)
ar(d,(485,270),(610,270));ar(d,(1080,270),(1210,270))
ln(d,(1665,270),(1950,270),RED,7);ln(d,(1950,270),(1950,1170),RED,7)
rows=[(495,'5V_MOTOR','驱动VM → 左右减速电机','驱动VCC接3V3_EXT',470),(720,'5V_SERVO','SG90红线  棕黑接地','PWM由AHCT125转为5 V',1000),(945,'5V_LOGIC','核心板5V入口  DFPlayer  HC-SR04','核心3V3只供核心及指定接口上拉',100)]
for y,label,a,b,c in rows:
 rect(d,(1080,y-55,1750,y+105),label+'  '+a+'\n'+b,27)
 ar(d,(1950,y+15),(1750,y+15),RED)
 txt(d,(110,y-30),str(c)+' µF / 16 V + 100 nF\n分别就近接在该支路5V与GND之间',29)
rect(d,(1080,1165,1750,1325),'5 V → 外设独立3.3 V稳压\n3V3_EXT → RFID FLASH MCP OLED等',28)
ar(d,(1950,1240),(1750,1240),RED);ln(d,(1950,1170),(1950,1240),RED,7)
txt(d,(110,1190),'全部GND共地，电机与舵机单独回电源分配点。\n核心3V3与3V3_EXT不直接并联。\nUSB串口VCC不接，核心USB口不接。',30)
txt(d,(90,1415),'图中是供电关系，端子物理位置按模块丝印。驱动和舵机电流不通过面包板或细杜邦线。',29,GRAY)
im.save(R/'power_branches.png')

im,d=start('轻型盖平行四边形连杆  闭合与开启位置',1530)
s=13;O2=(270,850);O1=(920,850)
def point(o,a):return(o[0]+20*s*math.cos(math.radians(a)),o[1]-20*s*math.sin(math.radians(a)))
for a,col in [(20,INK),(90,BLUE)]:
 A=point(O2,a);B=point(O1,a)
 ln(d,O2,A,col,7);ln(d,O1,B,col,7);ln(d,A,B,col,7)
 for x,y in [A,B]:d.ellipse((x-12,y-12,x+12,y+12),fill='white',outline=col,width=4)
ln(d,O2,O1,GRAY,3)
for o,label in [(O2,'O2 舵机轴'),(O1,'O1 盖铰链轴')]:
 x,y=o;d.ellipse((x-15,y-15,x+15,y+15),fill=RED);txt(d,(x-75,y+45),label,30)
dim(d,(270,1030),(920,1030),'两固定轴中心距50')
ln(d,O1,(1900,850),INK,7)
end=(O1[0]+610*math.cos(math.radians(70)),O1[1]-610*math.sin(math.radians(70)))
ln(d,O1,end,BLUE,8)
txt(d,(1320,620),'蓝色为开盖70°\n黑色为闭盖\n两摇臂随盖转动70°',33)
txt(d,(75,180),'两个摇臂孔距均20；拉杆两球心距50。\n闭盖时摇臂相对水平线约20°；开盖时约90°。\n从动臂与盖固定，不能让盖直接压在舵机轴上。',32)
ar(d,(820,425),(690,590),BLUE);txt(d,(530,330),'连杆孔心距50\n不是裸金属杆长度',31)
txt(d,(95,1130),'盖板160 × 150 × 2 mm PVC发泡板。\n安装后把盖、随动摇臂及紧固件一起称重：目标≤40 g，上限45 g。\n双球头保持自由摆动，金属杆与盖板错层；全程手动检查无干涉。\n维护时断电、拆一端拉杆、移开测距横梁，并固定住翻开的盖。',32)
txt(d,(90,1450),'本图仅表示侧面运动关系；输出轴及连杆平面需按SG90实物用转接片调齐。',28,GRAY)
im.save(R/'lid_linkage_new.png')

im,d=start('桌面验证与整机装配顺序',1350)
labels=[('01 配件与电压核对','标记型号  识别引脚'),('02 机械无电试装','板件  轮组  盖  内胆'),('03 电源空载验证','降压输出  分压  共地'),('04 核心与总线','SWD  串口  I²C  SPI'),('05 停止与输入','急停  碰撞  对射  测距'),('06 执行器分项','轮子架空  舵机卸杆'),('07 固定桶业务','RFID  事务  开盖积分'),('08 移动与交互','循迹停站  遥控  语音'),('09 合装与验收','收线  异常试验  记录')]
for i,(a,b) in enumerate(labels):
 row=i//3;col=i%3;x=75+col*720;y=180+row*340
 rect(d,(x,y,x+600,y+185),a+'\n'+b,33)
 if col<2:ar(d,(x+600,y+92),(x+720,y+92))
 if col==2 and row<2:
  ln(d,(x+300,y+185),(x+300,y+260),BLUE);ln(d,(x+300,y+260),(375,y+260),BLUE);ar(d,(375,y+260),(375,y+340))
txt(d,(95,1220),'每一步通过后再增加下一项负载；软件按同样顺序逐模块实现，不在整机里一次性排查全部问题。',29,GRAY)
im.save(R/'assembly_sequence.png')
print('4 diagrams complete')
