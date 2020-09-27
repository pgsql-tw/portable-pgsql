# Portable PostgreSQL for Windows
PostgreSQL 免安裝版，其實 PostgreSQL 不一定需要安裝程序，就可以使用喔！<br/>
你可以自己設定資料目錄，也可以不管，總之就是啓動它。<br/>
本專案把前置工作先做完了，讓各位可以下載就直接使用。

下面情況使用這個機制特別方便：
1. 你在你要安裝的電腦沒有管理者權限。
2. 你需要同時使用好幾個不同的 PostgreSQL。
3. 你的應用軟體自帶 PostgreSQL，程式開關服務和調整參數。
4. 你只想使用 Client 工具或 pgAdmin 4。

如果你也想做一個你自己的，最簡單的方法就是，把你安裝好的 PostgreSQL 拷貝出來，大致上就是本專案的內容。

## Tested
- Windows 10

## Usages

1. Clone 或 Download 此專案。
2. 修改 PGDATA.txt，設定資料庫資料檔案的路徑。
3. 第一次使用請先執行 init.bat。
4. 密碼就是 postgres 的密碼，不要忘記自己輸入的密碼。

### 查看版本
```
version.bat
```
### 啓動服務
- 視窗不要關掉，關掉視窗就會停止服務。
- Port 是預設的 5432。
```
start.bat
```
### 停止服務
- 如果你要從別的視窗關服務的話
```
stop.bat
```
### 測試
1. 啓動服務
2. 打開命令提示字元，%portable-pgsql% 請替換成你的下載目錄
3. 預設密碼: 在執行 init.bat 時輸入的密碼

```
> cd %portable-pgsql%
> bin\psql -U postgres -h localhost -p 5432 postgres
```

## 其他
1. 使用後會新產生一個 logfile.txt 記錄檔，供除錯之用。
2. "data" 目錄是可以搬移的，在停止服務的狀態，放置到你需要的路徑，然後修改 start.bat 和 stop.bat 的內容。
3. start.bat 和 stop.bat 指向的資料目錄(-D directory)必須相同。
4. 請參閱： [pg_ctl](https://www.postgresql.org/docs/current/app-pg-ctl.html)、[initdb](https://www.postgresql.org/docs/current/app-initdb.html)、[postgres](https://www.postgresql.org/docs/current/app-postgres.html)
