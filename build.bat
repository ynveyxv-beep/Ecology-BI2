@echo off
title Ecology-BI Builder

echo.
echo === Ecology-BI Full Build ===
echo.

:: ── 1. Activate venv ────────────────────────────────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: venv not found. Run: python -m venv venv
    pause & exit /b 1
)
call venv\Scripts\activate.bat
echo [OK] venv activated

:: ── 2. Install Python deps ───────────────────────────────────────────────────
python -c "import matplotlib"    2>nul || pip install matplotlib --quiet
python -c "import openpyxl"      2>nul || pip install openpyxl --quiet
python -c "import pyqtgraph"     2>nul || pip install pyqtgraph --quiet
python -c "import PySide6.QtSvg" 2>nul || pip install PySide6 --upgrade --quiet
python -m PyInstaller --version >nul 2>&1 || pip install pyinstaller --quiet
echo [OK] Python dependencies ready

:: ── 3. Clean previous build ──────────────────────────────────────────────────
echo [*] Cleaning previous build...
if exist "dist\Ecology-BI" rmdir /s /q "dist\Ecology-BI"
if exist "build"            rmdir /s /q "build"
if exist "installer"        rmdir /s /q "installer"

:: ── 4. PyInstaller ───────────────────────────────────────────────────────────
echo [*] Running PyInstaller (2-5 min)...
python -m PyInstaller ecology_bi.spec --noconfirm

if errorlevel 1 (
    echo ERROR: PyInstaller failed. See output above.
    pause & exit /b 1
)

:: Create templates folder
if not exist "dist\Ecology-BI\templates" mkdir "dist\Ecology-BI\templates"
if exist "templates\*.json" xcopy "templates\*.json" "dist\Ecology-BI\templates\" /Q /Y >nul

:: Copy AI model folder (GGUF-файл нужен рядом с exe для работы AI-ассистента)
if exist "models" (
    echo [*] Copying AI model folder...
    if not exist "dist\Ecology-BI\models" mkdir "dist\Ecology-BI\models"
    xcopy "models\*" "dist\Ecology-BI\models\" /Q /Y >nul
    echo [OK] Models copied
) else (
    echo [!] Папка models не найдена - AI-ассистент работать не будет.
    echo     Поместите qwen2.5-0.5b-instruct-q4_k_m.gguf в dist\Ecology-BI\models\
)

echo [OK] PyInstaller done

:: ── 5. Inno Setup ────────────────────────────────────────────────────────────
echo [*] Looking for Inno Setup...

set ISCC=

:: Try PATH first
where ISCC.exe >nul 2>&1 && set ISCC=ISCC.exe

:: Common install locations
if not defined ISCC if exist "C:\Program Files\Inno Setup 7\ISCC.exe"           set ISCC=C:\Program Files\Inno Setup 7\ISCC.exe
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe"       set ISCC=C:\Program Files (x86)\Inno Setup 7\ISCC.exe
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe"             set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not defined ISCC if exist "C:\Program Files\Inno Setup 5\ISCC.exe"             set ISCC=C:\Program Files\Inno Setup 5\ISCC.exe
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"       set ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe

:: Search registry for install path
if not defined ISCC (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup_is1" /v "InstallLocation" 2^>nul') do (
        if exist "%%b\ISCC.exe" set ISCC=%%bISCC.exe
    )
)
if not defined ISCC (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup_is1" /v "InstallLocation" 2^>nul') do (
        if exist "%%b\ISCC.exe" set ISCC=%%bISCC.exe
    )
)

if not defined ISCC (
    echo.
    echo [!] Inno Setup not found. Try:
    echo     1. Restart this bat after installing
    echo     2. Or run manually: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo.
    echo App folder is ready: dist\Ecology-BI\
    pause & exit /b 1
)

echo [OK] Found: %ISCC%

echo [*] Building installer...
mkdir installer 2>nul
"%ISCC%" installer.iss

if errorlevel 1 (
    echo ERROR: Inno Setup failed. See output above.
    pause & exit /b 1
)

:: ── 6. Done ──────────────────────────────────────────────────────────────────
echo.
echo === Done! ===
echo.
echo   Installer: installer\Ecology-BI-Setup.exe
echo   App folder: dist\Ecology-BI\
echo.
explorer "installer"
pause
