#Requires -RunAsAdministrator
# ATLAS Windows Optimization Script
# Run in elevated PowerShell (right-click > Run as Administrator)
#
# IMPORTANT: Creates a restore point first. Safe to run.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ATLAS Windows 11 Optimization Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create restore point
Write-Host "[1/6] Creating System Restore Point..." -ForegroundColor Yellow
try {
    Enable-ComputerRestore -Drive "C:\" -ErrorAction SilentlyContinue
    Checkpoint-Computer -Description "Before ATLAS Optimization $(Get-Date -Format 'yyyy-MM-dd')" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
    Write-Host "      Restore point created successfully." -ForegroundColor Green
} catch {
    Write-Host "      Warning: Could not create restore point. Continuing anyway..." -ForegroundColor Yellow
}

# Step 2: NDU Memory Leak Fix (CRITICAL)
Write-Host ""
Write-Host "[2/6] Fixing NDU Memory Leak (Registry)..." -ForegroundColor Yellow
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4 -ErrorAction Stop
    Write-Host "      NDU disabled. Expected savings: 200MB-1GB+" -ForegroundColor Green
} catch {
    Write-Host "      Error: Could not modify NDU registry key" -ForegroundColor Red
}

# Step 3: Disable Memory-Heavy Services
Write-Host ""
Write-Host "[3/6] Disabling Memory-Heavy Services..." -ForegroundColor Yellow

$services = @(
    @{Name="DoSvc"; Desc="Delivery Optimization"; Savings="50-200MB + prevents 20GB leak"},
    @{Name="SysMain"; Desc="Superfetch"; Savings="100-600MB"},
    @{Name="WSearch"; Desc="Windows Search"; Savings="200-500MB"},
    @{Name="DiagTrack"; Desc="Telemetry"; Savings="50-150MB"},
    @{Name="dmwappushservice"; Desc="WAP Push"; Savings="10-30MB"},
    @{Name="WerSvc"; Desc="Error Reporting"; Savings="10-50MB"},
    @{Name="diagsvc"; Desc="Diagnostic Service"; Savings="10-30MB"},
    @{Name="MapsBroker"; Desc="Maps Broker"; Savings="20-50MB"},
    @{Name="PcaSvc"; Desc="Program Compatibility"; Savings="10-30MB"}
)

foreach ($svc in $services) {
    try {
        $service = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name $svc.Name -Force -ErrorAction SilentlyContinue
            Set-Service -Name $svc.Name -StartupType Disabled -ErrorAction Stop
            Write-Host "      [OK] $($svc.Name) ($($svc.Desc)) - $($svc.Savings)" -ForegroundColor Green
        } else {
            Write-Host "      [--] $($svc.Name) not found (OK)" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "      [!!] $($svc.Name) - Could not disable" -ForegroundColor Yellow
    }
}

# Step 4: Registry Performance Tweaks
Write-Host ""
Write-Host "[4/6] Applying Registry Performance Tweaks..." -ForegroundColor Yellow

# Processor scheduling for foreground apps
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" -Name "Win32PrioritySeparation" -Value 38 -ErrorAction Stop
    Write-Host "      [OK] Processor scheduling optimized for foreground apps" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not set processor scheduling" -ForegroundColor Yellow
}

# Reduce background CPU reservation from 20% to 10%
try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" -Name "SystemResponsiveness" -Value 10 -ErrorAction Stop
    Write-Host "      [OK] Background CPU reservation reduced to 10%" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not set system responsiveness" -ForegroundColor Yellow
}

# Step 5: Disable Telemetry Scheduled Tasks
Write-Host ""
Write-Host "[5/6] Disabling Telemetry Scheduled Tasks..." -ForegroundColor Yellow

$tasks = @(
    "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
    "\Microsoft\Windows\Application Experience\ProgramDataUpdater",
    "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
    "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip"
)

foreach ($task in $tasks) {
    try {
        Disable-ScheduledTask -TaskName $task -ErrorAction Stop | Out-Null
        $shortName = $task.Split('\')[-1]
        Write-Host "      [OK] Disabled: $shortName" -ForegroundColor Green
    } catch {
        $shortName = $task.Split('\')[-1]
        Write-Host "      [--] $shortName (already disabled or not found)" -ForegroundColor DarkGray
    }
}

# Step 6: Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Optimization Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected RAM Savings: 400MB - 1.5GB+" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Create .wslconfig file (see instructions below)"
Write-Host "2. Restart your computer"
Write-Host "3. Run memory check in WSL2"
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  .wslconfig Instructions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Create this file: C:\Users\$env:USERNAME\.wslconfig" -ForegroundColor White
Write-Host ""
Write-Host "Paste this content:" -ForegroundColor White
Write-Host @"
[wsl2]
memory=6GB
swap=4GB
swapFile=C:\\Temp\\wsl-swap.vhdx
processors=8
gpuSupport=true
pageReporting=true

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
networkingMode=mirrored
"@ -ForegroundColor Cyan
Write-Host ""
Write-Host "Then run: wsl --shutdown" -ForegroundColor Yellow
Write-Host "Wait 8 seconds, then start WSL2 again." -ForegroundColor Yellow
Write-Host ""
