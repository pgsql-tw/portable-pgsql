@echo off
set /p DATA=<PGDATA.txt
cd %~dp0
bin\pg_ctl -D %DATA% -l logfile.txt stop