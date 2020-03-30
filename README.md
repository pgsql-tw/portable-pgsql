# Portable PostgreSQL for Windows
PostgreSQL 免安裝版，其實 PostgreSQL 不一定需要安裝程序，就可以使用喔！<br/>
你可以自己設定資料目錄，手動啓動它。<br/>
本專案把前置工作先做完了，讓各位可以下載就直接使用。

## Tested
- Windows 10

## Usages

git pull 或打包下載此專案

### 查看版本
```
version.bat
```
### 啓動服務
```
start.bat
```
### 停止服務
```
stop.bat
```
### 測試
1. 啓動服務
2. 打開命令提示字元，%portable-pgsql%請替換成你的下載目錄
3. 預設密碼: 00000000

```
> cd %portable-pgsql%
> bin\psql -U postgres -h localhost -p 5432 postgres
```

