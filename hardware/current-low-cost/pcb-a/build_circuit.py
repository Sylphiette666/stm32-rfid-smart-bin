import json,csv,pathlib,collections,hashlib

OUT=pathlib.Path(__file__).parent
ROOT=pathlib.Path(r'D:\Work\嵌入式课设')
REPO=ROOT/'stm32-rfid-smart-bin'
parts=[]
connectors=[]
FP_R='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'
FP_C='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_E='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm'
def part(ref,kind,value,pins,group,notes='',dnp=False,**kw):
    default={'resistor':('Device:R',FP_R),'capacitor':('Device:C',FP_C),'electrolytic':('Device:C_Polarized',FP_E),'npn':('Transistor_BJT:2N3904','Package_TO_SOT_THT:TO-92_Inline_Wide'),'logic':('74xx:74AHCT125','Package_DIP:DIP-14_W7.62mm_Socket')}
    sym,fp=default.get(kind,('',''))
    p={'ref':ref,'kind':kind,'value':value,'symbol':sym,'footprint':fp,'pins':{str(k):v for k,v in pins.items()},'pin_names':{},'group':group,'notes':notes,'dnp':dnp}
    p.update(kw);parts.append(p);return p
def R(n,val,a,b,grp,notes='',dnp=False,old=None):
    return part('R'+str(n),'resistor',val,{'1':a,'2':b},grp,notes,dnp,original_ref=old or '',power_rating_W=0.25,tolerance='1%' if n in (1,2,20,21) else '5% or better')
def C(n,val,a,b,grp,polar=False,notes='',old=None):
    return part('C'+str(n),'electrolytic' if polar else 'capacitor',val,{'1':a,'2':b},grp,notes,pin_names={'1':'+' if polar else '1','2':'-' if polar else '2'},original_ref=old or '',voltage_rating_V=16 if polar else 25)
def J(n,name,nets,grp,notes,targets=None,power=False):
    ref='J'+str(n);N=len(nets)
    p=part(ref,'connector',name,dict(enumerate(nets,1)),grp,notes,
           symbol=f'Connector_Generic:Conn_01x{N:02d}',
           footprint='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal' if power else f'Connector_PinHeader_2.54mm:PinHeader_1x{N:02d}_P2.54mm_Vertical',
           pin_names={str(i):net for i,net in enumerate(nets,1)},connector_type='THT screw terminal 2P 5.08mm' if power else f'custom 1x{N} 2.54mm signal header',high_current=power)
    connectors.append({'ref':ref,'name':name,'notes':notes,'targets':{str(i):x for i,x in enumerate(targets or nets,1)},'high_current':power})
    return p
def JP(n,name,nets,grp,default,allowed,notes):
    N=len(nets)
    return part('JP'+str(n),'jumper',name,dict(enumerate(nets,1)),grp,notes,
                symbol=f'Connector_Generic:Conn_01x{N:02d}',
                footprint=f'Connector_PinHeader_2.54mm:PinHeader_1x{N:02d}_P2.54mm_Vertical',
                pin_names={str(i):net for i,net in enumerate(nets,1)},default_shunt=default,allowed_shunts=allowed)

# Six original power terminal groups; 5 V branches are one net but routed as a star.
J(1,'BAT_SW',['VBAT_SW','GND'],'power','电池保护板输出正极经外置保险座和总开关后进入1脚；2脚为电池负极。禁止接未经保险的裸电池。',['外置总开关输出','电池负极'],True)
J(2,'BUCK_IN',['VBAT_SW','GND'],'power','外置非隔离5V降压输入；20AWG短线。',['降压IN+','降压IN-'],True)
J(3,'BUCK_OUT',['5V_BUS','GND'],'power','外置降压输出，接入板上星形中心。电池满电8.4V不能接此口。',['降压OUT+','降压OUT-'],True)
J(4,'MOTOR_PWR',['5V_BUS','GND'],'power','电机主电流支路；22AWG短线，长线/偏大电流用20AWG。',['TB6612 VM','TB6612动力GND'],True)
J(5,'SERVO_PWR',['5V_BUS','GND'],'power','舵机主电流仅走本支路；原3芯舵机延长线在配电处分离电源与信号。',['SG90红线/正极','SG90棕或黑线/负极'],True)
J(6,'LOGIC_PWR',['5V_BUS','GND'],'power','逻辑5V支路；可给DFPlayer和3.3V稳压输入等可靠分线，不把多根线强塞一只端子。',['逻辑电源分配正极','逻辑电源分配地'],True)
C(1,'470uF/16V','5V_BUS','GND','power',True,'靠近J4；若驱动距板较远，驱动VM端仍补就地电容。','PWR:CP1')
C(2,'1000uF/16V','5V_BUS','GND','power',True,'靠近J5；尺寸暂按直径12.5mm、脚距5mm预留，实物不匹配时短绝缘飞线并机械固定。','PWR:CP2')
C(3,'100uF/16V','5V_BUS','GND','power',True,'靠近J6逻辑支路；DFPlayer模块附近仍需其本地100uF。','PWR:CP3')
for n,old in ((4,'PWR:CP4'),(5,'PWR:CP5'),(6,'PWR:CP6')):
    C(n,'100nF','5V_BUS','GND','power',notes=f'对应J{n}支路去耦；实物瓷片脚距按实测核对。',old=old)
