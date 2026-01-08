#Requires -RunAsAdministrator
# ATLAS Optimization Script 3: Remove Bloat Apps
# Removes: OneDrive, Teams, Calibre, PC Health Check, Phone Link

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 3: Remove Bloat Apps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill running processes first
Write-Host "[1/3] Stopping bloat processes..." -ForegroundColor Yellow
$processes = @("OneDrive", "Teams", "PhoneExperienceHost", "calibre", "PCHealthCheck")
foreach ($proc in $processes) {
    Stop-Process -Name $proc -Force -ErrorAction SilentlyContinue
}
Write-Host "      Processes stopped." -ForegroundColor Green

# Remove OneDrive
Write-Host ""
Write-Host "[2/3] Removing apps..." -ForegroundColor Yellow

# OneDrive removal
Write-Host "      Removing OneDrive..." -ForegroundColor Yellow
try {
    # Stop OneDrive
    taskkill /f /im OneDrive.exe 2>$null

    # Uninstall OneDrive (64-bit and 32-bit paths)
    if (Test-Path "$env:SystemRoot\System32\OneDriveSetup.exe") {
        & "$env:SystemRoot\System32\OneDriveSetup.exe" /uninstall
    }
    if (Test-Path "$env:SystemRoot\SysWOW64\OneDriveSetup.exe") {
        & "$env:SystemRoot\SysWOW64\OneDriveSetup.exe" /uninstall
    }

    # Remove leftover folders
    Remove-Item "$env:USERPROFILE\OneDrive" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:LOCALAPPDATA\Microsoft\OneDrive" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:PROGRAMDATA\Microsoft OneDrive" -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "      [OK] OneDrive removed" -ForegroundColor Green
} catch {
    Write-Host "      [!!] OneDrive removal partial" -ForegroundColor Yellow
}

# Remove Microsoft Teams (new and classic)
Write-Host "      Removing Microsoft Teams..." -ForegroundColor Yellow
try {
    # New Teams
    Get-AppxPackage -Name "MSTeams" -AllUsers | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue
    Get-AppxPackage -Name "MicrosoftTeams" -AllUsers | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue

    # Classic Teams
    $teamsPath = [System.IO.Path]::Combine($env:LOCALAPPDATA, 'Microsoft', 'Teams')
    if (Test-Path $teamsPath) {
        Remove-Item $teamsPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Prevent Teams from reinstalling
    $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Communications"
    if (!(Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
    Set-ItemProperty -Path $regPath -Name "ConfigureChatAutoInstall" -Value 0 -Type DWord

    Write-Host "      [OK] Teams removed" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Teams removal partial" -ForegroundColor Yellow
}

# Remove Phone Link
Write-Host "      Removing Phone Link..." -ForegroundColor Yellow
try {
    Get-AppxPackage -Name "Microsoft.YourPhone" -AllUsers | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue
    Get-AppxPackage -Name "Microsoft.WindowsPhone" -AllUsers | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue
    Write-Host "      [OK] Phone Link removed" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Phone Link removal failed" -ForegroundColor Yellow
}

# Remove PC Health Check
Write-Host "      Removing PC Health Check..." -ForegroundColor Yellow
try {
    winget uninstall --id "Microsoft.PCHealthCheck" --silent 2>$null
    Write-Host "      [OK] PC Health Check removed" -ForegroundColor Green
} catch {
    Write-Host "      [--] PC Health Check not found" -ForegroundColor DarkGray
}

# Remove Calibre
Write-Host "      Removing Calibre..." -ForegroundColor Yellow
try {
    winget uninstall --name "calibre" --silent 2>$null
    Write-Host "      [OK] Calibre removed" -ForegroundColor Green
} catch {
    Write-Host "      [--] Calibre not found" -ForegroundColor DarkGray
}

# Remove other common bloat
Write-Host ""
Write-Host "[3/3] Removing Windows bloat apps..." -ForegroundColor Yellow

$bloatApps = @(
    "Microsoft.BingNews",
    "Microsoft.BingWeather",
    "Microsoft.GetHelp",
    "Microsoft.Getstarted",
    "Microsoft.MicrosoftSolitaireCollection",
    "Microsoft.People",
    "Microsoft.PowerAutomateDesktop",
    "Microsoft.Todos",
    "Microsoft.WindowsFeedbackHub",
    "Microsoft.WindowsMaps",
    "Microsoft.ZuneMusic",
    "Microsoft.ZuneVideo",
    "Clipchamp.Clipchamp",
    "Microsoft.MicrosoftOfficeHub",
    "Microsoft.Office.OneNote",
    "Microsoft.SkypeApp",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxGameOverlay",
    "Microsoft.XboxGamingOverlay",
    "Microsoft.XboxIdentityProvider",
    "Microsoft.XboxSpeechToTextOverlay"
)

foreach ($app in $bloatApps) {
    try {
        $pkg = Get-AppxPackage -Name $app -AllUsers -ErrorAction SilentlyContinue
        if ($pkg) {
            Remove-AppxPackage -Package $pkg.PackageFullName -AllUsers -ErrorAction Stop
            Write-Host "      [OK] Removed: $app" -ForegroundColor Green
        }
    } catch {
        # Silently skip if not installed
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 3 Complete" -ForegroundColor Cyan
Write-Host "  Expected savings: 300-600MB" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
