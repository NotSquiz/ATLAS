@echo off
REM ATLAS Voice Bridge - Desktop Launcher
REM Double-click this file to launch ATLAS
REM
REM To create a desktop shortcut:
REM   1. Right-click this file
REM   2. Select "Create shortcut"
REM   3. Move the shortcut to your Desktop
REM   4. Optionally rename it to "ATLAS"

cd /d "%~dp0"
python "\\wsl$\Ubuntu\home\squiz\ATLAS\scripts\atlas_launcher.py"
pause
