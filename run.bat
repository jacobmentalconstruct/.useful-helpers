@echo off
REM FILE:    run.bat
REM ROLE:    Supported Windows operator entrance for the Useful Helpers Suite.
REM USAGE:   run.bat help ^| attach ^| docs ^| list ^| refresh ^| smoke ^| ui ^| map ^| plan ^| cli ^<args...^> ^| mcp ^| tool ^<id^> ^<args-json^|@file^>
REM NOTES:   Convenience wrapper over python -m src.app and smoke_test.py. Resolves its
REM          own directory, so the working directory you start from does not matter -
REM          but it is not on PATH, so invoke it BY PATH: .useful-helpers\run.bat attach
REM
REM          EVERY MODE DISPATCHES BY LABEL AND ENDS WITH `exit /b %ERRORLEVEL%` AT THE
REM          TOP LEVEL. Two earlier shapes both lost the exit code, for different reasons,
REM          and both were measured rather than reasoned about:
REM
REM            exit /b %ERRORLEVEL% INSIDE an if-block -> 0.  cmd expands the variable when
REM            it parses the block, which is before the command in the block has run.
REM
REM            goto :eof inside an if-block            -> 0.  Correct when the batch is
REM            reached by `call` from another batch, and NOT when it is spawned as
REM            `cmd /c run.bat ...` - which is how every programmatic caller reaches it,
REM            including the release verifier.
REM
REM          `run.bat smoke` therefore watched 88 tests fail for 184 seconds and exited 0,
REM          and a release gate recorded ten checks as passing on the strength of it. At
REM          the top level there is no block to parse early and no `call` frame to return
REM          into, so the expansion happens per line, at execution, from the command that
REM          just ran. Delayed expansion would also work and is deliberately NOT used: it
REM          makes cmd process `!` inside every expanded string, and the payloads here are
REM          JSON.
REM
REM          INLINE JSON IS FOR HUMANS, `@file` IS FOR PROGRAMS. A .bat receives its
REM          arguments through cmd.exe, which does not read the backslash-escaped quotes
REM          that every language's subprocess layer emits - so a JSON payload sent by a
REM          program arrives shattered across %2, %3, %4... That is a property of cmd, not
REM          something this file can repair. Programmatic callers pass `@<path>`.
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"

if "%~1"=="" goto :help
if /I "%~1"=="help" goto :help
if /I "%~1"=="menu" goto :help
if /I "%~1"=="docs" goto :m_docs
if /I "%~1"=="list" goto :m_list
if /I "%~1"=="attach" goto :m_attach
if /I "%~1"=="refresh" goto :m_refresh
if /I "%~1"=="smoke" goto :m_smoke
if /I "%~1"=="mcp" goto :m_mcp
if /I "%~1"=="ui" goto :m_ui
if /I "%~1"=="plan" goto :m_plan
if /I "%~1"=="map" goto :m_map
if /I "%~1"=="install" goto :m_install
if /I "%~1"=="tool" goto :m_tool
if /I "%~1"=="cli" goto :m_cli
"%PYTHON_EXE%" -m src.app %*
exit /b %ERRORLEVEL%

:m_list
"%PYTHON_EXE%" -m src.app cli tool-list
exit /b %ERRORLEVEL%

:m_attach
REM The first question anyone asks: what is this target, and what next.
"%PYTHON_EXE%" -m src.app cli tool-call --tool attach --args-json "{}"
exit /b %ERRORLEVEL%

:m_refresh
"%PYTHON_EXE%" -m src.app cli registry-refresh
exit /b %ERRORLEVEL%

:m_smoke
"%PYTHON_EXE%" smoke_test.py
exit /b %ERRORLEVEL%

:m_mcp
"%PYTHON_EXE%" -m src.app mcp
exit /b %ERRORLEVEL%

:m_ui
"%PYTHON_EXE%" -m src.app ui
exit /b %ERRORLEVEL%

:m_plan
"%PYTHON_EXE%" -m src.app plan
exit /b %ERRORLEVEL%

:m_map
"%PYTHON_EXE%" -m src.app map
exit /b %ERRORLEVEL%

:m_cli
"%PYTHON_EXE%" -m src.app %*
exit /b %ERRORLEVEL%

:m_tool
if "%~2"=="" goto :tool_usage
if "%~3"=="" goto :tool_default
"%PYTHON_EXE%" -m src.app cli tool-call --tool "%~2" --args-json "%~3"
exit /b %ERRORLEVEL%

:tool_default
"%PYTHON_EXE%" -m src.app cli tool-call --tool "%~2" --args-json "{}"
exit /b %ERRORLEVEL%

:tool_usage
echo Usage: run.bat tool ^<tool_id^> ^<args-json ^| @file^>
exit /b 2

:m_docs
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

:m_install
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

:help
echo Useful Helpers Suite
echo.
echo Supported entrances:
echo   run.bat attach                       What is this target, and what should I do next
echo   run.bat docs                         List this instance's documentation
echo   run.bat list                         List registered tools
echo   run.bat tool ^<id^> ^<args-json^>       Invoke one tool through the control-plane seam
echo   run.bat tool ^<id^> @^<file^>          ...with the payload read from a file
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
echo.
echo   INLINE JSON IS FOR HUMANS TYPING IT. Scripts and programs must use @^<file^>:
echo   arguments reach a .bat through cmd.exe, which does not read the backslash-escaped
echo   quotes that subprocess layers emit, so an inline payload sent by a program arrives
echo   split across several arguments. This is a cmd.exe boundary, not a defect this
echo   launcher can repair. On POSIX, run.sh receives an argument vector and both forms
echo   are exact.
pause
exit /b 0
