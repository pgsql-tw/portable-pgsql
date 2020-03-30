@echo off
cd %~dp0
bin\pg_ctl -D "data\postgres" -l logfile.txt stop