"""Coordinate sheets and assembly guide from the measured CAD release, not photos."""
from pathlib import Path
import json,csv
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image,ImageDraw,ImageFont

B=Path(__file__).resolve().parents[1];O=B/'wall-panels-20261102'
d=json.loads((O/'checks/design.json').read_text(encoding='utf-8'))
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
rows=[]
def row(part,role,u,v,dia,length=0,angle=0):
 rows.append(dict(part=part,role=role,u=u,v=v,diameter=dia,slot_length=length,angle=angle))
for n,w,side in [('W01_FRONT',144,False),('W02_REAR',144,False),('W03_LEFT',160,True),('W04_RIGHT',160,True)]:
 for x in ([9,w-9] if side else [6,w-6]):
  for y in [22,158]:row(n,'角码',x,y,3.4)
for x in [34,46,98,110]:row('W02_REAR','合页',x,173,2.8)
for x in [6,138]:
 for y in [51,127]:row('W01_FRONT','操作腔长螺栓',x,y,3.4)
for f in d['interface_features']:
 if 'hole_centres_uv'in f:
  for x,y in f['hole_centres_uv']:row(f['wall'],'安装座',x,y,f['diameter'],f['vertical_slot_length'] or 0,90)
 if f.get('function')=='beam optical window':row(f['wall'],'对射光窗',*f['centre_uv'],f['slot_width'],f['slot_length'],90)
row('W01_FRONT','LED光孔',29,167,6)
for x in [6,138]:
 for y in [6,82]:row('PANEL_COVER','盖板固定',x,y,3.4)
for x in [11.25,32.75]:row('PANEL_COVER','OLED',x,72.25,2.8,4.8)
row('PANEL_COVER','编码器套筒',65,62,7.4)
for x in [42,57]:
 for y in [48,76]:row('PANEL_COVER','排针罩',x,y,2.8)
for x in [96,122]:
 row('PANEL_COVER','按键帽',x,63,12.4,16)
 for xx in [x-10,x+10]:row('PANEL_COVER','按键夹座',xx,57,2.8,10,90)
for x in [10,79]:
 for y in [15,40]:row('PANEL_COVER','RFID边夹',x,y,2.8,5)
