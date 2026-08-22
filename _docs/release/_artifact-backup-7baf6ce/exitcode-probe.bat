@echo off
setlocal
rem  P5b exit-code probe.  Answers one question: does `goto :eof` carry a non-zero
rem  exit code out of a parenthesized if-block, where `exit /b %ERRORLEVEL%` does not?
rem  Run it with no arguments; it calls itself for each case.
if "%~1"=="a" (
    cmd /c exit 7
    goto :eof
)
if "%~1"=="b" (
    cmd /c exit 7
    exit /b %ERRORLEVEL%
)
if "%~1"=="c" (
    python -c "import sys; sys.exit(3)"
    goto :eof
)
echo.
echo   P5b exit-code probe
echo   -------------------
call "%~f0" a
echo     goto :eof                 -^> %ERRORLEVEL%     want 7
call "%~f0" b
echo     exit /b %%ERRORLEVEL%%       -^> %ERRORLEVEL%     want 7  ^(0 confirms the bug^)
call "%~f0" c
echo     goto :eof after python    -^> %ERRORLEVEL%     want 3
echo.
