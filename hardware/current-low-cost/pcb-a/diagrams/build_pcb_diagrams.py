"""Compose instructional SVG pages from native KiCad SVG plots. No inferred traces."""
from pathlib import Path
import xml.etree.ElementTree as E
from html import escape
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'diagrams'
E.register_namespace('', 'http://www.w3.org/2000/svg')
def text(x,y,s,size=34,color='#213745',weight=400):return f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(s)}</text>'
def native(name):
    v=E.parse(ROOT/'renders'/name).getroot();v.set('x','180');v.set('y','260');v.set('width','1440');v.set('height','1440')
    s=E.tostring(v,encoding='unicode')
    return s.replace('#AFAFAF','#475569').replace('#4D7FC4','#AEC8E6').replace('#E8B2A7','#182C39').replace('#F2EDA1','#182C39')
def card(x,y,title,lines):
    s=f'<rect x="{x}" y="{y}" width="820" height="360" rx="10" fill="#F2F6F8" stroke="#B5C9D5" stroke-width="2"/>'+text(x+25,y+53,title,42,weight=700)
    for n,l in enumerate(lines):s+=text(x+25,y+113+n*53,l,33)
    return s
def make(name,title,sub,plot,left,right):
    s='<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2250" viewBox="0 0 1800 2250"><rect width="1800" height="2250" fill="white"/>'
    s+=text(50,90,title,58,weight=700)+text(50,154,sub,35,color='#63747F')
    s+=text(180,222,'真实 CAD 输出：100 × 100 mm；安装孔中心距 90 × 90 mm',34)
    s+=native(plot)
    s+=f'<rect x="180" y="260" width="1440" height="1440" fill="none" stroke="#526D7C" stroke-width="2"/>'
    s+=text(180,1755,'图中位号与实板一致；密集针号请放大电子图，并对照第 63 章逐针表。',33)
    s+=card(50,1795,*left)+card(930,1795,*right)
    s+=text(50,2210,'A1 / 排线连接 / MCP23017 成品模块在板外 / 电源大电流支路使用端子和导线',31,color='#63747F')+'</svg>'
    (OUT/(name+'.svg')).write_text(s,encoding='utf-8')
make('45_pcb_top','图 45｜PCB 顶面装配位置图','从元件面俯视；本图未镜像。端子 J1～J6 在左侧。','board-assembly-top.svg',
     ('按高度从低到高焊接',['① 电阻 → 小瓷片 → 14 脚插座','② 三极管 → 排针/跳帽 → 接线端子','③ 电解电容；检查正负极再焊','④ 清洗检查；测电源后再插 U1']),
     ('三个方向必须认准',['U1 缺口朝图上方；芯片暂不插入','C1～C3 的“+”焊盘朝左，负脚朝右','J1～J6 进线口朝板外（左侧）','划叉的 DNP 位按模块条件选装']))
make('46_pcb_bottom','图 46｜PCB 底面焊接与核对图','从焊接面直视；左右已经镜像一次，请勿再次翻转此图。','board-bottom-solder.svg',
     ('先认方向，再逐个焊点核对',['翻到背面后，J1～J6 应位于右侧','蓝色为底层铜；不是需要手搭的线','工厂已做好铜线与金属化孔','焊元件引脚即可，不另加焊锡连桥']),
     ('断电检查顺序',['放大核对相邻焊盘是否锡桥','先测 5V/GND、两路 3V3/GND','电解负极、U1 缺口再检查一次','首次限流通电，模块按步骤分批接']))