R(1,'33k','VBAT_SW','BAT_ADC_DIV','adc','1%；与R2构成分压，8.4V约1.953V。',old='PWR:RP1')
R(2,'10k','BAT_ADC_DIV','GND','adc','1%；ADC分压下臂。',old='PWR:RP2')
C(7,'100nF','BAT_ADC_DIV','GND','adc',notes='靠近R1/R2与JP9；ADC慢信号滤波。',old='PWR:CP7')
R(3,'100','MCP_GPA5','LED_GATE','led','栅极串联，不可拿来作为LED限流。',old='PWR:RP3')
R(4,'100k','LED_GATE','GND','led','G-S默认下拉，复位关灯。',old='PWR:RP4')
R(5,'220','5V_BUS','LED_POS','led','仅适用本方案单颗小功率白LED，目标几mA至约10mA。',old='PWR:RP5')

part('U1','logic','SN74AHCT125N',{'1':'GND','2':'PA0','3':'SERVO_SIG_5V','4':'GND','5':'PB15','6':'US_TRIG_5V','7':'GND','8':'BUZZ_5V','9':'PB9','10':'GND','11':None,'12':'GND','13':'5V_BUS','14':'5V_BUS'},'ahct','DIP14+7.62mm芯片座；N为PDIP。第3通道永久使能，输入PB9有默认偏置，输出通过JP3选择；第4通道固定禁用，11脚不接。不得替换成74HC125。',pin_names={'1':'/OE1','2':'A1','3':'Y1','4':'/OE2','5':'A2','6':'Y2','7':'GND','8':'Y3','9':'A3','10':'/OE3','11':'Y4_NC','12':'A4','13':'/OE4','14':'VCC'},original_ref='IO:U1')
C(8,'100nF','5V_BUS','GND','ahct',notes='紧邻U1第14/7脚，尽量短回路。',old='IO:C1')
R(6,'10k','PA0','GND','ahct','上电PWM输入下拉。',old='IO:R1')
R(7,'10k','PB15','GND','ahct','上电TRIG输入下拉。',old='IO:R2')
R(8,'4.7k','I2C_SCL','3V3_EXT','i2c','条件上拉：只保留合适的等效上拉；模块已带上拉时核算并可DNP。',True,'IO:R3')
R(9,'4.7k','I2C_SDA','3V3_EXT','i2c','条件上拉：两总线空闲电压只能为3V3_EXT，不允许5V上拉。',True,'IO:R4')
R(10,'10k','MCP_RESET_N','3V3_EXT','i2c','模块已有复位上拉时可以DNP；不可连接核心NRST。',False,'IO:R5')
R(11,'10k','PA4','3V3_EXT','spi','RC522 CS默认高；同轨已有适宜上拉时可以DNP。',False,'IO:R6')
R(12,'10k','PA15','3V3_EXT','spi','FLASH CS默认高；同轨已有适宜上拉时可以DNP。',False,'IO:R7')
R(13,'10k','FLASH_WP_N','3V3_EXT','spi','仅FLASH有对应外露脚且模块没有同轨上拉时安装；4/6针模块可以不接该引脚。',True,'IO:R8')
R(14,'10k','FLASH_HOLD_N','3V3_EXT','spi','仅FLASH有对应外露脚且模块没有同轨上拉时安装；具体/WP、/HOLD或IO2/IO3按芯片资料。',True,'IO:R9')
R(15,'4.7k','ESTOP_NC1_RETURN','ES1_BASE','estop','原3管急停；6.0V时接点电流约1.13mA。',old='IO:R10')
R(16,'100k','ES1_BASE','GND','estop',old='IO:R11')
R(17,'4.7k','ESTOP_NC2_RETURN','ES2_BASE','estop','双NC彼此独立，一路门控，一路状态。',old='IO:R12')
R(18,'100k','ES2_BASE','GND','estop',old='IO:R13')
R(19,'4.7k','3V3_EXT','KILL_BASE','estop','EXT有效且NC1断开时使Q2导通；EXT掉电时不能声称仍有完整硬件急停保证。',old='IO:R14')
R(20,'100k','KILL_BASE','GND','estop',old='IO:R15')
R(21,'1k','PB5','STBY_OUT','estop','限制PB5高而Q2钳低时电流；不得再以导线跨过该电阻。',old='IO:R16')
R(22,'10k','PB5','GND','estop',old='IO:R17')
R(23,'10k','STBY_OUT','GND','estop',old='IO:R18')
R(24,'10k','PB13','3V3_CORE','estop','急停反馈上拉只用CORE；正常0，按下或NC2断线1。',old='IO:R19')
R(25,'12k','US_ECHO_RAW','PB1','ultrasonic','ECHO分压上臂，建议1%；不是12k到地。',old='IO:R20')
R(26,'20k','PB1','GND','ultrasonic','ECHO分压下臂，建议1%；5.0V输入约3.125V。',old='IO:R21')
R(27,'10k','PB3','3V3_CORE','encoder','与模块已有EXT上拉二选一；若保留EXT上拉，本电阻DNP，避免两稳压轨经两上拉相连。',True,'IO:R22')
R(28,'10k','PB4','3V3_CORE','encoder','与R27相同；不能只改其中一根编码相。',True,'IO:R23')
R(29,'4.7k','PB11','3V3_EXT','dht','DHT低压侧开漏上拉；模块/BSS138已有合适同轨上拉时DNP。',True,'IO:R24')
R(30,'1k','PB10','DF_RX','voice','仅USART3 TX，模块TX不接PB11。',old='IO:R25')
R(31,'10k','PB12','3V3_CORE','switches','碰撞两NC串联接地；任一个断开为高。',old='IO:R26')
R(32,'10k','PB14','3V3_CORE','switches','闭盖NO接地，闭盖=0；未闭合/断线=1。',old='IO:R27')
for n,base,collector,old in [(1,'ES1_BASE','KILL_BASE','IO:Q1'),(2,'KILL_BASE','STBY_OUT','IO:Q2'),(3,'ES2_BASE','PB13','IO:Q3')]:
    part('Q'+str(n),'npn','2N3904',{'1':'GND','2':base,'3':collector},'estop','按onsemi 2N3904 Rev3 TO-92资料定义1=E,2=B,3=C；已购其它品牌必须核数据手册/实测，不按外壳平面猜脚。',pin_names={'1':'E','2':'B','3':'C'},original_ref=old)
