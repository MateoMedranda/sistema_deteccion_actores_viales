"""Generate only synthetic browser fixtures; no private environment or model loading."""
from fractions import Fraction
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"backend"))
from tests.fixtures_progressive import video
def main():
 folder=(ROOT/".runtime"/"e2e-009").resolve()
 if not folder.is_relative_to((ROOT/".runtime").resolve()):raise RuntimeError("fixture_directory_invalid")
 folder.mkdir(parents=True,exist_ok=True)
 for name,count in (("source",1200),("short",60)):
  video(folder/(name+".mp4"),[Fraction(i,30) for i in range(count)],640,360,lossless=False)
if __name__=="__main__":main()
