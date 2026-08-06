@echo off
REM FILE:    run.bat
REM ROLE:    Windows launcher for the Useful Helpers sidecar installer.
REM DOES:    Finds Python 3, then runs install.py (folder-picker GUI + HITL confirm),
REM          which installs the sidecar into the project folder you choose.
REM USAGE:   double-click, or: run.bat  (headless: run.bat --target C:\proj --mode reinstall)
setlocal
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py" )
if not defined PY (
    echo Python 3 is required but was not found on PATH.
    echo Install Python 3 from https://www.python.org/downloads/ and try again.
    pause
    exit /b 1
)

"%PY%" install.py %*
set "RC=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RC%
