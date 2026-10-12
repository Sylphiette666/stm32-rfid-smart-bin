"""Isolated kicad-tool extension for repeatable SmartBin PCB work.

All .kicad_pcb access is through KiCad's native object API in pcb_native.py.
JSON specifications are deliberately separate from editable KiCad source files.
"""
from pathlib import Path
import argparse, os, subprocess, sys
import kicad_tool

def main():
    parser=kicad_tool.build_parser()
    sub=next(a for a in parser._actions if isinstance(a,argparse._SubParsersAction))
    p=sub.add_parser('smartbin-pcb',help='native KiCad structured PCB backend')
    p.add_argument('action',choices=['project','build','import','finish','inspect','preview','drc','export','repair','obstacles','silk','rip','thermals','assemblyplot'])
    p.add_argument('root',type=Path)
    p.add_argument('--ses',type=Path)
    def execute(a):
        cmd=[os.environ.get('KICAD_PYTHON',r'D:\KiCad\bin\python.exe'),str(Path(__file__).with_name('pcb_native.py')),a.action,str(a.root.resolve())]
        if a.ses:cmd+=['--ses',str(a.ses.resolve())]
        return subprocess.call(cmd)
    p.set_defaults(func=execute)
    args=parser.parse_args()
    return args.func(args)

if __name__=='__main__':raise SystemExit(main())
