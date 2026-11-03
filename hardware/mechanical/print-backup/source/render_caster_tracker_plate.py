"""Render the combined P2S plate from the actual print meshes."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
import trimesh
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus'] = False

B = Path(__file__).resolve().parents[1]
O = B/'caster-tracker-plate-20261103'
report = json.loads((O/'geometry_check.json').read_text(encoding='utf8'))
source = {
    'CASTER_FRAME': B/'caster-riser-20261103/parts/CASTER_FRAME_PRINT.stl',
    'TRACKER_FRAME': B/'tracker-mount-20261103/parts/TRACKER_FRAME_PRINT.stl',
    'CASTER_COLUMN_A_H41': B/'caster-riser-20261103/parts/CASTER_COLUMN_41_PRINT.stl',
    'CASTER_COLUMN_B_H41': B/'caster-riser-20261103/parts/CASTER_COLUMN_41_PRINT.stl',
}
for h in (14, 18, 22):
    for suffix in ('A','B'):
        source[f'TRACKER_SPACER_{h}_{suffix}'] = B/f'tracker-mount-20261103/parts/SPACER_{h}_PRINT.stl'
colors = {'CASTER_FRAME':'#078c78','TRACKER_FRAME':'#3182bd'}
fig,ax = plt.subplots(figsize=(11,10),dpi=180)
ax.add_patch(Rectangle((0,0),256,256,facecolor='#f5f7fa',edgecolor='#263746',lw=2))
for name, box in report['bounds_xy_mm']:
    mesh = trimesh.load_mesh(source[name])
    tri = mesh.vertices[mesh.faces][:,:,:2].copy()
    tri[:,:,0] += box[0]-mesh.bounds[0,0]
    tri[:,:,1] += box[1]-mesh.bounds[0,1]
    color = colors.get(name,'#cf7b33' if name.startswith('CASTER_') else '#70a6cf')
    ax.add_collection(PolyCollection(tri,facecolors=color,edgecolors='none',alpha=.95))
    cx,cy=(box[0]+box[2])/2,(box[1]+box[3])/2
    if name=='CASTER_FRAME':
        label='万向轮支架 H41'
    elif name=='TRACKER_FRAME':
        label='循迹模块转接架'
    elif name.startswith('CASTER_COLUMN'):
        label='H41立柱'
    else:
        label=name.split('_')[2]+'mm'
    ax.text(cx,cy,label,ha='center',va='center',fontsize=10 if 'FRAME' in name else 7,
            color='white' if 'FRAME' in name else '#263746',weight='bold',
            bbox=dict(facecolor='#263746' if 'FRAME' in name else 'white',alpha=.85,edgecolor='none',pad=2))
ax.set(xlim=(-5,261),ylim=(-5,261),xlabel='打印盘 X (mm)',ylabel='打印盘 Y (mm)',
       title='P2S 同盘打印：H41 万向轮支架 + 循迹模块转接架（10 件）')
ax.set_aspect('equal')
ax.grid(alpha=.13)
fig.tight_layout()
fig.savefig(O/'plate_preview.png')
plt.close(fig)
print(O/'plate_preview.png')
