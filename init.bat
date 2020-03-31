@echo off
set DATA=data
cd %~dp0
.\bin\initdb.exe -D %DATA% -A md5 -U postgres -W -E UTF8
