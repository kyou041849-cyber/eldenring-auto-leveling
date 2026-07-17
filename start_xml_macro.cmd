@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%macro"
".venv\Scripts\python.exe" "replay_ps4macro_xml.py" --xml "%USERPROFILE%\Downloads\eldenring.xml" %*
echo.
pause
