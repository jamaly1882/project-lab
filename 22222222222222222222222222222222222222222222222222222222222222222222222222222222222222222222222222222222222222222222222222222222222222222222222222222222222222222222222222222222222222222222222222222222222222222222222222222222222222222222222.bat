@echo off
setlocal

set PROJECT_PATH=F:\2007\erea
set BACKUP_PATH=F:\2007\erea\backup

set MYSQLDUMP=C:\xampp\mysql\bin\mysqldump.exe
set PYTHON=F:\2007\erea\myenv\Scripts\python.exe

set USER=root
set PASSWORD=Egypt-+20!!
set DBNAME=erea

timeout /t 60 >nul

REM تشغيل MySQL Service
sc query MySQL | find "RUNNING" >nul
if errorlevel 1 (
    net start MySQL
    timeout /t 30 >nul
)

REM انتظار جاهزية MySQL
:WAITMYSQL
"%MYSQLDUMP%" -u %USER% -p"%PASSWORD%" --no-data %DBNAME% >nul 2>&1
if errorlevel 1 (
    timeout /t 5 >nul
    goto WAITMYSQL
)

for /f "tokens=1-3 delims=/-." %%a in ("%date%") do set TODAY=%%c%%a%%b

if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"

"%MYSQLDUMP%" -u %USER% -p"%PASSWORD%" %DBNAME% > "%BACKUP_PATH%\%DBNAME%_%TODAY%.sql"

for /f "skip=7" %%f in ('dir /b /o-d "%BACKUP_PATH%\%DBNAME%_*.sql"') do del "%BACKUP_PATH%\%%f"

cd /d "%PROJECT_PATH%"
start "" cmd /c ""%PYTHON%" manage.py runserver 127.0.0.1:8000 --noreload"

powershell -Command ^
"while (-not (Test-NetConnection 127.0.0.1 -Port 8000 -InformationLevel Quiet)) { Start-Sleep 1 }"

start "" "http://127.0.0.1:8000"

endlocal
