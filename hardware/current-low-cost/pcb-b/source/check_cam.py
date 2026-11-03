"""Parse actual fabrication ZIP independently from KiCad's board renderer."""
from pathlib import Path
from collections import OrderedDict
import json,hashlib,warnings,math
from gerbonara.layers import LayerStack
from gerbonara.utils import MM
R=Path(__file__).resolve().parents[1];src=R/'manufacturing/Gerber_RS274X.zip'
with warnings.catch_warnings(record=True) as messages:
 warnings.simplefilter('always');stack=LayerStack.open(src)
 for side in ['top','bottom']:(R/f'renders/cam-{side}.svg').write_text(str(stack.to_pretty_svg(side=side,margin=1)),encoding='utf-8')
 stack.graphic_layers=OrderedDict(sorted(stack.graphic_layers.items(),key=lambda kv:0 if kv[0][1]=='silk' else 1))
 for side in ['top','bottom']:
  colors={f'{side} copper':'#c3a34c',f'{side} silk':'#142536','drill pth':'#ffffff','drill npth':'#ffffff'}
  (R/f'renders/cam-{side}-plain.svg').write_text(str(stack.to_svg(side_re=side,colors=colors,margin=1)),encoding='utf-8')
 bounds=stack.board_bounds(unit=MM)
geo=json.loads((R/'checks/board-geometry.json').read_text(encoding='utf-8'))
pth=[];npth=[]
for f in geo['footprints']:
 for pad in f['pads']:
  if max(pad['drill'])>0:
   (npth if f['ref'].startswith('H') else pth).append((round(pad['position'][0]+50,4),round(pad['position'][1]+50,4),round(pad['drill'][0],4)))
for t in geo['tracks']:
 if t['class']=='PCB_VIA':pth.append((round(t['start'][0]+50,4),round(t['start'][1]+50,4),.4))
def holes(layer):
 return [(round(o.x,4),round(-o.y,4),round(o.tool.diameter,4)) for o in layer.objects]
actual_pth=holes(stack.drill_pth);actual_npth=holes(stack.drill_npth)
# Gerber's Y axis is inverted relative to KiCad's screen coordinates.
def match(expected,actual):
 assert len(expected)==len(actual)
 pool=list(actual);errors=[]
 for x,y,diam in expected:
  candidates=[(math.hypot(x-a,y-b),i) for i,(a,b,d) in enumerate(pool) if abs(d-diam)<.0001]
  err,i=min(candidates);assert err<=.0015,(x,y,diam,err);pool.pop(i);errors.append(err)
 assert not pool
 return max(errors,default=0)
pth_error=match(pth,actual_pth);npth_error=match(npth,actual_npth)
width=bounds[1][0]-bounds[0][0];height=bounds[1][1]-bounds[0][1]
assert abs(width-125)<.2 and abs(height-100)<.2,(width,height)
d={'pass':True,'zip_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'parser':'gerbonara 1.6.3','bounds_including_outline_stroke_mm':bounds,'nominal_board_size_mm':[125,100],'pth_count':len(pth),'npth_count':len(npth),'all_drill_positions_and_diameters_match':True,'drill_coordinate_quantization_max_mm':max(pth_error,npth_error),'layers':{str(k):len(v.objects) for k,v in stack.graphic_layers.items()},'warnings':[str(w.message) for w in messages],'warning_review':'G90 after M95 is emitted by KiCad; absolute drilling coordinates parsed and independently matched. No drill-position discrepancy above 0.0015mm.'}
(R/'review/cam-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d,ensure_ascii=False,indent=2))
