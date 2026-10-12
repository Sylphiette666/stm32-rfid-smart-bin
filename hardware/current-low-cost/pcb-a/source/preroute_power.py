from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'layout.json';d=json.loads(p.read_text())
ts=[]
def t(net,width,points,layer='F.Cu'):ts.append({'net':net,'width':width,'points':points,'layer':layer})
# 3A continuous / 4A short-pulse trunk. All actuator return current stays on
# the left power spine. Signal autorouting may add only the logic branches.
t('VBAT_SW',3,[(7,13),(13.5,13),(13.5,27),(7,27)])
t('5V_BUS',3,[(7,41),(13.5,41),(13.5,87)])
for y in (55,69,82):t('5V_BUS',2,[(7,y),(13.5,y)])
for y in (51,69,87):t('5V_BUS',2,[(13.5,y),(21,y)])
for y in (60,78,96):t('5V_BUS',.8,[(13.5,min(y,87)),(13.5,y),(18,y)])
t('GND',3,[(13.5,18.08),(13.5,93)],'B.Cu')
for y in (18.08,32.08,46.08,60.08,74.08,87.08):t('GND',3 if y in (18.08,32.08,46.08) else 2,[(7,y),(13.5,y)],'B.Cu')
for y,yy in [(51,57),(69,75),(87,93)]:t('GND',2,[(26,y),(29,y+3),(29,yy),(13.5,yy)],'B.Cu')
# AHCT local 100nF path to supply pin 14 (shortest unobstructed lead).
t('5V_BUS',.8,[(45.62,46),(45.62,45.38),(49,42)])
d['tracks']=ts;d['placement_conflicts']=[]
p.write_text(json.dumps(d,indent=2),encoding='utf-8')
