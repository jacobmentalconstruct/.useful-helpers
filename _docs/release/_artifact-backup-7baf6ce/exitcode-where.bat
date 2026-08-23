@echo off
setlocal
rem  Where does the exit code go? V13 says `run.bat cli tool-call <unknown tool>` returns 0
rem  on Windows, but `run.bat tool ping <inline json>` returned 255 in the same run - so the
rem  launcher CAN propagate. Four measurements localise it. Run with no arguments.
set "W=%TEMP%\uh-rc-probe"
rmdir /s /q "%W%" 2>nul
mkdir "%W%\target" 2>nul
python -c "import shutil,os,sys;shutil.unpack_archive(sys.argv[1], os.path.join(os.environ['TEMP'],'uh-rc-probe','dist'))" "%~dp0..\artifact\useful-helpers-release.zip" || goto :fail
python "%W%\dist\install.py" --target "%W%\target" --mode install >nul || goto :fail
set "H=%W%\target\.useful-helpers"
echo.
echo   exit-code localisation
echo   ----------------------
cmd /c ""%H%\run.bat" cli tool-call --tool __no_such_tool__ --args-json {}" >nul 2>&1
echo     A  run.bat cli tool-call ^<unknown^>     -^> %ERRORLEVEL%     want non-zero
pushd "%H%"
cmd /c "python -m src.app cli tool-call --tool __no_such_tool__ --args-json {}" >nul 2>&1
echo     B  python -m src.app   ^<unknown^>       -^> %ERRORLEVEL%     want non-zero
popd
cmd /c ""%H%\run.bat" tool __no_such_tool__ {}" >nul 2>&1
echo     C  run.bat tool ^<unknown^> {}           -^> %ERRORLEVEL%     want non-zero
cmd /c ""%H%\run.bat" cli version" >nul 2>&1
echo     D  run.bat cli version ^(control^)       -^> %ERRORLEVEL%     want 0
echo.
echo   A=0 with B non-zero  -^> the launcher loses it in the `cli` branch
echo   A and B both 0       -^> the CLI itself returns 0 for an unknown tool on Windows
echo.
goto :eof
:fail
echo   probe setup failed - is _docs\release\artifact\useful-helpers-release.zip present?
