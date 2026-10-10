from pathlib import Path
import json, math, re
from diagram_common import Diagram, INK, MUTED, BLUE, RED, GREEN, ORANGE, GREY, ROOT

FIGS=[]
paragraphs=[]
for line in (ROOT/'original_paragraphs.txt').read_text(encoding='utf-8').splitlines():
    parts=line.split('\t',2)
    if len(parts)==3: paragraphs.append(parts[2])

def anchor(step):
    hits=[p for p in paragraphs if re.match(rf'^步骤\s+0*{step}\s',p)]
    assert len(hits)==1,(step,hits)
    return hits[0]

def new(title,sub):
    d=Diagram(title)
    d.text((40,90),sub,32,color=MUTED)
    return d

def label(d,xy,text,size=32,color=INK,bold=False):
    d.text(xy,text,size,color,bold)

def finish(d,id,step,caption,alt):
    d.save(id)
    FIGS.append(dict(id=id,file=f'figures/{id}.png',anchor=anchor(step),position='before',caption=caption,alt=alt))

def double(d,a,b,text,xy,color=MUTED):
    d.arrow([a,b],color,3,12); d.arrow([b,a],color,3,12)
    label(d,xy,text,32,color)

def check(d,x,y,color=GREEN):
    d.line([(x,y),(x+12,y+13),(x+36,y-20)],color,7)

def cross(d,x,y,color=RED):
    d.line([(x-14,y-14),(x+14,y+14)],color,6)
    d.line([(x-14,y+14),(x+14,y-14)],color,6)

def s01():
    d=new('S01  分级调试：每过一关，再接下一组','已完成前文电源单独调压与空载检查。断电接线，每过一级再接下一组。')
    xs=[40,395,750,1105,1460]
    names=['最小核心','电源与 I²C','RFID 与存储','执行器架空','整机落地']
    detail=['SWD 能下载\n串口有计数','测 5 V / 3.3 V\nMCP / OLED / MPU','RC522 读卡\nFLASH 读写回读','电机先 10%\n舵机卸下连杆','低速直行\n循迹与投放']
    for i,x in enumerate(xs):
        d.number((x+28,180),i+1)
        d.center((x,225,x+300,275),names[i],38,bold=True)
        if i==0:
            d.rect((x+100,310,x+200,385),'#EAF2F8',BLUE,4)
            for j in range(4):
                yy=320+j*18;d.line([(x+75,yy),(x+100,yy)],BLUE,4);d.line([(x+200,yy),(x+225,yy)],BLUE,4)
            label(d,(x+118,331),'MCU',32,BLUE)
        elif i==1:
            d.line([(x+40,347),(x+270,347)],BLUE,5)
            for xx in [x+60,x+145,x+230]:
                d.line([(xx,347),(xx,310)],BLUE,4);d.rect((xx-25,290,xx+25,320),'#EAF2F8',BLUE,3)
            label(d,(x+72,363),'共地 / 扫地址',32)
        elif i==2:
            d.rect((x+28,310,x+132,380),'#EAF2F8',BLUE,4,8)
            d.rect((x+178,310,x+280,380),'#EAF5EE',GREEN,4,8)
            label(d,(x+42,331),'UID',32,BLUE);label(d,(x+181,331),'CRC',32,GREEN)
            d.arrow([(x+138,345),(x+169,345)],GREEN,4)
        elif i==3:
            d.circle((x+85,345),38,'white',BLUE,6);d.circle((x+215,345),38,'white',BLUE,6)
            d.line([(x+85,386),(x+85,410),(x+215,410),(x+215,386)],MUTED,4)
            d.line([(x+110,410),(x+75,433)],MUTED,4);d.line([(x+190,410),(x+225,433)],MUTED,4)
        else:
            d.rect((x+82,305,x+218,375),'#EAF2F8',BLUE,4,6)
            d.circle((x+98,390),20,INK);d.circle((x+202,390),20,INK)
            d.line([(x+30,420),(x+270,420)],MUTED,4)
        d.center((x,455,x+300,552),detail[i],32)
        if i<4:d.arrow([(x+312,250),(xs[i+1]-14,250)],GREEN,5)
        d.arrow([(x+150,570),(x+150,638)],RED,4)
    d.rect((40,642,1760,725),'#FFF1F1',RED,3,8)
    d.center((40,642,1760,725),'未通过 → 保持电机 PWM=0、PB5=0 → 本级查接线 / 供电 / 日志 → 复测本级',34,RED)
    label(d,(40,763),'通过标准：每一级都有实测结果；电机和舵机不能在最小程序阶段就全部接上。',32,MUTED)
    finish(d,'s01_debug_order',198,'按图从左向右调试。一个模块失败时先保留已通过的配置，排查该级；所有级别通过才做整机功能演示。','五级调试流程从最小核心、电源和I2C、RFID与存储、架空执行器到低速整机；每级失败向下进入共同停止排查流程。')

