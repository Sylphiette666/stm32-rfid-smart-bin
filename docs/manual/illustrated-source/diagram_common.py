from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, json

ROOT=Path(__file__).parent
FONT='C:/Windows/Fonts/msyh.ttc'
BOLD='C:/Windows/Fonts/msyhbd.ttc'
INK='#17252E'; MUTED='#566773'; BLUE='#1565A6'; RED='#C33D3D'; GREEN='#237655'; ORANGE='#B16916'; GREY='#DBE2E6'

class Diagram:
    def __init__(self,title,subtitle='',h=820):
        self.w,self.h=1800,h
        self.im=Image.new('RGB',(self.w,h),'white'); self.d=ImageDraw.Draw(self.im)
        self.text((40,20),title,48,bold=True)
        if subtitle:self.text((40,89),subtitle,30,color=MUTED)
    def font(self,s=34,bold=False):return ImageFont.truetype(BOLD if bold else FONT,s)
    def text(self,xy,txt,size=34,color=INK,bold=False,anchor=None):
        self.d.multiline_text(xy,str(txt),font=self.font(size,bold),fill=color,spacing=10,anchor=anchor)
    def center(self,box,txt,size=34,color=INK,bold=False):
        x0,y0,x1,y1=box; b=self.d.multiline_textbbox((0,0),str(txt),font=self.font(size,bold),spacing=10)
        self.text(((x0+x1-b[2]+b[0])/2,(y0+y1-b[3]+b[1])/2-b[1]),txt,size,color,bold)
    def rect(self,box,fill=None,outline=INK,width=3,radius=0):
        if radius:self.d.rounded_rectangle(box,radius,fill,outline,width)
        else:self.d.rectangle(box,fill,outline,width)
    def block(self,box,txt,fill='#F4F7F9',outline=INK,size=34):
        self.rect(box,fill,outline,3,10);self.center(box,txt,size)
    def line(self,points,color=INK,width=4):self.d.line(points,fill=color,width=width,joint='curve')
    def arrow(self,points,color=BLUE,width=5,head=17):
        self.line(points,color,width);x,y=points[-1];x0,y0=points[-2];a=math.atan2(y-y0,x-x0)
        self.d.polygon([(x,y),(x-head*math.cos(a-.45),y-head*math.sin(a-.45)),(x-head*math.cos(a+.45),y-head*math.sin(a+.45))],fill=color)
    def circle(self,xy,r=8,fill=INK,outline=None,width=2):
        x,y=xy;self.d.ellipse((x-r,y-r,x+r,y+r),fill,outline,width)
    def number(self,xy,n,color=BLUE):
        self.circle(xy,27,color);self.text((xy[0],xy[1]-2),str(n),32,'white',True,'mm')
    def dim(self,a,b,label,offset=(0,-45),color=MUTED):
        self.arrow([a,b],color,3,12);self.arrow([b,a],color,3,12)
        self.text(((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1]),label,31,color,anchor='mm')
    def footer(self,txt):self.text((40,self.h-55),txt,29,MUTED)
    def save(self,name):
        p=ROOT/'figures'/f'{name}.png';p.parent.mkdir(exist_ok=True);self.im.save(p,dpi=(254,254));return str(p)

def manifest(name,items):
    (ROOT/f'{name}_figures.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
