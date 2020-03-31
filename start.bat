@echo off
set DATA=data
cd %~dp0
bin\postgres -V
bin\pg_ctl -D %DATA% -l logfile.txt start
