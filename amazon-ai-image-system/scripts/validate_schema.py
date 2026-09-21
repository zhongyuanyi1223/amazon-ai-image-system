import argparse
import sys
from core import read, schema_validate, Blocked

def main():
    p=argparse.ArgumentParser(); p.add_argument('schema',choices=['product','image-job','image-plan','qc-result']); p.add_argument('file'); a=p.parse_args()
    try: schema_validate(read(a.file),a.schema); print('PASS'); return 0
    except (Blocked,OSError,ValueError) as e: print(str(e),file=sys.stderr); return 1
if __name__=='__main__': sys.exit(main())
