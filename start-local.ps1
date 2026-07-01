# TalentForge — local dev without Docker (Windows PowerShell)
# Usage: .\start-local.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

function Test-PortInUse([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

$ApiPort = 8000
if (Test-PortInUse $ApiPort) {
    Write-Host "Port 8000 is already in use (old API?). Trying 8001..." -ForegroundColor Yellow
    $ApiPort = 8001
    if (Test-PortInUse $ApiPort) {
        Write-Host "Port 8001 is also in use. Stop other servers or run: Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess" -ForegroundColor Red
        exit 1
    }
}

Write-Host "TalentForge local startup (no Docker)" -ForegroundColor Cyan
Write-Host "API port: $ApiPort" -ForegroundColor Cyan

Set-Location $Backend
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
pip install -q -r requirements.txt

Write-Host "Initializing database..."
python scripts/init_db.py
python scripts/seed.py

Write-Host "Starting API on http://localhost:$ApiPort ..."
$backendJob = Start-Job -ScriptBlock {
    param($BackendPath, $Port)
    Set-Location $BackendPath
    & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
} -ArgumentList $Backend, $ApiPort

Start-Sleep -Seconds 4

Set-Location $Frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

$env:VITE_API_URL = "http://localhost:$ApiPort"
Write-Host "Starting frontend on http://localhost:5173 ..."
Write-Host ""
Write-Host "Open: http://localhost:5173" -ForegroundColor Green
Write-Host "Login:" -ForegroundColor Green
Write-Host "  Admin:     admin@genvenx.com / admin123"
Write-Host "  Recruiter: hira@genvenx.com / recruiter123"
Write-Host ""
Write-Host "Press Ctrl+C to stop. To stop backend: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Yellow

try {
    npm run dev
} finally {
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
}
