@echo off
setlocal
set "open_browser=-OpenBrowser"
if /i "%~1"=="--no-pause" set "open_browser="
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0scripts\start-trial.ps1" %open_browser%
set "trial_status=%ERRORLEVEL%"
if /i not "%~1"=="--no-pause" pause
exit /b %trial_status%