# Only these five optional resistor positions are added beyond the original 44 electrical parts.
R(33,'10k','MCP_GPB4','3V3_EXT','encoder','编码器SW外部上拉；模块已有同轨上拉或已验证MCP内部上拉时DNP。',True)
R(34,'10k','MCP_GPB5','3V3_EXT','switches','MODE低有效；推荐安装，已验证内部上拉时可DNP。',False)
R(35,'10k','MCP_GPB6','3V3_EXT','switches','BACK低有效；推荐安装，已验证内部上拉时可DNP。',False)
R(36,'10k','PB9','GND','buzzer','默认安装使AHCT输入确定；高有效蜂鸣保留。低有效模块先拆R36再装R37，不能两者均不装后运行。',False)
R(37,'10k','PB9','3V3_CORE','buzzer','低有效蜂鸣模块选择本上拉，R36必须DNP；绝不可上拉5V。',True)
for r in parts:
    if r['ref'] in ('R25','R26'):r['tolerance']='1%'
    elif r['ref'] in ('R20','R21'):r['tolerance']='5% or better'

# CUSTOM PCB pin order only. Every module-side connection is by signal label.
J(7,'EXT_REG',['5V_BUS','GND','3V3_EXT'],'power','外置3.3V稳压模块低电流接口；确认额定输出及GND；本口3脚是模块输出进入本板，不是核心3V3。',['外置稳压IN+','外置稳压GND/IN-/OUT-','外置稳压OUT+'])
pa=['PA'+str(i) for i in range(13)]+['PA15']
pb=['PB0','PB1']+['PB'+str(i) for i in range(3,16)]
J(8,'CORE_PA',['5V_BUS','GND','3V3_CORE']+pa,'core','自定义17针线束；按核心丝印逐线连接，不能整排直插；正常系统核心由本板1脚供5V，禁止同时插核心USB；若做独立USB台架，先断本板电源并拔下与核心相连的全部线束，再另行测试。',['核心5V输入','核心GND','核心3V3输出/参考']+['核心'+p for p in pa])
J(9,'CORE_PB',['GND']+pb,'core','自定义16针线束；PB2/BOOT1不接；PA13/PA14在核心直接接SWD并始终保留。',['核心GND']+['核心'+p for p in pb])
J(10,'MCP_BUS',['3V3_EXT','GND','I2C_SCL','I2C_SDA','MCP_RESET_N'],'i2c','成品MCP23017模块五线；A0/A1/A2在模块侧接地；INTA/INTB不用；RESET不接核心NRST。',['模块VDD','模块GND','模块SCL','模块SDA','模块RESET'])
J(11,'MCP_A',['MCP_GPA'+str(i) for i in range(7)],'mcp','逐线接模块GPA0至GPA6；GPA7不外接、软件设输出0。',['模块GPA'+str(i) for i in range(7)])
J(12,'MCP_B',['MCP_GPB'+str(i) for i in range(7)],'mcp','逐线接模块GPB0至GPB6；GPB7不外接、软件设输出0。',['模块GPB'+str(i) for i in range(7)])
J(13,'OLED',['3V3_EXT','GND','I2C_SCL','I2C_SDA'],'i2c','仅用于已确认3.3V供电I2C OLED；I2C拉3V3_EXT。',['OLED VCC','OLED GND','OLED SCL','OLED SDA'])
J(14,'MPU6050',['V_MPU','GND','I2C_SCL','I2C_SDA'],'i2c','JP5选择模块实际VIN电压；不能因芯片3.3V就默认板VIN也3.3V；任何模块内5V总线上拉必须处理。',['MPU模块VIN/VCC','模块GND','模块SCL','模块SDA'])
J(15,'RC522',['3V3_EXT','GND','PA4','PA5','PA7','PA6','MCP_GPA4'],'spi','RC522仅3.3V；商品排针SDA在SPI模式为CS，不接I2C；IRQ不接。',['RC522 3.3V','RC522 GND','RC522 SDA/SS/CS','RC522 SCK','RC522 MOSI','RC522 MISO','RC522 RST'])
J(16,'FLASH',['3V3_EXT','GND','PA15','PA5','PA7','PA6','FLASH_WP_N','FLASH_HOLD_N'],'spi','按实际3.3V SPI NOR芯片核对；不存在的WP/HOLD外露脚不接，不能套商品针序。',['FLASH VCC','FLASH GND','FLASH CS','FLASH CLK','FLASH DI/MOSI','FLASH DO/MISO','FLASH /WP（若外露）','FLASH /HOLD（若外露）'])
J(17,'HC05',['V_HC05','GND','PA2','PA3'],'uart','JP6供电选择按模块规格；UART输入输出均须3.3V逻辑。',['HC05 VCC/VIN','HC05 GND','HC05 RX','HC05 TX'])
J(18,'PC_UART',['GND','PA9','PA10'],'uart','3.3V逻辑USB转串口；本接口不提供电源，转换器VCC/5V/3V3脚不接。',['USB串口GND','USB串口RXD','USB串口TXD'])
J(19,'TB6612_CTRL',['3V3_EXT','GND','MCP_GPA0','MCP_GPA1','MCP_GPA2','MCP_GPA3','PA8','PA11','STBY_OUT'],'motor','本口仅逻辑；VM和动力地走J4；AO1/AO2/BO1/BO2在驱动模块直接接电机粗线。',['驱动VCC','驱动信号GND','AIN1','AIN2','BIN1','BIN2','PWMA','PWMB','STBY'])
J(20,'SERVO_SIG',['SERVO_SIG_5V','GND'],'ahct','1脚是PWM逻辑输出，不是舵机正电源；SG90主电源走J5，主地也直接回J5。',['SG90信号（确认颜色）','信号参考地/不得承担舵机主电流'])
J(21,'HC_SR04',['5V_BUS','GND','US_TRIG_5V','US_ECHO_RAW'],'ultrasonic','ECHO已经由板上12k/20k分压至PB1；不得从模块ECHO再另跨线到核心。',['HC-SR04 VCC','GND','TRIG','ECHO'])
J(22,'DHT',['V_DHT','GND','DHT_DATA_RAW'],'dht','3.3V分支JP7=1-2且JP8闭合；5V分支JP7=2-3、JP8断开，外置BSS138经J23转换；严禁5V分支短接JP8。',['DHT模块VCC','DHT GND','DHT DATA'])
J(23,'DHT_LEVEL',['3V3_EXT','5V_BUS','GND','PB11','DHT_DATA_RAW'],'dht','仅5V DHT分支使用外置BSS138双向开漏转换；3.3V分支保持空。转换模块GND全部共地。',['BSS138 LV','BSS138 HV','BSS138 GND','BSS138 LV通道','BSS138对应HV通道'])
J(24,'ENCODER',['3V3_EXT','GND','PB3','PB4','MCP_GPB4'],'encoder','仅3.3V编码器模块；CLK/DT的CORE上拉与模块EXT上拉二选一；SW上拉同样核对。',['编码器VCC','GND','CLK','DT','SW'])
J(25,'KEYS_LID',['MCP_GPB5','GND','MCP_GPB6','GND','PB14','GND'],'switches','三组接地开关：MODE、BACK轻触NO；闭盖用NO微动。轻触4脚同组导通须实测。',['MODE接点','MODE另一接点','BACK接点','BACK另一接点','闭盖NO','闭盖COM'])
J(26,'BUMPER',['PB12','GND'],'switches','外置左右微动NC串联，任一个碰撞或断线为高；不用NO端。',['右NC；右COM接左NC','左COM'])
J(27,'ESTOP_2NC',['VBAT_SW','ESTOP_NC1_RETURN','VBAT_SW','ESTOP_NC2_RETURN'],'estop','急停必须两组独立NC；开关闭合正常通，按下断。此口含最高8.4V，不能插传感器/MCU；禁止插跳帽伪装急停。',['NC1一端','NC1另一端','NC2一端','NC2另一端'])
J(28,'AO3400_ADAPTER',['LED_GATE','GND','LED_NEG'],'led','AO3400A是已购裸管，先焊到转接板并核对G/S/D，再外接本接口；不能照商品排针顺序。',['MOS G','MOS S','MOS D'])
J(29,'WHITE_LED',['LED_POS','LED_NEG'],'led','单颗小功率白LED正负端，板上220Ω串联限流；不能换成灯带。',['LED阳极+','LED阴极-'])
J(30,'BUZZER',['V_BUZZ','GND','BUZZ_IN'],'buzzer','仅带驱动三线蜂鸣模块；核供电和有效电平再选JP3/4与R36/37。',['模块VCC','模块GND','模块IN'])
J(31,'DFPLAYER_SIG',['GND','DF_RX','MCP_GPA6'],'voice','仅信号口。DFPlayer VCC和电源GND以独立适当线径从J6引；喇叭接模块SPK1/2而非GND；模块TX不接。BUSY必须为<=3.3V或先外置适配。',['DFPlayer信号GND','DFPlayer RX','经核对/适配的BUSY'])
J(32,'LIGHT',['3V3_EXT','GND','PB0'],'adc','默认3.3V光敏AO。若仅DO改软件模式；若5V模拟AO需外置分压校准，禁止用NPN代替模拟采样。热敏为台架替换，不能与光敏并接。',['光敏模块VCC（确认支持3.3V）','GND','光敏AO（或明确选用DO）'])
J(33,'IR_INPUTS',['3V3_EXT','5V_BUS','GND','MCP_GPB0','MCP_GPB1','MCP_GPB2','MCP_GPB3','PB8','PA12'],'digital_inputs','自定义供电/信号汇集口；六路输入必须经外置条件适配后<=3.3V。3V3与5V是两根可用电源，绝不能同时接模块同一VCC。',['3.3V外设电源','5V外设电源','模块公共地','循迹左有效3.3V输入','循迹中有效3.3V输入','循迹右有效3.3V输入','靠近DO有效3.3V输入','前障碍DO有效3.3V输入','投放对射DO有效3.3V输入'])

