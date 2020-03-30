@echo off
cd %~dp0
bin\postgres -V
bin\pg_ctl -D "data\postgres" -l logfile.txt start