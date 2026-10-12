"""Independent read-only netlist review; writes evidence only in this directory."""
import csv, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / 'circuit.json'
OLD = Path('D:/Work/嵌入式课设/stm32-rfid-smart-bin/hardware/current-low-cost/perfboard/layout.json')
d = json.loads(SRC.read_text(encoding='utf-8-sig'))
old = json.loads(OLD.read_text(encoding='utf-8-sig'))
p = {x['ref']: x for x in d['parts']}
results = []

def check(name, ok, details=''):
    results.append({'check': name, 'status': 'PASS' if ok else 'REVIEW', 'details': details})

def pins(ref, expected):
    check('pins:'+ref, p[ref]['pins'] == expected, p[ref]['pins'])

check('unique references', len(p)==len(d['parts']))
check('33 features', len(d['features'])==33)
expected_gpio = {f'PA{x}' for x in range(16) if x not in (13,14)} | {f'PB{x}' for x in range(16) if x != 2}
check('29 assigned MCU GPIO', set(d['mcu_pin_map'])==expected_gpio)
check('no bit7 external nets', not any(n in ('MCP_GPA7','MCP_GPB7') for c in p.values() for n in c['pins'].values()))
check('MCP bit7 output restrictions documented', all('OUTPUT LOW' in d['mcp_pin_map'][n] for n in ('GPA7','GPB7')))
pins('Q1', {'1':'GND','2':'ES1_BASE','3':'KILL_BASE'})
pins('Q2', {'1':'GND','2':'KILL_BASE','3':'STBY_OUT'})
pins('Q3', {'1':'GND','2':'ES2_BASE','3':'PB13'})
pins('U1', {'1':'GND','2':'PA0','3':'SERVO_SIG_5V','4':'GND','5':'PB15','6':'US_TRIG_5V','7':'GND','8':'BUZZ_5V','9':'PB9','10':'GND','11':None,'12':'GND','13':'5V_BUS','14':'5V_BUS'})
check('AHCT PB9 defined while core reset', sum(not p[r]['dnp'] for r in ('R36','R37')) == 1)
check('AHCT direct wiring removes JP1 JP2', 'JP1' not in p and 'JP2' not in p)
pins('J10', {'1':'3V3_EXT','2':'GND','3':'I2C_SCL','4':'I2C_SDA','5':'MCP_RESET_N'})
pins('J15', {'1':'3V3_EXT','2':'GND','3':'PA4','4':'PA5','5':'PA7','6':'PA6','7':'MCP_GPA4'})
pins('J16', {'1':'3V3_EXT','2':'GND','3':'PA15','4':'PA5','5':'PA7','6':'PA6','7':'FLASH_WP_N','8':'FLASH_HOLD_N'})
pins('J19', {'1':'3V3_EXT','2':'GND','3':'MCP_GPA0','4':'MCP_GPA1','5':'MCP_GPA2','6':'MCP_GPA3','7':'PA8','8':'PA11','9':'STBY_OUT'})
pins('J23', {'1':'3V3_EXT','2':'5V_BUS','3':'GND','4':'PB11','5':'DHT_DATA_RAW'})
pins('J27', {'1':'VBAT_SW','2':'ESTOP_NC1_RETURN','3':'VBAT_SW','4':'ESTOP_NC2_RETURN'})
pins('J28', {'1':'LED_GATE','2':'GND','3':'LED_NEG'})
pins('J33', {'1':'3V3_EXT','2':'5V_BUS','3':'GND','4':'MCP_GPB0','5':'MCP_GPB1','6':'MCP_GPB2','7':'MCP_GPB3','8':'PB8','9':'PA12'})
check('I2C aliases physically in core header', p['J9']['pins']['7']=='I2C_SCL' and p['J9']['pins']['8']=='I2C_SDA')
core_pins = set(p['J8']['pins'].values()) | set(p['J9']['pins'].values())
check('all assigned MCU nets reach core connectors', all(i['net'] in core_pins for i in d['mcu_pin_map'].values()))
expected_up = {'R8':'3V3_EXT','R9':'3V3_EXT','R10':'3V3_EXT','R11':'3V3_EXT','R12':'3V3_EXT','R13':'3V3_EXT','R14':'3V3_EXT','R24':'3V3_CORE','R27':'3V3_CORE','R28':'3V3_CORE','R29':'3V3_EXT','R31':'3V3_CORE','R32':'3V3_CORE','R33':'3V3_EXT','R34':'3V3_EXT','R35':'3V3_EXT','R37':'3V3_CORE'}
check('all pull-up domains', all(rail in p[r]['pins'].values() for r,rail in expected_up.items()))
check('no direct CORE-EXT passive bridge', not any(set(x['pins'].values())=={'3V3_CORE','3V3_EXT'} for x in p.values()))
rows = list(csv.DictReader((SRC.parent/'connector-map.csv').open(encoding='utf-8-sig', newline='')))
csvnets = {(r['Ref'],r['PCB_pin']):r['Net'] for r in rows}
expected_csv = {(x['ref'],k):v for x in p.values() if x['kind'] in ('connector','jumper') for k,v in x['pins'].items()}
check('CSV connector pin exact match', csvnets == expected_csv, {'csv_pins':len(csvnets),'expected_pins':len(expected_csv)})
check('connector targets exact key match', all(set(c['targets'])==set(p[c['ref']]['pins']) for c in d['connectors']))

