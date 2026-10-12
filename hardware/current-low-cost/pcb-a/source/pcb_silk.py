"""Collision-aware native KiCad silkscreen placement, called by pcb_native."""
import math,json
import pcbnew as p
REMOVED=[]
def mm(v):return p.ToMM(v)
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def bbox(item,pad=0):
    a=item.GetBoundingBox();return [mm(a.GetX())-pad,mm(a.GetY())-pad,mm(a.GetRight())+pad,mm(a.GetBottom())+pad]
def hit(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def finalize(b,root):
    for t in list(b.GetDrawings()):
        if isinstance(t,p.PCB_TEXT):REMOVED.append(t);b.Remove(t)
    obs={p.F_SilkS:[],p.B_SilkS:[]};used={p.F_SilkS:[],p.B_SilkS:[]}
    for fp in b.GetFootprints():
        fp.Reference().SetVisible(False)
        for pad in fp.Pads():
            for layer in obs:obs[layer].append(bbox(pad,.23))
        for g in fp.GraphicalItems():
            if g.GetLayer() in obs and g.GetClass()!='PCB_FIELD':obs[g.GetLayer()].append(bbox(g,.16))
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':
            for layer in obs:obs[layer].append(bbox(t,.23))
    def put(t,orig,layer,size=1,preferred=None,radius=8):
        t.SetVisible(True);t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.15))
        offsets=[(0,0)] if preferred is None else preferred
        offsets=offsets+sorted([(dx*.5,dy*.5) for dx in range(-int(radius*2),int(radius*2)+1) for dy in range(-int(radius*2),int(radius*2)+1)],key=lambda a: a[0]**2+a[1]**2)
        for dx,dy in offsets:
            for angle in [0,90]:
                t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
                t.SetPosition(v(orig[0]+dx,orig[1]+dy));bb=bbox(t,.18)
                if bb[0]<50.8 or bb[1]<50.8 or bb[2]>149.2 or bb[3]>149.2:continue
                if any(hit(bb,o) for o in obs[layer]+used[layer]):continue
                used[layer].append(bb);return True
        return False
    def label(txt,pos,layer=p.F_SilkS,size=1,radius=3):
        t=p.PCB_TEXT(b);t.SetText(txt)
        if not put(t,pos,layer,size,radius=radius):raise RuntimeError('Cannot place '+txt)
        b.Add(t);return t
    label('SMARTBIN A1  100x100', (100,52),size=1.1,radius=1)
    label('PIN 1 = SQUARE PAD', (100,54.2),radius=1)
    label('SMARTBIN A1 - SOLDER SIDE', (100,52),p.B_SilkS,size=1.1,radius=1)
    label('PIN 1 = SQUARE PAD', (100,54.2),p.B_SilkS,radius=1)
    refs={};failed=[]
    fps=sorted(b.GetFootprints(),key=lambda f:(not f.GetReference().startswith('J'),not f.GetReference().startswith('U'),f.GetReference()))
    for fp in fps:
        ref=fp.GetReference()
        if ref.startswith('H'):continue
        pp=list(fp.Pads());xs=[mm(a.GetPosition().x) for a in pp];ys=[mm(a.GetPosition().y) for a in pp];x=(min(xs)+max(xs))/2;y=(min(ys)+max(ys))/2
        t=fp.Reference()
        if not put(t,(x,y),p.F_SilkS,radius=18):failed.append(ref)
        refs[ref]={'top':[mm(t.GetPosition().x)-50,mm(t.GetPosition().y)-50],'angle':t.GetTextAngle().AsDegrees()}
        label(ref,(x,y),p.B_SilkS,radius=12)
    for txt,pos in [('BAT',(65,63)),('BUCK IN',(65,77)),('5V IN',(65,91)),('MOTOR',(65,105)),('SERVO',(65,119)),('LOGIC',(65,132))]:
        label(txt,pos,p.F_SilkS,radius=6)
    if failed:raise RuntimeError('Unplaced refs '+','.join(failed))
    (root/'checks/silk-placement.json').write_text(json.dumps(refs,indent=2),encoding='utf-8')
