@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0..\backend"

if not exist .venv\Scripts\activate.bat (
  echo Сначала запустите setup.bat
  pause
  exit /b 1
)

echo Запуск Banetskaya.by ...
echo Приложение откроется в браузере: http://127.0.0.1:8001
call .venv\Scripts\activate.bat

REM Открыть браузер через 4 секунды после старта сервера
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8001"

python -m uvicorn server:app --host 127.0.0.1 --port 8001
pause
