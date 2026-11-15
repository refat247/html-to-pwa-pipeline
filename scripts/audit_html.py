#!/usr/bin/env python3
"""Produce a source inventory, not a blanket PWA readiness certificate."""
import argparse
import json
import sys
from pathlib import Path
from pwa_core import inspect_input


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--report',type=Path)
    args=p.parse_args(argv)
    try: report=inspect_input(args.source)
    except (OSError,UnicodeError,ValueError) as exc:
        print('AUDIT FAILED: '+str(exc),file=sys.stderr);return 2
    doc=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(doc,'utf-8')
    else: print(doc,end='')
    return 0 if report['static_conversion_eligible'] else 1

if __name__=='__main__':sys.exit(main())
