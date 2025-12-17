"""
機票價格追蹤核心模組

協調 API 查詢、資料儲存和通知功能。
"""

import time
from typing import List, Dict, Optional
from datetime import datetime

from .config import ROUTES, get_search_dates, DEFAULT_SEARCH_CONFIG
from .amadeus_client import AmadeusClient, FlightOffer
from .data_storage import DataStorage
from .notifier import DiscordNotifier


class PriceTracker:
    """機票價格追蹤器"""
    
    def __init__(
        self,
        amadeus_client: Optional[AmadeusClient] = None,
        storage: Optional[DataStorage] = None,
        notifier: Optional[DiscordNotifier] = None,
        delay_between_requests: float = 1.0
    ):
        """
        初始化追蹤器
        
        Args:
            amadeus_client: Amadeus API 客戶端
            storage: 資料儲存
            notifier: Discord 通知器
            delay_between_requests: API 請求間隔（秒）
        """
        self.client = amadeus_client or AmadeusClient()
        self.storage = storage or DataStorage()
        self.notifier = notifier or DiscordNotifier()
        self.delay = delay_between_requests
        
        # 追蹤統計
        self.stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "total_results": 0,
            "errors": 0,
            "lowest_prices": {},
        }
    
    def run_daily_tracking(self, routes: List = None, send_notification: bool = True) -> Dict:
        """
        執行每日價格追蹤
        
        Args:
            routes: 要追蹤的航線列表（預設為所有航線）
            send_notification: 是否發送 Discord 通知
        
        Returns:
            追蹤結果統計
        """
        routes = routes or ROUTES
        search_dates = get_search_dates()
        config = DEFAULT_SEARCH_CONFIG
        
        print(f"\n{'='*60}")
        print(f"🛫 EveryFly 每日機票價格追蹤")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"\n📍 追蹤航線: {len(routes)} 條")
        print(f"📆 查詢日期: {len(search_dates)} 種組合")
        print(f"🔢 預計查詢: {len(routes) * len(search_dates)} 次")
        print()
        
        all_deals = []
        
        for route in routes:
            print(f"\n--- {route.name} ({route.origin} → {route.destination}) ---")
            route_lowest = None
            
            for date_config in search_dates:
                self.stats["total_searches"] += 1
                
                try:
                    offers = self.client.search_flights(
                        origin=route.origin,
                        destination=route.destination,
                        departure_date=date_config["departure_date"],
                        return_date=date_config["return_date"],
                        adults=config.adults,
                        travel_class=config.travel_class,
                        non_stop=config.non_stop,
                        max_results=config.max_results,
                        currency=config.currency
                    )
                    
                    if offers:
                        self.stats["successful_searches"] += 1
                        self.stats["total_results"] += len(offers)
                        
                        # 儲存結果
                        saved = self.storage.save_results(
                            route_name=route.name,
                            origin=route.origin,
                            destination=route.destination,
                            departure_date=date_config["departure_date"],
                            return_date=date_config["return_date"],
                            trip_type=date_config["trip_type"],
                            search_label=date_config["label"],
                            offers=offers
                        )
                        
                        # 追蹤最低價
                        lowest = offers[0]
                        if route_lowest is None or lowest.price < route_lowest["price"]:
                            route_lowest = {
                                "route_name": route.name,
                                "price": lowest.price,
                                "currency": lowest.currency,
                                "trip_type": date_config["trip_type"],
                                "departure_date": date_config["departure_date"],
                                "return_date": date_config["return_date"],
                                "airlines": ",".join(lowest.airlines),
                                "stops": lowest.stops,
                            }
                        
                        print(f"  ✅ {date_config['label']}: {lowest.currency} {lowest.price:,.0f} ({len(offers)} 筆)")
                    else:
                        print(f"  ⚠️ {date_config['label']}: 無結果")
                
                except Exception as e:
                    self.stats["errors"] += 1
                    print(f"  ❌ {date_config['label']}: 錯誤 - {e}")
                
                # API 請求間隔
                time.sleep(self.delay)
            
            # 記錄該航線最低價
            if route_lowest:
                self.stats["lowest_prices"][route.name] = route_lowest
                all_deals.append(route_lowest)
        
        # 輸出摘要
        print(f"\n{'='*60}")
        print("📊 追蹤完成摘要")
        print(f"{'='*60}")
        print(f"  查詢總數: {self.stats['total_searches']}")
        print(f"  成功查詢: {self.stats['successful_searches']}")
        print(f"  取得報價: {self.stats['total_results']} 筆")
        print(f"  查詢失敗: {self.stats['errors']}")
        
        print("\n💰 各航線最低價:")
        for route_name, info in self.stats["lowest_prices"].items():
            trip = "來回" if info["trip_type"] == "round_trip" else "單程"
            print(f"  • {route_name}: {info['currency']} {info['price']:,.0f} ({trip})")
        
        # 發送 Discord 通知
        if send_notification and self.notifier.is_enabled():
            print("\n📤 發送 Discord 通知...")
            
            # 發送每日摘要
            success = self.notifier.send_daily_summary(self.stats)
            if success:
                print("  ✅ 摘要通知已發送")
            else:
                print("  ❌ 摘要通知發送失敗")
            
            # 發送優惠機票
            if all_deals:
                success = self.notifier.send_flight_deals(all_deals)
                if success:
                    print("  ✅ 優惠通知已發送")
                else:
                    print("  ❌ 優惠通知發送失敗")
        
        return self.stats
    
    def search_single_route(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None
    ) -> List[FlightOffer]:
        """
        搜尋單一航線
        
        Args:
            origin: 起點代碼
            destination: 終點代碼
            departure_date: 出發日期
            return_date: 回程日期
        
        Returns:
            FlightOffer 列表
        """
        config = DEFAULT_SEARCH_CONFIG
        
        return self.client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=config.adults,
            travel_class=config.travel_class,
            max_results=config.max_results,
            currency=config.currency
        )


if __name__ == "__main__":
    # 測試
    print("測試 PriceTracker...")
    
    try:
        tracker = PriceTracker()
        print("✅ PriceTracker 初始化成功")
    except Exception as e:
        print(f"❌ PriceTracker 初始化失敗: {e}")
