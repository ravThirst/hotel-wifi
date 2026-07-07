@echo off
title Hotel WiFi Management System

echo [1/4] Activating Virtual Environment...
call .venv\Scripts\activate.bat

echo [2/4] Applying Database Migrations...
python manage.py migrate --noinput

echo [3/4] Collecting Static Files...
python manage.py collectstatic --noinput

echo [4/4] Starting Waitress Production Server...
echo.
python run_server.py

:: If the server crashes, this keeps the window open so you can read the error
pause