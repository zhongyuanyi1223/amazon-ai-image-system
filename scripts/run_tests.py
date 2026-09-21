import sys
import unittest
from pathlib import Path

def main():
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1]/'tests'),pattern='test_*.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__': sys.exit(main())
