from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'circuit.json').read_text(encoding='utf-8'));parts={p['ref']:p for p in d['parts']}
with (R.with_name('pcb-a')/'connector-map.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
for row in rows:
 p=parts[row['Ref']];pin=row['PCB_pin'];row['Net']=p['pins'][pin];row['Name']=p['value']
 if row['Ref'] in ['J6','J31','J33']:row['Notes']=p['notes']
 if row['Ref']=='J6':row['External_signal_by_label']='DFPlayer VCC' if pin=='1' else 'DFPlayer GND'
 if row['Ref']=='J31' and pin=='3':row['External_signal_by_label']='DFPlayer BUSY原始输出（3.3V/5V）'
 if row['Ref']=='J33' and int(pin)>=4:row['External_signal_by_label']=['循迹左DO','循迹中DO','循迹右DO','靠近DO','前障碍DO','投放对射DO'][int(pin)-4]+'原始输出（3.3V/5V）'
for ref,labels in [('J34',['MCP23017 A0','MCP23017 A1','MCP23017 A2']),('J35',['辅助低功耗 CORE 3.3V','GND']),('J36',['辅助低功耗 EXT 3.3V','GND']),('J37',['辅助低功耗 5V','GND'])]:
 p=parts[ref]
 for pin,net in p['pins'].items():rows.append(dict(Ref=ref,Name=p['value'],PCB_pin=pin,Net=net,External_signal_by_label=labels[int(pin)-1],Connector_type=p['connector_type'],Notes=p['notes']))
assert len(rows)==190 and len({(r['Ref'],r['PCB_pin']) for r in rows})==190
with (R/'connector-map.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('190 pins mapped to actual module signal labels')
