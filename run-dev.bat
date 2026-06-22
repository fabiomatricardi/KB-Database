@echo off
echo ========================================
echo   ArticleDatabase - Dev Mode
echo ========================================

echo.
echo [1/2] Installing Python dependencies...
call uv sync

echo.
echo [2/2] Starting FastAPI server...
echo Open http://localhost:8000 in your browser
echo.
call uv run python -m backend.main
