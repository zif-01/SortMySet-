@echo off
setlocal

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "INSTALL_MUSICNN=0"
set "INSTALL_ACQUISITION=0"

if /I "%~1"=="/musicnn" set "INSTALL_MUSICNN=1"
if /I "%~1"=="/acquisition" set "INSTALL_ACQUISITION=1"
if /I "%~1"=="/all" (
    set "INSTALL_MUSICNN=1"
    set "INSTALL_ACQUISITION=1"
)
if /I "%~2"=="/musicnn" set "INSTALL_MUSICNN=1"
if /I "%~2"=="/acquisition" set "INSTALL_ACQUISITION=1"
if /I "%~2"=="/all" (
    set "INSTALL_MUSICNN=1"
    set "INSTALL_ACQUISITION=1"
)

py -3 --version >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python 3.10 or newer is required.
        pause
        exit /b 1
    )
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment: %VENV_DIR%
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -e ".[audio]"

if "%INSTALL_MUSICNN%"=="1" (
    echo Installing MusicNN support...
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements-musicnn.txt
)

if "%INSTALL_ACQUISITION%"=="1" (
    echo Installing acquisition support...
    "%VENV_DIR%\Scripts\python.exe" -m pip install yt-dlp
    where ffmpeg >nul 2>nul
    if errorlevel 1 (
        echo.
        echo ffmpeg was not found on PATH.
        echo Install it with: winget install Gyan.FFmpeg
        echo Or add the ffmpeg executable directory to PATH.
    )
)

echo.
echo SortMySet installed.
echo Start it with: run.bat
pause