JP(3,'BUZZ_SIG_SELECT',['PB9','BUZZ_IN','BUZZ_5V'],'buzzer','open',['open','1-2','2-3'],'3.3V可驱动模块选1-2；仅确需5V控制时2-3；通道3始终使能；两输出不可并接。')
JP(4,'BUZZ_V_SELECT',['3V3_EXT','V_BUZZ','5V_BUS'],'buzzer','open',['open','1-2','2-3'],'按模块VCC选3.3V或5V，只能一帽；未确认前保持开路。')
JP(5,'MPU_V_SELECT',['3V3_EXT','V_MPU','5V_BUS'],'i2c','open',['open','1-2','2-3'],'核模块VIN/稳压压差后选择；无论VIN如何SCL/SDA均只拉EXT3.3V。')
JP(6,'HC05_V_SELECT',['3V3_EXT','V_HC05','5V_BUS'],'uart','open',['open','1-2','2-3'],'带稳压底板通常VIN5V，裸核心通常3.3V；必须核对实物。')
JP(7,'DHT_V_SELECT',['3V3_EXT','V_DHT','5V_BUS'],'dht','open',['open','1-2','2-3'],'3.3V模块1-2；5V模块2-3，同时JP8必须开路并装外置BSS138。')
JP(8,'DHT_DIRECT',['PB11','DHT_DATA_RAW'],'dht','open',['open','1-2'],'仅3.3V供电且已确认DATA安全时闭合；与5V DHT分支互斥。')
JP(9,'ADC_LINK',['BAT_ADC_DIV','PA1'],'adc','1-2',['open','1-2'],'正常装帽；电池仍接通而单独关闭/拔掉核心电源前拔帽，防ADC向掉电核心注入。')
JP(10,'MCP_RESET_TEST',['MCP_RESET_N','GND'],'i2c','open',['open','momentary 1-2'],'复位测试短接点，正常禁止长期留帽；不是核心NRST。')

