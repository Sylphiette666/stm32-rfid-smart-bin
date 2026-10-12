import argparse,subprocess,sys
from pathlib import Path
import kicad_tool
p=kicad_tool.build_parser()
sub=next(a for a in p._actions if isinstance(a,argparse._SubParsersAction))
sp=sub.add_parser('four-skill-audit'); sp.add_argument('root',type=Path)
sp.set_defaults(func=lambda a:subprocess.call([r'D:\KiCad\bin\python.exe',str(Path(__file__).with_name('audit_native.py')),str(a.root.resolve())]))
a=p.parse_args();sys.exit(a.func(a))
