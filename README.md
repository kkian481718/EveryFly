# EveryFly - 機票價格追蹤機器人

自動追蹤多條航線的每日機票價格，並透過 Discord 通知低價資訊。

## 功能特色

- 🛫 追蹤 5 條熱門航線（台北 ↔ 東京/大阪/峇厘島/里斯本/柏林）
- 📊 比較單程/來回、直飛/轉機價格
- 💰 記錄歷史價格趨勢
- 🔔 透過 Discord Bot 通知低價
- ⏰ GitHub Actions 每日自動執行

## 追蹤航線

| 航線 | 距離 | 飛行時間 |
|------|------|----------|
| 台北 → 東京 | 2,100 km | 3h |
| 台北 → 大阪 | 1,700 km | 2.5h |
| 台北 → 峇厘島 | 3,600 km | 5h |
| 台北 → 里斯本 | 11,000 km | 16h+ |
| 台北 → 柏林 | 9,000 km | 13h+ |

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並填入：

```env
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_client_secret
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

### 3. 執行價格追蹤

```bash
python main.py
```

### 4. 測試 API 連線

```bash
python main.py --test-api
```

## 取得 API 金鑰

### Amadeus API

1. 前往 [Amadeus for Developers](https://developers.amadeus.com/)
2. 註冊免費帳戶
3. 建立新的 Application
4. 複製 API Key 和 API Secret

### Discord Webhook

1. 進入 Discord 伺服器設定
2. 整合 → Webhooks → 新增 Webhook
3. 複製 Webhook URL

## 資料輸出

價格資料儲存於 `data/prices.csv`，包含：

- 查詢時間
- 航線、出發/回程日期
- 航空公司、票價 (TWD)
- 行李資訊、轉機次數

## License

MIT
