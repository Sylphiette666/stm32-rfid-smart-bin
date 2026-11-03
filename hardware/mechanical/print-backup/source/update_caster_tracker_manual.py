"""Append the verified combined print plate to the same-name illustrated manual."""
from pathlib import Path
import json
import re
import shutil

from docx import Document
from docx.shared import Cm

B = Path(__file__).resolve().parents[1]
R = B.parents[2]
O = B/'caster-tracker-plate-20261103'
W = R.parent/'.p2s-caster-tracker-20261103/manual'
W.mkdir(parents=True,exist_ok=True)
name = 'STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx'
src = R/'docs/manual'/name
assert src.read_bytes() == (R.parent/name).read_bytes()
shutil.copy2(src,W/'before.docx')
before = Document(src)
assert not any(p.text.startswith('66.20 ') for p in before.paragraphs)
doc = Document(src)
doc.add_heading('66.20 H41万向轮支架与循迹架同盘打印',level=2)
doc.add_paragraph('同盘工程为 caster-tracker-plate-20261103/P2S_CASTER_H41_TRACKER_ALL_012.3mf。包含H41万向轮支架和两只34mm立柱、循迹模块转接架及14/18/22mm垫柱各两只，共10件。三种垫柱用于试装选择，实际装配只使用一对等高垫柱。')
doc.add_paragraph().add_run().add_picture(str(O/'plate_preview.png'),width=Cm(16.2))
doc.add_paragraph('图解93  P2S同盘摆放：左侧为H41万向轮支架，中间为循迹转接架，右侧为两只H41立柱和三对循迹垫柱。')
doc.add_paragraph('P2S 0.4mm喷嘴、Generic PLA、0.12mm层高、6墙、45% gyroid、5mm brim、无支撑；10件切片通过且无警告，估算约2小时32分、27.7g。保持100%比例和工程内朝向，按实用材料重新切片。实物打印、三轮着地和循迹探头离地距离仍需试装核对。')
steps = lambda d: [p.text for p in d.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(before) == steps(doc) and len(steps(doc)) == 330
assert len(before.tables) == len(doc.tables)
out = W/name
doc.save(out)
report = {'source':str(src),'staged':str(out),'original_step_count':330,
          'table_count':len(doc.tables),'new_figure':'图解93','render_checked':False}
(O/'manual_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out)
