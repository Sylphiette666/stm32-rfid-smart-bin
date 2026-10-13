"""Refresh uVision source groups; --template is only needed on initial creation."""
from pathlib import Path
import argparse
import copy
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--template',type=Path,default=ROOT/'MDK/SmartBin_A1.uvprojx')
a=p.parse_args()
tree=ET.parse(a.template)
root=tree.getroot()
targets=root.find('Targets')
target=copy.deepcopy(targets.find('Target'))
targets.clear();targets.append(target)
def setval(path,value):
    e=target.find(path)
    if e is not None:e.text=value
setval('TargetName','SmartBin_A1')
setval('TargetOption/TargetCommonOption/OutputDirectory','..\\build\\keil\\')
setval('TargetOption/TargetCommonOption/OutputName','SmartBin_A1')
setval('TargetOption/TargetCommonOption/ListingPath','..\\build\\keil\\')
setval('TargetOption/TargetCommonOption/TargetStatus/InvalidFlash','0')
for prefix in ('BeforeCompile','BeforeMake','AfterMake'):
    for i in (1,2):setval(f'TargetOption/TargetCommonOption/{prefix}/RunUserProg{i}','0')
setval('TargetOption/TargetArmAds/Cads/VariousControls/Define','STM32F10X_MD,__MICROLIB')
setval('TargetOption/TargetArmAds/Cads/VariousControls/IncludePath',
       '..\\include;..\\vendor\\CMSIS5_Core;..\\..\\legacy\\SmartBin_F103\\CMSIS\\Device')
setval('TargetOption/TargetArmAds/Cads/VariousControls/MiscControls','-std=c11 -Wall -Wextra -Werror')
setval('TargetOption/TargetArmAds/LDads/ScatterFile','.\\flash.sct')
setval('TargetOption/TargetArmAds/LDads/umfTarg','0')
setval('TargetOption/TargetArmAds/LDads/Misc','--strict')
setval('TargetOption/TargetArmAds/Aads/VariousControls/Define','__MICROLIB')
setval('TargetOption/TargetArmAds/Aads/VariousControls/IncludePath','')
groups=target.find('Groups');groups.clear()
for name,paths,typ in [('Application',sorted((ROOT/'src').glob('*.c')),1),
                       ('Startup',[ROOT/'src/startup.s'],2),
                       ('Headers',sorted((ROOT/'include').glob('*.h')),5)]:
    group=ET.SubElement(groups,'Group');ET.SubElement(group,'GroupName').text=name
    files=ET.SubElement(group,'Files')
    for path in paths:
        f=ET.SubElement(files,'File');ET.SubElement(f,'FileName').text=path.name
        ET.SubElement(f,'FileType').text=str(typ)
        ET.SubElement(f,'FilePath').text='..\\'+str(path.relative_to(ROOT)).replace('/','\\')
ET.indent(tree,space='  ')
tree.write(ROOT/'MDK/SmartBin_A1.uvprojx',encoding='utf-8',xml_declaration=True)
