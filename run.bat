@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\sortmyset-gui.exe" (
    call "%~dp0install.bat"
)

if "%~1"=="" (
    start "" "%VENV_DIR%\Scripts\sortmyset-gui.exe"
    exit /b
)

if /I "%~1"=="gui" (
    shift
    start "" "%VENV_DIR%\Scripts\sortmyset-gui.exe" %*
    exit /b
)

if /I "%~1"=="cli" (
    shift
    "%VENV_DIR%\Scripts\sortmyset.exe" %*
    exit /b
)

"%VENV_DIR%\Scripts\sortmyset.exe" %*
