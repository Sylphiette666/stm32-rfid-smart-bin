from pathlib import Path
import json,csv,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
O=Path(__file__).resolve().parents[1];B=O.parent
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
d=json.loads((B/'mounted-20261031/source/design.json').read_text())
fig,ax=plt.subplots(figsize=(12,9));ax.add_patch(Rectangle((0,0),280,220,fc='#edf3f5',ec='#223c47',lw=2))
rows=[]
for sp in d['modules']:
 n=sp['id']
 if not n.startswith('M'):continue
 x,y=sp['layout_origin'];a=sp['rotation'];l,w,t=sp['board_size']
 if n=='M09':x,y=252,65
 if n=='M08':x,y=253,170;a=90
 if a%180:l,w=w,l
 ax.add_patch(Rectangle((x-l/2,y-w/2),l,w,fc='#c9e1d7',ec='#306854'))
 ax.text(x,y,n,ha='center',va='center',fontsize=10)
 rows.append([n,sp['name'],x,y,a,sp['seat_height']+5])
ax.add_patch(Rectangle((110,60),125,100,fc='#acc9e6',ec='#295d8f',lw=1.5));ax.text(169,110,'B1 PCB\n125×100 mm\n承托面 Z=25',ha='center',va='center',fontsize=11)
for x,y in [(115,65),(205,65),(115,155),(205,155)]:ax.add_patch(Circle((x,y),2,fc='white',ec='#295d8f'))
ax.add_patch(Rectangle((138,10),76,40,fc='#ead5b5',ec='#986b30'));ax.text(176,30,'电池 76×40',ha='center',va='center')
ax.add_patch(Rectangle((181,177),43,21,fc='#c9e1d7',ec='#306854'));ax.text(202.5,187.5,'DC-DC',ha='center',va='center')
ax.add_patch(Circle((256,120),20,fc='#e4dfc6',ec='#87794a'));ax.text(256,120,'喇叭\nØ40',ha='center',va='center',fontsize=10)
for y in [96,144]:ax.plot(256,y,'o',color='#87794a')
for x,y in [(30,25),(250,25),(30,195),(250,195)]:ax.add_patch(Circle((x,y),5,fill=False,ec='#a34949',lw=2))
for y in [14,206]:
 ax.add_patch(Rectangle((82,y-13),28,26,fill=False,ec='#a0682b',linestyle='--'))
 ax.text(96,y,'电机',ha='center',va='center',fontsize=9)
for x,ys in [(240,[90,130]),(185,[80.25,139.75])]:
 for y in ys:ax.plot(x,y,'x',color='#a34949',ms=6)
ax.text(140,230,'红圈：平台立柱　红叉：底面安装孔（详细坐标见表）',ha='center',fontsize=10)
ax.text(281,110,'车\n头',fontsize=11,va='center');ax.text(-7,110,'车\n尾',fontsize=11,ha='right',va='center')
ax.set(xlim=(-20,300),ylim=(-15,239),xlabel='底板 X / mm',ylabel='底板 Y / mm',title='一体底板布局与 B1 PCB 安装位置（俯视）')
ax.set_aspect('equal');ax.set_xticks(range(0,281,20));ax.set_yticks(range(0,221,20));ax.grid(alpha=.18)
fig.tight_layout();fig.savefig(O/'preview/layout_dimensions.png',dpi=180);plt.close(fig)
with (O/'checks/module_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['ID','模块','中心X_mm','中心Y_mm','绕Z旋转_deg','PCB承托Z_mm']);w.writerows(rows)
print('layout saved')
