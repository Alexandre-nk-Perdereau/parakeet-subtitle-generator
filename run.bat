@echo off
echo Starting Parakeet Subtitle Generator...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

python -c "import tkinterdnd2" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Missing dependencies
    echo Reinstalling dependencies...
    uv pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting GUI...
python subtitle_gui.py

if errorlevel 1 (
    echo.
    echo Application closed with error.
    pause
)

echo.
echo Goodbye!
pause