def s02():
    d=new('S02  两种 PWM：频率相差 400 倍，接口不能接错','横轴分别标尺：舵机看毫秒，电机驱动看微秒；下面的波形只画控制信号。')
    label(d,(40,211),'PA0 → AHCT125\n→ SG90 信号端',34,BLUE,True)
    label(d,(40,318),'50 Hz\n周期 20 ms',34,BLUE)
    x0,x1=400,1640
    high,low=215,315
    pulse=93
    d.line([(x0,low),(x0,high),(x0+pulse,high),(x0+pulse,low),(x1,low),(x1,high),(1740,high)],BLUE,6)
    d.arrow([(645,174),(520,174),(477,211)],BLUE,3)
    label(d,(650,150),'中位示意：高电平 1.5 ms（1500 µs）',32,BLUE)
    double(d,(x0,366),(x1,366),'完整周期 20 ms',(830,376),BLUE)
    d.line([(40,442),(1760,442)],GREY,3)
    label(d,(40,490),'PA8 / PA11\n→ TB6612 PWMA/B',34,ORANGE,True)
    label(d,(40,602),'20 kHz\n周期 50 µs',34,ORANGE)
    d.line([(400,604),(400,504),(700,504),(700,604),(1000,604),(1000,504),(1300,504),(1300,604),(1600,604),(1600,504),(1740,504)],ORANGE,6)
    double(d,(400,663),(1000,663),'周期 50 µs',(590,674),ORANGE)
    label(d,(1050,665),'此处仅画 50% 占空比示例',32,ORANGE)
    label(d,(40,760),'电机首次架空试转按手册从 10% 起；舵机端点必须卸载、小步实测，不能按波形猜。',32,MUTED)
    finish(d,'s02_pwm_compare',205,'先核对定时器和引脚，再核对实际波形。SG90是20 ms周期、约1.5 ms中位脉冲；TB6612电机PWM周期是50 µs，不能互接。','上下两种波形对比：舵机50Hz中位1.5ms高电平、20ms周期；电机20kHz周期50微秒，图示50%仅为解释。')

def s03():
    d=new('S03  刷卡投放闭环：先确认账本成功，再延时关盖','下图只对应积分模式；没有完整投放事件就不提交积分。')
    xs=[40,485,930,1375];w=385
    top=[('① 停车待卡','无故障 / 未满'),('② 接受有效卡','锁定 UID 与 txid'),('③ 渐变开盖','约 1.2 s 到标定位置'),('④ 光束准备','先连续畅通 200 ms')]
    bot=[('⑧ 闭盖确认','PB14 有效后结束'),('⑦ 成功提示 +1','等待 2 s 再复核光束'),('⑥ FLASH 提交','回读确认才生效'),('⑤ 检测完整经过','遮挡后重新畅通')]
    for x,(a,b) in zip(xs,top):
        d.block((x,185,x+w,305),a+'\n'+b,'#EAF2F8',BLUE,32)
    for x,(a,b) in zip(xs,bot):
        d.block((x,417,x+w,537),a+'\n'+b,'#EAF5EE',GREEN,32)
    for i in range(3):d.arrow([(xs[i]+w+8,245),(xs[i+1]-8,245)],BLUE,5)
    d.arrow([(1565,310),(1565,406)],BLUE,5)
    for i in range(3,0,-1):d.arrow([(xs[i]-8,477),(xs[i-1]+w+8,477)],GREEN,5)
    d.arrow([(225,542),(225,585),(980,585)],GREEN,4)
    label(d,(995,562),'移卡后稳定离场 500 ms\n才允许下一次新会话',32,GREEN)
    d.center((40,650,1760,728),'10 s 无投放：不加分退出；持续挡光：保持开盖提示；提交失败：不提示积分成功。',32,RED)
    label(d,(40,763),'通过标准：重复演示 10 次，有效会话恰好 +10；提交中换卡、再次遮挡都不能另加分。',32,MUTED)
    finish(d,'s03_rfid_session',247,'跟随箭头逐步观察屏幕和串口。正文规定FLASH事务回读确认后才更新积分并提示成功，随后延时关盖；关盖开关确认前不得移动。','八个状态用折返箭头相连，从停车待卡、锁定身份、开盖、光束准备到完整经过、FLASH提交、成功提示和闭盖确认；异常不加分。')

