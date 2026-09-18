@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_wewrite.ps1" -Restart
set EXITCODE=%ERRORLEVEL%
echo.
if "%EXITCODE%"=="0" (
  echo WeWrite has stopped.
) else (
  echo WeWrite failed to start. Error code: %EXITCODE%
)
echo This window stays open so you can read any message above.
pause
exit /b %EXITCODE%
