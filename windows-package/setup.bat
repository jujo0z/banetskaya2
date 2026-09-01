@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."
echo ============================================
echo   Banetskaya.by - установка (Windows)
echo ============================================
echo.

echo [1/4] Создаю виртуальное окружение Python...
cd backend
python -m venv .venv || goto :err
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [2/4] Устанавливаю зависимости бэкенда...
pip install -r "%~dp0requirements-windows.txt" || goto :err
call deactivate
cd ..

echo [3/4] Готовлю .env файлы...
if not exist backend\.env copy /Y "%~dp0backend.env.example" backend\.env
copy /Y "%~dp0frontend.env.example" frontend\.env

echo [4/4] Собираю фронтенд (это может занять несколько минут)...
cd frontend
call yarn install || goto :err
call yarn build || goto :err
cd ..

echo.
echo ============================================
echo   Установка завершена!
echo   1) Проверьте backend\.env (путь к LibreOffice)
echo   2) Запустите start.bat
echo ============================================
pause
exit /b 0

:err
echo.
echo ОШИБКА при установке. Убедитесь, что установлены Python 3.11, Node.js LTS и Yarn.
pause
exit /b 1
