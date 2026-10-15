"""Offline expanded-corpus reanalysis with frozen earlier cohorts preserved."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.structure_corpus import analyze
if __name__=="__main__":analyze()