def s04():
    d=new('S04  一次会话只能记一笔：看事件，不数遮挡次数','时序示意，横轴不按比例；遮挡电平先按实际模块归一成 BLOCK / CLEAR。')
    x0,xend=320,1720
    for yy in [235,400,580]:d.arrow([(x0,yy+42),(xend,yy+42)],GREY,3,12)
    label(d,(40,193),'卡片在场',34,BLUE,True)
    d.line([(320,260),(380,260),(380,195),(1510,195),(1510,260),(1720,260)],BLUE,6)
    label(d,(480,202),'一直贴卡：仍只有一个 user_id / txid',32,BLUE)
    label(d,(1515,199),'移开',32,BLUE)
    label(d,(40,367),'投放光束',34,INK,True)
    label(d,(40,418),'高：CLEAR\n低：BLOCK',32,MUTED)
    d.line([(320,360),(660,360),(660,442),(830,442),(830,360),(1080,360),(1080,442),(1150,442),(1150,360),(1300,360),(1300,442),(1380,442),(1380,360),(1720,360)],INK,6)
    double(d,(385,321),(653,321),'先畅通≥200 ms',(350,276),BLUE)
    double(d,(664,490),(826,490),'30 ms 至 2 s',(628,501),BLUE)
    double(d,(834,321),(1040,321),'再畅通≥100 ms',(800,276),BLUE)
    label(d,(1120,474),'再次晃动 / 连续放第二件\n本会话不再触发另一笔',32,RED)
    label(d,(40,602),'事务层',34,GREEN,True)
    d.arrow([(382,620),(1015,620)],GREEN,4)
    label(d,(430,566),'尚未提交',32,MUTED)
    d.block((1045,568,1490,687),'仅一次 txn_begin\n提交成功后积分 +1','#EAF5EE',GREEN,32)
    d.arrow([(1500,622),(1720,622)],GREY,4)
    cross(d,1600,622)
    label(d,(1350,701),'后续边沿不再记账',32,RED)
    label(d,(40,761),'无遮挡、只遮挡未释放、超长挡光都不是有效投放；物体/手的区分属于本方案检测局限。',32,MUTED)
    finish(d,'s04_deposit_timing',248,'先观察CLEAR至少200 ms，再观察一次30 ms至2 s的BLOCK及至少100 ms的CLEAR。成功后在同一会话内再晃动物体，余额应保持不再增加。','卡片在场、投放光束和事务三个时序轨迹；首次完整遮挡后只提交一次，随后重复遮挡不形成第二笔积分。')

def s05():
    d=new('S05  满桶标定：先量真实袋口，再设置超声阈值','剖面为安装关系示意、不按比例；65 / 85 mm 是首轮候选值，必须实测替换。')
    # sensor and open bin cross-section
    d.rect((310,172,550,229),'#EAF2F8',BLUE,4,8)
    d.circle((365,201),20,'white',BLUE,4);d.circle((495,201),20,'white',BLUE,4)
    label(d,(590,179),'探头声学参考面',32,BLUE)
    d.line([(430,231),(430,628)],BLUE,3)
    d.arrow([(430,590),(430,628)],BLUE,4)
    d.line([(230,330),(230,647),(670,647),(670,330)],INK,6)
    d.line([(205,330),(260,330),(260,621),(640,621),(640,330),(695,330)],MUTED,4)
    d.line([(230,330),(670,330)],MUTED,3)
    label(d,(45,276),'真实袋口',32,MUTED)
    d.arrow([(182,315),(222,330)],MUTED,3)
    # calibration planes
    d.line([(267,377),(633,377)],RED,6)
    label(d,(650,383),'满位纸板',32,RED)
    d.line([(267,432),(633,432)],GREEN,6)
    label(d,(660,425),'下移 20 mm',32,GREEN)
    double(d,(740,330),(740,377),'15 mm',(765,336),RED)
    double(d,(157,332),(157,647),'内胆高\n121 mm',(50,470),MUTED)
    double(d,(298,234),(298,621),'D_empty',(470,555),BLUE)
    d.rect((220,668,680,705),'#EFF2F4',MUTED,3)
    label(d,(365,710),'平台',32,MUTED)
    d.number((937,202),1);label(d,(980,180),'在袋口下 15 mm 放平纸板\n停车、闭盖，采 30 次有效读数',32)
    d.number((937,327),2);label(d,(980,305),'将纸板再降低 20 mm\n测出清满回差点',32)
    d.number((937,452),3);label(d,(980,430),'首轮候选：65 mm 判满\n85 mm 清满；按实测改参数',32)
    d.number((937,577),4);label(d,(980,555),'空桶测袋底距离 D_empty\n袋褶 / 横梁不能挡住探头',32)
    label(d,(927,676),'无有效回波 → 显示未知并禁新投放',32,RED)
    label(d,(40,763),'通过标准：纸板仍低于袋口就可靠报满；清桶后恢复有回差，不能照抄旧桶的 45 / 65 mm。',32,MUTED)
    finish(d,'s05_full_calibration',254,'图中红线用于判满标定，绿线用于清满回差。先把实际垃圾袋固定好，再拿平纸板测量；65/85 mm只是候选，填写实际校准结果。','超声探头位于121mm内胆上方，真实袋口下15mm放满位纸板，再下降20mm测清满点；旁注65和85mm候选需实测。')

