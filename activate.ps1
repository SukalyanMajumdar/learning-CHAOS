
$VenvDir = Join-Path $PSScriptRoot ".venv"
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"

if (-not (Test-Path $ActivateScript)) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Create it using: py -3.14 -m venv .venv"
    return
}

. $ActivateScript

Write-Host "`n[CHAOS] Virtual environment activated!" -ForegroundColor Green
python --version
