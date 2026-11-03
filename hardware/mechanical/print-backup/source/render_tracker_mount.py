from pathlib import Path
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,Circle
import cadquery as cq
B=Path(__file__).resolve().parents[1];O=B/'tracker-mount-20261103';(O/'preview').mkdir(exist_ok=True)
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei','Arial Unicode MS'];plt.rcParams['axes.unicode_minus']=False
d=json.loads((B/'motor-existing-holes-20261102/checks/design.json').read_text(encoding='utf8'))
fig,ax=plt.subplots(figsize=(11,7));ax.add_patch(Rectangle((0,0),280,220,facecolor='#eff5f7',edgecolor='#334155',lw=2))
for name,v in d['variants'].items():ax.add_patch(Polygon(v['outline'],facecolor='#f3b665',edgecolor='#9a5b11',alpha=.7,label='电机转接板' if name=='LEFT' else None))
ax.add_patch(Rectangle((214,78),56,64,facecolor='#eda1aa',edgecolor='#a42638',alpha=.55,label='前万向轮保留区'))
for y in (82,110,138):ax.add_patch(Rectangle((118,y-12),40,24,facecolor='#8faac3',edgecolor='#42617c',alpha=.7))
shape=cq.importers.importStep(str(O/'step/TRACKER_FRAME_ASSEMBLY.step')).val();bb=shape.BoundingBox()
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
outline=unary_union([LineString([(150,88),(170,88),(185,80.25)]).buffer(4),LineString([(150,116),(170,116),(185,139.75)]).buffer(4),LineString([(170,88),(170,116)]).buffer(3.5)]+[Point(*p).buffer(6) for p in [(150,88),(150,116),(185,80.25),(185,139.75)]])
ax.add_patch(Polygon(list(outline.exterior.coords),facecolor='#148f83',edgecolor='#075d57',alpha=.9,label='新轻量转接架'))
ax.add_patch(Rectangle((171.5,76.5),27,67,facecolor='none',edgecolor='#175cd3',lw=2,linestyle='--',label='67×27循迹板外形'))
for i,p in enumerate([(150,88),(150,116),(185,80.25),(185,139.75)]):ax.add_patch(Circle(p,2,facecolor='white',edgecolor='black'));ax.text(p[0]+3,p[1]+3,['A','B','C','D'][i],fontsize=11,weight='bold')
ax.annotate('车头 +X',xy=(276,210),xytext=(235,210),arrowprops={'arrowstyle':'->','lw':2},fontsize=12)
ax.text(3,206,'俯视：底板下方安装位置（mm）',fontsize=15,weight='bold')
ax.set_xlim(-5,285);ax.set_ylim(-5,225);ax.set_aspect('equal');ax.set_xlabel('X：车尾 → 车头');ax.set_ylabel('Y：非舵机侧 → 舵机侧');ax.grid(alpha=.12);ax.legend(loc='upper left',bbox_to_anchor=(.01,.88),fontsize=9);fig.tight_layout();fig.savefig(O/'preview/01_tracker_layout.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));ax.add_patch(Rectangle((0,0),38,5,facecolor='#9fb9c8',label='底板 P01'));ax.add_patch(Rectangle((0,-5),38,5,facecolor='#668ba6',label='原拼接片'));ax.add_patch(Rectangle((0,-8),38,3,facecolor='#148f83',label='新转接架 3 mm'));ax.add_patch(Rectangle((20,-26),8,18,facecolor='#87b3a9',label='18 mm 垫柱示例'));ax.add_patch(Rectangle((12,-27.6),24,1.6,facecolor='#174cbd',label='循迹板示意'));ax.plot([20,20],[-29,5],color='#444',lw=1.5);ax.plot([28,28],[-29,5],color='#444',lw=1.5);ax.text(39,-3,'A/B：原拼接螺钉改 M3×20',fontsize=11);ax.text(39,-14,'C/D：板孔距 59.5 mm，选同长垫柱 2 只',fontsize=11);ax.text(39,-24,'探头最低点和离地距离须实测',fontsize=11,color='#a42638');ax.set_xlim(-2,100);ax.set_ylim(-36,12);ax.set_aspect('equal');ax.axis('off');ax.legend(loc='lower right',fontsize=9);fig.tight_layout();fig.savefig(O/'preview/02_tracker_stack.png',dpi=180);plt.close(fig)
