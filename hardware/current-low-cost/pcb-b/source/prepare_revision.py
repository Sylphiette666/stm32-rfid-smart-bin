"""Derive the B1 cable carrier from the immutable A1 JSON definition."""
from pathlib import Path
import json, shutil, csv

ROOT=Path(__file__).resolve().parents[1]
A=ROOT.with_name('pcb-a')
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    if (ROOT/'kicad/SmartBin_B.kicad_pcb').exists():
        raise SystemExit('Initialization only: refusing to overwrite the existing B1 design. Work in a new revision directory.')
    for sub in ['source','checks','kicad','renders','review','manufacturing']: (ROOT/sub).mkdir(exist_ok=True)
    d=json.loads((A/'circuit.json').read_text(encoding='utf-8'))
    d.update(revision='B1-2026-11-03',title='SmartBin B1 cable carrier with input translation',status='Design in verification; not physically tested')
    d['board'].update(target_size_mm=[125,100],assembly='Manual THT plus seven SOT-23-5 buffers and 0805 passives')
    parts=d['parts']; by={p['ref']:p for p in parts}
    by['J6']['value']='VOICE_PWR'
    by['J6']['notes']='DFPlayer VCC/GND dedicated screw terminal, short power pair. SPK1/SPK2 only to speaker; neither to GND.'
    by['J31']['pins']['3']='DF_BUSY_RAW';by['J31']['pin_names']['3']='DF_BUSY_RAW'
    by['J31']['notes']='1 GND, 2 DF_RX, 3 BUSY input 0..5.25V; on-board non-inverting translation. Power at J6. DFPlayer TX unused.'
    outs=['MCP_GPB0','MCP_GPB1','MCP_GPB2','MCP_GPB3','PB8','PA12','MCP_GPA6']
    raws=['IR0_RAW','IR1_RAW','IR2_RAW','IR3_RAW','IR4_RAW','IR5_RAW','DF_BUSY_RAW']
    for i in range(6):
        by['J33']['pins'][str(i+4)]=raws[i];by['J33']['pin_names'][str(i+4)]=raws[i]
    by['J33']['notes']='1 3V3_EXT, 2 5V_BUS, 3 GND; 4..9 IR0..5 raw inputs, 0..5.25V. Select exactly one rail for each sensor VCC. On-board buffers preserve polarity.'
    for i,(raw,out) in enumerate(zip(raws,outs)):
        rail='3V3_CORE' if out in ['PB8','PA12'] else '3V3_EXT'
        sig='BUF_IN_'+str(i)
        parts.append(dict(ref=f'U{i+2}',kind='logic',value='SN74LVC1G17DBVR',symbol='74xGxx:74LVC1G17',footprint='Package_TO_SOT_SMD:SOT-23-5',pins={'1':None,'2':sig,'3':'GND','4':out,'5':rail},pin_names={'1':'NC','2':'A','3':'GND','4':'Y','5':'VCC'},group='input_buffers',notes=f'{raw} to {out}; non-inverting Schmitt 5.5V tolerant input. Supply follows receiving logic domain.',dnp=False,MPN='SN74LVC1G17DBVR',Manufacturer='Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf'))
        for ref,val,pins in [(f'R{38+2*i}','1k',{'1':raw,'2':sig}),(f'R{39+2*i}','10k',{'1':sig,'2':rail})]:
            parts.append(dict(ref=ref,kind='resistor',value=val,symbol='Device:R',footprint='Resistor_SMD:R_0805_2012Metric',pins=pins,pin_names={},group='input_buffers',notes='Input series resistor / defined idle-high bias; 1%, 0.125W',dnp=False,tolerance='1%',power_rating_W=.125))
        parts.append(dict(ref=f'C{i+9}',kind='capacitor',value='100nF',symbol='Device:C',footprint='Capacitor_SMD:C_0805_2012Metric',pins={'1':rail,'2':'GND'},pin_names={},group='input_buffers',notes='Local buffer bypass, X7R 25V',dnp=False,voltage_rating_V=25))
    for ref,nets,value in [('J34',['GND']*3,'MCP_ADDR_GND'),('J35',['3V3_CORE','GND'],'AUX_CORE'),('J36',['3V3_EXT','GND'],'AUX_EXT'),('J37',['5V_BUS','GND'],'AUX_5V')]:
        parts.append(dict(ref=ref,kind='connector',value=value,symbol=f'Connector_Generic:Conn_01x0{len(nets)}',footprint=f'Connector_PinHeader_2.54mm:PinHeader_1x0{len(nets)}_P2.54mm_Vertical',pins={str(i+1):n for i,n in enumerate(nets)},pin_names={str(i+1):n for i,n in enumerate(nets)},group='input_buffers',notes='J34: MCP A0/A1/A2 to GND, address 0x20. AUX headers for low-current logic only, never motor/servo/voice.',dnp=False,connector_type='custom 2.54mm male header',high_current=False))
    d['connectors']=[p for p in parts if p['kind']=='connector']
    d['known_boundaries']=['External modules retained; no breadboard. Existing AO3400 and DHT level-shifter adapter modules still required.','No physical power, thermal, EMC or assembly test performed.','Motor emergency-stop function inherited from A1; servo power not cut by it.','125x100 mm outline; original M3 hole coordinates preserved. Mechanical clearance must use this revised outline.','Buffers accept 0..5.25V sensor signals; receiver rails separate and common GND.']
    d['summary']={'parts':len(parts),'input_buffer_channels':7,'connector_pin_count':sum(len(p['pins']) for p in parts if p['ref'].startswith(('J','JP')))}
    d['validation']={'state':'requires generated ERC, netlist parity and routed DRC'}
    d['configurations']=[c for c in d['configurations'] if c['id']!='digital_5v']
    d['configurations'].append({'id':'digital_inputs_B1','requires':{'U2-U8':'SN74LVC1G17DBVR fitted'},'notes':'Seven non-inverting on-board input translators; no external transistor adapters for J33 DO or J31 BUSY. Existing firmware polarity retained.'})
    d['sources'].append({'url':'https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf','description':'SCES351Y Oct 2025, DBV pins 1NC 2A 3GND 4Y 5VCC, 5.5V input capability; retrieved 2026-11-03'})
    save(ROOT/'circuit.json',d)
    layout=json.loads((A/'layout.json').read_text(encoding='utf-8'))
    layout['board_size_mm']=[125,100]
    layout['placements']['J33']=[120,12,0]
    for i in range(7):
        y=12+i*12
        layout['placements'].update({f'U{i+2}':[107,y,0],f'R{38+2*i}':[114,y,0],f'R{39+2*i}':[114,y+4,0],f'C{i+9}':[107,y+4,0]})
    for ref,y in [('J34',42),('J35',54),('J36',66),('J37',78)]:layout['placements'][ref]=[120,y,0]
    save(ROOT/'layout.json',layout)
    for fn in ['schematic_cli.py','pcb_cli.py','pcb_native.py','pcb_silk.py','package_fabrication.py']:
        s=(A/'source'/fn).read_text(encoding='utf-8').replace('SmartBin_A','SmartBin_B').replace('SmartBin A','SmartBin B').replace('SMARTBIN A1','SMARTBIN B1').replace("'A1'","'B1'").replace('2026-10-12','2026-11-03').replace('smartbin-a-20261012','smartbin-b-20261103')
        if fn=='schematic_cli.py':
            s=s.replace("TOOLING = HERE.parents[1] / 'tooling'", "TOOLING = Path(os.environ.get('SMARTBIN_TOOLING', str(HERE.parents[4] / '.pcb-lowcost-20261012/tooling')))")
            s=s.replace("PAGE_GROUPS = {", "PAGE_GROUPS = {\n    'input_buffers':'06 Non-inverting sensor input translation',")
            s=s.replace('9fd74206-b6db-4390-845b-12c12f476427','c47e0158-ae57-4edb-97d9-bd8f3de54c42').replace('A1 | Bare PCB + hand soldering','B1 | Cable carrier + input buffers')
        if fn=='pcb_silk.py':s=s.replace('149.2','174.2',1).replace('100x100','125x100').replace("('LOGIC',(65,132))","('VOICE',(65,132))")
        if not (ROOT/'source'/fn).exists(): (ROOT/'source'/fn).write_text(s,encoding='utf-8')
    with (ROOT/'connector-map.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['connector','pin','net','function','note'])
        for p in parts:
            if p['ref'].startswith(('J','JP')):
                for pin,net in p['pins'].items():w.writerow([p['ref'],pin,net,p['value'],p['notes']])
    print(d['summary'])
if __name__=='__main__':main()
