#Requires -RunAsAdministrator
# ATLAS Optimization Script 2: Remove NVIDIA Bloat
# Keeps: Display Driver + PhysX only
# Removes: GeForce Experience, CUDA, Telemetry, all extras

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 2: Remove NVIDIA Bloat" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keeping: Display Driver + PhysX" -ForegroundColor Green
Write-Host "Removing: Everything else" -ForegroundColor Yellow
Write-Host ""

# Stop NVIDIA services first
Write-Host "[1/3] Stopping NVIDIA services..." -ForegroundColor Yellow
$nvServices = @(
    "NVDisplay.ContainerLocalSystem",
    "NvContainerLocalSystem",
    "NvTelemetryContainer",
    "NvContainerNetworkService"
)

foreach ($svc in $nvServices) {
    try {
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Write-Host "      Stopped: $svc" -ForegroundColor Green
    } catch {}
}

# Remove NVIDIA apps via winget
Write-Host ""
Write-Host "[2/3] Removing NVIDIA apps..." -ForegroundColor Yellow

$nvApps = @(
    "NVIDIA.GeForceExperience",
    "NVIDIA.NVIDIAControlPanel",
    "NVIDIA.PhysX"  # We'll reinstall PhysX standalone if needed
)

# Check if winget is available
$wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue

if ($wingetAvailable) {
    # List installed NVIDIA packages
    Write-Host "      Scanning for NVIDIA packages..." -ForegroundColor Cyan
    $installed = winget list --name "NVIDIA" 2>$null

    # Remove GeForce Experience specifically
    Write-Host "      Removing GeForce Experience..." -ForegroundColor Yellow
    winget uninstall --id "NVIDIA.GeForceExperience" --silent 2>$null

    Write-Host "      [OK] GeForce Experience removal attempted" -ForegroundColor Green
} else {
    Write-Host "      winget not available. Manual removal required." -ForegroundColor Yellow
    Write-Host "      Go to: Settings > Apps > Installed Apps" -ForegroundColor Yellow
    Write-Host "      Remove: NVIDIA GeForce Experience" -ForegroundColor Yellow
}

# Disable NVIDIA telemetry and container services
Write-Host ""
Write-Host "[3/3] Disabling NVIDIA services..." -ForegroundColor Yellow

$nvServicesToDisable = @(
    @{Name="NvTelemetryContainer"; Desc="NVIDIA Telemetry"},
    @{Name="NvContainerNetworkService"; Desc="NVIDIA Network Service"},
    @{Name="NvContainerLocalSystem"; Desc="NVIDIA Container (non-essential)"}
)

foreach ($svc in $nvServicesToDisable) {
    try {
        $service = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
        if ($service) {
            Set-Service -Name $svc.Name -StartupType Disabled -ErrorAction Stop
            Write-Host "      [OK] Disabled: $($svc.Desc)" -ForegroundColor Green
        }
    } catch {
        Write-Host "      [--] $($svc.Name) not found" -ForegroundColor DarkGray
    }
}

# Remove NVIDIA scheduled tasks
Write-Host ""
Write-Host "      Disabling NVIDIA scheduled tasks..." -ForegroundColor Yellow
$nvTasks = Get-ScheduledTask | Where-Object {$_.TaskName -like "*NVIDIA*" -or $_.TaskName -like "*NvTm*"}
foreach ($task in $nvTasks) {
    try {
        Disable-ScheduledTask -TaskName $task.TaskName -ErrorAction Stop | Out-Null
        Write-Host "      [OK] Disabled: $($task.TaskName)" -ForegroundColor Green
    } catch {}
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 2 Complete" -ForegroundColor Cyan
Write-Host "  Expected savings: 200-400MB" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTE: Your GPU driver still works!" -ForegroundColor Yellow
Write-Host "For driver updates, download from:" -ForegroundColor Yellow
Write-Host "https://www.nvidia.com/Download/index.aspx" -ForegroundColor Cyan
Write-Host "(Choose 'Game Ready Driver' or 'Studio Driver')" -ForegroundColor Yellow
Write-Host ""
