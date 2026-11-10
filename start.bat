@echo off
REM Starts AgriCred on Windows (run the setup in README.md once first).
cd /d "%~dp0"
start "AgriCred API" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python app.py"
start "AgriCred web" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 6 /nobreak >nul
start http://localhost:5173
