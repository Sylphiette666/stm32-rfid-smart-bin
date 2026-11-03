from pathlib import Path
import json,matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,Circle
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
B=Path(__file__).resolve().parents[1];O=B/'caster-riser-20261103'
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei'];plt.rcParams['axes.unicode_minus']=False
d=json.loads((B/'motor-existing-holes-20261102/checks/design.json').read_text(encoding='utf8'))
fig,ax=plt.subplots(figsize=(10,7));ax.add_patch(Rectangle((0,0),280,220,facecolor='#eef4f6',edgecolor='#334155',lw=2))
for name,v in d['variants'].items():ax.add_patch(Polygon(v['outline'],facecolor='#efa45d',alpha=.6,edgecolor='#a85a10',label='电机转接板' if name=='LEFT' else None))
ax.add_patch(Rectangle((171.5,76.5),27,67,facecolor='#7eaad6',alpha=.7,label='循迹模块'))
a=[(205,65),(205,155)];c=[(240,90),(240,130)]
poly=unary_union([LineString([a[0],(218,76),c[0]]).buffer(4),LineString([a[1],(218,144),c[1]]).buffer(4),LineString(c).buffer(4)]+[Point(*p).buffer(7.5) for p in a+c])
ax.add_patch(Polygon(list(poly.exterior.coords),facecolor='#1e907c',edgecolor='#076150',alpha=.9,label='万向轮增高支架'))
ax.add_patch(Rectangle((214,78),56,64,facecolor='none',edgecolor='#aa3150',lw=2,ls='--',label='万向轮保留区'))
for i,(x,y) in enumerate(a+c):ax.add_patch(Circle((x,y),2.2,facecolor='white',edgecolor='#111'));ax.text(x+3,y+2,['A','B','C','D'][i],fontsize=11,weight='bold')
ax.text(3,207,'底板下方俯视安装图（mm）',fontsize=15,weight='bold');ax.annotate('车头 +X',xy=(277,210),xytext=(232,210),arrowprops={'arrowstyle':'->','lw':2},fontsize=12)
ax.set(xlim=(-5,285),ylim=(-5,225),xlabel='X：车尾 → 车头',ylabel='Y：非舵机侧 → 舵机侧');ax.set_aspect('equal');ax.grid(alpha=.12);ax.legend(loc='upper left',bbox_to_anchor=(.01,.85));fig.tight_layout();fig.savefig(O/'preview/01_caster_layout.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));ax.add_patch(Rectangle((0,0),45,5,facecolor='#a3bdc8',label='原底板 5mm'));ax.add_patch(Rectangle((5,-4),35,4,facecolor='#1e907c',label='支架 4mm'));ax.add_patch(Rectangle((20,-7),13,3,facecolor='#1e907c',label='孔位承力台'));ax.add_patch(Rectangle((20,-41),13,34,facecolor='#8ebcb4',label='H41 的 34mm 立柱'));ax.add_patch(Rectangle((12,-43),29,2,facecolor='#777',label='万向轮安装片示意'));ax.plot([26,26],[-45,-2.2],color='#333',lw=1.5);ax.text(47,1,'A/B：复用 A1 主板已有安装孔',fontsize=11);ax.text(47,-17,'C/D：万向轮两孔，中心距 40mm',fontsize=11);ax.text(47,-34,'H = 名义底板离地 61 − 万向轮总高 20 = 41mm',fontsize=10,color='#a12640');ax.set_xlim(-2,105);ax.set_ylim(-50,12);ax.axis('off');ax.legend(loc='lower right',fontsize=9);fig.tight_layout();fig.savefig(O/'preview/02_caster_stack.png',dpi=180);plt.close(fig)
