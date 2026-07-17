@echo off
setlocal
set "CHIAKI_DIR=%LOCALAPPDATA%\eldenring_auto_leveling\chiaki-ng\chiaki-ng-Win"
set "CHIAKI_EXE=%CHIAKI_DIR%\chiaki.exe"

if not exist "%CHIAKI_EXE%" (
  echo chiaki-ng was not found:
  echo %CHIAKI_EXE%
  echo.
  echo Re-copy chiaki-ng to an ASCII-only path, then try again.
  pause
  exit /b 1
)

start "" /D "%CHIAKI_DIR%" "%CHIAKI_EXE%"
timeout /t 3 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "$expected = [Environment]::GetEnvironmentVariable('CHIAKI_EXE'); $ok = Get-Process chiaki -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $expected }; if (-not $ok) { exit 1 }"
if errorlevel 1 (
  echo chiaki-ng started but exited immediately.
  echo.
  echo Expected path:
  echo %CHIAKI_EXE%
  echo.
  pause
  exit /b 1
)
