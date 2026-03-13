@echo off
setlocal enabledelayedexpansion

REM === 1) УКАЖИ ПУТЬ ДО PostgreSQL\bin ===
set "PG_BIN=E:\programs\Sql\bin"

REM === 2) ПАРАМЕТРЫ БД (как в .env) ===
set "DB_NAME=happytogether"
set "DB_USER=happytogether_user"
set "DB_HOST=127.0.0.1"
set "DB_PORT=5432"

REM === 3) ПАПКА ДЛЯ БЭКАПОВ ===
set "BACKUP_DIR=%~dp0backups"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM === 4) ИМЯ ФАЙЛА С ДАТОЙ-ВРЕМЕНЕМ ===
for /f "tokens=1-3 delims=." %%a in ("%date%") do set "D=%%c-%%b-%%a"
for /f "tokens=1-2 delims=:" %%a in ("%time%") do set "T=%%a%%b"
set "T=%T: =0%"
set "OUT_FILE=%BACKUP_DIR%\%DB_NAME%_%D%_%T%.dump"

echo [*] Creating backup: "%OUT_FILE%"
echo [*] Host=%DB_HOST% Port=%DB_PORT% DB=%DB_NAME% User=%DB_USER%
echo.

REM Пароль вводить не будем: лучше хранить в переменной окружения PGPASSWORD при запуске
REM Вариант 1: попросить пароль (безопаснее) — просто оставляем как есть, pg_dump сам спросит.
REM Вариант 2: поставить пароль в переменную PGPASSWORD (быстрее, но пароль будет в батнике) — НЕ РЕКОМЕНДУЮ.

"%PG_BIN%\pg_dump.exe" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -F c -b -v -f "%OUT_FILE%" %DB_NAME%

if errorlevel 1 (
  echo [!] Backup FAILED.
  exit /b 1
)

echo.
echo [+] Backup OK.
exit /b 0
