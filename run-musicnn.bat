@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" call "%~dp0install.bat" /musicnn

"%VENV_DIR%\Scripts\sortmyset-gui.exe"
