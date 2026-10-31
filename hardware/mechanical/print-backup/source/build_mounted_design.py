"""Measured one-piece deck and separate, reusable scheme-A module fixtures.

The base/upper remain single manufactured pieces. Small fixtures are removable
accessories. This builder exports clean local print meshes; packing is separate.
"""
from pathlib import Path
import json,math,sys,hashlib
import cadquery as cq
import numpy as np
import trimesh

sys.path.insert(0,str(Path(__file__).resolve().parent))
from module_clamps_a import build_holder,make_lock

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mounted-20261031'
for sub in ['parts','step','source','checks','preview','geometry','projects']:
    (OUT/sub).mkdir(parents=True,exist_ok=True)

def block(x,y,z,a,b,c):
    return cq.Workplane('XY').box(a,b,c,centered=False).translate((x,y,z)).val()
def cyl(x,y,z,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def union(shapes):return shapes[0].fuse(*shapes[1:]).clean()
def bounds(shape):
    b=shape.BoundingBox();return [[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]]
def boxes_overlap(a,b):
    aa=a.BoundingBox();bb=b.BoundingBox()
    return not (aa.xmax<=bb.xmin or bb.xmax<=aa.xmin or aa.ymax<=bb.ymin or bb.ymax<=aa.ymin or aa.zmax<=bb.zmin or bb.zmax<=aa.zmin)
def rigid(shape,xy,rotation=0,z=0):
    return shape.rotate((0,0,0),(0,0,1),rotation).translate((xy[0],xy[1],z))
def point_xy(p,xy,rotation=0):
    a=math.radians(rotation);x,y=p
    return [xy[0]+x*math.cos(a)-y*math.sin(a),xy[1]+x*math.sin(a)+y*math.cos(a)]

SPECS=[
 dict(id='M01',name='STM32核心板',l=53,w=22,seat_height=20,component_height=9,headers_face='back',header_protrusion=9,interfaces={'USB':'right','SWD':'left'},xy=[31.5,68],rotation=180),
 dict(id='M02',name='MCP23017',l=26,w=21,seat_height=20,component_height=5,headers_face='back',header_protrusion=9,interfaces={},xy=[91,74],rotation=0),
 dict(id='M03',name='FLASH',l=23,w=19,seat_height=4,component_height=9,headers_face='front',header_protrusion=9,interfaces={},xy=[92,125],rotation=0),
 dict(id='M04',name='TB6612驱动',l=25,w=25,seat_height=4,component_height=9,headers_face='front',header_protrusion=9,interfaces={},xy=[157,188.5],rotation=0),
 dict(id='M05',name='3.3V稳压',l=13,w=9,seat_height=10,component_height=1,headers_face='back',header_protrusion=5,interfaces={'bent_header':'right'},xy=[57.5,18.5],rotation=0),
 dict(id='M06',name='DFPlayer',l=21.5,w=20.5,seat_height=20,component_height=3,headers_face='back',header_protrusion=8,interfaces={'TF':'left'},xy=[23,113],rotation=0),
 dict(id='M07',name='HC-05蓝牙',l=39,w=16,seat_height=5,component_height=1,headers_face='front',header_protrusion=6,interfaces={'antenna':'right','front_header':{'edge':'left','face':'front'}},xy=[25,164],rotation=90),
 dict(id='M08',name='MPU6050',l=25,w=25,seat_height=4,component_height=2,headers_face='front',header_protrusion=9,interfaces={},xy=[120,188.5],rotation=0),
 dict(id='M09',name='蜂鸣器',l=24,w=15,seat_height=4,component_height=6,headers_face='front',header_protrusion=9,interfaces={'sound':'centre'},xy=[97,24],rotation=0),
]

parts=[];assembly=[];modules=[];holes=[];holders={};checks=[]
COLOURS={'body':'#9ba6af','lid':'#e6a04b','keeper':'#3d7eb8','detent':'#69a18a'}

def export_part(ident,shape,role,module):
    assert shape.isValid() and len(shape.Solids())==1,(ident,'CAD solid')
    cq.exporters.export(shape,str(OUT/'step'/(ident+'.step')))
    b=shape.BoundingBox();shift=[-b.xmin,-b.ymin,-b.zmin]
    flat=shape.translate(tuple(shift))
    path=OUT/'parts'/(ident+'.stl')
    cq.exporters.export(flat,str(path),tolerance=.018,angularTolerance=.05)
    mesh=trimesh.load_mesh(path)
    # OCC/STL float32 can produce duplicate points a few microns apart on a
    # tangent fillet seam. Weld numerically coincident vertices, never fill holes.
    mesh.merge_vertices(digits_vertex=5)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_winding_consistent,(ident,'mesh')
    shells=mesh.split(only_watertight=False)
    assert sum(s.volume>0 for s in shells)==1,(ident,'disconnected exterior')
    assert abs(mesh.volume-shape.Volume())/shape.Volume()<.005,(ident,'mesh volume')
    mesh.export(path)
    record={'id':ident,'module':module,'role':role,'stl':'parts/'+ident+'.stl',
            'step':'step/'+ident+'.step','print_extents':mesh.extents.tolist(),
            'normalising_translation':shift,'volume_mm3':shape.Volume(),
            'numerical_mesh_weld_mm':.00001,
            'closed_internal_voids':int(sum(s.volume<0 for s in shells))}
    parts.append(record);return record

for spec in SPECS:
    h=build_holder(spec);holders[spec['id']]=h
    for role in ['body','lid','keeper','detent']:
        export_part(spec['id']+'_'+role,h[role],role,spec['id'])
        assembly.append({'id':spec['id']+'_'+role,'shape':rigid(h[role],spec['xy'],spec['rotation'],5),'color':COLOURS[role]})
    fasteners=h.get('fastener_points_xy',{'foot':h['mount_holes_xy'],'axis':[h['dimensions']['lock_axis_xy']], 'anchor':[h['dimensions']['lock_anchor_xy']]})
    local_holes=[]
    for kind,points in fasteners.items():
        if points and isinstance(points[0],(int,float)):points=[points]
        for p in points:
            xy=point_xy(p,spec['xy'],spec['rotation']);holes.append({'name':spec['id']+'_'+kind,'xy':xy,'diameter':3.4})
            local_holes.append({'type':kind,'xy':xy,'diameter':3.4})
    b=h['board_bounds_local'];pcb=block(b[0][0],b[0][1],b[0][2],spec['l'],spec['w'],2)
    assembly.append({'id':spec['id']+'_PCB','shape':rigid(pcb,spec['xy'],spec['rotation'],5),'color':'#3e7c68','is_electronics':True})
    checks.append({'id':spec['id'],**h['digital_checks']})
    modules.append({'id':spec['id'],'name':spec['name'],'board_size':[spec['l'],spec['w'],2],
                    'layout_origin':spec['xy'],'rotation':spec['rotation'],'seat_height':spec['seat_height'],
                    'fixing':'方案A：金属轴翻盖压框、90°拨片、独立定位簧片',
                    'header_side':spec['headers_face'],'header_protrusion':spec['header_protrusion'],
                    'mount_holes':local_holes,'interfaces':spec['interfaces'],
                    'notes':['座高不含底板厚5mm。','压框只搭边，装配后核查排针塑壳和实际器件净空。'],
                    'mechanism':h['dimensions']})

# A1 motherboard: existing four holes, insulated 10-mm standoffs, power edge +X.
a1_xy=[160,110]
for p in [[-45,-45],[45,-45],[-45,45],[45,45]]:
    holes.append({'name':'A1_M3','xy':point_xy(p,a1_xy),'diameter':3.4})
a1=block(110,60,15,100,100,1.6)
assembly.append({'id':'A1_PCB','shape':a1,'color':'#3a6f62','is_electronics':True})
modules.append({'id':'A1','name':'A1主PCB','board_size':[100,100,1.6],
    'layout_origin':a1_xy,'rotation':180,'seat_height':10,'fixing':'四个M3孔＋10mm绝缘隔离柱',
    'notes':['四孔中心115/205、65/155。','动力端子朝车头+X，外侧预留20mm以上走线区。','用户28mm为正反焊后总包络，不与板厚重复叠加。'],
    'mount_holes':[p for p in holes if p['name']=='A1_M3']})

# 5V buck: only the measured two 3-mm mounting holes, not four solder pads.
buck_xy=[202.5,187.5]
buck=block(-23.5,-12.5,0,47,25,3.2)
for x,y in [[-14.5,8.5],[14.5,-8.5]]:
    buck=buck.fuse(cyl(x,y,0,3.3,6.2))
    buck=buck.cut(cyl(x,y,-1,1.4,9))
    # CadQuery polygon diameter is across corners; allow 5.4 mm across flats.
    nut=cq.Workplane('XY').polygon(6,5.4/math.cos(math.pi/6)).extrude(2.25).translate((x,y,-.05)).val()
    buck=buck.cut(nut)
for x in [-13,13]:
    buck=buck.cut(cyl(x,0,-1,1.7,5))
    holes.append({'name':'BUCK_base','xy':point_xy([x,0],buck_xy),'diameter':3.4})
buck=buck.clean();export_part('P06_BUCK_cradle',buck,'body','BUCK')
assembly.append({'id':'P06_BUCK_cradle','shape':rigid(buck,buck_xy,z=5),'color':'#a5aeb4'})
assembly.append({'id':'BUCK_PCB','shape':block(buck_xy[0]-21.5,buck_xy[1]-10.5,11.2,43,21,2),'color':'#4779a4','is_electronics':True})
modules.append({'id':'BUCK','name':'5V降压模块','board_size':[43,21,2],'layout_origin':buck_xy,
                'rotation':0,'seat_height':6.2,'fixing':'两大孔M2.5螺钉＋独立绝缘座；座再用2颗M3固定',
                'notes':['模块局部孔(7,19)/(36,2)，孔心横差29、纵差17；4焊盘不作安装孔。','先放底面M2.5螺母再固定载座，电位器上方留空。']})

# Speaker rim cradle and two adjustable ear studs. Ear height is not guessed.
spk_xy=[68,198]
speaker=cyl(0,0,0,21.2,2).cut(cyl(0,0,-1,17.8,4))
for x in [-24,24]:
    speaker=speaker.fuse(cyl(x,0,0,4.8,2)).fuse(block(min(x,0),-2,0,abs(x),4,2))
    speaker=speaker.cut(cyl(x,0,-1,1.7,5))
    holes.append({'name':'SPK_ear','xy':point_xy([x,0],spk_xy),'diameter':3.4})
# Three short locating lips leave the wire edge open.
lip=cyl(0,0,2,21.2,2).cut(cyl(0,0,1,20.5,4))
for angle in [15,135,255]:
    wedge=cq.Workplane('XY').moveTo(0,0).lineTo(24*math.cos(math.radians(angle)),24*math.sin(math.radians(angle))).threePointArc((24*math.cos(math.radians(angle+15)),24*math.sin(math.radians(angle+15))),(24*math.cos(math.radians(angle+30)),24*math.sin(math.radians(angle+30)))).close().extrude(6).val()
    speaker=speaker.fuse(lip.intersect(wedge))
speaker=speaker.cut(block(-3,-24,-1,6,7,6)).clean()
export_part('P07_SPEAKER_cradle',speaker,'body','SPK')
assembly.append({'id':'P07_SPEAKER_cradle','shape':rigid(speaker,spk_xy,z=5),'color':'#a5aeb4'})
assembly.append({'id':'SPK_body','shape':cyl(spk_xy[0],spk_xy[1],7,20,14),'color':'#3e4b55','is_electronics':True})
modules.append({'id':'SPK','name':'小喇叭','board_size':[40,40,14],'layout_origin':spk_xy,
    'rotation':0,'seat_height':2,'fixing':'Ø40定位圈＋48mm耳距M3螺柱，耳下螺母调高',
    'notes':['按图两耳孔Ø4±0.2、孔心距48±0.5。','安装耳高度未量，用下方螺母调到接触耳片，再用垫片和上螺母固定，勿压弯耳片。']})

# Battery: rigid cradle and two indexed keepers on the plastic case ends.
bat_xy=[176,30]
bat=block(-40.2,-22.2,0,80.4,44.4,2.4).cut(block(-36.2,-18.2,-1,72.4,36.4,4))
for x in [-22,22]:bat=bat.fuse(block(x-4,-18.3,0,8,36.6,2.4))
for x in [-40.2,38.6]:bat=bat.fuse(block(x,-22.2,0,1.6,44.4,7.4))
for y in [-22.2,20.6]:bat=bat.fuse(block(-40.2,y,0,80.4,1.6,7.4))
bat=bat.cut(block(37.8,-6,2.3,4,12,7))
for x in [-24,24]:
    for y in [-24,24]:
        bat=bat.fuse(cyl(x,y,0,4.5,2.4)).cut(cyl(x,y,-1,1.7,5))
        holes.append({'name':'BAT_foot','xy':point_xy([x,y],bat_xy),'diameter':3.4})
battery_locks=[]
for side,x,y,rot in [('L',-42.2,-10,90),('R',42.2,10,-90)]:
    lock=make_lock(base_z=0,catch_top_z=24.4)
    fixed=rigid(lock['body'],[x,y],rot)
    bat=bat.fuse(fixed)
    for role in ['keeper','detent']:
        shape=rigid(lock[role],[x,y],rot)
        ident='BAT_'+side+'_'+role
        export_part(ident,shape,role,'BAT')
        assembly.append({'id':ident,'shape':rigid(shape,bat_xy,z=5),'color':COLOURS[role]})
    for kind,p in [('axis',lock['axis_xy']),('anchor',lock['anchor_xy'])]:
        local=point_xy(p,[x,y],rot);holes.append({'name':'BAT_'+side+'_'+kind,'xy':point_xy(local,bat_xy),'diameter':3.4})
    battery_locks.append({'side':side,'axis_xy':point_xy([x,y],bat_xy),'rotation':rot,'lock':lock})
for x in [-24,24]:
    for y in [-24,24]:
        # Clear the low button head / OD6 washer from the adjacent case wall.
        bat=bat.cut(cyl(x,y,2.4,3.2,2.35))
bat=bat.clean();export_part('P05_BATTERY_cradle',bat,'body','BAT')
assembly.append({'id':'P05_BATTERY_cradle','shape':rigid(bat,bat_xy,z=5),'color':'#a5aeb4'})
assembly.append({'id':'BAT_body','shape':block(138,10,9.4,76,40,20),'color':'#405b85','is_electronics':True})
modules.append({'id':'BAT','name':'2S串联电池','board_size':[76,40,20],'layout_origin':bat_xy,
    'rotation':0,'seat_height':4.4,'fixing':'框式托架＋两端方案A旋转压片；支承条铺2mm EVA',
    'notes':['用户确认同尺寸为2S串联7.4V。','出线朝+X，右端中央12mm让线口；压片在端部塑料壳边，勿压电芯或导线。','闭合留0.2mm限位余隙，防跳出而非压紧电芯。']})

# Keep original geometry and all known full-depth structural zones. Refill only
# the mounting-hole lands through the existing underside relief pockets.
original=cq.importers.importStep(str(ROOT/'step/P01_light.step')).val()
full=cq.importers.importStep(str(ROOT/'step/P01_full.step')).val()
lands=[cyl(h['xy'][0],h['xy'][1],0,6,5).intersect(full) for h in holes]
base=original.fuse(*lands).clean()
for h in holes:
    x,y=h['xy'];assert 3.4<x<276.6 and 3.4<y<216.6,(h['name'],h['xy'])
    base=base.cut(cyl(x,y,-1,h['diameter']/2,7))
base=base.clean();assert base.isValid() and len(base.Solids())==1
for x,y in [[30,25],[250,25],[30,195],[250,195]]:
    assert base.intersect(cyl(x,y,-1,1.69,7)).Volume()<1e-6
cq.exporters.export(base,str(OUT/'step/P01_MOUNTED_BASE.step'))
cq.exporters.export(base,str(OUT/'parts/P01_MOUNTED_BASE_DESIGN.stl'),tolerance=.018,angularTolerance=.05)

# Cross-check all separate fixtures against each other and the four service posts.
physical=[a for a in assembly if not a.get('is_electronics')]
for i,a in enumerate(physical):
    for b in physical[i+1:]:
        if a['id'].split('_')[0]==b['id'].split('_')[0]:continue
        aa=a['shape'].BoundingBox();bb=b['shape'].BoundingBox()
        if aa.xmax<bb.xmin or bb.xmax<aa.xmin or aa.ymax<bb.ymin or bb.ymax<aa.ymin:continue
        volume=a['shape'].intersect(b['shape']).Volume()
        assert volume<1e-5,('fixture collision',a['id'],b['id'],volume)
for a in physical:
    for x,y in [[30,25],[250,25],[30,195],[250,195]]:
        assert a['shape'].intersect(cyl(x,y,5,5,65)).Volume()<1e-5,('pillar tool zone',a['id'],x,y)

upper=cq.importers.importStep(str(ROOT/'step/P02_light.step')).val().translate((20,15,65))
opening=[]
for spec in SPECS:
    h=holders[spec['id']]
    axis=h['dimensions']['hinge_axis']['point']
    tests=[]
    for angle in [0,15,30,45,60,75,90,105]:
        lid=h['lid'].rotate(tuple(axis),(axis[0]+1,axis[1],axis[2]),angle)
        world=rigid(lid,spec['xy'],spec['rotation'],5)
        # Full opening can require removal of the upper platform; report it.
        vol=world.intersect(upper).Volume() if boxes_overlap(world,upper) else 0.0
        others=[]
        for other in physical:
            if other['id'].startswith(spec['id']+'_'):continue
            if not boxes_overlap(world,other['shape']):continue
            v=world.intersect(other['shape']).Volume()
            if v>1e-5:others.append({'part':other['id'],'volume_mm3':v})
        tests.append({'degrees':angle,'upper_intersection_mm3':vol,'other_fixtures':others})
    opening.append({'id':spec['id'],'samples':tests})

hardware=[
 {'name':'M3低圆头螺钉','quantity':22,'spec':'M3×12，ISO7380圆头高1.65mm','used_for':'9卡座18颗＋电池座4颗','notes':'头在座脚上，两片0.5mm小垫圈，底板下方用高2.4mm普通六角螺母；此长度不配高4mm锁紧螺母。'},
 {'name':'M3螺栓或金属轴','quantity':9,'spec':'M3×30，ISO7380低圆头Ø5.7×1.65mm','used_for':'9个金属轴铰链','notes':'此头型为铰链避空依据，不可换高圆柱头；自锁螺母只锁轴向间隙，压框应能自由翻动。'},
 {'name':'M3拨片轴及簧片锚钉','quantity':10,'spec':'M3×40','used_for':'M01/M02/M06各2根＋电池左右各2根','notes':'全部头在5mm底板下面；每根上下各1片0.5mm垫圈、上方4mm高锁母。轴顶留0.1–0.2mm转动间隙，锚钉固定簧片头。'},
 {'name':'M3拨片轴及簧片锚钉','quantity':2,'spec':'M3×30','used_for':'M05稳压模块2根','notes':'同40mm组装法，簧片头上垫圈外径不得超过6mm。'},
 {'name':'M3拨片轴及簧片锚钉','quantity':10,'spec':'M3×25','used_for':'M03/M04/M07/M08/M09各2根','notes':'同40mm组装法，不在拨片轴座与拨片之间另加圆垫圈，以免遮住定位凸点。'},
 {'name':'M3降压载座固定螺钉','quantity':2,'spec':'M3×16，ISO7380圆头高1.65mm','used_for':'BUCK载座与5mm底板','notes':'头在载座上、锁母在底板下；两片0.5mm垫圈及4mm高锁母，载座厚3.2mm；两颗不包含于22颗座脚螺钉。'},
 {'name':'M3绝缘双通柱','quantity':4,'spec':'10mm','used_for':'A1 PCB','notes':'A1四孔90×90mm。'},
 {'name':'M3绝缘柱下螺钉','quantity':4,'spec':'M3×10','used_for':'A1柱底固定','notes':'头在5mm底板下，配0.5mm垫圈，名义入柱4.5mm；先核对实物盲孔深度。'},
 {'name':'M3绝缘柱上螺钉','quantity':4,'spec':'M3×6','used_for':'A1 PCB固定','notes':'板厚1.6mm＋0.5mm垫圈后名义入柱3.9mm。'},
 {'name':'M2.5螺钉及螺母','quantity':2,'spec':'M2.5×8','used_for':'5V模块两大孔','notes':'螺母先放到降压座底面六角窝。此处不加垫圈，约1.8mm有效吃牙；轻载试装，勿换长螺钉顶底板。'},
 {'name':'M3喇叭螺钉','quantity':2,'spec':'M3×30，暂定','used_for':'喇叭两耳','notes':'每根头下、耳下、耳上共3片垫圈，耳下普通螺母、耳上锁母。耳下表面距底板顶面E与耳厚t须满足E+t≤19mm；不得压弯耳片或抬高到脱离定位圈。'},
 {'name':'M3普通六角螺母','quantity':24,'spec':'高2.4mm、对边5.5mm','used_for':'22座脚＋2喇叭耳下调高','notes':'仅新增模块固定件，不含原立柱及舵机螺丝。'},
 {'name':'M3尼龙锁紧螺母','quantity':35,'spec':'DIN985，高4mm、螺距0.5mm','used_for':'9铰链＋22轴/锚＋2降压座＋2喇叭耳上','notes':'不要用高型锁母直接替换4mm高型。'},
 {'name':'M3小外径平垫圈','quantity':124,'spec':'内径3.2mm、外径≤6mm、厚约0.5mm','used_for':'新增全部M3连接的配套垫圈','notes':'簧片锚点上方必须小外径，不能压住12mm自由弹臂；124片为上述选定方案数量，不含备用。'}]
design={'units':'mm','status':'module_mounts_built_print_packing_pending',
 'coordinate_notes':'底板局部X由车尾指向车头，Y=0..220。layout_origin记录模块/卡座的中心；rotation为从模块本地长边+X逆时针转角。',
 'seat_height_reference':'座高相对底板顶面Z=5；PCB底面绝对Z=5+seat_height。',
 'base_size':[280,220,5],'upper_size':[240,190,5],'standoff_height':60,
 'modules':modules,'hardware':hardware,'mount_holes':holes,'parts':parts,
 'latch_parameters':{'type':'A','closed_degrees':0,'open_degrees':90,'rigid_overlap_mm':2.3,
   'metal_hinge':'M3轴；中央三节，统一30mm','spring_thickness_mm':1.16,'index_nib_mm':.48,'nominal_deflection_mm':.25,'spring_load_bearing':False},
  'assembly_notes':['本次全部M3螺钉按ISO7380低圆头Ø5.7×1.65mm审核，铰链、座脚与降压载座不得换高圆柱头。','先将卡座固定到底板，再装PCB、铰链轴、定位簧片和拨片。','定位簧片平放打印；只防误转，刚性拨片承受压框抬起力。','闭合到硬止挡，切勿用大力压弯PCB。','装配前按实物试合角点，排针塑壳/元件密集角位应避免强扣。','建议先拆上平台再维护；开盖包络的数字检查见checks/assembly.json。'],
 'print_notes':['两大板一体成型，无切块或板件拼接。','所有独立小件直接贴床，优先在支撑框架空区套排。','额外夹具改变耗时，旧22小时45分不再作为最终估算。'],
 'unmeasured_features':['电机支架、万向球、循迹与碰撞开关实际孔距仍未提供，不声称已核实它们的安装孔。','喇叭耳片高度用可调螺母处理。','杜邦线插好后的实际弯线包络仍需实装检查。'],
 'physical_print_test':False,'load_tested':False}
(OUT/'source/design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'checks/assembly.json').write_text(json.dumps({'status':'PASS','clamps':checks,'opening_sweeps':opening,
 'main_base_single_piece':True,'main_upper_single_piece':True,'original_pillars_preserved':True,
 'mounting_hole_count':len(holes),'physical_fit_test':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Export coloured assembly as STEP, for inspection only, not a printing layout.
scene=cq.Assembly(name='ASSEMBLY_VIEW_ONLY')
scene.add(base,name='P01_mounted_base',color=cq.Color('#477e9f'))
for a in assembly:scene.add(a['shape'],name=a['id'],color=cq.Color(a['color']))
scene.save(str(OUT/'step/ASSEMBLY_VIEW_ONLY.step'))
print(json.dumps({'parts':len(parts),'base_mount_holes':len(holes),'modules':len(modules),
 'step':str(OUT/'step/P01_MOUNTED_BASE.step'),'sweep_cases':len(opening)},ensure_ascii=False),flush=True)
