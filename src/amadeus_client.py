"""
Amadeus API 客戶端

封裝 Amadeus API 的機票搜尋功能。
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from amadeus import Client, ResponseError
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()


@dataclass
class FlightOffer:
    """機票報價資料結構"""
    price: float                    # 總價
    currency: str                   # 貨幣
    airlines: List[str]             # 航空公司代碼列表
    departure_time: str             # 出發時間
    arrival_time: str               # 抵達時間
    duration: str                   # 飛行時間
    stops: int                      # 轉機次數
    stop_cities: List[str]          # 轉機城市
    segments: int                   # 航段數
    cabin_class: str                # 艙等
    included_bags: int              # 含托運行李數
    booking_class: str              # 訂位艙等代碼
    validating_carrier: str         # 開票航空公司
    last_ticketing_date: str        # 最後訂票日
    raw_data: Dict[str, Any]        # 原始 API 回應


class AmadeusClient:
    """Amadeus API 客戶端"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        初始化 Amadeus 客戶端
        
        Args:
            client_id: Amadeus API Client ID (若未提供則從環境變數讀取)
            client_secret: Amadeus API Client Secret (若未提供則從環境變數讀取)
        """
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "請設定 AMADEUS_CLIENT_ID 和 AMADEUS_CLIENT_SECRET 環境變數，"
                "或在初始化時傳入參數"
            )
        
        # 移除可能的空白和引號
        self.client_id = self.client_id.strip().strip('"').strip("'")
        self.client_secret = self.client_secret.strip().strip('"').strip("'")
        
        # 使用 test 環境（hostname 預設就是 test.api.amadeus.com）
        self.client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            hostname='test'  # 明確指定使用測試環境
        )
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        non_stop: Optional[bool] = None,
        max_results: int = 10,
        currency: str = "TWD"
    ) -> List[FlightOffer]:
        """
        搜尋機票
        
        Args:
            origin: 起點 IATA 代碼 (如 TPE)
            destination: 終點 IATA 代碼 (如 NRT)
            departure_date: 出發日期 (YYYY-MM-DD)
            return_date: 回程日期 (YYYY-MM-DD)，若為 None 則搜尋單程
            adults: 成人人數
            travel_class: 艙等 (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            non_stop: True=僅直飛, False=僅轉機, None=不限
            max_results: 最多回傳結果數
            currency: 貨幣代碼
        
        Returns:
            FlightOffer 列表，依價格排序
        """
        try:
            # 建立查詢參數
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "travelClass": travel_class,
                "max": max_results,
                "currencyCode": currency,
            }
            
            if return_date:
                params["returnDate"] = return_date
            
            if non_stop is not None:
                params["nonStop"] = non_stop
            
            # 呼叫 API
            response = self.client.shopping.flight_offers_search.get(**params)
            
            # 解析回應
            return self._parse_offers(response.data, currency)
            
        except ResponseError as e:
            print(f"API 錯誤: {e}")
            return []
    
    def _parse_offers(self, data: List[Dict], currency: str) -> List[FlightOffer]:
        """解析 API 回應為 FlightOffer 列表"""
        offers = []
        
        for offer in data:
            try:
                # 價格資訊
                price = float(offer["price"]["total"])
                
                # 航程資訊（取第一個 itinerary）
                itineraries = offer.get("itineraries", [])
                if not itineraries:
                    continue
                
                first_itinerary = itineraries[0]
                segments = first_itinerary.get("segments", [])
                
                if not segments:
                    continue
                
                # 航空公司
                airlines = list(set(seg.get("carrierCode", "") for seg in segments))
                
                # 出發/抵達時間
                departure_time = segments[0].get("departure", {}).get("at", "")
                arrival_time = segments[-1].get("arrival", {}).get("at", "")
                
                # 飛行時間
                duration = first_itinerary.get("duration", "")
                
                # 轉機資訊
                stops = len(segments) - 1
                stop_cities = []
                for i in range(len(segments) - 1):
                    stop_city = segments[i].get("arrival", {}).get("iataCode", "")
                    if stop_city:
                        stop_cities.append(stop_city)
                
                # 行李資訊
                included_bags = 0
                traveler_pricings = offer.get("travelerPricings", [])
                if traveler_pricings:
                    fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
                    if fare_details:
                        bags = fare_details[0].get("includedCheckedBags", {})
                        included_bags = bags.get("quantity", 0) or (1 if bags.get("weight") else 0)
                
                # 艙等
                cabin_class = "ECONOMY"
                if traveler_pricings:
                    fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
                    if fare_details:
                        cabin_class = fare_details[0].get("cabin", "ECONOMY")
                
                # 訂位艙等
                booking_class = ""
                if traveler_pricings:
                    fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
                    if fare_details:
                        booking_class = fare_details[0].get("class", "")
                
                offers.append(FlightOffer(
                    price=price,
                    currency=currency,
                    airlines=airlines,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    duration=duration,
                    stops=stops,
                    stop_cities=stop_cities,
                    segments=len(segments),
                    cabin_class=cabin_class,
                    included_bags=included_bags,
                    booking_class=booking_class,
                    validating_carrier=offer.get("validatingAirlineCodes", [""])[0],
                    last_ticketing_date=offer.get("lastTicketingDate", ""),
                    raw_data=offer
                ))
                
            except (KeyError, IndexError, TypeError) as e:
                print(f"解析報價失敗: {e}")
                continue
        
        # 依價格排序
        offers.sort(key=lambda x: x.price)
        return offers
    
    def test_connection(self) -> bool:
        """
        測試 API 連線
        
        Returns:
            True 表示連線成功
        """
        try:
            # 顯示認證資訊（遮蔽部分）
            masked_id = self.client_id[:8] + "..." if len(self.client_id) > 8 else self.client_id
            masked_secret = self.client_secret[:4] + "***" if len(self.client_secret) > 4 else "***"
            print(f"   Client ID: {masked_id}")
            print(f"   Client Secret: {masked_secret}")
            print(f"   環境: test.api.amadeus.com")
            print()
            
            # 用簡單查詢測試連線（使用 30 天後的日期）
            test_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            print(f"   測試日期: {test_date}")
            print()
            
            response = self.client.shopping.flight_offers_search.get(
                originLocationCode="TPE",
                destinationLocationCode="NRT",
                departureDate=test_date,
                adults=1,
                max=1
            )
            print("✅ Amadeus API 連線成功!")
            print(f"   找到 {len(response.data)} 筆結果")
            return True
        except ResponseError as e:
            print(f"❌ Amadeus API 連線失敗!")
            print(f"   錯誤代碼: {e.response.status_code}")
            
            # 嘗試解析錯誤詳情
            try:
                error_detail = e.response.result
                if 'error_description' in error_detail:
                    print(f"   錯誤描述: {error_detail['error_description']}")
                if 'errors' in error_detail:
                    for err in error_detail['errors']:
                        print(f"   - {err.get('detail', err)}")
            except:
                print(f"   原始錯誤: {e}")
            
            # 常見問題提示
            if e.response.status_code == 401:
                print("\n💡 提示: 401 錯誤通常表示 API Key 或 Secret 不正確")
            elif e.response.status_code == 400:
                print("\n💡 提示: 400 錯誤可能是:")
                print("   1. API Key 或 Secret 格式錯誤（請檢查是否有多餘空白或引號）")
                print("   2. .env 檔案格式問題")
                print("   3. 請確認複製的是完整的金鑰")
            
            return False


if __name__ == "__main__":
    # 測試 API
    try:
        client = AmadeusClient()
        client.test_connection()
    except ValueError as e:
        print(f"設定錯誤: {e}")
