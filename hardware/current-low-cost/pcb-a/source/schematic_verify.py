"""Compare actual KiCad exported nets to the independently supplied circuit JSON."""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET

def verify(circuit, netlist, out):
    spec=json.loads(Path(circuit).read_text(encoding='utf-8-sig'))
    root=ET.parse(netlist).getroot()
    actual={}
    for net in root.findall('nets/net'):
        for node in net.findall('node'):
            actual[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name']
    errors=[];checked=0;nc=0
    for p in spec['parts']:
        for pin,net in p['pins'].items():
            observed=actual.get((p['ref'],pin))
            if net is None:
                nc+=1
                if observed and not observed.startswith('unconnected-'):
                    errors.append({'ref':p['ref'],'pin':pin,'expected':None,'actual':observed})
            else:
                checked+=1
                if net!=observed:
                    errors.append({'ref':p['ref'],'pin':pin,'expected':net,'actual':observed})
    expected_refs={p['ref'] for p in spec['parts']}
    exported_refs={p.attrib['ref'] for p in root.findall('components/comp')}
    if expected_refs != exported_refs:
        errors.append({'missing_refs':sorted(expected_refs-exported_refs),'extra_refs':sorted(exported_refs-expected_refs)})
    result={'pass':not errors,'checked_connected_pins':checked,'checked_nc_pins':nc,'parts':len(expected_refs),'exported_parts':len(exported_refs),'errors':errors}
    Path(out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('circuit');ap.add_argument('netlist');ap.add_argument('out');a=ap.parse_args()
    raise SystemExit(verify(a.circuit,a.netlist,a.out))