row('PANEL_COVER','急停',111,26,22.6)
for i,r in enumerate(rows):r['id']=f'H{i+1:02d}'
with (O/'source/interface_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['id','part','role','u','v','diameter','slot_length','angle']);writer.writeheader();writer.writerows(rows)
# Independent centreline void check in real STEP solids. Full slot extents remain CAD-defined.
checks=[]
for n in sorted(set(r['part'] for r in rows)):
 s=cq.importers.importStep(str(O/'step'/f'{n}.step')).val()
 for r in [r for r in rows if r['part']==n]:
  probe=cq.Solid.makeCylinder(max(.2,r['diameter']/2-.18),75,cq.Vector(r['u'],r['v'],-1))
  volume=s.intersect(probe).Volume();assert volume<1e-4,(r,volume)
  checks.append(dict(id=r['id'],centreline_void=True))
(O/'checks/hole_positions.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
titles={'W01_FRONT':'前壁','W02_REAR':'后壁','W03_LEFT':'左壁 非舵机侧','W04_RIGHT':'右壁 舵机侧','PANEL_COVER':'可拆操作面板'}
with PdfPages(O/'interface_coordinates.pdf') as pdf:
 for n,title in titles.items():
  w=160 if n in ['W03_LEFT','W04_RIGHT'] else 144;h=88 if n=='PANEL_COVER' else 180
  rr=[r for r in rows if r['part']==n]
  fig=plt.figure(figsize=(11.69,8.27));ax=fig.add_axes([.05,.17,.48,.70]);ax.add_patch(Rectangle((0,0),w,h,fill=False,lw=1.3))
  for r in rr:
   x,y,di,le=r['u'],r['v'],r['diameter'],r['slot_length']
   if le:
    ww,hh=(di,le) if r['angle']==90 else (le,di)
    ax.add_patch(Rectangle((x-ww/2,y-hh/2),ww,hh,fill=False,color='#29627b'))
   else:ax.add_patch(Circle((x,y),di/2,fill=False,color='#29627b'))
   ax.annotate(r['id'],(x,y),(3,3),textcoords='offset points',fontsize=6.5)
  if n=='PANEL_COVER':
   for x,y,ww,hh,label in [(9.5,54.5,25,15,'玻璃窗'),(45,50,10,24,'排针窗'),(13,8,62,40,'1.2mm膜')]:
    ax.add_patch(Rectangle((x,y),ww,hh,fill=False,ls='--',color='#ba6c2a'));ax.text(x+ww/2,y+hh/2,label,ha='center',fontsize=7)
  ax.set(xlim=(-8,w+12),ylim=(-8,h+12),xlabel='u / mm',ylabel='v / mm');ax.set_aspect('equal');ax.grid(alpha=.15)
  a=fig.add_axes([.57,.15,.41,.74]);a.axis('off')
  cells=[[r['id'],f"{r['u']:g}, {r['v']:g}",f"{r['diameter']:g}"+(f"×{r['slot_length']:g}" if r['slot_length'] else ''),r['role']] for r in rr]
  table=a.table(cellText=cells,colLabels=['孔号','中心 u,v','孔径/槽宽×长','用途'],loc='upper center',cellLoc='center',colWidths=[.13,.25,.26,.36]);table.auto_set_font_size(False);table.set_fontsize(7.5);table.scale(1,1.35)
  fig.suptitle(title+' 安装孔坐标与窗口',fontsize=16,y=.96)
  note='壁板按模型外侧视图；面板按模型背面视图。原点为对应零件左下角；槽端为半圆，图中矩形仅示范围。'
  fig.text(.05,.085,note,fontsize=9)
  if n in ['W03_LEFT','W04_RIGHT']:fig.text(.05,.045,'底脚：u=40、120，外伸z=10处各Ø3.4，轴线沿v；孔不在本正视图平面。',fontsize=9)
  elif n=='PANEL_COVER':fig.text(.05,.045,'矩形窗：玻璃左下(9.5,54.5)，25×15；排针左下(45,50)，10×24；刷卡膜左下(13,8)，62×40。',fontsize=8.5)
  elif n=='W01_FRONT':fig.text(.05,.045,'操作腔：u0–144，v45–133，外深60；下方过线口u59–85、外伸z12–24，穿过腔下壁。',fontsize=9)
  pdf.savefig(fig);fig.savefig(O/'preview'/f'coordinates_{n}.png',dpi=160);plt.close(fig)

# Labeled guide kept separate from the engineering-coordinate pages.
font=lambda s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s)
canvas=Image.new('RGB',(1700,1800),'white');draw=ImageDraw.Draw(canvas)
draw.text((55,28),'四块筒壁及外置元件安装座',font=font(40),fill='#183f50')
im=Image.open(O/'preview/complete_assembly_front.png');im.thumbnail((1600,1120));canvas.paste(im,((1700-im.width)//2,85))
texts=[
 '前方：OLED、编码器、两按键、RC522、急停装在可拆面板。',
 '前壁上方：开盖红外托架、向内照明LED、闭盖微动开关调节板。',
 '非舵机侧：DHT11裸探头通风座、光敏夹座、电源开关盒、线夹。',
 '左右上部：投放对射同轴窗口，光轴距桶口30mm；接线朝外。',
 '桶内后上方：固定超声横梁；探头向下，横梁可拆，不随盖转动。',
 '桶内不套袋、不加内胆；原上平台连续面朝上作底面，不具防水密封。',
 '图中未装电子件、螺钉及活动盖；配合、开盖行程和传感效果需实物试装。']
for i,t in enumerate(texts):draw.text((55,1190+i*72),t,font=font(28),fill='#263d47')
canvas.save(O/'preview/installation.png')
print('Coordinate checks:',len(checks),'PDF pages:',len(titles))