MCU={}
functions={
'PA0':('舵机PWM','TIM2_CH1；AHCT通道1'), 'PA1':('电池电压','ADC1_IN1；JP9可隔离'),
'PA2':('蓝牙TX','USART2 TX→HC05 RX'),'PA3':('蓝牙RX','USART2 RX←HC05 TX'),
'PA4':('RC522片选','SPI1 CS，模块SDA即CS'),'PA5':('共享SCK','SPI1 SCK'),'PA6':('共享MISO','SPI1 MISO'),'PA7':('共享MOSI','SPI1 MOSI'),
'PA8':('左电机PWM','TIM1_CH1，20kHz'),'PA9':('调试串口TX','USART1 TX→转换器RXD'),'PA10':('调试串口RX','USART1 RX←转换器TXD'),
'PA11':('右电机PWM','TIM1_CH4，20kHz；禁USB'),'PA12':('投放光束输入','1ms轮询；不可用EXTI12；禁USB并核核心板USB上拉'),
'PA15':('FLASH片选','禁JTAG保留SWD后作GPIO'),
'PB0':('光敏AO/DO','ADC1_IN8或数字输入二选一'),'PB1':('超声ECHO','EXTI1双边沿，12k/20k分压后'),
'PB3':('编码器CLK','禁JTAG保留SWD；轮询/EXTI3'),'PB4':('编码器DT','禁JTAG保留SWD；轮询/EXTI4'),
'PB5':('电机使能请求','经R21和Q2门控；不能直连STBY'),
'PB6':('I2C SCL','I2C1默认映射、开漏'),'PB7':('I2C SDA','I2C1默认映射、开漏'),
'PB8':('前方避障','外置条件电平适配'),'PB9':('蜂鸣器','GPIO/TIM4_CH4，按模块不响电平偏置'),
'PB10':('语音TX','USART3 TX，经1k；禁USART3 RX'),'PB11':('DHT数据','开漏+EXT上拉；EXTI11可用'),
'PB12':('碰撞回路','EXTI12，两NC串联，正常低'),'PB13':('急停反馈','EXTI13，正常低，按下/断线高'),
'PB14':('闭盖反馈','NO微动，闭盖低'),'PB15':('超声TRIG','普通GPIO→AHCT通道2')}
for p,(function,usage) in functions.items():
    MCU[p]={'function':function,'usage':usage,'net':{'PB6':'I2C_SCL','PB7':'I2C_SDA'}.get(p,p)}
