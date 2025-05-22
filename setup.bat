@echo off
echo Installing Parakeet Subtitle environment...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Checking uv...
uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv...
    python -m pip install uv
    if errorlevel 1 (
        echo ERROR: Failed to install uv
        pause
        exit /b 1
    )
)

echo Creating virtual environment...
uv venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
uv pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo =================================================
echo Installation completed successfully!
echo.
echo To run the application:
echo 1. Activate environment: venv\Scripts\activate.bat
echo 2. Start app: python subtitle_gui.py
echo.
echo Don't forget to start the Docker API first!
echo =================================================
pause