import argparse
import sys
from pathlib import Path
from core import read, validate_job, validate_generation, Blocked

def main():
    p=argparse.ArgumentParser(); p.add_argument('job',type=Path); p.add_argument('--generation',action='store_true'); a=p.parse_args()
    try:
        job=read(a.job)
        print((validate_generation if a.generation else validate_job)(job,a.job.resolve().parent)); return 0
    except (Blocked,OSError,ValueError,KeyError,TypeError) as e:
        print(f'BLOCKED: {getattr(e,"code","INPUT")}: {e}',file=sys.stderr); return 1
if __name__=='__main__': sys.exit(main())
