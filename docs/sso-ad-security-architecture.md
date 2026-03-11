# 單一系統入口（SSO）身分驗證架構設計（AD 主備援）

本文件提供一套以 **Windows Active Directory（主要/備援）** 為核心，搭配 **PHP + MariaDB + Nginx** 的 Web 驗證架構與安全控制基準，並對應 **OWASP Top 10 Web Application Security Risks**。

---

## 1. 架構目標

- 企業使用者以 AD 帳號登入單一入口。
- AD 採主站（Primary AD）＋備援站（Secondary AD），任一站異常時可持續登入。
- 應用層採 PHP，資料庫採 MariaDB，反向代理/SSL 終止採 Nginx。
- 以「最小權限、零信任、可稽核」為原則。

---

## 2. 高層架構

1. 使用者透過 HTTPS 存取 Nginx。
2. Nginx 轉發至 PHP-FPM。
3. PHP 驗證流程：
   - 先連線 Primary AD（LDAPS 636）。
   - 若逾時或失敗，自動切換 Secondary AD。
   - 成功後取得 `sAMAccountName / userPrincipalName / memberOf`。
4. PHP 根據 AD 群組對應本地角色（RBAC），並在 MariaDB 更新使用者快取資料與登入稽核。
5. 發放安全 Session（HttpOnly + Secure + SameSite），所有授權由後端判定。

> 建議網段：Web/App 與 AD 走內網或 VPN，禁止 Internet 直接連 AD。

---

## 3. AD 認證與故障切換建議

### 3.1 連線策略

- 僅允許 `ldaps://dc1.example.local:636`、`ldaps://dc2.example.local:636`。
- 設定短逾時（例如 2–3 秒）＋重試一次，避免登入長時間卡住。
- 失敗條件（連線拒絕、TLS 失敗、逾時）即切至備援 AD。
- 禁用匿名 Bind，使用專用 Service Account 做搜尋，再用使用者 DN 驗證密碼。

### 3.2 帳號與群組同步

- 本地資料庫僅保留必要欄位（帳號、顯示名、Email、最後登入時間、狀態）。
- 權限來源以 AD 群組為主，本地僅存映射（如 `AD_IT_ADMIN -> ROLE_ADMIN`）。
- 每次登入可增量同步群組；另可排程夜間全量校正。

### 3.3 緊急應變

- 設計 `break-glass` 本地管理員帳號（強制 MFA、IP 白名單、獨立密碼輪替）。
- 當 AD 全斷時僅開放最小維運功能，不開放一般使用者登入。

---

## 4. PHP 實作安全基準

### 4.1 Session 與 Cookie

- `session.cookie_httponly=1`
- `session.cookie_secure=1`
- `session.cookie_samesite=Strict`（跨站需求再調整 Lax）
- 登入成功後 `session_regenerate_id(true)`。
- 設定閒置逾時（如 15 分鐘）與絕對逾時（如 8 小時）。

### 4.2 輸入/輸出與資料存取

- 所有 DB 操作使用 Prepared Statements（PDO）。
- 對輸入做 allow-list 驗證（長度、格式、型別）。
- 前端輸出一律 escaping（避免反射/儲存型 XSS）。

### 4.3 認證與授權

- 以後端中介層做授權（不可僅靠前端隱藏按鈕）。
- API 每個端點皆檢查角色/權限。
- 對登入、重設密碼、敏感操作加上 rate limit 與鎖定策略。

### 4.4 稽核與可觀測性

- 記錄：登入成功/失敗、AD 切換事件、權限變更、管理操作。
- 日誌避免明文密碼/Token/個資。
- 日誌寫入集中式平台（如 SIEM）並設告警門檻。

---

## 5. Nginx 與傳輸安全

- 全站強制 HTTPS 與 HSTS。
- TLS 1.2+，停用弱加密套件。
- 設定安全標頭：
  - `Content-Security-Policy`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- 限制上傳大小與請求速率（`client_max_body_size`, `limit_req`）。
- 關閉版本資訊外洩（`server_tokens off`）。

---

## 6. MariaDB 安全基準

- 應用帳號採最小權限（僅 CRUD 必要資料表）。
- 禁止 root 遠端登入，管理介面僅內網可達。
- 啟用 TLS（App -> DB）與磁碟加密（含備份）。
- 定期備份＋還原演練。
- 針對審計表、登入紀錄表設保留策略與防竄改機制。

---

## 7. OWASP Top 10 對應控制

1. **A01 Broken Access Control**
   - 後端集中授權檢查、RBAC、管理功能二次驗證。
2. **A02 Cryptographic Failures**
   - 全程 TLS、密碼不落地、敏感資料加密/遮罩。
3. **A03 Injection**
   - Prepared Statements、輸入驗證、ORM/Query Builder 安全模式。
4. **A04 Insecure Design**
   - 威脅建模、最小權限、失效安全（fail secure）。
5. **A05 Security Misconfiguration**
   - IaC 標準化、基線掃描、移除預設帳號/設定。
6. **A06 Vulnerable and Outdated Components**
   - Composer 套件版本治理、SCA 掃描、定期修補。
7. **A07 Identification and Authentication Failures**
   - AD 集中認證、Session 強化、登入防暴力破解。
8. **A08 Software and Data Integrity Failures**
   - CI/CD 簽章、依賴來源可信任、備份校驗。
9. **A09 Security Logging and Monitoring Failures**
   - 完整審計日誌、告警、保存與追蹤。
10. **A10 Server-Side Request Forgery (SSRF)**
   - 對外連線白名單、DNS/IP 過濾、禁止任意 URL 代理。

---

## 8. 建議落地清單（MVP）

- [ ] 完成 AD 主備 LDAPS 連線與健康檢查。
- [ ] 完成 AD 群組到系統角色映射表。
- [ ] 完成登入流程（Session 輪替、逾時、稽核）。
- [ ] 完成 Nginx HTTPS 與安全標頭。
- [ ] 完成 MariaDB 最小權限帳號與備份策略。
- [ ] 導入 SAST/SCA/DAST 與弱點修補流程。
- [ ] 完成 OWASP Top 10 對應檢核表。

