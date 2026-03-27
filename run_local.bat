@echo off
echo === Wedding Photo Upload - Local Test ===
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install it from https://python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

:: Create .env if missing
if not exist ".env" (
    copy .env.example .env >nul
    echo Created .env from .env.example
)

echo.
echo ==========================================
echo   Open http://localhost:5000 in browser
echo   Try http://localhost:5000/?table=7
echo   Press Ctrl+C to stop
echo ==========================================
echo.

python app.py
