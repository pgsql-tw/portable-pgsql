@echo off
set /p DATA=<PGDATA.txt
cd %~dp0
.\bin\initdb.exe -D %DATA% -A md5 -U postgres -W -E UTF8