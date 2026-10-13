@echo off
chcp 65001 >nul
rem Двойной клик — запускает курс в браузере. Окно не закрывайте, пока учитесь.
cd /d "%~dp0"
set "PY="

if exist "runtime\python\python.exe" set "PY=runtime\python\python.exe"
if defined PY goto run

rem Установленный Python: сначала py (лаунчер python.org), потом python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto run
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto run

echo Python не найден. Скачиваю переносной Python 3.12 — около 11 МБ, один раз.
echo Он ляжет в папку runtime рядом с курсом и ничего не установит в систему.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\get-python.ps1"
if exist "runtime\python\python.exe" set "PY=runtime\python\python.exe"
if defined PY goto run

echo.
echo Не получилось скачать Python. Установите его с https://www.python.org/downloads/
echo — при установке отметьте «Add python.exe to PATH» — и запустите этот файл снова.
pause
exit /b 1

:run
%PY% tools\serve.py
if errorlevel 1 pause
