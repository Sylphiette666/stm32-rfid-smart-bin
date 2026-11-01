"""Publish checked motor adapter files and the reviewed manual, with hash guards."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

R = Path(__file__).resolve().parents[4]
B = R / 'hardware/mechanical/print-backup'
O = B / 'motor-adapter-20261101'
W = R.parent / '.p2s-motor-adapter-20261101/manual'
N = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

parser = argparse.ArgumentParser()
parser.add_argument('--checked-pages', required=True)
a = parser.parse_args()
checked = sorted(int(n) for n in a.checked_pages.split(','))
audit = load(W / 'raster_audit.json')
assert checked == audit['changed_pages']
assert audit['original_steps_preserved'] == 330 and audit['original_tables_preserved'] == 78
assert sha(W/N) == audit['docx_sha256']
targets = [R/'docs/manual'/N, R.parent/N]
assert all(sha(p) in [audit['baseline_sha256'], audit['docx_sha256']] for p in targets)
design = load(O/'checks/design.json')
assert design['closed_valid_solids'] and design['watertight_meshes'] and design['proven_coupon_material_preserved']
assert design['head_height_measured_mm'] == 5 and design['head_cavity_mm'] == 6
assert not design['text_on_part'] and not design['base_drilling_authorized_by_this_drawing']
slice_report = load(O/'checks/slicing.json')
assert slice_report['status'] == 'PASS' and slice_report['native_matches_tested']
assert not slice_report['warning_message']
first = load(O/'checks/first_layers.json')['1']
assert first['objects_with_first_layer_id'] == 2 and first['all_model_extrusions_within_bed'] and first['G39_absent']
project = O/'P2S_D06_ADAPTER_PAIR_028.3mf'
with zipfile.ZipFile(project) as z:
    assert z.testzip() is None
    assert not any(n.endswith('.gcode') for n in z.namelist())
    cfg = json.loads(z.read('Metadata/project_settings.config'))
    assert cfg['layer_height'] == '0.28' and cfg['wall_loops'] == '4'
    assert cfg['sparse_infill_density'] == '40%' and cfg['print_sequence'] == 'by layer'
for p in targets:
    shutil.copy2(W/N, p)
audit.update(visual_qa_pending=False, visually_checked_pages=checked, published_copies_match=True, status='PASS')
save(O/'checks/manual_qa.json', audit)
save(O/'checks/visual_review.json', {'status':'PASS', 'actual_first_layer_reviewed':True,
    'installation_diagram_reviewed':True, 'physical_load_test':False})
readme = O/'README.md'
t = readme.read_text(encoding='utf-8').replace('图解已准备合入同名手册66.10节，发布状态以checks/manual_qa.json为准。', '图解64已合入同名手册66.10节，226页已渲染检查，原330步骤保留；记录见checks/manual_qa.json。')
readme.write_text(t, encoding='utf-8', newline='\n')
nav = B/'README.md'
t = nav.read_text(encoding='utf-8')
if 'motor-adapter-20261101/README.md' not in t:
    t = '# D06电机正式转接座\n\n[打印两件转接座并查看安装说明](motor-adapter-20261101/README.md)：保留试配成功的3mm穿槽面，宽头腔6mm，无字；两件同盘约46分30秒、16.3g。先装完整轮组试摆，再确定底板孔位。\n\n'+t
nav.write_text(t, encoding='utf-8', newline='\n')
assembly = R/'docs/manual/ASSEMBLY.md'
t = assembly.read_text(encoding='utf-8')
if '### 66.10' not in t:
    t += '\n### 66.10 电机穿槽转接座\n\n[打印文件及安装说明](../../hardware/mechanical/print-backup/motor-adapter-20261101/README.md)：两种座各一件，P2S/0.4mm、0.28mm层高，约46分30秒、16.3g。已实物确认的槽12×2.4mm、中心距21mm、承托厚3mm保持；T形头高5mm，名义腔高6mm，电机接触面无字。分耳座用于非舵机侧，偏耳座用于舵机侧，四孔翼朝车头。先装固定片、电机、轮子并放到底板下试摆，确认轮胎净隙、两轴共线及五金避让，再确定孔位；暂不按候选坐标钻孔。后续两座合计8颗M3×20低圆头螺栓、16片外径≤6mm厚0.5mm垫圈、8颗约4mm高锁紧螺母，贯穿底板实心区固定。完整轮组、承重和行驶尚未验证。图解64已同步同名Word。\n'
assembly.write_text(t, encoding='utf-8', newline='\n')
attrs = R/'.gitattributes'
prefix = O.relative_to(R).as_posix()
t = attrs.read_text(encoding='utf-8')
if prefix+'/** -text' not in t:
    t += '\n# D06 motor adapter checked exports\n'+prefix+'/** -text\n'+prefix+'/parts/** binary\n'+prefix+'/step/** binary\n'+prefix+'/*.3mf binary\n'
attrs.write_text(t, encoding='utf-8', newline='\n')
sources = [B/'source'/f'{s}.py' for s in ['build_motor_adapter','render_motor_adapter','update_motor_adapter_manual','check_motor_adapter_layers','check_motor_adapter_manual','finalize_motor_adapter_release']]
normal = sources+[attrs, nav, assembly]
for p in O.rglob('*.json'):
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
for p in normal:
    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
save(O/'checks/release.json', {'status':'PASS', 'project':project.name, 'project_sha256':sha(project),
    'estimated_seconds':slice_report['estimated_seconds'], 'filament_g':slice_report['filament_g'],
    'manual_sha256':sha(targets[0]), 'manual_visually_checked':True, 'printer_jobs_sent':False,
    'full_motor_wheel_fit_tested':False, 'load_tested':False})
files = sorted(p for p in O.rglob('*') if p.is_file() and p.name != 'SHA256.json')
save(O/'checks/SHA256.json', {p.relative_to(O).as_posix():sha(p) for p in files})
manifest = R/'MANIFEST.sha256'
entries = {l.split('  ',1)[1]:l.split('  ',1)[0] for l in manifest.read_text(encoding='utf-8').splitlines() if '  ' in l}
for p in normal+[targets[0]]+[p for p in O.rglob('*') if p.is_file()]:
    entries[p.relative_to(R).as_posix()] = sha(p)
manifest.write_text(''.join(f'{v}  {k}\n' for k,v in sorted(entries.items())), encoding='utf-8', newline='\n')
print(json.dumps(load(O/'checks/release.json'), ensure_ascii=False))
