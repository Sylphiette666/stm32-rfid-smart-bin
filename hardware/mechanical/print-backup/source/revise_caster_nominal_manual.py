"""Replace the measurement-first caster recommendation with the derived H41 nominal design."""
from pathlib import Path
import shutil,re
from docx import Document
from docx.shared import Cm
B=Path(__file__).resolve().parents[1];R=B.parents[2];O=B/'caster-riser-20261103';W=R.parent/'.p2s-caster-nominal-20261103/manual';W.mkdir(parents=True,exist_ok=True)
N='STM32与RFID智能移动垃圾桶_逐步组装与调试实施手册_图解增强版.docx';src=R/'docs/manual'/N
assert src.read_bytes()==(R.parent/N).read_bytes();shutil.copy2(src,W/'before.docx')
before=Document(src);d=Document(src)
changes=0
for i,p in enumerate(d.paragraphs):
 t=p.text
 if t.startswith('按用户在“制定智能垃圾桶搭建步骤1”中的实测'):
  p.text='按用户在“制定智能垃圾桶搭建步骤1”中的实测，D05万向轮总安装高度20mm、两孔中心距40mm。65mm轮胎半径32.5mm；原方案底板离地参考45mm，等价于轮轴低于底板下表面12.5mm。已打印电机转接板使轮轴再下移16mm，故底板名义离地为32.5+12.5+16=61mm，万向轮名义增高量为61−20=41mm。本版首选H41。原轮轴偏移是方案参考而非实测，装车后须检查三轮着地。';changes+=1
 elif t.startswith('图解92 '):
  p.text='图解92  名义H41叠层：4mm支臂、孔位7mm承力台、34mm立柱和万向轮安装片。'
  imagep=d.paragraphs[i-1];imagep.clear();imagep.add_run().add_picture(str(O/'preview/02_caster_stack.png'),width=Cm(16.2));changes+=1
 elif t.startswith('先装两侧电机和65mm轮子'):
  p.text='按高度链首选H41打印工程：一块支架加两只34mm立柱，切片估算18.4g。H35/H40/H45仅为实装修正选项。装好两侧65mm驱动轮和万向轮后，在平整桌面检查三轮同时接地及底板水平；若实物轮轴偏移与原方案参考不同，再测底板下表面离地Hb，按H=Hb−20mm修正。';changes+=1
 elif t.startswith('断电并移开A1线束。'):
  p.text='断电并移开A1线束。C/D两颗M3低圆头螺钉从支架上面的沉孔穿入，头下各配OD≤6mm、约0.5mm平垫；头和垫片必须低于贴底板平面。套两只H41立柱，再接万向轮安装片，下面加平垫和M3防松螺母。按安装片约2mm厚的参考叠层，先试M3×50；实际孔径、片厚、露牙与滚轮净隙必须核对。';changes+=1
 elif t.startswith('打印使用P2S 0.4mm喷嘴'):
  p.text='首选文件为caster-riser-20261103/P2S_CASTER_RISER_H41_LIGHT_016.3mf。P2S 0.4mm喷嘴、PLA、0.16mm层高、6墙、45% gyroid、5mm brim、无支撑；保持100%比例和保存的朝向。数字检查和切片通过，实际承重、疲劳和行驶尚未验收。';changes+=1
assert changes==5,changes
steps=lambda x:[p.text for p in x.paragraphs if re.match(r'步骤 \d{3}',p.text)]
assert steps(before)==steps(d) and len(steps(d))==330 and len(before.tables)==len(d.tables)
out=W/N;d.save(out);print(out)
