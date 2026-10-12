"""Independent Excellon versus native PCB drill-coordinate review (read-only)."""
import json, math, re, hashlib
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
native = json.loads((HERE/'04-native-final-audit.json').read_text(encoding='utf-8'))
def key(x,y,d): return (round(x,4),round(y,4),round(d,4))
expected = {True: Counter(), False: Counter()}
holes = []
for p in native['all_pad_drills']:
    if p['drill'] <= 0: continue
    x,y = p['position']
    expected[p['plated']][key(x,y,p['drill'])] += 1
    holes.append({'name':p['ref']+'.'+p['pin'],'kind':'pad','xy':[x,y],'d':p['drill']})
for i,v in enumerate(native['vias']):
    x,y = v['position']
    expected[True][key(x,y,v['drill'])] += 1
    holes.append({'name':'via'+str(i),'kind':'via','xy':[x,y],'d':v['drill']})
reports = []
for plated,suffix in ((True,'PTH'),(False,'NPTH')):
    path = ROOT/'manufacturing'/('SmartBin_A-'+suffix+'.drl')
    txt = path.read_text(encoding='ascii')
    assert 'METRIC' in txt and 'G90' in txt, 'Requires metric absolute format'
    tools = {int(t):float(d) for t,d in re.findall(r'^T(\d+)C([\d.]+)',txt,re.M)}
    actual = Counter(); tool = None
    for line in txt.splitlines():
        t = re.fullmatch(r'T(\d+)',line)
        if t: tool=int(t.group(1))
        hit = re.fullmatch(r'X([\d.-]+)Y([\d.-]+)',line)
        if hit:
            x,y=map(float,hit.groups())
            actual[key(x-50,-y-50,tools[tool])] += 1
    # KiCad Excellon metric output resolves coordinates to 0.001 mm.
    # Match each hole once within half that resolution on both axes.
    remaining=list(actual.elements()); missing=[]; errors=[]
    for ex in expected[plated].elements():
        candidates=[(math.dist(ex[:2],ac[:2]),i,ac) for i,ac in enumerate(remaining)
                    if abs(ac[2]-ex[2])<1e-6 and max(abs(ex[0]-ac[0]),abs(ex[1]-ac[1]))<=.0005001]
        if not candidates: missing.append(ex); continue
        delta,i,ac=min(candidates); remaining.pop(i); errors.append(delta)
    reports.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'expected_count':sum(expected[plated].values()),'actual_count':sum(actual.values()),
                    'coordinate_tolerance_per_axis_mm':.0005,'maximum_radial_rounding_mm':max(errors,default=0),
                    'missing':missing,'extra':remaining,'pass':not missing and not remaining})
minimum={}
for i,a in enumerate(holes):
    for b in holes[i+1:]:
        group='-'.join(sorted([a['kind'],b['kind']]))
        gap=math.dist(a['xy'],b['xy'])-(a['d']+b['d'])/2
        if group not in minimum or gap<minimum[group]['gap_mm']:
            minimum[group]={'gap_mm':gap,'objects':[a['name'],b['name']]}
report={'status':'PASS' if all(r['pass'] for r in reports) else 'FAIL',
        'board_sha256':native['board_sha256'],'units':'mm',
        'coordinate_transform':'Excellon X-50, -Y-50 = board-relative native X,Y',
        'drill_matches':reports,'minimum_hole_edge_spacing':minimum,
        'scope':'Coordinates matched one-to-one at Excellon 0.001 mm precision; exact diameter and PTH/NPTH class; no physical part fit assertion.'}
(HERE/'05-drill-alignment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
