@echo off
echo Starting build_dummies...
C:\Users\Usuario\AppData\Local\Programs\Python\Python310\python.exe -u src\build_dummies.py
echo Script exit code: %ERRORLEVEL%
echo Checking output files:
dir data\processed\*.csv
pause
