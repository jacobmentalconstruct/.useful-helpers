@echo off
REM FILE:    run.bat
REM ROLE:    Supported Windows operator entrance for the Useful Helpers Suite.
REM USAGE:   run.bat help ^| attach ^| docs ^| list ^| refresh ^| smoke ^| ui ^| map ^| plan ^| cli ^<args...^> ^| mcp ^| tool ^<id^> ^<args-json^>
REM NOTES:   Convenience wrapper over python -m src.app and smoke_test.py. Resolves its
REM          own directory, so the working directory you start from does not matter -
REM          but it is not on PATH, so invoke it BY PATH: .useful-helpers\run.bat attach
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
    REM This pointed at %CD%\_docs\HUMAN_ONBOARDING.html, which no commit in this
    REM repository has ever contained. It named a file, not a directory that moved.
    echo Documentation for this instance, under %CD%
    echo.
    echo   AGENTS.md                    front door for any agent - read first
    echo   README.md                    what this is, and the quick start
    echo   docs\ARCHITECTURE.md         how it works
    echo   docs\TOOLS.md                the capability catalog - generated
    echo   docs\OPERATIONS.md           how to drive the tools
    echo   docs\ONBOARDING.md           read order
    echo   docs\PROJECT_GOVERNANCE.md   the optional authority ceiling
    echo.
    echo Regenerate the catalog with:  run.bat cli docs-refresh
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
    REM RETIRED IN T6. `src.app install` no longer exists, so this printed
    REM "unknown mode: install" and the usage banner. An installed instance belongs to
    REM ONE target and does not vend further sidecars (Charter SIDECAR:INSTANCE-OWNERSHIP).
    REM Kept as an explicit redirect rather than deleted: a user who learned this verb
    REM deserves to be told where installation moved, not shown a parse error.
    echo Installing a sidecar is the setup application's job, not this runtime's.
    echo.
    echo   Run the setup application you received and choose a folder.
    echo   Headless:  python packaging\installer\install.py --target FOLDER
    echo.
    echo This instance is bound to the folder it lives in and does not install others.
    exit /b 2
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
echo   run.bat attach                       What is this target, and what should I do next
echo   run.bat docs                         List this instance's documentation
echo   run.bat list                         List registered tools
echo   run.bat tool ^<id^> ^<args-json^>       Invoke one tool through the control-plane seam
echo   run.bat cli ^<args...^>                Run any CLI subcommand
echo   run.bat mcp                          Start the MCP server on stdio
echo   run.bat ui                           Launch the registry GUI control panel
echo   run.bat plan                         Launch the project-planner cockpit (start a new project)
echo   run.bat map                          Launch the Project Snapshot window (shareable map/dump)
echo   run.bat smoke                        Run the smoke suite
echo   run.bat refresh                      Regenerate config\registry.json
echo.
echo Notes:
echo   setup_env.bat is optional but recommended; run.bat falls back to system Python.
echo   The GUI, CLI, and MCP all read the same registry and dispatch through one governed seam.
pause
exit /b 0
