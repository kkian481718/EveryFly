"""
EveryFly - 機票價格追蹤機器人

主程式入口
"""

import argparse
import sys
from pathlib import Path

# 確保可以匯入 src 模組
sys.path.insert(0, str(Path(__file__).parent))

from src.amadeus_client import AmadeusClient
from src.price_tracker import PriceTracker
from src.data_storage import DataStorage
from src.notifier import DiscordNotifier
from src.config import ROUTES, get_search_dates


def test_api():
    """測試 Amadeus API 連線"""
    print("\n🔍 測試 Amadeus API 連線...")
    print("-" * 40)
    
    try:
        client = AmadeusClient()
        success = client.test_connection()
        return success
    except ValueError as e:
        print(f"❌ 設定錯誤: {e}")
        print("\n請確認已設定以下環境變數:")
        print("  - AMADEUS_CLIENT_ID")
        print("  - AMADEUS_CLIENT_SECRET")
        print("\n或複製 .env.example 為 .env 並填入 API 金鑰")
        return False


def test_discord():
    """測試 Discord Webhook"""
    print("\n🔍 測試 Discord Webhook...")
    print("-" * 40)
    
    notifier = DiscordNotifier()
    
    if not notifier.is_enabled():
        print("⚠️ Discord 通知未設定")
        print("  請設定 DISCORD_WEBHOOK_URL 環境變數")
        return False
    
    success = notifier.send_message("🧪 EveryFly 連線測試成功！")
    
    if success:
        print("✅ Discord Webhook 測試成功!")
    else:
        print("❌ Discord Webhook 測試失敗")
    
    return success


def show_config():
    """顯示目前配置"""
    print("\n📋 目前配置")
    print("-" * 40)
    
    print("\n🛫 追蹤航線:")
    for route in ROUTES:
        print(f"  • {route.name} ({route.origin} → {route.destination})")
    
    print("\n📅 查詢日期組合:")
    dates = get_search_dates()
    print(f"  共 {len(dates)} 種日期組合")
    
    for d in dates[:8]:
        print(f"  • {d['label']}: {d['departure_date']}", end="")
        if d['return_date']:
            print(f" → {d['return_date']}")
        else:
            print()
    
    if len(dates) > 8:
        print(f"  ... 以及 {len(dates) - 8} 種其他組合")
    
    print(f"\n🔢 每日查詢總數: {len(ROUTES)} 航線 × {len(dates)} 日期 = {len(ROUTES) * len(dates)} 次")


def show_stats():
    """顯示歷史統計"""
    print("\n📊 歷史資料統計")
    print("-" * 40)
    
    storage = DataStorage()
    stats = storage.get_stats()
    
    if stats["total_records"] == 0:
        print("  尚無歷史資料")
        return
    
    print(f"  記錄總數: {stats['total_records']}")
    print(f"  追蹤航線: {', '.join(stats['routes'])}")
    print(f"  資料範圍: {stats['date_range']['min']} ~ {stats['date_range']['max']}")
    
    # 顯示各航線最低價
    lowest = storage.get_lowest_prices()
    if lowest:
        print("\n💰 各航線歷史最低價:")
        for route_name, info in lowest.items():
            trip = "來回" if info["trip_type"] == "round_trip" else "單程"
            print(f"  • {route_name}: {info['currency']} {info['price']:,.0f} ({trip})")


def run_tracking(no_notification: bool = False):
    """執行每日追蹤"""
    print("\n🚀 開始執行每日追蹤...")
    print("-" * 40)
    
    try:
        tracker = PriceTracker()
        stats = tracker.run_daily_tracking(send_notification=not no_notification)
        
        print("\n✅ 追蹤完成!")
        return True
        
    except ValueError as e:
        print(f"❌ 設定錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        
        # 嘗試發送錯誤通知
        notifier = DiscordNotifier()
        if notifier.is_enabled():
            notifier.send_error(f"每日追蹤發生錯誤:\n```\n{str(e)}\n```")
        
        return False


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="EveryFly - 機票價格追蹤機器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python main.py                  # 執行每日追蹤
  python main.py --test-api       # 測試 API 連線
  python main.py --test-discord   # 測試 Discord 通知
  python main.py --config         # 顯示目前配置
  python main.py --stats          # 顯示歷史統計
  python main.py --no-notification # 執行追蹤但不發送通知
        """
    )
    
    parser.add_argument(
        "--test-api",
        action="store_true",
        help="測試 Amadeus API 連線"
    )
    
    parser.add_argument(
        "--test-discord",
        action="store_true",
        help="測試 Discord Webhook"
    )
    
    parser.add_argument(
        "--config",
        action="store_true",
        help="顯示目前配置"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="顯示歷史資料統計"
    )
    
    parser.add_argument(
        "--no-notification",
        action="store_true",
        help="執行追蹤但不發送 Discord 通知"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  EveryFly - 機票價格追蹤機器人")  
    print("=" * 60)
    
    # 根據參數執行對應功能
    if args.test_api:
        success = test_api()
        sys.exit(0 if success else 1)
    
    elif args.test_discord:
        success = test_discord()
        sys.exit(0 if success else 1)
    
    elif args.config:
        show_config()
        sys.exit(0)
    
    elif args.stats:
        show_stats()
        sys.exit(0)
    
    else:
        # 預設：執行每日追蹤
        success = run_tracking(no_notification=args.no_notification)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
