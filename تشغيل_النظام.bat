@echo off
start "" "C:\xampp\xampp-control.exe"
timeout /t 3 /nobreak >nul
cd /d "%~dp0"
start /min cmd /c python app.py
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5000