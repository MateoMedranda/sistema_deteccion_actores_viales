from pathlib import Path
import runpy
module=runpy.run_path(str(Path(__file__).resolve().parents[1]/'tests/performance/test_count_lines_overhead.py'))
module['compare']()
