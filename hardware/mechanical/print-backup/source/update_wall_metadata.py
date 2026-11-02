"""Reconcile measured requirements with implemented interfaces; no physical-fit claims."""
from pathlib import Path
import json
B=Path(__file__).resolve().parents[1]; O=B/'wall-panels-20261102'; W=B.parents[2].parent/'.p2s-wall-panels-20261102'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=load(O/'source/measurements.json')
m['status']='MEASURED_ENVELOPES_IMPLEMENTED_PHYSICAL_FIT_PENDING'
m['requirements']['bag_and_bottom_arrangement']='No bag or liner. Existing P02 continuous face UP supports bare bin; digital surface check passed, not waterproof.'
m['emergency_stop_product_drawing']['open_issues']=[x for x in m['emergency_stop_product_drawing']['open_issues'] if not x.startswith('Confirm22')]
m['design_direction_not_validated']['bottom']=m['requirements']['bag_and_bottom_arrangement']
m['design_direction_not_validated']['strength_or_print_time_claim']='Four CLI slices passed; estimated time is in checks/slicing.json; physical strength and fit remain unverified.'
save(O/'source/measurements.json',m)
if W.exists():save(W/'measurements.json',m)
c=load(O/'checks/component_coverage.json')
c['status']='IMPLEMENTED_AND_DIGITALLY_CHECKED_PHYSICAL_FIT_PENDING'
changes={
'靠近开盖红外':('前壁上部外侧水平托架','31×20板边缘压条，右端探头伸出10mm，排针侧开放','按实测外形完成；实际光轴及插头仍需试装'),
'投放对射TX/RX':('左右壁外侧，光轴v150mm','9×17光窗、竖向长孔和外壳夹座；不使用歧义孔径','20×10×9外壳已建模；不用内胆和袋；需实测对射对准'),
'DHT11':('左壁外侧','裸探头通风罩及开放下端出线','已按12×16×6mm裸蓝色探头完成'),
'光敏':('左壁外侧','边缘夹座和可拆压条，左针右探头开放','已按28×20×2mm和正面高9mm完成；插线空间实物复核'),
'HC-SR04':('桶内后上方可拆横梁，横梁底v162mm','43.4×18.9探头避让口和引线缺口、PCB边缘压条','按45×20.5板外形设计；不使用Ø1.5安装孔，探头包络试装'),
'闭盖微动开关':('前壁内侧上方','竖向长孔调节片、9.5mm孔距M2螺钉、独立触片','侧视尺寸建模；模块厚度和实际行程需试装'),
'独立电源总开关':('左壁下部外置接线盒','KCD1可换2mm安装片、19.4×12.4试配孔','按商品外形完成；卡扣夹持厚度和后部接线需试装'),
'主线束/传感线':('外壁及操作腔下方','26×12腔底开口及4组可拆线夹','已建模；实际线束须绝缘及固定，不依赖未量的护线圈'),
'裸桶腔/桶底':('现有上平台P02连续面朝上','四壁连续内侧薄面及平台底面','内腔底面连续性检查通过；不防水，不用内胆/袋'),
'壁板连接/平台固定':('四角外侧及左右底脚','8角码及4底脚；P02四候选孔处5mm完整材料','已完成实体、摆盘和路径检查；平台实物试摆后钻孔')}
for a in c['items']:
 if a['item'] in changes:a['location'],a['mounts_or_openings'],a['evidence_status']=changes[a['item']]
 if a['item']=='投放对射TX/RX':a['constraint']='光轴距桶口30mm；同轴调节后做遮挡测试'
 if a['item']=='HC-SR04':a['constraint']='探头向下且不随盖转；横梁可拆，保留清理通道'
 if a['item']=='裸桶腔/桶底':a['constraint']='不作防水或密封容器承诺'
c['release_gate']='CAD, assembly, slicing, toolpath and manual QA; physical fits and sensor performance remain first-article checks.'
save(O/'checks/component_coverage.json',c)
p=O/'README.md';t=p.read_text(encoding='utf-8-sig').replace('使用各零件外侧视图左下角作为u/v原点','壁板使用外侧视图、操作面板使用背面视图的左下角作为u/v原点')
p.write_text(t,encoding='utf-8')
print('Measured requirements and coverage reconciled')