# Compare preserved 44 electrical pieces, independently of the generator's check.
oldparts = {bid+':'+x['ref']:x for bid,b in old['boards'].items() for x in b['components'] if x['kind'] in ('R','C','electrolytic','npn','ic','logic','dip') or x['ref']=='U1'}
neworiginal = {x['original_ref']:x for x in p.values() if x.get('original_ref')}
check('all original 44 electrical refs mapped', set(oldparts)==set(neworiginal) and len(oldparts)==44, {'old_count':len(oldparts),'new_count':len(neworiginal),'missing':sorted(set(oldparts)-set(neworiginal))})
aliases = {'5V_LOGIC':'5V_BUS','BAT_ADC':'BAT_ADC_DIV','SCL':'I2C_SCL','SDA':'I2C_SDA','MCP_RESET':'MCP_RESET_N','NC1_RETURN':'ESTOP_NC1_RETURN','NC2_RETURN':'ESTOP_NC2_RETURN','ECHO_RAW':'US_ECHO_RAW','WP_N':'FLASH_WP_N','HOLD_N':'FLASH_HOLD_N','LED_CTRL':'MCP_GPA5'}
changes=[]
for ref,a in oldparts.items():
    b=neworiginal[ref]
    av=a['value'].replace(' 1%','').replace('R','')
    bv=b['value'].replace(' 1%','').replace('R','')
    an=[aliases.get(x['net'],x['net']) for x in a['pins']]
    bn=list(b['pins'].values())
    if av != bv or sorted(an,key=str) != sorted(bn,key=str):
        changes.append({'original':ref,'new':b['ref'],'value_old':a['value'],'value_new':b['value'],'nets_old_normalized':an,'nets_new':bn})
check('preserved component intentional changes only', all(c['original']=='IO:U1' for c in changes), changes)
netpins=defaultdict(list)
for x in p.values():
    for pin,net in x['pins'].items():
        if net:netpins[net].append(x['ref']+'.'+pin)
check('no unintended singleton electrical nets', not any(len(v)<2 for v in netpins.values()), {k:v for k,v in netpins.items() if len(v)<2})

report={'source':str(SRC),'sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'revision':d['revision'],'component_counts':dict(Counter(x['kind'] for x in p.values())),'net_count':len(netpins),'endpoint_count':sum(map(len,netpins.values())),'checks':results,'calculations':{'adc_at_8p4V':8.4*10/(33+10),'echo_at_5V':5*20/(12+20),'echo_at_5p15V_1pct_worst':5.15*20.2/(11.88+20.2),'stby_at_pb5_3p3V_nominal':3.3/(1+1/10+1/200),'q2_base_mA_at_3p3V_vbe_0p7V':(3.3-.7)/4.7-.7/100,'NC_current_mA_at_6V_vbe_0p85V':(6-.85)/4.7,'NC_current_mA_at_8p4V_vbe_0p7V':(8.4-.7)/4.7},'limits':'Structured checks plus human review, not ERC/DRC or physical validation.'}
(HERE/'02-structured-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'counts':report['component_counts'],'checks':len(results),'review':[r for r in results if r['status']!='PASS'],'sha256':report['sha256'],'calculations':report['calculations']},ensure_ascii=False,indent=2))
