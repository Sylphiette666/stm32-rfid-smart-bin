"""Dimensioned join drawings from the release's exact hole and joint metadata."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon,FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]/'flat-split-20261101'
d=json.loads((ROOT/'source/design.json').read_text(encoding='utf-8'))
plt.rcParams['font.family']='Microsoft YaHei';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(11,9.5))
ax.add_patch(Rectangle((0,0),137.85,220,facecolor='#c3dfeb',edgecolor='#315e74',lw=1.6))
ax.add_patch(Rectangle((138.15,0),141.85,220,facecolor='#d4e9e6',edgecolor='#315e74',lw=1.6))
for y in [32,174]:
 ax.add_patch(Rectangle((137.7,y-.25),6.55,16.5,color='white',zorder=2))
 ax.add_patch(FancyBboxPatch((136,y),8,16,boxstyle='round,pad=0,rounding_size=0.8',facecolor='#c3dfeb',edgecolor='#315e74',lw=1,zorder=3))
for h in d['mount_holes']:
 ax.add_patch(Circle(h['xy'],1.7,color='#607985'))
for x,y in [(30,25),(250,25),(30,195),(250,195)]:
 ax.add_patch(Circle((x,y),1.7,color='#162f3d'));ax.add_patch(Circle((x,y),5,fill=False,edgecolor='#162f3d',lw=1))
for y in [82,110,138]:
 ax.add_patch(FancyBboxPatch((118,y-12),40,24,boxstyle='round,pad=0,rounding_size=2',facecolor='#edc589',edgecolor='#ad7128',alpha=.85,zorder=4))
for x,y in d['joint']['new_holes']:ax.add_patch(Circle((x,y),1.7,color='#9d381e',zorder=5))
ax.annotate('3 块底部连接片\n每块 40×24×5 mm',xy=(158,110),xytext=(195,111),fontsize=11,arrowprops=dict(arrowstyle='->',color='#8d5b22'),color='#774d1d')
ax.annotate('两个定位舌\n侧向插合',xy=(141,183),xytext=(180,176),fontsize=11,arrowprops=dict(arrowstyle='->'),color='#193c4b')
ax.text(58,109,'后半片',ha='center',fontsize=16,color='#315e74');ax.text(236,62,'前半片',ha='center',fontsize=16,color='#315e74')
ax.annotate('',(280,-8),(0,-8),arrowprops=dict(arrowstyle='<->'));ax.text(140,-17,'组装后 280 mm（保持原尺寸）',ha='center',fontsize=11)
ax.annotate('',(-9,220),(-9,0),arrowprops=dict(arrowstyle='<->'));ax.text(-17,110,'220 mm',ha='center',va='center',rotation=90,fontsize=11)
ax.set_xlim(-26,286);ax.set_ylim(-26,226);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('底板平放拼接版：原孔位与原外形保留',fontsize=19,y=.98)
fig.text(.5,.03,'从底板上方看；橙色为底面连接片投影。先对齐 280×220 外形，再交替拧紧。',ha='center',fontsize=11)
fig.savefig(ROOT/'preview/01_join_layout.png',dpi=180,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(11.5,6.2))
for x,w,c in [(116,21.85,'#c3dfeb'),(138.15,21.85,'#d4e9e6')]:ax.add_patch(Rectangle((x,0),w,5,fc=c,ec='#315e74'))
ax.add_patch(Rectangle((118,-5),40,5,fc='#edc589',ec='#ad7128'))
for x in [126,150]:
 ax.add_patch(Rectangle((x-1.5,-10.5),3,16,fc='#9ba6ad',ec='#364550',lw=.8))
 ax.add_patch(Rectangle((x-3,5),6,.5,fc='#d5dce0',ec='#364550',lw=.8))
 ax.add_patch(Rectangle((x-2.85,5.5),5.7,1.65,fc='#9ba6ad',ec='#364550',lw=.8))
 ax.add_patch(Rectangle((x-3,-5.5),6,.5,fc='#d5dce0',ec='#364550',lw=.8))
 ax.add_patch(Rectangle((x-2.75,-9.5),5.5,4,fc='#9ba6ad',ec='#364550',lw=.8))
ax.add_patch(Rectangle((116,15),44,1.6,fc='#5a9d7d',ec='#305f4d'))
ax.text(138,17.5,'A1 PCB：原 10 mm 绝缘柱支承',ha='center',fontsize=12,color='#305f4d')
ax.annotate('板面 5 mm',xy=(155,2.5),xytext=(165,4),fontsize=11,arrowprops=dict(arrowstyle='->'))
ax.annotate('底部连接片 5 mm',xy=(154,-2.5),xytext=(165,-2.5),fontsize=11,arrowprops=dict(arrowstyle='->'))
ax.annotate('M3 防松螺母＋垫圈',xy=(150,-7.5),xytext=(160,-12),fontsize=11,arrowprops=dict(arrowstyle='->'))
ax.annotate('M3×16 低圆头螺钉\n头下加 0.5 mm 垫圈',xy=(126,6.5),xytext=(101,11),fontsize=11,arrowprops=dict(arrowstyle='->'))
ax.annotate('',(132,7.15),(132,15),arrowprops=dict(arrowstyle='<->'));ax.text(134,10.8,'名义净空 7.85',fontsize=10)
ax.set_xlim(98,191);ax.set_ylim(-16,21);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('接缝剖面与紧固顺序',fontsize=19,y=.98)
fig.text(.5,.12,'每块连接片四颗螺钉；共 12 颗 M3×16、24 片小垫圈、12 颗 M3 防松螺母。',ha='center',fontsize=11)
fig.text(.5,.055,'螺钉最低点在原底板下 10.5 mm；A1 板底焊脚和实际轮组必须试装检查。未进行承重实测。',ha='center',fontsize=10,color='#714e2c')
fig.savefig(ROOT/'preview/02_join_section.png',dpi=180,bbox_inches='tight');plt.close(fig)
print('Joint figures written.')
