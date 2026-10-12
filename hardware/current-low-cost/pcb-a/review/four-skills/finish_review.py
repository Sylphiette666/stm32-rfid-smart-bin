from pathlib import Path
import json,hashlib,shutil,re
R=Path(__file__).resolve().parent;W=R/'working';O=W/'review/four-skills'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
# Each exact upstream checklist line receives an explicit outcome. FAIL is retained,
# not silently converted to PASS merely because this is a prototype.
states=[
 [('PASS','100mm closed centerline; native/CAM agreement'),('PASS','3.2mm NPTH centers5/95mm; nominalM3 envelope checked; purchased fixtures still measure'),('PASS','External cable connectors; not a direct-fit core socket'),('PASS','2layerFR4 1.6mm handbuild; no integrated RF/converter'),('N-A','No controlled-impedance interface claimed'),('PASS','0.20clearance;0.25mintrace;.8/.4vias; intended stronger than ordinary2layer minimum'),('PASS','Through-hole handbuild; no edge/card mating'),('N-A','Single board no panel or PCBA'),('PASS','Existing order-and-assembly.md specifies bareboard parameters'),('N-A','No PCB antenna or HV; four mechanical holes checked'),('PASS','Frozen baseline/local review history; user-authorized Git repository backup')],
 [('PASS','Power left, signal right; external modules'),('PASS','Nominal placement reviewed in existing design plus current rendering'),('FAIL','U1/C8 pin distance5.24mm exceeds2mm recipe; residual EMC risk retained'),('N-A','No onboard crystal'),('PASS','Switching buck/driver external; power and signal banks separated'),('N-A','Buck internal hot loop outside this board'),('N-A','No onboard power converter or exposed-pad IC; no thermal qualification claimed'),('N-A','RFID antenna is external; physical clearance follows module manual'),('FAIL','Universal I/O ESD/filter network not fitted; short enclosed wires, no hotplug/ESD rating'),('PASS','Labeled through-hole headers are probe access; table in joint report'),('N-A','Already routed; final unconnected0 replaces ratsnest check'),('PASS','Nominal body/3D check; courtyard omissions explicitly supplemented; bought-part fit pending'),('PASS','Baseline and revision files retained locally')],
 [('PASS','Final KiCad DRC0; ignored rule classes disclosed separately'),('PASS','Final unconnected0 after refill'),('N-A','External converter'),('FAIL','PA6 and other segments lack continuous opposite-layer GND; raw coverage and CAM retained'),('FAIL','55GND stitches improve but not every transition has <=1mmGND via'),('N-A','No differential interface on carrier'),('N-A','No synchronous skew budget; short low-rate SPI/I2C prototype'),('PASS','33 planned power/return segments preserved; actual load thermal validation pending'),('N-A','No converter FB; ADC is filtered slow battery divider'),('PASS','Filled disconnected-island removal and DRC0;55groundstitchesadded'),('PASS','Native/CAM viewed; references and polarity readable; final silkscreen DRC0'),('PASS','Native3D refreshed; external module and actual bought parts still need real fit'),('PASS','Revision checkpoint retained')],
 [('PASS','gerber_audit.py exit0; report stored'),('PASS','9files includingPTH/NPTH; paste N-A for hand solder'),('PASS','Only intended7Gerberlayers+2drills inzip'),('PASS','BOM/refsetschecked; placement-fileN-A noSMT; existingbomlintdataretained unchanged'),('PASS','Bareboard notes complete;quantityactualorder'),('PASS','KiCad schematic parity0'),('PASS','Official capability read at release; ordinary2layer rules'),('FAIL','Actual battery/driver/stop system not inspected by a human hardware reviewer; no safety certification claimed'),('PASS','Manual63 and64 specify voltages and staged tests'),('PASS','Local journal plus authorizedGitHubpush; uploadedcommitmustbeverifiedbeforefinaldelivery'),('N-A','Educationalprototype; no publicfilehostbackup mandate; GitHubbackup peruser')],
 [('PASS','FreshERC0; sourceunchanged'),('PASS','Namedfunctionalnets'),('PASS','Native94ref/pinmatch; intentionalADC/Echo/stopasymmetries'),('PASS','Specifiedresistorbias and unusedAHCTinputlevels checked; firmwareGPIOinit stillrequired'),('N-A','No onboardMCUresetsequencer; externalmodulestartup not simulated'),('FAIL','Rails mapped; full externalmodulepeakload and20%budget not measured yet'),('PASS','181connectorpins assigned byfunction; modulephysicalsequence notassumed'),('N-A','NoUSB-C oncarrier'),('PASS','C4/C5/C6/C8localdecoupling andbulk; distancewarning retained'),('N-A','Externalbuckadjustment;dividersverifiedseparately'),('PASS','U1andQreferencepinoutcrosscheck; purchasedgenericQidentitypending'),('PASS','Stagedbringupmanual andprobepoints'),('PASS','LocalbaselineandGitcheckpoint')]
]
src=Path(r'C:\Users\35462\.codex\skills\pcb-pitfalls\references\checklists.md').read_text(encoding='utf-8')
sections=[];current=None
for line in src.splitlines():
 if line.startswith('## '):current=[];sections.append((line[3:],current))
 elif line.startswith('- [ ] '):current.append(line[6:])
 elif current and line.startswith('      '):current[-1]+=' '+line.strip()
