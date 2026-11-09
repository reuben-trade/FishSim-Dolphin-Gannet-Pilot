"""Rebuild current report figures from the complete portable evidence bundle."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in [HERE,*HERE.parents] if (p/'notebook_support_v6.py').is_file())
sys.path.insert(0,str(ROOT))
from notebook_support_v6 import reproduce_figures
if __name__=='__main__':reproduce_figures(HERE/'figures')
