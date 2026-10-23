"""Diagnostic only: preserve both native CLI placement orders, never call a
successful transport exit a successful construction. Does not build a binary.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bridge',type=Path,required=True)
    parser.add_argument('--sha',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    executable=args.bridge.resolve()
    base=['reset',
          'line boundary 7 outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000 fixity F F F F F F',
          'line placement 7 on boundary 7 origin 0 0 0 u +x v +y',
          'line timber 1 27 20 role boundary','line timber 2 27 20 role boundary']
    place={1:'line place 1 on 7 at-face e0 +u +n',2:'line place 2 on 7 at-face e2 +u +n'}
    rows=[]
    for order in ((1,2),(2,1)):
        commands=base+[place[i] for i in order]+['dump','objects']
        stdin='\n'.join(commands)+'\n'
        run=subprocess.run([str(executable)],input=stdin,capture_output=True,text=True,timeout=30)
        replies=[];protocol_error=None
        try:
            replies=[json.loads(line) for line in run.stdout.splitlines()]
        except ValueError as error:
            protocol_error=str(error)
        complete=protocol_error is None and len(replies)==len(commands)
        results=[replies[len(base)+i] if complete else None for i in range(2)]
        row={'order':order,'argv':run.args,'stdin':stdin,'exit_code':run.returncode,
             'stdout':run.stdout,'stderr':run.stderr,'protocol_complete':complete,'protocol_error':protocol_error,
             'place_responses':results,'both_place_accepted':complete and all(reply.get('ok') is True for reply in results)}
        rows.append(row)
    receipt={'scope':'CLI reachability observation, not an acceptance or mutation verdict. A bridge exit0 only proves orderly protocol transport.',
             'requested_source_sha':args.sha,'executable':str(executable),
             'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
             'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'environment':{'platform':platform.platform(),'python':sys.version,
                            'LANG':os.environ.get('LANG'),'LC_ALL':os.environ.get('LC_ALL')},'rows':rows}
    args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:value for key,value in receipt.items() if key!='rows'},ensure_ascii=False))
    for row in rows:
        print(json.dumps({key:row[key] for key in ('order','exit_code','protocol_complete','both_place_accepted','place_responses')},ensure_ascii=False))
    if any(row['exit_code']!=0 or not row['protocol_complete'] for row in rows):
        return 2
    # Construction rejection remains explicit in both_place_accepted/answers;
    # this diagnostic has no boolean product-pass assertion to weaken.
    return 0


if __name__=='__main__':
    sys.exit(main())
