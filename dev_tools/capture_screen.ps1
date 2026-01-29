<#
.SYNOPSIS
    Capture screenshot of ATLAS Command Centre window.

.DESCRIPTION
    Uses .NET System.Drawing to capture the primary monitor.
    Screenshots saved to Pictures/Screenshots with timestamp.

    SECURITY NOTES:
    - Only captures screen, no file access beyond output directory
    - Timestamp filename prevents overwrites and path manipulation
    - No elevation required
    - No user input interpolated into paths

.PARAMETER OutputDir
    Optional output directory. Defaults to Pictures/Screenshots.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File capture_screen.ps1

.EXAMPLE
    # From WSL2:
    # powershell.exe -ExecutionPolicy Bypass -File 'C:\path\capture_screen.ps1'

.NOTES
    Author: ATLAS Project
    Version: 1.0
#>

param(
    [string]$OutputDir = "$env:USERPROFILE\Pictures\Screenshots"
)

# Load required assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Generate output path with timestamp (prevents overwrites)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputFile = Join-Path $OutputDir "atlas_$timestamp.png"

# Ensure directory exists
if (-not (Test-Path $OutputDir)) {
    try {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    } catch {
        Write-Error "Failed to create output directory: $_"
        exit 1
    }
}

# Capture screen
$screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = $null
$graphic = $null

try {
    $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
    $graphic = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphic.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
    $bitmap.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)

    # Output the path for callers to capture
    Write-Output $outputFile

} catch {
    Write-Error "Screenshot capture failed: $_"
    exit 1

} finally {
    # Clean up resources
    if ($graphic) {
        $graphic.Dispose()
    }
    if ($bitmap) {
        $bitmap.Dispose()
    }
}
