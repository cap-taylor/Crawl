@echo off
REM Setup script for Product Collector GUI
REM Run this script ONCE on a new computer

echo ========================================
echo Product Collector - Initial Setup
echo ========================================
echo.

REM Check Python installation
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Install Python packages
echo [2/4] Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages!
    pause
    exit /b 1
)
echo.

REM Install Playwright browsers
echo [3/4] Installing Playwright browsers...
playwright install firefox
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Playwright browsers!
    pause
    exit /b 1
)
echo.

REM Create .env file if not exists
echo [4/4] Checking .env file...
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file and set your DB_PASSWORD!
    echo File location: %CD%\.env
    echo.
) else (
    echo .env file already exists.
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and set DB_PASSWORD
echo 2. Run 'run_gui.bat' to start the application
echo.
pause
