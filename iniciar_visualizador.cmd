@echo off
setlocal
title Visualizador TFG - Servidor

REM Carpeta del proyecto (donde esta este .cmd)
cd /d "%~dp0"

set PYEXE=C:\Users\Usuario\AppData\Local\Programs\Python\Python310\python.exe
if not exist "%PYEXE%" set PYEXE=python

echo ====================================================
echo   Visualizador TFG - Iniciando servidor
echo ====================================================
echo.

REM 1. Regenerar visualizador.html con los datos embebidos
echo [1/2] Regenerando visualizador.html...
"%PYEXE%" notebooks\generar_visualizador.py
if errorlevel 1 (
  echo.
  echo ERROR al regenerar visualizador.html. Mira el log de arriba.
  pause
  exit /b 1
)
echo.

REM 2. Levantar servidor (abre el browser solo)
echo [2/2] Levantando servidor en http://localhost:8765/
echo     Ctrl+C en esta ventana para detenerlo.
echo.
"%PYEXE%" notebooks\server.py --port 8765

echo.
echo Servidor detenido.
pause
