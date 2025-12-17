"""
Discord 通知模組

透過 Discord Webhook 發送機票低價通知。
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


class DiscordNotifier:
    """Discord Webhook 通知"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        初始化 Discord 通知器
        
        Args:
            webhook_url: Discord Webhook URL (若未提供則從環境變數讀取)
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        
        if not self.webhook_url:
            print("⚠️ 未設定 DISCORD_WEBHOOK_URL，通知功能將停用")
    
    def is_enabled(self) -> bool:
        """檢查通知是否啟用"""
        return bool(self.webhook_url)
    
    def send_message(self, content: str) -> bool:
        """
        發送純文字訊息
        
        Args:
            content: 訊息內容
        
        Returns:
            True 表示發送成功
        """
        if not self.is_enabled():
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json={"content": content},
                timeout=10
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Discord 發送失敗: {e}")
            return False
    
    def send_embed(
        self,
        title: str,
        description: str,
        fields: List[Dict[str, str]] = None,
        color: int = 0x5865F2,
        footer: str = None
    ) -> bool:
        """
        發送嵌入訊息
        
        Args:
            title: 標題
            description: 描述
            fields: 欄位列表 [{"name": "...", "value": "...", "inline": True/False}]
            color: 顏色代碼
            footer: 頁尾文字
        
        Returns:
            True 表示發送成功
        """
        if not self.is_enabled():
            return False
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if fields:
            embed["fields"] = fields
        
        if footer:
            embed["footer"] = {"text": footer}
        
        try:
            response = requests.post(
                self.webhook_url,
                json={"embeds": [embed]},
                timeout=10
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Discord 發送失敗: {e}")
            return False
    
    def send_flight_deals(self, deals: List[Dict]) -> bool:
        """
        發送機票優惠通知
        
        Args:
            deals: 優惠列表，每項包含航線、價格等資訊
        
        Returns:
            True 表示發送成功
        """
        if not deals:
            return False
        
        fields = []
        for deal in deals[:10]:  # 最多顯示 10 筆
            route = deal.get("route_name", "未知航線")
            price = deal.get("price", 0)
            currency = deal.get("currency", "TWD")
            trip_type = "來回" if deal.get("trip_type") == "round_trip" else "單程"
            departure = deal.get("departure_date", "")
            return_date = deal.get("return_date", "")
            airlines = deal.get("airlines", "")
            stops = deal.get("stops", 0)
            
            stop_text = "直飛" if stops == 0 else f"轉機{stops}次"
            date_text = f"{departure}"
            if return_date:
                date_text += f" → {return_date}"
            
            fields.append({
                "name": f"✈️ {route}",
                "value": (
                    f"💰 **{currency} {price:,.0f}** ({trip_type})\n"
                    f"📅 {date_text}\n"
                    f"🛫 {airlines} | {stop_text}"
                ),
                "inline": True
            })
        
        return self.send_embed(
            title="🎫 每日機票價格報告",
            description=f"找到 {len(deals)} 筆優惠機票！",
            fields=fields,
            color=0x00D166,  # 綠色
            footer="EveryFly 機票追蹤機器人"
        )
    
    def send_daily_summary(self, summary: Dict) -> bool:
        """
        發送每日摘要
        
        Args:
            summary: 摘要資訊
        
        Returns:
            True 表示發送成功
        """
        total_searches = summary.get("total_searches", 0)
        total_results = summary.get("total_results", 0)
        lowest_prices = summary.get("lowest_prices", {})
        errors = summary.get("errors", 0)
        
        # 建立價格文字
        price_lines = []
        for route, info in lowest_prices.items():
            price = info.get("price", 0)
            currency = info.get("currency", "TWD")
            trip_type = "來回" if info.get("trip_type") == "round_trip" else "單程"
            price_lines.append(f"• {route}: **{currency} {price:,.0f}** ({trip_type})")
        
        description = (
            f"📊 共查詢 {total_searches} 次\n"
            f"✅ 取得 {total_results} 筆報價\n"
        )
        
        if errors:
            description += f"❌ {errors} 次查詢失敗\n"
        
        description += "\n**各航線最低價格：**\n" + "\n".join(price_lines)
        
        return self.send_embed(
            title="📈 每日追蹤摘要",
            description=description,
            color=0x5865F2,  # Discord 藍
            footer=f"EveryFly | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    
    def send_error(self, error_message: str) -> bool:
        """
        發送錯誤通知
        
        Args:
            error_message: 錯誤訊息
        
        Returns:
            True 表示發送成功
        """
        return self.send_embed(
            title="⚠️ 追蹤發生錯誤",
            description=error_message,
            color=0xED4245,  # 紅色
            footer="EveryFly"
        )


if __name__ == "__main__":
    # 測試
    notifier = DiscordNotifier()
    
    if notifier.is_enabled():
        print("Discord 通知已啟用")
        
        # 測試發送
        success = notifier.send_message("🧪 EveryFly 測試訊息")
        print(f"發送測試訊息: {'成功' if success else '失敗'}")
    else:
        print("Discord 通知未啟用（未設定 DISCORD_WEBHOOK_URL）")
