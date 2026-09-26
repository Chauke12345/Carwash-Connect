@echo off
cd /d "D:\Edvance Tech\EdVance Projects\CarWash Connect"
start "" ".venv\Scripts\pythonw.exe" manage.py runserver 8008
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8008/"
exit
