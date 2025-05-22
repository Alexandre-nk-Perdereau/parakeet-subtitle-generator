@echo off
echo Stopping Parakeet Subtitle API...
echo.

docker compose down

if errorlevel 1 (
    echo ERROR: Failed to stop containers
    pause
    exit /b 1
)

echo.
echo =================================================
echo API stopped successfully!
echo =================================================
pause