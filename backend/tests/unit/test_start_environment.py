import os,shutil,subprocess
from pathlib import Path
import pytest
pytestmark=pytest.mark.skipif(os.name!="nt",reason="Windows PowerShell environment selector")
def test_selector_uses_compatible_environment_without_starting_service():
    script=Path(__file__).resolve().parents[2]/"start.ps1"
    result=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),"-CheckEnvironment"],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert "python.exe" in result.stdout and "Traceback" not in result.stderr

def test_selector_reports_missing_environments_without_native_traceback(tmp_path):
    script=Path(__file__).resolve().parents[2]/"start.ps1"
    target=tmp_path/"backend"/"start.ps1";target.parent.mkdir();shutil.copyfile(script,target)
    result=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(target),"-CheckEnvironment"],capture_output=True,text=True,timeout=15)
    assert result.returncode!=0
    assert "NativeCommandError" not in result.stderr and "Traceback" not in result.stderr