# CORE_PB pins PB6/PB7 must use bus net aliases, not disconnected PB6/PB7 nets.
for p in parts:
    if p['ref']=='J9':
        p['pins']={k:{'PB6':'I2C_SCL','PB7':'I2C_SDA'}.get(v,v) for k,v in p['pins'].items()}

features={
'A1':'RC522/STM32 UID识别','A2':'RC522+FLASH 注册/删除/挂失','A3':'RC522+对射+FLASH有效投放积分','A4':'FLASH持久化','A5':'RC522+OLED积分查询','A6':'RC522 RFID读写实验','A7':'管理员卡+菜单','A8':'FLASH日志/排名+串口导出','A9':'FLASH虚拟兑换',
'B1':'RC522+SG90刷卡开盖','B2':'对射投放检测','B3':'对射+状态机防重复积分','B4':'靠近红外+SG90便民开盖','B5':'HC-SR04满桶检测','B8':'菜单维护清理模式',
'C1':'TB6612+双减速电机差速','C2':'前红外避障','C3':'三路循迹','C4':'循迹站点识别','C6':'HC05蓝牙手动','C8':'MPU6050倾斜保护','C9':'双NC碰撞停车',
'D1':'OLED人机显示','D2':'蜂鸣器提醒','D3':'MODE/BACK按键','D4':'编码器旋转/按下','D5':'双NC急停','D6':'上电自检','D7':'ADC电量监测','D8':'USB串口日志/配置','E1':'DHT温湿度','E2':'光敏+LED自动照明','E4':'DFPlayer语音'}
configs=[
 {'id':'ahct_ch3_always_enabled','requires':{'U1.9':'PB9','U1.10':'GND','R36_or_R37':'exactly one populated'},'notes':'第3通道永久使能，即使不用蜂鸣也必须保留R36/R37其中一只使PB9有确定复位偏置；JP3可开路或1-2直驱3.3V兼容模块，或2-3使用5V输出。'},
 {'id':'buzzer_5v_control','requires':{'JP3':'2-3'},'notes':'JP4按模块额定电源；R36/R37二选一使复位不响。'},
 {'id':'buzzer_active_high','requires':{'R36':'populate','R37':'DNP'},'notes':'PB9低不响；5V缓冲与直驱均为同相。'},
 {'id':'buzzer_active_low','requires':{'R36':'DNP','R37':'populate'},'notes':'PB9高不响；只允许拉3V3_CORE。'},
 {'id':'dht_3v3','requires':{'JP7':'1-2','JP8':'1-2','J23':'unconnected'},'notes':'确认模块支持3.3V且总线开漏。R29按同轨上拉情况装配。'},
 {'id':'dht_5v','requires':{'JP7':'2-3','JP8':'open','J23':'external BSS138 fitted'},'notes':'双向开漏转换；5V不得直通PB11。'},
 {'id':'encoder_module_pullup','requires':{'R27':'DNP','R28':'DNP'},'notes':'保留实物模块已有到EXT的CLK/DT上拉。'},
 {'id':'encoder_board_pullup','requires':{'R27':'populate','R28':'populate'},'notes':'先移除模块CLK/DT原上拉，两路只拉CORE。'},
 {'id':'i2c_pullups','requires':{'R8':'conditional','R9':'conditional'},'notes':'全总线等效上拉只到3V3_EXT，起步100kHz；按现有模块上拉和总线波形核算，不默认每块并装。'},
 {'id':'digital_5v','requires':{'external_adapter':'per affected input'},'notes':'模块DO→10k→2N3904 B，B→100k→GND，E→GND，C→对应3.3V输入，C→10k→3V3_EXT；逻辑反相。用于6路IR或DF BUSY，不能用于DHT/SPI/I2C/模拟AO。'}]
