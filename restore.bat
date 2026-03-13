@echo off
setlocal

REM === 1) УКАЖИ ПУТЬ ДО PostgreSQL\bin ===
set "PG_BIN=E:\programs\Sql\bin"

REM === 2) ПАРАМЕТРЫ БД ===
set "DB_NAME=happytogether"
set "DB_USER=happytogether_user"
set "DB_HOST=127.0.0.1"
set "DB_PORT=5432"

REM === 3) ФАЙЛ ДЛЯ ВОССТАНОВЛЕНИЯ (передай как параметр) ===
if "%~1"=="" (
  echo Usage: restore.bat "C:\projects\intranet\backups\file.dump"
  exit /b 1
)
set "IN_FILE=%~1"

echo [!] This will restore DB from: "%IN_FILE%"
echo [*] Host=%DB_HOST% Port=%DB_PORT% DB=%DB_NAME% User=%DB_USER%
echo.

REM Восстановление формата custom (-F c) делается через pg_restore
"%PG_BIN%\pg_restore.exe" -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c -v "%IN_FILE%"

if errorlevel 1 (
  echo [!] Restore FAILED.
  exit /b 1
)

echo.
echo [+] Restore OK.
exit /b 0
