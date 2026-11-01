"""Slice and export native recovery projects using an isolated official CLI.

Pass the portable CLI directory and resolved manufacturer config directory.
The user's GUI session is never accessed, and no G-code is delivered.
"""
from pathlib import Path
import argparse,json,subprocess,zipfile,hashlib
import xml.etree.ElementTree as ET

parser=argparse.ArgumentParser()
parser.add_argument('--portable',type=Path,required=True)
parser.add_argument('--config-dir',type=Path,required=True)
parser.add_argument('--work-dir',type=Path,required=True)
parser.add_argument('--only')
parser.add_argument('--model-dir',type=Path)
args=parser.parse_args()
ROOT=args.model_dir or Path(__file__).resolve().parents[1]/'parallel-four-p2s-20261101'
ROOT.joinpath('projects').mkdir(exist_ok=True)
args.work_dir.mkdir(exist_ok=True,parents=True)
load=lambda name:json.loads((args.config_dir/name).read_text(encoding='utf-8'))
machine=load('machine.json')
process=load('process.json')
filament=load('filament.json')
process.update({'name':'SmartBin Four P2S Parallel Bodies 0.24',
    'layer_height':'0.24','initial_layer_print_height':'0.2','wall_loops':'4',
    'top_shell_layers':'7','bottom_shell_layers':'7',
    'top_shell_thickness':'1.6','bottom_shell_thickness':'1.6',
    'sparse_infill_density':'30%','sparse_infill_pattern':'gyroid',
    'brim_type':'outer_only','brim_width':'5','brim_object_gap':'0',
    'initial_layer_speed':['25']*3,'initial_layer_infill_speed':['40']*3,
    'outer_wall_speed':['60']*3,'inner_wall_speed':['100']*3,
    'internal_solid_infill_speed':['140']*3,
    'default_acceleration':['1500']*3,'outer_wall_acceleration':['800']*3,
    'travel_speed':['250']*3,'travel_acceleration':['2000']*3,
    'enable_support':'0','enable_prime_tower':'0','timelapse_type':'0',
    'print_sequence':'by layer','skirt_loops':'0','enable_wrapping_detection':'0'})