sources=[
 {'title':'当前低成本 WIRING.md','path':str(REPO/'hardware/current-low-cost/WIRING.md')},
 {'title':'原两板结构化布局','path':str(REPO/'hardware/current-low-cost/perfboard/layout.json')},
 {'title':'330步骤手册源','path':str(REPO/'docs/manual/ASSEMBLY.md')},
 {'title':'TI SN74AHCT125 datasheet','url':'https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf'},
 {'title':'onsemi 2N3904 Rev3 / TO92 1E2B3C','url':'https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf'},
 {'title':'Microchip MCP23017 DS20001952D（GPA7/GPB7仅输出）','url':'https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf'}]

obj={'schema_version':'1.0','revision':'A1-electrical-2026-10-12','status':'electrical definition for schematic/PCB generation; not fabricated or powered','title':'SmartBin Low-cost THT Carrier A','board':{'target_size_mm':[100,100],'layers':2,'thickness_mm':1.6,'copper_oz':1,'assembly':'manual THT using purchased parts','module_mounting':'all active modules external, labeled individual wires, no assumed commercial header order'},'parts':parts,'connectors':connectors,'mcu_pin_map':MCU,'mcp_pin_map':{'GPA0':'TB6612 AIN1','GPA1':'TB6612 AIN2','GPA2':'TB6612 BIN1','GPA3':'TB6612 BIN2','GPA4':'RC522 RST','GPA5':'LED MOS gate via 100R','GPA6':'DFPlayer BUSY input','GPA7':'OUTPUT LOW, no external connection','GPB0':'LINE_L input','GPB1':'LINE_C input','GPB2':'LINE_R input','GPB3':'NEAR input','GPB4':'ENC_SW input','GPB5':'MODE input','GPB6':'BACK input','GPB7':'OUTPUT LOW, no external connection'},'features':features,'configurations':configs,'sources':sources,
 'power_budget':{'battery':'protected 2S18650 6.6–8.4V normal range; 6.0V abnormal immediate-stop threshold; >=5A pack capability','fuse':'external 5x20mm 3A initial value; final response curve and wire protection validated with real loads','buck':'external 5.00V, real >=3A continuous and >=4A transient under actual input/cooling conditions','motor_assumption':'each <=1A stall at5V; two <=2A; never intentional continuous stall','servo_allowance_A':2.0,'logic_total_5v_equivalent_allowance_A':0.5,'mutual_exclusion':'motor motion and servo travel interlocked, motors disabled before lid motion; voice limited to budget','worst_planned_active_A':2.5,'with_20_percent_margin_A':3.0,'external_3v3':'existing regulator >=200mA per original list; total actual peripheral current must fit with >=20% headroom; if not, replace with >=300mA qualified module or reduce load','large_current_off_board':['battery fuse/master switch/XT30','buck conversion loop and wiring','TB6612 bridge and motor outputs','SG90 internal drive','DFPlayer speaker outputs'], 'dupont_limit':'signal and verified low-current logic only; never battery/buck trunk, motor VM/output, servo power/return or speaker current'},
 'known_boundaries':[
 'Existing three-NPN stop gate depends on 3V3_EXT. It is not a certified or fully power-failure-safe emergency-stop circuit; EXT loss while MCU remains powered must not be treated as covered. Do not drive external pins high if EXT is absent. Main switch physically removes supply.',
 'Battery ADC remains connected to VBAT_SW while core could be off. Open JP9 before isolated MCU power-down with battery still live; normal single-supply startup retained. No claim of zero injection current during arbitrary power sequences.',
 '5V digital inputs require external validated adaptation; board does not make J33/DF BUSY 5V tolerant. Unknown modules are not plug-and-play.',
 'DHT5V requires external BSS138 and JP8 open; a 5V analog light signal needs appropriate analog divider, not an NPN.',
 '3V3_CORE and3V3_EXT must not be parallelled. Module pullups on encoder or buses must be checked; signal protection paths can still couple rails when one rail is unpowered.',
 'GPA7 and GPB7 are output-only on current MCP23017 datasheet; configure low outputs and leave unwired. POR/reset inputs on other pins are handled by STBY defaults and commissioning sequence.',
 'All 2N3904 footprints use1E2B3C per referenced onsemi part. Actual purchased transistor leadout must match; otherwise use insulated formed leads/verified adapter, do not reverse by visual guess.',
 'Capacitor and terminal physical dimensions are not guaranteed by nominal value. D12.5/P5 electrolytic courtyard reserved; measure purchased parts, use mechanically supported short insulated leads if needed.',
 'Core board must be removed from teaching base; PA11/12 are GPIO not USB, PA12 existing USB pullup must be assessed; core USB power and board5V must not be directly dual-fed.',
 'This definition is not ERC/DRC or manufacturing proof. Layout, board/schematic consistency, fabrication checks and hardware tests are separate.'],
 'layout_requirements':[
 'J3 is power star: J4/J5/J6 positive and return branches do not daisy-chain through signal headers or MCU ground leads. Use wide copper and solid low-impedance ground; do not make long high-current thermals.',
 'KeepVBAT/J1/J2/J27 visibly separate from3.3V signal headers. Label every connector pin and pin1 square. Put polarity on board top silk.',
 'PlaceC1/C4 nearJ4,C2/C5 nearJ5,C3/C6 nearJ6;C8 adjacentU1 pin14/7. PlaceADC divider/filter away from motor current routes.',
 'Give electrolytics D12.5mm bodies clearance; terminal screws accessible at edge, cable bend space outside outline. Check purchased terminal pin shape and actual body before release.',
 'All selectable jumpers single-cap only; clearly silk 3V3/5V or OFF/ON. Keep JP9 and reset test accessible. Reserve mounting holes and insulated underside.',
 'All external module signal wiring <=20cm initially;SPI andI2C share nearby GND. Choose100kHz I2C and conservative SPI clock for first test.']}

