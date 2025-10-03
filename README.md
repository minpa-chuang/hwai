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

## 授權

尚未指定授權條款，後續可依組織需求補充。
