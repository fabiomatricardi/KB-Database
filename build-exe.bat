@echo off
echo ============================================
echo   Building ArticleDatabase v0.2.2
echo ============================================
echo.

echo [1/3] Building Vue frontend...
cd frontend
call npm install
call npm run build
if %ERRORLEVEL% neq 0 (
    echo ERROR: Frontend build failed!
    exit /b 1
)
cd ..

echo.
echo [2/3] Installing Python dependencies...
call uv sync
if %ERRORLEVEL% neq 0 (
    echo ERROR: uv sync failed!
    exit /b 1
)

echo.
echo [3/3] Building .exe with PyInstaller...
call uv run python build.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller build failed!
    exit /b 1
)

echo.
echo ============================================
echo   DONE! Output: dist\ArticleDatabase-v0.2.2.exe
echo ============================================
pause