# Mechanical mounting positions; non-electrical parts intentionally have no pins.
for i,xy in enumerate(((5,5),(95,5),(5,95),(95,95)),1):
    part('H'+str(i),'mounting_hole','M3 NPTH',{},'MECHANICAL','3.2mm非金属化M3孔；孔中心坐标由100x100mm板左上基准定义。',
         symbol='Mechanical:MountingHole',footprint='MountingHole:MountingHole_3.2mm_M3',position_mm=list(xy))
obj['power_flags']=['GND','VBAT_SW','5V_BUS','3V3_EXT','3V3_CORE']
obj['mechanical_envelopes']={'electrolytics':{'max_body_diameter_mm':12.5,'nominal_lead_pitch_mm':5.0,'height':'check actual parts and enclosure; not constrained by value alone','fallback':'short insulated leads plus mechanical support, no unsupported hanging capacitor'},'terminals':{'pitch_mm':5.08,'positions':2,'target_max_body_mm':[11.5,10.5],'wire_entry':'board edge, >=10mm external working clearance; verify actual KF301 variant'},'resistors':{'lead_pitch_mm':10.16,'max_body_mm':[6.3,2.5]},'through_hole_pins':'manufacturing drill sizes determined by actual component leads plus assembly tolerance, not nominal pitch'}
# Structural checks; these do not replace transistor/data-sheet or hardware tests.
assert len(features)==33
assert len(MCU)==29
assert len({p['ref'] for p in parts})==len(parts)
assert all((p['pins'] or p['kind']=='mounting_hole') and all(isinstance(n,str) and n for n in p['pins']) for p in parts)
original=[p for p in parts if p.get('original_ref')]
assert len(original)==44,(len(original),[p['ref'] for p in original])
assert len([p for p in parts if p['kind']=='connector' and p['high_current']])==6
assert parts[[p['ref'] for p in parts].index('U1')]['pins']['11'] is None
assert not any(v in ('MCP_GPA7','MCP_GPB7') for p in parts for v in p['pins'].values())
assert not any(v in ('PB6','PB7') for p in parts for v in p['pins'].values())
obj['summary']={'electrical_positions':sum(p['kind'] not in ('connector','jumper','mounting_hole') for p in parts),'original_electrical_positions':44,'additional_optional_bias_positions':5,'connector_groups':33,'power_terminal_groups':6,'header_groups':27,'jumper_groups':8,'total_refs':len(parts),'kind_counts':dict(collections.Counter(p['kind'] for p in parts))}
obj['validation']={'unique_refs':'PASS','original_44_electrical_parts_preserved':'PASS','feature_count':33,'assigned_mcu_io_count':29,'no_mcp_bit7_external_net':'PASS','i2c_alias_connected':'PASS','footprint_library_existence':'pending root verification','physical_bought_part_fit':'not measured','manufacturing_checks':'not run in this electrical-definition task'}
(OUT/'circuit.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'connector-map.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['Ref','Name','PCB_pin','Net','External_signal_by_label','Connector_type','Notes'])
    byref={p['ref']:p for p in parts}
    for c in connectors:
        p=byref[c['ref']]
        for pin,net in p['pins'].items():w.writerow([p['ref'],p['value'],pin,net,c['targets'].get(pin,''),p['connector_type'],c['notes']])
    for p in parts:
        if p['kind']=='jumper':
            for pin,net in p['pins'].items():w.writerow([p['ref'],p['value'],pin,net,'跳帽选择端','custom2.54mm',p['notes']+' 默认:'+p['default_shunt']])
print(json.dumps(obj['summary'],ensure_ascii=False))
