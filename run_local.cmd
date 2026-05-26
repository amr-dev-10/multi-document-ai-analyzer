@echo off
setlocal
cd /d "%~dp0"
".venv-py312\Scripts\python.exe" -c "from backend.db.session import init_db; init_db(); print('database connected and tables created')"
if errorlevel 1 (
  echo.
  echo Database connection failed. Start PostgreSQL in WSL and verify the analyzer user/database.
  exit /b 1
)
".venv-py312\Scripts\python.exe" run_dev.py
