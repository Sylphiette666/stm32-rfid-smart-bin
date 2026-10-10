from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, json, html, hashlib

OUT=Path(__file__).resolve().parent
FONT='C:/Windows/Fonts/msyh.ttc'
BOLD='C:/Windows/Fonts/msyhbd.ttc'
INK='#17252E'; MUTED='#566773'; BLUE='#1565A6'; ORANGE='#B16916'
RED='#C33D3D'; GREEN='#237655'; GREY='#DBE2E6'
BLUEF='#E7F0F8'; ORANGEF='#F7ECD9'; GREENF='#E8F2EB'

class Canvas:
    def __init__(self,name,title,subtitle,h=1550):
        self.name,self.w,self.h=name,1800,h
        self.im=Image.new('RGB',(self.w,h),'white');self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="{h}" viewBox="0 0 1800 {h}">',
                  '<rect width="100%" height="100%" fill="white"/>',
                  '<style>text{font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif}</style>']
        self.text((45,30),title,48,bold=True)
        self.text((45,103),subtitle,36,MUTED)
    def text(self,xy,txt,size=38,color=INK,bold=False,center=False):
        lines=str(txt).split('\n');f=ImageFont.truetype(BOLD if bold else FONT,size)
        spacing=12
        total=len(lines)*size+(len(lines)-1)*spacing
        x,y=xy
        if center:y-=total/2
        for t in lines:
            # Pillow top anchor and SVG baseline refer to the same nominal font em.
            self.d.text((x,y),t,font=f,fill=color,anchor='mt' if center else 'lt')
            self.svg.append(f'<text x="{x:.2f}" y="{y+size*.87:.2f}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{"middle" if center else "start"}">{html.escape(t)}</text>')
            y+=size+spacing
    def rect(self,b,fill=None,stroke=INK,width=3):
        x0,y0,x1,y1=b
        self.d.rectangle(b,fill=fill,outline=stroke,width=width)
        self.svg.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{width}"/>')
    def line(self,pts,color=INK,width=3,dash=False):
        if dash:
            for a,b in zip(pts,pts[1:]):
                dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
                if not length:continue
                n=0
                while n<length:
                    e=min(n+13,length)
                    self.d.line([(a[0]+dx*n/length,a[1]+dy*n/length),(a[0]+dx*e/length,a[1]+dy*e/length)],fill=color,width=width)
                    n+=23
        else:self.d.line(pts,fill=color,width=width,joint='curve')
        s=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)
        self.svg.append(f'<polyline points="{s}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="13 10"' if dash else '')+'/>')
    def poly(self,pts,fill,stroke=None,width=3):
        self.d.polygon(pts,fill=fill,outline=stroke)
        self.svg.append(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in pts)}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{width}"/>')
    def arrow(self,pts,color=BLUE,width=3,both=False,head=15):
        self.line(pts,color,width)
        for p,q in [(pts[-2],pts[-1])]+([(pts[1],pts[0])] if both else []):
            a=math.atan2(q[1]-p[1],q[0]-p[0])
            self.poly([q,(q[0]-head*math.cos(a-.45),q[1]-head*math.sin(a-.45)),(q[0]-head*math.cos(a+.45),q[1]-head*math.sin(a+.45))],color)
    def dim_h(self,x0,x1,y,label,ext0=None,ext1=None,color=MUTED):
        if ext0 is not None:self.line([(x0,ext0),(x0,y-10)],color,2)
        if ext1 is not None:self.line([(x1,ext1),(x1,y-10)],color,2)
        self.arrow([(x0,y),(x1,y)],color,3,True)
        self.text(((x0+x1)/2,y-35),label,38,color,center=True)
    def dim_v(self,y0,y1,x,label,refx=None,color=MUTED):
        if refx is not None:
            self.line([(refx,y0),(x-10,y0)],color,2);self.line([(refx,y1),(x-10,y1)],color,2)
        self.arrow([(x,y0),(x,y1)],color,3,True)
        y=(y0+y1)/2
        self.rect((x-57,y-34,x+57,y+34),'white',None,0)
        self.text((x,y),label,38,color,center=True)
    def save(self):
        self.im.save(OUT/(self.name+'.png'),dpi=(300,300))
        (OUT/(self.name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        return {'filename':self.name+'.png','svg':self.name+'.svg','png_width':self.w,'png_height':self.h}

# Exact part rectangles in mm, measured from sheet 1 top-left; 5 mm or more stock gap.
# Rear fixed strip reserves a 150x12 blank, trimmed to actual 10-12 mm after hinge trial.
PARTS=[
 {'id':'P03-L','name':'左侧壁','x':5,'y':5,'w':160,'h':180,'t':3},
 {'id':'P04-R','name':'后壁','x':170,'y':5,'w':144,'h':180,'t':3},
 {'id':'P03-R','name':'右侧壁','x':5,'y':190,'w':160,'h':180,'t':3},
 {'id':'P04-F','name':'前壁','x':170,'y':190,'w':144,'h':180,'t':3},
 {'id':'P05','name':'壳底','x':319,'y':5,'w':154,'h':144,'t':3},
 {'id':'P07','name':'前操作板毛坯','x':5,'y':375,'w':190,'h':120,'t':3},
 {'id':'P10','name':'触边横杠毛坯','x':200,'y':375,'w':180,'h':25,'t':3,'approximate':True},
 {'id':'P08','name':'可拆超声横梁毛坯','x':200,'y':405,'w':150,'h':35,'t':3},
 {'id':'FIXED-STRIP','name':'后固定条预留毛坯','x':200,'y':445,'w':150,'h':12,'t':3,'finished_width_mm':'10–12，按实物铰链试装'}
]
def verify_nesting():
    for p in PARTS:
        assert p['x']>=5 and p['y']>=5 and p['x']+p['w']<=495 and p['y']+p['h']<=495,p
    for i,a in enumerate(PARTS):
        for b in PARTS[i+1:]:
            assert a['x']+a['w']+5<=b['x'] or b['x']+b['w']+5<=a['x'] or a['y']+a['h']+5<=b['y'] or b['y']+b['h']+5<=a['y'],(a,b)
    return {'sheet_mm':[500,500,3],'minimum_edge_margin_mm':5,'minimum_interpart_gap_mm':5,'all_rectangles_within_sheet':True,'no_overlap':True,'parts':PARTS,'second_sheet':'500×500×3 整片备用','drawing_scale_is_not_print_scale':True}

def nesting():
    c=Canvas('pvc_42_nesting','图解 42｜3 mm 发泡 PVC 排料：第一片裁主件，第二片备用','单位 mm｜原料共 2 片 500×500×3；本图不含 2 mm 活动盖，也不含 PP 内胆。',1550)
    c.text((140,160),'第 1 片：按编号逐片划线',42,bold=True)
    x0,y0,s=140,290,1.8
    c.rect((x0,y0,x0+500*s,y0+500*s),'#F6F8F9',MUTED,3)
    c.dim_h(x0,x0+900,275,'500',y0,y0)
    c.dim_v(y0,y0+900,85,'500',x0)
    colors={'P03-L':BLUEF,'P03-R':BLUEF,'P04-R':ORANGEF,'P04-F':ORANGEF,'P05':GREENF,'P07':'#EEEAF5','P08':'#EBF3F3','P10':'#F6E8E8','FIXED-STRIP':'#E3E7EC'}
    for p in PARTS:
        x,y=x0+p['x']*s,y0+p['y']*s;w,h=p['w']*s,p['h']*s
        c.rect((x,y,x+w,y+h),colors[p['id']],INK,3)
        if p['id'].startswith('P03'):
            c.text((x+w/2,y+h/2),f"P03 {p['name']}\n160×180",40,BLUE,True,True)
        elif p['id'].startswith('P04'):
            c.text((x+w/2,y+h/2),f"P04 {p['name']}\n144×180",39,ORANGE,True,True)
        elif p['id']=='P05':c.text((x+w/2,y+h/2),'P05 壳底\n154×144',40,GREEN,True,True)
        elif p['id']=='P07':c.text((x+w/2,y+h/2),'P07 操作板\n190×120',40,INK,True,True)
        elif p['id']=='P10':c.text((x+w/2,y+h/2),'P10 约180×25',34,INK,False,True)
        elif p['id']=='P08':c.text((x+w/2,y+h/2),'P08 150×35',36,INK,False,True)
    c.text((870,735),'余料区\n保留试切、\n试钻和补强',38,MUTED,False,True)
    c.text((1180,160),'第 2 片：完整留作备用',42,bold=True)
    bx,by,bw=1225,290,390
    c.rect((bx,by,bx+bw,by+bw),'#F6F8F9',MUTED,3)
    c.text((bx+bw/2,by+bw/2),'500×500×3\n不必立即裁开',42,MUTED,False,True)
    c.text((1205,705),'第二片缩小显示；尺寸同第一片。',34,MUTED)
    c.text((1160,795),'先用第一片余料试切、试钻；\n第二片留给补强、失败重做。',38)
    c.text((1160,935),'固定侧补强按实物裁；\n随盖补强仍须计入活动质量。',38)
    c.arrow([(790,1102),(1090,1102),(1140,1125)],MUTED,3)
    c.text((1160,1080),'后固定条预留 150×12×3；\n试装后取宽 10～12。\n不是活动盖，不预钻铰链孔。',36)
    c.text((140,1235),'排料方法',42,BLUE,True)
    c.text((140,1300),'① 边缘与片间均留至少 5；按标注的零件尺寸划线，刀或锯走余料一侧。',38)
    c.text((140,1365),'② 多次浅切，逐片修边；在余料上试钻，再标明“内 / 外 / 前 / 后”。',38)
    c.text((140,1430),'③ 面板、横梁与横杠为毛坯；无胶试拼通过后，按实际模块描孔。',38)
    c.text((140,1492),'按数字下料，不按打印图的大小切割。所有尺寸以现行手册及实物试装为准。',34,MUTED)
    return c.save()

def shell():
    c=Canvas('pvc_43_shell_joint','图解 43｜桶壳拼接：前后壁夹入，底板嵌入且底面齐平','单位 mm｜固定桶壳全部用 3 mm 发泡 PVC；外形 160×150×180，未画实际角码和螺孔。',1550)
    c.text((140,160),'俯视：先无胶试拼四壁',42,bold=True)
    x,y,s=160,305,4.0
    w,h=160*s,150*s;t=3*s
    c.rect((x,y,x+w,y+h),None,MUTED,2)
    # P03 side walls span X=160; P04 end walls fit between them across Y=144.
    c.rect((x,y,x+w,y+t),BLUEF,BLUE,3)
    c.rect((x,y+h-t,x+w,y+h),BLUEF,BLUE,3)
    c.rect((x,y+t,x+t,y+h-t),ORANGEF,ORANGE,3)
    c.rect((x+w-t,y+t,x+w,y+h-t),ORANGEF,ORANGE,3)
    c.rect((x+t,y+t,x+w-t,y+h-t),GREENF,GREEN,2)
    c.dim_h(x,x+w,280,'外长 160',y,y)
    c.dim_v(y,y+h,91,'150',x)
    c.text((x+w/2,y+h/2-25),'P05 壳底\n154×144×3',46,GREEN,True,True)
    c.text((x+w/2,y+h/2+120),'底板嵌在四壁里面',36,GREEN,False,True)
    c.arrow([(480,390),(480,310)],BLUE,3)
    c.text((480,435),'P03 侧壁：160×180×3',36,BLUE,False,True)
    c.arrow([(480,815),(480,900)],BLUE,3)
    c.text((480,775),'P03 侧壁：160×180×3',36,BLUE,False,True)
    c.arrow([(285,1010),(168,930),(168,740)],ORANGE,3)
    c.arrow([(665,1010),(790,930),(794,740)],ORANGE,3)
    c.text((475,1050),'P04 后壁 / 前壁：各 144×180×3\n夹在两块 P03 侧壁之间',36,ORANGE,False,True)
    c.arrow([(520,1140),(800,1140)],BLUE,4)
    c.text((400,1140),'车头 +X',36,BLUE,False,True)
    c.text((140,1200),'前后壁宽：150 − 2×3 = 144',38)
    c.text((140,1260),'壳底长宽：154 × 144',38)
    c.text((140,1320),'154 = 160 − 2×3',38,MUTED)

    c.text((990,160),'沿 X 的竖剖面：底部做齐平',42,bold=True)
    sx,sy,ss=1030,305,3.3
    sw,sh,st=160*ss,180*ss,3*ss
    c.rect((sx,sy,sx+st,sy+sh),ORANGEF,ORANGE,3)
    c.rect((sx+sw-st,sy,sx+sw,sy+sh),ORANGEF,ORANGE,3)
    c.rect((sx+st,sy+sh-st,sx+sw-st,sy+sh),GREENF,GREEN,3)
    c.rect((sx-40,sy+sh,sx+sw+40,sy+sh+36),'#E7E3DA',MUTED,3)
    c.line([(sx-70,sy+sh),(sx+sw+70,sy+sh)],RED,3,dash=True)
    c.dim_v(sy,sy+sh,1660,'180',sx+sw)
    c.text((1290,470),'壁板高 180\n底板放在壁内',40,ORANGE,False,True)
    c.text((1290,690),'P05 厚 3',40,GREEN,True,True)
    c.arrow([(1290,743),(1290,889)],GREEN,3)
    c.text((1290,980),'P02 木平台：全面承托壳底',36,MUTED,False,True)
    c.text((990,1060),'红虚线 = P02 上表面\n四壁底缘与 P05 底面都落在此处。',36,RED)
    c.text((990,1185),'底板不垫在四壁下面；\n也不另加抬高底板的木条。',38)
    c.text((990,1310),'名义净口 154×144；\n装角码、螺母后须重测实际通道。',36,MUTED)
    c.line([(90,1400),(1710,1400)],GREY,3)
    c.text((90,1430),'四壁试拼方正 → 两对角线差值目标≤2 → 底面齐平 → 内胆实际放入、取出。',38)
    c.text((90,1492),'采用外侧短角码或局部加强片；孔位按实物标记，不占用内胆全高度取出通道。',34,MUTED)
    return c.save()

def lid():
    c=Canvas('pvc_44_lid_strip','图解 44｜活动盖用 2 mm 新板；后固定条仍用 3 mm 余料','单位 mm｜活动盖 P06 与固定压条是两件不同的零件；铰链让位和安装孔均按实物确定。',1500)
    c.text((120,160),'200×200×2 新板：只裁活动盖',42,bold=True)
    x,y,s=135,295,3.1
    c.rect((x,y,x+200*s,y+200*s),'#F6F8F9',MUTED,3)
    c.dim_h(x,x+200*s,278,'200',y,y)
    c.dim_v(y,y+200*s,80,'200',x)
    lx,ly=x+5*s,y+5*s
    c.rect((lx,ly,lx+160*s,ly+150*s),BLUEF,BLUE,4)
    c.text((lx+80*s,ly+75*s),'P06 活动盖\n160×150×2',46,BLUE,True,True)
    c.text((x+100*s,y+180*s),'余料保留试切、试钻',35,MUTED,False,True)
    c.text((120,970),'160 沿车身 X；150 沿横向 Y。',38)
    c.text((120,1035),'边缘修平、轻微圆角；先称裸盖。',38)
    c.text((120,1125),'裸盖目标 ≤30 g',42,BLUE,True)
    c.text((120,1190),'活动总成目标 ≤40 g；上限 45 g。',38,RED,True)
    c.text((120,1255),'盖、随盖臂、活动补强、紧固件等\n一起称量；取不出的活动铰链计入。',36)

    c.text((970,160),'闭盖俯视：覆盖关系示意',42,bold=True)
    # Nominal initial placement from M41, not an independently defined hinge drilling map.
    xx,yy,sc=1000,400,3.25
    def X(v):return xx+(v-64)*sc
    def Y(v):return yy+(v+75)*sc
    # Fixed strip X=64..74, lid X=75..235, shell X=70..230.
    c.rect((X(64),Y(-75),X(74),Y(75)), '#DEE5E9',MUTED,3)
    c.rect((X(75),Y(-75),X(235),Y(75)),BLUEF,BLUE,4)
    # Dashed shell projection makes the 5 mm front overhang visible.
    c.line([(X(70),Y(-75)),(X(230),Y(-75)),(X(230),Y(75)),(X(70),Y(75)),(X(70),Y(-75))],ORANGE,3,True)
    c.text((X(155),Y(0)-20),'活动盖 P06\n160×150×2',44,BLUE,True,True)
    c.text((X(155),Y(0)+115),'随盖运动并计入质量',36,BLUE,False,True)
    c.text((975,270),'固定条：150×(10～12)×3\n先以宽 10 试放，再按铰链让位。',36,MUTED)
    c.arrow([(1040,370),(X(69),Y(-50))],MUTED,3)
    c.arrow([(X(225),Y(60)),(1690,945)],ORANGE,3)
    c.text((1430,1000),'橙虚线：桶壳投影\n160×150',36,ORANGE,False,True)
    c.arrow([(X(235),Y(0)),(1690,Y(0))],BLUE,3)
    c.text((1640,Y(0)+85),'车头 +X\n前伸约 5',35,BLUE,False,True)
    c.text((970,1080),'盖后轴参考 X=75；固定条先试放\nX=64～74，与盖留约 1 的缝。',36)
    c.text((970,1195),'条固定在后壁 / 外角件上，\n不随盖运动、不承担连杆转矩。',36)
    c.text((970,1310),'孔位与让位口用真实铰链描出；\n手动全程开闭顺畅后再固定。',36)
    c.line([(90,1410),(1710,1410)],GREY,3)
    c.text((90,1440),'1 mm PP 只用于五片内胆，不用于本图的固定壳、活动盖或后固定条。',38,MUTED)
    return c.save()

if __name__=='__main__':
    check=verify_nesting()
    (OUT/'nesting_check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    a,b,c=nesting(),shell(),lid()
    meta=[
      dict(number=42,**a,caption='3 mm 发泡 PVC 排料：全部主要板件可在第一片裁出，第二片保留试切、补强和重做。',alt='第一片500毫米正方形板内排两侧壁160乘180、两前后壁144乘180、壳底154乘144、操作板190乘120、超声横梁150乘35、约180乘25触边横杠及150乘12固定条预留毛坯，间距和边距至少5毫米。第二片保持整张。',解释='尺寸依照第12章切件表；后固定条尺寸来自第07章与步骤051。图中150×12只是预留毛坯，最终宽10～12按实物铰链试装，步骤051先试宽10。所有固定件孔位均须实物描。',anchor='步骤 036 M26｜先划后切 PVC'),
      dict(number=43,**b,caption='桶壳拼接关系：144 mm 前后壁夹在侧壁之间，154×144 mm 底板嵌入，底面与四壁底缘齐平。',alt='俯视外长160外宽150，四周壁厚3，内底154乘144。剖面壁高180，底板厚3嵌在壁内，底面与壁板底缘共同落在木平台P02上，外高不增加。',解释='以现行切件表核算：150−2×3=144；160−2×3=154。外高180成立的条件是壳底嵌入且齐平。实际角码和螺母会占内通道，必须实物核对装袋PP内胆可进出。',anchor='步骤 037 M27｜四壁无胶试拼'),
      dict(number=44,**c,caption='2 mm 活动盖与3 mm 后固定条分开裁制，闭盖覆盖和铰链让位先试装，再按实物钻孔。',alt='200乘200乘2毫米发泡PVC裁160乘150活动盖。闭盖长边沿X，盖轴参考X75前缘X235，壳体后缘X70前缘X230，后固定条先试X64至74留约1毫米缝；固定条不会随盖运动。裸盖目标不超过30克，活动总成目标40克以内、上限45克。',解释='盖与固定条的参考坐标直接来自步骤051。实际铰链变化须同步修正盖覆盖关系与舵机轴位置；图不是铰链孔位模板。PP内胆为另用1mmPP，不混入PVC清单。',anchor='步骤 050 M40｜裁出新盖并称裸板')
    ]
    for m in meta:
        m['position']='before'
        m['source']='docs/manual/ASSEMBLY.md 第07—19章（现行168页Word对应文字）'
        m['sha256_png']=hashlib.sha256((OUT/m['filename']).read_bytes()).hexdigest()
        m['sha256_svg']=hashlib.sha256((OUT/m['svg']).read_bytes()).hexdigest()
        m['recommended_width_cm']=17.0
        m['height_at_recommended_width_cm']=round(17*m['png_height']/m['png_width'],2)
    (OUT/'figure_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(meta),'nesting':'PASS','dimensions':[(m['number'],m['png_width'],m['png_height']) for m in meta]},ensure_ascii=False))
