# ATLAS WSL2 Optimization Script
# Run as Administrator in PowerShell on Windows
#
# This script disables Windows services that cause memory leaks in WSL2:
# - DoSvc (Delivery Optimization) - Known memory leak culprit
# - Ndu (Network Data Usage Monitor) - Accumulates memory over time
# - SysMain (Superfetch) - Unnecessary in WSL context
# - WSearch (Windows Search) - Reduces background disk/memory activity
#
# After running, restart WSL with: wsl --shutdown

#Requires -RunAsAdministrator

Write-Host "ATLAS WSL2 Optimization Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Disabling DoSvc (Delivery Optimization)..." -ForegroundColor Yellow
try {
    Stop-Service -Force -Name "DoSvc" -ErrorAction SilentlyContinue
    Set-Service -Name "DoSvc" -StartupType Disabled
    Write-Host "  DoSvc disabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not disable DoSvc - $_" -ForegroundColor Yellow
}

Write-Host "Disabling Ndu (Network Data Usage Monitor)..." -ForegroundColor Yellow
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4
    Write-Host "  Ndu disabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not disable Ndu - $_" -ForegroundColor Yellow
}

Write-Host "Disabling SysMain (Superfetch)..." -ForegroundColor Yellow
try {
    Stop-Service -Force -Name "SysMain" -ErrorAction SilentlyContinue
    Set-Service -Name "SysMain" -StartupType Disabled
    Write-Host "  SysMain disabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not disable SysMain - $_" -ForegroundColor Yellow
}

Write-Host "Disabling WSearch (Windows Search)..." -ForegroundColor Yellow
try {
    Stop-Service -Force -Name "WSearch" -ErrorAction SilentlyContinue
    Set-Service -Name "WSearch" -StartupType Disabled
    Write-Host "  WSearch disabled successfully" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not disable WSearch - $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Optimization complete!" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Create/update C:\Users\$env:USERNAME\.wslconfig with:" -ForegroundColor White
Write-Host ""
Write-Host @"
[wsl2]
memory=6GB
swap=8GB
processors=6
networkingMode=mirrored
dnsTunneling=true
firewall=true

[experimental]
autoMemoryReclaim=dropcache
sparseVhd=true
hostAddressLoopback=true
"@ -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Restart WSL by running: wsl --shutdown" -ForegroundColor White
Write-Host "3. Open a new WSL terminal and verify with: free -h" -ForegroundColor White
Write-Host ""
Write-Host "Expected result: ~1.5-2GB used, 6GB total, 8GB swap" -ForegroundColor Green
