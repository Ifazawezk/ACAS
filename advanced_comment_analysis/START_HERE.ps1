$proj = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $proj

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ACAS STARTUP SEQUENCE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Virtual Environment Check
$venvDir = Join-Path $proj '.venv'
if (-Not (Test-Path $venvDir)) {
    Write-Host "[1/5] Creating venv..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "[1/5] Virtualenv exists." -ForegroundColor Green
}

# 2. Dependencies
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
if (Test-Path "requirements.txt") {
    Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
    & "$venvPython" -m pip install -r requirements.txt
}

# 3. Data Directory
if (-Not (Test-Path "data")) { 
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
    Write-Host "[3/5] Created data directory." -ForegroundColor Green
}

# 4. Safe Port Cleanup (Simplified Structure)
Write-Host "[4/5] Checking Port 8000..." -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1

if ($conn -and $conn.OwningProcess -gt 0) {
    Write-Host "  Found process $($conn.OwningProcess) on port 8000. Stopping..." -ForegroundColor Gray
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
} 

# 5. Launch Backend
Write-Host "[5/5] Starting Backend..." -ForegroundColor Cyan
$procArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000")

# We use Start-Process to keep uvicorn running even if this script finishes
Start-Process -NoNewWindow -FilePath $venvPython -ArgumentList $procArgs

Write-Host ""
Write-Host "ACAS IS LIVE: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop this window."
Write-Host ""

# Keep the window open
while($true) { Start-Sleep -Seconds 1 }