
$VenvDir = Join-Path $PSScriptRoot ".venv"
$DeActivateScript = Join-Path $VenvDir "Scripts\deactivate.bat"

if (-not (Test-Path $DeActivateScript)) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Create it using: py -3.14 -m venv .venv"
    return
}

deactivate

Write-Host "`n[CHAOS] Virtual environment DeActivated!" -ForegroundColor Green