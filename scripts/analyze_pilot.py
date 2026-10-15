"""Offline deterministic reanalysis; frozen semantic/generation evidence is preserved."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from physstyle.pilot import analyze_pilot
if __name__=="__main__":
    print(json.dumps(analyze_pilot(),ensure_ascii=False,indent=2))
