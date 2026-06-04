@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   PageIndex Web - Starting...
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Starting backend on http://localhost:8001 ...
start "PageIndex-Backend" cmd /c "cd /d "%~dp0" && python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8001"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend on http://localhost:3000 ...
start "PageIndex-Frontend" cmd /c "cd /d "%~dp0\web" && npx vite --port 3000 --host"

echo.
echo ========================================
echo   Backend:  http://localhost:8001/api
echo   Frontend: http://localhost:3000
echo ========================================
echo.
echo Open http://localhost:3000 in your browser.
echo Press any key to stop both servers...
pause >nul

taskkill /FI "WINDOWTITLE eq PageIndex-Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq PageIndex-Frontend*" /F >nul 2>&1