assert len(sections)==len(states)
lines=['# Toaster阶段清单逐项审查','','本项目是已有设计的低成本手焊教学原型。FAIL保持为未满足/待实测项；不代表已获整机量产、热或EMC批准。裸板几何与文件检查单独记录。','']
for (title,items),result in zip(sections,states):
 assert len(items)==len(result),(title,len(items),len(result))
 lines+=['## '+title,'','| 原检查项 | 结果 | 本板证据或适用边界 |','|---|---|---|']
 lines += [f'| {item} | {state} | {reason} |' for item,(state,reason) in zip(items,result)]
 lines+=['']
(O/'phase-checklist.md').write_text('\n'.join(lines),encoding='utf-8')
# Refresh the narrow manufacturing review, preserve its actual scope.
oldpcb=sha(R/'baseline/kicad/SmartBin_A.kicad_pcb');oldzip=sha(R/'baseline/manufacturing/Gerber_RS274X.zip')
p=W/'review/07-final-manufacturing-review.md';s=p.read_text(encoding='utf-8')
s=s.replace(oldpcb,sha(W/'kicad/SmartBin_A.kicad_pcb')).replace(oldzip,sha(W/'manufacturing/Gerber_RS274X.zip'))
s=s.replace('未发现需要阻止本版裸 PCB 打样的未关闭问题。','文件层面未发现短路、漏连或钻孔错配；四套技能复查仍保留地回流和去耦布局限制，见 `four-skills/四套技能联合审查报告.md`。')
s=s.replace('时间为 18:25:52','采用本次接地加强版重新运行的报告').replace('62 个，外径','117 个（新增55个GND过孔），外径').replace('356 个 PTH（其中 62 个过孔）','411 个 PTH（其中 117 个过孔）')
s+='\n\n## 本次接地加强补充\n\n2026-10-12新增55个GND过孔，未变更BOM、接口或原走线。此文件仅验收制造数据；EMC工具仍有45条error级启发式项，热及生命周期工具缺少数据，均不能据此声称全项目通过。完整分类及待实测条件见四套技能联合报告。\n'
p.write_text(s,encoding='utf-8')
p=W/'review/release-manual.json';d=load(p)
d['reviews']['gerber_visual_and_drill_alignment']['evidence']=f'Current Gerber {sha(W/"manufacturing/Gerber_RS274X.zip")} independently parsed with gerbonara; top/bottom copper, mask and silk reviewed.411PTH+4NPTH match the final native PCB; all9zipentriesmatch. No paste required for THT handbuild.'
d['reviews']['decoupling_and_analog_separation']['evidence']='Connectivity and nominal placement checked; C8-to-U1VCC5.24mm remains an EMC warning, not a performance PASS. This manufacturing check only confirms decoupler is fitted/connected; analog filter and external power boundaries documented. See four-skills report for residual layout risks.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('## 先使用哪些文件','## 四套技能复查更新\n\n本次接地加强版新增55个GND过孔，无新增BOM元件或手焊任务。制造检查通过；EMC回流/去耦仍有待实测项，不能理解为四套工具全部零告警。图解增强版新增第64章。完整证据见[四套技能联合审查报告](review/four-skills/四套技能联合审查报告.md)。\n\n## 先使用哪些文件');p.write_text(s,encoding='utf-8')
j=W/'PROJECT_JOURNAL.md'
with j.open('a',encoding='utf-8') as f:f.write('\n\n## 2026-10-12 四套技能接地加强复查\n\n经真实KiCad10IPC加入55个GND过孔，最终117个。94位号、BOM、接口和33段动力电源/地走线保持。ERC/DRC/原理图一致性零违规，Gerber孔位一一匹配。两处分压以ngspice-46DLL核验。保留EMC地回流/去耦风险与未完成热/生命周期实物信息，不宣称全机验证。更新同名Word第64章及当前制造包，并按用户授权同步GitHub；详见review/four-skills。\n')
print('56-line phase checklist and narrow manufacturing documentation refreshed.')
