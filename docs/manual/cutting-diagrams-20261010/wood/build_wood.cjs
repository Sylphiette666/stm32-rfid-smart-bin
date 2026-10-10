const fs=require('fs');
const path=require('path');
const {chromium}=require('C:/Users/35462/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const OUT=__dirname;
const ink='#18344b',blue='#1568a8',green='#26795d',orange='#ac6017',gray='#687c8b';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;');
let a=[];
function start(h,title,sub){a=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="${h}" viewBox="0 0 1800 ${h}"><title>${esc(title)}</title><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M 8 0 L 0 4 L 8 8" fill="none" stroke="${gray}" stroke-width="1.2"/></marker><pattern id="hatch" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M-5,5 L5,-5 M0,20 L20,0 M15,25 L25,15" stroke="#dce3e8" stroke-width="2"/></pattern></defs><style>text{font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;font-size:34px} .small{font-size:32px} .bold{font-weight:700}</style><rect width="1800" height="${h}" fill="white"/>`];text(70,72,title,46,ink,'start',700);text(70,128,sub,34,gray);}
function end(file){a.push('</svg>');fs.writeFileSync(path.join(OUT,file+'.svg'),a.join('\n'));}
function text(x,y,t,size=34,fill=ink,anchor='start',weight=400){a.push(`<text x="${x}" y="${y}" font-size="${size}px" style="font-size:${size}px" fill="${fill}" text-anchor="${anchor}" font-weight="${weight}">${esc(t)}</text>`);}
function lines(x,y,ls,size=34,fill=ink,gap=48){ls.forEach((t,i)=>text(x,y+i*gap,t,size,fill));}
function rect(x,y,w,h,fill='#fff',stroke=ink,sw=3,dash=''){a.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"${dash?` stroke-dasharray="${dash}"`:''}/>`);}
function line(x1,y1,x2,y2,color=gray,sw=2,dash=''){a.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${sw}"${dash?` stroke-dasharray="${dash}"`:''}/>`);}
function circle(x,y,r,fill='none',stroke=ink,sw=3,dash=''){a.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"${dash?` stroke-dasharray="${dash}"`:''}/>`);}
function dimH(x1,x2,y,label){a.push(`<path d="M${x1},${y}H${x2}" fill="none" stroke="${gray}" stroke-width="2" marker-start="url(#arr)" marker-end="url(#arr)"/>`);line(x1,y-10,x1,y+10);line(x2,y-10,x2,y+10);text((x1+x2)/2,y-16,label,34,gray,'middle');}
function dimV(x,y1,y2,label){a.push(`<path d="M${x},${y1}V${y2}" fill="none" stroke="${gray}" stroke-width="2" marker-start="url(#arr)" marker-end="url(#arr)"/>`);line(x-10,y1,x+10,y1);line(x-10,y2,x+10,y2);a.push(`<text x="${x-16}" y="${(y1+y2)/2}" text-anchor="middle" style="font-size:34px" fill="${gray}" transform="rotate(-90 ${x-16} ${(y1+y2)/2})">${esc(label)}</text>`);}
function labelBox(x,y,w,ls,fill='#f3f7fa',color=ink){rect(x,y,w,ls.length*48+34,fill,'none',0);lines(x+20,y+43,ls,34,color);}

// Figure 40. Exact nesting matches diagram_spec.json, all coordinates measured from sheet lower-left.
start(1530,'图解 40  两张 300 × 300 × 5 mm 木板排料','全部尺寸为 mm；彩色轮廓是成品线。示意图非 1:1，须用尺重新划线。');
const sy=282,s=2.1,sh=630;
function sheet(x,num){text(x+315,188,`第 ${num} 张：300 × 300 × 5`,38,ink,'middle',700);rect(x,sy,630,630,'url(#hatch)',ink,3);dimH(x,x+630,258,'300');dimV(x-42,sy,sy+630,'300');text(x,957,'左下角为排料原点 (0, 0)',32,gray);}
function part(bx,x,y,w,h,fill,stroke,ls){const px=bx+x*s,py=sy+(300-y-h)*s;rect(px,py,w*s,h*s,fill,stroke,3);ls.forEach((v,i)=>text(px+w*s/2,py+h*s/2+(i-(ls.length-1)/2)*47+12,v,34,stroke,'middle',i===0?700:400));}
sheet(150,1);sheet(1020,2);
part(150,5,5,280,220,'#e7f1fb',blue,['P01 底板','280 × 220 × 5']);
part(150,5,230,190,60,'#fff0db',orange,['P11 舵机立架','190 × 60 × 5']);
part(150,200,230,80,40,'#e4f4ed',green,['80 × 40']);
text(660,323,'调节托片',32,green,'middle');line(660,328,660,341,green,2);
part(1020,5,5,240,190,'#e7f1fb',blue,['P02 上平台','240 × 190 × 5']);
rect(1030.5,292.5,609,199.5,'#f3f6f8',gray,2,'10 7');
text(1335,371,'余料保留，不预切小件',34,gray,'middle',700);
text(1335,421,'转接片 / 三角撑按实物做',32,gray,'middle');
// Highlight the actual 5 mm gap between P01 and the two small parts, without inventing saw kerf.
line(160.5, sy+72.5*s, 770, sy+72.5*s, '#c14332',3,'8 6');
text(440,500,'虚线所在废料带：宽 5',32,'#a33629','middle');
line(440,475,440,439,'#a33629',2);
text(80,1029,'逐件定位：坐标从各自整张木板左下角量起（不是装车坐标）',36,ink,'start',700);
const tx=80,ty=1053,cw=[170,380,450,640],rh=60;
const rows=[['原料','零件','成品左下角 (x, y)','成品长 × 宽 × 厚'],['第 1 张','P01 底板','(5, 5)','280 × 220 × 5'],['第 1 张','P11 舵机立架','(5, 230)','190 × 60 × 5；装车时 190 竖直'],['第 1 张','舵机调节托片','(200, 230)','80 × 40 × 5'],['第 2 张','P02 上平台','(5, 5)','240 × 190 × 5']];
rows.forEach((r,j)=>{let xx=tx;r.forEach((v,i)=>{rect(xx,ty+j*rh,cw[i],rh,j?'#ffffff':'#e9f0f6','#ccd6de',1);text(xx+14,ty+j*rh+41,v,32,ink,'start',j?400:700);xx+=cw[i];});});
lines(80,1412,['边缘与相邻成品至少留 5；锯片走尺寸线外侧的废料，最后锉到成品线。','先保住 P01 / P02 完整；余料不足以适配实物支架时另补小料，不能拼主要承载板。'],34,ink,48);
end('wood_40_nesting');

// Figure 41. Exact pillar holes, no invented fastener pattern for bought modules or mounts.
start(1920,'图解 41  两板四柱孔定位与实物描孔边界','从板件安装面俯视；车尾在左、车头在右。两板均用自身左下角为局部原点。');
const ps=2.4;
const p1={x:140,y:235,w:280,h:220},p2={x:1030,y:307,w:240,h:190};
function board(p,name){rect(p.x,p.y,p.w*ps,p.h*ps,'#fafcfe',ink,3);text(p.x+p.w*ps/2,195,name,38,ink,'middle',700);dimH(p.x,p.x+p.w*ps,p.y+p.h*ps+53,String(p.w));dimV(p.x-45,p.y,p.y+p.h*ps,String(p.h));text(p.x,p.y+p.h*ps+107,'(0, 0)  车尾侧',32,gray);text(p.x+p.w*ps,p.y+p.h*ps+107,'车头 →',32,gray,'end');}
board(p1,'P01  底板 280 × 220 × 5');board(p2,'P02  上平台 240 × 190 × 5');
function xy(p,x,y){return [p.x+x*ps,p.y+(p.h-y)*ps];}
function holes(p,hs){hs.forEach(([id,x,y],i)=>{const [xx,yy]=xy(p,x,y);circle(xx,yy,1.7*ps,'white',blue,3);line(xx-14,yy,xx+14,yy,blue,2);line(xx,yy-14,xx,yy+14,blue,2);const right=i%2===1;let dx,dy,anchor;if(p===p1){dx=right?-24:-12;dy=i<2?-20:44;anchor='end';}else{dx=right?-10:24;dy=i<2?-34:46;anchor=right?'middle':'start';}text(xx+dx,yy+dy,id,34,blue,anchor,700);});}
// Reference motor mounting regions only: dashed zones are NOT hole/slot cut lines.
for(const y of [10,180]){const [xx,yy]=xy(p1,45,y+30);rect(xx,yy,90*ps,30*ps,'#fff6e9',orange,2,'10 7');text(xx+45*ps,yy+50,'①',34,orange,'middle',700);}
const [bx,by]=xy(p1,240,110);circle(bx,by,40,'#fff6e9',orange,2,'10 7');text(bx,by+12,'②',34,orange,'middle',700);
text(458,490,'4 孔均为 ⌀3.4',36,blue,'middle',700);
text(458,540,'中线 yb = 110',32,gray,'middle');line(p1.x,p1.y+110*ps,p1.x+280*ps,p1.y+110*ps,gray,1,'10 10');
const [sx,sy2]=xy(p2,50,170);rect(sx,sy2,160*ps,150*ps,'#eaf5ef',green,2,'12 8');text(sx+192,sy2+137,'③ 桶壳定位',34,green,'middle',700);text(sx+192,sy2+187,'160 × 150 投影',32,green,'middle');text(sx+192,sy2+237,'不是切割开口',34,green,'middle');
holes(p1,[['H1',30,25],['H2',250,25],['H3',30,195],['H4',250,195]]);
holes(p2,[['H1',10,10],['H2',230,10],['H3',10,180],['H4',230,180]]);
text(80,938,'精确可加工的四柱孔：先测量画十字，再夹板配钻；孔径 ⌀3.4',36,blue,'start',700);
const c2=[150,500,500,490],t2y=961,rows2=[['孔号','P01 局部 (X, yb)','P02 局部 (xp, yp)','整机坐标 (X, Y)'],['H1','(30, 25)','(10, 10)','(30, −85)'],['H2','(250, 25)','(230, 10)','(250, −85)'],['H3','(30, 195)','(10, 180)','(30, +85)'],['H4','(250, 195)','(230, 180)','(250, +85)']];
rows2.forEach((r,j)=>{let x=80;r.forEach((v,i)=>{rect(x,t2y+j*60,c2[i],60,j?'white':'#e9f0f6','#ccd6de',1);text(x+16,t2y+j*60+41,v,34,ink,'start',j?400:700);x+=c2[i];});});
text(80,1310,'换算：yb = Y + 110；xp = X − 20；yp = yb − 15。X 向车头、Y 向舵机侧。',34,gray);
text(80,1378,'灰 / 橙 / 绿虚线是试摆或定位参考，均不是钻孔或切槽模板',36,ink,'start',700);
lines(80,1428,[
'① 电机支架先带轮试摆，参考轴心 X≈90；槽与转接孔只按实物覆盖范围描出。',
'② 前万向球参考接地点 X≈240、Y≈0；固定孔距与转接片按实物，不能照圈钻。',
'③ 桶壳在 P02 的局部左下角为 (50, 20)；外角码孔按实物，板面不切出矩形。',
'电池每条绑带两侧各 1 槽，建议 24×4、长边沿 X；槽间距按电池，模块孔亦实描。',
'舵机托片不可压住 H3 柱顶：按实物留检修孔 / 开口，再定位角码和托片固定孔。'
],34,ink,50);
rect(80,1710,1640,145,'#eff5fa','none',0);
lines(100,1756,['配钻顺序：① P01 测量标 4 孔并打导孔 → ② P02 按 (20, 15) 偏移夹牢',
'→ ③ 配钻至 ⌀3.4，逐孔穿临时螺钉防滑；4 颗 M3 螺钉应能自然穿入。'],34,ink,52);
text(80,1894,'成品外形目标误差 ±1 mm；本图非 1:1，不能直接打印贴板当钻孔模板。',32,gray);
end('wood_41_pillar_holes');

const manifest=[
{id:'wood_40',file:'wood_40_nesting.png',svg:'wood_40_nesting.svg',caption:'图解 40 两张木板排料：沿成品线外侧锯切，5 mm 留缝属于废料。',alt:'两张300×300×5毫米木板精确排料，第一张含280×220底板、190×60旋转立架及80×40托片，第二张含240×190上平台与保留余料；附排料原点与成品坐标表。',suggested_width_cm:17.5,anchor:'步骤 017 M07｜在板材上排版',position:'before',notes:['按基准 diagram_spec.json 的排料坐标绘制；不改变既有主要木件。','排料坐标独立于装车坐标。5 mm是余量及成品之间废料宽度，不是锯缝宽度。','余料转接件需以实际支架外形复核，未给定的孔距没有编造。']},
{id:'wood_41',file:'wood_41_pillar_holes.png',svg:'wood_41_pillar_holes.svg',caption:'图解 41 四柱孔位与配钻：两板局部坐标不同，其他安装孔按实物描出。',alt:'P01和P02俯视图及H1至H4坐标表，精确四柱孔径3.4毫米，展示P02相对P01的20和15毫米偏移，电机、万向球与桶壳以虚线试摆区域区分，绑带与模块安装孔按实物。',suggested_width_cm:17.5,anchor:'步骤 019 M09｜上下平台配钻立柱孔',position:'before',notes:['图中只有H1至H4是确定的钻孔。虚线位置不是固定支架原生孔距。','P02对应四孔为(10,10),(230,10),(10,180),(230,180)，与P01精确对齐。','H3柱顶须保留检修通道，托片固定孔不可照旧参考点盲钻。']}
];
fs.writeFileSync(path.join(OUT,'manifest.json'),JSON.stringify(manifest,null,2));
fs.writeFileSync(path.join(OUT,'figure_manifest.json'),JSON.stringify(manifest.map((m,i)=>({...m,number:40+i,filename:m.file,png_width_px:3600,png_height_px:i===0?3060:3840,svg_width:1800,svg_height:i===0?1530:1920,explanation:i===0?'先在两张整料上按表中原点量出四件成品边界；每一边锯片落在废料侧，磨到尺寸线。先裁大板，再裁余料小件，保留第二张余料适配实际支架。':'先按 P01 四孔坐标画十字并钻导孔；P02 后缘距底板后缘20 mm、两侧各退15 mm，夹牢后配钻至3.4 mm。电机、球轮、模块和绑带先按实物试摆，图中虚线不代表固定孔槽。'})),null,2));
const physical={units:'mm',sheet:[300,300,5],clearance:5,sheets:[[{id:'P01',x:5,y:5,w:280,h:220},{id:'P11',x:5,y:230,w:190,h:60},{id:'servo_shelf',x:200,y:230,w:80,h:40}],[{id:'P02',x:5,y:5,w:240,h:190}]],p01:[[30,25],[250,25],[30,195],[250,195]],p02:[[10,10],[230,10],[10,180],[230,180]],diameter:3.4,offset:[20,15]};
const checks=[];
for(const [i,parts] of physical.sheets.entries()){for(const p of parts){if(p.x<5||p.y<5||p.x+p.w>295||p.y+p.h>295)throw Error('edge clearance '+p.id);}for(let j=0;j<parts.length;j++)for(let k=j+1;k<parts.length;k++){const u=parts[j],v=parts[k];const gaps=[v.x-(u.x+u.w),u.x-(v.x+v.w),v.y-(u.y+u.h),u.y-(v.y+v.h)];if(Math.max(...gaps)<5)throw Error('part clearance '+u.id+v.id);}checks.push(`sheet ${i+1}: all parts inside sheet with >=5 mm edge clearance; pairwise gap >=5 mm`);}
physical.p02.forEach((p,i)=>{if(p[0]+20!==physical.p01[i][0]||p[1]+15!==physical.p01[i][1])throw Error('hole map');});
checks.push('four pillar holes align exactly after P02 offset (20,15)');
fs.writeFileSync(path.join(OUT,'geometry_checks.json'),JSON.stringify({source:'docs/manual/ASSEMBLY.md + .assembly-manual-20261010/diagram_spec.json',physical,checks},null,2));
(async()=>{const b=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});const p=await b.newPage({viewport:{width:1800,height:1920},deviceScaleFactor:2});const qa=[];for(const m of manifest){await p.goto('file:///'+path.join(OUT,m.svg).replaceAll('\\','/'));await p.evaluate(()=>document.fonts.ready);const out=await p.evaluate(()=>{const s=document.documentElement,box=s.viewBox.baseVal;const clipped=[...s.querySelectorAll('text')].filter(e=>{const b=e.getBBox();return b.x<0||b.x+b.width>box.width||b.y<0||b.y+b.height>box.height;}).map(e=>e.textContent);return {width:box.width,height:box.height,clipped};});await p.locator('svg').screenshot({path:path.join(OUT,m.file)});qa.push({file:m.file,...out});}fs.writeFileSync(path.join(OUT,'render_checks.json'),JSON.stringify(qa,null,2));console.log(JSON.stringify(qa,null,2));await b.close();})();
