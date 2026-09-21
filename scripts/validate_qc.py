import argparse
import sys
from pathlib import Path
from core import read, validate_qc, Blocked

def main():
    p=argparse.ArgumentParser(); p.add_argument('report',type=Path); p.add_argument('--job',type=Path,required=True); a=p.parse_args()
    try:
        print(validate_qc(read(a.report),read(a.job),a.job.resolve().parent)); return 0
    except (Blocked,OSError,ValueError,KeyError,TypeError) as e:
        print(f'BLOCKED: {getattr(e,"code","INPUT")}: {e}',file=sys.stderr); return 1
if __name__=='__main__': sys.exit(main())
