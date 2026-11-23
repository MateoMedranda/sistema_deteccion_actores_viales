param(
    [ValidateSet("api", "gateway")]
    [string]$Service = "api",
    [int]$Port = 0,
    [switch]$CheckEnvironment
)
$ErrorActionPreference = "Stop"
$backendRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $backendRoot
$candidates = @(
    (Join-Path $backendRoot ".venv/Scripts/python.exe"),
    (Join-Path $projectRoot ".venv/Scripts/python.exe")
)
$python = $null
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    $probeInfo = New-Object System.Diagnostics.ProcessStartInfo
    $probeInfo.FileName = $candidate
    $probeCode = "import sys, importlib.util; print('compatible' if sys.version_info[:2] in ((3,12),(3,13)) and all(importlib.util.find_spec(m) for m in ('fastapi','uvicorn','pydantic_settings','httpx')) else 'incompatible')"
    $probeInfo.Arguments = '-c "' + $probeCode + '"'
    $probeInfo.UseShellExecute = $false
    $probeInfo.CreateNoWindow = $true
    $probeInfo.RedirectStandardOutput = $true
    $probeInfo.RedirectStandardError = $true
    $probeProcess = New-Object System.Diagnostics.Process
    $probeProcess.StartInfo = $probeInfo
    $probeOk = $false
    try {
        [void]$probeProcess.Start()
        $probeResult = $probeProcess.StandardOutput.ReadToEnd().Trim()
        [void]$probeProcess.StandardError.ReadToEnd()
        $probeProcess.WaitForExit()
        $probeOk = $probeProcess.ExitCode -eq 0 -and $probeResult -eq 'compatible'
    } catch {
        $probeOk = $false
    } finally {
        $probeProcess.Dispose()
    }
    if ($probeOk) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    throw "No hay un entorno compatible con las dependencias instaladas. En backend ejecuta: uv sync --python 3.12 --extra dev"
}
if ($CheckEnvironment) { Write-Output $python; return }
if ($Port -eq 0) { $Port = if ($Service -eq "api") { 8000 } else { 4174 } }
$application = if ($Service -eq "api") { "app.main:app" } else { "app.web.main:app" }
Push-Location -LiteralPath $backendRoot
try {
    & $python -m uvicorn $application --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "El servicio terminó con código $LASTEXITCODE" }
} finally {
    Pop-Location
}
