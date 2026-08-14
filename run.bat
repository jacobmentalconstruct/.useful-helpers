@echo off
REM FILE:    run.bat
REM ROLE:    Supported Windows operator entrance for the Useful Helpers Suite.
REM USAGE:   run.bat help ^| docs ^| list ^| refresh ^| smoke ^| ui ^| map ^| cli ^<args...^> ^| mcp ^| tool ^<id^> ^<args-json^>
REM STATUS:  DONE - convenience wrapper over python -m src.app and smoke_test.py.
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

if "%~1"=="" goto :help
if /I "%~1"=="help" goto :help
if /I "%~1"=="menu" goto :help
if /I "%~1"=="docs" (
    echo Open this local page in a browser:
    echo %CD%\_docs\HUMAN_ONBOARDING.html
    exit /b 0
)
if /I "%~1"=="list" (
    "%PYTHON_EXE%" -m src.app cli tool-list
    goto :eof
)
if /i "%~1"=="attach" (
    REM The first question anyone asks: what is this target, and what next.
    "%PYTHON_EXE%" -m src.app cli tool-call --tool attach --args-json "{}"
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="refresh" (
    "%PYTHON_EXE%" -m src.app cli registry-refresh
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="smoke" (
    "%PYTHON_EXE%" smoke_test.py
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="mcp" (
    "%PYTHON_EXE%" -m src.app mcp
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="ui" (
    "%PYTHON_EXE%" -m src.app ui
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="plan" (
    "%PYTHON_EXE%" -m src.app plan
    goto :eof
)
if /I "%~1"=="map" (
    "%PYTHON_EXE%" -m src.app map
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="install" (
    "%PYTHON_EXE%" -m src.app install
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="tool" (
    if "%~2"=="" (
        echo Usage: run.bat tool ^<tool_id^> ^<args-json^>
        exit /b 2
    )
    if "%~3"=="" (
        "%PYTHON_EXE%" -m src.app cli tool-call --tool "%~2" --args-json "{}"
    ) else (
        "%PYTHON_EXE%" -m src.app cli tool-call --tool "%~2" --args-json "%~3"
    )
    exit /b %ERRORLEVEL%
)
if /I "%~1"=="cli" (
    "%PYTHON_EXE%" -m src.app %*
    exit /b %ERRORLEVEL%
)

"%PYTHON_EXE%" -m src.app %*
exit /b %ERRORLEVEL%

:help
echo Useful Helpers Suite
echo.
echo Supported entrances:
echo   run.bat docs                        Show the local HTML onboarding page path
echo   run.bat list                         List registered tools
echo   run.bat tool ^<id^> ^<args-json^>       Invoke one tool through the control-plane seam
echo   run.bat cli ^<args...^>                Run any CLI subcommand
echo   run.bat mcp                          Start the MCP server on stdio
echo   run.bat ui                           Launch the registry GUI control panel
echo   run.bat plan                         Launch the project-planner cockpit (start a new project)
echo   run.bat map                          Launch the Project Snapshot window (shareable map/dump)
echo   run.bat install                      Install the toolkit into a project (.useful-helpers sidecar)
echo   run.bat smoke                        Run the smoke suite
echo   run.bat refresh                      Regenerate config\registry.json
echo.
echo Notes:
echo   setup_env.bat is optional but recommended; run.bat falls back to system Python.
echo   The GUI, CLI, and MCP all read the same registry and dispatch through one governed seam.
pause
exit /b 0
