from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'circuit.json').read_text(encoding='utf-8'))
pl={c['ref']:[50,50,0] for c in cfg['parts']}
pl.update({'H1':[5,5,0],'H2':[95,5,0],'H3':[5,95,0],'H4':[95,95,0]})
(root/'layout.json').write_text(json.dumps({'placements':pl,'tracks':[],'silk':[]},indent=2),encoding='utf-8')
