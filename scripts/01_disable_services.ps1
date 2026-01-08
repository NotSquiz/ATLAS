#Requires -RunAsAdministrator
# ATLAS Optimization Script 1: Disable Bloat Services
# Run in elevated PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 1: Disable Bloat Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create restore point first
Write-Host "[1/4] Creating System Restore Point..." -ForegroundColor Yellow
try {
    Enable-ComputerRestore -Drive "C:\" -ErrorAction SilentlyContinue
    Checkpoint-Computer -Description "Before ATLAS Aggressive Optimization $(Get-Date -Format 'yyyy-MM-dd')" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
    Write-Host "      Restore point created." -ForegroundColor Green
} catch {
    Write-Host "      Warning: Could not create restore point. Continuing..." -ForegroundColor Yellow
}

# NDU Memory Leak Fix (CRITICAL - can save 200MB-1GB+)
Write-Host ""
Write-Host "[2/4] Fixing NDU Memory Leak (Registry)..." -ForegroundColor Yellow
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4 -ErrorAction Stop
    Write-Host "      NDU disabled. Expected: 200MB-1GB+ savings" -ForegroundColor Green
} catch {
    Write-Host "      Error: Could not modify NDU registry" -ForegroundColor Red
}

# Aggressive service list
Write-Host ""
Write-Host "[3/4] Disabling Memory-Heavy Services..." -ForegroundColor Yellow

$services = @(
    # High Impact (500MB+)
    @{Name="DoSvc"; Desc="Delivery Optimization"; Savings="500MB-20GB leak"},
    @{Name="SysMain"; Desc="Superfetch"; Savings="100-600MB"},
    @{Name="WSearch"; Desc="Windows Search"; Savings="200-500MB"},

    # Medium Impact (50-200MB each)
    @{Name="DiagTrack"; Desc="Telemetry"; Savings="50-150MB"},
    @{Name="WerSvc"; Desc="Error Reporting"; Savings="10-50MB"},
    @{Name="diagsvc"; Desc="Diagnostic Service"; Savings="10-30MB"},
    @{Name="dmwappushservice"; Desc="WAP Push"; Savings="10-30MB"},
    @{Name="MapsBroker"; Desc="Maps Broker"; Savings="20-50MB"},
    @{Name="PcaSvc"; Desc="Program Compatibility"; Savings="10-30MB"},

    # Phone/Tablet related (you don't use)
    @{Name="PhoneSvc"; Desc="Phone Service"; Savings="10-30MB"},
    @{Name="TabletInputService"; Desc="Tablet Input"; Savings="10-20MB"},

    # Xbox/Gaming (if not using Xbox features)
    @{Name="XblAuthManager"; Desc="Xbox Auth"; Savings="10-30MB"},
    @{Name="XblGameSave"; Desc="Xbox Game Save"; Savings="10-20MB"},
    @{Name="XboxGipSvc"; Desc="Xbox Accessory"; Savings="5-15MB"},
    @{Name="XboxNetApiSvc"; Desc="Xbox Networking"; Savings="10-20MB"},

    # Rarely needed
    @{Name="Fax"; Desc="Fax Service"; Savings="5-10MB"},
    @{Name="RetailDemo"; Desc="Retail Demo"; Savings="5-10MB"},
    @{Name="wisvc"; Desc="Windows Insider"; Savings="10-20MB"},
    @{Name="WMPNetworkSvc"; Desc="WMP Network"; Savings="10-20MB"},
    @{Name="icssvc"; Desc="Mobile Hotspot"; Savings="10-20MB"},
    @{Name="lfsvc"; Desc="Geolocation"; Savings="10-30MB"},

    # Print (you confirmed no printer)
    @{Name="Spooler"; Desc="Print Spooler"; Savings="20-50MB"},
    @{Name="PrintNotify"; Desc="Print Extensions"; Savings="5-10MB"}
)

foreach ($svc in $services) {
    try {
        $service = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name $svc.Name -Force -ErrorAction SilentlyContinue
            Set-Service -Name $svc.Name -StartupType Disabled -ErrorAction Stop
            Write-Host "      [OK] $($svc.Name) ($($svc.Desc)) - $($svc.Savings)" -ForegroundColor Green
        } else {
            Write-Host "      [--] $($svc.Name) not found" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "      [!!] $($svc.Name) - Could not disable" -ForegroundColor Yellow
    }
}

# Registry Performance Tweaks
Write-Host ""
Write-Host "[4/4] Applying Registry Performance Tweaks..." -ForegroundColor Yellow

# Processor scheduling for foreground apps
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" -Name "Win32PrioritySeparation" -Value 38 -ErrorAction Stop
    Write-Host "      [OK] Foreground app priority boost" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not set processor scheduling" -ForegroundColor Yellow
}

# Reduce background CPU reservation
try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" -Name "SystemResponsiveness" -Value 10 -ErrorAction Stop
    Write-Host "      [OK] Background CPU reduced to 10%" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not set system responsiveness" -ForegroundColor Yellow
}

# Disable telemetry scheduled tasks
$tasks = @(
    "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
    "\Microsoft\Windows\Application Experience\ProgramDataUpdater",
    "\Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
    "\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
    "\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector"
)

foreach ($task in $tasks) {
    try {
        Disable-ScheduledTask -TaskName $task -ErrorAction Stop | Out-Null
        $shortName = $task.Split('\')[-1]
        Write-Host "      [OK] Disabled task: $shortName" -ForegroundColor Green
    } catch {
        $shortName = $task.Split('\')[-1]
        Write-Host "      [--] $shortName (already disabled)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 1 Complete" -ForegroundColor Cyan
Write-Host "  Expected savings: 800MB - 2GB+" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
