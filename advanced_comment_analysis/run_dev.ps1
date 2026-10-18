# Dev runner: start the FastAPI app in local-first mode
# Usage: powershell -ExecutionPolicy Bypass -File .\run_dev.ps1

$proj = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $proj

Write-Output "Project root: $proj"

# Ensure data dir exists for SQLite
$dataDir = Join-Path $proj 'data'
if (-Not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-Output "Created data directory: $dataDir"
} else {
    Write-Output "Data directory exists: $dataDir"
}

# Kill any process listening on 8000
$ports = @(8000)
foreach ($p in $ports) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
n        if ($conn) {
            $pid = $conn.OwningProcess
            if ($pid) {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Output "Stopped process $pid on port $p"
            }
        }
    } catch {
        # ignore
    }
}

# Path to venv python
$venvPython = Join-Path $proj '.venv\Scripts\python.exe'
if (-Not (Test-Path $venvPython)) {
    Write-Output "Warning: virtualenv python not found at $venvPython. Make sure you have a .venv or run: python -m venv .venv; ./.venv/Scripts/Activate.ps1; pip install -r requirements.txt"
}

# Run uvicorn (no --reload)
$cmd = "`"$venvPython`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir `"$proj`""
Write-Output "Starting: $cmd"
Start-Process -NoNewWindow -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--app-dir", "$proj"
Write-Output "uvicorn started (background). Use Ctrl+C in the terminal where you run the script directly to stop if you started it interactively." 
