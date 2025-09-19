# AI 理財小幫手

這個專案提供一個初版的「AI 理財小幫手」，依照 SRS 規劃實作資料擷取、AI 分析與報告輸出的核心流程。

## 快速開始

1. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
2. 設定 `OPENAI_API_KEY` 環境變數。
3. 更新 `config/config.json` 內的股票與公司資訊。
4. 執行一次報告流程：
   ```bash
   python -m ai_financial_assistant --config config/config.json
   ```

## 主要功能
- 使用 `yfinance` 擷取股價資訊。
- 透過 Google News RSS 擷取財經新聞與全文。
- 串接 OpenAI 生成新聞摘要、情緒分析與綜合點評。
- 以 Markdown 生成每日報告並輸出至 `reports/` 目錄。
- 可透過 `--schedule` 或設定檔開啟排程模式。

## 結構
- `ai_financial_assistant/config.py`：設定載入與驗證。
- `ai_financial_assistant/stock_data.py`：股價資料擷取。
- `ai_financial_assistant/news_fetcher.py`：Google News 文章擷取與解析。
- `ai_financial_assistant/analysis.py`：OpenAI 摘要與情緒分析封裝。
- `ai_financial_assistant/report.py`：報告格式化與輸出。
- `ai_financial_assistant/pipeline.py`：整體流程協調。
- `ai_financial_assistant/cli.py`：命令列介面。
- `ai_financial_assistant/scheduler.py`：排程執行支援。

## 注意事項
- 實際執行會觸發外部 API 與網路請求，請留意使用政策與費用。
- 若未提供 `OPENAI_API_KEY` 或使用 `--disable-ai`，AI 分析將停用並以占位文字顯示。
