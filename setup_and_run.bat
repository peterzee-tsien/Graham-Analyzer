@echo off
echo Setting up Benjamin Graham Stock Valuation GUI...

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in your PATH. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Run the application
echo Starting the application...
python main_window.py

pause
