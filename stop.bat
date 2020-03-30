@echo off
cd %~dp0
bin\pg_ctl -D data -l logfile.txt stop