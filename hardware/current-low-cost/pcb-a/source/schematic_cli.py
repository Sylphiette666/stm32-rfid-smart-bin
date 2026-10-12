"""Project-local kicad-tool extension: structured schematic generation.

No raw S-expression edits: kiutils objects serialize symbols, sheets and wires.
Run with the isolated tooling venv. The upstream CLI remains available.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
TOOLING = HERE.parents[1] / 'tooling'
sys.path.insert(0, str(TOOLING / 'kicad-skills/skills/kicad-tool/scripts'))
import kicad_tool as upstream
from kiutils.schematic import Schematic
from kiutils.symbol import Symbol, SymbolLib
from kiutils.libraries import LibTable, Library
from kiutils.items.common import Position, Property, Effects, Font, Justify, TitleBlock, PageSettings, Stroke
from kiutils.items.schitems import (SchematicSymbol, SymbolProjectInstance, SymbolProjectPath,
    HierarchicalSheet, HierarchicalSheetProjectInstance, HierarchicalSheetProjectPath,
    HierarchicalSheetInstance, GlobalLabel, Connection, NoConnect, Text)

LIB_ROOT = Path(os.environ.get('KICAD_SYMBOL_DIR', 'D:/KiCad/share/kicad/symbols'))
NAMESPACE = uuid.UUID('9fd74206-b6db-4390-845b-12c12f476427')
PROJECT = 'SmartBin_A'
LIB = 'SmartBin_A'
PAGE_GROUPS = {
    'power':'01 Power distribution and ADC', 'adc':'01 Power distribution and ADC', 'MECHANICAL':'01 Power distribution and ADC',
    'core':'02 MCU, MCP23017 and emergency stop', 'mcp':'02 MCU, MCP23017 and emergency stop',
    'estop':'02 MCU, MCP23017 and emergency stop','motor':'02 MCU, MCP23017 and emergency stop',
    'i2c':'03 Serial module interfaces','spi':'03 Serial module interfaces','uart':'03 Serial module interfaces','voice':'03 Serial module interfaces',
    'ahct':'04 Buffered outputs and actuators','ultrasonic':'04 Buffered outputs and actuators','led':'04 Buffered outputs and actuators','buzzer':'04 Buffered outputs and actuators',
    'switches':'05 Sensor and user inputs','digital_inputs':'05 Sensor and user inputs','encoder':'05 Sensor and user inputs','dht':'05 Sensor and user inputs',
}
ROOT_UUID = str(uuid.uuid5(NAMESPACE, 'root'))
LIBRARIES = {}
LIB_SYMBOLS = {}

def uid(name): return str(uuid.uuid5(NAMESPACE, name))
def pos(x, y, a=0): return Position(round(x,6), round(y,6), a)
def effects(size=1.0, hide=False, bold=False, just=None):
    return Effects(font=Font(height=size,width=size,bold=bold), hide=hide,
        justify=Justify(horizontally=just))
def prop(key,value,x,y,hide=False,size=1.0):
    return Property(key=key,value=str(value),position=pos(x,y),effects=effects(size,hide))

def load_symbol(lib_id):
    """Resolve standard inheritance into an independent, portable local symbol."""
    if lib_id in LIB_SYMBOLS: return copy.deepcopy(LIB_SYMBOLS[lib_id])
    lname, name = lib_id.split(':',1)
    if lname not in LIBRARIES:
        LIBRARIES[lname] = SymbolLib.from_file(str(LIB_ROOT / f'{lname}.kicad_sym'))
    source = next(s for s in LIBRARIES[lname].symbols if s.entryName == name)
    if source.extends:
        resolved = load_symbol(f'{lname}:{source.extends}')
        resolved.properties = copy.deepcopy(source.properties)
    else: resolved = copy.deepcopy(source)
    local_name = lname + '_' + name
    resolved.libraryNickname = None
    resolved.entryName = local_name
    resolved.extends = None
    for unit in resolved.units:
        unit.libraryNickname = None
        unit.entryName = local_name
    LIB_SYMBOLS[lib_id] = copy.deepcopy(resolved)
    return resolved

def sym_units(symbol):
    ids = sorted({s.unitId for s in symbol.units if s.unitId and (s.pins or s.graphicItems)})
    return ids or [1]

def unit_pins(symbol, unit):
    pins = list(symbol.pins)
    for u in symbol.units:
        if u.unitId in (0,unit) and u.styleId in (0,1): pins.extend(u.pins)
    return pins

def add_text(sch,text,x,y,size=1.1,bold=False):
    sch.texts.append(Text(text=text,position=pos(x,y),effects=effects(size,bold=bold,just='left'),uuid=uid(sch.uuid+'/text/'+text+str(x)+str(y))))

def add_wire(sch,p1,p2,key):
    sch.graphicalItems.append(Connection(type='wire',points=[pos(*p1),pos(*p2)],stroke=Stroke(width=0,type='default'),uuid=uid(key)))

def add_label(sch,net,x,y,angle,key):
    # KiCad's passive global labels use left justification at 0/90, right at 180/270.
    sch.globalLabels.append(GlobalLabel(text=net,shape='passive',position=pos(x,y,angle),
        effects=effects(0.95,just='left' if angle in (0,90) else 'right'),uuid=uid(key),
        properties=[prop('Intersheetrefs','${INTERSHEET_REFS}',x,y,True)]))

def transformed(x,y,angle,sx,sy):
    a=math.radians(angle)
    return (round(sx+x*math.cos(a)-y*math.sin(a),6), round(sy-x*math.sin(a)-y*math.cos(a),6))

def part_height(part,sym):
    pins=unit_pins(sym,1)
    if part['ref'].startswith(('R','C')): return 24.0
    if len(sym_units(sym))>1: return 45.0
    ys=[p.position.Y for p in pins] or [0]
    return max(30.0,max(ys)-min(ys)+21)

def add_part(sch,part,sym,x,y,sheet_path,paths,unit=1):
    x=round(x/1.27)*1.27; y=round(y/1.27)*1.27
    angle=90 if part['ref'].startswith(('R','C')) else 0
    ref=part['ref']; cuuid=uid('component/'+ref if unit==1 else f'component/{ref}/unit{unit}')
    allpins=unit_pins(sym,unit)
    pins=part['pins']
    embedded=copy.deepcopy(sym);embedded.libraryNickname=LIB
    if not any(s.entryName==embedded.entryName for s in sch.libSymbols): sch.libSymbols.append(embedded)
    instance=SchematicSymbol(libraryNickname=LIB,entryName=sym.entryName,position=pos(x,y,angle),unit=unit,
        inBom=not ref.startswith('#'),onBoard=not ref.startswith('#'),dnp=bool(part.get('dnp',False)),uuid=cuuid,
        pins={p.number:uid(ref+'/'+p.number) for p in allpins},
        instances=[SymbolProjectInstance(name=PROJECT,paths=[SymbolProjectPath(sheetInstancePath=sheet_path,reference=ref,unit=unit)])])
    # Reference and value above the symbol; hidden provenance fields remain editable.
    top=min([transformed(p.position.X,p.position.Y,angle,x,y)[1] for p in allpins] or [y])
    label_y = top-8.89
    if ref.startswith(('R','C')): label_y=y-5.08
    if ref.startswith('C'): label_y=y-6.35
    if len(sym_units(sym))>1: label_y=top-11.43
    instance.properties=[prop('Reference',ref,x,label_y,False,1.1),prop('Value',part['value'],x,label_y+2.54,False,1.0),
        prop('Footprint',part.get('footprint',''),x,y,True),prop('Datasheet',part.get('datasheet',''),x,y,True),
        prop('Description',part.get('notes',''),x,y,True)]
    if angle:
        for p in instance.properties[:2]: p.position.angle=angle
    for key in ('MPN','Manufacturer','Assembly','group'):
        if key in part: instance.properties.append(prop(key,part[key],x,y,True))
    sch.schematicSymbols.append(instance)
    for p in allpins:
        px,py=transformed(p.position.X,p.position.Y,angle,x,y)
        net=pins.get(p.number)
        if net is None:
            sch.noConnects.append(NoConnect(position=pos(px,py),uuid=uid(ref+'/'+p.number+'/nc')))
            continue
        pa=(p.position.angle+angle)%360
        # Extend outward from pin. Vertical pins dog-leg to the right for readable text.
        dx=-math.cos(math.radians(pa));dy=math.sin(math.radians(pa))
        if abs(dx)>0.5:
            ex=px+dx*7.62;ey=py
            add_wire(sch,(px,py),(ex,ey),ref+'/'+p.number+'/wire')
            la=0 if dx>0 else 180
        else:
            ex=px+7.62;ey=py+dy*5.08
            add_wire(sch,(px,py),(px,ey),ref+'/'+p.number+'/wire1')
            add_wire(sch,(px,ey),(ex,ey),ref+'/'+p.number+'/wire2')
            la=0
        add_label(sch,net,ex,ey,la,ref+'/'+p.number+'/label')
    if not ref.startswith('#') and unit==1:
        paths[ref]={'uuid':cuuid,'sheet_uuid':sch.uuid,'sheet_path':sheet_path,'path':sheet_path+'/'+cuuid,
            'sheet_file':Path(sch.filePath).name,'value':part['value'],'footprint':part.get('footprint','')}

def new_sheet(title,index,file):
    sch=Schematic.create_new();sch.version='20250114';sch.generator='kicad-tool';sch.generatorVersion='1.0'
    sch.uuid=uid('sheet/'+file);sch.paper=PageSettings(paperSize='A3')
    sch.filePath=str(file);sch.sheetInstances=[]
    sch.titleBlock=TitleBlock(title='SmartBin A / '+title,date='2026-10-12',revision='A1',company='STM32 + RFID / DIY through-hole carrier',
        comments={1:'Existing external modules; cable connected; all named nets are global.',2:'Prototype: verify polarity and module pin order before connection.'})
    add_text(sch,title.upper(),15,16,2,bold=True)
    add_text(sch,'A1 | Bare PCB + hand soldering | Existing assembled modules remain external',15,22,1.15)
    return sch

def cmd_build(args):
    spec=json.loads(Path(args.circuit).read_text(encoding='utf-8-sig'))
    parts=spec.get('parts',spec.get('components',[]))
    if args.dry_run:
        print(json.dumps({'dry_run':True,'parts':len(parts),'groups':sorted({p.get('group','other') for p in parts})},ensure_ascii=False,indent=2));return 0
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    groups={}
    for p in parts:
        group=p.get('group','Other');groups.setdefault(PAGE_GROUPS.get(group,group),[]).append(p)
    groups=dict(sorted(groups.items()))
    paths={}; sheets=[]
    for gi,(group,gparts) in enumerate(groups.items(),1):
        page=1;sch=None;col=0;cursor=38
        for p in gparts:
            sym=load_symbol(p['symbol']);units=sym_units(sym)
            for unit in units:
                height=part_height(p,sym)
                if sch is None or (cursor+height>258 and col==3):
                    filename=f'SmartBin_A_{gi:02}_{page:02}.kicad_sch'
                    sch=new_sheet(group,gi,filename);sch.filePath=str(out/filename)
                    sheets.append((group,sch));page+=1;col=0;cursor=38
                elif cursor+height>258: col+=1;cursor=38
                cx=60+col*98
                pins=unit_pins(sym,unit)
                ymax=max([q.position.Y for q in pins] or [0])
                cy=cursor+9+(ymax if not p['ref'].startswith(('R','C')) else 0)
                add_part(sch,p,sym,cx,cy,'/'+ROOT_UUID+'/'+sch.uuid,paths,unit)
                cursor+=height
    # Inject power-source declarations without adding fabricated components to the BOM.
    known_nets={v for p in parts for v in p['pins'].values() if v is not None}
    power_flags=spec.get('power_flags',[n for n in ['GND','VBAT_SW','5V_BUS','5V_LOGIC','3V3_EXT','3V3_CORE'] if n in known_nets])
    for i,net in enumerate(power_flags,1):
        first=sheets[0][1];sym=load_symbol('power:PWR_FLAG')
        p={'ref':f'#FLG{i:03}','value':'PWR_FLAG','pins':{'1':net},'footprint':''}
        add_part(first,p,sym,32+(i-1)*58,272,'/'+ROOT_UUID+'/'+first.uuid,paths)
    top=new_sheet('System index',0,'SmartBin_A.kicad_sch');top.uuid=ROOT_UUID;top.filePath=str(out/'SmartBin_A.kicad_sch')
    top.sheetInstances=[HierarchicalSheetInstance(instancePath='/',page='1')]
    add_text(top,'PROJECT STRUCTURE',20,38,1.5,True)
    for i,(name,sch) in enumerate(sheets):
        x=25+(i%2)*190;y=54+(i//2)*37
        sheet_name=prop('Sheetname',f'{i+2:02} {name}',x+5,y+5,size=1.2)
        sheet_file=prop('Sheetfile',Path(sch.filePath).name,x+5,y+14,size=1.1)
        sheet_name.effects.justify=Justify(horizontally='left')
        sheet_file.effects.justify=Justify(horizontally='left')
        top.sheets.append(HierarchicalSheet(position=pos(x,y),width=160,height=20,uuid=sch.uuid,
            sheetName=sheet_name,fileName=sheet_file,
            instances=[HierarchicalSheetProjectInstance(name=PROJECT,paths=[HierarchicalSheetProjectPath(sheetInstancePath='/'+ROOT_UUID,page=str(i+2))])]))
        sch.to_file()
    add_text(top,'Assembly guidance and external module connections are specified in the accompanying manual.',20,255,1.2)
    add_text(top,'Do not connect the core 3.3 V rail in parallel with the external 3.3 V regulator.',20,262,1.2)
    top.to_file()
    SymbolLib(version='20211014',generator='kicad-tool',symbols=list(LIB_SYMBOLS.values())).to_file(str(out/'SmartBin_A.kicad_sym'))
    LibTable(type='sym_lib_table',libs=[Library(name=LIB,type='KiCad',uri='${KIPRJMOD}/SmartBin_A.kicad_sym',description='Self-contained resolved symbols for SmartBin A')]).to_file(str(out/'sym-lib-table'))
    (out/'schematic_paths.json').write_text(json.dumps({'root_uuid':ROOT_UUID,'project':PROJECT,'components':paths},ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'schematic':str(out/'SmartBin_A.kicad_sch'),'parts':len(paths),'sheets':len(sheets)+1,'symbols':len(LIB_SYMBOLS)}
    print(json.dumps(summary,ensure_ascii=False,indent=2));return 0

def cmd_export(args):
    source=Path(args.schematic).resolve();dest=Path(args.output).resolve();dest.mkdir(parents=True,exist_ok=True)
    cli=upstream.kicad_cli()
    calls=[['sch','export','netlist','--format','kicadxml','--output',str(dest/'SmartBin_A.net.xml'),str(source)],
           ['sch','export','pdf','--output',str(dest/'SmartBin_A_schematic.pdf'),str(source)],
           ['sch','export','svg','--output',str(dest/'schematic-svg'),str(source)],
           ['sch','erc','--format','json','--output',str(dest/'schematic-erc.json'),str(source)],
           ['sch','erc','--format','report','--output',str(dest/'schematic-erc.rpt'),str(source)]]
    results=[]
    for cmd in calls:
        p=subprocess.run([cli]+cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        results.append({'argv':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    (dest/'schematic-export-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    erc_path=dest/'schematic-erc.json'
    erc=json.loads(erc_path.read_text(encoding='utf-8')) if erc_path.exists() else {}
    count=sum(len(s.get('violations',[])) for s in erc.get('sheets',[]))
    print(json.dumps({'results':results,'erc_violations':count},ensure_ascii=False,indent=2))
    return 0 if all(r['returncode']==0 for r in results) and erc_path.exists() and count==0 else 1

def main():
    parser=upstream.build_parser()
    action=next(a for a in parser._actions if isinstance(a,argparse._SubParsersAction))
    project=action.add_parser('project',help='Project-local structural KiCad generators')
    sub=project.add_subparsers(dest='project_command',required=True)
    build=sub.add_parser('sch-build',help='Build hierarchical schematic using structured kiutils objects')
    build.add_argument('circuit');build.add_argument('output');build.add_argument('--dry-run',action='store_true');build.set_defaults(func=cmd_build)
    export=sub.add_parser('sch-export',help='Export netlist, PDF, SVG and ERC from the top-level schematic')
    export.add_argument('schematic');export.add_argument('output');export.set_defaults(func=cmd_export)
    args=parser.parse_args()
    return args.func(args)

if __name__=='__main__': raise SystemExit(main())
