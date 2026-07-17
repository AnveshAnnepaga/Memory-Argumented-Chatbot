# Boot the backend server and stream logs to console.
$ErrorActionPreference = "Continue"

# Activate venv
$VenvPy = "D:\Memory-Argumented-Chatbot\Memory-Argumented-Chatbot\.venv\Scripts\python.exe"
$RepoRoot = "D:\Memory-Argumented-Chatbot\Memory-Argumented-Chatbot"

Write-Host "=== Backend Boot ===" -ForegroundColor Cyan
Write-Host "Python: $VenvPy"
Write-Host "Repo:   $RepoRoot"

# Kill any old uvicorn that might be holding port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
}

Set-Location $RepoRoot

# Run uvicorn detached, redirect to log
$LogPath = Join-Path $RepoRoot "backend_boot.log"
if (Test-Path $LogPath) { Remove-Item $LogPath -Force }

$Args = @(
    "-m", "uvicorn",
    "main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--log-level", "info"
)

Write-Host "Spawning uvicorn: $VenvPy $($Args -join ' ')"

# Start in a detached process so the shell can keep working
$Proc = Start-Process `
    -FilePath $VenvPy `
    -ArgumentList $Args `
    -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput $LogPath `
    -RedirectStandardError  (Join-Path $RepoRoot "backend_boot.err.log") `
    -PassThru `
    -WindowStyle Hidden

Write-Host ("Started PID {0}" -f $Proc.Id) -ForegroundColor Green

# Wait briefly and surface first lines of the log for diagnosis
Start-Sleep -Seconds 6
if (Test-Path $LogPath) {
    Write-Host "---- backend_boot.log (head) ----" -ForegroundColor Yellow
    Get-Content -Path $LogPath -Tail 40
} else {
    Write-Host "Log file not yet created." -ForegroundColor Red
}
