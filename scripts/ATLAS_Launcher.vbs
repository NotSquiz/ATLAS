' ATLAS Voice Bridge - Silent Launcher
' Double-click this file to launch ATLAS without a console window
'
' To create a desktop shortcut:
'   1. Right-click this file
'   2. Select "Create shortcut"
'   3. Move the shortcut to your Desktop
'   4. Rename it to "ATLAS"

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw ""\\wsl$\Ubuntu\home\squiz\ATLAS\scripts\atlas_launcher.py""", 0, False
