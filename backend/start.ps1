param(
    [ValidateSet("api", "gateway")]
    [string]$Service = "api",
    [int]$Port = 0
)
$ErrorActionPreference = "Stop"
$backendRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent $backendRoot
$candidates = @(
    (Join-Path $backendRoot ".venv/Scripts/python.exe"),
    (Join-Path $projectRoot ".venv/Scripts/python.exe")
)
$python = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
    throw "No hay entorno Python. En backend ejecuta: uv sync --extra dev"
}
if ($Port -eq 0) { $Port = if ($Service -eq "api") { 8000 } else { 4174 } }
$application = if ($Service -eq "api") { "app.main:app" } else { "app.web.main:app" }
Push-Location -LiteralPath $backendRoot
try {
    & $python -m uvicorn $application --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "El servicio terminó con código $LASTEXITCODE" }
} finally {
    Pop-Location
}
