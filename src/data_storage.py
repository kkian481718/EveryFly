"""
資料儲存模組

將機票價格資料儲存為 CSV 格式。
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class DataStorage:
    """CSV 資料儲存"""
    
    # CSV 欄位定義
    FIELDNAMES = [
        "query_time",           # 查詢時間
        "route_name",           # 航線名稱
        "origin",               # 起點代碼
        "destination",          # 終點代碼
        "departure_date",       # 出發日期
        "return_date",          # 回程日期
        "trip_type",            # 行程類型 (one_way/round_trip)
        "price",                # 價格
        "currency",             # 貨幣
        "airlines",             # 航空公司
        "stops",                # 轉機次數
        "stop_cities",          # 轉機城市
        "duration",             # 飛行時間
        "cabin_class",          # 艙等
        "included_bags",        # 含托運行李數
        "departure_time",       # 出發時間
        "arrival_time",         # 抵達時間
        "validating_carrier",   # 開票航空公司
        "search_label",         # 搜尋標籤
    ]
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化資料儲存
        
        Args:
            data_dir: 資料目錄路徑
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.data_dir / "prices.csv"
        
        # 如果檔案不存在，建立並寫入標題列
        if not self.csv_path.exists():
            self._init_csv()
    
    def _init_csv(self):
        """初始化 CSV 檔案"""
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
    
    def save_results(
        self,
        route_name: str,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        trip_type: str,
        search_label: str,
        offers: List[Any]
    ) -> int:
        """
        儲存搜尋結果
        
        Args:
            route_name: 航線名稱
            origin: 起點代碼
            destination: 終點代碼
            departure_date: 出發日期
            return_date: 回程日期
            trip_type: 行程類型
            search_label: 搜尋標籤
            offers: FlightOffer 列表
        
        Returns:
            儲存的記錄數
        """
        query_time = datetime.now().isoformat()
        count = 0
        
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            
            for offer in offers:
                row = {
                    "query_time": query_time,
                    "route_name": route_name,
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date or "",
                    "trip_type": trip_type,
                    "price": offer.price,
                    "currency": offer.currency,
                    "airlines": ",".join(offer.airlines),
                    "stops": offer.stops,
                    "stop_cities": ",".join(offer.stop_cities),
                    "duration": offer.duration,
                    "cabin_class": offer.cabin_class,
                    "included_bags": offer.included_bags,
                    "departure_time": offer.departure_time,
                    "arrival_time": offer.arrival_time,
                    "validating_carrier": offer.validating_carrier,
                    "search_label": search_label,
                }
                writer.writerow(row)
                count += 1
        
        return count
    
    def get_lowest_prices(self, route_name: Optional[str] = None) -> Dict[str, Dict]:
        """
        取得各航線的最低價格
        
        Args:
            route_name: 指定航線名稱，若為 None 則回傳所有航線
        
        Returns:
            各航線的最低價格資訊
        """
        lowest = {}
        
        if not self.csv_path.exists():
            return lowest
        
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row["route_name"]
                
                if route_name and name != route_name:
                    continue
                
                price = float(row["price"])
                
                if name not in lowest or price < lowest[name]["price"]:
                    lowest[name] = {
                        "price": price,
                        "currency": row["currency"],
                        "departure_date": row["departure_date"],
                        "return_date": row["return_date"],
                        "trip_type": row["trip_type"],
                        "airlines": row["airlines"],
                        "stops": int(row["stops"]),
                        "query_time": row["query_time"],
                    }
        
        return lowest
    
    def get_today_results(self) -> List[Dict]:
        """
        取得今天的查詢結果
        
        Returns:
            今天的所有查詢記錄
        """
        today = datetime.now().date().isoformat()
        results = []
        
        if not self.csv_path.exists():
            return results
        
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if row["query_time"].startswith(today):
                    results.append(row)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        取得資料統計
        
        Returns:
            統計資訊
        """
        stats = {
            "total_records": 0,
            "routes": set(),
            "date_range": {"min": None, "max": None},
        }
        
        if not self.csv_path.exists():
            return stats
        
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats["total_records"] += 1
                stats["routes"].add(row["route_name"])
                
                query_date = row["query_time"][:10]
                if stats["date_range"]["min"] is None or query_date < stats["date_range"]["min"]:
                    stats["date_range"]["min"] = query_date
                if stats["date_range"]["max"] is None or query_date > stats["date_range"]["max"]:
                    stats["date_range"]["max"] = query_date
        
        stats["routes"] = list(stats["routes"])
        return stats


if __name__ == "__main__":
    # 測試
    storage = DataStorage()
    print(f"CSV 路徑: {storage.csv_path}")
    
    stats = storage.get_stats()
    print(f"統計: {stats}")