filament['textured_plate_temp']=['60']
filament['textured_plate_temp_initial_layer']=['60']
for name,data in [('machine',machine),('process',process),('filament',filament)]:
    (args.work_dir/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

saved=ROOT/'checks/slicing.json'
results=json.loads(saved.read_text(encoding='utf-8'))['plates'] if args.only and saved.exists() else {}
plate_names=[p.stem for p in sorted((ROOT/'geometry').glob('*.3mf'))]
for name in plate_names:
    if args.only and args.only!=name:continue
    output=args.work_dir/name;output.mkdir(exist_ok=True)
    plate_process=dict(process)
    plate_process['brim_width']='5'
    plate_process.update({'initial_layer_infill_speed':['50']*3,
        'default_acceleration':['3000']*3,'outer_wall_acceleration':['1000']*3,
        'travel_speed':['300']*3,'travel_acceleration':['3000']*3})
    (output/'process.json').write_text(json.dumps(plate_process,ensure_ascii=False,indent=2),encoding='utf-8')
    cmd=[str(args.portable/'BambuCliHost.exe'),'--datadir',str(args.portable.parent/'isolated-data'),
         '--load-settings',str(args.work_dir/'machine.json')+';'+str(output/'process.json'),
         '--load-filaments',str(args.work_dir/'filament.json'),
         '--arrange','0','--orient','0','--slice','0','--export-3mf','sliced.3mf',
         '--outputdir',str(output),'--debug','2',str(ROOT/'geometry'/(name+'.3mf'))]
    with (output/'slice.log').open('w',encoding='utf-8') as log:
        done=subprocess.run(cmd,cwd=args.portable,stdout=log,stderr=subprocess.STDOUT)
    assert done.returncode==0,(name,done.returncode,(output/'slice.log').read_text(encoding='utf-8',errors='replace')[-3000:])
    result=json.loads((output/'result.json').read_text(encoding='utf-8'))
    plate=result['sliced_plates'][0]
    assert result['return_code']==0 and not plate['warning_message'],result
    printer=int(name.split('_')[1])+1
    label={2:'BASE_REAR',3:'BASE_FRONT',4:'UPPER',5:'STAND_SPEAKER_BRIDGES'}[printer]
    native_name=f'P2S_PRINTER_{printer:02d}_{label}.3mf'
    index=cmd.index('--slice');del cmd[index:index+2]
    cmd[cmd.index('--export-3mf')+1]=native_name
    cmd[cmd.index('--outputdir')+1]=str(ROOT/'projects')
    with (output/'native_export.log').open('w',encoding='utf-8') as log:
        done=subprocess.run(cmd,cwd=args.portable,stdout=log,stderr=subprocess.STDOUT)
    assert done.returncode==0
    native=ROOT/'projects'/native_name
    with zipfile.ZipFile(native) as archive,zipfile.ZipFile(output/'sliced.3mf') as tested:
        assert archive.testzip() is None and not any(n.endswith('.gcode') for n in archive.namelist())
        model_files=[n for n in archive.namelist() if n.endswith('.model')]
        for item in model_files:assert archive.read(item)==tested.read(item),item
        cfg=json.loads(archive.read('Metadata/project_settings.config'))
        assert cfg['print_sequence']=='by layer' and cfg['wall_loops']=='4'
        assert cfg['layer_height']=='0.24' and cfg['brim_object_gap']=='0'
        assert cfg['textured_plate_temp']==['60']
        assert cfg['enable_wrapping_detection']=='0'
        assert cfg['z_hop'][0]=='0.4'
        xml=ET.fromstring(archive.read('3D/3dmodel.model'))
        ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        count=len(xml.findall('m:build/m:item',ns))
        with zipfile.ZipFile(ROOT/'geometry'/(name+'.3mf')) as source:
            original_xml=ET.fromstring(source.read('3D/3dmodel.model'))
            expected_count=len(original_xml.findall('m:build/m:item',ns))
        assert count==expected_count
    import re
    with zipfile.ZipFile(output/'sliced.3mf') as tested:
        code='\n'.join(tested.read(n).decode('utf-8',errors='replace') for n in tested.namelist() if n.endswith('.gcode'))
        assert code and not re.search(r'^\s*G39(?:\s|;|$)',code,re.M),'Nozzle wrapping detection must stay disabled for this layout.'
    results[name]={'estimated_seconds':plate['total_predication'],
        'filament_g':sum(f['total_used_g'] for f in plate['filaments']),
        'return_code':result['return_code'],'warning_message':plate['warning_message'],
        'feature_type_times':plate['feature_type_times'],'native_project':native_name,
        'native_contains_gcode':False,'native_geometry_and_positions_match_tested':True,
        'object_count':count,'nozzle_wrapping_detection_disabled':True,
        'gcode_has_no_G39_command':True,'sha256':hashlib.sha256(native.read_bytes()).hexdigest()}
    results[name]['process']=plate_process
    print(json.dumps({name:{k:v for k,v in results[name].items() if k!='process'}},ensure_ascii=False),flush=True)

results=dict(sorted(results.items()))
report={'parallel_elapsed_seconds_if_started_together':max(r['estimated_seconds'] for r in results.values()),'status':'PASS','bambu_studio_version':'02.08.02.61','machine':'Bambu Lab P2S 0.4 nozzle',
        'material':'Generic PLA','plates':results,'total_estimated_seconds':sum(r['estimated_seconds'] for r in results.values()),
        'total_filament_g':sum(r['filament_g'] for r in results.values()),
        'process_changes':process,'physical_print_test':False,
        'baseline_fast_four_upright_estimated_seconds':83025.5,
        'comparison_note':'Historical four-part 0.20-mm speed profile; failed physically. Four independent tasks run concurrently; each includes its own start/end scripts. Manual plate swap time is excluded.',
        'stock_end_script_note':'Official P2S T65535 stock end command triggers a CLI parser note; stock script unchanged; return code zero and no sliced G-code is delivered.'}
(ROOT/'checks/slicing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={'status':'PASS','slicer_version':'Bambu Studio 02.08.02.61','plates':[{'file':'projects/'+r['native_project'],
    'objects':r['object_count'],'estimated_seconds':r['estimated_seconds'],'filament_g':r['filament_g']}
    for r in results.values()], 'total_seconds':report['total_estimated_seconds'],
    'total_filament_g':report['total_filament_g'],
    'parallel_elapsed_seconds_if_started_together':report['parallel_elapsed_seconds_if_started_together'],
    'settings':{'printer':'P2S 0.4 mm','material':'Generic PLA','layer_height_mm':.24,
                'wall_loops':4,'infill':'30% gyroid','auto_support':False,
                'sequence':'by layer','brim_mm':5,'nozzle_wrapping_detection':False},
    'notes':['保持工程位置，禁止自动排盘/自动朝向和逐件打印。',
             '喷嘴缠料检测关闭；相机炒面检测为独立功能，应保持开启。',
             '四项任务可在四台P2S同时运行，均含机器起止脚本；并行等待时间取最长项。',
             '仅补打附件精细盘之外的8件：底板两片、连接片三块、上平台、舵机支架、喇叭圈。'],
    'physical_print_test':False,'unprinted':True,'load_tested':False}
(ROOT/'checks/final_printing.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total_hours':report['total_estimated_seconds']/3600,'total_filament_g':report['total_filament_g']},ensure_ascii=False),flush=True)
