# AI 理財小幫手

這個專案提供一個初版的「AI 理財小幫手」，依照 SRS 規劃實作資料擷取、AI 分析與報告輸出的核心流程。

## 快速開始

1. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
2. 設定必要的 API Key 環境變數：
   - `OPENAI_API_KEY`（ChatGPT/OpenAI 分析，預設使用）
   - `GEMINI_API_KEY`（選用，用於啟用 Gemini）
   - `PERPLEXITY_API_KEY`（選用，用於啟用 Perplexity）
3. 更新 `config/config.json` 內的股票與公司資訊與 AI 供應商設定。
4. 執行一次報告流程：
   ```bash
   python -m ai_financial_assistant --config config/config.json
   ```

若只想針對特定股票進行分析，可使用 `--ticker` 多次指定：

```bash
python -m ai_financial_assistant --ticker 2330.TW --ticker 2454.TW
```

## 主要功能
- 使用 `yfinance` 擷取股價資訊。
- 透過 Google News RSS 擷取財經新聞與全文。
- 串接 OpenAI、Gemini、Perplexity 等多種 LLM，生成新聞摘要、情緒分析與綜合點評。
- 以 Markdown 生成每日報告並輸出至 `reports/` 目錄。
- 自動累積歷史股價與 AI 情緒紀錄，支援長期追蹤。
- 產出投資組合總覽頁面，整理多檔標的現況與多模型專業諮詢結果。
- 可透過 `--schedule` 或設定檔開啟排程模式。

## 結構
- `ai_financial_assistant/config.py`：設定載入與驗證。
- `ai_financial_assistant/stock_data.py`：股價資料擷取。
- `ai_financial_assistant/news_fetcher.py`：Google News 文章擷取與解析。
- `ai_financial_assistant/analysis.py`：多供應商 AI 摘要、情緒與諮詢封裝。
- `ai_financial_assistant/report.py`：報告格式化與輸出。
- `ai_financial_assistant/history.py`：股價歷史追蹤與儲存。
- `ai_financial_assistant/pipeline.py`：整體流程協調。
- `ai_financial_assistant/cli.py`：命令列介面。
- `ai_financial_assistant/scheduler.py`：排程執行支援。

## 注意事項
- 實際執行會觸發外部 API 與網路請求，請留意使用政策與費用。
- 若未提供任何 API Key，可在設定檔關閉對應供應商或於命令列使用 `--disable-ai` 跳過分析。
