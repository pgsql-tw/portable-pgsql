@echo off
cd %~dp0
bin\postgres -V
bin\pg_ctl -D data -l logfile.txt start