@echo off
REM Run Product Collector GUI
REM Double-click this file to start the application

echo ========================================
echo Starting Product Collector GUI...
echo ========================================
echo.

REM Check if setup was run
if not exist .env (
    echo ERROR: .env file not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Run the GUI (Multi-Task Version - Latest)
python product_collector_multi_gui.py

REM Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application crashed!
    echo Check the error message above.
    pause
)
