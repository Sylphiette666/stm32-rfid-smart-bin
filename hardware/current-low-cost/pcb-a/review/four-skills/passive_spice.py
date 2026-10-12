"""Actual ngspice shared-library DC operating points for the two fitted dividers.
No MCU clamp, cable, transistor or module model is claimed by this test.
"""
import ctypes as c,os,json,math
from pathlib import Path
R=Path(__file__).resolve().parent
cookie=os.add_dll_directory(r'D:\KiCad\bin')
lib=c.CDLL(r'D:\KiCad\bin\ngspice.dll')
logs=[]
CB=c.CFUNCTYPE(c.c_int,c.c_char_p,c.c_int,c.c_void_p)
@CB
def send(s,i,p):logs.append(s.decode('utf-8','replace'));return 0
EXIT=c.CFUNCTYPE(c.c_int,c.c_int,c.c_bool,c.c_bool,c.c_int,c.c_void_p)
@EXIT
def controlled_exit(status,immediate,quitexit,i,p):logs.append(f'controlled_exit {status} {immediate} {quitexit}');return 0
BG=c.CFUNCTYPE(c.c_int,c.c_bool,c.c_int,c.c_void_p)
@BG
def background(running,i,p):return 0
lib.ngSpice_Init.argtypes=[c.c_void_p]*7;lib.ngSpice_Init.restype=c.c_int
assert lib.ngSpice_Init(send,send,controlled_exit,None,None,background,None)==0
lib.ngSpice_Command.argtypes=[c.c_char_p];lib.ngSpice_Command.restype=c.c_int
lib.ngSpice_Circ.argtypes=[c.POINTER(c.c_char_p)];lib.ngSpice_Circ.restype=c.c_int
class Vec(c.Structure):
 _fields_=[('name',c.c_char_p),('type',c.c_int),('flags',c.c_short),('real',c.POINTER(c.c_double)),('complex',c.c_void_p),('length',c.c_int)]
lib.ngGet_Vec_Info.argtypes=[c.c_char_p];lib.ngGet_Vec_Info.restype=c.POINTER(Vec)
cases=[]
for name,upper,lower,maxvin,limit in [('BAT_ADC R1/R2',33000.,10000.,8.4,3.3),('ECHO R25/R26',12000.,20000.,5.15,3.3)]:
 for tag,rt,rb,vin in [('nominal',upper,lower,8.4 if 'BAT' in name else 5.),('high_output_1pct',upper*.99,lower*1.01,maxvin),('low_output_1pct',upper*1.01,lower*.99,maxvin)]:
  lines=['Divider DC review',f'V1 src 0 {vin}',f'Rupper src out {rt}',f'Rlower out 0 {rb}','.op','.end']
  arr=(c.c_char_p*(len(lines)+1))(*[s.encode() for s in lines],None)
  assert lib.ngSpice_Circ(arr)==0;assert lib.ngSpice_Command(b'run')==0
  v=lib.ngGet_Vec_Info(b'v(out)');assert v and v.contents.length>0
  result=float(v.contents.real[0]);expected=vin*rb/(rt+rb)
  assert abs(result-expected)<1e-8
  cases.append({'circuit':name,'case':tag,'vin_V':vin,'upper_ohm':rt,'lower_ohm':rb,'spice_V':result,'formula_V':expected,'limit_V':limit,'pass':result<limit,'upper_dissipation_mW':(vin-result)**2/rt*1000})
  lib.ngSpice_Command(b'destroy all')
out={'engine':'ngspice shared library bundled with KiCad 10','automatic_skill_runner':'No standalone executable detected; this adapter uses the installed engine through its C API.','scope':'Unloaded DC divider only, 1% resistor corners. Does not validate power-off injection, MCU VIH margin at low VDD, cable ringing, ADC acquisition time, motors or emergency logic.','cases':cases,'battery_RC_tau_ms':(33000*10000/(33000+10000))*.0000001*1000,'pass':all(ca['pass'] for ca in cases)}
(R/'analysis/passive-spice.json').write_text(json.dumps(out,indent=2));(R/'analysis/passive-spice.log').write_text('\n'.join(logs));print(json.dumps(out))
