@echo off
:: 1. Force the working directory to be the folder where this .bat file lives.
:: This prevents Task Scheduler from running in the wrong directory (like C:\Windows\System32).
cd /d "%~dp0"

:: 2. Activate the Python Virtual Environment
call .venv\Scripts\activate.bat

:: 3. Run the Django management command.
:: >> appends standard output to the log file.
:: 2>&1 redirects error output to the same log file.
python manage.py expire_sessions >> cron_jobs.log 2>&1