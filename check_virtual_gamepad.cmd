@echo off
setlocal
set "ROOT=%~dp0"
start "" control joy.cpl
cd /d "%ROOT%macro"
".venv\Scripts\python.exe" "test_virtual_gamepad.py"
echo.
pause
