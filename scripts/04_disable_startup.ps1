#Requires -RunAsAdministrator
# ATLAS Optimization Script 4: Disable Startup Items
# Prevents apps from auto-starting with Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 4: Disable Startup Items" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Registry paths for startup items
$startupPaths = @(
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
)

# Items to disable (partial name match)
$itemsToDisable = @(
    "Discord",
    "Teams",
    "OneDrive",
    "Spotify",
    "Steam",
    "Epic",
    "Zoom",
    "Slack",
    "Adobe",
    "CCleaner",
    "iTunes",
    "Dropbox",
    "Google",
    "NVIDIA",
    "Cortana",
    "Skype"
)

Write-Host "[1/2] Scanning startup registry..." -ForegroundColor Yellow

foreach ($path in $startupPaths) {
    if (Test-Path $path) {
        $items = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
        if ($items) {
            $props = $items.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" }
            foreach ($prop in $props) {
                foreach ($disable in $itemsToDisable) {
                    if ($prop.Name -like "*$disable*" -or $prop.Value -like "*$disable*") {
                        try {
                            Remove-ItemProperty -Path $path -Name $prop.Name -ErrorAction Stop
                            Write-Host "      [OK] Disabled: $($prop.Name)" -ForegroundColor Green
                        } catch {
                            Write-Host "      [!!] Could not disable: $($prop.Name)" -ForegroundColor Yellow
                        }
                    }
                }
            }
        }
    }
}

# Disable startup apps via Task Manager method (Startup folder)
Write-Host ""
Write-Host "[2/2] Checking Startup folder..." -ForegroundColor Yellow

$startupFolder = [Environment]::GetFolderPath("Startup")
$commonStartup = [Environment]::GetFolderPath("CommonStartup")

foreach ($folder in @($startupFolder, $commonStartup)) {
    if (Test-Path $folder) {
        $shortcuts = Get-ChildItem -Path $folder -Filter "*.lnk" -ErrorAction SilentlyContinue
        foreach ($shortcut in $shortcuts) {
            foreach ($disable in $itemsToDisable) {
                if ($shortcut.Name -like "*$disable*") {
                    try {
                        Remove-Item $shortcut.FullName -Force
                        Write-Host "      [OK] Removed startup shortcut: $($shortcut.Name)" -ForegroundColor Green
                    } catch {}
                }
            }
        }
    }
}

# Disable Edge auto-start
Write-Host ""
Write-Host "      Disabling Edge auto-start..." -ForegroundColor Yellow
try {
    $edgePath = "HKLM:\SOFTWARE\Policies\Microsoft\Edge"
    if (!(Test-Path $edgePath)) { New-Item -Path $edgePath -Force | Out-Null }
    Set-ItemProperty -Path $edgePath -Name "StartupBoostEnabled" -Value 0 -Type DWord
    Set-ItemProperty -Path $edgePath -Name "BackgroundModeEnabled" -Value 0 -Type DWord
    Write-Host "      [OK] Edge startup boost disabled" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not configure Edge" -ForegroundColor Yellow
}

# Disable Cortana
Write-Host "      Disabling Cortana..." -ForegroundColor Yellow
try {
    $cortanaPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search"
    if (!(Test-Path $cortanaPath)) { New-Item -Path $cortanaPath -Force | Out-Null }
    Set-ItemProperty -Path $cortanaPath -Name "AllowCortana" -Value 0 -Type DWord
    Write-Host "      [OK] Cortana disabled" -ForegroundColor Green
} catch {
    Write-Host "      [!!] Could not disable Cortana" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script 4 Complete" -ForegroundColor Cyan
Write-Host "  Startup items disabled" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "TIP: Open Task Manager > Startup tab to verify" -ForegroundColor Yellow
Write-Host ""
