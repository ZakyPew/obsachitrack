@echo off
REM StreamTracker Windows Build - Batch Wrapper 🎀

echo ============================================
echo 🎀 StreamTracker Windows Build
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.x
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
)

echo 🚀 Starting build...
python build_windows.py

echo.
echo Press any key to exit...
pause >nul
