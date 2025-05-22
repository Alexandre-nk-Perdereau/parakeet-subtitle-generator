@echo off
echo Starting Parakeet Subtitle API...
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not installed or not running
    echo Please install Docker Desktop and start it
    pause
    exit /b 1
)

if not exist "temp" mkdir temp

echo Building and starting containers with GPU support...
echo.

docker compose up --build -d

if errorlevel 1 (
    echo ERROR: Failed to start containers
    echo Check logs with: docker compose logs
    pause
    exit /b 1
)

echo.
echo =================================================
echo API starting up...
echo.
echo API URL: http://localhost:8000
echo Documentation: http://localhost:8000/docs
echo.

echo Waiting for model loading (may take 1-2 minutes)...
timeout /t 10 /nobreak >nul

:check_api
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo Loading...
    timeout /t 5 /nobreak >nul
    goto check_api
)

echo API ready!
echo.
echo You can now start the GUI:
echo run.bat
echo =================================================
pause