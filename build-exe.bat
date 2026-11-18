@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" call "%~dp0install.bat"

"%VENV_DIR%\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 (
    echo Failed to install PyInstaller.
    pause
    exit /b 1
)

"%VENV_DIR%\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed ^
    --name SortMySet-GUI --paths src sortmyset_gui.py
if errorlevel 1 exit /b 1

"%VENV_DIR%\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --console ^
    --name SortMySet --paths src sortmyset_cli.py
if errorlevel 1 exit /b 1

echo.
echo Built executables:
echo dist\SortMySet-GUI.exe
echo dist\SortMySet.exe
pause
