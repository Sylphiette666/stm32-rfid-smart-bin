"""Route residual connections on a clearance raster; native DRC is final authority."""
from pathlib import Path
import json, math, heapq
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Point,LineString,box
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'checks/routing-obstacles.json').read_text(encoding='utf-8'))
STEP=.1; N=1001
def xy(v):return tuple(round((x-50)/STEP) for x in v)
def real(x,y):return [50+x*STEP,50+y*STEP]
def raster(shape,draw):
    if shape.is_empty:return
    if hasattr(shape,'geoms'):
        for s in shape.geoms:raster(s,draw)
    else:draw.polygon([xy(v) for v in shape.exterior.coords],fill=1)
def padshape(a):
    sx,sy=a['size'];x,y=a['pos']
    if a['shape']==0:s=Point(0,0).buffer(sx/2)
    elif a['shape']==2:
        if sx>=sy:s=LineString([(-(sx-sy)/2,0),((sx-sy)/2,0)]).buffer(sy/2)
        else:s=LineString([(0,-(sy-sx)/2),(0,(sy-sx)/2)]).buffer(sx/2)
    else:s=box(-sx/2,-sy/2,sx/2,sy/2)
    return translate(rotate(s,-a['angle'],origin=(0,0)),x,y)
def blocked(net):
    ims=[Image.new('1',(N,N)) for _ in range(2)];draw=[ImageDraw.Draw(i) for i in ims]
    for a in D['pads']:
        if a['net']!=net:
            s=padshape(a)
            for d in draw:raster(s,d)
    for t in D['tracks']:
        if t['net']==net:continue
        s=Point(t['start']).buffer(t['width']/2) if t['via'] else LineString([t['start'],t['end']]).buffer(t['width']/2)
        for i in ([0,1] if t['via'] else [0 if t['layer']=='F.Cu' else 1]):raster(s,draw[i])
    distances=np.stack([distance_transform_edt(~np.array(i,dtype=bool))*STEP for i in ims])
    clear=distances>.39
    clear[:,:8,:]=False;clear[:,-8:,:]=False;clear[:,:,:8]=False;clear[:,:,-8:]=False
    via=(distances>.70).all(axis=0)
    # New via holes must not overlap any existing drilled hole, including same net.
    for a in D['pads']:
        px,py=xy(a['pos']);radius=(max(a['drill'])/2+.2+.25)/STEP
        xmin=max(0,int(px-radius-1));xmax=min(N,int(px+radius+2));ymin=max(0,int(py-radius-1));ymax=min(N,int(py+radius+2))
        yy,xx=np.ogrid[ymin:ymax,xmin:xmax];via[ymin:ymax,xmin:xmax]&=(xx-px)**2+(yy-py)**2>radius**2
    return clear,via
def route(net,ref1,pin1,ref2,pin2):
    a=next(x for x in D['pads'] if x['ref']==ref1 and x['pin']==pin1)
    b=next(x for x in D['pads'] if x['ref']==ref2 and x['pin']==pin2)
    assert a['net']==net and b['net']==net
    sx,sy=xy(a['pos']);tx,ty=xy(b['pos']);clear,via=blocked(net);print(net,'destination',clear[:,ty,tx],flush=True)
    dist=np.full((2,N,N),np.inf);parents={};heap=[]
    def h(x,y):return math.hypot(x-tx,y-ty)
    for z in [0,1]:
        assert clear[z,sy,sx],(net,'blocked source',z)
        dist[z,sy,sx]=0;heapq.heappush(heap,(h(sx,sy),0,z,sx,sy))
    count=0;end=None
    while heap:
        _,cost,z,x,y=heapq.heappop(heap)
        if cost!=dist[z,y,x]:continue
        count+=1
        if x==tx and y==ty:end=(z,x,y);break
        moves=[(z,x+dx,y+dy,1.41421356237 if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
        if via[y,x]:moves.append((1-z,x,y,35))
        for nz,nx,ny,add in moves:
            if nx<0 or ny<0 or nx>=N or ny>=N or not clear[nz,ny,nx]:continue
            if nx!=x and ny!=y and (not clear[z,y,nx] or not clear[z,ny,x]):continue
            nc=cost+add
            if nc>=dist[nz,ny,nx]:continue
            dist[nz,ny,nx]=nc;parents[(nz,nx,ny)]=(z,x,y);heapq.heappush(heap,(nc+h(nx,ny),nc,nz,nx,ny))
    if end is None:
        for zz in [0,1]:
            img=np.zeros((N,N,3),dtype=np.uint8);img[clear[zz]]=[70,70,70];img[np.isfinite(dist[zz])]=[0,160,80];img[ty-2:ty+3,tx-2:tx+3]=[255,0,0];Image.fromarray(img).crop((tx-100,ty-100,tx+100,ty+100)).resize((800,800)).save(ROOT/'checks'/('blocked-'+str(zz)+'.png'))
        raise RuntimeError(('no path',net,count))
    path=[end]
    while path[-1] in parents:path.append(parents[path[-1]])
    path.reverse();groups=[];vias=[];group=[];prevz=path[0][0]
    for z,x,y in path:
        if z!=prevz:
            groups.append((prevz,group));vias.append(real(x,y));group=[(x,y)];prevz=z
        else:group.append((x,y))
    groups.append((prevz,group));segs=[]
    for z,pts in groups:
        simple=[pts[0]]
        for i in range(1,len(pts)-1):
            old=(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);new=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1])
            if old!=new:simple.append(pts[i])
        if len(pts)>1:simple.append(pts[-1])
        pp=[real(*t) for t in simple]
        if len(pp)>1:segs.append({'layer':'F.Cu' if z==0 else 'B.Cu','points':pp})
    segs[0]['points'][0]=a['pos'];segs[-1]['points'][-1]=b['pos']
    result={'net':net,'width':.25,'segments':segs,'vias':vias,'expanded':count}
    for seg in segs:
        for aa,bb in zip(seg['points'],seg['points'][1:]):D['tracks'].append({'net':net,'via':False,'width':.25,'layer':seg['layer'],'start':aa,'end':bb})
    for v in vias:D['tracks'].append({'net':net,'via':True,'width':.8,'layer':'F.Cu','start':v,'end':v})
    print(net,'states',count,'segments',sum(len(s['points'])-1 for s in segs),'vias',len(vias),flush=True)
    return result
result=[]
for spec in [('MCP_GPB1','J12','2','J33','5'),('PB1','R26','1','R25','2'),('VBAT_SW','J27','3','R1','1'),('MCP_GPA3','J11','4','J19','6')]:
    result.append(route(*spec));(ROOT/'checks/repair-routes.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
