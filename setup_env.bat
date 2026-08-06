@echo off
:: FILE:    setup_env.bat
:: ROLE:    Create/refresh the shared root .venv for the whole suite (decision A).
:: STATUS:  DONE — installs the shared dependency union used by supported launchers.
:: NOTES:   One env at the project root; all tools/apps share it.
setlocal
cd /d "%~dp0"
if not exist ".venv" (
    echo Creating shared root virtual environment...
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if exist "requirements.txt" pip install -r requirements.txt
echo.
echo Shared root environment ready (.venv).
endlocal
