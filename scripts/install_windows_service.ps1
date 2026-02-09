<#
Inventory Sentinel Windows service installer helper
Supports two approaches:
  1) nssm (recommended) — installs the Python script as a service cleanly
  2) sc.exe fallback (simple) — may require additional config

Usage (PowerShell, run as Administrator):
  .\install_windows_service.ps1 [-ServiceName InventorySentinel] [-PythonPath 'C:\Path\to\python.exe']

This script only performs installation steps; use Start-Service/Stop-Service to control.
#>
param(
    [string]$ServiceName = "InventorySentinel",
    [string]$PythonPath = "",
    [string]$ScriptPath = "$(Resolve-Path "..\cli_agent.py")"
)

# Resolve default python in virtualenv if not provided
if (-not $PythonPath) {
    $venv = Join-Path (Get-Location).Path "..\.venv\Scripts\python.exe"
    if (Test-Path $venv) {
        $PythonPath = $venv
    } else {
        $PythonPath = "C:\\Python39\\python.exe"  # fallback, user should adjust
    }
}

Write-Host "Service: $ServiceName"
Write-Host "Python: $PythonPath"
Write-Host "Script: $ScriptPath"

# Try nssm if available
$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if ($nssm) {
    Write-Host "nssm found — installing service via nssm"
    & nssm install $ServiceName $PythonPath "$ScriptPath" "run" "--interval" "300"
    & nssm set $ServiceName Start SERVICE_AUTO_START
    Write-Host "Service installed. Use 'nssm start $ServiceName' to start."
    return
}

# Fallback: use sc.exe to create a service that runs Python with the script
$binPath = "`"$PythonPath`" `"$ScriptPath`" run --interval 300"
Write-Host "nssm not found; using sc.exe fallback (may require manual tuning)"
Write-Host "Creating service using: sc create $ServiceName binPath= $binPath"

# sc requires the binPath without an equals sign directly after param name
& sc.exe create $ServiceName binPath= "$binPath" start= auto

Write-Host "Service created. To start: Start-Service -Name $ServiceName"
Write-Host "To remove: sc.exe delete $ServiceName"

# If sc approach doesn't fit, recommend Scheduled Task
Write-Host "If a service is unsuitable, consider registering a Scheduled Task with 'schtasks' to run the CLI on a schedule."