def s06():
    d=new('S06  故障解除不等于继续运动：必须再确认、再发命令','任何时刻收到停止条件都优先停轮；恢复路线、松开急停或重连蓝牙不自动起步。')
    boxes=[(60,180,530,282),(665,180,1135,282),(1270,180,1740,282)]
    for box,txt in zip(boxes,['急停按下 / 急停线断\nPB13 = 1','碰撞开关触发\nPB12 输入触发','倾斜超限 / 姿态失效\n由 MPU 检测']):d.block(box,txt,'#FFF1F1',RED,32)
    for x in [295,900,1505]:d.arrow([(x,287),(x,320),(900,320),(900,356)],RED,4)
    d.block((270,360,1530,475),'立即令电机 PWM = 0、PB5 = 0\n记录故障并锁停；急停另有硬件拉低 STBY 的通路','#FFF1F1',RED,36)
    d.arrow([(900,481),(900,511),(280,511),(280,552)],RED,4)
    d.block((60,558,505,687),'① 排除触发原因\n仍保持 STOP','#F4F7F9',MUTED,34)
    d.block((677,558,1122,687),'② 人工 BACK 确认\n全部互锁有效','#EAF2F8',BLUE,34)
    d.block((1295,558,1740,687),'③ 新的运行命令\n才允许起步','#EAF5EE',GREEN,34)
    d.arrow([(512,623),(667,623)],BLUE,5)
    d.arrow([(1130,623),(1285,623)],GREEN,5)
    label(d,(40,763),'通过标准：架空慢转时触发故障会停；松开后等待也不转，确认且重新发命令后才动作。',32,MUTED)
    finish(d,'s06_stop_latch',266,'轮子架空测试急停与碰撞，再测试倾角。停止后先消除原因，再人工确认，最后发送新的运行命令；任何一次自动续跑都不通过。','三类停止事件汇入PWM和PB5清零及故障锁存，再经过排除原因、人工确认和新运行指令三个门槛恢复。')

