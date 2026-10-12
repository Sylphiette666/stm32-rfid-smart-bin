"""Read-only CAM parsing/rendering of exported files, independent of pcbnew SVG."""
import sys, json, warnings, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'gerber-tools'))
from gerbonara.layers import LayerStack
from gerbonara.utils import MM
src=Path(sys.argv[1]) if len(sys.argv)>1 else HERE.parent/'manufacturing'
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    stack=LayerStack.open(src)
    bounds=stack.board_bounds(unit=MM)
    for side in ('top','bottom'):
        (HERE/f'cam-{side}.svg').write_text(str(stack.to_pretty_svg(side=side,margin=1)),encoding='utf-8')
        (HERE/f'cam-{side}-copper.svg').write_text(str(stack.to_svg(side_re=side,colors={f'{side} copper':'#bd3035' if side=='top' else '#3056bd','drill pth':'#ffffff','drill npth':'#ffffff'},margin=1)),encoding='utf-8')
report={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest() if src.is_file() else None,
        'parser':'gerbonara 1.6.3','board_bounds_mm':bounds,
        'layers':{str(k):{'objects':len(v.objects),'bounds':v.bounding_box(unit=MM)} for k,v in stack.graphic_layers.items()},
        'pth_objects':len(stack.drill_pth.objects) if stack.drill_pth else 0,
        'npth_objects':len(stack.drill_npth.objects) if stack.drill_npth else 0,
        'warnings':[str(w.message) for w in caught],
        'scope':'Independent parser rendered actual exported Gerber/Excellon files; visual review is a separate recorded step.'}
(HERE/'06-gerber-cam-parse.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
