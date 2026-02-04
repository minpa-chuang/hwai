# 工作日誌與維修管理系統

本專案依循《工作日誌與維修管理系統 - 功能需求規格書 v2.3》建立，目標為提供一套基於 **PHP + MariaDB** 的維修工作管理平台。本階段著重於建立初始專案結構、資料庫 Schema 與環境設定範例，為後續功能開發打下基礎。

## 專案結構

```
backend/
├── bootstrap.php          # 後端啟動檔，負責載入設定與初始化元件
├── config/
│   └── database.php       # 資料庫連線設定
├── public/
│   └── index.php          # API 入口檔 (預計搭配前端以 REST API 互動)
├── src/
│   ├── Application.php    # 系統核心容器，集中服務註冊與取得
│   ├── Http/
│   │   └── Router.php     # 簡易路由器，後續將擴充為 RESTful API 處理
│   └── Support/
│       └── Env.php        # 讀取 .env 設定的輔助類別
└── storage/
    └── logs/              # 紀錄應用程式日誌 (預留)

database/
└── schema.sql             # MariaDB 建表語法 (對應規格書所有資料表)

frontend/
└── README.md              # 前端規劃說明與後續開發待辦

.env.example               # 環境變數範例設定
```

## 開發環境準備

1. 複製 `.env.example` 為 `.env`，並依實際環境調整設定值。
2. 使用 Composer 安裝依賴套件：

   ```bash
   composer install
   ```

3. 建立資料庫並導入 `database/schema.sql`：

   ```bash
   mysql -u <USER> -p <DATABASE_NAME> < database/schema.sql
   ```

4. 使用 PHP 內建伺服器啟動後端 (開發模式)：

   ```bash
   php -S 0.0.0.0:8000 -t backend/public backend/public/index.php
   ```

5. 覆蓋 `backend/public/index.php` 以框架或自訂路由處理所有 API 請求。後續開發將導入更完整的 MVC 或微框架實作。

## 後續開發重點

- 實作使用者認證與雙層權限。
- 依照規格書實作維修記錄、標籤、附件、稽核等 API。
- 建立前端儀表板、查詢介面與統計圖表。
- 整合郵件服務、快取機制與安全強化需求。
- 撰寫自動化測試與 API 文件 (OpenAPI)。

## 員工上下班打卡系統規劃

以下為員工上下班打卡系統的基礎規劃，聚焦於帳號密碼認證、行動裝置綁定與 GPS 位置驗證，便於後續納入本專案或獨立實作。

### 目標與範圍

- 提供員工每日上下班打卡、補打卡與稽核流程。
- 支援帳號密碼登入與裝置綁定，避免代打卡。
- 透過 GPS 定位驗證打卡位置，支援公司/工地/多據點。

### 使用者流程

1. **註冊/建立帳號**：由管理者匯入或人工建立，初次登入強制修改密碼。
2. **登入**：帳號密碼 + 短期驗證碼 (可選)。
3. **綁定裝置**：
   - 首次登入需完成裝置綁定 (可使用 device_id + 推播 token)。
   - 支援管理者解除綁定或更換裝置。
4. **打卡**：
   - App 取得 GPS 位置與時間戳記。
   - 後端驗證裝置綁定狀態與定位是否符合允許範圍。
   - 上/下班、出差、外勤等類型打卡。
5. **補打卡**：
   - 員工提出補卡申請，需附原因與證明。
   - 主管審核後入帳。

### 核心功能需求

- **帳號密碼認證**
  - 密碼加鹽雜湊儲存 (例如 bcrypt/argon2)。
  - 密碼策略：最少長度、複雜度、定期更新。
  - 失敗登入鎖定策略與審計日誌。
- **行動裝置綁定**
  - 單一員工可綁定 1~N 台裝置 (依政策)。
  - 裝置指紋欄位：device_id、OS、App 版本、推播 token。
  - 支援遠端解除綁定與異常通知。
- **GPS 位置驗證**
  - 定義多個「允許位置」(中心點 + 半徑或多邊形)。
  - 打卡時回傳 GPS 精度、速度、定位來源 (GPS/Wi-Fi/Cell)。
  - 位置偏差超過門檻時要求補充說明或管理者確認。

### 資料模型草案

- **employees**：員工基本資料、狀態、部門/職級。
- **auth_accounts**：帳號、密碼雜湊、最後登入時間、鎖定狀態。
- **devices**：裝置資訊、綁定狀態、最後使用時間。
- **work_sites**：允許打卡位置、GPS 範圍與有效期間。
- **clock_records**：打卡紀錄 (上班/下班/外勤/補卡)。
- **clock_corrections**：補卡申請與審核流程。
- **audit_logs**：登入、綁定、打卡與審核操作紀錄。

### API 規劃 (示意)

- `POST /api/auth/login`：登入取得 access token。
- `POST /api/devices/bind`：綁定裝置。
- `POST /api/clock/records`：提交打卡 (包含 GPS、裝置資訊)。
- `GET /api/clock/records`：查詢打卡紀錄。
- `POST /api/clock/corrections`：提交補卡申請。
- `POST /api/clock/corrections/{id}/approve`：主管審核。

### 權限與稽核

- 員工僅可查看自己的打卡記錄與補卡申請。
- 主管可檢視所屬部門，HR 可全域檢視。
- 重要操作 (解除綁定、補卡審核) 需完整稽核紀錄。

### 資安與隱私

- 所有 API 需走 HTTPS。
- GPS 資訊儘量採用最小必要原則，僅保存必要精度與期限。
- 需提供使用者可查詢的個資使用告知與保留期限。

### 後續擴充

- 人臉辨識或 NFC 打卡。
- 離線打卡與補傳機制。
- 報表匯出與薪資系統對接。

### 可運行環境規劃 (Nginx + PHP + MariaDB)

為確保打卡系統可在標準 LEMP 環境運行，以下提供基礎部署規劃與建議設定：

#### 基礎服務

- **Nginx**：反向代理與靜態檔案服務。
- **PHP-FPM**：執行後端 PHP 應用程式。
- **MariaDB**：保存帳號、裝置與打卡紀錄等資料。

#### Nginx 配置要點

- 將 `backend/public` 設為網站根目錄。
- 所有 API 請求導向 `index.php` (前置控制器)。
- 強制 HTTPS 並設定安全標頭 (HSTS、X-Content-Type-Options 等)。
- 限制上傳大小與連線逾時。

#### PHP-FPM 配置要點

- 建議 PHP 8.1+。
- 設定 `memory_limit`、`max_execution_time`、`post_max_size` 等。
- 啟用 OPcache 以提升效能。
- 依照環境配置 `.env` 與資料庫連線參數。

#### MariaDB 配置要點

- 建議 MariaDB 10.6+。
- 設定 InnoDB 為預設引擎。
- 開啟慢查詢記錄以便優化。
- 定期備份與設定資料保留期限 (尤其 GPS 資訊)。

#### 部署流程 (概略)

1. 建置 Nginx、PHP-FPM、MariaDB。
2. 匯入 `database/schema.sql` 建表。
3. 佈署程式碼並設定 `.env`。
4. 設定 Nginx 虛擬主機與 PHP-FPM 連線。
5. 使用 HTTPS 憑證與排程備份。

## 授權

尚未指定授權條款，後續可依組織需求補充。