def s07():
    d=new('S07  三探头循迹与站点计数：只走已铺好的无岔路线','黑胶带主线宽 18 mm；图示俯视，不按比例。起点由人指定，不是自由导航。')
    label(d,(65,166),'普通主线：010',36,BLUE,True)
    d.line([(370,267),(370,345)],INK,26)
    d.rect((160,270,580,345),None,BLUE,3,10)
    for xx,name,val in [(220,'L','0'),(370,'C','1'),(520,'R','0')]:
        d.circle((xx,307),26,GREEN if val=='1' else 'white',BLUE,3)
        label(d,(xx-14,353),val,34,BLUE,True);label(d,(xx-13,228),name,32)
    label(d,(65,449),'站点宽条：111',36,GREEN,True)
    d.line([(370,490),(370,584)],INK,26)
    d.rect((175,538,565,584),INK,INK,1)
    for xx in [220,370,520]:d.circle((xx,560),26,GREEN,BLUE,3);label(d,(xx-12,604),'1',34,GREEN,True)
    label(d,(50,650),'宽条须盖住三探头\n沿行驶方向先取 30—40 mm',32)
    d.line([(790,170),(790,725)],GREY,3)
    # closed route and travel direction
    d.d.rounded_rectangle((960,260,1680,635),radius=150,outline=INK,width=20)
    d.arrow([(1170,625),(1310,625)],BLUE,7,24)
    d.arrow([(1670,515),(1670,462)],BLUE,7,22)
    d.arrow([(1430,270),(1330,270)],BLUE,7,22)
    # station 1 along vertical right section, station 2 along horizontal top section
    d.rect((1625,374,1730,417),INK,INK,1)
    label(d,(1460,320),'1 号站',36,GREEN,True)
    d.rect((1210,215,1255,315),INK,INK,1)
    label(d,(1110,170),'2 号站',36,GREEN,True)
    d.circle((1110,625),13,BLUE)
    label(d,(987,678),'人工起点：计数清 0',32,BLUE)
    label(d,(1070,350),'先选目标 1 或 2\n111 持续 80 ms → 只计一次\n离条回主线 300 ms 才解锁\n到目标 → 停车后服务',32)
    label(d,(40,763),'通过标准：慢过站条也不重复计数；断线 / 歧义就锁停。变更路线后重设起点，不自动返航。',32,MUTED)
    finish(d,'s07_line_stations',275,'先把三个探头分别放到白底和18 mm黑胶带上核对0/1。路线无岔路，站点用宽条；每次从人工起点出发清零，选择第一或第二站。','左侧俯视三探头中间压主线为010、横向宽站条覆盖三探头为111；右侧闭合固定路线标起点、1号和2号站与行进方向。')

def s08():
    d=new('S08  FLASH 掉电恢复：只认完整提交的记录','示例：原余额 10，本次有效投放 +1。测试前禁用电机、断开舵机支路。')
    xs=[40,640,1240];w=520
    titles=['断电前：旧记录有效','中途掉电：新记录无效','提交完成：新记录有效']
    for i,x in enumerate(xs):
        d.center((x,168,x+w,215),titles[i],34,bold=True)
        d.rect((x+28,243,x+w-28,510),'#F7F9FA',MUTED,3,8)
        d.rect((x+50,267,x+w-50,323),'#EAF5EE',GREEN,2,4)
        d.center((x+50,267,x+w-50,323),'旧快照 / 旧已提交日志',32,GREEN)
        if i==0:
            d.center((x+50,350,x+w-50,474),'尚无本次新事务\n旧记录保留不变',34)
        elif i==1:
            d.rect((x+50,346,x+w-50,400),'#FFF1F1',RED,2,4)
            d.center((x+50,346,x+w-50,400),'正文不完整 / CRC 失败',32,RED)
            d.rect((x+50,418,x+w-50,476),'#FFF1F1',RED,2,4)
            d.center((x+50,418,x+w-50,476),'或 commit 尚未完成',32,RED)
        else:
            d.rect((x+50,346,x+w-50,400),'#EAF5EE',GREEN,2,4)
            d.center((x+50,346,x+w-50,400),'正文完整 + CRC 正确',32,GREEN)
            d.rect((x+50,418,x+w-50,476),'#EAF5EE',GREEN,2,4)
            d.center((x+50,418,x+w-50,476),'commit 最后写入并有效',32,GREEN)
        d.arrow([(x+w/2,520),(x+w/2,575)],BLUE,5)
        d.block((x+25,585,x+w-25,678),'重启恢复：'+('10 分' if i<2 else '11 分'),'#EAF2F8',BLUE,38)
    label(d,(40,704),'正文 + CRC 先写；提交字最后单独写。仅 CRC 对但提交字无效的记录，也必须跳过。',32,RED)
    label(d,(40,763),'通过标准：真实切断核心与 FLASH 电源再启动，只恢复 10 或 11；同一 txid 不得再重放加分。',32,MUTED)
    finish(d,'s08_flash_recovery',235,'先保存测试前余额和日志，再在手册规定的检查点切总电源。重启只能得到旧完整状态10或本次完整状态11；有CRC但缺提交字也不能入账。','三个存储示意栏对比旧有效记录、中途掉电导致新记录不完整或未提交、完整新记录含有效CRC及最后写入的提交标志；重启余额分别10、10、11。')

if __name__=='__main__':
    for f in [s01,s02,s03,s04,s05,s06,s07,s08]:f()
    (ROOT/'software_figures.json').write_text(json.dumps(FIGS,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(FIGS),'manifest':str(ROOT/'software_figures.json')},ensure_ascii=False))
